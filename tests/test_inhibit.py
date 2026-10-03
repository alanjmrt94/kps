"""Tests de inhibición idle/sleep del SO."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

from unittest.mock import MagicMock, patch

from utils.inhibit import IdleInhibit


def test_start_linux_without_systemd() -> None:
    """Comprueba start linux without systemd."""
    inhibitor = IdleInhibit()
    with (
        patch("utils.inhibit.sys.platform", "linux"),
        patch("utils.inhibit.shutil.which", return_value=None),
    ):
        assert inhibitor.start() is False
        assert inhibitor.running is False


def test_start_stop_unix_process() -> None:
    """Comprueba start stop unix process."""
    inhibitor = IdleInhibit()
    proc = MagicMock()
    proc.poll.return_value = None
    proc.pid = 42
    with (
        patch("utils.inhibit.sys.platform", "linux"),
        patch("utils.inhibit.shutil.which", return_value="/usr/bin/systemd-inhibit"),
        patch("utils.inhibit.subprocess.Popen", return_value=proc),
    ):
        assert inhibitor.start() is True
        assert inhibitor.running is True
        inhibitor.stop()
        proc.terminate.assert_called_once()


def test_start_unix_oserror() -> None:
    """Comprueba start unix oserror."""
    inhibitor = IdleInhibit()
    with (
        patch("utils.inhibit.sys.platform", "darwin"),
        patch("utils.inhibit.subprocess.Popen", side_effect=OSError("no")),
    ):
        assert inhibitor.start() is False


def test_start_windows() -> None:
    """Comprueba start windows."""
    inhibitor = IdleInhibit()
    mock_ct = MagicMock()
    with (
        patch("utils.inhibit.sys.platform", "win32"),
        patch.dict("sys.modules", {"ctypes": mock_ct}),
    ):
        assert inhibitor.start() is True
        inhibitor.stop()
        assert inhibitor.running is False


def test_start_already_running() -> None:
    """Comprueba start already running."""
    inhibitor = IdleInhibit()
    inhibitor._windows_active = True
    assert inhibitor.start() is True


def test_stop_kills_on_timeout() -> None:
    """Comprueba stop kills on timeout."""
    inhibitor = IdleInhibit()
    proc = MagicMock()
    proc.poll.return_value = None
    proc.wait.side_effect = [
        __import__("subprocess").TimeoutExpired(cmd="x", timeout=3),
        None,
    ]
    inhibitor._process = proc
    inhibitor.stop()
    proc.kill.assert_called_once()


def test_start_windows_attribute_error() -> None:
    """Comprueba start windows attribute error."""
    mock_ct = MagicMock()
    mock_ct.windll.kernel32.SetThreadExecutionState.side_effect = AttributeError("no")
    with (
        patch("utils.inhibit.sys.platform", "win32"),
        patch.dict("sys.modules", {"ctypes": mock_ct}),
    ):
        assert IdleInhibit().start() is False


def test_stop_already_exited_process() -> None:
    """Comprueba stop already exited process."""
    inhibitor = IdleInhibit()
    proc = MagicMock()
    proc.poll.return_value = 0
    inhibitor._process = proc
    inhibitor.stop()
    proc.terminate.assert_not_called()


def test_context_manager_calls_stop() -> None:
    """Comprueba context manager calls stop."""
    inhibitor = IdleInhibit()
    with (
        patch.object(inhibitor, "start", return_value=True),
        patch.object(inhibitor, "stop") as stop,
    ):
        with inhibitor:
            pass
        stop.assert_called_once()
