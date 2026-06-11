"""Cierre graceful: señales del sistema y hotkey opcional (F1–F12)."""

from __future__ import annotations

import logging
import signal
import threading

from utils.hotkey import parse_function_key, start_hotkey_listener, windows_vk_from_hotkey

log = logging.getLogger("kps.shutdown")

# Alias para tests y compatibilidad
_windows_vk_from_hotkey = windows_vk_from_hotkey


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
        """Inicia escucha de hotkey F1–F12 (Windows, Linux y macOS con pynput)."""
        if not hotkey:
            return
        if parse_function_key(hotkey) is None:
            log.warning(
                "Hotkey '%s' no reconocida; usa F1–F12 (o Ctrl+C / SIGUSR1 en daemon).",
                hotkey,
            )
            return
        self._hotkey_thread = start_hotkey_listener(hotkey, self.request)
        if self._hotkey_thread is not None:
            log.info("Hotkey de cierre: %s", hotkey.strip().upper())


def _windows_hotkey_loop(vk: int, label: str, on_trigger) -> None:
    """Compatibilidad con tests; delega en utils.hotkey."""
    from utils.hotkey import _windows_vk_loop  # pylint: disable=import-outside-toplevel

    _windows_vk_loop(vk, label, on_trigger)
