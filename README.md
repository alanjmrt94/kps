# kps

Keep moving the cursor if you are away to avoid inactivity.

## Features

* Supports **Windows**, **Linux** and **macOS**.
* On Linux, supports both **X11** and **Wayland**!
* **Auto install dependencies** via platform scripts and virtualenv.
* Supports **Python 3+**.

The program works in the background and waits only for inactivity to move the mouse.

## Latest changes

Release **v1.3.0** — Linux install fixes (Ubuntu 24.04+):

* **Venv:** `--system-site-packages`; recrea `.venv` automáticamente si es incompatible
* **PyGObject:** desde apt (`python3-gi`), no compila desde pip
* **apt:** `libgirepository-2.0-dev`, `gir1.2-glib-2.0`; detección de paquetes corregida
* **pip (Linux):** solo `python-uinput`

See [CHANGES.md](CHANGES.md) for full release notes.

## Quick start

Clone the repository:

    git clone https://github.com/alanjmrt94/kps
    cd kps

### Linux (Debian/Ubuntu)

Instalar y ejecutar en un paso:

    ./run

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
| Linux | `scripts/install.sh` | `scripts/requirements.txt` | `run` |
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

### Linux: permisos uinput (sin sudo)

kps mueve el cursor vía `/dev/uinput`. **No se usa sudo en runtime.**

1. Ejecuta `./scripts/install.sh` (o `./run`). El script:
   - carga el módulo `uinput` del kernel
   - instala la regla udev en `/etc/udev/rules.d/40-uinput.rules`
   - añade tu usuario al grupo `uinput`
2. **Cierra sesión y vuelve a entrar** (o reinicia) para que el grupo surta efecto.
3. Verifica acceso:

       ls -l /dev/uinput
       groups

   Deberías ver el grupo `uinput` y permisos `crw-rw----` con grupo `uinput`.

4. Al arrancar, `kps.py` comprueba imports y abre uinput **sin sudo**. Si falla, muestra un mensaje con el paso siguiente.

**Regla udev** (`scripts/udev-rules/40-uinput.rules`):

    SUBSYSTEM=="misc", KERNEL=="uinput", MODE="0660", GROUP="uinput"

## Project layout (install/run)

```
kps/
├── run                    # Linux: install + run
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
