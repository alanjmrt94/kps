# Release notes

## 2.0.2

**Parche calidad de código y CI.**

### Lint y documentación

* Docstrings en `utils/idle.py`, `scripts/generate_icons.py` y todos los tests
* **`scripts/lint.sh`**: reparación post-autopep8 de comentarios `# pylint: disable=...` partidos
* Pylint **10/10** en los 41 archivos `.py` del proyecto

### Tests

* **`test_uinput_device`**: carga vía `importlib` tras `importorskip("fcntl")` (compatible Windows CI)
* Correcciones pylint en `test_move` y `Protocol` de idle

---

## 2.0.1

**Parche AppImage y runtime empaquetado.**

### AppImage

* Metadatos **AppStream** (`io.github.alanjmrt94.kps.appdata.xml`) — validación `appstreamcli` OK
* Desktop entry con id reverse-DNS (`io.github.alanjmrt94.kps.desktop`)
* **`run-appimage`**: ofrece instalar **libfuse2** con apt; opción `-y`; fallback `APPIMAGE_EXTRACT_AND_RUN=1`

### Runtime empaquetado

* **`verify_bundled_runtime()`** — verificación de imports y uinput **in-process** vía `importlib` (PyInstaller no soporta `python -c`)
* Corrige: `Los imports no están disponibles en el binario empaquetado`

### CI

* Job **`build-appimage`** en GitHub Actions (`.github/workflows/ci.yml`)
* Ejecuta `build_appimage.sh`, smoke test con `APPIMAGE_EXTRACT_AND_RUN=1` y publica artefacto `kps-x86_64.AppImage` (14 días)

### Tests

* Nuevos casos bundled en `test_install.py`

---

## 2.0.0

**Release mayor — dependencias mínimas, empaquetado multiplataforma e iconos.**

### Cambios rompedores (migración desde v1.7.x)

* **Linux:** ya no se usa PyGObject (`python3-gi`) ni `python-uinput` en pip. Tras actualizar:
  1. `./run --uninstall -y` (opcional: limpia venv y paquetes apt de kps)
  2. `./run` (reinstala con 6 paquetes apt y venv nuevo sin `--system-site-packages`)
  3. Cerrar sesión si cambió el grupo `uinput`
* Si conservas un `.venv` antiguo (con `--system-site-packages`), bórralo y ejecuta `./scripts/install.sh`.
* Idle D-Bus y movimiento uinput son **módulos internos**; no hace falta instalar `gi` ni compilar nada.

### Linux — apt mínimo (X11 y Wayland)

* Eliminados PyGObject, `python-uinput`, build-essential y paquetes `-dev` (~20 → **6** paquetes apt)
* Paquetes apt: `python3`, `python3-pip`, `python3-venv`, `libglib2.0-bin`, `libx11-6`, `libxss1`
* Idle D-Bus vía `gdbus`/`busctl`/`dbus-send` (`utils/dbus_idle.py`)
* Movimiento uinput vía ctypes (`utils/uinput_device.py`)
* Venv estándar (sin `--system-site-packages`)
* Wayland: D-Bus Mutter / freedesktop / MATE (sin cambios funcionales)
* X11: fallback XScreenSaver con `libx11-6` + `libxss1` (runtime)
* **`utils/idle.py`** simplificado: delega en `dbus_idle` y XScreenSaver; sin imports `gi`
* **`utils/app.py`** — detección X11/Wayland solo con variables de entorno (sin Gdk)
* **`utils/keyboard_pulse.py`** — pulso Shift en Linux vía `uinput_device` (sin `python-uinput`)

### Movimiento del ratón y runtime

* **`run_move()`** ejecuta el movimiento **in-process** (dev y empaquetado); ya no lanza subprocess `utils/move.py` (evita `ModuleNotFoundError: utils`)
* **`utils/move.py`** — ejecutable directo (`python utils/move.py`) con bootstrap de `sys.path`
* **`is_bundled()`** (`utils/install.py`) — omite venv, autoinstall y verify de pip en binarios PyInstaller/AppImage
* **Daemon** (`utils/daemon.py`) — en modo empaquetado re-ejecuta el binario, no `kps.py`

