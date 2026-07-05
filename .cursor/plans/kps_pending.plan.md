---
name: kps — pendientes
overview: Estado del proyecto kps v2.0.5 — Linux, Windows listos; PyPI como kps-idle; pendiente validación manual macOS.
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
  - id: v202-quality
    content: "v2.0.2: docstrings, lint.sh, pylint 10/10"
    status: completed
  - id: v204-win-ci
    content: "v2.0.4: test-windows estable (helpers linux_uinput_modules, rutas bundled)"
    status: completed
  - id: test-win
    content: "Prueba manual Windows 10/11 (exe + idle + move)"
    status: completed
  - id: pypi
    content: "Publicación PyPI (pip install kps-idle)"
    status: completed
  - id: test-macos
    content: "Prueba manual macOS 12+ (.app + Accesibilidad)"
    status: pending
isProject: true
---

# Plan kps — pendientes

> Última actualización: 2026-07-05 · Versión: **v2.0.5**

**Leyenda:** `OK` hecho y testeado · `PENDIENTE` falta hacer o probar

---

## Objetivo

Evitar inactividad del cursor (suspensión, bloqueo, Teams/Slack) en Linux, Windows y macOS.

| Objetivo | Estado |
|----------|--------|
| Instalación simple en Linux | OK |
| Linux X11 + Wayland | OK (Ubuntu MATE/Xfce + GNOME 26.04) |
| CI (lint, pytest, mypy, AppImage, test-windows) | OK |
| Empaquetado usuario final | OK (Linux AppImage, Windows exe, macOS .app) |
| AppImage Linux en uso real | OK |
| Windows en uso real | OK (v2.0.4) |
| PyPI (`pip install kps-idle`) | listo para publicar v2.0.5 |
| macOS en uso real | PENDIENTE |

---

## v2.0.5 — PyPI kps-idle

| Ítem | Estado |
|------|--------|
| Rename PyPI `kps` → `kps-idle` (403 por nombre ocupado) | OK |
| `release.sh`: globs/URL PyPI dinámicos, fallo explícito twine | OK |
| Documentación `pip install kps-idle` | OK |
| Subida PyPI v2.0.5 | pendiente (`./scripts/release.sh` opción 2 o 4) |

---

## v2.0.4 — Windows y CI

| Ítem | Estado |
|------|--------|
| CI `test-windows` estable (mock `fcntl`, `linux_uinput_modules`) | OK |
| Rutas bundled con `Path.resolve()` en tests | OK |
| `tests/helpers.py` | OK |
| Publicación PyPI | movido a v2.0.5 (`kps-idle`) |
| Prueba manual Windows 10/11 (`kps.exe`) | OK |
| `release.sh` / `lint.sh` | OK (v2.0.2+) |

---

## v2.0.2 — calidad de código

| Ítem | Estado |
|------|--------|
| Docstrings en idle, tests, `generate_icons.py` | OK |
| `lint.sh` (autopep8 + pylint + mypy) | OK |
| Pylint 10/10 (41 archivos `.py`) | OK |

---

## v2.0.1 — parche AppImage

| Ítem | Estado |
|------|--------|
| AppStream `io.github.alanjmrt94.kps.appdata.xml` | OK |
| `run-appimage`: instalar `libfuse2` / fallback sin FUSE | OK |
| `verify_bundled_runtime()` in-process (`importlib`) | OK (tests) |
| CI: job `build-appimage` → artefacto `kps-x86_64.AppImage` | OK |

---

## v2.0.0 — release mayor (cerrado)

| Ítem | Estado |
|------|--------|
| `utils/dbus_idle.py`, `utils/uinput_device.py` | OK |
| `install.sh` mínimo, `--uninstall` | OK |
| Bundled: `is_bundled()`, runner in-process | OK |
| `build_appimage.sh`, `run-appimage`, iconos | OK |
| ~214 tests, cobertura ~96% | OK |

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
| Linux AppImage (`./run-appimage`) | OK |
| CI `build-appimage` + `test-windows` (GitHub Actions) | OK |
| Windows 10/11 (`dist/kps.exe`) | OK (v2.0.4) |
| macOS 12+ (`dist/kps.app`) | PENDIENTE |

---

## Pendiente

1. **PENDIENTE** — Prueba manual macOS: Quartz + pyautogui + Accesibilidad + `.app`.
2. **Opcional** — AppImageHub (PR vía `./scripts/release.sh appimagehub` tras GitHub Release).

---

## Referencias

- `CHANGES.md`, `README.md`, `scripts/README.md`, `assets/icons/README.md`
- CI: `.github/workflows/ci.yml`
- Publicación: `scripts/release.sh`
- PyPI: https://pypi.org/project/kps-idle/
- Entry: `kps.py` → `utils/cli.py` → `utils/runner.py`

---

## Histórico (cerrado)

v1.2.0 → v2.0.5: consolidación, multiplataforma, UX, CI, empaquetado, iconos, PyPI (kps-idle) y Windows. Detalle en `CHANGES.md`.
