"""Modo daemon: ejecutar kps en segundo plano."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from utils.install import project_root

_FOREGROUND_FLAG = "--foreground"


def is_foreground_child(argv: list[str] | None = None) -> bool:
    """True si el proceso actual es el hijo en segundo plano."""
    return _FOREGROUND_FLAG in (argv if argv is not None else sys.argv)


def strip_daemon_flags(argv: list[str]) -> list[str]:
    """Elimina flags internos y de daemon de la línea de comandos."""
    skip = {"-d", "--daemon", _FOREGROUND_FLAG}
    return [arg for arg in argv if arg not in skip]


def spawn_daemon(argv: list[str] | None = None) -> None:
    """
    Re-ejecuta kps en segundo plano y termina el proceso padre.

    El hijo recibe ``--foreground`` para no volver a bifurcar.
    """
    args = list(argv if argv is not None else sys.argv)
    if is_foreground_child(args):
        return

    kps_script = project_root() / "kps.py"
    child_argv = strip_daemon_flags(args[1:])
    cmd = [str(Path(sys.executable).resolve()), str(kps_script), _FOREGROUND_FLAG, *child_argv]

    kwargs: dict = {
        "cwd": project_root(),
        "stdin": subprocess.DEVNULL,
    }

    if sys.platform == "win32":
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    else:
        kwargs["start_new_session"] = True
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL

    process = subprocess.Popen(cmd, **kwargs)  # pylint: disable=consider-using-with
    print(f"[kps] Ejecutando en segundo plano (PID {process.pid}).")
    if sys.platform != "win32":
        print("[kps] Detener: kill -TERM", process.pid, "o kill -USR1", process.pid)
    sys.exit(0)


def write_pid_file(path: Path) -> None:
    """Escribe el PID del proceso actual."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(os.getpid()), encoding="utf-8")


def remove_pid_file(path: Path | None) -> None:
    """Elimina el archivo PID al salir."""
    if path and path.is_file():
        try:
            path.unlink()
        except OSError:
            pass
