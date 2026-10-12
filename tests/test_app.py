import time

import httpx

from tests.fakes import handler
from void_gamecheck.cache import Cache
from void_gamecheck.service import GameCheck


def wait(qapp, cond, timeout=10):
    end = time.monotonic() + timeout
    while time.monotonic() < end and not cond():
        qapp.processEvents()
        time.sleep(0.01)
    return cond()


def test_search_select_and_report(qapp):
    from void_gamecheck.app import MainWindow

    gc = GameCheck(cache=Cache(":memory:"), transport=httpx.MockTransport(handler([])))
    win = MainWindow(gc)
    win.query.setText("saga")
    win.search()
    assert wait(qapp, lambda: win.report is not None and not win._tasks)
    assert win.results.count() == 1
    assert win.verdict.text() == "EXCELLENT  ·  VIA PROTON"
    assert win.cards["proton"].value.text() == "PLATINUM"
    assert win.cards["deck"].value.text() == "VERIFIED"
    assert win.cards["lutris"].value.text() == "2 SCRIPTS"
    body = win.body.toPlainText()
    assert "SET UP ON YOUR SYSTEM" in body and "LINUX REQUIREMENTS" not in body
    win.query.setText("native")
    win.search()
    assert wait(qapp, lambda: win.report is not None and win.report.appid == 100
                and not win._tasks)
    assert win.verdict.text() == "EXCELLENT  ·  NATIVE"
    assert "OS: Ubuntu 22.04" in win.body.toPlainText()
    win.close()


def test_failed_search_is_reported(qapp):
    from void_gamecheck.app import MainWindow

    gc = GameCheck(cache=Cache(":memory:"),
                   transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    win = MainWindow(gc)
    win.query.setText("anything")
    win.search()
    assert wait(qapp, lambda: "Search failed" in win.status.text())
    assert win.go.isEnabled()
    win.close()