### Desinstalación

* `./scripts/install.sh --uninstall` — preview, confirmación y borrado de `.venv` + paquetes apt de kps
* `./run --uninstall` — delega a `install.sh --uninstall`
* Opción `-y` / `--yes` para omitir confirmación
* **No** elimina `python3`, la regla udev ni revierte el grupo `uinput`

### Empaquetado (usuario final)

* **Windows:** `scripts/build_windows.bat` + `scripts/kps.spec` → `dist/kps.exe`
* **macOS:** `scripts/build_macos.sh` + `scripts/kps-macos.spec` → `dist/kps.app`
* **Linux:** `scripts/build_appimage.sh` + `scripts/kps-linux.spec` → `dist/kps-<arch>.AppImage`
* Specs versionados en el repo (`*.spec` en `scripts/`; excepción en `.gitignore`)
* Lanzador **`./run-appimage`** (desde la raíz del repo)
* Builds excluyen `gi` / PyGObject del bundle

### Iconos

* Suite en `assets/icons/` (ICO, ICNS, hicolor, bandeja, AppImage)
* Fuentes: `assets/image_base.png`, `assets/image_base.icns` (opcional)
* Scripts: `scripts/generate_icons.sh`, `scripts/verify_icons.sh`, `scripts/generate_icons.py`
* **`utils/icons.py`** — rutas de iconos en dev y empaquetado; bandeja `--tray` y datos PyInstaller
* **`utils/tray.py`** — carga icono desde `assets/icons/kps-tray.png`

### CI y calidad

* Job **`test-linux`**: eliminado paso apt PyGObject; tests idle vía mocks de `dbus_idle`
* **211 tests** (1 skipped), cobertura ~98% (umbral CI ≥ 95%)
* Nuevos: `test_dbus_idle.py`, `test_uinput_device.py`, `test_icons.py`
* Actualizados: `test_idle.py`, `test_install.py`, `test_runner.py`, `test_move.py`, `test_daemon.py`, …

### Otros

* **`.gitignore`**: `build/appimage/`, `build/tools/`, `assets/icons/build/`, `*.AppImage`
* Plan de pendientes: `.cursor/plans/kps_pending.plan.md`

---

## 1.7.2

**Parche CI y mypy (post v1.7.1).**

### CI

* **GitHub Actions** actualizadas a `actions/checkout@v6` y `actions/setup-python@v6` (runtime **Node.js 24**; sin aviso de deprecación de Node 20)

### mypy

* Corrige los 5 errores del job `mypy` en CI:
  * `utils/app.py` — retorno `bool` explícito y `str` en nombre de clase Gdk
  * `utils/config_file.py` — `cast` tras `tomllib.loads`
  * `utils/hotkey.py` — `ctypes.windll` en Windows (`type: ignore[attr-defined]`)
  * `utils/idle.py` — protocolo `_MonitorApi` para `Monitor` multiplataforma
* Job **mypy** pasa a ser **bloqueante** (eliminado `continue-on-error`)

---

## 1.7.1

**Parche de documentación y CI (post v1.7.0).**

### CI y calidad

* **Pylint en CI** ampliado a `tests/*.py` (antes solo `kps.py` y `utils/`)
* **178 tests** (1 skipped), cobertura **100%** en `utils/` + `kps` + `tests/` cubiertos por suite
* `.pylintrc`: `init-hook` para resolver `pytest` sin activar venv manualmente
* Pre-commit alineado: pylint sobre `kps`, `utils` y `tests`

### Documentación

* README y plan actualizados al estado real post-v1.7 (métricas, pendientes, §8)

---

## 1.7.0

**Post-plan: distribución, UX avanzada y cobertura ampliada.**

### Nuevas funciones

* **`--keyboard`** / `keyboard_pulse` en TOML — pulso de Shift además del ratón; **desactivado por defecto**
* **`--tray`** / `tray` en TOML — icono en bandeja (`pip install "kps[gui]"`: pystray + Pillow)
* **Hotkey F1–F12** en Linux/macOS vía `pynput` (antes solo Windows)
* **D-Bus MATE** — `org.mate.ScreenSaver` en cadena idle (Wayland/X11 MATE)
* **systemd user** — `scripts/kps-user.service` + `scripts/install-systemd.sh`
* **PyInstaller** — `scripts/kps.spec` + `scripts/build_windows.bat`

