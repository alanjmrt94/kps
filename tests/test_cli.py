"""Tests de CLI y configuración de logging."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from utils.cli import KpsConfig, parse_args, print_banner, setup_logging


def test_parse_args_defaults(tmp_path: Path) -> None:
    missing = tmp_path / "missing.toml"
    with patch("utils.cli.default_config_path", return_value=missing):
        config = parse_args([])
    assert config.away_time == 2
    assert config.poll_interval == 5
    assert config.dry_run is False
    assert config.config_path is None


def test_parse_args_overrides(sample_config: Path) -> None:
    config = parse_args(["--config", str(sample_config), "-t", "3"])
    assert config.away_time == 3
    assert config.poll_interval == 7
    assert config.verbose is True
    assert config.dry_run is True
    assert config.config_path == sample_config


def test_parse_args_dry_run_and_daemon() -> None:
    config = parse_args(["-n", "-d", "--foreground"])
    assert config.dry_run is True
    assert config.daemon is True
    assert config.foreground is True


def test_parse_args_hotkey_stripped() -> None:
    config = parse_args(["--hotkey", "  F10  "])
    assert config.hotkey == "F10"


def test_parse_args_rejects_invalid_time() -> None:
    with pytest.raises(SystemExit):
        parse_args(["-t", "0"])


def test_parse_args_rejects_invalid_poll() -> None:
    with pytest.raises(SystemExit):
        parse_args(["-p", "0"])


def test_parse_args_rejects_verbose_and_quiet() -> None:
    with pytest.raises(SystemExit):
        parse_args(["-v", "-q"])


def test_setup_logging_quiet() -> None:
    config = KpsConfig(quiet=True)
    log = setup_logging(config)
    assert log.getEffectiveLevel() == logging.WARNING


def test_setup_logging_verbose(tmp_path: Path) -> None:
    log_file = tmp_path / "kps.log"
    config = KpsConfig(verbose=True, log_file=log_file)
    setup_logging(config)
    assert log_file.parent.exists()


def test_setup_logging_info_default() -> None:
    log = setup_logging(KpsConfig())
    assert log.getEffectiveLevel() == logging.INFO


def test_parse_args_invalid_time_message(tmp_path: Path) -> None:
    missing = tmp_path / "missing.toml"
    with (
        patch("utils.cli.default_config_path", return_value=missing),
        patch.object(argparse.ArgumentParser, "error", side_effect=SystemExit) as mock_error,
    ):
        with pytest.raises(SystemExit):
            parse_args(["-t", "0"])
        mock_error.assert_called_once()


def test_parse_args_invalid_poll_message(tmp_path: Path) -> None:
    missing = tmp_path / "missing.toml"
    with (
        patch("utils.cli.default_config_path", return_value=missing),
        patch.object(argparse.ArgumentParser, "error", side_effect=SystemExit),
    ):
        with pytest.raises(SystemExit):
            parse_args(["-p", "0"])


def test_print_banner_minimal() -> None:
    log = MagicMock()
    print_banner(log, KpsConfig())
    log.info.assert_called()


def test_print_banner_all_flags() -> None:
    log = MagicMock()
    print_banner(
        log,
        KpsConfig(
            config_path=Path("/tmp/cfg.toml"),
            dry_run=True,
            daemon=True,
            foreground=True,
        ),
    )
    assert log.info.call_count >= 3
