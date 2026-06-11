"""Tests de CLI y configuración de logging."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from utils.cli import KpsConfig, parse_args, print_banner, setup_logging


def test_parse_args_defaults() -> None:
    config = parse_args([])
    assert config.away_time == 2
    assert config.poll_interval == 5
    assert config.dry_run is False


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


def test_parse_args_rejects_invalid_time() -> None:
    with pytest.raises(SystemExit):
        parse_args(["-t", "0"])


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


def test_print_banner_options() -> None:
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