### Calidad

* **178 tests** (1 skipped), cobertura **100%** (umbral CI ≥ 95%)
* Tests: hotkey, keyboard pulse, tray, MATE idle, timelapse multi-ciclo (`-t` en sesiones largas)
* **mypy** gradual en `pyproject.toml` + job CI no bloqueante
* Dependencia **pynput** en requirements Linux/Windows/macOS

### Módulos nuevos

* `utils/keyboard_pulse.py`, `utils/hotkey.py`, `utils/tray.py`

---

## 1.6.2

**CI multiplataforma y cobertura completa (parche sobre 1.6.1).**

### GitHub Actions

* **`test-linux`** (Python 3.10, 3.11, 3.12): paso apt + `PyGObject` para tests de `utils/idle.py` en el runner
* **`test-windows`**: imports Unix-only eliminados del arranque del módulo
* Corrige fallos de collection por `gi`, `uinput` y `StrEnum` en la matrix completa

### Código

* **`StrEnum` en Python 3.10** — polyfill en `utils/const.py` (stdlib desde 3.11)
* **`grp` solo Linux** — import diferido en `is_in_uinput_group()` (Windows en CI)
* **`uinput` lazy** — import dentro de `move_once()` (collectors sin pip `python-uinput`)

### Tests y cobertura

* **152 tests** (1 skipped), cobertura **~100%** en 3.12 local; umbral CI **≥ 95%** (3.10 ~99% por ramas solo 3.11+)
* Ajustes CI: mock de `grp`/`uinput` en collectors; deps GObject en `test-linux`
* Cobertura al 100% — ramas antes sin cubrir:
  * `test_const.py` — polyfill `StrEnum` (simula Python 3.10)
  * `test_install.py` — `grp` ausente, `verify_imports` sin stderr, `verify_uinput_device` sin hint
  * `test_runner.py` — salida del bucle con shutdown ya solicitado
  * `test_shutdown.py` — sin `SIGUSR1`, tecla `F13`, mensaje Windows no-hotkey
  * `test_idle.py` — alias `Monitor = DesktopIdleMonitor()` (reload como win32)
  * `test_move.py` — `move_once()` con `uinput` mockeado
* `pyproject.toml`: `--cov-fail-under=95` en Linux; `test-windows` usa `--cov-fail-under=0` (bloque GObject de `idle.py` no cargable en win32)
* Tests portables: rutas con `as_posix()`, `project_root` mockeado, módulo `grp` inyectado en `sys.modules`

---

## 1.6.1

**Tests, cobertura y validación pre-release (parche sobre 1.6.0).**

### Tests y cobertura

* Suite ampliada: **144 tests** (antes 51), **1 skipped**
* Cobertura **~99%** en `utils/` + `kps` (umbral CI: **≥ 95%**)
* Nuevos/renovados: `tests/test_kps.py`, cobertura de `install`, `idle`, `shutdown`, `daemon`, entrypoints `move_*.py`
* `pyproject.toml`: `--cov=kps`, sin omitir módulos de plataforma; `fail-under=95`

### CI / lint

* **GitHub Actions** verificado en remoto (push/PR): `lint`, `test-linux` 3.10–3.12, `test-windows`
* **`.pylintrc`**: `ignored-modules=gi,gi.repository` (PyGObject es dep de sistema, no del venv de CI); alias `Autoinstall` en `good-names`

### Validación instalación

* **Ubuntu limpio (VM)**: `./run` desde cero sin hacks — `install.sh`, venv, imports y arranque OK

---

## 1.6.0

**Calidad y distribución (Fase 5).**

### Tests

* Suite **`tests/`** con pytest (51 tests, cobertura ≥ 60% en `utils/`)
* `tests/test_cli.py`, `test_config_file.py`, `test_install.py`, `test_idle.py`, `test_move.py`, `test_runner.py`, …

