"""Fixtures compartidas para tests de kps."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def sample_config(tmp_path: Path) -> Path:
    """Archivo TOML mínimo de prueba."""
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
[kps]
away_time = 15
poll_interval = 7
verbose = true
dry_run = true
log_file = "/tmp/kps-test.log"
hotkey = "F11"
""".strip(),
        encoding="utf-8",
    )
    return cfg
