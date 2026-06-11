"""Detección de entorno gráfico (X11/Wayland) con fallback sin Gdk."""

from __future__ import annotations

import logging
import os

from utils.const import Display

log = logging.getLogger("kps.app")


def is_wayland_session() -> bool:
    """True si la sesión es Wayland (sin importar Gdk)."""
    return os.environ.get("XDG_SESSION_TYPE") == "wayland"


def is_display(display: Display) -> bool:
    """Comprueba el tipo de display; Wayland vía env, X11 vía Gdk si está disponible."""
    if display == Display.WAYLAND:
        return is_wayland_session()

    if display != Display.X11:
        return False

    try:
        display_class = _gdk_display_class_name()
        if display_class is None:
            log.warning("No se pudo determinar el gestor de ventanas")
            return False
        return bool(display_class == display.value)
    except (ImportError, ValueError) as error:
        log.debug("Gdk no disponible para detectar X11: %s", error)
        return not is_wayland_session()


def _gdk_display_class_name() -> str | None:
    """Nombre de la clase Gdk.Display por defecto, o None si no hay display."""
    import gi  # pylint: disable=import-outside-toplevel

    gi.require_version("Gdk", "4.0")
    from gi.repository import Gdk  # pylint: disable=import-outside-toplevel

    default = Gdk.Display.get_default()
    if default is None:
        return None
    return str(default.__class__.__name__)
