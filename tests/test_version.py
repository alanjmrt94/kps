"""Tests de versión."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

from utils.const import Version
from utils.version import App_version, Py_version


def test_app_version_matches_const() -> None:
    """Comprueba app version matches const."""
    assert App_version() == Version


def test_py_version_is_int() -> None:
    """Comprueba py version is int."""
    assert Py_version() >= 3
