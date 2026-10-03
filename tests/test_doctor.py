"""Tests de kps doctor."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from utils.doctor import (
    CheckResult,
    check_appimage_signature,
    check_python,
    format_report,
    run_doctor,
)


def test_check_python_ok() -> None:
    """Comprueba check python ok."""
    result = check_python()
    assert result.ok is True
    assert "3." in result.detail


def test_format_report_failure() -> None:
    """Comprueba format report failure."""
    text = format_report(
        [
            CheckResult("A", True, "ok"),
            CheckResult("B", False, "fallo", hint="arreglá esto"),
            CheckResult("C", False, "aviso", optional=True),
        ]
    )
    assert "[OK] A" in text
    assert "[FALLO] B" in text
    assert "[AVISO] C" in text
    assert "crítica" in text


def test_run_doctor_exit_codes() -> None:
    """Comprueba run doctor exit codes."""
    ok = [CheckResult("x", True, "ok")]
    with patch("utils.doctor.collect_checks", return_value=ok):
        assert run_doctor() == 0
    bad = [CheckResult("x", False, "no")]
    with patch("utils.doctor.collect_checks", return_value=bad):
        assert run_doctor() == 1


def test_check_appimage_signature_not_appimage() -> None:
    """Comprueba check appimage signature not appimage."""
    with patch.dict("os.environ", {}, clear=False):
        env = {"APPIMAGE": ""}
        with patch("utils.doctor.os.environ.get", side_effect=lambda k, d=None: env.get(k, d)):
            result = check_appimage_signature()
    assert result.ok is True
    assert result.optional is True


def test_check_appimage_signature_pgp() -> None:
    """Comprueba check appimage signature pgp."""
    with (
        patch("utils.doctor.os.environ.get", return_value="/tmp/kps.AppImage"),
        patch("utils.doctor.Path.is_file", return_value=True),
        patch("utils.doctor.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(stdout="-----BEGIN PGP SIGNATURE-----\n", stderr="")
        result = check_appimage_signature()
    assert result.ok is True


def test_check_macos_notes_and_session() -> None:
    """Comprueba check macos notes and session."""
    from utils.doctor import check_macos_notes, check_session

    with patch.object(sys, "platform", "linux"):
        assert check_macos_notes().ok is True
    with patch.object(sys, "platform", "darwin"):
        note = check_macos_notes()
        assert "Accesibilidad" in note.hint
    result = check_session()
    assert result.name == "Sesión"


def test_check_uinput_missing(monkeypatch) -> None:
    """Comprueba check uinput missing."""
    from utils.doctor import check_uinput

    with patch.object(sys, "platform", "linux"):
        monkeypatch.setattr("utils.doctor.Path.exists", lambda self: False)
        result = check_uinput()
    assert result.ok is False


def test_check_dbus_idle_non_linux() -> None:
    """Comprueba check dbus idle non linux."""
    from utils.doctor import check_dbus_idle

    with patch.object(sys, "platform", "win32"):
        assert check_dbus_idle().optional is True


def test_check_python_too_old() -> None:
    """Comprueba check python too old."""
    with patch.object(sys, "version_info", (3, 9, 0)):
        result = check_python()
    assert result.ok is False


def test_check_session_wayland_without_display() -> None:
    """Comprueba check session wayland without display."""
    from utils.doctor import check_session

    env = {"XDG_SESSION_TYPE": "wayland", "WAYLAND_DISPLAY": "", "DISPLAY": ""}
    with (
        patch.object(sys, "platform", "linux"),
        patch("utils.doctor.os.environ.get", side_effect=lambda k, d=None: env.get(k) or d),
    ):
        result = check_session()
    assert result.ok is False


def test_check_dbus_clients_missing_and_found() -> None:
    """Comprueba check dbus clients missing and found."""
    from utils.doctor import check_dbus_clients

    with patch("utils.doctor.shutil.which", return_value=None):
        assert check_dbus_clients().ok is False
    with patch("utils.doctor.shutil.which", side_effect=lambda n: n if n == "gdbus" else None):
        assert "gdbus" in check_dbus_clients().detail


def test_check_dbus_idle_success_and_fail() -> None:
    """Comprueba check dbus idle success and fail."""
    from utils.dbus_idle import DBusIdleError
    from utils.doctor import check_dbus_idle

    with patch.object(sys, "platform", "linux"):
        with patch("utils.dbus_idle.get_session_idle_ms", return_value=1500):
            result = check_dbus_idle()
        assert result.ok is True
        with patch("utils.dbus_idle.get_session_idle_ms", side_effect=DBusIdleError("no")):
            with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
                failed = check_dbus_idle()
        assert failed.ok is False


def test_check_uinput_writable_and_denied() -> None:
    """Comprueba check uinput writable and denied."""
    from utils.doctor import check_uinput

    fake_node = MagicMock()
    fake_node.exists.return_value = True
    fake_node.__str__.return_value = "/dev/uinput"
    with patch.object(sys, "platform", "linux"), patch("utils.doctor.Path", return_value=fake_node):
        with patch("utils.doctor.os.access", return_value=True):
            assert check_uinput().ok is True
        with (
            patch("utils.doctor.os.access", return_value=False),
            patch("utils.doctor._user_groups", return_value=[("uinput", 1)]),
        ):
            denied = check_uinput()
        assert denied.ok is False
        with (
            patch("utils.doctor.os.access", return_value=False),
            patch("utils.doctor._user_groups", return_value=[("users", 1)]),
        ):
            no_group = check_uinput()
        assert "uinput" in no_group.hint


def test_check_uinput_non_linux() -> None:
    """Comprueba check uinput non linux."""
    from utils.doctor import check_uinput

    with patch.object(sys, "platform", "win32"):
        assert check_uinput().optional is True


def test_user_groups_keyerror() -> None:
    """Comprueba user groups keyerror."""
    from utils import doctor as doc

    mock_grp = MagicMock()
    mock_grp.getgrgid.side_effect = KeyError
    with (
        patch.object(doc, "grp", mock_grp),
        patch.object(doc.os, "getgroups", return_value=[999]),
    ):
        groups = doc._user_groups()
    assert groups[0][0] == "999"


def test_appimage_signature_branches() -> None:
    """Comprueba appimage signature branches."""

    with patch("utils.doctor.os.environ.get", return_value=None):
        with patch("utils.doctor.is_bundled", return_value=True):
            assert "empaquetado" in check_appimage_signature().detail
        with patch("utils.doctor.is_bundled", return_value=False):
            assert "no corre" in check_appimage_signature().detail
    with (
        patch("utils.doctor.os.environ.get", return_value="/no/such.AppImage"),
        patch("utils.doctor.Path.is_file", return_value=False),
    ):
        assert check_appimage_signature().ok is False
    with (
        patch("utils.doctor.os.environ.get", return_value="/tmp/kps.AppImage"),
        patch("utils.doctor.Path.is_file", return_value=True),
        patch("utils.doctor.subprocess.run", side_effect=OSError("boom")),
    ):
        assert check_appimage_signature().ok is False
    with (
        patch("utils.doctor.os.environ.get", return_value="/tmp/kps.AppImage"),
        patch("utils.doctor.Path.is_file", return_value=True),
        patch("utils.doctor.subprocess.run", return_value=MagicMock(stdout="", stderr="none")),
    ):
        unsigned = check_appimage_signature()
    assert unsigned.ok is False
    assert unsigned.optional is True


def test_collect_checks_non_linux() -> None:
    """Comprueba collect checks non linux."""
    from utils.doctor import collect_checks

    with patch.object(sys, "platform", "darwin"):
        checks = collect_checks()
    assert len(checks) >= 5


def test_check_inhibit_tool() -> None:
    """Comprueba check inhibit tool."""
    from utils.doctor import check_inhibit_tool

    with patch.object(sys, "platform", "win32"):
        assert "SetThreadExecutionState" in check_inhibit_tool().detail
    with (
        patch.object(sys, "platform", "darwin"),
        patch("utils.doctor.shutil.which", return_value=None),
    ):
        assert check_inhibit_tool().ok is False
    with (
        patch.object(sys, "platform", "darwin"),
        patch("utils.doctor.shutil.which", return_value="/usr/bin/caffeinate"),
    ):
        assert check_inhibit_tool().ok is True
    with (
        patch.object(sys, "platform", "linux"),
        patch("utils.doctor.shutil.which", return_value="/bin/si"),
    ):
        assert check_inhibit_tool().ok is True
    with (
        patch.object(sys, "platform", "linux"),
        patch("utils.doctor.shutil.which", return_value=None),
    ):
        assert check_inhibit_tool().ok is False
