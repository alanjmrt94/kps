"""Tests de hotkey multiplataforma."""

from __future__ import annotations

from utils.hotkey import parse_function_key, windows_vk_from_hotkey


def test_parse_function_key_valid() -> None:
    assert parse_function_key("f12") == "F12"
    assert parse_function_key(" F1 ") == "F1"


def test_parse_function_key_invalid() -> None:
    assert parse_function_key("ctrl+c") is None
    assert parse_function_key("F13") is None


def test_windows_vk_from_hotkey() -> None:
    assert windows_vk_from_hotkey("F1") == 0x70
    assert windows_vk_from_hotkey("F12") == 0x7B
