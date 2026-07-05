# Scripts de instalación — kps

Scripts para preparar el entorno de ejecución en cada plataforma.

## Flujo común

1. Comprobar / instalar dependencias del sistema (Linux: mínimo apt)
2. Crear `.venv` con `python3 -m venv .venv`
3. Activar el entorno (`source .venv/bin/activate` o `activate.bat` en Windows)
4. Actualizar `pip`, `wheel`, `setuptools`
5. Instalar dependencias pip desde `requirements-*.txt`
6. Verificar imports críticos

## Linux — `install.sh`

**Requisitos:** Debian/Ubuntu, `apt-get`, `sudo` (para paquetes de sistema y udev).

```bash
./scripts/install.sh
```

- Instala **6 paquetes apt** solo si faltan: Python, `libglib2.0-bin` (gdbus), `libx11-6`, `libxss1`
- **Sin** PyGObject, build-essential ni paquetes `-dev`
- Idle Wayland/X11: D-Bus vía `gdbus`/`busctl`/`dbus-send` (`utils/dbus_idle.py`)
- Movimiento: `/dev/uinput` vía ctypes (`utils/uinput_device.py`)
- Carga módulo `uinput` y aplica regla udev desde `udev-rules/40-uinput.rules`
- Añade el usuario al grupo `uinput` (requiere **cerrar sesión** para aplicar)

### Tras `install.sh`: re-login obligatorio

El grupo `uinput` no aplica hasta que cierres sesión (o reinicies). Comprueba:

```bash
groups          # debe listar uinput
ls -l /dev/uinput   # crw-rw---- root uinput
```

`kps.py` verifica acceso a uinput **sin sudo** al arrancar. Si falla, indica si falta install o re-login.

### Escritorios y sesiones gráficas (Linux)

kps **no usa GTK ni PyGObject**. Idle en Linux:

1. D-Bus `org.freedesktop.ScreenSaver`
2. D-Bus `org.gnome.Mutter.IdleMonitor` (GNOME/Wayland)
3. D-Bus `org.mate.ScreenSaver`
4. XScreenSaver / `libXss` (solo sesión **X11**)

| Escritorio | Sesión | Backend habitual |
|------------|--------|------------------|
| GNOME | Wayland | D-Bus (Mutter o freedesktop) |
| GNOME, KDE | X11 | D-Bus o XScreenSaver |
| MATE, Xfce, LXQt, Cinnamon | X11 | XScreenSaver |
| KDE Plasma | Wayland | D-Bus freedesktop (si disponible) |

**Lanzador:** `../run` (install + `kps.py`).

### Actualizar desde v1.7.x

kps 2.0 elimina PyGObject y `python-uinput`. Recomendado:

```bash
./run --uninstall -y   # opcional: quita venv y paquetes apt de kps
./run                  # reinstala (6 paquetes apt, venv nuevo)
```

Si no usas `--uninstall`, borra manualmente `.venv` antes de `./scripts/install.sh`.

Desinstalar venv y paquetes apt de kps (con confirmación):

```bash
./run --uninstall
# o
./scripts/install.sh --uninstall
```

No elimina `python3` ni revierte la regla udev / grupo `uinput`. Opción `-y` para omitir confirmación.

## Windows — `install.bat` + `build_windows.bat`

**Requisitos:** Python 3 en PATH (`python`).

```bat
scripts\install.bat
scripts\build_windows.bat
```

Genera `dist\kps.exe` (PyInstaller, sin Python instalado).

Spec: `scripts\kps.spec` (excluye `gi`).

**Lanzador desarrollo:** `..\run.bat`.

## macOS — `install-macos.sh` + `build_macos.sh`

**Requisitos:** `python3` (Homebrew opcional si falta).

```bash
./scripts/install-macos.sh
./scripts/build_macos.sh
```

Genera `dist/kps.app` (PyInstaller). Puede requerir **Accesibilidad** en Ajustes → Privacidad.

Spec: `scripts/kps-macos.spec`.

**Lanzador desarrollo:** `../run-macos`.

## Iconos (`assets/icons/`)

Ver [`assets/icons/README.md`](../assets/icons/README.md) para la lista completa de archivos.

```bash
./scripts/generate_icons.sh      # desde assets/image_base.png (+ image_base.icns)
./scripts/verify_icons.sh      # qué falta
```

| Archivo | Plataforma |
|---------|------------|
| `kps.ico` | Windows `.exe` |
| `kps.icns` | macOS `.app` |
| `linux/kps.png` | AppImage (256×256) |
| `linux/hicolor/*/apps/kps.png` | Menú Linux |
| `kps-tray.png` | Bandeja `--tray` |

## Linux — AppImage — `build_appimage.sh` + `run-appimage`

**Requisitos para compilar:** `.venv` (ejecuta `./scripts/install.sh` o `./run` una vez), `wget` o `curl`.

```bash
./scripts/build_appimage.sh
```

Genera `dist/kps-x86_64.AppImage` (o `kps-aarch64.AppImage` en ARM).

