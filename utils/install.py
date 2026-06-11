"""Instalación de dependencias de kps por plataforma."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from utils.const import OsType, VENV_DIR_NAME

# Verificación de imports tras instalar (por plataforma)
_VERIFY_LINUX = """
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib, GObject
import uinput
"""

_VERIFY_WINDOWS = """
import pyautogui
"""

_VERIFY_MACOS = """
import pyautogui
from Quartz import CGEventSourceSecondsSinceLastEventType
"""

_UINPUT_DEVICE_TEST = """
import uinput
events = (uinput.REL_X, uinput.REL_Y, uinput.BTN_LEFT, uinput.BTN_RIGHT)
with uinput.Device(events) as device:
    device.emit(uinput.REL_X, 1)
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


def venv_has_system_site_packages() -> bool:
    """Comprueba si .venv fue creado con --system-site-packages."""
    cfg = venv_dir() / "pyvenv.cfg"
    if not cfg.is_file():
        return False
    return "include-system-site-packages = true" in cfg.read_text(encoding="utf-8")


def ensure_venv() -> Path:
    """Crea .venv una sola vez si no existe (Linux: --system-site-packages)."""
    path = venv_dir()
    if path.is_dir():
        if detect_os() == "linux" and not venv_has_system_site_packages():
            print("[kps] Recreando venv (faltaba --system-site-packages)...")
            shutil.rmtree(path)
        else:
            print(f"[kps] Entorno virtual existente: {path}")
            return path

    print(f"[kps] Creando entorno virtual en {path}...")
    cmd = [sys.executable, "-m", "venv", str(path)]
    if detect_os() == "linux":
        cmd.insert(3, "--system-site-packages")
    _run(cmd)
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


def _import_check_result() -> subprocess.CompletedProcess[str]:
    """Ejecuta la verificación de imports en el venv."""
    py = venv_python()
    code = {
        "linux": _VERIFY_LINUX,
        "windows": _VERIFY_WINDOWS,
        "macos": _VERIFY_MACOS,
    }[detect_os()]
    return subprocess.run(
        [str(py), "-c", code.strip()],
        capture_output=True,
        text=True,
        check=False,
    )


def _run_import_check() -> bool:
    """Comprueba imports en el venv sin imprimir mensajes."""
    if not venv_python().is_file():
        return False
    return _import_check_result().returncode == 0


def verify_imports() -> bool:
    """Comprueba que los imports principales funcionan en el venv."""
    if not venv_python().is_file():
        print("[kps] ERROR: no existe el intérprete del venv. Ejecuta la instalación primero.")
        return False

    print("[kps] Verificando imports principales...")
    result = _import_check_result()
    if result.returncode != 0:
        print("[kps] ERROR: falló la verificación de imports.")
        if result.stderr:
            print(result.stderr.strip())
        return False

    print("[kps] OK: imports verificados.")
    return True


def test_package() -> bool:
    """Comprueba que el entorno está listo para ejecutar kps."""
    return _run_import_check()


def is_in_uinput_group() -> bool:
    """Indica si el usuario actual pertenece al grupo uinput."""
    try:
        import grp  # pylint: disable=import-outside-toplevel
    except ModuleNotFoundError:
        return False
    try:
        uinput_gid = grp.getgrnam("uinput").gr_gid
    except KeyError:
        return False
    return uinput_gid in os.getgroups()


def describe_uinput_issue() -> str:
    """Mensaje de ayuda según el estado de /dev/uinput y el grupo uinput."""
    uinput_dev = Path("/dev/uinput")
    if not uinput_dev.exists():
        return (
            "El dispositivo /dev/uinput no existe. "
            "Ejecuta: sudo modprobe uinput (o ./scripts/install.sh)."
        )
    if can_access_uinput():
        return ""
    if is_in_uinput_group():
        return (
            "Perteneces al grupo uinput pero aún no tienes acceso efectivo. "
            "Cierra sesión y vuelve a entrar (o reinicia el equipo)."
        )
    return (
        "No tienes acceso a /dev/uinput. Ejecuta ./scripts/install.sh "
        "y cierra sesión tras unirte al grupo uinput."
    )


def verify_uinput_device(*, quiet: bool = False) -> bool:
    """Prueba abrir uinput y emitir un evento mínimo (sin sudo)."""
    if detect_os() != "linux":
        return True

    py = venv_python()
    if not py.is_file():
        return False

    if not quiet:
        print("[kps] Probando acceso uinput (sin sudo)...")
    result = subprocess.run(
        [str(py), "-c", _UINPUT_DEVICE_TEST.strip()],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        if not quiet:
            print("[kps] OK: uinput operativo sin sudo.")
        return True

    print("[kps] ERROR: uinput no operativo.")
    if result.stderr:
        print(result.stderr.strip())
    hint = describe_uinput_issue()
    if hint:
        print(f"[kps] {hint}")
    return False


def can_access_uinput() -> bool:
    """Comprueba acceso de lectura/escritura a /dev/uinput en Linux."""
    if detect_os() != "linux":
        return True
    uinput_dev = Path("/dev/uinput")
    if not uinput_dev.exists():
        return False
    return os.access(uinput_dev, os.R_OK | os.W_OK)


def verify_runtime() -> None:
    """Comprueba venv, imports (silencioso) y uinput antes de ejecutar kps."""
    if not venv_dir().is_dir():
        raise RuntimeError(
            "No hay entorno virtual (.venv). Ejecuta ./scripts/install.sh o ./run"
        )
    if not _run_import_check():
        raise RuntimeError("Los imports no están disponibles en el venv.")
    if detect_os() == "linux":
        issue = describe_uinput_issue()
        if issue:
            raise RuntimeError(issue)
        if not verify_uinput_device(quiet=True):
            raise RuntimeError(
                "No se pudo usar uinput sin sudo. "
                "Revisa permisos de /dev/uinput y el grupo uinput."
            )
    print("[kps] Entorno listo.")


def verify_setup() -> None:
    """Alias de verify_runtime (compatibilidad)."""
    verify_runtime()


def ensure_venv_runtime() -> None:
    """Re-ejecuta kps con el Python del venv si aún no lo usa."""
    vpy = venv_python()
    if not vpy.is_file():
        return
    if Path(sys.executable).resolve() == vpy.resolve():
        return
    print(f"[kps] Cambiando al intérprete del venv: {vpy}")
    os.execv(str(vpy), [str(vpy), *sys.argv])


def setup_environment() -> None:
    """Instala dependencias si faltan, verifica el entorno y activa el venv."""
    ensure_venv_runtime()
    if not venv_dir().is_dir() or not _run_import_check():
        autoinstall()
    verify_runtime()


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


Autoinstall = autoinstall  # compatibilidad con imports antiguos
