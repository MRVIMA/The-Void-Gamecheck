"""One clear Linux outlook from several sources, with the reasons behind it."""

from __future__ import annotations

from dataclasses import dataclass, field

# ProtonDB tiers, best first (https://www.protondb.com/help/improving-ratings)
PROTON_TIERS = {
    "platinum": (5, "runs perfectly out of the box"),
    "gold": (4, "runs perfectly after small tweaks"),
    "silver": (3, "runs with minor issues; playable"),
    "bronze": (2, "runs, but often crashes or has issues"),
    "borked": (0, "doesn't start or isn't playable"),
}
DECK = {"verified": 4, "playable": 3, "unsupported": 1}

LEVELS = {
    5: ("EXCELLENT", "Works great on Linux."),
    4: ("GOOD", "Works well on Linux."),
    3: ("PLAYABLE", "Playable on Linux, with some issues."),
    2: ("POOR", "Runs on Linux, but expect problems."),
    1: ("UNLIKELY", "Probably won't work well on Linux."),
    0: ("BROKEN", "Reported not to work on Linux."),
}


@dataclass
class Verdict:
    level: int | None
    label: str
    summary: str
    how: str                              # "native", "proton" or ""
    reasons: list[str] = field(default_factory=list)


def judge(native: bool | None, proton: dict | None, deck: str | None,
          lutris: dict | None) -> Verdict:
    reasons: list[str] = []
    score: int | None = None
    how = ""
    if native:
        score, how = 5, "native"
        reasons.append("Native Linux version on Steam (no Proton needed).")
    tier = (proton or {}).get("tier")
    if tier in PROTON_TIERS:
        level, meaning = PROTON_TIERS[tier]
        total = (proton or {}).get("total") or 0
        conf = (proton or {}).get("confidence") or "unknown"
        reasons.append(f"ProtonDB: {tier.upper()} — {meaning} ({total:,} reports, "
                       f"{conf} confidence).")
        trend = (proton or {}).get("trendingTier")
        if trend and trend != tier and trend in PROTON_TIERS:
            reasons.append(f"Recent reports trend towards {trend.upper()}.")
        if score is None:
            score, how = level, "proton"
    elif proton is not None:
        reasons.append("ProtonDB: not enough reports yet.")
    if deck in DECK:
        note = (" — Valve found problems on SteamOS (Linux)." if deck == "unsupported"
                else " — the Deck runs SteamOS (Linux), a strong sign.")
        reasons.append(f"Steam Deck: {deck.capitalize()}{note}")
        if score is None:
            score, how = DECK[deck], "proton"
    if lutris and lutris.get("installers"):
        runners = sorted({i["runner"] for i in lutris["installers"] if i.get("runner")})
        reasons.append(f"Lutris: {len(lutris['installers'])} install script(s) "
                       f"({', '.join(runners) or 'various runners'}).")
    if score is None:
        return Verdict(None, "UNKNOWN", "No Linux compatibility data found for this game.",
                       "", reasons or ["None of the sources has information yet."])
    label, summary = LEVELS[score]
    return Verdict(score, label, summary, how, reasons)
