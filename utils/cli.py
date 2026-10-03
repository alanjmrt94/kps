"""Línea de comandos y configuración de logging para kps."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from utils.config_file import default_config_path, file_defaults
from utils.const import (
    DEFAULT_AWAY_TIME,
    DEFAULT_POLL_INTERVAL,
    PULSE_BOTH,
    PULSE_INHIBIT,
    PULSE_KEYBOARD,
    PULSE_MODES,
    PULSE_MOUSE,
)
from utils.version import App_version


@dataclass
class KpsConfig:  # pylint: disable=too-many-instance-attributes
    """Opciones de ejecución (archivo de config + CLI)."""

    away_time: int = DEFAULT_AWAY_TIME
    poll_interval: int = DEFAULT_POLL_INTERVAL
    verbose: bool = False
    quiet: bool = False
    dry_run: bool = False
    daemon: bool = False
    foreground: bool = False
    log_file: Path | None = None
    pid_file: Path | None = None
    hotkey: str | None = None
    keyboard_pulse: bool = False
    keyboard_only: bool = False
    pulse: str = PULSE_MOUSE
    tray: bool = False
    config_path: Path | None = None
    command: str = "run"
    autostart_action: str = "status"
    profile: str | None = None
    schedule_start: str | None = None
    schedule_end: str | None = None


def build_parser(defaults: dict | None = None) -> argparse.ArgumentParser:
    """Construye el parser de argumentos."""
    cfg = defaults or {}
    parser = argparse.ArgumentParser(
        description=(
            "Mantiene el cursor activo cuando estás ausente para evitar inactividad. "
            "El programa espera inactividad y mueve el ratón en segundo plano."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "Subcomandos: kps doctor · kps autostart enable|disable|status. "
            "Pulso: --pulse mouse|keyboard|both|inhibit "
            "(o --keyboard / --keyboard-only / --inhibit-only)."
        ),
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=("run", "doctor", "autostart"),
        help="Acción: ejecutar, diagnosticar o configurar arranque",
    )
    parser.add_argument(
        "autostart_action",
        nargs="?",
        default="status",
        choices=("enable", "disable", "status"),
        help="Acción de autostart (solo con 'autostart')",
    )
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=cfg.get("away_time", DEFAULT_AWAY_TIME),
        help="Segundos de inactividad antes de mover el ratón",
    )
    parser.add_argument(
        "-p",
        "--poll",
        type=int,
        default=cfg.get("poll_interval", DEFAULT_POLL_INTERVAL),
        help="Intervalo de sondeo en segundos",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=cfg.get("verbose", False),
        help="Salida detallada (DEBUG)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=cfg.get("quiet", False),
        help="Solo mensajes WARNING o superiores",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        default=cfg.get("dry_run", False),
        help="Detectar inactividad sin mover el ratón",
    )
    parser.add_argument(
        "-d",
        "--daemon",
        action="store_true",
        default=cfg.get("daemon", False),
        help="Ejecutar en segundo plano",
    )
    parser.add_argument(
        "--foreground",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="PATH",
        help=f"Archivo de configuración (default: {default_config_path()})",
    )
    parser.add_argument(
        "--profile",
        default=cfg.get("profile"),
        metavar="NAME",
        help="Perfil TOML (p. ej. work, night)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=cfg.get("log_file"),
        metavar="PATH",
        help="Escribir logs también en un archivo",
    )
    parser.add_argument(
        "--pid-file",
        type=Path,
        default=cfg.get("pid_file"),
        metavar="PATH",
        help="Ruta del archivo PID (útil con --daemon)",
    )
    parser.add_argument(
        "--hotkey",
        default=cfg.get("hotkey"),
        metavar="KEY",
        help="Tecla de cierre (F1–F12; Linux/macOS requiere pynput)",
    )
    parser.add_argument(
        "--pulse",
        choices=PULSE_MODES,
        default=cfg.get("pulse", PULSE_MOUSE),
        help="Ratón, teclado, ambos, o solo inhibir sleep/idle del SO",
    )
    parser.add_argument(
        "--keyboard",
        action="store_true",
        default=False,
        help="Pulso de Shift además del ratón (equivale a --pulse both)",
    )
    parser.add_argument(
        "--keyboard-only",
        action="store_true",
        default=False,
        help="Solo pulso de teclado, sin mover el cursor",
    )
    parser.add_argument(
        "--inhibit-only",
        action="store_true",
        default=False,
        help="Solo inhibir idle/sleep del SO (sin ratón ni teclado)",
    )
    parser.add_argument(
        "--tray",
        action="store_true",
        default=cfg.get("tray", False),
        help="Icono en bandeja del sistema (requiere pip install \"kps[gui]\")",
    )
    return parser


def _pulse_from_args(args: argparse.Namespace, raw_argv: list[str]) -> str:
    """Prioridad: aliases CLI, luego --pulse / config."""
    if "--inhibit-only" in raw_argv:
        return PULSE_INHIBIT
    if "--keyboard-only" in raw_argv:
        return PULSE_KEYBOARD
    if "--keyboard" in raw_argv:
        return PULSE_BOTH
    return str(args.pulse)


def parse_args(argv: list[str] | None = None) -> KpsConfig:
    """Parsea argumentos, fusiona config TOML y devuelve KpsConfig."""
    raw_argv = list(argv if argv is not None else sys.argv[1:])

    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config", type=Path, default=None)
    pre.add_argument("--profile", default=None)
    pre_args, _ = pre.parse_known_args(raw_argv)
    config_path = pre_args.config or default_config_path()
    defaults = file_defaults(config_path, profile=pre_args.profile)

    args = build_parser(defaults).parse_args(raw_argv)

    if args.command == "run":
        if args.time < 1:
            build_parser(defaults).error("El tiempo de inactividad debe ser al menos 1 segundo.")
        if args.poll < 1:
            build_parser(defaults).error("El intervalo de sondeo debe ser al menos 1 segundo.")
        if args.verbose and args.quiet:
            build_parser(defaults).error("No se pueden usar --verbose y --quiet a la vez.")
        pulse_aliases = [
            flag
            for flag in ("--keyboard", "--keyboard-only", "--inhibit-only")
            if flag in raw_argv
        ]
        if len(pulse_aliases) > 1:
            build_parser(defaults).error(
                "Usá solo uno de --keyboard, --keyboard-only o --inhibit-only."
            )

    hotkey = args.hotkey.strip() if args.hotkey else None
    pulse = _pulse_from_args(args, raw_argv)
    profile = args.profile or defaults.get("profile")

    return KpsConfig(
        away_time=args.time,
        poll_interval=args.poll,
        verbose=args.verbose,
        quiet=args.quiet,
        dry_run=args.dry_run,
        daemon=args.daemon,
        foreground=args.foreground,
        log_file=args.log_file,
        pid_file=args.pid_file,
        hotkey=hotkey,
        keyboard_pulse=pulse == PULSE_BOTH,
        keyboard_only=pulse == PULSE_KEYBOARD,
        pulse=pulse,
        tray=args.tray,
        config_path=config_path if config_path.is_file() else None,
        command=args.command,
        autostart_action=args.autostart_action,
        profile=profile,
        schedule_start=defaults.get("schedule_start"),
        schedule_end=defaults.get("schedule_end"),
    )


def setup_logging(config: KpsConfig) -> logging.Logger:
    """Configura logging según -v / -q y --log-file."""
    if config.quiet:
        level = logging.WARNING
    elif config.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    formatter = logging.Formatter("[%(name)s] %(message)s")
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if config.log_file:
        config.log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(config.log_file, encoding="utf-8"))

    logging.basicConfig(level=level, handlers=handlers, force=True)
    for handler in handlers:
        handler.setFormatter(formatter)

    return logging.getLogger("kps")


def print_banner(log: logging.Logger, config: KpsConfig) -> None:
    """Muestra la versión y opciones relevantes al iniciar."""
    log.info("kps v%s", App_version())
    if config.config_path:
        log.info("Config: %s", config.config_path)
    if config.profile:
        log.info("Perfil: %s", config.profile)
    if config.schedule_start or config.schedule_end:
        log.info("Horario: %s–%s", config.schedule_start or "*", config.schedule_end or "*")
    if config.dry_run:
        log.info("Modo dry-run: no se moverá el ratón.")
    if config.daemon and config.foreground:
        log.info("Proceso en segundo plano.")
    if config.pulse == PULSE_KEYBOARD:
        log.info("Pulso: solo teclado (sin mover el cursor).")
    elif config.pulse == PULSE_BOTH:
        log.info("Pulso: ratón y teclado en paralelo.")
    elif config.pulse == PULSE_INHIBIT:
        log.info("Modo inhibit: solo idle/sleep del SO (sin ratón ni teclado).")
    if config.tray:
        log.info("Modo bandeja del sistema.")
