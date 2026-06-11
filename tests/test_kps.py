"""Tests del entrypoint kps.py."""

from __future__ import annotations

import runpy
from pathlib import Path
from unittest.mock import MagicMock, patch

import kps
import pytest


@patch("kps.run_loop")
@patch("kps.setup_environment")
@patch("kps.setup_logging")
@patch("kps.parse_args")
def test_main_success(mock_parse, mock_log_setup, mock_setup, mock_loop) -> None:
    config = MagicMock(daemon=False, foreground=False, pid_file=None, hotkey=None, tray=False)
    mock_parse.return_value = config
    mock_log_setup.return_value = MagicMock()
    with pytest.raises(SystemExit) as exc:
        kps.main()
    assert exc.value.code == 0


@patch("kps.spawn_daemon", side_effect=SystemExit(0))
@patch("kps.parse_args")
def test_main_daemon_spawns(mock_parse, mock_spawn) -> None:
    config = MagicMock(daemon=True, foreground=False, log_file=None, pid_file=None, hotkey=None, tray=False)
    mock_parse.return_value = config
    with pytest.raises(SystemExit):
        kps.main()
    mock_spawn.assert_called_once()


@patch("kps.write_pid_file")
@patch("kps.run_loop", side_effect=RuntimeError("fallo entorno"))
@patch("kps.setup_environment")
@patch("kps.setup_logging")
@patch("kps.parse_args")
def test_main_runtime_error(mock_parse, mock_log_setup, _setup, _loop, _pid) -> None:
    config = MagicMock(daemon=False, foreground=False, pid_file=MagicMock(), hotkey=None, tray=False)
    mock_parse.return_value = config
    mock_log_setup.return_value = MagicMock()
    with pytest.raises(SystemExit) as exc:
        kps.main()
    assert exc.value.code == 1


@patch("kps.run_loop", side_effect=KeyboardInterrupt)
@patch("kps.setup_environment")
@patch("kps.setup_logging")
@patch("kps.parse_args")
def test_main_keyboard_interrupt(mock_parse, mock_log_setup, _setup, _loop) -> None:
    config = MagicMock(daemon=False, foreground=False, pid_file=None, hotkey=None, tray=False)
    mock_parse.return_value = config
    mock_log_setup.return_value = MagicMock()
    with pytest.raises(SystemExit) as exc:
        kps.main()
    assert exc.value.code == 0


def test_kps_main_module() -> None:
    kps_path = Path(kps.__file__)
    config = MagicMock(daemon=False, foreground=False, pid_file=None, hotkey=None, log_file=None, tray=False)
    with (
        patch("utils.cli.parse_args", return_value=config),
        patch("utils.cli.setup_logging", return_value=MagicMock()),
        patch("utils.install.setup_environment"),
        patch("utils.runner.run_loop"),
        patch("utils.shutdown.ShutdownController"),
    ):
        with pytest.raises(SystemExit) as exc:
            runpy.run_path(str(kps_path), run_name="__main__")
        assert exc.value.code == 0
