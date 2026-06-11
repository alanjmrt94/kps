"""Tests de modo daemon."""


# pylint: disable=missing-function-docstring,missing-class-docstring,protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from utils import daemon


def test_is_foreground_child() -> None:
    assert daemon.is_foreground_child(["kps.py", "--foreground", "-t", "5"]) is True
    assert daemon.is_foreground_child(["kps.py", "-d"]) is False
    with patch.object(daemon.sys, "argv", ["kps.py", "--foreground"]):
        assert daemon.is_foreground_child() is True


def test_strip_daemon_flags() -> None:
    argv = ["kps.py", "-d", "--daemon", "--foreground", "-t", "5"]
    assert daemon.strip_daemon_flags(argv) == ["kps.py", "-t", "5"]


def test_spawn_daemon_skips_foreground_child() -> None:
    daemon.spawn_daemon(["kps.py", "--foreground", "-t", "5"])


def test_spawn_daemon_unix() -> None:
    mock_proc = MagicMock(pid=4242)
    with (
        patch.object(daemon.subprocess, "Popen", return_value=mock_proc) as mock_popen,
        patch.object(daemon.sys, "platform", "linux"),
        patch.object(daemon.sys, "executable", "/usr/bin/python3"),
        patch.object(daemon.sys, "exit", side_effect=SystemExit) as mock_exit,
    ):
        with pytest.raises(SystemExit):
            daemon.spawn_daemon(["kps.py", "-d", "-t", "5"])
        mock_popen.assert_called_once()
        mock_exit.assert_called_once_with(0)


def test_spawn_daemon_windows() -> None:
    mock_proc = MagicMock(pid=999)
    with (
        patch.object(daemon.subprocess, "Popen", return_value=mock_proc) as mock_popen,
        patch.object(daemon.subprocess, "DETACHED_PROCESS", 8, create=True),
        patch.object(
            daemon.subprocess, "CREATE_NEW_PROCESS_GROUP", 512, create=True
        ),
        patch.object(daemon.sys, "platform", "win32"),
        patch.object(daemon.sys, "executable", "C:\\Python\\python.exe"),
        patch.object(daemon.sys, "exit", side_effect=SystemExit),
    ):
        with pytest.raises(SystemExit):
            daemon.spawn_daemon(["kps.py", "-d"])
        kwargs = mock_popen.call_args.kwargs
        assert "creationflags" in kwargs


def test_spawn_daemon_unix_prints_kill_hint(capsys: pytest.CaptureFixture[str]) -> None:
    mock_proc = MagicMock(pid=4242)
    with (
        patch.object(daemon.subprocess, "Popen", return_value=mock_proc),
        patch.object(daemon.sys, "platform", "linux"),
        patch.object(daemon.sys, "executable", "/usr/bin/python3"),
        patch.object(daemon.sys, "exit", side_effect=SystemExit),
    ):
        with pytest.raises(SystemExit):
            daemon.spawn_daemon(["kps.py", "-d"])
    assert "kill -TERM" in capsys.readouterr().out


def test_pid_file_roundtrip(tmp_path: Path) -> None:
    pid_file = tmp_path / "kps.pid"
    daemon.write_pid_file(pid_file)
    assert pid_file.read_text(encoding="utf-8") == str(os.getpid())
    daemon.remove_pid_file(pid_file)
    assert not pid_file.exists()


def test_remove_pid_file_none_and_oserror(tmp_path: Path) -> None:
    daemon.remove_pid_file(None)
    pid_file = tmp_path / "kps.pid"
    pid_file.write_text("1", encoding="utf-8")
    with patch.object(Path, "unlink", side_effect=OSError("busy")):
        daemon.remove_pid_file(pid_file)
