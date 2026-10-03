"""Tests de horarios de perfiles."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

import datetime as dt

from utils.schedule import is_within_window, parse_hhmm, schedule_allows


def test_parse_hhmm_valid() -> None:
    """Comprueba parse hhmm valid."""
    assert parse_hhmm("09:30") == dt.time(9, 30)


def test_parse_hhmm_invalid() -> None:
    """Comprueba parse hhmm invalid."""
    assert parse_hhmm("25:00") is None
    assert parse_hhmm(None) is None


def test_window_daytime() -> None:
    """Comprueba window daytime."""
    start, end = dt.time(9, 0), dt.time(18, 0)
    assert is_within_window(dt.time(12, 0), start, end) is True
    assert is_within_window(dt.time(8, 0), start, end) is False
    assert is_within_window(dt.time(18, 0), start, end) is False


def test_window_overnight() -> None:
    """Comprueba window overnight."""
    start, end = dt.time(22, 0), dt.time(7, 0)
    assert is_within_window(dt.time(23, 0), start, end) is True
    assert is_within_window(dt.time(3, 0), start, end) is True
    assert is_within_window(dt.time(12, 0), start, end) is False


def test_window_partial_and_equal() -> None:
    """Comprueba window partial and equal."""
    noon = dt.time(12, 0)
    assert is_within_window(noon, None, dt.time(18, 0)) is True
    assert is_within_window(noon, dt.time(9, 0), None) is True
    assert is_within_window(noon, dt.time(9, 0), dt.time(9, 0)) is True


def test_schedule_allows_explicit_now() -> None:
    """Comprueba schedule allows explicit now."""
    assert schedule_allows("09:00", "18:00", now=dt.time(10, 0)) is True
    assert schedule_allows("09:00", "18:00", now=dt.time(20, 0)) is False
