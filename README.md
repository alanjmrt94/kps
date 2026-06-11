# kps

Keep moving the cursor if you are away to avoid inactivity.

## Features

* Supports **Windows**, **Linux** and **macOS**.
* On Linux, supports both **X11** and **Wayland**!
* **Auto install dependencies** via platform scripts and virtualenv.
* Supports **Python 3+**.

The program works in the background and waits only for inactivity to move the mouse.

## Latest changes

Release **v1.6.2** — CI multiplataforma y cobertura 100% (parche 1.6.1):

* **152 tests**, cobertura **100%** en `utils/` + `kps`
* Matrix **Linux 3.10–3.12** y **Windows** verdes en GitHub Actions
* Polyfill **`StrEnum`** (Python 3.10), `grp`/`uinput` sin romper collectors en CI
* Job `test-linux`: deps GObject (apt + PyGObject) para tests de idle

Release **v1.6.1** — tests y validación (parche 1.6.0):

* **144 tests**, cobertura **~99%** (umbral CI ≥ 95%)
* **Ubuntu limpio (VM)**: `./run` de cero validado
* Pylint en CI sin falsos positivos por `gi` (dep de apt)

Release **v1.6.0** — calidad (Fase 5):

* **pytest** + `pyproject.toml` (`pip install ".[dev]" && pytest`)
* Comando global **`kps`** tras `pip install .`
* **GitHub Actions** CI (lint + tests Linux/Windows)

Release **v1.5.0** — UX (Fase 4):

* **Config** `~/.config/kps/config.toml` (ver `config.example.toml`)
* **`--dry-run`** — probar idle sin mover ratón
* **`--daemon`** + **`--pid-file`** — segundo plano
* **`--log-file`** — logs a archivo
* Cierre graceful: Ctrl+C, SIGTERM, SIGUSR1 (daemon Linux)

Release **v1.4.1** — logging más limpio (probado en MATE/Xfce X11):

* Menos ruido en install (`pip -q`) y arranque (sin verify duplicado)
* Backend idle visible: `Monitor idle: XScreenSaver (X11)`
* Solo movimientos del ratón en INFO; actividad y fallbacks D-Bus con `-v`

Release **v1.4.0** — multiplataforma (Fase 3):

* **Linux:** idle vía D-Bus (Gio) sin GTK4; Wayland por `XDG_SESSION_TYPE`
* **Windows:** `utils/move_win.py` (pyautogui); sin `move.bat`
* **macOS:** `utils/move_mac.py` + idle Quartz (`MacIdleMonitor`)

Release **v1.3.1** — refactor (Fase 2):

* **`utils/cli.py`** / **`utils/runner.py`** — separación CLI y bucle principal
* **Constantes** centralizadas en `utils/const.py`
* **Logging** con `-v` / `-q`; mensajes en español
* Eliminado `utils/sleepy.py`

See [CHANGES.md](CHANGES.md) for full release notes.

## Compatibilidad

Versiones y entornos probados o esperados según el backend de inactividad y movimiento del ratón.

### Python

| Versión | Estado |
|---------|--------|
| 3.10 – 3.12 | Compatible (objetivo principal; Ubuntu 24.04) |
| 3.8 – 3.9 | Probable; no verificado en CI |
| menor que 3.8 | No soportado |

### Linux

**Distros con script de instalación:** Debian/Ubuntu (`scripts/install.sh`). Otras distros: instalar manualmente PyGObject/Gio, `libxss-dev`, `python-uinput` y permisos uinput.

**Importante:** kps **no depende del GTK del escritorio** (GTK3 vs GTK4 del DE). En runtime solo usa **Gio/D-Bus** y, en X11, **XScreenSaver** (`libXss`). Los paquetes apt `gir1.2-gtk-4.0` / `python3-gi` son la pila PyGObject del sistema, no el toolkit de MATE/GNOME.

| Escritorio / entorno | Sesión típica | Detección idle | Movimiento ratón |
|----------------------|---------------|----------------|------------------|
| **GNOME** (Ubuntu, Fedora…) | Wayland | D-Bus `org.freedesktop.ScreenSaver` o `org.gnome.Mutter.IdleMonitor` | uinput |
| **GNOME** | X11 | D-Bus → fallback XScreenSaver | uinput |
| **Ubuntu MATE**, **Xfce**, **LXQt**, **Cinnamon** | X11 | XScreenSaver (`libXss`) | uinput |
| **KDE Plasma** | X11 | D-Bus freedesktop o XScreenSaver | uinput |
| **KDE Plasma** | Wayland | D-Bus freedesktop (si el compositor lo expone) | uinput |
| **i3**, **Openbox**, WM mínimos | X11 | XScreenSaver | uinput |

**Wayland sin D-Bus idle** (p. ej. MATE experimental en Wayland, algunos compositores): el monitor puede quedar no disponible; usar sesión **X11** o un DE que exponga idle por D-Bus.

**Comprobar en tu máquina:**

```bash
echo "$XDG_SESSION_TYPE"    # x11 o wayland
./run -v                    # logs del backend idle elegido
```

### Windows

| Versión | Detección idle | Movimiento |
|---------|----------------|------------|
| Windows 10 | `GetLastInputInfo` (WinAPI) | pyautogui |
| Windows 11 | Idem | pyautogui |

Requisito: Python 3 en PATH (`python`).

### macOS

| Versión | Detección idle | Movimiento |
|---------|----------------|------------|
| macOS 12+ (Monterey y posteriores) | Quartz `CGEventSourceSecondsSinceLastEventType` | pyautogui |

Requisito: `python3`; permisos de **Accesibilidad** pueden ser necesarios para pyautogui (Ajustes → Privacidad).

### Resumen por plataforma

| Plataforma | Probado / objetivo | Limitaciones conocidas |
|------------|-------------------|------------------------|
| Ubuntu 22.04 / 24.04 + GNOME | Sí | Re-login tras install (grupo `uinput`) |
| Ubuntu MATE (GTK3, X11) | Esperado vía XScreenSaver | Wayland MATE no verificado |
| Windows 10/11 | Implementado | Prueba manual pendiente |
| macOS 12+ | Implementado | Accesibilidad; prueba manual pendiente |

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

Use `-h` to see available options. Examples:

    python3 kps.py -t 10
    python3 kps.py -p 3 -v
    python3 kps.py -q
    python3 kps.py -n -t 5          # dry-run: probar idle sin mover ratón
    python3 kps.py -d --pid-file /tmp/kps.pid   # segundo plano (Linux)

### Config file

Copia `config.example.toml` a `~/.config/kps/config.toml` (Linux) o `%APPDATA%\kps\config.toml` (Windows).
La CLI tiene prioridad sobre el archivo.

    mkdir -p ~/.config/kps
    cp config.example.toml ~/.config/kps/config.toml

Detener daemon en Linux:

    kill -USR1 $(cat /tmp/kps.pid)
    # o
    kill -TERM $(cat /tmp/kps.pid)

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

* `python-uinput` (+ `wheel`, `setuptools`)
* PyGObject y pycairo vía **apt** (`python3-gi`, `python3-gi-cairo`) y venv `--system-site-packages`

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

## Development

Instalar en modo editable con dependencias de desarrollo:

    pip install -e ".[dev]"

Ejecutar tests y lint:

    pytest          # cobertura 100% obligatoria (utils + kps)
    pylint kps.py utils/*.py

CI en GitHub corre los mismos checks en cada push/PR a `main`/`master`.

Instalar como comando global (tras `pip install .`):

    kps -h

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
