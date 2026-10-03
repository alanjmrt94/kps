"""Tests del cargador de configuración TOML."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from utils import config_file


def test_parse_kps_section_minimal() -> None:
    """Comprueba parse kps section minimal."""
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
    """Comprueba parse toml uses tomllib when available."""
    text = "[kps]\naway_time = 4\n"
    data = config_file._parse_toml(text)
    assert data["kps"]["away_time"] == 4


def test_parse_toml_fallback_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Comprueba parse toml fallback minimal."""
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
    """Comprueba default config path linux."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    with patch.object(config_file.sys, "platform", "linux"):
        assert ".config" in str(config_file.default_config_path())


def test_default_config_path_xdg(monkeypatch: pytest.MonkeyPatch) -> None:
    """Comprueba default config path xdg."""
    monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
    with patch.object(config_file.sys, "platform", "linux"):
        assert config_file.default_config_path().as_posix() == "/custom/config/kps/config.toml"


def test_default_config_path_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Comprueba default config path windows."""
    monkeypatch.setenv("APPDATA", "/appdata")
    with patch.object(config_file.sys, "platform", "win32"):
        assert config_file.default_config_path().as_posix() == "/appdata/kps/config.toml"


def test_load_user_config_from_file(sample_config: Path) -> None:
    """Comprueba load user config from file."""
    loaded = config_file.load_user_config(sample_config)
    assert loaded["away_time"] == 15
    assert loaded["dry_run"] is True


def test_load_user_config_missing_returns_empty(tmp_path: Path) -> None:
    """Comprueba load user config missing returns empty."""
    assert not config_file.load_user_config(tmp_path / "missing.toml")


def test_load_user_config_read_error(tmp_path: Path) -> None:
    """Comprueba load user config read error."""
    cfg = tmp_path / "bad.toml"
    cfg.write_text("[kps]\naway_time = x\n", encoding="utf-8")
    with patch.object(config_file, "_parse_toml", side_effect=ValueError("bad")):
        assert not config_file.load_user_config(cfg)


def test_load_user_config_invalid_section(tmp_path: Path) -> None:
    """Comprueba load user config invalid section."""
    cfg = tmp_path / "bad.toml"
    cfg.write_text("x", encoding="utf-8")
    with patch.object(config_file, "_parse_toml", return_value={"kps": "not-a-dict"}):
        assert not config_file.load_user_config(cfg)


def test_coerce_file_values_bool_string() -> None:
    """Comprueba coerce file values bool string."""
    result = config_file._coerce_file_values({"verbose": "true", "log_file": ""})
    assert result["verbose"] is True
    assert "log_file" not in result


def test_file_defaults_merge(sample_config: Path) -> None:
    """Comprueba file defaults merge."""
    defaults = config_file.file_defaults(sample_config)
    assert defaults["away_time"] == 15
    assert defaults["verbose"] is True
    assert defaults["daemon"] is False


def test_parse_profiles_minimal() -> None:
    """Comprueba parse profiles minimal."""
    text = """
[kps]
profile = "work"
[profiles.work]
away_time = 8
pulse = "both"
start = "09:00"
end = "18:00"
"""
    data = config_file._parse_kps_section_minimal(text)
    assert data["kps"]["profile"] == "work"
    assert data["profiles"]["work"]["away_time"] == 8
    assert data["profiles"]["work"]["start"] == "09:00"


def test_apply_profile_overrides(tmp_path: Path) -> None:
    """Comprueba apply profile overrides."""
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
[kps]
away_time = 15
profile = "night"
[profiles.night]
away_time = 4
pulse = "keyboard"
start = "22:00"
end = "07:00"
""".strip(),
        encoding="utf-8",
    )
    loaded = config_file.load_user_config(cfg)
    assert loaded["away_time"] == 4
    assert loaded["pulse"] == "keyboard"
    assert loaded["schedule_start"] == "22:00"
    assert loaded["profile"] == "night"


def test_apply_profile_missing_name() -> None:
    """Comprueba apply profile missing name."""
    merged = config_file.apply_profile({"away_time": 1}, {}, "nope")
    assert merged["profile"] == "nope"
    assert merged["away_time"] == 1


def test_coerce_profiles_invalid() -> None:
    """Comprueba coerce profiles invalid."""
    assert not config_file._coerce_profiles("x")
    assert not config_file._coerce_profiles({"a": 1})


def test_load_config_invalid_kps_section(tmp_path: Path) -> None:
    """Comprueba load config invalid kps section."""
    cfg = tmp_path / "bad.toml"
    cfg.write_text("x = 1\n", encoding="utf-8")
    with patch.object(config_file, "_parse_toml", return_value={"kps": "no"}):
        doc = config_file.load_config_document(cfg)
    assert not doc["kps"]


def test_cli_profile_from_file(tmp_path: Path) -> None:
    """Comprueba cli profile from file."""
    from utils.cli import parse_args

    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
[kps]
away_time = 2
[profiles.work]
away_time = 9
pulse = "both"
""".strip(),
        encoding="utf-8",
    )
    config = parse_args(["--config", str(cfg), "--profile", "work"])
    assert config.away_time == 9
    assert config.pulse == "both"
    assert config.profile == "work"


def test_resolve_pulse_inhibit_only() -> None:
    """Comprueba resolve pulse inhibit only."""
    assert config_file.resolve_pulse({"inhibit_only": True}) == "inhibit"
