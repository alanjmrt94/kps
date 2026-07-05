#!/usr/bin/env python3
"""Genera la suite de iconos de kps desde assets/image_base.png."""

# pylint: disable=missing-function-docstring

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

# Tamaños estándar freedesktop + builds kps
HICOLOR_SIZES = (16, 32, 48, 64, 128, 256, 512)
ICO_SIZES = (16, 32, 48, 64, 128, 256)
ICNS_ICONSET_SIZES = (16, 32, 128, 256, 512)
TRAY_SIZE = 64
APPIMAGE_SIZE = 256


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_source() -> Path:
    return project_root() / "assets" / "image_base.png"


def default_icns_source() -> Path:
    return project_root() / "assets" / "image_base.icns"


def icons_dir() -> Path:
    return project_root() / "assets" / "icons"


def log(msg: str) -> None:
    print(f"[kps icons] {msg}")


def die(msg: str, code: int = 1) -> None:
    print(f"[kps icons] ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def load_source(path: Path) -> Image.Image:
    if not path.is_file():
        die(f"No se encontró la imagen base: {path}")
    try:
        image = Image.open(path).convert("RGBA")
    except OSError as error:
        die(f"No se pudo abrir {path}: {error}")
    log(f"Base: {path} ({image.width}×{image.height})")
    return image


def resize_icon(master: Image.Image, size: int) -> Image.Image:
    return master.resize((size, size), Image.Resampling.LANCZOS)


def write_png(image: Image.Image, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest, format="PNG", optimize=True)


def generate_hicolor(master: Image.Image, out: Path) -> None:
    log("Generando PNG hicolor...")
    for size in HICOLOR_SIZES:
        dest = out / "linux" / "hicolor" / f"{size}x{size}" / "apps" / "kps.png"
        write_png(resize_icon(master, size), dest)
        log(f"  OK {dest.relative_to(out)}")

    app_png = out / "linux" / "kps.png"
    write_png(resize_icon(master, APPIMAGE_SIZE), app_png)
    log(f"  OK {app_png.relative_to(out)}")

    tray_png = out / "kps-tray.png"
    write_png(resize_icon(master, TRAY_SIZE), tray_png)
    log(f"  OK {tray_png.relative_to(out)}")


def generate_ico(master: Image.Image, dest: Path) -> None:
    log("Generando kps.ico (Windows)...")
    images = [resize_icon(master, size) for size in ICO_SIZES]
    dest.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        dest,
        format="ICO",
        sizes=[img.size for img in images],
        append_images=images[1:],
    )
    log(f"  OK {dest.relative_to(icons_dir())}")


def _iconset_pngs(master: Image.Image, iconset: Path) -> None:
    iconset.mkdir(parents=True, exist_ok=True)
    for size in ICNS_ICONSET_SIZES:
        write_png(resize_icon(master, size), iconset / f"icon_{size}x{size}.png")
        write_png(resize_icon(master, size * 2), iconset / f"icon_{size}x{size}@2x.png")


def generate_icns_macos(master: Image.Image, dest: Path) -> bool:
    if sys.platform != "darwin" or not shutil.which("iconutil"):
        return False
    log("Generando kps.icns (macOS iconutil)...")
    with tempfile.TemporaryDirectory(prefix="kps-iconset-") as tmp:
        iconset = Path(tmp) / "kps.iconset"
        _iconset_pngs(master, iconset)
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(dest)],
            check=True,
        )
    log(f"  OK {dest.relative_to(icons_dir())}")
    return True


def generate_icns_magick(master: Image.Image, dest: Path) -> bool:
    magick = shutil.which("magick") or shutil.which("convert")
    if not magick:
        return False
    log("Generando kps.icns (ImageMagick)...")
    with tempfile.TemporaryDirectory(prefix="kps-iconset-") as tmp:
        iconset = Path(tmp) / "kps.iconset"
        _iconset_pngs(master, iconset)
        dest.parent.mkdir(parents=True, exist_ok=True)
        cmd = [magick]
        for png in sorted(iconset.glob("*.png")):
            cmd.append(str(png))
        cmd.append(str(dest))
        subprocess.run(cmd, check=True)
    log(f"  OK {dest.relative_to(icons_dir())}")
    return True


def install_icns_from_base(dest: Path, icns_source: Path | None = None) -> bool:
    """Copia assets/image_base.icns si existe (no requiere redimensionar manualmente)."""
    source = (icns_source or default_icns_source()).resolve()
    if not source.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    log(f"Copiado {source.name} → {dest.relative_to(icons_dir())}")
    return True


def generate_icns(master: Image.Image, dest: Path, icns_source: Path | None = None) -> None:
    if install_icns_from_base(dest, icns_source):
        return
    if generate_icns_macos(master, dest):
        return
    if generate_icns_magick(master, dest):
        return
    log(
        "AVISO: kps.icns no generado. Coloca assets/image_base.icns, "
        "ejecuta en macOS (iconutil) o instala ImageMagick con soporte ICNS."
    )


def archive_source(source: Path, out: Path) -> None:
    """Copia la base al árbol de iconos como referencia."""
    ref_dir = out / "source"
    ref_dir.mkdir(parents=True, exist_ok=True)
    ref = ref_dir / "kps-base.png"
    if source.resolve() != ref.resolve():
        shutil.copy2(source, ref)
        log(f"Copia de referencia: {ref.relative_to(out)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera iconos kps desde assets/image_base.png",
    )
    parser.add_argument(
        "-s",
        "--source",
        type=Path,
        default=default_source(),
        help="Imagen base PNG (default: assets/image_base.png)",
    )
    parser.add_argument(
        "--icns-source",
        type=Path,
        default=default_icns_source(),
        help="ICNS listo para macOS (default: assets/image_base.icns)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=icons_dir(),
        help="Directorio de salida (default: assets/icons)",
    )
    parser.add_argument(
        "--skip-icns",
        action="store_true",
        help="No intentar generar kps.icns",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    out = args.output.resolve()

    log(f"Salida: {out}")
    master = load_source(source)
    generate_hicolor(master, out)
    generate_ico(master, out / "kps.ico")
    if not args.skip_icns:
        generate_icns(master, out / "kps.icns", args.icns_source)
    archive_source(source, out)
    log("Listo. Verifica con: ./scripts/verify_icons.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
