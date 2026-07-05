"""Tests de cliente D-Bus idle (sin PyGObject)."""


# pylint: disable=missing-function-docstring,missing-class-docstring,protected-access
from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from utils import dbus_idle


def test_parse_idle_ms_variants() -> None:
    assert dbus_idle._parse_idle_ms("(uint32 8000)") == 8000
    assert dbus_idle._parse_idle_ms("(uint64 12000)") == 12000
    assert dbus_idle._parse_idle_ms("u 5000") == 5000


def test_parse_idle_ms_invalid() -> None:
    with pytest.raises(dbus_idle.DBusIdleError):
        dbus_idle._parse_idle_ms("no data")


def test_run_checked_success() -> None:
    ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="(uint32 1)", stderr="")
    with patch.object(dbus_idle.subprocess, "run", return_value=ok):
        assert dbus_idle._run_checked(["gdbus"]) == "(uint32 1)"


def test_run_checked_failure() -> None:
    fail = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="Error")
    with patch.object(dbus_idle.subprocess, "run", return_value=fail):
        with pytest.raises(dbus_idle.DBusIdleError):
            dbus_idle._run_checked(["gdbus"])


def test_call_gdbus() -> None:
    ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="(uint32 3000)", stderr="")
    with patch.object(dbus_idle.subprocess, "run", return_value=ok):
        assert dbus_idle._call_gdbus("d", "/p", "i", "m") == 3000


def test_call_busctl() -> None:
    ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="u 4000", stderr="")
    with patch.object(dbus_idle.subprocess, "run", return_value=ok):
        assert dbus_idle._call_busctl("d", "/p", "i", "m") == 4000


def test_call_dbus_send() -> None:
    ok = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="method return sender=:1.1 -> uint32 6000",
        stderr="",
    )
    with patch.object(dbus_idle.subprocess, "run", return_value=ok):
        assert dbus_idle._call_dbus_send("d", "/p", "i", "m") == 6000


def test_pick_caller_prefers_gdbus() -> None:
    with patch.object(dbus_idle.shutil, "which", side_effect=lambda name: name == "gdbus"):
        caller = dbus_idle._pick_caller()
        assert caller is dbus_idle._call_gdbus


def test_pick_caller_no_client() -> None:
    with patch.object(dbus_idle.shutil, "which", return_value=None):
        with pytest.raises(dbus_idle.DBusIdleError, match="cliente D-Bus"):
            dbus_idle._pick_caller()


def test_gnome_idle_monitor_get_idle_error() -> None:
    with patch.object(dbus_idle, "get_session_idle_ms", return_value=7000):
        monitor = dbus_idle.DBusGnomeIdleMonitor()
    monitor.last_idle_time = 2
    with patch.object(monitor, "_get_idle_sec_fail", side_effect=dbus_idle.DBusIdleError("fail")):
        assert monitor.get_idle_sec() == 2
    monitor.set_extended_away(True)
    assert monitor.is_extended_away() is True


def test_freedesktop_get_idle_error() -> None:
    with patch.object(dbus_idle, "get_session_idle_ms", return_value=1000):
        monitor = dbus_idle.DBusFreedesktopIdleMonitor()
    with patch.object(monitor, "_get_idle_sec_fail", side_effect=dbus_idle.DBusIdleError("fail")):
        monitor.last_idle_time = 1
        assert monitor.get_idle_sec() == 1


def test_get_session_idle_ms() -> None:
    with patch.object(dbus_idle, "_pick_caller", return_value=MagicMock(return_value=9000)):
        assert dbus_idle.get_session_idle_ms("d", "/p", "i", "m") == 9000


def test_pick_caller_busctl_fallback() -> None:
    with patch.object(
        dbus_idle.shutil,
        "which",
        side_effect=lambda name: name == "busctl",
    ):
        assert dbus_idle._pick_caller() is dbus_idle._call_busctl


def test_pick_caller_dbus_send_fallback() -> None:
    with patch.object(
        dbus_idle.shutil,
        "which",
        side_effect=lambda name: name == "dbus-send",
    ):
        assert dbus_idle._pick_caller() is dbus_idle._call_dbus_send
