# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para kps en Linux (onedir → AppImage).

from pathlib import Path

root = Path(SPEC).resolve().parent.parent
icons = root / "assets" / "icons"
icon_datas = []
if icons.is_dir() and any(
    p.suffix.lower() in {".png", ".ico", ".icns", ".svg"}
    for p in icons.rglob("*")
    if p.is_file()
):
    icon_datas = [(str(icons), "assets/icons")]

a = Analysis(
    [str(root / "kps.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "utils"), "utils"),
        (str(root / "config.example.toml"), "."),
        *icon_datas,
    ],
    hiddenimports=[
        "pynput",
        "pynput.keyboard",
        "pynput.keyboard._xorg",
        "pynput.keyboard._uinput",
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
