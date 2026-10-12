import json

import httpx
import pytest

from tests.fakes import handler
from void_gamecheck import cli, distro
from void_gamecheck.cache import Cache
from void_gamecheck.service import GameCheck
from void_gamecheck.verdict import judge


@pytest.fixture
def gc():
    calls = []
    g = GameCheck(cache=Cache(":memory:"), transport=httpx.MockTransport(handler(calls)))
    g.calls = calls
    yield g
    g.close()


# ---- verdict -----------------------------------------------------------------------------

@pytest.mark.parametrize("native,tier,deck,label,how", [
    (True, "bronze", None, "EXCELLENT", "native"),         # native beats a poor Proton rating
    (False, "platinum", "verified", "EXCELLENT", "proton"),
    (False, "gold", None, "GOOD", "proton"),
    (False, "silver", None, "PLAYABLE", "proton"),
    (False, "bronze", None, "POOR", "proton"),
    (False, "borked", None, "BROKEN", "proton"),
    (False, None, "verified", "GOOD", "proton"),            # no ProtonDB data: Deck decides
    (False, None, "unsupported", "UNLIKELY", "proton"),
    (None, None, None, "UNKNOWN", ""),
])
def test_verdict_levels(native, tier, deck, label, how):
    v = judge(native, {"tier": tier, "total": 10} if tier else None, deck, None)
    assert (v.label, v.how) == (label, how)
    assert v.reasons


def test_verdict_explains_every_source():
    v = judge(False, {"tier": "gold", "trendingTier": "platinum", "total": 2105,
                      "confidence": "strong"}, "verified",
              {"installers": [{"runner": "steam"}, {"runner": "wine"}]})
    text = " ".join(v.reasons)
    assert "GOLD" in text and "2,105 reports" in text and "trend towards PLATINUM" in text
    assert "Steam Deck: Verified" in text and "Lutris: 2 install script(s) (steam, wine)" in text


# ---- service -----------------------------------------------------------------------------

def test_native_game_report(gc):
    r = gc.check("native quest")
    assert r.appid == 100 and r.native and r.verdict.label == "EXCELLENT"
    assert r.verdict.how == "native" and r.deck == "verified"
    assert r.steam["linux_requirements"] == "OS: Ubuntu 22.04"
    assert r.lutris["url"] == "https://lutris.net/games/native-quest/"
    assert set(r.links) == {"Steam", "ProtonDB", "Lutris"}


def test_proton_and_missing_data(gc):
    assert gc.check("rough edges").verdict.label == "POOR"
    deck_only = gc.check("deck only")
    assert deck_only.proton is None and deck_only.verdict.label == "PLAYABLE"
    mystery = gc.check("mystery game")
    assert mystery.verdict.label == "UNKNOWN" and mystery.lutris is None
    assert gc.check("does not exist") is None


def test_results_are_cached(gc):
    gc.check("proton saga")
    n = len(gc.calls)
    gc.check("proton saga")
    assert len(gc.calls) == n                           # second look-up: no network
    gc.check("proton saga", refresh=True)
    assert len(gc.calls) > n


def test_source_errors_are_reported_not_fatal():
    def flaky(request):
        if "protondb" in request.url.host:
            return httpx.Response(503)
        return handler([])(request)
    g = GameCheck(cache=Cache(":memory:"), transport=httpx.MockTransport(flaky))
    r = g.check("proton saga")
    assert r.errors == {"proton": "HTTP 503"}
    assert r.verdict.label == "GOOD"                    # still judged from the Deck status
    g.close()


# ---- distro tips -------------------------------------------------------------------------

@pytest.mark.parametrize("os_release,family,needle", [
    ('ID=cachyos\nID_LIKE=arch\nPRETTY_NAME="CachyOS"', "arch", "cachyos-gaming-meta"),
    ('ID=endeavouros\nID_LIKE=arch', "arch", "multilib"),
    ('ID=fedora\nPRETTY_NAME="Fedora Linux 44"', "fedora", "RPM Fusion"),
    ('ID=pop\nID_LIKE="ubuntu debian"', "debian", "steam-installer"),
    ('ID="opensuse-tumbleweed"\nID_LIKE="opensuse suse"', "suse", "zypper"),
    ('ID=nixos', "other", "flatpak"),
])
def test_distro_detection_and_tips(os_release, family, needle):
    d = distro.detect(os_release)
    assert d.family == family
    assert needle in "\n".join(distro.tips(d, how="proton", level=3, has_lutris=True))


def test_tips_depend_on_the_game():
    d = distro.detect("ID=cachyos\nID_LIKE=arch")
    native = "\n".join(distro.tips(d, how="native", level=5, has_lutris=False))
    assert "native Linux build" in native and "Proton-GE" not in native
    rough = "\n".join(distro.tips(d, how="proton", level=2, has_lutris=False))
    assert "protonup-qt" in rough and "ProtonDB page" in rough


# ---- CLI ---------------------------------------------------------------------------------

def test_cli_text_and_json(gc, monkeypatch, capsys):
    monkeypatch.setattr(cli, "GameCheck", lambda: gc)
    monkeypatch.setattr(gc, "close", lambda: None)
    assert cli.main(["--no-tips", "proton", "saga"]) == 0
    out = capsys.readouterr().out
    assert "Proton Saga" in out and "EXCELLENT" in out and "ProtonDB: PLATINUM" in out
    assert cli.main(["--json", "--appid", "300"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["verdict"]["label"] == "POOR" and data["native"] is False
    assert cli.main(["--list", "a"]) == 0
    assert "native Linux" in capsys.readouterr().out
    assert cli.main(["nothing-like-this"]) == 1