### Empaquetado

* **`pyproject.toml`** — metadata, `pip install .`, entry point **`kps = kps:main`**
* Dependencias dev: `pip install ".[dev]"` (pytest, pytest-cov, pylint)

### CI/CD

* **`.github/workflows/ci.yml`** — jobs `lint`, `test-linux` (3.10–3.12), `test-windows`
* **`.pre-commit-config.yaml`** — pylint + pytest local

### Otros

* `utils/move_pyautogui.py` — import lazy de pyautogui (Linux sin dep extra)

---

## 1.5.0

**Experiencia de usuario (Fase 4).**

### Configuración persistente

* Archivo **`~/.config/kps/config.toml`** (Linux) o **`%APPDATA%\kps\config.toml`** (Windows)
* Ejemplo en **`config.example.toml`**
* Nuevo **`utils/config_file.py`** — carga TOML (`tomllib` 3.11+ o lector mínimo en 3.10)
* La **CLI tiene prioridad** sobre el archivo de config

### Nuevas opciones CLI

| Opción | Descripción |
|--------|-------------|
| `-n` / `--dry-run` | Detecta inactividad sin mover el ratón |
| `-d` / `--daemon` | Ejecuta en segundo plano |
| `--config PATH` | Ruta alternativa al config TOML |
| `--log-file PATH` | Escribe logs también en archivo |
| `--pid-file PATH` | Guarda PID (útil con `--daemon`) |
| `--hotkey KEY` | Cierre con tecla (Windows: F1–F12) |

### Cierre graceful

* Señales **SIGINT**, **SIGTERM** y **SIGUSR1** (Linux/macOS daemon)
* Bucle interrumpible entre sondeos (`utils/shutdown.py`)
* Mensaje de salida con motivo del cierre

### Daemon

* **`utils/daemon.py`** — re-ejecuta en segundo plano (`--foreground` interno)
* Linux: `kill -TERM PID` o `kill -USR1 PID`

---

## 1.4.1

**Logging y arranque más silenciosos** — validado en Ubuntu MATE / Xfce (X11 + XScreenSaver).

### Install (`scripts/install.sh`)

* `pip install -q` — sin listado de *Requirement already satisfied*
* Verificación post-install alineada con runtime: solo **Gio** + **uinput** (sin Gtk/Gdk)
* Corregido mensaje del lanzador: `./run` (antes `.run`)

### Arranque (`utils/install.py`)

* Sin verificación duplicada de imports tras `./run` (install.sh ya verifica; kps comprueba en silencio)
* uinput: mensajes de éxito suprimidos en arranque normal; errores siguen visibles

### Idle y bucle

* Fallback D-Bus (ScreenSaver, Mutter) pasa a **DEBUG** — esperado en MATE/Xfce
* Una línea **INFO** al elegir backend: `Monitor idle: XScreenSaver (X11)` (o D-Bus en GNOME)
* `Set interval` del monitor interno → DEBUG
* **Actividad detectada** en el bucle → DEBUG; en INFO solo movimientos del ratón
* Detalle completo con `-v`

---

## 1.4.0

**Soporte multiplataforma (Fase 3).**

### Linux (3.1)

* Detección idle vía **Gio/D-Bus** sin exigir GTK4/Gdk en import
* Wayland detectado con `XDG_SESSION_TYPE` (sin Gdk)
* Fallback: `org.freedesktop.ScreenSaver` → `org.gnome.Mutter.IdleMonitor` → XScreenSaver (solo X11)
* Verificación post-install Linux: solo `Gio` + `uinput` (no Gtk/Gdk)

### Windows (3.2)

* Nuevo **`utils/move_win.py`** — movimiento del cursor con pyautogui
* Eliminada dependencia de `utils/move.bat` (inexistente)
* **`utils/runner.py`** unifica ejecución de move por plataforma vía venv

### macOS (3.3)

* Nuevo **`utils/move_mac.py`** — movimiento con pyautogui
* **`MacIdleMonitor`** — tiempo idle vía Quartz (`CGEventSourceSecondsSinceLastEventType`)
* Monitor desktop ligero sin PyGObject en Windows/macOS

