"""Autostart: XDG + systemd (Linux), LaunchAgent (macOS), Startup (Windows)."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

from utils.install import is_bundled, project_root

DESKTOP_NAME = "kps.desktop"
SYSTEMD_UNIT = "kps.service"
LAUNCH_AGENT = "io.github.alanjmrt94.kps.plist"
WINDOWS_STARTUP_BAT = "kps-autostart.bat"


def launch_command() -> list[str]:
    """Comando para relanzar kps (prioriza la ruta del AppImage)."""
    appimage = os.environ.get("APPIMAGE")
    extra = ["--tray", "--foreground"]
    if appimage:
        return [appimage, *extra]
    if is_bundled():
        return [str(Path(sys.executable).resolve()), *extra]
    python = sys.executable
    script = str(project_root() / "kps.py")
    return [python, script, *extra]


def quoted_exec(cmd: list[str]) -> str:
    """Línea Exec= / ExecStart= con quoting seguro."""
    return " ".join(shlex.quote(part) for part in cmd)


def xdg_autostart_path() -> Path:
    """~/.config/autostart/kps.desktop."""
    base = os.environ.get("XDG_CONFIG_HOME")
    config = Path(base) if base else Path.home() / ".config"
    return config / "autostart" / DESKTOP_NAME


def systemd_user_path() -> Path:
    """~/.config/systemd/user/kps.service."""
    base = os.environ.get("XDG_CONFIG_HOME")
    config = Path(base) if base else Path.home() / ".config"
    return config / "systemd" / "user" / SYSTEMD_UNIT


def macos_launch_agent_path() -> Path:
    """~/Library/LaunchAgents/...plist."""
    return Path.home() / "Library" / "LaunchAgents" / LAUNCH_AGENT


def windows_startup_path() -> Path:
    """Carpeta Inicio de Windows."""
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return (
        Path(appdata)
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "Startup"
        / WINDOWS_STARTUP_BAT
    )


def desktop_entry(cmd: list[str]) -> str:
    """Contenido .desktop para autostart gráfico."""
    exec_line = quoted_exec(cmd)
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=kps\n"
        "Comment=Evita inactividad cuando estás ausente\n"
        f"Exec={exec_line}\n"
        "Terminal=false\n"
        "Categories=Utility;\n"
        "X-GNOME-Autostart-enabled=true\n"
    )


def systemd_unit(cmd: list[str]) -> str:
    """Unidad systemd --user para el AppImage o kps.py."""
    exec_line = quoted_exec(cmd)
    return (
        "[Unit]\n"
        "Description=kps — evita inactividad\n"
        "After=graphical-session.target\n"
        "PartOf=graphical-session.target\n"
        "\n"
        "[Service]\n"
        "Type=simple\n"
        f"ExecStart={exec_line}\n"
        "Restart=on-failure\n"
        "RestartSec=5\n"
        "\n"
        "[Install]\n"
        "WantedBy=graphical-session.target\n"
    )


def macos_plist(cmd: list[str]) -> str:
    """LaunchAgent macOS."""
    args = "".join(f"        <string>{_xml_escape(part)}</string>\n" for part in cmd)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "<dict>\n"
        "    <key>Label</key>\n"
        f"    <string>{LAUNCH_AGENT.replace('.plist', '')}</string>\n"
        "    <key>ProgramArguments</key>\n"
        "    <array>\n"
        f"{args}"
        "    </array>\n"
        "    <key>RunAtLoad</key>\n"
        "    <true/>\n"
        "    <key>KeepAlive</key>\n"
        "    <false/>\n"
        "</dict>\n"
        "</plist>\n"
    )


def _xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def windows_bat(cmd: list[str]) -> str:
    """Script de Inicio en Windows."""
    return f"@echo off\nstart \"\" {quoted_exec(cmd)}\n"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _remove(path: Path) -> bool:
    if path.is_file():
        path.unlink()
        return True
    return False


def _systemctl_user(*args: str) -> bool:
    try:
        subprocess.run(
            ["systemctl", "--user", *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False


def enable_linux() -> list[str]:
    """Instala autostart XDG y unidad systemd de usuario."""
    cmd = launch_command()
    notes: list[str] = []
    desktop = xdg_autostart_path()
    _write(desktop, desktop_entry(cmd))
    notes.append(f"XDG: {desktop}")
    unit = systemd_user_path()
    _write(unit, systemd_unit(cmd))
    notes.append(f"systemd: {unit}")
    if _systemctl_user("daemon-reload") and _systemctl_user("enable", "--now", SYSTEMD_UNIT):
        notes.append("systemctl --user enable --now kps.service")
    else:
        notes.append(
            "systemd no disponible o sin sesión; el .desktop de XDG basta al iniciar sesión."
        )
    return notes


def disable_linux() -> list[str]:
    """Quita autostart Linux."""
    notes: list[str] = []
    _systemctl_user("disable", "--now", SYSTEMD_UNIT)
    if _remove(systemd_user_path()):
        notes.append(f"eliminado {systemd_user_path()}")
    if _remove(xdg_autostart_path()):
        notes.append(f"eliminado {xdg_autostart_path()}")
    if not notes:
        notes.append("no había archivos de autostart")
    return notes


def enable_macos() -> list[str]:
    """Instala LaunchAgent."""
    path = macos_launch_agent_path()
    _write(path, macos_plist(launch_command()))
    try:
        subprocess.run(
            ["launchctl", "load", str(path)],
            check=False,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass
    return [f"LaunchAgent: {path}"]


def disable_macos() -> list[str]:
    """Quita LaunchAgent."""
    path = macos_launch_agent_path()
    try:
        subprocess.run(
            ["launchctl", "unload", str(path)],
            check=False,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass
    if _remove(path):
        return [f"eliminado {path}"]
    return ["no había LaunchAgent"]


def enable_windows() -> list[str]:
    """Instala script en la carpeta Inicio."""
    path = windows_startup_path()
    _write(path, windows_bat(launch_command()))
    return [f"Inicio: {path}"]


def disable_windows() -> list[str]:
    """Quita el script de Inicio."""
    path = windows_startup_path()
    if _remove(path):
        return [f"eliminado {path}"]
    return ["no había script de Inicio"]


def status_paths() -> list[tuple[str, Path, bool]]:
    """Rutas relevantes según la plataforma."""
    if sys.platform == "darwin":
        path = macos_launch_agent_path()
        return [("LaunchAgent", path, path.is_file())]
    if sys.platform == "win32":
        path = windows_startup_path()
        return [("Inicio", path, path.is_file())]
    return [
        ("XDG", xdg_autostart_path(), xdg_autostart_path().is_file()),
        ("systemd", systemd_user_path(), systemd_user_path().is_file()),
    ]


def run_autostart(action: str) -> int:
    """enable / disable / status. Código 0 si ok."""
    action = (action or "status").strip().lower()
    if action not in ("enable", "disable", "status"):
        sys.stderr.write("Uso: kps autostart enable|disable|status\n")
        return 2

    if action == "status":
        print(f"Comando: {quoted_exec(launch_command())}")
        for label, path, exists in status_paths():
            mark = "sí" if exists else "no"
            print(f"{label}: {mark} ({path})")
        return 0

    if sys.platform == "darwin":
        notes = enable_macos() if action == "enable" else disable_macos()
    elif sys.platform == "win32":
        notes = enable_windows() if action == "enable" else disable_windows()
    else:
        notes = enable_linux() if action == "enable" else disable_linux()

    verb = "Autostart activado" if action == "enable" else "Autostart desactivado"
    print(verb)
    for note in notes:
        print(f"  {note}")
    return 0
