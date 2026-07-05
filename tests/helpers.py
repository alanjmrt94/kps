"""Utilidades compartidas para tests."""

from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock, patch


def ensure_linux_uinput_modules() -> None:
    """Carga move/uinput_device mockeando fcntl (hosts sin módulo Linux)."""
    mock_fcntl = MagicMock()
    with patch.dict(sys.modules, {"fcntl": mock_fcntl}):
        if "utils.uinput_device" not in sys.modules:
            importlib.import_module("utils.uinput_device")
        if "utils.move" not in sys.modules:
            importlib.import_module("utils.move")
