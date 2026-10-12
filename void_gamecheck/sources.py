"""Public data sources. Each function returns plain data, or None when the source has
nothing for the game; network problems raise SourceError."""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

STEAM_SEARCH = "https://store.steampowered.com/api/storesearch/"
STEAM_DETAILS = "https://store.steampowered.com/api/appdetails"
DECK_REPORT = "https://store.steampowered.com/saleaction/ajaxgetdeckappcompatibilityreport"
PROTONDB = "https://www.protondb.com/api/v1/reports/summaries/{appid}.json"
LUTRIS_SEARCH = "https://lutris.net/api/games"
LUTRIS_GAME = "https://lutris.net/api/games/{slug}"

DECK_CATEGORIES = {0: "unknown", 1: "unsupported", 2: "playable", 3: "verified"}


class SourceError(RuntimeError):
    pass


@dataclass
class SteamHit:
    appid: int
    name: str
    linux: bool
    windows: bool
    mac: bool
    image: str = ""


def _get(client: httpx.Client, url: str, **params):
    try:
        resp = client.get(url, params=params or None)
    except httpx.HTTPError as exc:
        raise SourceError(f"{type(exc).__name__}: {exc}") from None
    if resp.status_code == 404:
        return None
    if resp.status_code == 429:
        raise SourceError("rate limited, try again in a minute")
    if resp.status_code >= 400:
        raise SourceError(f"HTTP {resp.status_code}")
    try:
        return resp.json()
    except ValueError:
        raise SourceError("unexpected response (not JSON)") from None


def steam_search(client: httpx.Client, term: str, *, country: str = "us") -> list[SteamHit]:
    data = _get(client, STEAM_SEARCH, term=term, cc=country, l="en") or {}
    hits = []
    for item in data.get("items", []):
        if item.get("type", "app") != "app":
            continue
        p = item.get("platforms") or {}
        hits.append(SteamHit(int(item["id"]), item.get("name", ""), bool(p.get("linux")),
                             bool(p.get("windows")), bool(p.get("mac")),
                             item.get("tiny_image", "")))
    return hits


def steam_details(client: httpx.Client, appid: int) -> dict | None:
    data = _get(client, STEAM_DETAILS, appids=appid, l="en") or {}
    entry = data.get(str(appid)) or {}
    if not entry.get("success"):
        return None
    d = entry.get("data") or {}
    req = d.get("linux_requirements")
    req_text = _strip_html(req.get("minimum", "")) if isinstance(req, dict) else ""
    if req_text.strip().rstrip(":").lower() == "minimum":
        req_text = ""
    return {"name": d.get("name", ""), "platforms": d.get("platforms") or {},
            "type": d.get("type", ""), "is_free": bool(d.get("is_free")),
            "header_image": d.get("header_image", ""),
            "short_description": _strip_html(d.get("short_description", "")),
            "developers": d.get("developers") or [], "linux_requirements": req_text,
            "release_date": (d.get("release_date") or {}).get("date", "")}


def protondb_summary(client: httpx.Client, appid: int) -> dict | None:
    data = _get(client, PROTONDB.format(appid=appid))
    if not data:
        return None
    return {k: data.get(k) for k in ("tier", "trendingTier", "bestReportedTier", "confidence",
                                     "score", "total")}


def deck_status(client: httpx.Client, appid: int) -> str | None:
    data = _get(client, DECK_REPORT, nAppID=appid, l="english") or {}
    results = data.get("results") or {}
    if not data.get("success") or "resolved_category" not in results:
        return None
    return DECK_CATEGORIES.get(int(results["resolved_category"]), "unknown")


def lutris_lookup(client: httpx.Client, name: str, appid: int | None = None) -> dict | None:
    """The Lutris entry for a game: matched by Steam app id when Lutris has it, else by name."""
    data = _get(client, LUTRIS_SEARCH, search=name) or {}
    results = data.get("results") or []
    wanted = _norm(name)
    match = next((r for r in results if appid and str(r.get("steamid") or "") == str(appid)),
                 None) or next((r for r in results if _norm(r.get("name", "")) == wanted), None)
    if match is None:
        return None
    game = _get(client, LUTRIS_GAME.format(slug=match["slug"])) or match
    installers = game.get("installers") or []
    return {"slug": match["slug"], "name": game.get("name", match.get("name", "")),
            "installers": [{"runner": i.get("runner", ""), "version": i.get("version", "")}
                           for i in installers if isinstance(i, dict)],
            "url": f"https://lutris.net/games/{match['slug']}/"}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>|</li>|</p>", "\n", text or "", flags=re.I)
    text = re.sub(r"<[^<>]{0,500}>", "", text)
    return "\n".join(" ".join(line.split()) for line in text.splitlines() if line.strip())
