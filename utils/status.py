"""Estado de presencia para la bandeja: activo, ausente, pausado."""

from __future__ import annotations

import threading
from enum import unique

from utils.const import StrEnum


@unique
class PresenceStatus(StrEnum):
    """Etiqueta visible en bandeja y logs."""

    def __str__(self) -> str:
        return str(self.value)

    ACTIVE = "activo"
    AWAY = "ausente"
    PAUSED = "pausado"


class StatusHub:
    """Almacén thread-safe del estado de presencia."""

    def __init__(self, initial: PresenceStatus = PresenceStatus.ACTIVE) -> None:
        self._lock = threading.Lock()
        self._state = initial

    def set(self, state: PresenceStatus | str) -> None:
        """Actualiza el estado."""
        value = PresenceStatus(state) if not isinstance(state, PresenceStatus) else state
        with self._lock:
            self._state = value

    def get(self) -> PresenceStatus:
        """Estado actual."""
        with self._lock:
            return self._state

    def label(self) -> str:
        """Texto en español para tooltip/menú."""
        return str(self.get())
