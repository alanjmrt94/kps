# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para kps en Linux (onedir → AppImage).

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

root = Path(SPEC).resolve().parent.parent
icons = root / "assets" / "icons"
icon_datas = []
if icons.is_dir() and any(
    p.suffix.lower() in {".png", ".ico", ".icns", ".svg"}
    for p in icons.rglob("*")
    if p.is_file()
):
    icon_datas = [(str(icons), "assets/icons")]

tray_datas, tray_binaries, tray_hidden = collect_all("pystray")
pil_datas, pil_binaries, pil_hidden = collect_all("PIL")

a = Analysis(
    [str(root / "kps.py")],
    pathex=[str(root)],
    binaries=[*tray_binaries, *pil_binaries],
    datas=[
        (str(root / "utils"), "utils"),
        (str(root / "config.example.toml"), "."),
        *icon_datas,
        *tray_datas,
        *pil_datas,
    ],
    hiddenimports=[
        "pynput",
        "pynput.keyboard",
        "pynput.keyboard._xorg",
        "pynput.keyboard._uinput",
        "pystray",
        "pystray._appindicator",
        "pystray._util",
        "pystray._util.gtk",
        "pystray._util.notify_dbus",
        "PIL",
        "PIL.Image",
        *tray_hidden,
        *pil_hidden,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["gi", "gi.repository"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="kps",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="kps",
)
