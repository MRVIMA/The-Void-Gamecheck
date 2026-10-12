"""Look-ups across all sources, in parallel, with caching and per-source errors."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from void_gamecheck import USER_AGENT, sources
from void_gamecheck.cache import Cache
from void_gamecheck.verdict import Verdict, judge


def cache_path() -> Path:
    import os

    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "the-void-gamecheck" / "cache.db"


@dataclass
class Report:
    appid: int
    name: str
    steam: dict | None
    proton: dict | None
    deck: str | None
    lutris: dict | None
    verdict: Verdict
    errors: dict[str, str] = field(default_factory=dict)
    checked_at: float = field(default_factory=time.time)

    @property
    def native(self) -> bool:
        return bool((self.steam or {}).get("platforms", {}).get("linux"))

    @property
    def links(self) -> dict[str, str]:
        out = {"Steam": f"https://store.steampowered.com/app/{self.appid}/",
               "ProtonDB": f"https://www.protondb.com/app/{self.appid}"}
        if self.lutris:
            out["Lutris"] = self.lutris["url"]
        return out


class GameCheck:
    def __init__(self, cache: Cache | None = None,
                 transport: httpx.BaseTransport | None = None) -> None:
        self.cache = cache if cache is not None else Cache(cache_path())
        self.client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=15,
                                   follow_redirects=True, transport=transport)

    def _cached(self, key: str, fetch, *, refresh: bool):
        if not refresh and (hit := self.cache.get(key)) is not None:
            return hit["v"]
        value = fetch()
        self.cache.put(key, {"v": value})
        return value

    def search(self, term: str, *, refresh: bool = False) -> list[sources.SteamHit]:
        term = " ".join(term.split())
        if not term:
            return []
        raw = self._cached(f"search:{term.lower()}",
                           lambda: [h.__dict__ for h in sources.steam_search(self.client, term)],
                           refresh=refresh)
        return [sources.SteamHit(**h) for h in raw]

    def report(self, appid: int, name: str = "", *, refresh: bool = False) -> Report:
        jobs = {
            "steam": (f"steam:{appid}", lambda: sources.steam_details(self.client, appid)),
            "proton": (f"proton:{appid}", lambda: sources.protondb_summary(self.client, appid)),
            "deck": (f"deck:{appid}", lambda: sources.deck_status(self.client, appid)),
        }
        results, errors = {}, {}

        def run(item):
            key, (cache_key, fetch) = item
            try:
                return key, self._cached(cache_key, fetch, refresh=refresh), None
            except sources.SourceError as exc:
                return key, None, str(exc)

        with ThreadPoolExecutor(max_workers=4) as pool:
            for key, value, err in pool.map(run, jobs.items()):
                results[key] = value
                if err:
                    errors[key] = err
        title = (results["steam"] or {}).get("name") or name
        try:
            lutris = self._cached(f"lutris:{appid}",
                                  lambda: sources.lutris_lookup(self.client, title, appid),
                                  refresh=refresh) if title else None
        except sources.SourceError as exc:
            lutris, errors["lutris"] = None, str(exc)
        native = (results["steam"] or {}).get("platforms", {}).get("linux") \
            if results["steam"] else None
        verdict = judge(native, results["proton"], results["deck"], lutris)
        return Report(appid, title or f"App {appid}", results["steam"], results["proton"],
                      results["deck"], lutris, verdict, errors)

    def check(self, term: str, *, refresh: bool = False) -> Report | None:
        """Search and report on the best match in one go (exact name first)."""
        hits = self.search(term, refresh=refresh)
        if not hits:
            return None
        want = term.casefold().strip()
        best = next((h for h in hits if h.name.casefold() == want), hits[0])
        return self.report(best.appid, best.name, refresh=refresh)

    def close(self) -> None:
        self.client.close()
