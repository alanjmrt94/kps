"""Tests del cargador de configuración TOML."""


# pylint: disable=missing-function-docstring,missing-class-docstring,protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from utils import config_file


def test_parse_kps_section_minimal() -> None:
    text = """
[other]
skip = 1
[kps]
away_time = 10
poll_interval = 3
verbose = true
quiet = false
dry_run = true
name = custom
hotkey = "F9"
[tail]
x = 1
"""
    data = config_file._parse_kps_section_minimal(text)
    section = data["kps"]
    assert section["away_time"] == 10
    assert section["name"] == "custom"
    assert section["hotkey"] == "F9"


def test_parse_toml_uses_tomllib_when_available() -> None:
    text = "[kps]\naway_time = 4\n"
    data = config_file._parse_toml(text)
    assert data["kps"]["away_time"] == 4


def test_parse_toml_fallback_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "tomllib":
            raise ImportError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    data = config_file._parse_toml("[kps]\naway_time = 9\n")
    assert data["kps"]["away_time"] == 9


def test_default_config_path_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    with patch.object(config_file.sys, "platform", "linux"):
        assert ".config" in str(config_file.default_config_path())


def test_default_config_path_xdg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
    with patch.object(config_file.sys, "platform", "linux"):
        assert config_file.default_config_path().as_posix() == "/custom/config/kps/config.toml"


def test_default_config_path_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APPDATA", "/appdata")
    with patch.object(config_file.sys, "platform", "win32"):
        assert config_file.default_config_path().as_posix() == "/appdata/kps/config.toml"


def test_load_user_config_from_file(sample_config: Path) -> None:
    loaded = config_file.load_user_config(sample_config)
    assert loaded["away_time"] == 15
    assert loaded["dry_run"] is True


def test_load_user_config_missing_returns_empty(tmp_path: Path) -> None:
    assert not config_file.load_user_config(tmp_path / "missing.toml")


def test_load_user_config_read_error(tmp_path: Path) -> None:
    cfg = tmp_path / "bad.toml"
    cfg.write_text("[kps]\naway_time = x\n", encoding="utf-8")
    with patch.object(config_file, "_parse_toml", side_effect=ValueError("bad")):
        assert not config_file.load_user_config(cfg)


def test_load_user_config_invalid_section(tmp_path: Path) -> None:
    cfg = tmp_path / "bad.toml"
    cfg.write_text("x", encoding="utf-8")
    with patch.object(config_file, "_parse_toml", return_value={"kps": "not-a-dict"}):
        assert not config_file.load_user_config(cfg)


def test_coerce_file_values_bool_string() -> None:
    result = config_file._coerce_file_values({"verbose": "true", "log_file": ""})
    assert result["verbose"] is True
    assert "log_file" not in result


def test_file_defaults_merge(sample_config: Path) -> None:
    defaults = config_file.file_defaults(sample_config)
    assert defaults["away_time"] == 15
    assert defaults["verbose"] is True
    assert defaults["daemon"] is False
