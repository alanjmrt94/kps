import argparse
import os
import time
from datetime import datetime
from getpass import getpass
from subprocess import call
from utils.const import OsType

from utils.install import Autoinstall, Restart
from utils.version import App_version

away_time = 2
poll_interval = 5
cmd = 'python3 ./utils/move.py'


def commandline():
    parser = argparse.ArgumentParser(
        description="This program keep moving the cursor if you are away to avoid inactivity."
                    "This program won't do anything if you are using your computer.")

    parser.add_argument(
        "-t", "--time", type=int,
        help="time in seconds of how long to wait after a user is considered inactive.(Default: 2)")

    args = parser.parse_args()

    if args.time:
        global away_time
        away_time = int(args.time)

    print('Set move mouse time every',
          str(away_time), 'seconds of inactivity.\n')


def get_now_timestamp():
    now = datetime.now()
    return now.strftime("%H:%M:%S")


def move_mouse(pwd):
    from utils.idle import Monitor
    while 1:
        seconds = Monitor.get_idle_sec()
        if seconds > away_time:
            print(get_now_timestamp(), 'You were away more than',
                  away_time, 'seconds. Moving mouse...')
            if pwd == None:
                os.system(cmd)
            else:
                call('echo {} | sudo -S {}'.format("", cmd), shell=True)
        else:
            print(get_now_timestamp(), 'User activity detected')
            time.sleep(poll_interval)
    return


def main():
    print("kps v" + App_version())
    commandline()

    if os.name == OsType.WINDOWS:
        move_mouse(None)
    else:
        print("On Linux you must enter your sudo password for it to work: ")
        pwd = getpass()
        call('echo {} | sudo -S {}'.format(pwd,
             "sudo :>/dev/null 2>&1"), shell=True)
        Autoinstall()
        move_mouse(pwd)


if __name__ == "__main__":
    main()
