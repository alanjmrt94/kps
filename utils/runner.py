"""Bucle principal: detectar inactividad y mover el ratón."""

from __future__ import annotations

import logging
import os
import subprocess
import time
from datetime import datetime

from utils.cli import KpsConfig
from utils.const import MOVE_SCRIPT, OsType, WINDOWS_MOVE_CMD
from utils.install import project_root, venv_python

log = logging.getLogger("kps.runner")


def now_timestamp() -> str:
    """Hora actual en formato HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")


def run_move() -> None:
    """Ejecuta el script de movimiento del ratón según la plataforma."""
    if os.name == OsType.WINDOWS:
        log.debug("Ejecutando movimiento Windows: %s", WINDOWS_MOVE_CMD)
        os.system(WINDOWS_MOVE_CMD)
        return

    move_py = project_root() / MOVE_SCRIPT
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

    Import tardío de Monitor: requiere PyGObject del venv tras setup_environment().
    """
    from utils.idle import Monitor  # pylint: disable=import-outside-toplevel

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
            log.info("%s — Actividad detectada (%s s idle)", now_timestamp(), seconds)
            time.sleep(config.poll_interval)