Spec PyInstaller: `kps-linux.spec` (excluye `gi`; incluye `assets/icons/` si existen).

Metadatos AppStream: `scripts/appimage/io.github.alanjmrt94.kps.appdata.xml` (validado por `appimagetool`).

### CI (GitHub Actions)

El workflow `.github/workflows/ci.yml` incluye el job **`build-appimage`**:

1. Crea `.venv` e instala `scripts/requirements.txt`
2. Ejecuta `./scripts/build_appimage.sh`
3. Smoke test: `APPIMAGE_EXTRACT_AND_RUN=1 dist/kps-x86_64.AppImage -h`
4. Publica el artefacto **`kps-x86_64-appimage`** (retención 14 días)

### Cómo ejecutar el AppImage

| Quién | Desde dónde | Comando |
|-------|-------------|---------|
| Desarrollador (repo clonado) | Raíz del proyecto | `./run-appimage -h` |
| Usuario final | Cualquier carpeta | `./kps-x86_64.AppImage -h` o doble clic (terminal) |

`run-appimage` busca `dist/kps-<arquitectura>.AppImage` y reenvía los argumentos a CLI de kps.

Usa FUSE si `libfuse2` está instalado. Si no, **pregunta** si instalarlo con apt (`libfuse2`); con `-y` instala sin confirmar. Si se rechaza o falla, usa `APPIMAGE_EXTRACT_AND_RUN=1`.

Si ejecutas el `.AppImage` directamente y falla con `libfuse.so.2`, usa `./run-appimage` o `sudo apt install libfuse2`.

### Qué incluye / qué no

**Dentro del AppImage:** Python, pynput y módulos kps (sin pip ni `.venv`).

**En el sistema host (una vez):**

* `gdbus` / `busctl` / `dbus-send` — idle en Wayland (`libglib2.0-bin`)
* `libX11` + `libXss` — idle en X11
* `/dev/uinput` + grupo `uinput` — `./scripts/install.sh` (udev; no va dentro del AppImage)

**Lanzador desarrollo con venv:** `../run`.

## Lint y tipos (`lint.sh`)

Pylint no tiene `--fix`; el script usa **autopep8** (PEP 8, `max-line-length=100`) y luego **pylint** + **mypy** como en CI.

```bash
./scripts/lint.sh           # fix + verificar
./scripts/lint.sh --check   # solo pylint y mypy
./scripts/lint.sh --fix     # solo autopep8
```

Requiere `pip install ".[dev]"` (o el script instala autopep8 / dev en el venv activo).

## Publicación (release)

`release.sh` — menú interactivo para publicar una versión:

| Opción | Qué hace |
|--------|----------|
| GitHub Release | Tag `vX.Y.Z`, notas desde `CHANGES.md`, adjunta `dist/*` si existen |
| PyPI | `python -m build` + `twine upload` |
| AppImage | `build_appimage.sh`; opcionalmente sube el `.AppImage` al release |
| AppImageHub | PR a [appimage.github.io](https://github.com/AppImage/appimage.github.io) (`data/kps`) |
| Todo | Tests (opcional) → PyPI → AppImage → GitHub → PR AppImageHub (opcional) |

**Requisitos**

* `gh` autenticado (`gh auth login`)
* `PYPI_API_TOKEN` o `TWINE_PASSWORD` (token de [pypi.org](https://pypi.org/manage/account/token/))
* Versión alineada en `utils/const.py` y `pyproject.toml`
* Sección `## X.Y.Z` en `CHANGES.md` para las notas del release

```bash
export PYPI_API_TOKEN=pypi-...
./scripts/release.sh              # menú interactivo
./scripts/release.sh appimagehub  # solo PR al catálogo
```

**AppImageHub**

1. Publica antes el **GitHub Release** con el `.AppImage` adjunto (la inspección descarga el binario con `wget`).
2. Opción **6** o `./scripts/release.sh appimagehub`:
   - **Alta nueva** — crea `data/kps` con la URL del repo (`scripts/appimage/appimagehub.data`).
   - **Re-inspección** — añade o quita una línea `#` para forzar actualización de metadatos.
3. El script hace fork, branch, commit y `gh pr create` contra `AppImage/appimage.github.io`.
4. Espera el check verde en el PR; catálogo: https://appimage.github.io/kps/

**¿Dónde publicar además?**

* **GitHub Releases** — canal principal para el AppImage y futuros `.exe` / `.app`.
* **PyPI** — `pip install kps`; las dependencias de plataforma siguen vía `install.sh` / `pip install kps[gui]`.
* **AppImageHub** — catálogo comunitario (PR automatizado desde `release.sh`).
* Homebrew / Winget / Flathub — solo si más adelante mantienes fórmulas o empaquetado distinto (no necesario ahora).

## Requirements

| Archivo | Plataforma | Paquetes principales |
|---------|------------|----------------------|
| `requirements.txt` | Linux | pynput (uinput/D-Bus internos) |
| `requirements-windows.txt` | Windows | pyautogui, pynput |
| `requirements-macos.txt` | macOS | pyautogui, pynput, pyobjc-framework-Quartz |
