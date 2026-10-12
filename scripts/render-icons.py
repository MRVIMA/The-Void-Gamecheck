"""Render the SVG app icon to the PNG sizes desktops expect (data/icons/hicolor)."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parent.parent
APP_ID = "com.thevoid.GameCheck"
SVG = ROOT / "void_gamecheck" / "assets" / f"{APP_ID}.svg"

app = QGuiApplication(sys.argv[:1])
renderer = QSvgRenderer(str(SVG))
for size in (16, 24, 32, 48, 64, 128, 256, 512):
    out = ROOT / "data" / "icons" / "hicolor" / f"{size}x{size}" / "apps" / f"{APP_ID}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    img.save(str(out))
scalable = ROOT / "data" / "icons" / "hicolor" / "scalable" / "apps" / f"{APP_ID}.svg"
scalable.parent.mkdir(parents=True, exist_ok=True)
scalable.write_bytes(SVG.read_bytes())
print("icons written to", ROOT / "data" / "icons" / "hicolor")
