"""Movimiento del cursor vía pyautogui (Windows/macOS)."""

import sys
import time

import pyautogui  # pylint: disable=import-error


def jiggle_cursor() -> int:
    """Realiza un pequeño movimiento horizontal del cursor."""
    pyautogui.FAILSAFE = False
    try:
        x, y = pyautogui.position()
        for dx in (100, 100, -75):
            pyautogui.moveTo(x + dx, y, duration=0.2)
            time.sleep(0.5)
    except OSError as error:
        print(f"[kps move] ERROR: {error}", file=sys.stderr)
        return 1
    return 0
