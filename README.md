# kps

Keep moving the cursor if you are away to avoid inactivity.

## Features

* Supports **Windows**, **Linux** and **macOS**.
* On Linux, supports both **X11** and **Wayland**!
* **Pure Python**, no C modules to be compiled.
* **Auto install dependencies**.
* Supports **Python 3+**.
  
The program works in the background and waits only for inactivity to move the mouse.

## Latest changes

Release v1.2.0:

* Rewrite `scripts/install.sh` for Debian/Ubuntu: system packages, uinput (kernel module, udev rule, user group), virtualenv, and pip install from `scripts/requirements.txt`
* Add missing system dependencies (X11/XSS idle fallback, `libudev-dev`, Python build tools, GTK4/GIO stack)
* Improve `scripts/requirements.txt` with `wheel` and minimum versions for `pycairo`, `PyGObject`, `setuptools`, and `python-uinput`
* Fallback to vendored `libs/python-uinput-1.0.1` when PyPI install fails
* Verify core imports (`gi`, `Gdk`, `Gio`, `uinput`) at the end of installation

Release v1.1.6:

* Auto install dependencies depending on OS platform and py version
* Add version utilities
* Fix strings and typos
* Show kps version

## Usage

Clone the repository (no installation required, source files are sufficient):

    git clone https://github.com/alanjmrt94/kps

On a terminal, run:

    python3 kps.py

*Use -h to see available options.*
