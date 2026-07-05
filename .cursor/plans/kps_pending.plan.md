---
name: kps — pendientes
overview: Estado del proyecto kps v2.0.1 — AppImage estable en Linux con CI; pendiente validación manual Win/macOS y PyPI.
todos:
  - id: fases-0-5
    content: "Fases 0–5 (v1.2–v1.7.2): instalación, multi-OS, UX, CI, tests"
    status: completed
  - id: v20-core
    content: "v2.0.0: D-Bus sin PyGObject, uinput ctypes, install.sh mínimo, --uninstall"
    status: completed
  - id: v20-bundle
    content: "v2.0.0: PyInstaller Win/macOS, AppImage Linux, is_bundled(), run-appimage"
    status: completed
  - id: v20-icons
    content: "v2.0.0: assets/icons, generate_icons, verify_icons, utils/icons.py"
    status: completed
  - id: v201-appimage
    content: "v2.0.1: AppStream, libfuse2 en run-appimage, verify bundled in-process"
    status: completed
  - id: ci-appimage
    content: "v2.0.1: job CI build-appimage (GitHub Actions + artefacto)"
    status: completed
  - id: test-win
    content: "Prueba manual Windows 10/11 (exe + idle + move)"
    status: pending
  - id: test-macos
    content: "Prueba manual macOS 12+ (.app + Accesibilidad)"
    status: pending
  - id: pypi
    content: "Publicación PyPI (opcional)"
    status: pending
isProject: true
---

# Plan kps — pendientes

> Última actualización: 2026-07-05 · Versión: **v2.0.1**

**Leyenda:** `OK` hecho y testeado · `PENDIENTE` falta hacer o probar

---

## Objetivo

Evitar inactividad del cursor (suspensión, bloqueo, Teams/Slack) en Linux, Windows y macOS.

| Objetivo | Estado |
|----------|--------|
| Instalación simple en Linux | OK |
| Linux X11 + Wayland | OK (Ubuntu MATE/Xfce + GNOME 26.04) |
| CI (lint, pytest, mypy, AppImage) | OK |
| Empaquetado usuario final | OK (scripts; falta probar artefactos Win/mac) |
| AppImage Linux en uso real | OK (v2.0.1) |
| Windows / macOS en uso real | PENDIENTE |

---

## v2.0.1 — parche AppImage

| Ítem | Estado |
|------|--------|
| AppStream `io.github.alanjmrt94.kps.appdata.xml` | OK |
| `run-appimage`: instalar `libfuse2` / fallback sin FUSE | OK |
| `verify_bundled_runtime()` in-process (`importlib`) | OK (tests) |
| AppImage dry-run + idle Wayland | OK |
| CI: job `build-appimage` → artefacto `kps-x86_64.AppImage` | OK |

---

## v2.0.0 — release mayor (cerrado)

| Ítem | Estado |
|------|--------|
| `utils/dbus_idle.py`, `utils/uinput_device.py` | OK |
| `install.sh` mínimo, `--uninstall` | OK |
| Bundled: `is_bundled()`, runner in-process | OK |
| `build_appimage.sh`, `run-appimage`, iconos | OK |
| ~211 tests, cobertura ~98% | OK |

---

## Iconos

| Archivo fuente | Notas |
|----------------|-------|
| `assets/image_base.png` | Cualquier tamaño cuadrado; el script genera 16…512, tray 64, AppImage 256 |
| `assets/image_base.icns` | ICNS exportado en macOS; se copia a `assets/icons/kps.icns` |

```bash
./scripts/generate_icons.sh
./scripts/verify_icons.sh
```

---

## Pruebas manuales

| Entorno | Estado |
|---------|--------|
| Linux X11 (MATE/Xfce) | OK |
| Linux Wayland + GNOME | OK (Ubuntu 26.04) |
| Linux `./run` en VM limpia | OK |
| Linux AppImage (`./run-appimage`) | OK (v2.0.1) |
| CI `build-appimage` (GitHub Actions) | OK |
| Windows 10/11 (`dist/kps.exe`) | PENDIENTE |
| macOS 12+ (`dist/kps.app`) | PENDIENTE |

---

## Pendiente

1. **PENDIENTE** — Prueba manual Windows: idle WinAPI + `move_win.py` + exe con icono.
2. **PENDIENTE** — Prueba manual macOS: Quartz + pyautogui + Accesibilidad + `.app`.
3. **PENDIENTE** — Publicación PyPI (`pip install kps`).

---

## Referencias

- `CHANGES.md`, `README.md`, `scripts/README.md`, `assets/icons/README.md`
- CI: `.github/workflows/ci.yml` (job `build-appimage`)
- Entry: `kps.py` → `utils/cli.py` → `utils/runner.py`

---

## Histórico (cerrado)

v1.2.0 → v2.0.0: consolidación, multiplataforma, UX, CI, empaquetado e iconos. Detalle en `CHANGES.md`.
