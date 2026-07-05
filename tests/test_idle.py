"""Tests de detección de entorno e idle (mockeado)."""


# pylint: disable=missing-function-docstring,missing-class-docstring,protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

import sys
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from utils import app
from utils.const import Display
from utils.idle import DesktopIdleMonitor, MacIdleMonitor, WindowsIdleMonitor


def test_is_wayland_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert app.is_wayland_session() is True
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    assert app.is_wayland_session() is False


def test_is_display_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert app.is_display(Display.WAYLAND) is True


def test_is_display_x11_with_display(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("DISPLAY", ":0")
    assert app.is_display(Display.X11) is True


def test_is_display_x11_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("DISPLAY", ":0")
    assert app.is_display(Display.X11) is False


def test_is_display_x11_no_display(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    assert app.is_display(Display.X11) is False


def test_is_display_x11_without_display_on_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    assert app.is_display(Display.X11) is False


def test_is_display_non_x11_wayland() -> None:
    assert app.is_display(Display.WIN32) is False


def _mock_windll() -> SimpleNamespace:
    user32 = MagicMock()
    kernel32 = MagicMock()
    user32.GetLastInputInfo = MagicMock()
    user32.SystemParametersInfoW = MagicMock(return_value=0)
    user32.OpenInputDesktop = MagicMock(return_value=1)
    user32.CloseDesktop = MagicMock()
    kernel32.GetTickCount = MagicMock(return_value=5000)
    return SimpleNamespace(user32=user32, kernel32=kernel32)


def test_windows_idle_monitor_idle_and_unlocked() -> None:
    import utils.idle as idle

    with patch.object(idle.ctypes, "windll", _mock_windll(), create=True):
        monitor = WindowsIdleMonitor()
        monitor.GetLastInputInfo = MagicMock()
        monitor.GetTickCount = MagicMock(return_value=5000)
        monitor.lastInputInfo.dwTime = 1000
        assert monitor.get_idle_sec() == 4.0
        assert monitor.is_extended_away() is False


def test_windows_idle_monitor_saver_running() -> None:
    import utils.idle as idle

    def fake_spi(_code: int, _zero: int, ref: object, _flags: int) -> int:
        ref._obj.value = 1  # type: ignore[attr-defined]
        return 1

    with patch.object(idle.ctypes, "windll", _mock_windll(), create=True):
        monitor = WindowsIdleMonitor()
        monitor.SystemParametersInfo = fake_spi
        assert monitor.is_extended_away() is True


def test_windows_idle_monitor_locked_progression() -> None:
    import utils.idle as idle

    windll = _mock_windll()
    windll.user32.OpenInputDesktop = MagicMock(return_value=0)
    with patch.object(idle.ctypes, "windll", windll, create=True):
        monitor = WindowsIdleMonitor()
        monitor.SystemParametersInfo = MagicMock(return_value=0)
        assert monitor.is_extended_away() is False
        assert monitor.is_extended_away() is False
        monitor._locked_time = time.time() - 20
        assert monitor.is_extended_away() is True


def test_mac_idle_monitor() -> None:
    quartz = MagicMock()
    quartz.CGEventSourceSecondsSinceLastEventType = MagicMock(return_value=12.5)
    quartz.kCGEventSourceStateCombinedSessionState = 0
    with patch.dict(sys.modules, {"Quartz": quartz}):
        monitor = MacIdleMonitor()
        assert monitor.get_idle_sec() == 12.5
        assert monitor.is_extended_away() is False


@pytest.mark.skipif(sys.platform == "win32", reason="DesktopIdleMonitor")
def test_desktop_idle_monitor_unavailable_on_linux() -> None:
    if sys.platform == "darwin":
        pytest.skip("darwin usa MacIdleMonitor")
    monitor = DesktopIdleMonitor()
    assert monitor.is_available() is False
    assert monitor.get_idle_sec() == 0


@pytest.mark.skipif(sys.platform not in ("win32", "darwin"), reason="solo win/mac")
def test_desktop_idle_monitor_available() -> None:
    with patch("utils.idle.WindowsIdleMonitor") as mock_cls:
        mock_cls.return_value.get_idle_sec.return_value = 2
        monitor = DesktopIdleMonitor()
        assert monitor.is_available()
        assert monitor.get_idle_sec() == 2


@pytest.mark.skipif(sys.platform in ("win32", "darwin"), reason="DBus idle solo Linux")
def test_dbus_and_idle_monitor_linux() -> None:
    from utils import dbus_idle

    with patch.object(dbus_idle, "get_session_idle_ms", return_value=8000):
        freedesktop = dbus_idle.DBusFreedesktopIdleMonitor()
        assert freedesktop.get_idle_sec() == 8
        freedesktop.set_extended_away(True)
        assert freedesktop.is_extended_away() is True

        gnome = dbus_idle.DBusGnomeIdleMonitor()
        assert gnome.get_idle_sec() == 8

    with patch.object(
        dbus_idle,
        "get_session_idle_ms",
        side_effect=dbus_idle.DBusIdleError("fail"),
    ):
        with pytest.raises(dbus_idle.DBusIdleError):
            dbus_idle.DBusFreedesktopIdleMonitor()

    freedesktop = dbus_idle.DBusFreedesktopIdleMonitor.__new__(dbus_idle.DBusFreedesktopIdleMonitor)
    freedesktop.last_idle_time = 3
    with patch.object(
        freedesktop,
        "_get_idle_sec_fail",
        side_effect=dbus_idle.DBusIdleError("fail"),
    ):
        assert freedesktop.get_idle_sec() == 3


@pytest.mark.skipif(sys.platform in ("win32", "darwin"), reason="LinuxIdleMonitor")
def test_linux_idle_monitor() -> None:
    import utils.idle as idle

    backend = MagicMock()
    backend.get_idle_sec.return_value = 42

    with patch.object(idle.LinuxIdleMonitor, "_get_idle_monitor", return_value=backend):
        monitor = idle.LinuxIdleMonitor()
    assert monitor.is_available()
    assert monitor.get_idle_sec() == 42

    with patch.object(idle.LinuxIdleMonitor, "_get_idle_monitor", return_value=None):
        monitor = idle.LinuxIdleMonitor()
    assert not monitor.is_available()
    assert monitor.get_idle_sec() == 0


@pytest.mark.skipif(sys.platform in ("win32", "darwin"), reason="_get_idle_monitor")
def test_get_idle_monitor_fallback_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    import utils.idle as idle
    from utils.dbus_idle import DBusIdleError

    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")

    with (
        patch.object(idle, "DBusFreedesktopIdleMonitor", side_effect=DBusIdleError("no")),
        patch.object(idle, "DBusGnomeIdleMonitor", side_effect=DBusIdleError("no")),
        patch.object(idle, "DBusMateIdleMonitor", side_effect=DBusIdleError("no")),
        patch.object(idle, "XssIdleMonitor", side_effect=OSError("no xss")),
    ):
        assert idle.LinuxIdleMonitor._get_idle_monitor() is None

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    with (
        patch.object(idle, "DBusFreedesktopIdleMonitor", side_effect=DBusIdleError("no")),
        patch.object(idle, "DBusGnomeIdleMonitor", side_effect=DBusIdleError("no")),
        patch.object(idle, "DBusMateIdleMonitor", side_effect=DBusIdleError("no")),
    ):
        assert idle.LinuxIdleMonitor._get_idle_monitor() is None


@pytest.mark.skipif(sys.platform in ("win32", "darwin"), reason="XssIdleMonitor")
def test_xss_idle_monitor() -> None:
    import utils.idle as idle

    class FakeContents:
        idle = 4500

    class FakeInfo:
        contents = FakeContents()

    mock_x11 = MagicMock()
    mock_xss = MagicMock()
    display = MagicMock()
    mock_x11.XOpenDisplay.return_value = display
    mock_x11.XDefaultRootWindow.return_value = 1
    mock_xss.XScreenSaverQueryExtension.return_value = 1
    mock_xss.XScreenSaverAllocInfo.return_value = FakeInfo()
    mock_xss.XScreenSaverQueryInfo.return_value = 1

    def load_library(path: str) -> MagicMock:
        if "Xss" in path:
            return mock_xss
        return mock_x11

    with (
        patch("utils.idle.ctypes.util.find_library", side_effect=lambda lib: f"/lib/{lib}.so"),
        patch("utils.idle.ctypes.cdll.LoadLibrary", side_effect=load_library),
    ):
        monitor = idle.XssIdleMonitor()
        assert monitor.get_idle_sec() == 4
        monitor.set_extended_away(True)
        assert monitor.is_extended_away() is False
        mock_xss.XScreenSaverQueryInfo.return_value = 0
        assert monitor.get_idle_sec() == 0


def test_desktop_idle_monitor_darwin_branch() -> None:
    import utils.idle as idle

    backend = MagicMock()
    backend.get_idle_sec.return_value = 4
    with (
        patch.object(idle.sys, "platform", "darwin"),
        patch.object(idle, "MacIdleMonitor", return_value=backend),
    ):
        monitor = idle.DesktopIdleMonitor()
        assert monitor.is_available()
        assert monitor.get_idle_sec() == 4


def test_monitor_alias_desktop_on_win32_import() -> None:
    """Cubre Monitor = DesktopIdleMonitor() en plataformas win32."""
    import importlib

    import utils.idle as idle

    orig = sys.platform
    windll = _mock_windll()
    try:
        with (
            patch.object(idle.sys, "platform", "win32"),
            patch.object(idle.ctypes, "windll", windll, create=True),
        ):
            importlib.reload(idle)
        assert isinstance(idle.Monitor, idle.DesktopIdleMonitor)
        assert idle.Monitor.is_available()
    finally:
        with patch.object(idle.sys, "platform", orig):
            importlib.reload(idle)


def test_desktop_idle_monitor_win32_branch() -> None:
    import utils.idle as idle

    backend = MagicMock()
    backend.get_idle_sec.return_value = 7
    with (
        patch.object(idle.sys, "platform", "win32"),
        patch.object(idle, "WindowsIdleMonitor", return_value=backend),
    ):
        monitor = idle.DesktopIdleMonitor()
        assert monitor.is_available()
        assert monitor.get_idle_sec() == 7


@pytest.mark.skipif(sys.platform in ("win32", "darwin"), reason="LinuxIdleMonitor sin backend")
def test_linux_idle_monitor_unavailable() -> None:
    import utils.idle as idle

    with patch.object(idle.LinuxIdleMonitor, "_get_idle_monitor", return_value=None):
        monitor = idle.LinuxIdleMonitor()
        assert not monitor.is_available()


@pytest.mark.skipif(sys.platform in ("win32", "darwin"), reason="XssIdleMonitor errores")
def test_xss_idle_monitor_init_failures() -> None:
    import utils.idle as idle

    with patch("utils.idle.ctypes.util.find_library", return_value=None):
        with pytest.raises(OSError, match="libX11"):
            idle.XssIdleMonitor()

    mock_x11 = MagicMock()
    mock_x11.XOpenDisplay.return_value = MagicMock()

    def load_library(path: str) -> MagicMock:
        if "Xss" in path:
            raise OSError("no xss")
        return mock_x11

    with (
        patch("utils.idle.ctypes.util.find_library", side_effect=lambda lib: f"/lib/{lib}.so"),
        patch("utils.idle.ctypes.cdll.LoadLibrary", side_effect=load_library),
    ):
        with pytest.raises(OSError, match="no xss"):
            idle.XssIdleMonitor()

    mock_x11.XOpenDisplay.return_value = None
    with (
        patch("utils.idle.ctypes.util.find_library", side_effect=lambda lib: f"/lib/{lib}.so"),
        patch("utils.idle.ctypes.cdll.LoadLibrary", return_value=mock_x11),
    ):
        with pytest.raises(OSError, match="X Display"):
            idle.XssIdleMonitor()

    mock_x11.XOpenDisplay.return_value = MagicMock()
    mock_xss_ext = MagicMock()
    mock_xss_ext.XScreenSaverQueryExtension.return_value = 0

    def load_no_extension(path: str) -> MagicMock:
        return mock_xss_ext if "Xss" in path else mock_x11

    with (
        patch("utils.idle.ctypes.util.find_library", side_effect=lambda lib: f"/lib/{lib}.so"),
        patch("utils.idle.ctypes.cdll.LoadLibrary", side_effect=load_no_extension),
    ):
        with pytest.raises(OSError, match="Extension not available"):
            idle.XssIdleMonitor()

    mock_xss = MagicMock()
    mock_xss.XScreenSaverQueryExtension.return_value = 1
    mock_xss.XScreenSaverAllocInfo.return_value = None

    def load_xss(path: str) -> MagicMock:
        return mock_xss if "Xss" in path else mock_x11

    with (
        patch("utils.idle.ctypes.util.find_library", side_effect=lambda lib: f"/lib/{lib}.so"),
        patch("utils.idle.ctypes.cdll.LoadLibrary", side_effect=load_xss),
    ):
        with pytest.raises(OSError, match="Out of Memory"):
            idle.XssIdleMonitor()

    mock_x11_only = MagicMock()
    with (
        patch(
            "utils.idle.ctypes.util.find_library",
            side_effect=lambda lib: "/lib/X11.so" if lib == "X11" else None,
        ),
        patch("utils.idle.ctypes.cdll.LoadLibrary", return_value=mock_x11_only),
    ):
        with pytest.raises(OSError, match="libXss"):
            idle.XssIdleMonitor()


@pytest.mark.skipif(sys.platform in ("win32", "darwin"), reason="DBusMateIdleMonitor")
def test_mate_idle_monitor_linux() -> None:
    from utils import dbus_idle

    with patch.object(dbus_idle, "get_session_idle_ms", return_value=5000):
        monitor = dbus_idle.DBusMateIdleMonitor()
        assert monitor.get_idle_sec() == 5
        monitor.set_extended_away(True)
        assert monitor.is_extended_away() is True


@pytest.mark.skipif(sys.platform in ("win32", "darwin"), reason="DBusMateIdleMonitor error")
def test_mate_idle_monitor_dbus_error() -> None:
    from utils import dbus_idle

    with patch.object(
        dbus_idle,
        "get_session_idle_ms",
        side_effect=dbus_idle.DBusIdleError("fail"),
    ):
        with pytest.raises(dbus_idle.DBusIdleError):
            dbus_idle.DBusMateIdleMonitor()

    monitor = dbus_idle.DBusMateIdleMonitor.__new__(dbus_idle.DBusMateIdleMonitor)
    monitor.last_idle_time = 3
    with patch.object(monitor, "_get_idle_sec_fail", side_effect=dbus_idle.DBusIdleError("fail")):
        assert monitor.get_idle_sec() == 3


@pytest.mark.skipif(sys.platform in ("win32", "darwin"), reason="_get_idle_monitor éxito")
def test_get_idle_monitor_success_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    import utils.idle as idle
    from utils.dbus_idle import DBusIdleError

    with patch.object(idle, "DBusFreedesktopIdleMonitor", return_value=MagicMock()):
        backend = idle.LinuxIdleMonitor._get_idle_monitor()
        assert backend is not None

    with (
        patch.object(idle, "DBusFreedesktopIdleMonitor", side_effect=DBusIdleError("no")),
        patch.object(idle, "DBusGnomeIdleMonitor", return_value=MagicMock()),
    ):
        backend = idle.LinuxIdleMonitor._get_idle_monitor()
        assert backend is not None

    with (
        patch.object(idle, "DBusFreedesktopIdleMonitor", side_effect=DBusIdleError("no")),
        patch.object(idle, "DBusGnomeIdleMonitor", side_effect=DBusIdleError("no")),
        patch.object(idle, "DBusMateIdleMonitor", return_value=MagicMock()),
    ):
        backend = idle.LinuxIdleMonitor._get_idle_monitor()
        assert backend is not None

    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    with (
        patch.object(idle, "DBusFreedesktopIdleMonitor", side_effect=DBusIdleError("no")),
        patch.object(idle, "DBusGnomeIdleMonitor", side_effect=DBusIdleError("no")),
        patch.object(idle, "DBusMateIdleMonitor", side_effect=DBusIdleError("no")),
        patch.object(idle, "XssIdleMonitor", return_value=MagicMock()),
    ):
        backend = idle.LinuxIdleMonitor._get_idle_monitor()
        assert backend is not None
