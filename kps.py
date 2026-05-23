"""kps — evita inactividad moviendo el cursor cuando el usuario está ausente."""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime

from utils.const import OsType
from utils.install import project_root, setup_environment, venv_python
from utils.version import App_version

AWAY_TIME = 2
POLL_INTERVAL = 5
WINDOWS_CMD = "cmd /c utils/move.bat"


def commandline() -> None:
    """
    Parse the command line arguments

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description="This program keeps moving the cursor if you are away to avoid inactivity."
        "The program works in the background and waits only for inactivity to move the mouse."
    )

    parser.add_argument(
        "-t",
        "--time",
        type=int,
        help="time in seconds of how long to wait after a user is considered inactive.(Default: 2)",
    )

    args = parser.parse_args()

    if args.time:
        global AWAY_TIME  # pylint: disable=global-statement
        AWAY_TIME = int(args.time)

    print("Set move mouse time every", str(AWAY_TIME), "seconds of inactivity.\n")


def get_now_timestamp() -> str:
    """
    Get the current timestamp in the format of HH:MM:SS

    Returns:
        str: The current timestamp in the format of HH:MM:SS
    """
    now = datetime.now()
    return now.strftime("%H:%M:%S")


def run_move() -> None:
    """Ejecuta el script de movimiento del ratón según la plataforma."""
    if os.name == OsType.WINDOWS:
        os.system(WINDOWS_CMD)
        return

    move_py = project_root() / "utils" / "move.py"
    result = subprocess.run(
        [str(venv_python()), str(move_py)],
        cwd=project_root(),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(get_now_timestamp(), "ERROR: no se pudo mover el ratón.")
        if result.stderr:
            print(result.stderr.strip())


def move_mouse() -> None:
    """
    Mueve el cursor si el usuario lleva más de AWAY_TIME segundos inactivo.

    Returns:
        None
    """
    # Import tardío: requiere PyGObject del venv tras setup_environment()
    from utils.idle import Monitor  # pylint: disable=import-outside-toplevel

    while True:
        seconds = Monitor.get_idle_sec()
        if seconds > AWAY_TIME:
            print(
                get_now_timestamp(),
                "You were away more than",
                AWAY_TIME,
                "seconds. Moving mouse...",
            )
            run_move()
        else:
            print(get_now_timestamp(), "User activity detected")
            time.sleep(POLL_INTERVAL)


def main() -> None:
    """
    Main function to run the program

    Run kps v to see the version
    Run kps -t 10 to set the time to 10 seconds
    Run kps to run the program
    """
    print("kps v" + App_version())
    commandline()

    try:
        setup_environment()
    except RuntimeError as error:
        print(f"[kps] ERROR: {error}", file=sys.stderr)
        sys.exit(1)

    move_mouse()


if __name__ == "__main__":
    main()
