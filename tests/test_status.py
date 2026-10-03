"""Tests del estado de presencia."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

from utils.status import PresenceStatus, StatusHub


def test_status_hub_roundtrip() -> None:
    """Comprueba status hub roundtrip."""
    hub = StatusHub()
    assert hub.label() == "activo"
    hub.set(PresenceStatus.AWAY)
    assert hub.get() == PresenceStatus.AWAY
    hub.set("pausado")
    assert hub.label() == "pausado"
