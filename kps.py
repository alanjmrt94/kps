import argparse
import os
import time
from datetime import datetime
from getpass import getpass
from subprocess import call
from utils.const import OsType

from utils.idle import Monitor
from utils.install import Autoinstall
from utils.version import App_version

AWAY_TIME = 2
POLL_INTERVAL = 5
LINUX_CMD = "python3 ./utils/move.py"
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
        global AWAY_TIME
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


def move_mouse(pwd: str | None) -> None:
    """
    Move the mouse cursor if the user is away for more than the set time
    with sudo password if the system is Linux, otherwise call the command without sudo

    Args:
        pwd: sudo password if the system is Linux, otherwise None
    Returns:
        None
    """
    # Set the command based on OS type
    cmd = WINDOWS_CMD if os.name == OsType.WINDOWS else LINUX_CMD

    while 1:
        seconds = Monitor.get_idle_sec()
        if seconds > AWAY_TIME:
            print(
                get_now_timestamp(),
                "You were away more than",
                AWAY_TIME,
                "seconds. Moving mouse...",
            )
            if pwd is None:
                os.system(cmd)
            else:
                call(f"echo {pwd} | sudo -S {cmd}", shell=True)
        else:
            print(get_now_timestamp(), "User activity detected")
            time.sleep(POLL_INTERVAL)
    return


def main():
    """
    Main function to run the program

    Run kps v to see the version
    Run kps -t 10 to set the time to 10 seconds
    Run kps to run the program
    """
    print("kps v" + App_version())
    commandline()

    if os.name == OsType.WINDOWS:
        move_mouse(None)
    else:
        print("On Linux, you must enter your sudo password for it to work: ")
        pwd = getpass()
        # Fix: Set the command before using it
        cmd = LINUX_CMD
        call(f"echo {pwd} | sudo -S {cmd}", shell=True)
        Autoinstall()
        move_mouse(pwd)


if __name__ == "__main__":
    main()
