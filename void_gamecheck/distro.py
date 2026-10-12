"""Detect the Linux distribution and give matching, verified setup steps."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Distro:
    id: str
    name: str
    family: str          # arch, fedora, debian, suse, other


def detect(os_release: str | None = None) -> Distro:
    if os_release is None:
        try:
            os_release = Path("/etc/os-release").read_text()
        except OSError:
            os_release = ""
    info = {}
    for line in os_release.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            info[k] = v.strip().strip('"')
    ids = [info.get("ID", "").lower(), *info.get("ID_LIKE", "").lower().split()]
    family = next((f for f, keys in (("arch", ("arch",)), ("fedora", ("fedora", "rhel")),
                                     ("debian", ("debian", "ubuntu")),
                                     ("suse", ("suse", "opensuse", "opensuse-tumbleweed")))
                   if any(i in keys or i.startswith(keys) for i in ids if i)), "other")
    return Distro(ids[0] or "linux", info.get("PRETTY_NAME") or info.get("NAME") or "Linux",
                  family)


STEAM = {
    "cachyos": ["sudo pacman -S --needed steam cachyos-gaming-meta",
                "(cachyos-gaming-meta adds proton-cachyos-slr, umu-launcher, protontricks and "
                "the 32-bit libraries games need)"],
    "arch": ["Enable [multilib] in /etc/pacman.conf, then:", "sudo pacman -S steam"],
    "fedora": ["Enable RPM Fusion (free + nonfree), then:", "sudo dnf install steam"],
    "debian": ["Ubuntu: sudo apt install steam-installer",
               "Debian: enable contrib/non-free and i386 (sudo dpkg --add-architecture i386), "
               "then sudo apt install steam-installer"],
    "suse": ["sudo zypper install steam"],
    "other": ["flatpak install flathub com.valvesoftware.Steam"],
}
LUTRIS = {"arch": "sudo pacman -S lutris", "fedora": "sudo dnf install lutris",
          "debian": "flatpak install flathub net.lutris.Lutris",
          "suse": "sudo zypper install lutris",
          "other": "flatpak install flathub net.lutris.Lutris"}
PROTON_TOOLS = {"cachyos": "sudo pacman -S protonup-qt   (installs Proton-GE and others)",
                "arch": "flatpak install flathub net.davidotek.pupgui2   (ProtonUp-Qt)"}


def tips(d: Distro, *, how: str, level: int | None, has_lutris: bool) -> list[str]:
    """Practical steps for this distro and this game's situation."""
    out = [f"Your system: {d.name}"]
    out += ["Install Steam:"] + [f"  {s}" for s in STEAM.get(d.id) or STEAM.get(d.family)
                                  or STEAM["other"]]
    if how == "native":
        out.append("This game has a native Linux build: install it from Steam as usual.")
    elif how == "proton" or level is None:
        out.append("Run it with Proton: Steam → Settings → Compatibility → "
                   "\"Enable Steam Play for all other titles\".")
        if level is not None and level <= 3:
            out.append("If it misbehaves, try another Proton version: game → Properties → "
                       "Compatibility (Proton Experimental, or Proton-GE).")
            tool = PROTON_TOOLS.get(d.id) or PROTON_TOOLS.get(d.family)
            if tool:
                out.append(f"  {tool}")
            out.append("Read the newest reports on the game's ProtonDB page for fixes and "
                       "launch options.")
    if has_lutris:
        out.append(f"Lutris (for non-Steam versions): {LUTRIS.get(d.family, LUTRIS['other'])}")
    if d.family == "arch":
        out.append("NVIDIA GPU? Also install the 32-bit driver: sudo pacman -S lib32-nvidia-utils")
    return out
