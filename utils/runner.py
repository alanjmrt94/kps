"""Bucle principal: detectar inactividad y mover el ratón."""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from utils.cli import KpsConfig
from utils.const import (
    MOVE_SCRIPT_LINUX,
    MOVE_SCRIPT_MACOS,
    MOVE_SCRIPT_WINDOWS,
    PULSE_BOTH,
    PULSE_INHIBIT,
    PULSE_KEYBOARD,
    PULSE_MOUSE,
    OsType,
)
from utils.inhibit import IdleInhibit
from utils.install import project_root
from utils.keyboard_pulse import pulse_shift
from utils.schedule import schedule_allows
from utils.shutdown import ShutdownController
from utils.status import PresenceStatus, StatusHub

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
    """Mueve el ratón en el mismo proceso (evita fallos de import en subprocess)."""
    _run_move_inprocess()


def _run_move_inprocess() -> None:
    """Mueve el ratón en el mismo proceso."""
    try:
        if os.name == OsType.WINDOWS:
            from utils.move_win import main as move_main  # pylint: disable=import-outside-toplevel

            rc = move_main()
        elif sys.platform == "darwin":
            from utils.move_mac import main as move_main  # pylint: disable=import-outside-toplevel

            rc = move_main()
        else:
            from utils.move import move_once  # pylint: disable=import-outside-toplevel

            time.sleep(1)
            move_once()
            rc = 0
    except (OSError, PermissionError) as error:
        log.error("%s — no se pudo mover el ratón: %s", now_timestamp(), error)
        return

    if rc != 0:
        log.error("%s — no se pudo mover el ratón.", now_timestamp())


def interruptible_sleep(seconds: float, shutdown: ShutdownController) -> bool:
    """Duerme en intervalos cortos; True si se solicitó cierre."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if shutdown.requested:
            return True
        time.sleep(min(0.5, deadline - time.monotonic()))
    return shutdown.requested


def emit_presence(config: KpsConfig) -> None:
    """Emite el pulso configurado (ratón, teclado o ambos)."""
    if config.pulse == PULSE_INHIBIT:
        return
    if config.pulse in (PULSE_MOUSE, PULSE_BOTH):
        run_move()
    if config.pulse in (PULSE_KEYBOARD, PULSE_BOTH):
        pulse_shift()


def _sync_inhibit(config: KpsConfig, inhibitor: IdleInhibit, paused: bool) -> None:
    """Activa o suelta la inhibición según horario y modo."""
    if config.pulse != PULSE_INHIBIT or config.dry_run:
        if inhibitor.running:
            inhibitor.stop()
        return
    if paused:
        inhibitor.stop()
        return
    if not inhibitor.running:
        if inhibitor.start():
            log.info("Inhibición idle/sleep del SO activa.")
        else:
            log.warning("No se pudo inhibir idle/sleep del SO.")


def run_loop(  # pylint: disable=too-many-branches
    config: KpsConfig,
    shutdown: ShutdownController | None = None,
    status: StatusHub | None = None,
) -> None:
    """
    Bucle principal: pulso de presencia tras ``away_time`` segundos de inactividad.

    Import tardío de Monitor: requiere deps del venv tras setup_environment().
    """
    from utils.idle import Monitor  # pylint: disable=import-outside-toplevel

    ctrl = shutdown or ShutdownController()
    hub = status or StatusHub()
    inhibitor = IdleInhibit()
    monitor_ok = Monitor.is_available()

    if config.pulse != PULSE_INHIBIT and not monitor_ok:
        log.error("Monitor de inactividad no disponible en esta plataforma.")
        sys.exit(1)

    log.info(
        "Presencia tras %s s de inactividad (sondeo cada %s s, pulso=%s).",
        config.away_time,
        config.poll_interval,
        config.pulse,
    )

    try:
        while not ctrl.requested:
            paused = not schedule_allows(config.schedule_start, config.schedule_end)
            _sync_inhibit(config, inhibitor, paused)
            if paused:
                hub.set(PresenceStatus.PAUSED)
                log.debug("%s — Fuera de horario del perfil; pausado.", now_timestamp())
                if interruptible_sleep(config.poll_interval, ctrl):
                    break
                continue

            if not monitor_ok:
                hub.set(PresenceStatus.AWAY)
                if interruptible_sleep(config.poll_interval, ctrl):
                    break
                continue

            seconds = Monitor.get_idle_sec()
            if seconds > config.away_time:
                hub.set(PresenceStatus.AWAY)
                if config.dry_run:
                    log.info(
                        "%s — Inactividad %s s (> %s s). Dry-run: sin pulso.",
                        now_timestamp(),
                        seconds,
                        config.away_time,
                    )
                elif config.pulse == PULSE_INHIBIT:
                    log.debug(
                        "%s — Inactividad %s s; inhibit activo (sin pulso).",
                        now_timestamp(),
                        seconds,
                    )
                else:
                    log.info(
                        "%s — Inactividad %s s (> %s s). Pulso (%s)...",
                        now_timestamp(),
                        seconds,
                        config.away_time,
                        config.pulse,
                    )
                    emit_presence(config)
                if interruptible_sleep(config.poll_interval, ctrl):
                    break
            else:
                hub.set(PresenceStatus.ACTIVE)
                log.debug("%s — Actividad detectada (%s s idle)", now_timestamp(), seconds)
                if interruptible_sleep(config.poll_interval, ctrl):
                    break
    finally:
        inhibitor.stop()

    reason = ctrl.reason or "señal de cierre"
    log.info("Detenido (%s).", reason)
