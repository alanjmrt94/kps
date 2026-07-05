"""Utilidades compartidas para tests."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def linux_uinput_modules() -> Iterator[None]:
    """Mantiene fcntl mockeado y carga utils.move / utils.uinput_device."""
    mock_fcntl = MagicMock()
    prev_fcntl = sys.modules.get("fcntl")
    sys.modules["fcntl"] = mock_fcntl
    try:
        importlib.import_module("utils.uinput_device")
        importlib.import_module("utils.move")
        yield
    finally:
        if prev_fcntl is None:
            sys.modules.pop("fcntl", None)
        else:
            sys.modules["fcntl"] = prev_fcntl


def ensure_linux_uinput_modules() -> None:
    """Compatibilidad: carga módulos Linux con fcntl mockeado (sin restaurar)."""
    if "fcntl" not in sys.modules:
        sys.modules["fcntl"] = MagicMock()
    if "utils.uinput_device" not in sys.modules:
        importlib.import_module("utils.uinput_device")
    if "utils.move" not in sys.modules:
        importlib.import_module("utils.move")
