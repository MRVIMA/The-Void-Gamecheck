#!/usr/bin/env bash
# Add THE VOID GAMECHECK to the application menu for this user (no root needed).
#   bash scripts/install-desktop.sh                       from this source folder
#   bash scripts/install-desktop.sh --appimage FILE       install a built AppImage
#   bash scripts/install-desktop.sh --remove              uninstall
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ID="com.thevoid.GameCheck"
BIN="$HOME/.local/bin"
APPS="$HOME/.local/share/applications"
ICONS="$HOME/.local/share/icons/hicolor"

if [ "${1:-}" = "--remove" ]; then
    rm -f "$BIN/the-void-gamecheck" "$BIN/gamecheck" "$APPS/$APP_ID.desktop" \
          "$HOME/Applications"/THE-VOID-GAMECHECK-*.AppImage
    rm -f "$ICONS"/*/apps/"$APP_ID".*
    command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 >/dev/null 2>&1 || true
    echo "Removed. (Cached data: ~/.cache/the-void-gamecheck)"
    exit 0
fi

mkdir -p "$BIN" "$APPS" "$ICONS"
rm -f "$BIN/the-void-gamecheck" "$BIN/gamecheck"
if [ "${1:-}" = "--appimage" ]; then
    SRC="$(readlink -f "${2:?give the AppImage file}")"
    mkdir -p "$HOME/Applications"
    rm -f "$HOME/Applications"/THE-VOID-GAMECHECK-*.AppImage
    TARGET="$HOME/Applications/$(basename "$SRC")"
    cp "$SRC" "$TARGET"
    chmod +x "$TARGET"
    ln -s "$TARGET" "$BIN/the-void-gamecheck"
    ln -s "$TARGET" "$BIN/gamecheck"          # called as "gamecheck" → terminal mode
else
    [ -x "$ROOT/.venv/bin/python" ] || bash "$ROOT/scripts/setup.sh"
    # Launchers point at this source folder's environment.
    printf '#!/bin/sh\nexec "%s/.venv/bin/python" -m void_gamecheck.app "$@"\n' "$ROOT" \
        > "$BIN/the-void-gamecheck"
    printf '#!/bin/sh\nexec "%s/.venv/bin/python" -m void_gamecheck "$@"\n' "$ROOT" \
        > "$BIN/gamecheck"
    chmod +x "$BIN/the-void-gamecheck" "$BIN/gamecheck"
fi
sed "s|^Exec=.*|Exec=$BIN/the-void-gamecheck|" "$ROOT/data/$APP_ID.desktop" > "$APPS/$APP_ID.desktop"
cp -r "$ROOT/data/icons/hicolor/." "$ICONS/"
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 >/dev/null 2>&1 || true
echo "Installed: application menu → THE VOID GAMECHECK;  terminal: gamecheck \"game name\""