### Otros

* **`utils/app.py`** — detección Wayland/X11 con fallback sin Gdk
* Constantes de move por OS en `utils/const.py` (`MOVE_SCRIPT_LINUX/WINDOWS/MACOS`)

### Documentación

* **Tabla de compatibilidad** en README: Python, distros Linux, escritorios (GNOME, MATE, KDE, Xfce…), X11/Wayland y backends idle
* `scripts/README.md`: entornos Linux adicionales y requisitos por sesión gráfica

---

## 1.3.1

**Refactor arquitectónico (Fase 2).**

* Eliminar `utils/sleepy.py` (código legacy no usado)
* Centralizar constantes en `utils/const.py` (`DEFAULT_AWAY_TIME`, `DEFAULT_POLL_INTERVAL`, rutas de move)
* Nuevo `utils/cli.py` — argparse, `KpsConfig`, logging (`-v` / `-q`), CLI `-p` / `--poll`
* Nuevo `utils/runner.py` — bucle de inactividad y `run_move()`
* `kps.py` reducido a entrypoint mínimo
* Mensajes de usuario en español vía logging

---

## 1.3.0

**Fix Linux install on Ubuntu 24.04+** — venv, PyGObject y apt.

### Resumen

* Venv Linux con `--system-site-packages` (PyGObject/pycairo desde apt, no compila pip)
* Recreación automática de `.venv` si no incluye paquetes del sistema
* Dependencias apt corregidas para GIRepository 2.0 (`libgirepository-2.0-dev`)
* Comprobación apt más robusta (`gir1.2-glib-2.0` en lugar de `gir1.2-gio-2.0`)
* Pip en Linux: solo `python-uinput` (+ wheel/setuptools)

### Cambios en `scripts/install.sh`

* Usar `.venv/bin/python3` explícitamente (Debian no siempre expone `python` en el venv)
* Detectar venv incompatible y recrearlo sin intervención manual
* `is_pkg_satisfied()` / `apt_pkg_exists()` — evita falsos “falta 1 paquete” sin instalar nada
* Paquetes apt añadidos: `libgirepository-2.0-dev`, `gir1.2-girepository-2.0-dev`

### Cambios en `scripts/requirements.txt` (Linux)

* Eliminados `PyGObject` y `pycairo` del pip (provistos por `python3-gi` / `python3-gi-cairo`)

### `utils/install.py`

* `ensure_venv()` alineado con `--system-site-packages` en Linux
* Recreación automática del venv si falta `system-site-packages`

---

## 1.2.0

**Fix installation and startup flow** — Fase 0 + Fase 1 completadas.

### Resumen

* Instalación multiplataforma con scripts dedicados y lanzadores (`run`, `run.bat`, `run-macos`)
* Entorno virtual único (`.venv`) con dependencias pip desde PyPI
* Arranque de `kps.py` sin contraseña sudo en runtime
* uinput configurado vía udev + grupo `uinput` (sudo solo en `install.sh`)
* Verificación automática del entorno antes del bucle principal

---

### Fase 0 — Consolidación

* Refactor de `kps.py`: type hints, constantes (`AWAY_TIME`, `POLL_INTERVAL`), mejor estructura
* Restaurar `utils/__init__.py` vacío como marcador de paquete Python
* Normalizar permisos: `644` en código/docs; `755` solo en scripts ejecutables
* Migrar backlog de `_NOTES.MD` al plan de desarrollo (§11) y eliminar el archivo suelto
* `python-uinput` instalado exclusivamente vía **pip/PyPI** (sin lib vendoreada en `libs/`)
* Lanzadores multiplataforma en la raíz del proyecto

### Instalación y lanzadores

* **`scripts/install.sh`** (Debian/Ubuntu):
  * Instala paquetes apt **solo si faltan**
  * Crea `.venv` con `python3 -m venv .venv`
  * Activa el entorno con `source .venv/bin/activate`
  * Instala pip deps desde `scripts/requirements.txt`
  * Configura uinput: módulo kernel, regla udev, grupo `uinput`
  * Verifica imports (`gi`, `Gdk`, `Gio`, `uinput`)
