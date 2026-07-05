# kps

Keep moving the cursor if you are away to avoid inactivity.

## Features

* Supports **Windows**, **Linux** and **macOS**.
* On Linux, supports both **X11** and **Wayland**!
* **Auto install dependencies** via platform scripts and virtualenv.
* Supports **Python 3+**.

The program works in the background and waits only for inactivity to move the mouse.

## Latest changes

Release **v2.0.0** — dependencias mínimas, empaquetado e iconos:

* **Linux:** 6 paquetes apt (sin PyGObject ni `python-uinput`); D-Bus vía `gdbus`/`busctl`; uinput vía ctypes
* **Empaquetado:** `dist/kps.exe` (Win), `dist/kps.app` (macOS), `dist/kps-*.AppImage` (Linux); `./run-appimage`
* **Iconos:** suite en `assets/icons/` desde `image_base.png` / `image_base.icns`; bandeja `--tray`
* **Desinstalar:** `./run --uninstall` o `./scripts/install.sh --uninstall`
* **Movimiento in-process** — sin subprocess; corrige fallos de import en Linux
* **211 tests** (1 skipped), cobertura ~98%

**Migración desde v1.7.x (Linux):** `./run --uninstall -y` (opcional) y luego `./run`. Borra `.venv` antiguo si usaba `--system-site-packages`. Ver [CHANGES.md](CHANGES.md#200).

Release **v1.7.2** — parche CI y mypy; Wayland + GNOME validado (Ubuntu 26.04).

Release **v1.7.0** — tray, systemd, teclado opcional, hotkey Unix, PyInstaller Windows.

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

**Distros con script de instalación:** Debian/Ubuntu (`scripts/install.sh`). Otras distros: instalar manualmente `python3`, `libglib2.0-bin`, `libx11-6`, `libxss1`, permisos uinput y `pip install pynput`.

**Importante:** kps **no usa GTK ni PyGObject**. En Linux, idle vía **D-Bus** (`gdbus`/`busctl`) y, en X11, **XScreenSaver** (`libXss`). Movimiento del ratón vía `/dev/uinput` (ctypes, sin `python-uinput`).

| Escritorio / entorno | Sesión típica | Detección idle | Movimiento ratón |
|----------------------|---------------|----------------|------------------|
| **GNOME** (Ubuntu, Fedora…) | Wayland | D-Bus `org.gnome.Mutter.IdleMonitor` (o freedesktop) — **probado Ubuntu 26.04** | uinput |
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
| Ubuntu 22.04 / 24.04 / **26.04** + GNOME (Wayland) | **Sí** — idle Mutter D-Bus + uinput | Re-login tras install (grupo `uinput`) |
| Ubuntu MATE (GTK3, X11) | Sí — XScreenSaver + uinput (v1.4.1) | Wayland MATE no verificado |
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

### Linux system packages (mínimo)

`install.sh` instala **solo si faltan** (6 paquetes apt):

* `python3`, `python3-pip`, `python3-venv`
* `libglib2.0-bin` — cliente D-Bus (`gdbus`) para idle en Wayland/GNOME
* `libx11-6`, `libxss1` — fallback XScreenSaver en sesión X11

Además configura `/dev/uinput` vía udev (`scripts/udev-rules/40-uinput.rules`). **No** se instalan PyGObject, build-essential ni paquetes `-dev`.

### Empaquetado (usuario final, sin instalar Python)

| Plataforma | Build | Salida | Icono requerido |
|------------|-------|--------|-----------------|
| Windows | `scripts\build_windows.bat` | `dist\kps.exe` | `assets/icons/kps.ico` |
| macOS | `bash scripts/build_macos.sh` | `dist/kps.app` | `assets/icons/kps.icns` |
| Linux | `./scripts/build_appimage.sh` | `dist/kps-*.AppImage` | `assets/icons/linux/kps.png` + `hicolor/` |

**Suite de iconos:** coloca `assets/image_base.png` (y opcionalmente `assets/image_base.icns`) y ejecuta `./scripts/generate_icons.sh`. Verificar con `./scripts/verify_icons.sh`.

**Desarrollo** (con venv): `./run` · **AppImage** (sin Python): `./run-appimage` o `dist/kps-*.AppImage`

Tras `install.bat` / `install-macos.sh` / `install.sh`, ejecuta el script de build de tu plataforma. En macOS puede hacer falta **Accesibilidad** para `pyautogui`. En Linux el AppImage aún requiere **gdbus** y permisos **uinput** en el host (ver abajo).

### Python dependencies (pip)

**Linux** (`scripts/requirements.txt`):

* `pynput` (+ `wheel`, `setuptools`)
* Idle D-Bus y uinput son **módulos internos** (`utils/dbus_idle.py`, `utils/uinput_device.py`)

**Windows** (`scripts/requirements-windows.txt`):

* `pyautogui`, `pynput`

**macOS** (`scripts/requirements-macos.txt`):

* `pyautogui`, `pynput`, `pyobjc-framework-Quartz`

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

    pytest          # 211 tests; cobertura ≥ 95% en CI
    pylint kps.py utils/*.py tests/*.py

CI en GitHub corre los mismos checks en cada push/PR a `main`/`master`.

Instalar como comando global (tras `pip install .`):

    kps -h

## Project layout (install/run)

```
kps/
├── run                    # Linux: install + run
├── run-appimage           # Linux: ejecutar AppImage en dist/
├── run.bat                # Windows: install + run
├── run-macos              # macOS: install + run
├── kps.py                 # Main program
├── assets/
│   ├── image_base.png     # Fuente iconos (PNG)
│   ├── image_base.icns    # Fuente iconos (macOS, opcional)
│   └── icons/             # Suite generada (ICO, ICNS, hicolor, tray)
├── scripts/
│   ├── install.sh         # Linux install / --uninstall
│   ├── install.bat        # Windows install
│   ├── install-macos.sh   # macOS install
│   ├── build_appimage.sh  # Linux AppImage
│   ├── build_macos.sh     # macOS .app
│   ├── build_windows.bat  # Windows .exe
│   ├── kps.spec           # PyInstaller Windows
│   ├── kps-macos.spec     # PyInstaller macOS
│   ├── kps-linux.spec     # PyInstaller Linux (AppImage)
│   ├── generate_icons.sh  # Generar suite de iconos
│   ├── verify_icons.sh    # Verificar iconos
│   ├── requirements*.txt
│   └── udev-rules/
│       └── 40-uinput.rules
└── utils/                 # Core modules
```

## Development plan

See `.cursor/plans/kps_pending.plan.md` for the current roadmap.

**v2.0.0** — dependencias mínimas en Linux, empaquetado Win/macOS/AppImage, iconos y desinstalación. Pendiente: pruebas manuales Windows/macOS y PyPI opcional.

## Older releases

Release v1.1.6:

* Auto install dependencies depending on OS platform and py version
* Add version utilities
* Fix strings and typos
* Show kps version
