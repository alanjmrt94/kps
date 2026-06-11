"""Tests de modo daemon."""

from __future__ import annotations

import os
from pathlib import Path

from utils.daemon import is_foreground_child, remove_pid_file, strip_daemon_flags, write_pid_file


def test_is_foreground_child() -> None:
    assert is_foreground_child(["kps.py", "--foreground", "-t", "5"]) is True
    assert is_foreground_child(["kps.py", "-d"]) is False


def test_strip_daemon_flags() -> None:
    argv = ["kps.py", "-d", "--daemon", "--foreground", "-t", "5"]
    assert strip_daemon_flags(argv) == ["kps.py", "-t", "5"]


def test_pid_file_roundtrip(tmp_path: Path) -> None:
    pid_file = tmp_path / "kps.pid"
    write_pid_file(pid_file)
    assert pid_file.read_text(encoding="utf-8") == str(os.getpid())
    remove_pid_file(pid_file)
    assert not pid_file.exists()


def test_remove_pid_file_none() -> None:
    remove_pid_file(None)


def test_spawn_daemon_skips_foreground_child() -> None:
    from utils.daemon import spawn_daemon

    spawn_daemon(["kps.py", "--foreground", "-t", "5"])
