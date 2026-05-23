"""Mueve el cursor en Windows vía pyautogui."""

import sys

from utils.move_pyautogui import jiggle_cursor


def main() -> int:
    """Punto de entrada del script de movimiento en Windows."""
    return jiggle_cursor()


if __name__ == "__main__":
    sys.exit(main())
