# Scripts de instalación — kps

Scripts para preparar el entorno de ejecución en cada plataforma.

## Flujo común

1. Comprobar / instalar dependencias del sistema (solo Linux y macOS si aplica)
2. Crear `.venv` en la raíz del proyecto (`python3 -m venv .venv`)
3. Activar el entorno (`source .venv/bin/activate` o `activate.bat` en Windows)
4. Actualizar `pip`, `wheel`, `setuptools`
5. Instalar dependencias desde el `requirements-*.txt` correspondiente (PyPI)
6. Verificar imports críticos

## Linux — `install.sh`

**Requisitos:** Debian/Ubuntu, `apt-get`, `sudo` (para paquetes de sistema y udev).

```bash
./scripts/install.sh
```

- Instala paquetes apt **solo si no están presentes**
- Carga módulo `uinput` y aplica regla udev desde `udev-rules/40-uinput.rules`
- Añade el usuario al grupo `uinput` (requiere re-login)

**Lanzador:** `../.run` (install + `kps.py`).

## Windows — `install.bat`

**Requisitos:** Python 3 en PATH (`python`).

```bat
scripts\install.bat
```

**Lanzador:** `..\run.bat`.

## macOS — `install-macos.sh`

**Requisitos:** `python3` (Homebrew opcional si falta).

```bash
./scripts/install-macos.sh
```

**Lanzador:** `../run-macos`.

## Requirements

| Archivo | Plataforma | Paquetes principales |
|---------|------------|----------------------|
| `requirements.txt` | Linux | PyGObject, pycairo, python-uinput |
| `requirements-windows.txt` | Windows | pyautogui |
| `requirements-macos.txt` | macOS | pyautogui, pyobjc-framework-Quartz |

`python-uinput` se instala **solo desde PyPI** (decisión Fase 0.5).
