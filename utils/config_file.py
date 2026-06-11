"""Carga de configuración persistente en TOML (~/.config/kps/config.toml)."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, cast

from utils.const import (
    CONFIG_FILENAME,
    DEFAULT_AWAY_TIME,
    DEFAULT_POLL_INTERVAL,
)

log = logging.getLogger("kps.config")


def default_config_path() -> Path:
    """Ruta por defecto del archivo de configuración del usuario."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
        return base / "kps" / CONFIG_FILENAME
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "kps" / CONFIG_FILENAME
    return Path.home() / ".config" / "kps" / CONFIG_FILENAME


def _parse_toml(text: str) -> dict[str, Any]:
    """Parsea TOML con tomllib (3.11+) o un lector mínimo para [kps]."""
    try:
        import tomllib  # pylint: disable=import-outside-toplevel
    except ImportError:
        return _parse_kps_section_minimal(text)
    return cast(dict[str, Any], tomllib.loads(text))


def _parse_kps_section_minimal(text: str) -> dict[str, Any]:
    """Lector mínimo de la sección [kps] (Python 3.10 sin tomllib)."""
    in_section = False
    values: dict[str, Any] = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[kps]":
            in_section = True
            continue
        if line.startswith("[") and line.endswith("]"):
            in_section = False
            continue
        if not in_section or "=" not in line:
            continue

        key, _, raw_value = line.partition("=")
        key = key.strip()
        value = raw_value.strip().strip('"').strip("'")
        if value.lower() in ("true", "false"):
            values[key] = value.lower() == "true"
        else:
            try:
                values[key] = int(value)
            except ValueError:
                values[key] = value

    return {"kps": values}


def _coerce_file_values(section: dict[str, Any]) -> dict[str, Any]:
    """Normaliza claves conocidas del archivo de configuración."""
    result: dict[str, Any] = {}
    int_keys = ("away_time", "poll_interval")
    bool_keys = ("verbose", "quiet", "dry_run", "daemon", "keyboard_pulse", "tray")
    str_keys = ("log_file", "pid_file", "hotkey")

    for key in int_keys:
        if key in section:
            result[key] = int(section[key])
    for key in bool_keys:
        if key in section:
            val = section[key]
            result[key] = val if isinstance(val, bool) else str(val).lower() == "true"
    for key in str_keys:
        if key in section and section[key]:
            result[key] = str(section[key])

    return result


def load_user_config(path: Path | None = None) -> dict[str, Any]:
    """Carga valores de [kps] desde el archivo de configuración, si existe."""
    cfg_path = path or default_config_path()
    if not cfg_path.is_file():
        return {}

    try:
        text = cfg_path.read_text(encoding="utf-8")
        data = _parse_toml(text)
    except (OSError, ValueError) as error:
        log.warning("No se pudo leer %s: %s", cfg_path, error)
        return {}

    section = data.get("kps", {})
    if not isinstance(section, dict):
        log.warning("Sección [kps] inválida en %s", cfg_path)
        return {}

    log.debug("Configuración cargada desde %s", cfg_path)
    return _coerce_file_values(section)


def file_defaults(path: Path | None = None) -> dict[str, Any]:
    """Valores por defecto para argparse a partir del archivo de configuración."""
    loaded = load_user_config(path)
    return {
        "away_time": loaded.get("away_time", DEFAULT_AWAY_TIME),
        "poll_interval": loaded.get("poll_interval", DEFAULT_POLL_INTERVAL),
        "verbose": loaded.get("verbose", False),
        "quiet": loaded.get("quiet", False),
        "dry_run": loaded.get("dry_run", False),
        "daemon": loaded.get("daemon", False),
        "log_file": loaded.get("log_file"),
        "pid_file": loaded.get("pid_file"),
        "hotkey": loaded.get("hotkey"),
        "keyboard_pulse": loaded.get("keyboard_pulse", False),
        "tray": loaded.get("tray", False),
    }
