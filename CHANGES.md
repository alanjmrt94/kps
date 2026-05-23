# Release notes

## 1.2.0

### Fase 0 — Consolidación

* Refactor de `kps.py`: type hints, constantes (`AWAY_TIME`, `POLL_INTERVAL`), imports al inicio, fix de contraseña sudo en el bucle de movimiento del ratón
* Restaurar `utils/__init__.py` vacío como marcador de paquete Python
* Normalizar permisos: `644` en código y docs; `755` solo en scripts ejecutables (`.run`, `install.sh`, etc.)
* Migrar backlog de `_NOTES.MD` al plan de desarrollo (§11) y eliminar el archivo suelto
* Decisión `python-uinput`: instalación exclusiva vía **pip/PyPI** (sin lib vendoreada en `libs/`)

### Instalación y lanzadores multiplataforma

* Reescribir `scripts/install.sh` (Debian/Ubuntu):
  * Instala paquetes apt **solo si faltan**
  * Crea `.venv` con `python3 -m venv .venv`
  * Activa el entorno con `source .venv/bin/activate`
  * Instala dependencias pip desde `scripts/requirements.txt`
  * Configura uinput: módulo kernel, regla udev (`scripts/udev-rules/`), grupo `uinput`
  * Verifica imports (`gi`, `Gdk`, `Gio`, `uinput`)
* Añadir `scripts/install.bat` (Windows) y `scripts/install-macos.sh` (macOS) con el mismo flujo: venv → activate → pip
* Añadir `scripts/requirements-windows.txt` y `scripts/requirements-macos.txt`
* Añadir lanzadores en la raíz del proyecto:
  * **Linux:** `.run` → `install.sh` + `kps.py`
  * **Windows:** `run.bat` → `install.bat` + `kps.py`
  * **macOS:** `run-macos` → `install-macos.sh` + `kps.py`

### Documentación

* Actualizar `README.md` con instalación por plataforma y uso de lanzadores
* Plan de desarrollo en `.cursor/plans/kps_desarrollo_completo.plan.md`

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
