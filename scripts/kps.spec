# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para kps en Windows.

from pathlib import Path

root = Path(SPEC).resolve().parent.parent
icons = root / "assets" / "icons"
win_icon = icons / "kps.ico"
icon_file = str(win_icon) if win_icon.is_file() else None

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
    hiddenimports=["pyautogui", "pynput", "pynput.keyboard._win32"],
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
    a.binaries,
    a.datas,
    [],
    name="kps",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
