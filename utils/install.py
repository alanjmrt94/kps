import os
import subprocess
import sys

from utils.const import OsType
from utils.version import Py_version

module = ""
venv_path = ".venv"

ubuntu_apt_reqs = "libcairo2 libcairo2-dev pkg-config python3-dev libgirepository1.0-dev python3-gi libxt-dev python3-uinput"
pip_reqs = ["pycairo", "PyGObject", "python-uinput"]

def install_apt():
    print("Check and install apt packages:\n")
    proc = subprocess.Popen('sudo apt install -y ' + ubuntu_apt_reqs, shell=True, executable="/bin/bash")
    proc.wait()

def create_and_activate_venv(venv_path):
    subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

    if sys.platform.startswith("win"):
        activate_script = os.path.join(venv_path, "Scripts", "activate")
        subprocess.run([activate_script], shell=True, check=True)
    else:
        activate_script = os.path.join(venv_path, "bin", "activate")
        subprocess.run([".", activate_script], shell=True, check=True)

def install_package(venv_path, package):
    print("\nInstalling package {0}\n".format(package))
    if (Py_version() < 3):
        subprocess.run([os.path.join(venv_path, "bin", "pip"), "install", package], check=True)
    else:
        subprocess.run([os.path.join(venv_path, "bin", "pip3"), "install", package], check=True)

def install(package_name):
    create_and_activate_venv(venv_path)
    install_package(venv_path, package_name)

def deactivate_env():
    # Deactivate the virtual environment
    if sys.platform.startswith("win"):
        deactivate_script = os.path.join(venv_path, "Scripts", "deactivate")
        subprocess.run([deactivate_script], shell=True, check=True)
    else:
        deactivate_script = os.path.join(venv_path, "bin", "deactivate")
        subprocess.run([".", deactivate_script], shell=True, check=True)

def Restart():
    print("restart")
    subprocess.run([os.path.join(venv_path, "bin", "python3"), "kps.py"], check=True)

def Autoinstall():
    if os.name == OsType.UNIX:
        install_apt()
        install("pycairo")
        install("PyGObject")
        install("python-uinput")

def test_package():
    try:
        print("\n\tTesting new package...\n")
        # TODO: TEST FUNC
    except:
        print()
        # print("\n\tPackage {} couldn't be loaded".format(module))
