"""Tests de detección de entorno e idle (sin GObject en CI)."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from utils import app
from utils.const import Display
from utils.idle import DesktopIdleMonitor, WindowsIdleMonitor


def test_is_wayland_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert app.is_wayland_session() is True
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    assert app.is_wayland_session() is False


def test_is_display_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert app.is_display(Display.WAYLAND) is True


@patch("utils.app._gdk_display_class_name", side_effect=ImportError("no gdk"))
def test_is_display_x11_without_gdk(_mock: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    assert app.is_display(Display.X11) is True


def test_is_display_non_x11_wayland() -> None:
    assert app.is_display(Display.WIN32) is False


@patch("utils.app._gdk_display_class_name", return_value=None)
def test_is_display_x11_no_default_display(
    _mock: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    assert app.is_display(Display.X11) is False


@pytest.mark.skipif(sys.platform != "win32", reason="WindowsIdleMonitor solo en Windows")
def test_windows_idle_monitor_get_idle_sec() -> None:
    monitor = WindowsIdleMonitor()
    with (
        patch.object(monitor, "GetLastInputInfo"),
        patch.object(monitor, "GetTickCount", return_value=5000),
        patch.object(monitor.lastInputInfo, "dwTime", 1000, create=True),
    ):
        assert monitor.get_idle_sec() == 4.0


@pytest.mark.skipif(
    sys.platform not in ("win32", "darwin"),
    reason="DesktopIdleMonitor solo en Windows/macOS",
)
def test_desktop_idle_monitor_available() -> None:
    monitor = DesktopIdleMonitor()
    assert monitor.is_available() is True
    assert monitor.get_idle_sec() >= 0
