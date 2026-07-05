"""Consultas D-Bus de tiempo idle sin PyGObject (gdbus/busctl/dbus-send)."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from typing import Callable

log = logging.getLogger("kps.dbus_idle")

_DBUS_ERROR = re.compile(
    r"(Error|error|not found|No such object|ServiceUnknown|NameHasNoOwner)",
    re.IGNORECASE,
)
_VALUE_RE = re.compile(r"(?:uint32|uint64|u|t)\s+(\d+)")


class DBusIdleError(OSError):
    """Fallo al consultar idle por D-Bus."""


def _parse_idle_ms(stdout: str) -> int:
    match = _VALUE_RE.search(stdout)
    if not match:
        raise DBusIdleError(f"Respuesta D-Bus no reconocida: {stdout.strip()!r}")
    return int(match.group(1))


def _run_checked(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0 or _DBUS_ERROR.search(output):
        raise DBusIdleError(output.strip() or f"comando falló: {' '.join(cmd)}")
    return result.stdout or ""


def _call_gdbus(dest: str, path: str, interface: str, method: str) -> int:
    stdout = _run_checked(
        [
            "gdbus",
            "call",
            "--session",
            "--dest",
            dest,
            "--object-path",
            path,
            "--method",
            f"{interface}.{method}",
        ]
    )
    return _parse_idle_ms(stdout)


def _call_busctl(dest: str, path: str, interface: str, method: str) -> int:
    stdout = _run_checked(
        [
            "busctl",
            "--user",
            "call",
            dest,
            path,
            interface,
            method,
        ]
    )
    return _parse_idle_ms(stdout)


def _call_dbus_send(dest: str, path: str, interface: str, method: str) -> int:
    stdout = _run_checked(
        [
            "dbus-send",
            "--print-reply",
            f"--dest={dest}",
            path,
            f"{interface}.{method}",
        ]
    )
    return _parse_idle_ms(stdout)


def _pick_caller() -> Callable[[str, str, str, str], int]:
    for name, caller in (
        ("gdbus", _call_gdbus),
        ("busctl", _call_busctl),
        ("dbus-send", _call_dbus_send),
    ):
        if shutil.which(name):
            log.debug("D-Bus idle: usando %s", name)
            return caller
    raise DBusIdleError(
        "No hay cliente D-Bus (gdbus, busctl ni dbus-send). "
        "Instala libglib2.0-bin o dbus."
    )


def get_session_idle_ms(dest: str, path: str, interface: str, method: str) -> int:
    """Devuelve milisegundos idle; lanza DBusIdleError si el servicio no existe."""
    caller = _pick_caller()
    return caller(dest, path, interface, method)


class _DBusIdleMonitorBase:
    """Base común para monitores idle por D-Bus."""

    _DEST: str
    _PATH: str
    _IFACE: str
    _METHOD: str

    def __init__(self) -> None:
        self.last_idle_time = 0
        self._extended_away = False
        log.debug("Probando D-Bus %s", self._DEST)
        self._get_idle_sec_fail()
        log.debug("D-Bus %s operativo", self._DEST)

    def _get_idle_sec_fail(self) -> int:
        idle_ms = get_session_idle_ms(self._DEST, self._PATH, self._IFACE, self._METHOD)
        return idle_ms // 1000

    def get_idle_sec(self) -> int:
        """Segundos idle; conserva el último valor si falla la consulta."""
        try:
            self.last_idle_time = self._get_idle_sec_fail()
        except DBusIdleError as error:
            log.warning("%s.%s() failed: %s", self._IFACE, self._METHOD, error)
        return self.last_idle_time

    def set_extended_away(self, state: bool) -> None:
        """Activa o desactiva el estado extended away."""
        self._extended_away = state

    def is_extended_away(self) -> bool:
        """Indica si extended away está activo."""
        return self._extended_away


class DBusFreedesktopIdleMonitor(_DBusIdleMonitorBase):
    """Idle vía org.freedesktop.ScreenSaver.GetSessionIdleTime."""

    _DEST = "org.freedesktop.ScreenSaver"
    _PATH = "/org/freedesktop/ScreenSaver"
    _IFACE = "org.freedesktop.ScreenSaver"
    _METHOD = "GetSessionIdleTime"


class DBusGnomeIdleMonitor(_DBusIdleMonitorBase):
    """Idle vía org.gnome.Mutter.IdleMonitor.GetIdletime (GNOME/Wayland)."""

    _DEST = "org.gnome.Mutter.IdleMonitor"
    _PATH = "/org/gnome/Mutter/IdleMonitor/Core"
    _IFACE = "org.gnome.Mutter.IdleMonitor"
    _METHOD = "GetIdletime"


class DBusMateIdleMonitor(_DBusIdleMonitorBase):
    """Idle vía org.mate.ScreenSaver.GetSessionIdleTime."""

    _DEST = "org.mate.ScreenSaver"
    _PATH = "/org/mate/ScreenSaver"
    _IFACE = "org.mate.ScreenSaver"
    _METHOD = "GetSessionIdleTime"
