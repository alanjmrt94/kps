"""Tests de CLI y configuración de logging."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from utils.cli import KpsConfig, parse_args, print_banner, setup_logging


def test_parse_args_defaults(tmp_path: Path) -> None:
    """Comprueba parse args defaults."""
    missing = tmp_path / "missing.toml"
    with patch("utils.cli.default_config_path", return_value=missing):
        config = parse_args([])
    assert config.away_time == 2
    assert config.poll_interval == 5
    assert config.dry_run is False
    assert config.config_path is None


def test_parse_args_overrides(sample_config: Path) -> None:
    """Comprueba parse args overrides."""
    config = parse_args(["--config", str(sample_config), "-t", "3"])
    assert config.away_time == 3
    assert config.poll_interval == 7
    assert config.verbose is True
    assert config.dry_run is True
    assert config.config_path == sample_config


def test_parse_args_dry_run_and_daemon() -> None:
    """Comprueba parse args dry run and daemon."""
    config = parse_args(["-n", "-d", "--foreground"])
    assert config.dry_run is True
    assert config.daemon is True
    assert config.foreground is True


def test_parse_args_hotkey_stripped() -> None:
    """Comprueba parse args hotkey stripped."""
    config = parse_args(["--hotkey", "  F10  "])
    assert config.hotkey == "F10"


def test_parse_args_rejects_invalid_time() -> None:
    """Comprueba parse args rejects invalid time."""
    with pytest.raises(SystemExit):
        parse_args(["-t", "0"])


def test_parse_args_rejects_invalid_poll() -> None:
    """Comprueba parse args rejects invalid poll."""
    with pytest.raises(SystemExit):
        parse_args(["-p", "0"])


def test_parse_args_rejects_verbose_and_quiet() -> None:
    """Comprueba parse args rejects verbose and quiet."""
    with pytest.raises(SystemExit):
        parse_args(["-v", "-q"])


def test_setup_logging_quiet() -> None:
    """Comprueba setup logging quiet."""
    config = KpsConfig(quiet=True)
    log = setup_logging(config)
    assert log.getEffectiveLevel() == logging.WARNING


def test_setup_logging_verbose(tmp_path: Path) -> None:
    """Comprueba setup logging verbose."""
    log_file = tmp_path / "kps.log"
    config = KpsConfig(verbose=True, log_file=log_file)
    setup_logging(config)
    assert log_file.parent.exists()


def test_setup_logging_info_default() -> None:
    """Comprueba setup logging info default."""
    log = setup_logging(KpsConfig())
    assert log.getEffectiveLevel() == logging.INFO


def test_parse_args_invalid_time_message(tmp_path: Path) -> None:
    """Comprueba parse args invalid time message."""
    missing = tmp_path / "missing.toml"
    with (
        patch("utils.cli.default_config_path", return_value=missing),
        patch.object(argparse.ArgumentParser, "error", side_effect=SystemExit) as mock_error,
    ):
        with pytest.raises(SystemExit):
            parse_args(["-t", "0"])
        mock_error.assert_called_once()


def test_parse_args_invalid_poll_message(tmp_path: Path) -> None:
    """Comprueba parse args invalid poll message."""
    missing = tmp_path / "missing.toml"
    with (
        patch("utils.cli.default_config_path", return_value=missing),
        patch.object(argparse.ArgumentParser, "error", side_effect=SystemExit),
    ):
        with pytest.raises(SystemExit):
            parse_args(["-p", "0"])


def test_print_banner_minimal() -> None:
    """Comprueba print banner minimal."""
    log = MagicMock()
    print_banner(log, KpsConfig())
    log.info.assert_called()


def test_print_banner_all_flags() -> None:
    """Comprueba print banner all flags."""
    log = MagicMock()
    print_banner(
        log,
        KpsConfig(
            config_path=Path("/tmp/cfg.toml"),
            dry_run=True,
            daemon=True,
            foreground=True,
            keyboard_pulse=True,
            tray=True,
        ),
    )
    assert log.info.call_count >= 5
