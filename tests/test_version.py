"""Tests de versión."""


# pylint: disable=missing-function-docstring,missing-class-docstring,protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

from utils.const import Version
from utils.version import App_version, Py_version


def test_app_version_matches_const() -> None:
    assert App_version() == Version


def test_py_version_is_int() -> None:
    assert Py_version() >= 3
