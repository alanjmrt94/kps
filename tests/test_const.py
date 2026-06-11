"""Tests de constantes y enums."""

from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

import utils.const as const_mod
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


def test_display_str_and_values() -> None:
    assert str(Display.X11) == Display.X11.value
    assert str(Display.WAYLAND) == "GdkWaylandDisplay"
    assert str(Display.WIN32) == Display.WIN32.value
    assert str(Display.QUARTZ) == Display.QUARTZ.value


def test_idle_state_values() -> None:
    assert str(IdleState.AWAKE) == "awake"
    assert str(IdleState.AWAY) == "away"
    assert str(IdleState.XA) == "extended away"
    assert str(IdleState.UNKNOWN) == IdleState.UNKNOWN.value


def test_os_type_values() -> None:
    assert str(OsType.UNIX) == "posix"
    assert str(OsType.WINDOWS) == "nt"


def test_strenum_polyfill_on_python310() -> None:
    """Cubre el polyfill StrEnum cuando version_info < 3.11."""
    with patch.object(sys, "version_info", (3, 10, 12, "final", 0)):
        importlib.reload(const_mod)
        assert issubclass(const_mod.StrEnum, str)

        class _Sample(const_mod.StrEnum):
            FOO = "bar"

        assert _Sample.FOO == "bar"
    importlib.reload(const_mod)
