"""Tests de pulso de teclado."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.helpers import linux_uinput_modules
from utils import keyboard_pulse


def test_pulse_pyautogui_success() -> None:
    """Comprueba pulse pyautogui success."""
    mock_pg = MagicMock()
    with patch.dict("sys.modules", {"pyautogui": mock_pg}):
        with patch.object(keyboard_pulse.sys, "platform", "win32"):
            assert keyboard_pulse.pulse_shift() is True
    mock_pg.press.assert_called_once_with("shift")


def test_pulse_uinput_success() -> None:
    """Comprueba pulse uinput success."""
    device = MagicMock()
    device.__enter__ = MagicMock(return_value=device)
    device.__exit__ = MagicMock(return_value=False)
    with linux_uinput_modules():
        with (
            patch("utils.uinput_device.UInputDevice", return_value=device),
            patch.object(keyboard_pulse.sys, "platform", "linux"),
        ):
            assert keyboard_pulse.pulse_shift() is True


def test_pulse_pyautogui_import_error() -> None:
    """Comprueba pulse pyautogui import error."""
    with patch("builtins.__import__", side_effect=ImportError("no pyautogui")):
        with patch.object(keyboard_pulse.sys, "platform", "darwin"):
            assert keyboard_pulse.pulse_shift() is False


def test_pulse_pyautogui_oserror() -> None:
    """Comprueba pulse pyautogui oserror."""
    mock_pg = MagicMock()
    mock_pg.press.side_effect = OSError("denied")
    with patch.dict("sys.modules", {"pyautogui": mock_pg}):
        with patch.object(keyboard_pulse.sys, "platform", "win32"):
            assert keyboard_pulse.pulse_shift() is False


def test_pulse_uinput_permission_error() -> None:
    """Comprueba pulse uinput permission error."""
    with linux_uinput_modules():
        with (
            patch(
                "utils.uinput_device.UInputDevice",
                side_effect=PermissionError("udev"),
            ),
            patch.object(keyboard_pulse.sys, "platform", "linux"),
        ):
            assert keyboard_pulse.pulse_shift() is False
