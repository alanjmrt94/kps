"""Instalación de dependencias de kps por plataforma."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from utils.const import OsType

VENV_DIR_NAME = ".venv"

# Verificación de imports tras instalar (por plataforma)
_VERIFY_LINUX = """
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gio, GLib, GObject
import uinput
"""

_VERIFY_WINDOWS = """
import pyautogui
"""

_VERIFY_MACOS = """
import pyautogui
from Quartz import CGEventSourceSecondsSinceLastEventType
"""


def project_root() -> Path:
    """Ruta raíz del proyecto kps."""
    return Path(__file__).resolve().parent.parent


def scripts_dir() -> Path:
    """Directorio scripts/ del proyecto."""
    return project_root() / "scripts"


def venv_dir() -> Path:
    """Ruta del entorno virtual .venv."""
    return project_root() / VENV_DIR_NAME


def venv_python() -> Path:
    """Ejecutable python dentro del venv según la plataforma."""
    root = venv_dir()
    if sys.platform == "win32":
        return root / "Scripts" / "python.exe"
    return root / "bin" / "python3"


def venv_pip() -> Path:
    """Ejecutable pip dentro del venv según la plataforma."""
    root = venv_dir()
    if sys.platform == "win32":
        return root / "Scripts" / "pip.exe"
    return root / "bin" / "pip"


def detect_os() -> str:
    """Devuelve linux, windows o macos según el sistema actual."""
    if os.name == OsType.WINDOWS:
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def requirements_file() -> Path:
    """Archivo requirements pip correspondiente a la plataforma."""
    name = {
        "linux": "requirements.txt",
        "windows": "requirements-windows.txt",
        "macos": "requirements-macos.txt",
    }[detect_os()]
    return scripts_dir() / name


def platform_install_script() -> Path:
    """Script de instalación del sistema operativo actual."""
    name = {
        "linux": "install.sh",
        "windows": "install.bat",
        "macos": "install-macos.sh",
    }[detect_os()]
    return scripts_dir() / name


def _run(cmd: list[str], *, cwd: Path | None = None, shell: bool = False) -> None:
    """Ejecuta un subprocess y propaga errores."""
    subprocess.run(cmd, cwd=cwd or project_root(), check=True, shell=shell)


def run_platform_install() -> None:
    """Ejecuta el script de instalación del sistema operativo actual."""
    script = platform_install_script()
    if not script.is_file():
        raise FileNotFoundError(f"No se encontró el script de instalación: {script}")

    print(f"[kps] Ejecutando {script.name}...")
    if detect_os() == "windows":
        _run([str(script)], shell=True)
    else:
        _run(["bash", str(script)])


def ensure_venv() -> Path:
    """Crea .venv una sola vez si no existe."""
    path = venv_dir()
    if path.is_dir():
        print(f"[kps] Entorno virtual existente: {path}")
        return path

    print(f"[kps] Creando entorno virtual en {path}...")
    _run([sys.executable, "-m", "venv", str(path)])
    return path


def install_pip_deps() -> None:
    """Instala dependencias pip en .venv (fallback o uso directo desde Python)."""
    req = requirements_file()
    if not req.is_file():
        raise FileNotFoundError(f"No se encontró {req}")

    ensure_venv()
    pip = venv_pip()
    if not pip.is_file():
        raise FileNotFoundError(f"No se encontró pip en el venv: {pip}")

    print(f"[kps] Instalando dependencias desde {req.name}...")
    _run([str(pip), "install", "--upgrade", "pip", "wheel", "setuptools"])
    _run([str(pip), "install", "-r", str(req)])


def verify_imports() -> bool:
    """Comprueba que los imports principales funcionan en el venv."""
    py = venv_python()
    if not py.is_file():
        print("[kps] ERROR: no existe el intérprete del venv. Ejecuta la instalación primero.")
        return False

    code = {
        "linux": _VERIFY_LINUX,
        "windows": _VERIFY_WINDOWS,
        "macos": _VERIFY_MACOS,
    }[detect_os()]

    print("[kps] Verificando imports principales...")
    result = subprocess.run(
        [str(py), "-c", code.strip()],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("[kps] ERROR: falló la verificación de imports.")
        if result.stderr:
            print(result.stderr.strip())
        return False

    print("[kps] OK: imports verificados.")
    return True


def test_package() -> bool:
    """Comprueba que el entorno está listo para ejecutar kps."""
    return verify_imports()


def autoinstall() -> None:
    """
    Instala dependencias según la plataforma:
    1. Script install del OS (apt/venv/pip o equivalente)
    2. Verificación de imports en .venv
    """
    print("[kps] Iniciando autoinstalación...")
    run_platform_install()
    if not verify_imports():
        raise RuntimeError(
            "La instalación terminó pero los imports no pasaron la verificación. "
            "Revisa la salida de install.sh o instala manualmente con ./scripts/install.sh"
        )
    print("[kps] Autoinstalación completada.")


# Alias legacy usado por kps.py
Autoinstall = autoinstall
