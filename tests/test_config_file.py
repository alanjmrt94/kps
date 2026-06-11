"""Tests del cargador de configuración TOML."""

from __future__ import annotations

from pathlib import Path

from utils.config_file import (
    _parse_kps_section_minimal,
    file_defaults,
    load_user_config,
)


def test_parse_kps_section_minimal() -> None:
    text = """
# comentario
[kps]
away_time = 10
poll_interval = 3
verbose = true
quiet = false
dry_run = true
hotkey = "F9"
"""
    data = _parse_kps_section_minimal(text)
    section = data["kps"]
    assert section["away_time"] == 10
    assert section["poll_interval"] == 3
    assert section["verbose"] is True
    assert section["quiet"] is False
    assert section["dry_run"] is True
    assert section["hotkey"] == "F9"


def test_load_user_config_from_file(sample_config: Path) -> None:
    loaded = load_user_config(sample_config)
    assert loaded["away_time"] == 15
    assert loaded["dry_run"] is True
    assert loaded["hotkey"] == "F11"


def test_load_user_config_missing_returns_empty(tmp_path: Path) -> None:
    assert load_user_config(tmp_path / "missing.toml") == {}


def test_file_defaults_merge(sample_config: Path) -> None:
    defaults = file_defaults(sample_config)
    assert defaults["away_time"] == 15
    assert defaults["verbose"] is True
    assert defaults["daemon"] is False
