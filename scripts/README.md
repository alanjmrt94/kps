# Scripts de instalación — kps

Scripts para preparar el entorno de ejecución en cada plataforma.

## Flujo común

1. Comprobar / instalar dependencias del sistema (solo Linux y macOS si aplica)
2. Crear `.venv` con `python3 -m venv --system-site-packages .venv` (Linux)
3. Activar el entorno (`source .venv/bin/activate` o `activate.bat` en Windows)
4. Actualizar `pip`, `wheel`, `setuptools`
5. Instalar dependencias pip desde `requirements-*.txt` (Linux: solo python-uinput; GI vía apt)
6. Verificar imports críticos

## Linux — `install.sh`

**Requisitos:** Debian/Ubuntu, `apt-get`, `sudo` (para paquetes de sistema y udev).

```bash
./scripts/install.sh
```

- Instala paquetes apt **solo si no están presentes** (incl. `python3-gi`, `libgirepository-2.0-dev` para Ubuntu 24.04+)
- Crea `.venv` con **`--system-site-packages`** (PyGObject/pycairo desde apt, no compila desde pip)
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

kps **no usa el GTK del escritorio** (MATE GTK3, GNOME GTK4, etc.). Idle en Linux:

1. D-Bus `org.freedesktop.ScreenSaver`
2. D-Bus `org.gnome.Mutter.IdleMonitor` (GNOME/Wayland)
3. XScreenSaver / `libXss` (solo sesión **X11**)

| Escritorio | Sesión | Backend habitual |
|------------|--------|------------------|
| GNOME | Wayland | D-Bus (Mutter o freedesktop) |
| GNOME, KDE | X11 | D-Bus o XScreenSaver |
| MATE, Xfce, LXQt, Cinnamon | X11 | XScreenSaver |
| KDE Plasma | Wayland | D-Bus freedesktop (si disponible) |

En **Ubuntu MATE (X11)** suele funcionar vía XScreenSaver aunque no exista el D-Bus de GNOME. En **Wayland sin D-Bus idle**, el monitor puede fallar; preferir X11 o un compositor que exponga idle por D-Bus.

Ver también la sección **Compatibilidad** en el [README](../README.md) del proyecto.

**Lanzador:** `../run` (install + `kps.py`).

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
| `requirements.txt` | Linux | python-uinput (PyGObject/pycairo vía apt + system-site-packages) |
| `requirements-windows.txt` | Windows | pyautogui |
| `requirements-macos.txt` | macOS | pyautogui, pyobjc-framework-Quartz |

`python-uinput` se instala **solo desde PyPI** (decisión Fase 0.5).
