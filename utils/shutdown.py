"""Cierre graceful: señales del sistema y hotkey opcional (Windows)."""

from __future__ import annotations

import logging
import signal
import sys
import threading
from typing import Callable

log = logging.getLogger("kps.shutdown")


class ShutdownController:
    """Coordina la salida limpia del bucle principal."""

    def __init__(self) -> None:
        self.requested = False
        self._reason = ""
        self._hotkey_thread: threading.Thread | None = None

    @property
    def reason(self) -> str:
        """Motivo de la solicitud de cierre."""
        return self._reason

    def request(self, reason: str = "señal recibida") -> None:
        """Marca el bucle para terminar."""
        if self.requested:
            return
        self.requested = True
        self._reason = reason
        log.debug("Cierre solicitado: %s", reason)

    def install_signal_handlers(self) -> None:
        """Registra manejadores para cierre graceful."""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        if hasattr(signal, "SIGUSR1"):
            signal.signal(signal.SIGUSR1, self._handle_signal)

    def _handle_signal(self, signum: int, _frame) -> None:
        name = signal.Signals(signum).name
        hint = ""
        if signum == getattr(signal, "SIGUSR1", -1):
            hint = " (daemon: kill -USR1 $(cat pidfile))"
        self.request(f"{name}{hint}")

    def start_hotkey_listener(self, hotkey: str | None) -> None:
        """Inicia escucha de hotkey; solo Windows (F1–F12) sin deps extra."""
        if not hotkey:
            return
        if sys.platform != "win32":
            log.info(
                "Hotkey '%s' no soportada en esta plataforma; "
                "usa Ctrl+C o kill -USR1 en daemon.",
                hotkey,
            )
            return

        vk = _windows_vk_from_hotkey(hotkey)
        if vk is None:
            log.warning("Hotkey '%s' no reconocida; usa F1–F12 en Windows.", hotkey)
            return

        self._hotkey_thread = threading.Thread(
            target=_windows_hotkey_loop,
            args=(vk, hotkey, self.request),
            name="kps-hotkey",
            daemon=True,
        )
        self._hotkey_thread.start()
        log.info("Hotkey de cierre: %s", hotkey.upper())


def _windows_vk_from_hotkey(hotkey: str) -> int | None:
    """Convierte F1–F12 a código virtual de Windows."""
    key = hotkey.strip().upper().replace(" ", "")
    if key.startswith("F") and key[1:].isdigit():
        num = int(key[1:])
        if 1 <= num <= 12:
            # VK_F1 = 0x70
            return 0x6F + num
    return None


def _windows_hotkey_loop(vk: int, label: str, on_trigger: Callable[[str], None]) -> None:
    """Bloquea hasta pulsar la hotkey registrada (Windows)."""
    import ctypes  # pylint: disable=import-outside-toplevel
    import ctypes.wintypes  # pylint: disable=import-outside-toplevel

    user32 = ctypes.windll.user32
    if not user32.RegisterHotKey(None, 1, 0, vk):
        log.warning("No se pudo registrar hotkey %s", label)
        return
    try:
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == 0x0312:  # WM_HOTKEY
                on_trigger(f"hotkey {label.upper()}")
                break
    finally:
        user32.UnregisterHotKey(None, 1)
