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
    PULSE_BOTH,
    PULSE_INHIBIT,
    PULSE_KEYBOARD,
    PULSE_MODES,
    PULSE_MOUSE,
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
    """Parsea TOML con tomllib (3.11+) o un lector mínimo para [kps] y perfiles."""
    try:
        import tomllib  # pylint: disable=import-outside-toplevel
    except ImportError:
        return _parse_kps_section_minimal(text)
    return cast(dict[str, Any], tomllib.loads(text))


def _parse_scalar(raw_value: str) -> Any:
    """Convierte un valor TOML simple."""
    value = raw_value.strip().strip('"').strip("'")
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        return value


def _parse_kps_section_minimal(text: str) -> dict[str, Any]:
    """Lector mínimo de [kps] y [profiles.nombre] (Python 3.10 sin tomllib)."""
    in_kps = False
    profile_name: str | None = None
    values: dict[str, Any] = {}
    profiles: dict[str, dict[str, Any]] = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[kps]":
            in_kps = True
            profile_name = None
            continue
        if line.startswith("[profiles.") and line.endswith("]"):
            in_kps = False
            profile_name = line[len("[profiles.") : -1].strip()
            profiles.setdefault(profile_name, {})
            continue
        if line.startswith("[") and line.endswith("]"):
            in_kps = False
            profile_name = None
            continue
        if "=" not in line:
            continue

        key, _, raw_value = line.partition("=")
        key = key.strip()
        parsed = _parse_scalar(raw_value)
        if in_kps:
            values[key] = parsed
        elif profile_name:
            profiles[profile_name][key] = parsed

    result: dict[str, Any] = {"kps": values}
    if profiles:
        result["profiles"] = profiles
    return result


def resolve_pulse(section: dict[str, Any]) -> str:
    """Determina mouse / keyboard / both a partir del TOML o flags."""
    if section.get("inhibit_only"):
        return PULSE_INHIBIT
    if section.get("keyboard_only"):
        return PULSE_KEYBOARD
    pulse = section.get("pulse")
    if isinstance(pulse, str) and pulse in PULSE_MODES:
        return pulse
    if section.get("keyboard_pulse"):
        return PULSE_BOTH
    return PULSE_MOUSE


def _coerce_file_values(section: dict[str, Any]) -> dict[str, Any]:
    """Normaliza claves conocidas del archivo de configuración."""
    result: dict[str, Any] = {}
    int_keys = ("away_time", "poll_interval")
    bool_keys = (
        "verbose",
        "quiet",
        "dry_run",
        "daemon",
        "keyboard_pulse",
        "keyboard_only",
        "inhibit_only",
        "tray",
    )
    str_keys = ("log_file", "pid_file", "hotkey", "profile", "pulse")

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

    start = section.get("schedule_start") or section.get("start")
    end = section.get("schedule_end") or section.get("end")
    if start:
        result["schedule_start"] = str(start)
    if end:
        result["schedule_end"] = str(end)

    result["pulse"] = resolve_pulse({**section, **result})
    result["keyboard_pulse"] = result["pulse"] == PULSE_BOTH
    result["keyboard_only"] = result["pulse"] == PULSE_KEYBOARD
    result["inhibit_only"] = result["pulse"] == PULSE_INHIBIT
    return result


def _coerce_profiles(raw: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for name, section in raw.items():
        if isinstance(section, dict):
            out[str(name)] = _coerce_file_values(section)
    return out


def load_config_document(path: Path | None = None) -> dict[str, Any]:
    """Carga [kps] y perfiles; vacío si no hay archivo."""
    cfg_path = path or default_config_path()
    if not cfg_path.is_file():
        return {"kps": {}, "profiles": {}}

    try:
        text = cfg_path.read_text(encoding="utf-8")
        data = _parse_toml(text)
    except (OSError, ValueError) as error:
        log.warning("No se pudo leer %s: %s", cfg_path, error)
        return {"kps": {}, "profiles": {}}

    section = data.get("kps", {})
    if not isinstance(section, dict):
        log.warning("Sección [kps] inválida en %s", cfg_path)
        return {"kps": {}, "profiles": {}}

    log.debug("Configuración cargada desde %s", cfg_path)
    return {
        "kps": _coerce_file_values(section),
        "profiles": _coerce_profiles(data.get("profiles", {})),
    }


def apply_profile(
    base: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    name: str | None,
) -> dict[str, Any]:
    """Superpone un perfil sobre [kps]."""
    merged = dict(base)
    if not name:
        return merged
    overlay = profiles.get(name)
    if overlay is None:
        log.warning("Perfil %r no encontrado en la configuración.", name)
        merged["profile"] = name
        return merged
    merged.update(overlay)
    merged["profile"] = name
    merged["pulse"] = resolve_pulse(merged)
    merged["keyboard_pulse"] = merged["pulse"] == PULSE_BOTH
    merged["keyboard_only"] = merged["pulse"] == PULSE_KEYBOARD
    merged["inhibit_only"] = merged["pulse"] == PULSE_INHIBIT
    return merged


def load_user_config(path: Path | None = None, profile: str | None = None) -> dict[str, Any]:
    """Carga valores de [kps] (y perfil) desde el archivo de configuración."""
    document = load_config_document(path)
    name = profile or document["kps"].get("profile")
    return apply_profile(document["kps"], document["profiles"], name)


def file_defaults(path: Path | None = None, profile: str | None = None) -> dict[str, Any]:
    """Valores por defecto para argparse a partir del archivo de configuración."""
    loaded = load_user_config(path, profile=profile)
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
        "keyboard_only": loaded.get("keyboard_only", False),
        "inhibit_only": loaded.get("inhibit_only", False),
        "pulse": loaded.get("pulse", PULSE_MOUSE),
        "tray": loaded.get("tray", False),
        "profile": loaded.get("profile"),
        "schedule_start": loaded.get("schedule_start"),
        "schedule_end": loaded.get("schedule_end"),
    }
