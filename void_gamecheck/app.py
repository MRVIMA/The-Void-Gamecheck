"""THE VOID GAMECHECK desktop app (PySide6, THE VOID theme)."""

from __future__ import annotations

import html
import sys
import time
from importlib.resources import files

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtGui import QDesktopServices, QFontDatabase, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from void_gamecheck import APP_ID, APP_NAME, __version__, distro
from void_gamecheck.service import GameCheck, Report

BG, PANEL, BORDER, FG, MUTED = "#08090D", "#111318", "#292D36", "#F2F2F2", "#9599A4"
CRIMSON, GREEN, AMBER, RED = "#D90429", "#3DDC97", "#FFB020", "#FF4D5E"
LEVEL_COLORS = {"EXCELLENT": GREEN, "GOOD": GREEN, "PLAYABLE": AMBER, "POOR": AMBER,
                "UNLIKELY": RED, "BROKEN": RED, "UNKNOWN": MUTED}
E = html.escape

QSS = f"""
QWidget {{ background: {BG}; color: {FG}; font-family: Inter; font-size: 10pt; }}
QLabel#title {{ font-family: Rajdhani; font-size: 24pt; font-weight: 700; letter-spacing: 2px; }}
QLabel#subtitle, QLabel#muted {{ color: {MUTED}; }}
QLabel#verdict {{ font-family: Rajdhani; font-size: 22pt; font-weight: 700; letter-spacing: 2px; }}
QLabel#gameName {{ font-family: Rajdhani; font-size: 18pt; font-weight: 700; }}
QLabel#cardTitle {{ color: {MUTED}; font-size: 8pt; letter-spacing: 1px; }}
QLabel#cardValue {{ font-family: Rajdhani; font-size: 14pt; font-weight: 700; }}
QFrame#card {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 4px; }}
QFrame#card QLabel {{ background: transparent; border: none; }}
QLineEdit {{ background: {PANEL}; border: 1px solid {BORDER}; padding: 8px 10px;
             font-size: 12pt; border-radius: 3px; }}
QLineEdit:focus {{ border-color: {CRIMSON}; }}
QPushButton {{ background: {PANEL}; border: 1px solid {BORDER}; padding: 8px 16px;
               font-family: Rajdhani; font-size: 11pt; font-weight: 700; letter-spacing: 1px; }}
QPushButton:hover {{ border-color: {CRIMSON}; }}
QPushButton#primary {{ background: {CRIMSON}; border-color: {CRIMSON}; }}
QPushButton:disabled {{ color: {MUTED}; }}
QListWidget, QTextBrowser {{ background: {PANEL}; border: 1px solid {BORDER}; }}
QListWidget::item {{ padding: 8px; border-bottom: 1px solid {BORDER}; }}
QListWidget::item:selected {{ background: #3A0410; border-left: 3px solid {CRIMSON}; }}
QSplitter::handle {{ background: {BG}; }}
"""


class Task(QThread):
    done = Signal(object, str)

    def __init__(self, fn) -> None:
        super().__init__()
        self.fn = fn

    def run(self) -> None:
        try:
            self.done.emit(self.fn(), "")
        except Exception as exc:  # shown in the status line; the app keeps running
            self.done.emit(None, f"{type(exc).__name__}: {exc}")


class Card(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__(objectName="card")
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 10, 12, 10)
        v.addWidget(QLabel(title.upper(), objectName="cardTitle"))
        self.value = QLabel("—", objectName="cardValue")
        self.detail = QLabel("", objectName="muted", wordWrap=True)
        v.addWidget(self.value)
        v.addWidget(self.detail)

    def set(self, value: str, detail: str = "", color: str = FG) -> None:
        self.value.setText(value)
        self.value.setStyleSheet(f"color: {color};")
        self.detail.setText(detail)


