"""Tests de movimiento del ratón (mockeado, sin hardware)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from utils.runner import move_script_path


def test_jiggle_cursor_success() -> None:
    import utils.move_pyautogui as mp

    mock_pg = MagicMock()
    mock_pg.position.return_value = (100, 200)
    with patch.dict("sys.modules", {"pyautogui": mock_pg}):
        assert mp.jiggle_cursor() == 0
    assert mock_pg.moveTo.call_count == 3


def test_jiggle_cursor_os_error() -> None:
    import utils.move_pyautogui as mp

    mock_pg = MagicMock()
    mock_pg.position.side_effect = OSError("sin display")
    with patch.dict("sys.modules", {"pyautogui": mock_pg}):
        assert mp.jiggle_cursor() == 1


def test_move_script_path_by_platform() -> None:
    path = move_script_path()
    if sys.platform == "win32":
        assert path.name == "move_win.py"
    elif sys.platform == "darwin":
        assert path.name == "move_mac.py"
    else:
        assert path.name == "move.py"
