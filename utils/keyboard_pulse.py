"""Pulso de tecla inocuo (Shift) para complementar el movimiento del ratón."""

from __future__ import annotations

import logging
import sys

log = logging.getLogger("kps.keyboard")


def pulse_shift() -> bool:
    """Emite un pulso breve de Shift; False si no se pudo."""
    if sys.platform in ("win32", "darwin"):
        return _pulse_pyautogui()
    return _pulse_uinput()


def _pulse_pyautogui() -> bool:
    try:
        import pyautogui  # pylint: disable=import-outside-toplevel
    except ImportError:
        log.warning("pyautogui no disponible para pulso de teclado.")
        return False
    try:
        pyautogui.press("shift")
        return True
    except OSError as error:
        log.warning("No se pudo pulsar tecla: %s", error)
        return False


def _pulse_uinput() -> bool:
    try:
        import uinput  # pylint: disable=import-outside-toplevel,import-error
    except ImportError:
        log.warning("uinput no disponible para pulso de teclado.")
        return False
    try:
        with uinput.Device((uinput.KEY_LEFTSHIFT,)) as device:
            device.emit(uinput.KEY_LEFTSHIFT, 1)
            device.emit(uinput.KEY_LEFTSHIFT, 0)
        return True
    except (OSError, PermissionError) as error:
        log.warning("Pulso uinput falló: %s", error)
        return False
