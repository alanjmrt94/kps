"""Tests de cierre graceful."""


# pylint: disable=missing-function-docstring,missing-class-docstring,protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

import signal
import sys
from unittest.mock import MagicMock, patch

import pytest

from utils.shutdown import ShutdownController, _windows_hotkey_loop, _windows_vk_from_hotkey


def test_shutdown_request_once() -> None:
    ctrl = ShutdownController()
    ctrl.request("test")
    assert ctrl.requested is True
    assert ctrl.reason == "test"
    ctrl.request("otro")
    assert ctrl.reason == "test"


def test_handle_signal_sigint() -> None:
    ctrl = ShutdownController()
    ctrl._handle_signal(signal.SIGINT, None)
    assert ctrl.requested
    assert "SIGINT" in ctrl.reason


@pytest.mark.skipif(not hasattr(signal, "SIGUSR1"), reason="SIGUSR1")
def test_handle_signal_sigusr1() -> None:
    ctrl = ShutdownController()
    ctrl._handle_signal(signal.SIGUSR1, None)
    assert "SIGUSR1" in ctrl.reason


def test_install_signal_handlers() -> None:
    ShutdownController().install_signal_handlers()


def test_install_signal_handlers_without_sigusr1() -> None:
    def fake_hasattr(obj: object, name: str) -> bool:
        if name == "SIGUSR1":
            return False
        return hasattr(obj, name)

    with patch("utils.shutdown.hasattr", fake_hasattr):
        ShutdownController().install_signal_handlers()


def test_start_hotkey_none() -> None:
    ShutdownController().start_hotkey_listener(None)


def test_start_hotkey_skips_log_when_listener_fails() -> None:
    with patch("utils.shutdown.start_hotkey_listener", return_value=None):
        with patch("utils.shutdown.log") as mock_log:
            ShutdownController().start_hotkey_listener("F1")
            mock_log.info.assert_not_called()


def test_start_hotkey_logs_when_registered() -> None:
    mock_thread = MagicMock()
    with patch("utils.shutdown.start_hotkey_listener", return_value=mock_thread):
        with patch("utils.shutdown.log") as mock_log:
            ShutdownController().start_hotkey_listener("f1")
            mock_log.info.assert_called_once_with("Hotkey de cierre: %s", "F1")


def test_start_hotkey_non_windows() -> None:
    with (
        patch.object(sys, "platform", "linux"),
        patch("utils.hotkey._start_pynput", return_value=MagicMock()),
    ):
        ShutdownController().start_hotkey_listener("F12")


def test_start_hotkey_invalid_windows() -> None:
    with patch.object(sys, "platform", "win32"):
        ShutdownController().start_hotkey_listener("ctrl+c")


def test_start_hotkey_windows_starts_thread() -> None:
    with (
        patch.object(sys, "platform", "win32"),
        patch("utils.shutdown.threading.Thread") as mock_thread,
    ):
        mock_thread.return_value.start = MagicMock()
        ctrl = ShutdownController()
        ctrl.start_hotkey_listener("F11")
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()


def test_windows_vk_from_hotkey() -> None:
    assert _windows_vk_from_hotkey("f12") == 0x7B
    assert _windows_vk_from_hotkey("F1") == 0x70
    assert _windows_vk_from_hotkey("ctrl+c") is None
    assert _windows_vk_from_hotkey("F13") is None


def test_windows_hotkey_loop_register_fail() -> None:
    user32 = MagicMock()
    user32.RegisterHotKey.return_value = 0
    mock_ctypes = MagicMock()
    mock_ctypes.windll.user32 = user32
    with patch.dict(sys.modules, {"ctypes": mock_ctypes, "ctypes.wintypes": MagicMock()}):
        called = []

        def on_trigger(msg: str) -> None:
            called.append(msg)

        _windows_hotkey_loop(0x70, "f1", on_trigger)
        assert not called


def test_windows_hotkey_loop_trigger() -> None:
    user32 = MagicMock()
    user32.RegisterHotKey.return_value = 1
    user32.GetMessageW.side_effect = [1, 0]
    msg = MagicMock()
    msg.message = 0x0312
    mock_wintypes = MagicMock()
    mock_wintypes.MSG.return_value = msg
    mock_ctypes = MagicMock()
    mock_ctypes.windll.user32 = user32
    mock_ctypes.wintypes = mock_wintypes
    mock_ctypes.byref.return_value = msg
    with patch.dict(sys.modules, {"ctypes": mock_ctypes, "ctypes.wintypes": mock_wintypes}):
        called: list[str] = []

        def on_trigger(reason: str) -> None:
            called.append(reason)

        _windows_hotkey_loop(0x70, "f1", on_trigger)
        assert called == ["hotkey F1"]
        user32.UnregisterHotKey.assert_called_once()


def test_handle_signal_sigterm() -> None:
    ctrl = ShutdownController()
    ctrl._handle_signal(signal.SIGTERM, None)
    assert "SIGTERM" in ctrl.reason


def test_windows_hotkey_loop_non_hotkey_message() -> None:
    user32 = MagicMock()
    user32.RegisterHotKey.return_value = 1
    user32.GetMessageW.side_effect = [1, 0]
    msg = MagicMock()
    msg.message = 0x0000
    mock_wintypes = MagicMock()
    mock_wintypes.MSG.return_value = msg
    mock_ctypes = MagicMock()
    mock_ctypes.windll.user32 = user32
    mock_ctypes.wintypes = mock_wintypes
    mock_ctypes.byref.return_value = msg
    with patch.dict(sys.modules, {"ctypes": mock_ctypes, "ctypes.wintypes": mock_wintypes}):
        called: list[str] = []

        def on_trigger(reason: str) -> None:
            called.append(reason)

        _windows_hotkey_loop(0x70, "f1", on_trigger)
        assert not called
        user32.UnregisterHotKey.assert_called_once()
