# kps

Keep moving the cursor if you are away to avoid inactivity.

## Features

* Supports **Windows**, **Linux** and **macOS**.
* On Linux, supports both **X11** and **Wayland**!
* **Auto install dependencies** via platform scripts and virtualenv.
* Supports **Python 3+**.

The program works in the background and waits only for inactivity to move the mouse.

## Latest changes

Release v1.2.0:

* **Fase 0:** refactor de `kps.py`, permisos, `utils/__init__.py`, backlog migrado al plan, `python-uinput` vía pip
* **Linux:** `scripts/install.sh` — apt solo si faltan paquetes, `.venv`, `source .venv/bin/activate`, pip desde `scripts/requirements.txt`, udev/uinput
* **Windows / macOS:** `scripts/install.bat`, `scripts/install-macos.sh` y requirements por plataforma
* **Lanzadores:** `.run` (Linux), `run.bat` (Windows), `run-macos` (macOS) — instalan y ejecutan `kps.py`

See [CHANGES.md](CHANGES.md) for full release notes.

## Quick start

Clone the repository:

    git clone https://github.com/alanjmrt94/kps
    cd kps

### Linux (Debian/Ubuntu)

Instalar y ejecutar en un paso:

    ./.run

Solo instalar:

    ./scripts/install.sh

Luego manualmente:

    source .venv/bin/activate
    python kps.py

### Windows

Doble clic o en CMD/PowerShell:

    run.bat

Solo instalar:

    scripts\install.bat

### macOS

    ./run-macos

Solo instalar:

    ./scripts/install-macos.sh

## Manual usage

After installation:

    python3 kps.py

Use `-h` to see available options. Example:

    python3 kps.py -t 10

## Installation details

| Plataforma | Script install | Requirements pip | Lanzador |
|------------|----------------|------------------|----------|
| Linux | `scripts/install.sh` | `scripts/requirements.txt` | `.run` |
| Windows | `scripts/install.bat` | `scripts/requirements-windows.txt` | `run.bat` |
| macOS | `scripts/install-macos.sh` | `scripts/requirements-macos.txt` | `run-macos` |

### Linux system packages

`install.sh` installs (if missing): build tools, Python dev, GTK4/GIO stack, X11/XSS libs, `libudev-dev`, and configures `/dev/uinput` via udev rule in `scripts/udev-rules/40-uinput.rules`.

### Python dependencies (pip)

**Linux** (`scripts/requirements.txt`):

* `pycairo`, `PyGObject`, `python-uinput`, `setuptools`, `wheel`

**Windows** (`scripts/requirements-windows.txt`):

* `pyautogui`

**macOS** (`scripts/requirements-macos.txt`):

* `pyautogui`, `pyobjc-framework-Quartz`

All Python packages are installed from **PyPI** into `.venv` at the project root.

## Project layout (install/run)

```
kps/
├── .run                    # Linux: install + run
├── run.bat                 # Windows: install + run
├── run-macos               # macOS: install + run
├── kps.py                  # Main program
├── scripts/
│   ├── install.sh          # Linux install
│   ├── install.bat         # Windows install
│   ├── install-macos.sh    # macOS install
│   ├── requirements.txt
│   ├── requirements-windows.txt
│   ├── requirements-macos.txt
│   └── udev-rules/
│       └── 40-uinput.rules
└── utils/                  # Core modules
```

## Development plan

See `.cursor/plans/kps_desarrollo_completo.plan.md` for the full roadmap (Fase 1+).

## Older releases

Release v1.1.6:

* Auto install dependencies depending on OS platform and py version
* Add version utilities
* Fix strings and typos
* Show kps version
