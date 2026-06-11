"""Tests de hotkey multiplataforma."""


# pylint: disable=missing-function-docstring,missing-class-docstring,protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from utils import hotkey
from utils.hotkey import (
    _start_pynput,
    _start_windows,
    _windows_loop,
    parse_function_key,
    start_hotkey_listener,
    windows_vk_from_hotkey,
)


def test_parse_function_key_valid() -> None:
    assert parse_function_key("f12") == "F12"
    assert parse_function_key(" F1 ") == "F1"


def test_parse_function_key_invalid() -> None:
    assert parse_function_key("ctrl+c") is None
    assert parse_function_key("F13") is None


def test_windows_vk_from_hotkey() -> None:
    assert windows_vk_from_hotkey("F1") == 0x70
    assert windows_vk_from_hotkey("F12") == 0x7B
    assert windows_vk_from_hotkey("ctrl+c") is None


def test_start_hotkey_listener_invalid() -> None:
    assert start_hotkey_listener("ctrl+c", lambda _msg: None) is None


def test_start_windows_starts_thread() -> None:
    with patch("utils.hotkey.threading.Thread") as mock_thread:
        mock_thread.return_value.start = MagicMock()
        thread = _start_windows("F1", lambda _msg: None)
        assert thread is mock_thread.return_value
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()


def test_start_hotkey_listener_windows() -> None:
    with (
        patch.object(sys, "platform", "win32"),
        patch.object(hotkey, "_start_windows", return_value=MagicMock()) as mock_start,
    ):
        start_hotkey_listener("F2", lambda _msg: None)
        mock_start.assert_called_once_with("F2", mock_start.call_args[0][1])


def test_windows_loop_trigger() -> None:
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
    called: list[str] = []

    with patch.dict(sys.modules, {"ctypes": mock_ctypes, "ctypes.wintypes": mock_wintypes}):
        _windows_loop(0x70, "F1", called.append)

    assert called == ["hotkey F1"]
    user32.UnregisterHotKey.assert_called_once()


def test_start_pynput_import_error() -> None:
    import builtins

    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name.split(".")[0] == "pynput":
            raise ImportError("no pynput")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=blocked_import):
        assert _start_pynput("F1", lambda _msg: None) is None


def _fake_pynput_modules(
    *,
    key: object | None = None,
    listener_factory: object | None = None,
) -> dict[str, object]:
    fake_keyboard = types.ModuleType("pynput.keyboard")
    fake_keyboard.Key = SimpleNamespace(**({} if key is None else {"f1": key}))
    if listener_factory is not None:
        fake_keyboard.Listener = listener_factory
    fake_pynput = types.ModuleType("pynput")
    fake_pynput.keyboard = fake_keyboard
    return {"pynput": fake_pynput, "pynput.keyboard": fake_keyboard}


def test_start_pynput_unknown_key() -> None:
    with patch.dict(sys.modules, _fake_pynput_modules()):
        assert _start_pynput("F1", lambda _msg: None) is None


def test_start_pynput_success_and_on_press() -> None:
    target = object()
    captured: dict[str, object] = {}

    def listener_factory(**kwargs: object) -> MagicMock:
        captured["on_press"] = kwargs["on_press"]
        return MagicMock()

    triggered: list[str] = []

    fake_modules = _fake_pynput_modules(key=target, listener_factory=listener_factory)
    with (
        patch.dict(sys.modules, fake_modules),
        patch("utils.hotkey.threading.Thread") as mock_thread,
    ):
        mock_thread.return_value.start = MagicMock()
        thread = _start_pynput("F1", triggered.append)
        assert thread is mock_thread.return_value
        on_press = captured["on_press"]
        assert callable(on_press)
        on_press(target)
        on_press("other")
        assert triggered == ["hotkey F1"]
