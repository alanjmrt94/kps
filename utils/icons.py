"""Rutas y carga de iconos de kps (desarrollo y binario empaquetado)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

log = logging.getLogger("kps.icons")

ICON_NAME = "kps"
TRAY_ICON_NAME = "kps-tray.png"
LINUX_APP_ICON = "linux/kps.png"
HICOLOR_REL = "linux/hicolor"


def _is_bundled() -> bool:
    return bool(getattr(sys, "frozen", False))


def icons_dir() -> Path:
    """Directorio raíz de assets/icons."""
    if _is_bundled():
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return base / "assets" / "icons"
    return Path(__file__).resolve().parent.parent / "assets" / "icons"


def _resolve(relative: str) -> Path | None:
    path = icons_dir() / relative
    return path if path.is_file() else None


def windows_ico() -> Path | None:
    """Icono para kps.exe (Windows)."""
    return _resolve("kps.ico")


def macos_icns() -> Path | None:
    """Icono para kps.app (macOS)."""
    return _resolve("kps.icns")


def linux_appimage_png() -> Path | None:
    """PNG 256×256 para AppImage y .DirIcon."""
    return _resolve(LINUX_APP_ICON) or _resolve(f"{HICOLOR_REL}/256x256/apps/{ICON_NAME}.png")


def hicolor_tree() -> Path | None:
    """Árbol hicolor para empaquetado Linux."""
    path = icons_dir() / HICOLOR_REL
    if not path.is_dir():
        return None
    if any(path.rglob("*.png")):
        return path
    return None


def tray_icon_path() -> Path | None:
    """Icono de bandeja (--tray)."""
    return _resolve(TRAY_ICON_NAME) or _resolve(f"{HICOLOR_REL}/64x64/apps/{ICON_NAME}.png")


def _dev_icons_root() -> Path:
    """Ruta assets/icons en árbol de fuentes (build PyInstaller)."""
    return Path(__file__).resolve().parent.parent / "assets" / "icons"


def _has_image_assets(root: Path) -> bool:
    allowed = {".png", ".ico", ".icns", ".svg"}
    return any(p.suffix.lower() in allowed for p in root.rglob("*") if p.is_file())


def pyinstaller_icon_datas() -> list[tuple[str, str]]:
    """Entradas datas para incluir iconos en PyInstaller."""
    root = _dev_icons_root()
    if not root.is_dir() or not _has_image_assets(root):
        return []
    return [(str(root), "assets/icons")]


def load_tray_image():  # type: ignore[no-untyped-def]
    """Carga PIL.Image para pystray o None si no hay icono."""
    path = tray_icon_path()
    if path is None:
        log.debug("Sin icono de bandeja en assets/icons; se usa color plano.")
        return None
    try:
        from PIL import Image  # pylint: disable=import-outside-toplevel

        return Image.open(path).convert("RGBA")
    except OSError as error:
        log.warning("No se pudo cargar icono de bandeja %s: %s", path, error)
        return None
