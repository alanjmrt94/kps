# Copyright (C) 2003-2014 Yann Leboulanger <asterix AT lagaule.org>
# Copyright (C) 2005-2006 Nikos Kouremenos <kourem AT gmail.com>
# Copyright (C) 2007 Jean-Marie Traissard <jim AT lapin.org>
# Copyright (C) 2008 Mateusz Biliński <mateusz AT bilinski.it>
# Copyright (C) 2008 Thorsten P. 'dGhvcnN0ZW5wIEFUIHltYWlsIGNvbQ==\n'.decode("base64")
# Copyright (C) 2018 Philipp Hörist <philipp AT hoerist.com>
#
# This file is part of Gajim.
#
# Gajim is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation; version 3 only.
#
# Gajim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Gajim. If not, see <http://www.gnu.org/licenses/>.
#
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,invalid-name,too-few-public-methods,ungrouped-imports

import ctypes
import ctypes.util
import logging
import sys
import time
from typing import TYPE_CHECKING, Protocol, cast

log = logging.getLogger('kps.u.idle')


class WindowsIdleMonitor:
    def __init__(self):
        self.OpenInputDesktop = ctypes.windll.user32.OpenInputDesktop
        self.CloseDesktop = ctypes.windll.user32.CloseDesktop
        self.SystemParametersInfo = ctypes.windll.user32.SystemParametersInfoW
        self.GetTickCount = ctypes.windll.kernel32.GetTickCount
        self.GetLastInputInfo = ctypes.windll.user32.GetLastInputInfo

        self._locked_time = None

        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_uint)]

        self.lastInputInfo = LASTINPUTINFO()
        self.lastInputInfo.cbSize = ctypes.sizeof(self.lastInputInfo)

    def get_idle_sec(self):
        self.GetLastInputInfo(ctypes.byref(self.lastInputInfo))
        return float(self.GetTickCount() - self.lastInputInfo.dwTime) / 1000

    def is_extended_away(self):
        # Check if Screen Saver is running
        # 0x72 is SPI_GETSCREENSAVERRUNNING
        saver_runing = ctypes.c_int(0)
        info = self.SystemParametersInfo(
            0x72, 0, ctypes.byref(saver_runing), 0)
        if info and saver_runing.value:
            return True

        # Check if Screen is locked
        # Also a UAC prompt counts as locked
        # So just return True if we are more than 10 seconds locked
        desk = self.OpenInputDesktop(0, False, 0)
        unlocked = bool(desk)
        self.CloseDesktop(desk)

        if unlocked:
            self._locked_time = None
            return False

        if self._locked_time is None:
            self._locked_time = time.time()
            return False

        threshold = time.time() - 10
        if threshold > self._locked_time:
            return True
        return False


class MacIdleMonitor:
    """Tiempo idle en macOS vía Quartz (sin PyGObject)."""

    def __init__(self):
        from Quartz import (  # pylint: disable=import-error,import-outside-toplevel
            CGEventSourceSecondsSinceLastEventType,
            kCGEventSourceStateCombinedSessionState,
        )

        self._seconds_since = CGEventSourceSecondsSinceLastEventType
        self._source_state = kCGEventSourceStateCombinedSessionState

    def get_idle_sec(self):
        return self._seconds_since(self._source_state)

    def is_extended_away(self):
        return False


if TYPE_CHECKING:

    class _MonitorApi(Protocol):
        """API mínima compartida por IdleMonitor y DesktopIdleMonitor."""

        def is_available(self) -> bool: ...

        def get_idle_sec(self) -> float | int: ...


class DesktopIdleMonitor:
    """Monitor ligero para Windows y macOS (sin GObject/GLib)."""

    def __init__(self):
        if sys.platform == 'win32':
            self._idle_monitor = WindowsIdleMonitor()
        elif sys.platform == 'darwin':
            self._idle_monitor = MacIdleMonitor()
        else:
            self._idle_monitor = None

    def is_available(self):
        return self._idle_monitor is not None

    def get_idle_sec(self):
        if self._idle_monitor is None:
            return 0
        return self._idle_monitor.get_idle_sec()