class MainWindow(QMainWindow):
    def __init__(self, gc: GameCheck | None = None) -> None:
        super().__init__()
        self.gc = gc or GameCheck()
        self.distro = distro.detect()
        self._tasks: set[Task] = set()
        self.report: Report | None = None
        self.setWindowTitle(APP_NAME)
        self.resize(1280, 820)
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 22, 28, 18)
        outer.setSpacing(14)

        head = QVBoxLayout()
        head.addWidget(QLabel("THE VOID GAMECHECK", objectName="title"))
        head.addWidget(QLabel("How well does a game run on Linux? Native support, ProtonDB, "
                              f"Steam Deck and Lutris in one answer · {self.distro.name}",
                              objectName="subtitle"))
        outer.addLayout(head)

        bar = QHBoxLayout()
        self.query = QLineEdit(placeholderText="Search a game, e.g. Elden Ring, Hades, Dota 2")
        self.query.returnPressed.connect(self.search)
        self.go = QPushButton("SEARCH", objectName="primary")
        self.go.clicked.connect(self.search)
        bar.addWidget(self.query, 1)
        bar.addWidget(self.go)
        outer.addLayout(bar)

        split = QSplitter()
        self.results = QListWidget()
        self.results.setMinimumWidth(320)
        self.results.currentItemChanged.connect(lambda *_: self._selected())
        split.addWidget(self.results)
        split.addWidget(self._build_detail())
        split.setSizes([380, 900])
        outer.addWidget(split, 1)
        self.status = QLabel(objectName="muted")
        outer.addWidget(self.status)
        self._show_empty()

    def _build_detail(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(12, 0, 0, 0)
        top = QHBoxLayout()
        names = QVBoxLayout()
        self.name = QLabel(objectName="gameName", wordWrap=True)
        self.meta = QLabel(objectName="muted")
        names.addWidget(self.name)
        names.addWidget(self.meta)
        top.addLayout(names, 1)
        self.refresh_btn = QPushButton("REFRESH")
        self.refresh_btn.setToolTip("Fetch fresh data (results are cached for 24 hours)")
        self.refresh_btn.clicked.connect(lambda: self._load_report(refresh=True))
        top.addWidget(self.refresh_btn)
        v.addLayout(top)
        self.verdict = QLabel(objectName="verdict")
        self.summary = QLabel(wordWrap=True)
        v.addWidget(self.verdict)
        v.addWidget(self.summary)
        grid = QGridLayout()
        grid.setSpacing(10)
        self.cards = {k: Card(t) for k, t in (("native", "Native Linux"),
                                              ("proton", "ProtonDB"),
                                              ("deck", "Steam Deck"), ("lutris", "Lutris"))}
        for i, card in enumerate(self.cards.values()):
            grid.addWidget(card, 0, i)
        v.addLayout(grid)
        self.body = QTextBrowser(openLinks=False)
        self.body.anchorClicked.connect(lambda url: QDesktopServices.openUrl(url))
        v.addWidget(self.body, 1)
        return box

    # ---- actions -----------------------------------------------------------------------

    def _run(self, fn, on_done) -> None:
        task = Task(fn)
        task.done.connect(on_done)
        task.finished.connect(lambda t=task: (self._tasks.discard(t), t.deleteLater()))
        self._tasks.add(task)
        task.start()

    def search(self) -> None:
        term = self.query.text().strip()
        if not term:
            return
        self.go.setEnabled(False)
        self.status.setText(f"Searching Steam for “{term}”…")
        self._run(lambda: self.gc.search(term), self._searched)

    def _searched(self, hits, error: str) -> None:
        self.go.setEnabled(True)
        self.results.clear()
        if error:
            self.status.setText(f"⚠ Search failed: {error}")
            return
        for h in hits or []:
            tag = "NATIVE LINUX" if h.linux else "WINDOWS · PROTON"
            item = QListWidgetItem(f"{h.name}\n{tag}")
            item.setData(256, (h.appid, h.name))
            self.results.addItem(item)
        self.status.setText(f"{len(hits or [])} game(s). Select one to check it.")
        if hits:
            self.results.setCurrentRow(0)

    def _selected(self) -> None:
        if self.results.currentItem():
            self._load_report()

    def _load_report(self, *, refresh: bool = False) -> None:
        item = self.results.currentItem()
        if item is None:
            return
        appid, name = item.data(256)
        self.refresh_btn.setEnabled(False)
        self.status.setText(f"Checking {name} on Steam, ProtonDB, Steam Deck and Lutris…")
        self._run(lambda: self.gc.report(appid, name, refresh=refresh), self._reported)

    def _reported(self, report: Report | None, error: str) -> None:
        self.refresh_btn.setEnabled(True)
        if error or report is None:
            self.status.setText(f"⚠ {error or 'No data'}")
            return
        cur = self.results.currentItem()
        if cur is not None and cur.data(256)[0] != report.appid:
            return          # a newer selection is loading
        self.report = report
        self.show_report(report)
        when = time.strftime("%H:%M", time.localtime(report.checked_at))
        self.status.setText(f"Checked {when}" + (f" · some sources failed: "
                                                 f"{', '.join(report.errors)}"
                                                 if report.errors else ""))

    # ---- rendering ---------------------------------------------------------------------

    def _show_empty(self) -> None:
        self.name.setText("Search for a game")
        self.meta.setText("")
        self.verdict.setText("")
        self.summary.setText("The verdict combines four public sources and explains why. "
                             "Setup steps are tailored to your distribution.")
        for c in self.cards.values():
            c.set("—")
        self.refresh_btn.setEnabled(False)
        self.body.setHtml("")

    def show_report(self, r: Report) -> None:
        v = r.verdict
        steam = r.steam or {}
        self.name.setText(r.name)
        self.meta.setText(" · ".join(x for x in (f"Steam app {r.appid}",
                                                 ", ".join(steam.get("developers") or []),
                                                 steam.get("release_date", "")) if x))
        self.verdict.setText(v.label + ("  ·  NATIVE" if v.how == "native" else
                                        "  ·  VIA PROTON" if v.how == "proton" else ""))
        self.verdict.setStyleSheet(f"color: {LEVEL_COLORS[v.label]};")
        self.summary.setText(v.summary)
        self.cards["native"].set("YES" if r.native else "NO" if r.steam else "—",
                                 "Linux build on Steam" if r.native else "Windows build",
                                 GREEN if r.native else FG)
        p = r.proton or {}
        tier = (p.get("tier") or "").upper()
        self.cards["proton"].set(tier or "NO DATA",
                                 f"{p.get('total', 0):,} reports · {p.get('confidence', '')}"
                                 if tier else "not enough reports",
                                 {"PLATINUM": GREEN, "GOLD": GREEN, "SILVER": AMBER,
                                  "BRONZE": AMBER, "BORKED": RED}.get(tier, MUTED))
        deck = (r.deck or "unknown").upper()
        self.cards["deck"].set(deck, "Valve's SteamOS test",
                               {"VERIFIED": GREEN, "PLAYABLE": AMBER,
                                "UNSUPPORTED": RED}.get(deck, MUTED))
        n = len((r.lutris or {}).get("installers") or [])
        self.cards["lutris"].set(f"{n} SCRIPT{'S' if n != 1 else ''}" if r.lutris else "NONE",
                                 "install scripts" if r.lutris else "not on Lutris",
                                 GREEN if n else MUTED)
        reasons = "".join(f"<li>{E(x)}</li>" for x in v.reasons)
        errors = "".join(f"<li style='color:{AMBER}'>{E(k)}: {E(e)}</li>"
                         for k, e in r.errors.items())
        links = " &nbsp;·&nbsp; ".join(f"<a style='color:{CRIMSON}' href='{E(u)}'>{E(k)}</a>"
                                       for k, u in r.links.items())
        tips = distro.tips(self.distro, how=v.how, level=v.level, has_lutris=bool(r.lutris))
        tips_html = "<br>".join(
            f"<span style='font-family:JetBrains Mono;color:{FG}'>{E(t.strip())}</span>"
            if t.startswith("  ") else E(t) for t in tips)
        # Steam sends a stub for Windows-only games; show requirements for native builds only.
        req = steam.get("linux_requirements") if r.native else ""
        desc = steam.get("short_description")
        self.body.setHtml(
            f"<h3 style='color:{CRIMSON}'>WHY</h3><ul>{reasons}{errors}</ul>"
            f"<p>{links}</p>"
            f"<h3 style='color:{CRIMSON}'>SET UP ON YOUR SYSTEM</h3><p>{tips_html}</p>"
            + (f"<h3 style='color:{CRIMSON}'>LINUX REQUIREMENTS</h3><p>"
               f"{E(req).replace(chr(10), '<br>')}</p>" if req else "")
            + (f"<h3 style='color:{CRIMSON}'>ABOUT</h3><p style='color:{MUTED}'>{E(desc)}</p>"
               if desc else "")
            + f"<p style='color:{MUTED};font-size:8pt'>Sources: Steam store, ProtonDB "
              "(community reports), Steam Deck compatibility (Valve), Lutris. Results are "
              "cached for 24 hours.</p>")

    def closeEvent(self, event) -> None:  # noqa: N802
        for task in list(self._tasks):
            task.wait(15000)
        self.gc.close()
        super().closeEvent(event)


def load_fonts() -> None:
    for f in files("void_gamecheck").joinpath("assets", "fonts").iterdir():
        if f.name.endswith(".ttf"):
            QFontDatabase.addApplicationFont(str(f))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    if "--version" in argv:
        print(f"the-void-gamecheck {__version__}")
        return 0
    QApplication.setApplicationName("the-void-gamecheck")
    QApplication.setApplicationDisplayName(APP_NAME)
    QApplication.setDesktopFileName(APP_ID)
    app = QApplication.instance() or QApplication(argv)
    load_fonts()
    app.setStyleSheet(QSS)
    app.setWindowIcon(QIcon(str(files("void_gamecheck").joinpath("assets",
                                                                  f"{APP_ID}.svg"))))
    win = MainWindow()
    win.show()
    for a in argv[1:]:
        if not a.startswith("-"):
            win.query.setText(" ".join(x for x in argv[1:] if not x.startswith("-")))
            QTimer.singleShot(0, win.search)
            break
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
