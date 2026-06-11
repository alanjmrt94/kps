"""Tests del bucle principal (unidad, sin bucle infinito)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from utils.cli import KpsConfig
from utils.const import OsType
from utils.runner import interruptible_sleep, move_script_path, now_timestamp, run_loop, run_move
from utils.shutdown import ShutdownController


def test_now_timestamp_format() -> None:
    assert len(now_timestamp()) == 8


def test_move_script_path_linux() -> None:
    with patch.object(sys, "platform", "linux"), patch("utils.runner.os.name", OsType.UNIX):
        assert move_script_path().name == "move.py"


def test_move_script_path_windows() -> None:
    import pathlib

    import utils.runner as runner

    fake_root = pathlib.PosixPath("/fake/project")
    with (
        patch.object(runner.os, "name", OsType.WINDOWS),
        patch.object(runner, "project_root", return_value=fake_root),
    ):
        path = runner.move_script_path()
        assert path.name == "move_win.py"
        assert str(path) == "/fake/project/utils/move_win.py"


def test_move_script_path_macos() -> None:
    with patch.object(sys, "platform", "darwin"), patch("utils.runner.os.name", OsType.UNIX):
        assert move_script_path().name == "move_mac.py"


def test_run_move_success() -> None:
    ok = MagicMock(returncode=0, stderr="")
    with (
        patch("utils.runner.subprocess.run", return_value=ok),
        patch("utils.runner.venv_python", return_value=MagicMock()),
        patch("utils.runner.move_script_path", return_value=MagicMock()),
    ):
        run_move()


def test_run_move_failure() -> None:
    fail = MagicMock(returncode=1, stderr="error move")
    with (
        patch("utils.runner.subprocess.run", return_value=fail),
        patch("utils.runner.venv_python", return_value=MagicMock()),
        patch("utils.runner.move_script_path", return_value=MagicMock()),
    ):
        run_move()


def test_run_move_failure_no_stderr() -> None:
    fail = MagicMock(returncode=1, stderr="")
    with (
        patch("utils.runner.subprocess.run", return_value=fail),
        patch("utils.runner.venv_python", return_value=MagicMock()),
        patch("utils.runner.move_script_path", return_value=MagicMock()),
    ):
        run_move()


def test_interruptible_sleep_completes() -> None:
    ctrl = ShutdownController()
    assert interruptible_sleep(0.1, ctrl) is False


def test_interruptible_sleep_shutdown() -> None:
    ctrl = ShutdownController()
    ctrl.request("test")
    assert interruptible_sleep(2.0, ctrl) is True


@patch("utils.idle.Monitor")
@patch("utils.runner.interruptible_sleep", return_value=True)
def test_run_loop_exits_on_shutdown(_sleep: MagicMock, mock_monitor: MagicMock) -> None:
    mock_monitor.is_available.return_value = True
    mock_monitor.get_idle_sec.return_value = 0
    ctrl = ShutdownController()
    run_loop(KpsConfig(poll_interval=1), ctrl)


@patch("utils.idle.Monitor")
@patch("utils.runner.run_move")
@patch("utils.runner.interruptible_sleep", return_value=True)
def test_run_loop_moves_mouse(
    _sleep: MagicMock,
    mock_move: MagicMock,
    mock_monitor: MagicMock,
) -> None:
    mock_monitor.is_available.return_value = True
    mock_monitor.get_idle_sec.return_value = 99
    ctrl = ShutdownController()
    run_loop(KpsConfig(away_time=2), ctrl)
    mock_move.assert_called_once()


@patch("utils.idle.Monitor")
@patch("utils.runner.run_move")
@patch("utils.runner.interruptible_sleep", return_value=True)
def test_run_loop_dry_run_no_move(
    _sleep: MagicMock,
    mock_move: MagicMock,
    mock_monitor: MagicMock,
) -> None:
    mock_monitor.is_available.return_value = True
    mock_monitor.get_idle_sec.return_value = 99
    ctrl = ShutdownController()
    run_loop(KpsConfig(away_time=2, dry_run=True), ctrl)
    mock_move.assert_not_called()


@patch("utils.idle.Monitor")
def test_run_loop_monitor_unavailable(mock_monitor: MagicMock) -> None:
    mock_monitor.is_available.return_value = False
    with pytest.raises(SystemExit) as exc:
        run_loop(KpsConfig())
    assert exc.value.code == 1


@patch("utils.idle.Monitor")
@patch("utils.runner.interruptible_sleep", side_effect=[False, True])
def test_run_loop_activity_branch(
    _sleep: MagicMock,
    mock_monitor: MagicMock,
) -> None:
    mock_monitor.is_available.return_value = True
    mock_monitor.get_idle_sec.return_value = 0
    ctrl = ShutdownController()
    run_loop(KpsConfig(poll_interval=1), ctrl)


@patch("utils.idle.Monitor")
def test_run_loop_shutdown_before_loop(mock_monitor: MagicMock) -> None:
    mock_monitor.is_available.return_value = True
    ctrl = ShutdownController()
    ctrl.request("ya detenido")
    run_loop(KpsConfig(), ctrl)


@patch("utils.idle.Monitor")
@patch("utils.runner.run_move")
@patch("utils.runner.interruptible_sleep", side_effect=[False, True])
def test_run_loop_move_then_shutdown(
    _sleep: MagicMock,
    mock_move: MagicMock,
    mock_monitor: MagicMock,
) -> None:
    mock_monitor.is_available.return_value = True
    mock_monitor.get_idle_sec.return_value = 99
    ctrl = ShutdownController()
    run_loop(KpsConfig(away_time=2, poll_interval=1), ctrl)
    assert mock_move.called