* **`scripts/install.bat`** (Windows) y **`scripts/install-macos.sh`** (macOS): venv → activate → pip
* **`scripts/requirements-windows.txt`** y **`scripts/requirements-macos.txt`**
* **`scripts/udev-rules/40-uinput.rules`** — permisos `0660` para grupo `uinput`
* Lanzadores: **`run`** (Linux), **`run.bat`** (Windows), **`run-macos`** (macOS)

---

### Fase 1 — Instalación y arranque

#### `utils/install.py` (reescrito)

* `detect_os()` — linux / windows / macos
* `run_platform_install()` — delega al script install del OS
* `ensure_venv()` — crea `.venv` una sola vez (corrige bug de recrear venv por paquete)
* `install_pip_deps()` — fallback pip desde Python
* `verify_imports()` — comprueba deps en el venv por plataforma
* `verify_setup()` — venv + imports + uinput en Linux
* `verify_uinput_device()` — prueba real de `/dev/uinput` sin sudo
* `is_in_uinput_group()` / `describe_uinput_issue()` — diagnóstico y mensajes de re-login
* `ensure_venv_runtime()` — re-ejecuta kps con el Python del venv
* `setup_environment()` — orquesta install + verify + venv runtime
* `autoinstall()` / alias `Autoinstall` — API pública de instalación

#### `kps.py` (nuevo flujo)

```
CLI → setup_environment() → move_mouse()
```

* Eliminados `getpass`, `sudo` y `echo {pwd} | sudo -S` del runtime
* Import tardío de `Monitor` (PyGObject solo tras activar venv)
* `run_move()` usa `.venv/bin/python3 utils/move.py` (sin sudo)
* Errores de movimiento capturados con mensaje en stderr

#### `utils/move.py`

* Errores claros (`PermissionError`, `OSError`) con instrucciones en español
* Exit codes para uso desde subprocess

#### Seguridad

* Sin contraseñas en shell ni en el bucle de movimiento del ratón
* Elevación con `sudo` **solo** en `scripts/install.sh` (setup one-time, prompt interactivo)

#### Documentación

* `README.md` — quick start, tabla de scripts, permisos uinput sin sudo, re-login
* `scripts/README.md` — flujo de install por plataforma y verificación post-install

---

### Cambios respecto a 1.1.6

| Antes (1.1.6) | Ahora (1.2.0) |
|---------------|---------------|
| `utils/install.py` recreaba `.venv` en cada paquete pip | venv único; install delegado a scripts |
| `Autoinstall()` después de sudo al inicio | `setup_environment()` antes del bucle |
| Contraseña sudo en cada movimiento del ratón | uinput vía grupo `uinput`, sin sudo en runtime |
| `python3 kps.py` con Python del sistema | Re-ejecución automática con Python del venv |
| README: "Pure Python, no C modules" | Deps reales documentadas (PyGObject, uinput, etc.) |
| Sin lanzadores | `run`, `run.bat`, `run-macos` |

### Migración desde 1.1.6

1. Clonar/actualizar el repo
2. Ejecutar `./scripts/install.sh` (o `./run`)
3. **Cerrar sesión y volver a entrar** (grupo `uinput`)
4. Verificar: `groups` incluye `uinput`; `ls -l /dev/uinput` muestra `crw-rw---- root uinput`
5. Ejecutar `./run` o `.venv/bin/python3 kps.py`

### Limitaciones conocidas (1.2.0)

* Resueltas en **1.4.0**: Windows (`move_win.py`) y macOS (`move_mac.py` + Quartz idle)
* `utils/install.py` legacy en 1.1.6 reemplazado; usar scripts + `setup_environment()`
* Prueba en Ubuntu limpio (VM) — validada en **v1.6.1**

---

## 1.1.6

* Auto install dependencies depending on OS platform and py version
* Add version utilities
* Fix strings and typos
* Show kps version
* Fix const enums
* Fix .venv location

## 1.1.0

* Auto install dependencies on Linux
* Fix user space detection
* Update time settings

## 1.0.0

*-* Initial release.
