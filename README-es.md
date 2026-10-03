# kps

<small>[GitHub](https://github.com/alanjmrt94/kps) · [PyPI — `kps-idle`](https://pypi.org/project/kps-idle/) · [Releases](https://github.com/alanjmrt94/kps/releases) · <a href="README.md"><img src="https://flagcdn.com/w20/us.png" width="20" alt="Read in English" /> Read in English</a></small>

Mantiene el cursor en movimiento si estás ausente para evitar inactividad.

## Características

* Soporta **Windows**, **Linux** y **macOS**.
* En Linux, **X11** y **Wayland**.
* **Instala dependencias** con scripts de plataforma y un virtualenv.
* Requiere **Python 3.10+**.
* **Perfiles** con horario, estado en bandeja, pulso ratón/teclado/`both`/`inhibit`, `kps doctor` y autostart del AppImage.

El programa corre en segundo plano. Tras inactividad puede mover el ratón, pulsar una tecla, hacer ambas cosas, o solo inhibir el sleep del SO.

## Modos de pulso

| Modo | CLI | Efecto |
|------|-----|--------|
| `mouse` | (por defecto) | Mueve el cursor |
| `keyboard` | `--keyboard-only` | Solo pulso de Shift |
| `both` | `--keyboard` | Ratón y teclado a la vez |
| `inhibit` | `--inhibit-only` | El SO no duerme (`systemd-inhibit` / `caffeinate` / `SetThreadExecutionState`); sin fingir entrada |

Los perfiles (`work`, `night`, …) van en `config.toml` en `[profiles.nombre]` con `pulse` y `start`/`end`. Fuera de horario kps queda **pausado** (bandeja) y suelta la inhibición.

Bandeja: **activo** / **ausente** / **pausado**. Comandos: `kps doctor`, `kps autostart enable|disable|status`.

## Últimos cambios

Release **v2.2.0** — solo inhibir idle/sleep:

* `--inhibit-only` / `--pulse inhibit`: el SO no duerme (sin ratón ni teclado)
* Linux `systemd-inhibit`, macOS `caffeinate`, Windows `SetThreadExecutionState`

Release **v2.1.0** — perfiles, bandeja, doctor, autostart:

* `--pulse mouse|keyboard|both|inhibit`; bandeja: activo / ausente / pausado
* `kps doctor` y `kps autostart enable` (AppImage vía `$APPIMAGE`)

Release **v2.0.7** — AppImage para Ubuntu 18.04–26.04:

* Build en glibc 2.27 (Docker Ubuntu 18.04); runtime estático (sin `libfuse2`)
* AppImageUpdate (`.zsync`); bandeja por defecto; un solo icono 128×128

Release **v2.0.6** — AppImage para AppImageHub:

* Un solo `kps.png` de 128×128 dentro del AppImage (sin la copia del bundle PyInstaller)

Release **v2.0.5** — PyPI `kps-idle`:

* Paquete PyPI renombrado a **`kps-idle`** (`pip install kps-idle`; comando CLI `kps`)
* **`release.sh`**: artefactos y URL PyPI según `pyproject.toml`; error explícito si twine falla

Release **v2.0.4** — Windows CI y validación:

* Job **`test-windows`** estable (`linux_uinput_modules`, rutas bundled con `Path.resolve()`)
* **Windows 10/11** validado manualmente (`kps.exe`, idle, movimiento)

Release **v2.0.2** — calidad de código:

* Docstrings en tests, `idle.py` y `generate_icons.py`
* **`lint.sh`**: autopep8 + reparación de comentarios pylint; pylint 10/10
* Tests uinput compatibles con CI Windows (`importlib`)

Release **v2.0.1** — parche AppImage:

* **AppStream** en AppImage (metadatos validados por `appimagetool`)
* **`run-appimage`**: pregunta por instalar `libfuse2`; fallback sin FUSE
* **CI:** job `build-appimage` en GitHub Actions (artefacto `kps-x86_64.AppImage`)

Release **v2.0.0** — dependencias mínimas, empaquetado e iconos:

* **Linux:** 6 paquetes apt (sin PyGObject ni `python-uinput`); D-Bus vía `gdbus`/`busctl`; uinput vía ctypes
* **Empaquetado:** `dist/kps.exe` (Win), `dist/kps.app` (macOS), `dist/kps-*.AppImage` (Linux); `./run-appimage`
* **Iconos:** suite en `assets/icons/` desde `image_base.png` / `image_base.icns`; bandeja `--tray`
* **Desinstalar:** `./run --uninstall` o `./scripts/install.sh --uninstall`
* **Movimiento in-process** — sin subprocess; corrige fallos de import en Linux

**Migración desde v1.7.x (Linux):** `./run --uninstall -y` (opcional) y luego `./run`. Borra un `.venv` antiguo si usaba `--system-site-packages`. Ver [CHANGES.md](CHANGES.md#200).

Release **v1.7.2** — parche CI y mypy; Wayland + GNOME validado (Ubuntu 26.04).

Release **v1.7.0** — tray, systemd, teclado opcional, hotkey Unix, PyInstaller Windows.

Notas completas (en español): [CHANGES.md](CHANGES.md).

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
| Windows 10/11 | **Sí** — idle WinAPI + pyautogui + `kps.exe` | Hotkey F1–F12 solo en Windows |
| macOS 12+ | Implementado | Accesibilidad; prueba manual pendiente |

## Inicio rápido

Clonar el repositorio:

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

## Uso manual

Tras la instalación:

    python3 kps.py

Usá `-h` para ver opciones. Ejemplos:

    python3 kps.py -t 10
    python3 kps.py -p 3 -v
    python3 kps.py -q
    python3 kps.py -n -t 5          # dry-run: probar idle sin mover ratón
    python3 kps.py -d --pid-file /tmp/kps.pid   # segundo plano (Linux)
    python3 kps.py --keyboard-only  # solo Shift, sin mover el cursor
    python3 kps.py --keyboard       # ratón y teclado en paralelo
    python3 kps.py --inhibit-only   # solo inhibir idle/sleep del SO
    python3 kps.py --profile work
    python3 kps.py doctor
    python3 kps.py autostart enable

### Archivo de configuración

Copiá `config.example.toml` a `~/.config/kps/config.toml` (Linux) o `%APPDATA%\kps\config.toml` (Windows).
La CLI tiene prioridad sobre el archivo. Perfiles de ejemplo: `[profiles.work]`, `[profiles.night]`.

```toml
[kps]
pulse = "mouse"          # mouse | keyboard | both | inhibit
profile = "work"

[profiles.work]
pulse = "both"
start = "09:00"
end = "18:00"
```

    mkdir -p ~/.config/kps
    cp config.example.toml ~/.config/kps/config.toml

Autostart (Linux, útil con AppImage):

    kps autostart enable    # ~/.config/autostart + systemd --user
    kps autostart status
    kps autostart disable

Diagnóstico (uinput, idle D-Bus, herramienta inhibit, firma AppImage):

    kps doctor

Detener daemon en Linux:

    kill -USR1 $(cat /tmp/kps.pid)
    # o
    kill -TERM $(cat /tmp/kps.pid)

## Detalles de instalación

| Plataforma | Script install | Requirements pip | Lanzador |
|------------|----------------|------------------|----------|
| Linux | `scripts/install.sh` | `scripts/requirements.txt` | `run` |
| Windows | `scripts/install.bat` | `scripts/requirements-windows.txt` | `run.bat` |
| macOS | `scripts/install-macos.sh` | `scripts/requirements-macos.txt` | `run-macos` |

### Paquetes de sistema Linux (mínimo)

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
| Linux | `./scripts/build_appimage.sh` | `dist/kps-*.AppImage` (+ `.zsync`) | `assets/icons/linux/kps.png` + `hicolor/` |

**Suite de iconos:** ya está en `assets/icons/`. Comprobar con `./scripts/verify_icons.sh`.

**Desarrollo** (con venv): `./run` · **AppImage** (sin Python): `./run-appimage` o `./dist/kps-*.AppImage`

El AppImage se construye en Ubuntu 18.04 (glibc 2.27) vía Docker cuando el host es más nuevo, para cubrir Ubuntu 18.04–26.04. Incluye runtime estático (no necesita `libfuse2`) y, al publicarlo, el `.zsync` para AppImageUpdate.

**Firma GPG:** el build firma el AppImage con la clave del proyecto si está disponible en el anillo local (`KPS_GPG_KEY_ID`, por defecto `73140C59FF3EBE5D`). Para omitir: `KPS_APPIMAGE_SIGN=0`.

```bash
# Verificar un AppImage descargado (sin APPIMAGE_EXTRACT_AND_RUN)
./kps-x86_64.AppImage --appimage-signature

# Importar la clave pública del repo
gpg --import keys/kps-signing-key.asc
# Fingerprint: 5077A813F9AE818752168EA173140C59FF3EBE5D
# Key ID: 73140C59FF3EBE5D
# https://keys.openpgp.org
```

Tras `install.bat` / `install-macos.sh` / `install.sh`, ejecutá el script de build de tu plataforma. En macOS puede hacer falta **Accesibilidad** para `pyautogui`. En Linux el AppImage aún requiere **gdbus** y permisos **uinput** en el host (ver abajo).

### Dependencias Python (pip)

**Linux** (`scripts/requirements.txt`):

* `pynput` (+ `wheel`, `setuptools`)
* Idle D-Bus y uinput son **módulos internos** (`utils/dbus_idle.py`, `utils/uinput_device.py`)

**Windows** (`scripts/requirements-windows.txt`):

* `pyautogui`, `pynput`

**macOS** (`scripts/requirements-macos.txt`):

* `pyautogui`, `pynput`, `pyobjc-framework-Quartz`

Todos los paquetes Python se instalan desde **PyPI** en `.venv` en la raíz del proyecto (`pip install kps-idle` también está publicado; el comando sigue siendo `kps`).

### Linux: permisos uinput (sin sudo)

kps mueve el cursor vía `/dev/uinput`. **No se usa sudo en runtime.**

1. Ejecutá `./scripts/install.sh` (o `./run`). El script:
   - carga el módulo `uinput` del kernel
   - instala la regla udev en `/etc/udev/rules.d/40-uinput.rules`
   - añade tu usuario al grupo `uinput`
2. **Cerrá sesión y volvé a entrar** (o reiniciá) para que el grupo surta efecto.
3. Verificá acceso:

       ls -l /dev/uinput
       groups

   Deberías ver el grupo `uinput` y permisos `crw-rw----` con grupo `uinput`.

4. Al arrancar, `kps.py` comprueba imports y abre uinput **sin sudo**. Si falla, muestra un mensaje con el paso siguiente.

**Regla udev** (`scripts/udev-rules/40-uinput.rules`):

    SUBSYSTEM=="misc", KERNEL=="uinput", MODE="0660", GROUP="uinput"

## Desarrollo

Instalar en modo editable con dependencias de desarrollo:

    pip install -e ".[dev]"

Tests y lint:

    pytest          # cobertura ≥ 95% en CI Linux (~296 tests)
    pylint kps.py utils/*.py tests/*.py

CI en GitHub corre los mismos checks en cada push/PR a `main`/`master`: `lint`, `mypy`, `test-linux` (3.10–3.12), `test-windows` y **`build-appimage`** (artefacto descargable).

Instalar como comando global (tras `pip install .`):

    kps -h

## Estructura del proyecto (install/run)

```
kps/
├── README.md              # Documentación en inglés
├── README-es.md           # Documentación en español
├── CHANGES.md             # Notas de versión (español)
├── config.example.toml    # Perfiles de ejemplo (work / night)
├── run                    # Linux: install + run
├── run-appimage           # Linux: ejecutar AppImage en dist/
├── run.bat                # Windows: install + run
├── run-macos              # macOS: install + run
├── kps.py                 # Programa principal
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
│   ├── verify_icons.sh    # Verificar iconos antes de empaquetar
│   ├── requirements*.txt
│   └── udev-rules/
│       └── 40-uinput.rules
├── keys/
│   └── kps-signing-key.asc  # Clave pública GPG (AppImage / commits)
└── utils/                 # Core (cli, runner, inhibit, doctor, tray, …)
```

**v2.2.0** — `--inhibit-only`. **v2.1.0** — perfiles, bandeja, doctor, autostart, docs bilingües. Pendiente: prueba manual macOS y notarización Apple.

## Releases anteriores

Release v1.1.6:

* Instalación automática de dependencias según SO y versión de Python
* Utilidades de versión
* Corrección de strings y typos
* Mostrar versión de kps
