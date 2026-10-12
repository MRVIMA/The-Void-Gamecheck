"""``gamecheck``: how well does a game run on Linux?

    gamecheck "elden ring"          verdict, sources and setup tips for the best match
    gamecheck --list "witcher"      all matching games, with a quick native/Proton check
    gamecheck --appid 1245620       a game by its Steam app id
    gamecheck --json "dota 2"       machine-readable output
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from void_gamecheck import APP_NAME, __version__, distro
from void_gamecheck.service import GameCheck, Report

COLORS = {"EXCELLENT": "32", "GOOD": "32", "PLAYABLE": "33", "POOR": "33", "UNLIKELY": "31",
          "BROKEN": "31", "UNKNOWN": "90"}


def _c(text: str, code: str, on: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if on else text


def show(r: Report, *, color: bool, tips: bool) -> None:
    v = r.verdict
    print(_c(r.name, "1", color) + f"  (Steam app {r.appid})")
    print(f"  {_c(v.label, COLORS[v.label], color)} — {v.summary}"
          + (f"  [{'native' if v.how == 'native' else 'via Proton'}]" if v.how else ""))
    for reason in v.reasons:
        print(f"   • {reason}")
    for src, err in r.errors.items():
        print(_c(f"   ! {src}: {err}", "33", color))
    print("  " + "   ".join(f"{k}: {u}" for k, u in r.links.items()))
    if tips:
        print()
        for line in distro.tips(distro.detect(), how=v.how, level=v.level,
                                has_lutris=bool(r.lutris)):
            print(f"  {line}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="gamecheck", description=f"{APP_NAME}: Linux game "
                                 "compatibility from Steam, ProtonDB, Steam Deck and Lutris.")
    ap.add_argument("game", nargs="*", help="game name")
    ap.add_argument("--appid", type=int, help="Steam app id instead of a name")
    ap.add_argument("--list", action="store_true", help="list all matches")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--refresh", action="store_true", help="ignore cached data")
    ap.add_argument("--no-tips", action="store_true", help="hide distro setup tips")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    a = ap.parse_args(argv)
    term = " ".join(a.game)
    if not term and a.appid is None:
        ap.error("give a game name or --appid")
    color = sys.stdout.isatty() and not a.json
    gc = GameCheck()
    try:
        if a.list:
            hits = gc.search(term, refresh=a.refresh)
            if a.json:
                print(json.dumps([h.__dict__ for h in hits], indent=2))
            for h in hits if not a.json else []:
                kind = _c("native Linux", "32", color) if h.linux else "Windows → Proton"
                print(f"{h.appid:>9}  {h.name}  ·  {kind}")
            if not hits:
                print("No games found.")
            return 0 if hits else 1
        report = gc.report(a.appid, refresh=a.refresh) if a.appid else \
            gc.check(term, refresh=a.refresh)
        if report is None:
            print(f"No game found for “{term}”.")
            return 1
        if a.json:
            data = asdict(report)
            data["native"], data["links"] = report.native, report.links
            print(json.dumps(data, indent=2, default=str))
        else:
            show(report, color=color, tips=not a.no_tips)
        return 0
    finally:
        gc.close()


if __name__ == "__main__":
    raise SystemExit(main())
