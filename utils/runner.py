"""Bucle principal: detectar inactividad y mover el ratón."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from utils.cli import KpsConfig
from utils.const import (
    MOVE_SCRIPT_LINUX,
    MOVE_SCRIPT_MACOS,
    MOVE_SCRIPT_WINDOWS,
    OsType,
)
from utils.install import project_root, venv_python

log = logging.getLogger("kps.runner")


def now_timestamp() -> str:
    """Hora actual en formato HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")


def move_script_path() -> Path:
    """Ruta del script de movimiento según la plataforma."""
    if os.name == OsType.WINDOWS:
        return project_root() / MOVE_SCRIPT_WINDOWS
    if sys.platform == "darwin":
        return project_root() / MOVE_SCRIPT_MACOS
    return project_root() / MOVE_SCRIPT_LINUX


def run_move() -> None:
    """Ejecuta el script de movimiento del ratón según la plataforma."""
    move_py = move_script_path()
    cmd = [str(venv_python()), str(move_py)]
    log.debug("Ejecutando: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        cwd=project_root(),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error("%s — no se pudo mover el ratón.", now_timestamp())
        if result.stderr:
            log.error(result.stderr.strip())


def run_loop(config: KpsConfig) -> None:
    """
    Bucle principal: mueve el cursor tras ``away_time`` segundos de inactividad.

    Import tardío de Monitor: requiere deps del venv tras setup_environment().
    """
    from utils.idle import Monitor  # pylint: disable=import-outside-toplevel

    if not Monitor.is_available():
        log.error("Monitor de inactividad no disponible en esta plataforma.")
        sys.exit(1)

    log.info(
        "Mover el ratón tras %s s de inactividad (sondeo cada %s s).",
        config.away_time,
        config.poll_interval,
    )

    while True:
        seconds = Monitor.get_idle_sec()
        if seconds > config.away_time:
            log.info(
                "%s — Inactividad %s s (> %s s). Moviendo ratón...",
                now_timestamp(),
                seconds,
                config.away_time,
            )
            run_move()
        else:
            log.debug("%s — Actividad detectada (%s s idle)", now_timestamp(), seconds)
            time.sleep(config.poll_interval)
