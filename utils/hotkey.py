"""Hotkey de cierre multiplataforma (F1–F12)."""

from __future__ import annotations

import logging
import sys
import threading
from typing import Callable

log = logging.getLogger("kps.hotkey")


def windows_vk_from_hotkey(hotkey: str) -> int | None:
    """Convierte F1–F12 a código virtual de Windows."""
    label = parse_function_key(hotkey)
    if label is None:
        return None
    return 0x6F + int(label[1:])


def parse_function_key(hotkey: str) -> str | None:
    """Devuelve 'F1'…'F12' normalizado o None."""
    key = hotkey.strip().upper().replace(" ", "")
    if key.startswith("F") and key[1:].isdigit():
        num = int(key[1:])
        if 1 <= num <= 12:
            return f"F{num}"
    return None


def start_hotkey_listener(
    hotkey: str, on_trigger: Callable[[str], None]
) -> threading.Thread | None:
    """Inicia hilo de escucha; None si la hotkey no es válida o falla el registro."""
    label = parse_function_key(hotkey)
    if label is None:
        return None
    if sys.platform == "win32":
        return _start_windows(label, on_trigger)
    return _start_pynput(label, on_trigger)


def _start_windows(label: str, on_trigger: Callable[[str], None]) -> threading.Thread | None:
    vk = 0x6F + int(label[1:])
    thread = threading.Thread(
        target=_windows_loop,
        args=(vk, label, on_trigger),
        name="kps-hotkey",
        daemon=True,
    )
    thread.start()
    return thread


def _windows_vk_loop(vk: int, label: str, on_trigger: Callable[[str], None]) -> None:
    import ctypes  # pylint: disable=import-outside-toplevel
    import ctypes.wintypes  # pylint: disable=import-outside-toplevel

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    if not user32.RegisterHotKey(None, 1, 0, vk):
        log.warning("No se pudo registrar hotkey %s", label)
        return
    try:
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == 0x0312:
                on_trigger(f"hotkey {label.upper()}")
                break
    finally:
        user32.UnregisterHotKey(None, 1)


def _windows_loop(vk: int, label: str, on_trigger: Callable[[str], None]) -> None:
    _windows_vk_loop(vk, label, on_trigger)


def _start_pynput(label: str, on_trigger: Callable[[str], None]) -> threading.Thread | None:
    try:
        from pynput import keyboard  # pylint: disable=import-outside-toplevel
    except ImportError:
        log.warning(
            "Hotkey %s requiere pynput (pip install pynput). Usa Ctrl+C o SIGUSR1.",
            label,
        )
        return None

    target = getattr(keyboard.Key, label.lower(), None)
    if target is None:
        log.warning("Hotkey %s no reconocida.", label)
        return None

    def on_press(key: object) -> None:
        if key == target:
            on_trigger(f"hotkey {label.upper()}")

    listener = keyboard.Listener(on_press=on_press)
    thread = threading.Thread(target=listener.run, name="kps-hotkey", daemon=True)
    thread.start()
    return thread
