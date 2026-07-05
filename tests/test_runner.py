"""Tests del bucle principal (unidad, sin bucle infinito)."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import utils.runner as runner
from utils.cli import KpsConfig
from utils.const import MOVE_SCRIPT_LINUX, MOVE_SCRIPT_MACOS, MOVE_SCRIPT_WINDOWS, OsType
from utils.runner import interruptible_sleep, now_timestamp, run_loop, run_move
from utils.shutdown import ShutdownController

_FAKE_ROOT = Path("fake", "project", "root")


def test_now_timestamp_format() -> None:
    """Comprueba now timestamp format."""
    assert len(now_timestamp()) == 8


def test_move_script_path_linux() -> None:
    """Comprueba move script path linux."""
    with (
        patch.object(runner, "project_root", return_value=_FAKE_ROOT),
        patch.object(sys, "platform", "linux"),
        patch.object(runner.os, "name", OsType.UNIX),
    ):
        path = runner.move_script_path()
        assert path.name == "move.py"
        assert path == _FAKE_ROOT / MOVE_SCRIPT_LINUX


def test_move_script_path_windows() -> None:
    """Comprueba move script path windows."""
    with (
        patch.object(runner, "project_root", return_value=_FAKE_ROOT),
        patch.object(runner.os, "name", OsType.WINDOWS),
    ):
        path = runner.move_script_path()
        assert path.name == "move_win.py"
        assert path == _FAKE_ROOT / MOVE_SCRIPT_WINDOWS


def test_move_script_path_macos() -> None:
    """Comprueba move script path macos."""
    with (
        patch.object(runner, "project_root", return_value=_FAKE_ROOT),
        patch.object(sys, "platform", "darwin"),
        patch.object(runner.os, "name", OsType.UNIX),
    ):
        path = runner.move_script_path()
        assert path.name == "move_mac.py"
        assert path == _FAKE_ROOT / MOVE_SCRIPT_MACOS


def test_run_move_success() -> None:
    """Comprueba run move success."""
    with (
        patch("utils.runner.time.sleep"),
        patch("utils.move.move_once") as mock_move,
        patch.object(sys, "platform", "linux"),
        patch.object(runner.os, "name", OsType.UNIX),
    ):
        run_move()
    mock_move.assert_called_once()


def test_run_move_failure() -> None:
    """Comprueba run move failure."""
    with (
        patch("utils.move.move_once", side_effect=OSError("uinput fail")),
        patch.object(sys, "platform", "linux"),
        patch.object(runner.os, "name", OsType.UNIX),
    ):
        run_move()


def test_run_move_failure_no_stderr() -> None:
    """Comprueba run move failure no stderr."""
    with (
        patch("utils.move_win.main", return_value=1),
        patch.object(runner.os, "name", OsType.WINDOWS),
    ):
        run_move()


def test_run_move_bundled_linux() -> None:
    """Comprueba run move bundled linux."""
    with (
        patch("utils.runner.time.sleep"),
        patch("utils.move.move_once") as mock_move,
        patch.object(sys, "platform", "linux"),
        patch.object(runner.os, "name", OsType.UNIX),
    ):
        run_move()
    mock_move.assert_called_once()


def test_interruptible_sleep_completes() -> None:
    """Comprueba interruptible sleep completes."""
    ctrl = ShutdownController()
    assert interruptible_sleep(0.1, ctrl) is False


def test_interruptible_sleep_shutdown() -> None:
    """Comprueba interruptible sleep shutdown."""
    ctrl = ShutdownController()
    ctrl.request("test")
    assert interruptible_sleep(2.0, ctrl) is True


@patch("utils.idle.Monitor")
@patch("utils.runner.interruptible_sleep", return_value=True)
def test_run_loop_exits_on_shutdown(_sleep: MagicMock, mock_monitor: MagicMock) -> None:
    """Comprueba run loop exits on shutdown."""
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
    """Comprueba run loop moves mouse."""
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
    """Comprueba run loop dry run no move."""
    mock_monitor.is_available.return_value = True
    mock_monitor.get_idle_sec.return_value = 99
    ctrl = ShutdownController()
    run_loop(KpsConfig(away_time=2, dry_run=True), ctrl)
    mock_move.assert_not_called()


@patch("utils.idle.Monitor")
def test_run_loop_monitor_unavailable(mock_monitor: MagicMock) -> None:
    """Comprueba run loop monitor unavailable."""
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
    """Comprueba run loop activity branch."""
    mock_monitor.is_available.return_value = True
    mock_monitor.get_idle_sec.return_value = 0
    ctrl = ShutdownController()
    run_loop(KpsConfig(poll_interval=1), ctrl)


@patch("utils.idle.Monitor")
def test_run_loop_shutdown_before_loop(mock_monitor: MagicMock) -> None:
    """Comprueba run loop shutdown before loop."""
    mock_monitor.is_available.return_value = True
    ctrl = ShutdownController()
    ctrl.request("ya detenido")
    run_loop(KpsConfig(), ctrl)


@patch("utils.idle.Monitor")
@patch("utils.runner.pulse_shift")
@patch("utils.runner.run_move")
@patch("utils.runner.interruptible_sleep", return_value=True)
def test_run_loop_keyboard_pulse(
    _sleep: MagicMock,
    mock_move: MagicMock,
    mock_pulse: MagicMock,
    mock_monitor: MagicMock,
) -> None:
    """Comprueba run loop keyboard pulse."""
    mock_monitor.is_available.return_value = True
    mock_monitor.get_idle_sec.return_value = 99
    ctrl = ShutdownController()
    run_loop(KpsConfig(away_time=2, keyboard_pulse=True), ctrl)
    mock_move.assert_called_once()
    mock_pulse.assert_called_once()


@patch("utils.idle.Monitor")
@patch("utils.runner.run_move")
@patch("utils.runner.interruptible_sleep", side_effect=[False, False, False, True])
def test_run_loop_timelapse_multiple_idle_cycles(
    _sleep: MagicMock,
    mock_move: MagicMock,
    mock_monitor: MagicMock,
) -> None:
    """Varios ciclos idle/activo sin salir del bucle (check timelapse -t)."""
    mock_monitor.is_available.return_value = True
    mock_monitor.get_idle_sec.side_effect = [0, 99, 0, 120]
    ctrl = ShutdownController()
    run_loop(KpsConfig(away_time=2, poll_interval=1), ctrl)
    assert mock_move.call_count == 2


@patch("utils.idle.Monitor")
@patch("utils.runner.run_move")
@patch("utils.runner.interruptible_sleep", side_effect=[False, True])
def test_run_loop_move_then_shutdown(
    _sleep: MagicMock,
    mock_move: MagicMock,
    mock_monitor: MagicMock,
) -> None:
    """Comprueba run loop move then shutdown."""
    mock_monitor.is_available.return_value = True
    mock_monitor.get_idle_sec.return_value = 99
    ctrl = ShutdownController()
    run_loop(KpsConfig(away_time=2, poll_interval=1), ctrl)
    assert mock_move.called
