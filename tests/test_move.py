"""Tests de movimiento del ratón (mockeado, sin hardware)."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import,invalid-name
from __future__ import annotations

import runpy
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import utils.move_mac as move_mac
import utils.move_win as move_win
from utils import move_pyautogui

if sys.platform == "linux":
    import utils.move as move_linux
else:
    move_linux = None  # type: ignore[assignment,misc]


def test_jiggle_cursor_success() -> None:
    """Comprueba jiggle cursor success."""
    mock_pg = MagicMock()
    mock_pg.position.return_value = (100, 200)
    with patch.dict("sys.modules", {"pyautogui": mock_pg}):
        assert move_pyautogui.jiggle_cursor() == 0
    assert mock_pg.moveTo.call_count == 3


def test_jiggle_cursor_os_error() -> None:
    """Comprueba jiggle cursor os error."""
    mock_pg = MagicMock()
    mock_pg.position.side_effect = OSError("sin display")
    with patch.dict("sys.modules", {"pyautogui": mock_pg}):
        assert move_pyautogui.jiggle_cursor() == 1


def test_move_win_and_mac_main() -> None:
    """Comprueba move win and mac main."""
    with patch("utils.move_win.jiggle_cursor", return_value=0):
        assert move_win.main() == 0
    with patch("utils.move_mac.jiggle_cursor", return_value=1):
        assert move_mac.main() == 1


@pytest.mark.skipif(sys.platform != "linux", reason="uinput solo en Linux")
def test_move_once_with_uinput_mock() -> None:
    """Comprueba move once with uinput mock."""
    device = MagicMock()
    device.__enter__ = MagicMock(return_value=device)
    device.__exit__ = MagicMock(return_value=False)
    with (
        patch("utils.move.UInputDevice", return_value=device),
        patch.object(move_linux.time, "sleep"),
    ):
        move_linux.move_once()
    assert device.emit.call_count == 3


@pytest.mark.skipif(sys.platform != "linux", reason="uinput solo en Linux")
def test_move_linux_success() -> None:
    """Comprueba move linux success."""
    with (
        patch.object(move_linux, "move_once"),
        patch.object(move_linux.time, "sleep"),
    ):
        assert move_linux.main() == 0


@pytest.mark.skipif(sys.platform != "linux", reason="uinput solo en Linux")
def test_move_linux_permission_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Comprueba move linux permission error."""
    with patch.object(move_linux, "move_once", side_effect=PermissionError):
        assert move_linux.main() == 1
    assert "uinput" in capsys.readouterr().err


@pytest.mark.skipif(sys.platform != "linux", reason="uinput solo en Linux")
def test_move_linux_os_error() -> None:
    """Comprueba move linux os error."""
    with patch.object(move_linux, "move_once", side_effect=OSError("broken")):
        assert move_linux.main() == 1


def test_move_entrypoints_main() -> None:
    """Comprueba move entrypoints main."""
    win_path = Path(move_win.__file__)
    mac_path = Path(move_mac.__file__)
    with patch("utils.move_pyautogui.jiggle_cursor", return_value=0):
        with pytest.raises(SystemExit) as exc:
            runpy.run_path(str(win_path), run_name="__main__")
        assert exc.value.code == 0
    with patch("utils.move_pyautogui.jiggle_cursor", return_value=1):
        with pytest.raises(SystemExit) as exc:
            runpy.run_path(str(mac_path), run_name="__main__")
        assert exc.value.code == 1


@pytest.mark.skipif(sys.platform != "linux", reason="uinput solo en Linux")
def test_move_entrypoints_linux_main() -> None:
    """Comprueba move entrypoints linux main."""
    linux_path = Path(move_linux.__file__)
    device = MagicMock()
    device.__enter__ = MagicMock(return_value=device)
    device.__exit__ = MagicMock(return_value=False)
    with (
        patch("utils.uinput_device.UInputDevice", return_value=device),
        patch("time.sleep"),
    ):
        with pytest.raises(SystemExit) as exc:
            runpy.run_path(str(linux_path), run_name="__main__")
        assert exc.value.code == 0
