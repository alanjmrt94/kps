"""Inhibir idle/sleep del sistema (sin pulso de ratón ni teclado)."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from typing import Any

log = logging.getLogger("kps.inhibit")

# WinAPI SetThreadExecutionState
_ES_CONTINUOUS = 0x80000000
_ES_SYSTEM_REQUIRED = 0x00000001
_ES_DISPLAY_REQUIRED = 0x00000002
_ES_IDLE_STATUS = _ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_DISPLAY_REQUIRED


class IdleInhibit:
    """Mantiene el SO despierto mientras está activo; liberar con ``stop()``."""

    def __init__(self) -> None:
        self._process: subprocess.Popen[Any] | None = None
        self._windows_active = False

    @property
    def running(self) -> bool:
        """True si hay una inhibición en curso."""
        if self._windows_active:
            return True
        if self._process is None:
            return False
        return self._process.poll() is None

    def start(self) -> bool:
        """Activa la inhibición; False si no se pudo."""
        if self.running:
            return True
        if sys.platform == "win32":
            return self._start_windows()
        if sys.platform == "darwin":
            return self._start_unix(["caffeinate", "-dims"])
        inhibit = shutil.which("systemd-inhibit")
        if not inhibit:
            log.warning("systemd-inhibit no está en PATH; no se inhibe el idle del SO.")
            return False
        return self._start_unix(
            [
                inhibit,
                "--what=idle:sleep",
                "--who=kps",
                "--why=Evitar suspensión por inactividad",
                "--mode=block",
                "sleep",
                "infinity",
            ]
        )

    def stop(self) -> None:
        """Libera la inhibición."""
        if self._windows_active:
            self._stop_windows()
        proc = self._process
        self._process = None
        if proc is None:
            return
        if proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)

    def _start_unix(self, cmd: list[str]) -> bool:
        try:
            self._process = subprocess.Popen(  # pylint: disable=consider-using-with
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as error:
            log.warning("No se pudo inhibir idle/sleep: %s", error)
            self._process = None
            return False
        log.debug("Inhibición activa: %s (PID %s)", cmd[0], self._process.pid)
        return True

    def _start_windows(self) -> bool:
        try:
            import ctypes  # pylint: disable=import-outside-toplevel

            ctypes.windll.kernel32.SetThreadExecutionState(_ES_IDLE_STATUS)  # type: ignore[attr-defined]
        except (AttributeError, OSError) as error:
            log.warning("SetThreadExecutionState falló: %s", error)
            return False
        self._windows_active = True
        log.debug("Inhibición activa: SetThreadExecutionState")
        return True

    def _stop_windows(self) -> None:
        try:
            import ctypes  # pylint: disable=import-outside-toplevel

            ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass
        self._windows_active = False

    def __enter__(self) -> IdleInhibit:
        self.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.stop()
