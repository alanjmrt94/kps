"""Línea de comandos y configuración de logging para kps."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass

from utils.const import DEFAULT_AWAY_TIME, DEFAULT_POLL_INTERVAL
from utils.version import App_version


@dataclass
class KpsConfig:
    """Opciones de ejecución parseadas desde la CLI."""

    away_time: int = DEFAULT_AWAY_TIME
    poll_interval: int = DEFAULT_POLL_INTERVAL
    verbose: bool = False
    quiet: bool = False


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos."""
    parser = argparse.ArgumentParser(
        description=(
            "Mantiene el cursor activo cuando estás ausente para evitar inactividad. "
            "El programa espera inactividad y mueve el ratón en segundo plano."
        ),
    )
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=DEFAULT_AWAY_TIME,
        help=f"Segundos de inactividad antes de mover el ratón (default: {DEFAULT_AWAY_TIME})",
    )
    parser.add_argument(
        "-p",
        "--poll",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Intervalo de sondeo en segundos (default: {DEFAULT_POLL_INTERVAL})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Salida detallada (DEBUG)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Solo avisos y errores",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> KpsConfig:
    """Parsea argumentos y devuelve la configuración de ejecución."""
    args = build_parser().parse_args(argv)
    if args.time < 1:
        build_parser().error("El tiempo de inactividad debe ser al menos 1 segundo.")
    if args.poll < 1:
        build_parser().error("El intervalo de sondeo debe ser al menos 1 segundo.")
    if args.verbose and args.quiet:
        build_parser().error("No se pueden usar --verbose y --quiet a la vez.")
    return KpsConfig(
        away_time=args.time,
        poll_interval=args.poll,
        verbose=args.verbose,
        quiet=args.quiet,
    )


def setup_logging(config: KpsConfig) -> logging.Logger:
    """Configura logging según -v / -q."""
    if config.quiet:
        level = logging.WARNING
    elif config.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="[%(name)s] %(message)s",
        stream=sys.stdout,
        force=True,
    )
    return logging.getLogger("kps")


def print_banner(log: logging.Logger) -> None:
    """Muestra la versión al iniciar."""
    log.info("kps v%s", App_version())
