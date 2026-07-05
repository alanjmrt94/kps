"""Detección de entorno gráfico (X11/Wayland) sin dependencias GTK."""

from __future__ import annotations

import logging
import os

from utils.const import Display

log = logging.getLogger("kps.app")


def is_wayland_session() -> bool:
    """True si la sesión es Wayland."""
    return os.environ.get("XDG_SESSION_TYPE") == "wayland"


def is_display(display: Display) -> bool:
    """Comprueba el tipo de display vía variables de entorno."""
    if display == Display.WAYLAND:
        return is_wayland_session()

    if display != Display.X11:
        return False

    if is_wayland_session():
        return False

    if os.environ.get("DISPLAY"):
        return True

    log.warning("No se detectó DISPLAY; asumiendo sesión no-X11")
    return False
