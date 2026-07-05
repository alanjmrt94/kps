"""Dispositivo virtual /dev/uinput vía ctypes (sin python-uinput)."""

from __future__ import annotations

import fcntl
import os
import struct
import time

# linux/input-event-codes.h (subset)
EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02

REL_X = 0x00
REL_Y = 0x01
BTN_LEFT = 0x110
BTN_RIGHT = 0x111
KEY_LEFTSHIFT = 0x2A

# linux/uinput.h
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_SET_RELBIT = 0x40045566
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502

ABS_CNT = 0x40
UINPUT_MAX_NAME_SIZE = 80


def _pack_input_event(ev_type: int, code: int, value: int) -> bytes:
    """Estruct input_event en Linux 64-bit."""
    sec = int(time.time())
    usec = int((time.time() % 1) * 1_000_000)
    return struct.pack("llHHi", sec, usec, ev_type, code, value)


def _pack_user_device(name: str = "kps-virtual") -> bytes:
    """uinput_user_dev mínimo para UI_DEV_CREATE."""
    encoded = name.encode("utf-8")[: UINPUT_MAX_NAME_SIZE - 1]
    device_name = encoded.ljust(UINPUT_MAX_NAME_SIZE, b"\x00")
    # input_id: bustype=BUS_USB, vendor, product, version
    device_id = struct.pack("HHHH", 0x0003, 0x1234, 0x5678, 0x0001)
    ff_effects_max = struct.pack("i", 0)
    abs_data = b"\x00" * (ABS_CNT * 4 * 4)
    return device_name + device_id + ff_effects_max + abs_data


class UInputDevice:
    """Context manager para emitir eventos de teclado/ratón en /dev/uinput."""

    def __init__(self, capabilities: tuple[int, ...]) -> None:
        self._fd: int | None = None
        self._capabilities = capabilities
        self._open_and_configure()

    def _open_and_configure(self) -> None:
        fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
        try:
            needs_key = False
            needs_rel = False
            for code in self._capabilities:
                if code in (REL_X, REL_Y):
                    needs_rel = True
                    fcntl.ioctl(fd, UI_SET_RELBIT, code)
                else:
                    needs_key = True
                    fcntl.ioctl(fd, UI_SET_KEYBIT, code)
            if needs_rel:
                fcntl.ioctl(fd, UI_SET_EVBIT, EV_REL)
            if needs_key:
                fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY)
            fcntl.ioctl(fd, UI_SET_EVBIT, EV_SYN)
            os.write(fd, _pack_user_device())
            fcntl.ioctl(fd, UI_DEV_CREATE)
        except OSError:
            os.close(fd)
            raise
        self._fd = fd

    def emit(self, code: int, value: int) -> None:
        """Emite un evento de tecla o relativa y sincroniza."""
        if self._fd is None:
            raise OSError("Dispositivo uinput cerrado")
        ev_type = EV_REL if code in (REL_X, REL_Y) else EV_KEY
        os.write(self._fd, _pack_input_event(ev_type, code, value))
        os.write(self._fd, _pack_input_event(EV_SYN, 0, 0))

    def close(self) -> None:
        """Destruye el dispositivo virtual y cierra el descriptor."""
        if self._fd is None:
            return
        fd = self._fd
        self._fd = None
        try:
            fcntl.ioctl(fd, UI_DEV_DESTROY)
        except OSError:
            pass
        os.close(fd)

    def __enter__(self) -> UInputDevice:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
