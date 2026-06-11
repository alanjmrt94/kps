"""Tests del bucle principal (unidad, sin bucle infinito)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from utils.cli import KpsConfig
from utils.runner import interruptible_sleep, run_loop
from utils.shutdown import ShutdownController


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
