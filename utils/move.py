"""Mueve el cursor vía /dev/uinput (Linux). Requiere acceso sin sudo."""

import sys
import time
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.uinput_device import (  # pylint: disable=wrong-import-position
    BTN_LEFT,
    BTN_RIGHT,
    REL_X,
    REL_Y,
    UInputDevice,
)


def move_once() -> None:
    """Realiza un pequeño movimiento horizontal del cursor."""
    events = (REL_X, REL_Y, BTN_LEFT, BTN_RIGHT)
    with UInputDevice(events) as device:
        for i in range(3):
            if i == 2:
                device.emit(REL_X, -75)
            else:
                device.emit(REL_X, 100)
            time.sleep(0.5)


def main() -> int:
    """Punto de entrada del script de movimiento."""
    try:
        time.sleep(1)
        move_once()
    except PermissionError:
        print(
            "[kps move] ERROR: permiso denegado en /dev/uinput. "
            "Ejecuta ./scripts/install.sh y vuelve a iniciar sesión.",
            file=sys.stderr,
        )
        return 1
    except OSError as error:
        print(f"[kps move] ERROR: no se pudo usar uinput: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
