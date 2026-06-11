"""Tests de constantes y enums."""

from __future__ import annotations

from utils.const import (
    CONFIG_FILENAME,
    DEFAULT_AWAY_TIME,
    DEFAULT_POLL_INTERVAL,
    Display,
    IdleState,
    OsType,
    Version,
)


def test_version_format() -> None:
    parts = Version.split(".")
    assert len(parts) == 3


def test_defaults_positive() -> None:
    assert DEFAULT_AWAY_TIME >= 1
    assert DEFAULT_POLL_INTERVAL >= 1


def test_config_filename() -> None:
    assert CONFIG_FILENAME.endswith(".toml")


def test_display_str() -> None:
    assert str(Display.X11) == Display.X11.value


def test_idle_state_values() -> None:
    assert IdleState.AWAKE.value == "awake"


def test_os_type_values() -> None:
    assert str(OsType.UNIX) == "posix"
