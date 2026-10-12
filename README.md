<div align="center">

<img src="void_gamecheck/assets/com.thevoid.GameCheck.svg" width="104" alt="THE VOID GAMECHECK icon">

# THE VOID GAMECHECK

**How well does a game run on Linux? One search, one clear answer, with the reasons and the setup steps for your distro.**

CachyOS / Arch Linux · works on any distro · Python · Qt 6

![Version](https://img.shields.io/badge/version-1.0.0-D90429)
![Platform](https://img.shields.io/badge/platform-Linux-08090D)
![License](https://img.shields.io/badge/license-MIT-08090D)

</div>

---

## What it checks

| Source | What it tells you |
|---|---|
| **Steam store** | Whether the game has a **native Linux** version (and its Linux requirements) |
| **ProtonDB** | Community rating for running the Windows version through **Proton**: Platinum, Gold, Silver, Bronze or Borked, with the number of reports |
| **Steam Deck** | Valve's own test result: **Verified**, **Playable** or **Unsupported**. The Deck runs SteamOS, which is Linux, so this is a strong signal |
| **Lutris** | Whether community **install scripts** exist (handy for GOG, Epic and other non-Steam copies) |

These are combined into one **Linux outlook**: EXCELLENT, GOOD, PLAYABLE, POOR, UNLIKELY,
BROKEN or UNKNOWN. You also see each reason behind it and links to every source.

**Setup tips for your system.** The app reads `/etc/os-release` and shows the right
commands for CachyOS, Arch-based distros, Fedora, Debian / Ubuntu, openSUSE, or Flatpak
elsewhere. They cover installing Steam, enabling Proton, Proton-GE for difficult games, and
Lutris.

## Install

### AppImage (any distro)

Download `THE-VOID-GAMECHECK-1.0.0-x86_64.AppImage` from the Releases page, then:

```bash
chmod +x THE-VOID-GAMECHECK-1.0.0-x86_64.AppImage
./THE-VOID-GAMECHECK-1.0.0-x86_64.AppImage                    # desktop app
./THE-VOID-GAMECHECK-1.0.0-x86_64.AppImage cli "elden ring"   # terminal mode
```

To add it to the application menu, with a `gamecheck` terminal command (from a clone of this
repository):

```bash
bash scripts/install-desktop.sh --appimage THE-VOID-GAMECHECK-1.0.0-x86_64.AppImage
```

### Arch Linux / CachyOS package

```bash
git clone https://github.com/MRVIMA/the-void-gamecheck.git
cd the-void-gamecheck/packaging/arch
makepkg -si
```

It uses the system's `pyside6` and `python-httpx`, all from the official repositories.

### From source

```bash
sudo pacman -S --needed python pyside6
bash scripts/install-desktop.sh       # runs from this folder; adds the menu entry
```

Remove any of these with `bash scripts/install-desktop.sh --remove`.

## Use from the terminal

```bash
gamecheck "elden ring"          # verdict, reasons, links and setup tips
gamecheck --list witcher        # every match: native Linux or Windows → Proton
gamecheck --appid 570           # by Steam app id
gamecheck --json "hades"        # machine-readable
gamecheck --refresh "hades"     # ignore the 24-hour cache
```

Example:

```
ELDEN RING  (Steam app 1245620)
  GOOD — Works well on Linux.  [via Proton]
   • ProtonDB: GOLD — runs perfectly after small tweaks (2,105 reports, strong confidence).
   • Recent reports trend towards PLATINUM.
   • Steam Deck: Verified — the Deck runs SteamOS (Linux), a strong sign.
   • Lutris: 2 install script(s) (steam).
```

## Good to know

- Results are cached for 24 hours in `~/.cache/the-void-gamecheck/`. Use **REFRESH** (or
  `--refresh`) for fresh data.
- ProtonDB ratings are community reports and Steam Deck results are Valve's tests. Both are
  strong guides, not guarantees, especially for brand-new releases and online games.
- Only public endpoints are used, at a polite pace (one look-up = a handful of requests). No
  account and no API key are needed.

## Development

```bash
bash scripts/setup.sh           # .venv with the system PySide6, editable install
bash scripts/run.sh             # desktop app from source
bash scripts/test.sh            # lint + tests (all sources mocked; no internet needed)
USE_SYSTEM_PYSIDE=1 bash packaging/appimage/build-appimage.sh   # build the AppImage
```

Build release AppImages on an old base system (e.g. Ubuntu 22.04, without
`USE_SYSTEM_PYSIDE`) so they run on most distributions.

| Module | Purpose |
|---|---|
| `void_gamecheck/sources.py` | Steam, ProtonDB, Steam Deck and Lutris clients |
| `void_gamecheck/verdict.py` | Combines them into the Linux outlook with reasons |
| `void_gamecheck/distro.py` | Distro detection and setup tips |
| `void_gamecheck/service.py` | Parallel look-ups, cache, per-source errors |
| `void_gamecheck/cli.py`, `app.py` | Terminal tool and desktop app |

## Credits

A **THE VOID** project by **THE VOID PROTOCOL** · Owner of THE VOID: **MRVIMA** (alias **VOIDVIMA**)

Data: [Steam](https://store.steampowered.com), [ProtonDB](https://www.protondb.com),
[Lutris](https://lutris.net). THE VOID GAMECHECK isn't affiliated with Valve, ProtonDB or Lutris.
Fonts: Rajdhani, Inter, JetBrains Mono (SIL Open Font License; licenses in `void_gamecheck/assets/fonts/`).

## License

[MIT](LICENSE) © 2026 THE VOID PROTOCOL