if sys.platform not in ('win32', 'darwin'):
    from utils import app
    from utils.dbus_idle import (
        DBusFreedesktopIdleMonitor,
        DBusGnomeIdleMonitor,
        DBusIdleError,
        DBusMateIdleMonitor,
    )

    class XssIdleMonitor:
        def __init__(self):

            self._extended_away = False

            class XScreenSaverInfo(ctypes.Structure):
                _fields_ = [
                    ('window', ctypes.c_ulong),
                    ('state', ctypes.c_int),
                    ('kind', ctypes.c_int),
                    ('til_or_since', ctypes.c_ulong),
                    ('idle', ctypes.c_ulong),
                    ('eventMask', ctypes.c_ulong)
                ]

            XScreenSaverInfo_p = ctypes.POINTER(XScreenSaverInfo)

            display_p = ctypes.c_void_p
            xid = ctypes.c_ulong
            c_int_p = ctypes.POINTER(ctypes.c_int)

            libX11path = ctypes.util.find_library('X11')
            if libX11path is None:
                raise OSError('libX11 could not be found.')
            libX11 = ctypes.cdll.LoadLibrary(libX11path)
            libX11.XOpenDisplay.restype = display_p
            libX11.XOpenDisplay.argtypes = (ctypes.c_char_p,)
            libX11.XDefaultRootWindow.restype = xid
            libX11.XDefaultRootWindow.argtypes = (display_p,)

            libXsspath = ctypes.util.find_library('Xss')
            if libXsspath is None:
                raise OSError('libXss could not be found.')
            self.libXss = ctypes.cdll.LoadLibrary(libXsspath)
            self.libXss.XScreenSaverQueryExtension.argtypes = display_p, c_int_p, c_int_p
            self.libXss.XScreenSaverAllocInfo.restype = XScreenSaverInfo_p
            self.libXss.XScreenSaverQueryInfo.argtypes = (
                display_p, xid, XScreenSaverInfo_p)

            self.dpy_p = libX11.XOpenDisplay(None)
            if self.dpy_p is None:
                raise OSError('Could not open X Display.')

            _event_basep = ctypes.c_int()
            _error_basep = ctypes.c_int()
            extension = self.libXss.XScreenSaverQueryExtension(
                self.dpy_p, ctypes.byref(_event_basep), ctypes.byref(_error_basep))
            if extension == 0:
                raise OSError('XScreenSaver Extension not available on display.')

            self.xss_info_p = self.libXss.XScreenSaverAllocInfo()
            if self.xss_info_p is None:
                raise OSError('XScreenSaverAllocInfo: Out of Memory.')

            self.rootwindow = libX11.XDefaultRootWindow(self.dpy_p)

        def get_idle_sec(self):
            info = self.libXss.XScreenSaverQueryInfo(
                self.dpy_p, self.rootwindow, self.xss_info_p)
            if info == 0:
                return info
            return int(self.xss_info_p.contents.idle / 1000)

        def set_extended_away(self, state):
            self._extended_away = state

        def is_extended_away(self):
            return False

    class LinuxIdleMonitor:
        """Monitor idle en Linux (D-Bus o XScreenSaver); sin GObject."""

        def __init__(self) -> None:
            self._idle_monitor = self._get_idle_monitor()

        def is_available(self) -> bool:
            return self._idle_monitor is not None

        def get_idle_sec(self) -> float | int:
            if self._idle_monitor is None:
                return 0
            return cast(float | int, self._idle_monitor.get_idle_sec())

        @staticmethod
        def _get_idle_monitor():
            try:
                monitor = DBusFreedesktopIdleMonitor()
                log.info('Monitor idle: D-Bus (org.freedesktop.ScreenSaver)')
                return monitor
            except DBusIdleError as error:
                log.debug('D-Bus ScreenSaver no disponible: %s', error)

            try:
                monitor = DBusGnomeIdleMonitor()
                log.info('Monitor idle: D-Bus (org.gnome.Mutter.IdleMonitor)')
                return monitor
            except DBusIdleError as error:
                log.debug('D-Bus Mutter IdleMonitor no disponible: %s', error)

            try:
                monitor = DBusMateIdleMonitor()
                log.info('Monitor idle: D-Bus (org.mate.ScreenSaver)')
                return monitor
            except DBusIdleError as error:
                log.debug('D-Bus MATE ScreenSaver no disponible: %s', error)

            if app.is_wayland_session():
                log.warning(
                    'Sin monitor idle en Wayland (D-Bus no disponible). '
                    'Usa sesión X11 o un compositor con D-Bus idle.')
                return None

            try:
                monitor = XssIdleMonitor()
                log.info('Monitor idle: XScreenSaver (X11)')
                return monitor
            except OSError as error:
                log.debug('XScreenSaver no disponible: %s', error)
            return None

    Monitor = cast("_MonitorApi", LinuxIdleMonitor())
else:
    Monitor = cast("_MonitorApi", DesktopIdleMonitor())
