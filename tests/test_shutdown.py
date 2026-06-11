"""Tests de cierre graceful."""

from __future__ import annotations

from utils.shutdown import ShutdownController, _windows_vk_from_hotkey


def test_shutdown_request_once() -> None:
    ctrl = ShutdownController()
    ctrl.request("test")
    assert ctrl.requested is True
    assert ctrl.reason == "test"
    ctrl.request("otro")
    assert ctrl.reason == "test"


def test_windows_vk_from_hotkey() -> None:
    assert _windows_vk_from_hotkey("f12") == 0x7B
    assert _windows_vk_from_hotkey("F1") == 0x70
    assert _windows_vk_from_hotkey("ctrl+c") is None


def test_install_signal_handlers() -> None:
    ctrl = ShutdownController()
    ctrl.install_signal_handlers()
