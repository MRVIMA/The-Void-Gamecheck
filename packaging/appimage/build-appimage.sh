#!/usr/bin/env bash
# Build THE-VOID-GAMECHECK-<version>-x86_64.AppImage.
#
#   bash packaging/appimage/build-appimage.sh
#
# For an AppImage that runs on most distros, build on an OLD base system (e.g. Ubuntu 22.04):
# an AppImage only runs where glibc is at least as new as the build host's.
#   USE_SYSTEM_PYSIDE=1   reuse the distro's PySide6 instead of downloading it (local builds)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
APP_ID="com.thevoid.GameCheck"
VERSION="$(python3 -c "import re;print(re.search(r'__version__ = \"(.+?)\"', open('void_gamecheck/__init__.py').read())[1])")"
ARCH="x86_64"
BUILD="$ROOT/build/appimage"
APPDIR="$BUILD/AppDir"
OUT="$ROOT/dist/THE-VOID-GAMECHECK-$VERSION-$ARCH.AppImage"

step() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
mkdir -p "$BUILD/tools" "$ROOT/dist"

step "Python environment"
venv_args=()
[ "${USE_SYSTEM_PYSIDE:-0}" = 1 ] && venv_args+=(--system-site-packages)
[ -x "$BUILD/venv/bin/python" ] || python3 -m venv "${venv_args[@]}" "$BUILD/venv"
"$BUILD/venv/bin/python" -m pip install -q --upgrade pip
extra=()
[ "${USE_SYSTEM_PYSIDE:-0}" = 1 ] || extra+=("PySide6>=6.8")
"$BUILD/venv/bin/python" -m pip install -q "$ROOT" pyinstaller "${extra[@]}"

step "PyInstaller"
"$BUILD/venv/bin/pyinstaller" --noconfirm --clean --log-level WARN \
    --distpath "$BUILD/dist" --workpath "$BUILD/work" packaging/pyinstaller/the-void-gamecheck.spec
"$BUILD/dist/the-void-gamecheck/the-void-gamecheck" --version

step "AppDir"
rm -rf "$APPDIR"
LIB="$APPDIR/usr/lib/the-void-gamecheck"
mkdir -p "$APPDIR/usr/lib" "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons"
cp -a "$BUILD/dist/the-void-gamecheck" "$LIB"
ln -s ../lib/the-void-gamecheck/the-void-gamecheck "$APPDIR/usr/bin/the-void-gamecheck"
install -m755 packaging/appimage/AppRun "$APPDIR/AppRun"
install -m644 "data/$APP_ID.desktop" "$APPDIR/$APP_ID.desktop"
install -m644 "data/$APP_ID.desktop" "$APPDIR/usr/share/applications/"
cp -r data/icons/hicolor "$APPDIR/usr/share/icons/"
install -m644 "data/icons/hicolor/scalable/apps/$APP_ID.svg" "$APPDIR/$APP_ID.svg"
install -m644 "data/icons/hicolor/256x256/apps/$APP_ID.png" "$APPDIR/.DirIcon"
install -m644 LICENSE "$LIB/LICENSE"

step "appimagetool"
TOOL="$BUILD/tools/appimagetool"
if [ ! -x "$TOOL" ]; then
    curl -fL --retry 3 -o "$TOOL" \
        "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$ARCH.AppImage"
    chmod +x "$TOOL"
fi
ARCH=$ARCH "$TOOL" --appimage-extract-and-run --no-appstream "$APPDIR" "$OUT"

step "Done"
ls -lh "$OUT"
