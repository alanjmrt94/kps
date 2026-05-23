"""Mueve el cursor vía uinput (Linux). Requiere acceso a /dev/uinput sin sudo."""

import sys
import time

import uinput  # pylint: disable=import-error

EVENTS = (
    uinput.REL_X,
    uinput.REL_Y,
    uinput.BTN_LEFT,
    uinput.BTN_RIGHT,
)


def move_once() -> None:
    """Realiza un pequeño movimiento horizontal del cursor."""
    with uinput.Device(EVENTS) as device:
        for i in range(3):
            if i == 2:
                device.emit(uinput.REL_X, -75)
            else:
                device.emit(uinput.REL_X, 100)
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
