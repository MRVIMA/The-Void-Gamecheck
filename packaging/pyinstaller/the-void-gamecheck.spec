# PyInstaller one-folder build used by the AppImage.
import os

from PyInstaller.utils.hooks import collect_data_files

ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))

a = Analysis(
    [os.path.join(SPECPATH, "launch.py")],
    pathex=[ROOT],
    datas=collect_data_files("void_gamecheck") + collect_data_files("certifi"),
    hiddenimports=["void_gamecheck.app", "void_gamecheck.cli", "h2"],
    excludes=["tkinter", "pytest", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
              "PySide6.Qt3DCore", "PySide6.QtQuick3D", "PySide6.QtMultimedia",
              "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtPdf",
              "PySide6.QtBluetooth", "PySide6.QtLocation", "PySide6.QtQml", "PySide6.QtQuick"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="the-void-gamecheck",
          console=False, strip=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="the-void-gamecheck")
