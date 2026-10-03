"""Diagnóstico de entorno: sesión, idle D-Bus, uinput, AppImage."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import grp
except ImportError:  # pragma: no cover - Windows
    grp = None  # type: ignore[assignment]

from utils.const import Version
from utils.install import is_bundled, project_root


@dataclass
class CheckResult:
    """Resultado de una comprobación de ``kps doctor``."""

    name: str
    ok: bool
    detail: str
    hint: str = ""
    optional: bool = False


def _ok(name: str, detail: str, hint: str = "", optional: bool = False) -> CheckResult:
    return CheckResult(name, True, detail, hint, optional)


def _fail(name: str, detail: str, hint: str = "", optional: bool = False) -> CheckResult:
    return CheckResult(name, False, detail, hint, optional)


def check_python() -> CheckResult:
    """Versión de Python."""
    version = sys.version.split()[0]
    if sys.version_info < (3, 10):
        return _fail("Python", version, "kps requiere Python 3.10 o superior.")
    return _ok("Python", version)


def check_session() -> CheckResult:
    """Tipo de sesión gráfica."""
    session = os.environ.get("XDG_SESSION_TYPE") or "desconocido"
    display = os.environ.get("DISPLAY") or "-"
    wayland = os.environ.get("WAYLAND_DISPLAY") or "-"
    detail = f"tipo={session} DISPLAY={display} WAYLAND_DISPLAY={wayland}"
    if sys.platform == "linux" and session == "wayland" and wayland == "-":
        return _fail("Sesión", detail, "Sesión Wayland sin WAYLAND_DISPLAY.")
    return _ok("Sesión", detail)


def check_dbus_clients() -> CheckResult:
    """Clientes D-Bus en PATH."""
    found = [name for name in ("gdbus", "busctl", "dbus-send") if shutil.which(name)]
    if not found:
        return _fail(
            "D-Bus (cliente)",
            "ninguno",
            "Instala libglib2.0-bin (gdbus) o dbus (busctl/dbus-send).",
        )
    return _ok("D-Bus (cliente)", ", ".join(found))


def check_dbus_idle() -> CheckResult:
    """Servicios idle por D-Bus (no bloquea si no hay sesión gráfica)."""
    if sys.platform != "linux":
        return _ok("Idle D-Bus", "no aplica", optional=True)
    try:
        from utils.dbus_idle import (  # pylint: disable=import-outside-toplevel
            DBusIdleError,
            get_session_idle_ms,
        )
    except ImportError as error:
        return _fail("Idle D-Bus", str(error), optional=True)

    probes = (
        (
            "Mutter",
            "org.gnome.Mutter.IdleMonitor",
            "/org/gnome/Mutter/IdleMonitor/Core",
            "org.gnome.Mutter.IdleMonitor",
            "GetIdletime",
        ),
        (
            "freedesktop",
            "org.freedesktop.ScreenSaver",
            "/org/freedesktop/ScreenSaver",
            "org.freedesktop.ScreenSaver",
            "GetSessionIdleTime",
        ),
        (
            "MATE",
            "org.mate.ScreenSaver",
            "/org/mate/ScreenSaver",
            "org.mate.ScreenSaver",
            "GetSessionIdleTime",
        ),
    )
    working: list[str] = []
    last_error = ""
    for label, dest, path, iface, method in probes:
        try:
            idle_ms = get_session_idle_ms(dest, path, iface, method)
            working.append(f"{label} ({idle_ms} ms)")
        except (OSError, DBusIdleError) as error:
            last_error = str(error)
    if working:
        return _ok("Idle D-Bus", "; ".join(working))
    session = os.environ.get("XDG_SESSION_TYPE", "")
    hint = "En Wayland hace falta un compositor con idle D-Bus; en X11 hay fallback XScreenSaver."
    optional = session != "wayland"
    return _fail("Idle D-Bus", last_error or "ningún servicio respondió", hint, optional=optional)


def _user_groups() -> list[tuple[str, int]]:
    """Grupos del usuario actual (nombre, gid)."""
    result: list[tuple[str, int]] = []
    getgroups = getattr(os, "getgroups", None)
    if grp is None or getgroups is None:
        return result
    try:
        for gid in getgroups():
            try:
                result.append((grp.getgrgid(gid).gr_name, gid))
            except KeyError:
                result.append((str(gid), gid))
    except OSError:
        pass
    return result


def check_uinput() -> CheckResult:
    """Permisos de /dev/uinput usando grupos de la sesión."""
    if sys.platform != "linux":
        return _ok("uinput", "no aplica", optional=True)
    node = Path("/dev/uinput")
    if not node.exists():
        return _fail(
            "uinput",
            "/dev/uinput no existe",
            "sudo modprobe uinput && ./scripts/install.sh (luego cierra sesión).",
        )
    writable = os.access(node, os.W_OK)
    names = [name for name, _gid in _user_groups()]
    detail = f"{node} writable={writable} grupos={','.join(names) or '-'}"
    if writable:
        return _ok("uinput", detail)
    hint = "Añade tu usuario al grupo uinput (./scripts/install.sh) y vuelve a iniciar sesión."
    if "uinput" not in names:
        hint = "Tu sesión no tiene el grupo uinput. Cierra sesión tras install.sh."
    return _fail("uinput", detail, hint)


def check_macos_notes() -> CheckResult:
    """Recordatorio de Accesibilidad en macOS."""
    if sys.platform != "darwin":
        return _ok("macOS", "no aplica", optional=True)
    return _ok(
        "macOS",
        "Quartz + pyautogui",
        "Si el ratón no se mueve: Ajustes → Privacidad → Accesibilidad.",
        optional=True,
    )


def check_appimage_signature() -> CheckResult:
    """Firma GPG embebida si corre desde un AppImage."""
    appimage = os.environ.get("APPIMAGE")
    if not appimage:
        if is_bundled():
            return _ok("Firma AppImage", "binario empaquetado (sin APPIMAGE)", optional=True)
        return _ok("Firma AppImage", "no corre como AppImage", optional=True)
    path = Path(appimage)
    if not path.is_file():
        return _fail("Firma AppImage", f"APPIMAGE inválido: {appimage}", optional=True)
    try:
        result = subprocess.run(
            [str(path), "--appimage-signature"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return _fail("Firma AppImage", str(error), optional=True)
    output = (result.stdout or "") + (result.stderr or "")
    if "BEGIN PGP SIGNATURE" in output:
        key_hint = str(project_root() / "keys" / "kps-signing-key.asc")
        return _ok("Firma AppImage", "PGP embebida", f"Verificar con: gpg --import {key_hint}")
    return _fail(
        "Firma AppImage",
        "sin firma embebida",
        "Reconstruí con la clave GPG (KPS_APPIMAGE_SIGN=1) o importá keys/kps-signing-key.asc.",
        optional=True,
    )


def check_inhibit_tool() -> CheckResult:
    """Herramienta para --inhibit-only (systemd-inhibit / caffeinate / WinAPI)."""
    if sys.platform == "win32":
        return _ok("Inhibit", "SetThreadExecutionState", optional=True)
    if sys.platform == "darwin":
        path = shutil.which("caffeinate")
        if path:
            return _ok("Inhibit", path, optional=True)
        return _fail("Inhibit", "caffeinate no está en PATH", optional=True)
    path = shutil.which("systemd-inhibit")
    if path:
        return _ok("Inhibit", path, optional=True)
    return _fail(
        "Inhibit",
        "systemd-inhibit no está en PATH",
        "Instalá systemd (o usá --pulse mouse). El modo --inhibit-only lo necesita.",
        optional=True,
    )


def collect_checks() -> list[CheckResult]:
    """Ejecuta todas las comprobaciones."""
    return [
        check_python(),
        check_session(),
        check_dbus_clients()
        if sys.platform == "linux"
        else _ok("D-Bus (cliente)", "no aplica", optional=True),
        check_dbus_idle(),
        check_uinput(),
        check_macos_notes(),
        check_inhibit_tool(),
        check_appimage_signature(),
    ]


def format_report(checks: list[CheckResult]) -> str:
    """Texto de informe para stdout."""
    lines = [f"kps doctor v{Version}", ""]
    for item in checks:
        if item.ok:
            mark = "OK"
        elif item.optional:
            mark = "AVISO"
        else:
            mark = "FALLO"
        lines.append(f"[{mark}] {item.name}: {item.detail}")
        if item.hint and (not item.ok or item.optional):
            lines.append(f"       → {item.hint}")
    failed = [c for c in checks if not c.ok and not c.optional]
    lines.append("")
    if failed:
        lines.append(f"{len(failed)} comprobación(es) crítica(s) fallaron.")
    else:
        lines.append("Sin fallos críticos.")
    return "\n".join(lines) + "\n"


def run_doctor() -> int:
    """Imprime el informe; 1 si hay fallos no opcionales."""
    checks = collect_checks()
    sys.stdout.write(format_report(checks))
    if any(not item.ok and not item.optional for item in checks):
        return 1
    return 0
