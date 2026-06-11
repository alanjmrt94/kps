"""Tests de pulso de teclado."""


# pylint: disable=missing-function-docstring,missing-class-docstring,protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

from unittest.mock import MagicMock, patch

from utils import keyboard_pulse


def test_pulse_pyautogui_success() -> None:
    mock_pg = MagicMock()
    with patch.dict("sys.modules", {"pyautogui": mock_pg}):
        with patch.object(keyboard_pulse.sys, "platform", "win32"):
            assert keyboard_pulse.pulse_shift() is True
    mock_pg.press.assert_called_once_with("shift")


def test_pulse_uinput_success() -> None:
    mock_uinput = MagicMock()
    device = MagicMock()
    device.__enter__ = MagicMock(return_value=device)
    device.__exit__ = MagicMock(return_value=False)
    mock_uinput.Device.return_value = device
    mock_uinput.KEY_LEFTSHIFT = 42
    with patch.dict("sys.modules", {"uinput": mock_uinput}):
        with patch.object(keyboard_pulse.sys, "platform", "linux"):
            assert keyboard_pulse.pulse_shift() is True


def test_pulse_pyautogui_import_error() -> None:
    with patch("builtins.__import__", side_effect=ImportError("no pyautogui")):
        with patch.object(keyboard_pulse.sys, "platform", "darwin"):
            assert keyboard_pulse.pulse_shift() is False


def test_pulse_pyautogui_oserror() -> None:
    mock_pg = MagicMock()
    mock_pg.press.side_effect = OSError("denied")
    with patch.dict("sys.modules", {"pyautogui": mock_pg}):
        with patch.object(keyboard_pulse.sys, "platform", "win32"):
            assert keyboard_pulse.pulse_shift() is False


def test_pulse_uinput_import_error() -> None:
    with patch("builtins.__import__", side_effect=ImportError("no uinput")):
        with patch.object(keyboard_pulse.sys, "platform", "linux"):
            assert keyboard_pulse.pulse_shift() is False


def test_pulse_uinput_permission_error() -> None:
    mock_uinput = MagicMock()
    mock_uinput.Device.side_effect = PermissionError("udev")
    mock_uinput.KEY_LEFTSHIFT = 42
    with patch.dict("sys.modules", {"uinput": mock_uinput}):
        with patch.object(keyboard_pulse.sys, "platform", "linux"):
            assert keyboard_pulse.pulse_shift() is False
