# kps

<small>[GitHub](https://github.com/alanjmrt94/kps) · [PyPI — `kps-idle`](https://pypi.org/project/kps-idle/) · [Releases](https://github.com/alanjmrt94/kps/releases) · <a href="README-es.md"><img src="https://flagcdn.com/w20/ar.png" width="20" alt="Leer versión en Español" /> Leer en Español</a></small>

Keep moving the cursor if you are away to avoid inactivity.

## Features

* Supports **Windows**, **Linux** and **macOS**.
* On Linux, supports both **X11** and **Wayland**.
* **Auto-installs dependencies** via platform scripts and a virtualenv.
* Requires **Python 3.10+**.
* Scheduled **profiles**, tray status, mouse/keyboard/`both`/`inhibit` pulse, `kps doctor`, and AppImage autostart.

The program runs in the background. After idle time it can move the mouse, pulse a key, do both, or only inhibit OS sleep.

## Pulse modes

| Mode | CLI | Effect |
|------|-----|--------|
| `mouse` | (default) | Move the cursor |
| `keyboard` | `--keyboard-only` | Shift pulse only |
| `both` | `--keyboard` | Mouse and keyboard together |
| `inhibit` | `--inhibit-only` | Keep the OS awake (`systemd-inhibit` / `caffeinate` / `SetThreadExecutionState`); no input faking |

Profiles (`work`, `night`, …) live in `config.toml` under `[profiles.name]` with `pulse` and `start`/`end`. Outside the window, kps is **paused** (tray) and releases inhibit.

Tray tooltip: **active** / **away** / **paused**. Commands: `kps doctor`, `kps autostart enable|disable|status`.

## Latest changes

Release **v2.2.0** — inhibit-only:

* `--inhibit-only` / `--pulse inhibit` keeps the OS awake (no mouse/keyboard)
* Linux `systemd-inhibit`, macOS `caffeinate`, Windows `SetThreadExecutionState`

Release **v2.1.0** — profiles, tray, doctor, autostart:

* `--pulse mouse|keyboard|both|inhibit`; tray: active / away / paused
* `kps doctor` and `kps autostart enable` (AppImage via `$APPIMAGE`)

Release **v2.0.7** — AppImage for Ubuntu 18.04–26.04:

* Built against glibc 2.27 (Docker Ubuntu 18.04); static runtime (no `libfuse2`)
* AppImageUpdate (`.zsync`); tray by default; a single 128×128 icon

Release **v2.0.6** — AppImageHub catalog:

* A single `kps.png` at 128×128 inside the AppImage (no PyInstaller duplicate)

Release **v2.0.5** — PyPI `kps-idle`:

* PyPI package renamed to **`kps-idle`** (`pip install kps-idle`; CLI command `kps`)
* **`release.sh`**: artifacts and PyPI URL from `pyproject.toml`; explicit error if twine fails

Release **v2.0.4** — Windows CI and validation:

* Stable **`test-windows`** job (`linux_uinput_modules`, bundled paths via `Path.resolve()`)
* **Windows 10/11** verified manually (`kps.exe`, idle, movement)

Release **v2.0.2** — code quality:

* Docstrings in tests, `idle.py`, and `generate_icons.py`
* **`lint.sh`**: autopep8 plus pylint comment repair; pylint 10/10
* uinput tests compatible with Windows CI (`importlib`)

Release **v2.0.1** — AppImage patch:

* **AppStream** metadata in the AppImage (validated by `appimagetool`)
* **`run-appimage`**: prompts to install `libfuse2`; fallback without FUSE
* **CI:** `build-appimage` job on GitHub Actions (`kps-x86_64.AppImage` artifact)

Release **v2.0.0** — minimal deps, packaging, and icons:

* **Linux:** 6 apt packages (no PyGObject or `python-uinput`); D-Bus via `gdbus`/`busctl`; uinput via ctypes
* **Packaging:** `dist/kps.exe` (Win), `dist/kps.app` (macOS), `dist/kps-*.AppImage` (Linux); `./run-appimage`
* **Icons:** suite under `assets/icons/` from `image_base.png` / `image_base.icns`; tray `--tray`
* **Uninstall:** `./run --uninstall` or `./scripts/install.sh --uninstall`
* **In-process movement** — no subprocess; fixes Linux import failures

**Migrating from v1.7.x (Linux):** `./run --uninstall -y` (optional) then `./run`. Delete an old `.venv` if it used `--system-site-packages`. See [CHANGES.md](CHANGES.md#200).

Release **v1.7.2** — CI and mypy patch; Wayland + GNOME verified (Ubuntu 26.04).

Release **v1.7.0** — tray, systemd, optional keyboard, Unix hotkey, Windows PyInstaller.

See [CHANGES.md](CHANGES.md) for full release notes (Spanish).

## Compatibility

Tested or expected versions depending on the idle backend and mouse movement.

### Python

| Version | Status |
|---------|--------|
| 3.10 – 3.12 | Supported (primary target; Ubuntu 24.04) |
| 3.8 – 3.9 | Likely; not verified in CI |
| older than 3.8 | Not supported |

### Linux

**Distros with an install script:** Debian/Ubuntu (`scripts/install.sh`). Other distros: install `python3`, `libglib2.0-bin`, `libx11-6`, `libxss1`, uinput permissions, and `pip install pynput` yourself.

**Note:** kps **does not use GTK or PyGObject**. On Linux, idle is via **D-Bus** (`gdbus`/`busctl`) and, on X11, **XScreenSaver** (`libXss`). Mouse movement uses `/dev/uinput` (ctypes, no `python-uinput`).

| Desktop / environment | Typical session | Idle detection | Mouse movement |
|----------------------|-----------------|----------------|----------------|
| **GNOME** (Ubuntu, Fedora…) | Wayland | D-Bus `org.gnome.Mutter.IdleMonitor` (or freedesktop) — **tested on Ubuntu 26.04** | uinput |
| **GNOME** | X11 | D-Bus → XScreenSaver fallback | uinput |
| **Ubuntu MATE**, **Xfce**, **LXQt**, **Cinnamon** | X11 | XScreenSaver (`libXss`) | uinput |
| **KDE Plasma** | X11 | D-Bus freedesktop or XScreenSaver | uinput |
| **KDE Plasma** | Wayland | D-Bus freedesktop (if the compositor exposes it) | uinput |
| **i3**, **Openbox**, minimal WMs | X11 | XScreenSaver | uinput |

**Wayland without D-Bus idle** (e.g. experimental MATE on Wayland, some compositors): the monitor may be unavailable; use an **X11** session or a DE that exposes idle over D-Bus.

**Check on your machine:**

```bash
echo "$XDG_SESSION_TYPE"    # x11 or wayland
./run -v                    # logs which idle backend was chosen
```

### Windows

| Version | Idle detection | Movement |
|---------|----------------|----------|
| Windows 10 | `GetLastInputInfo` (WinAPI) | pyautogui |
| Windows 11 | Same | pyautogui |

Requirement: Python 3 on PATH (`python`).

### macOS

| Version | Idle detection | Movement |
|---------|----------------|----------|
| macOS 12+ (Monterey and later) | Quartz `CGEventSourceSecondsSinceLastEventType` | pyautogui |

Requirement: `python3`; **Accessibility** permission may be required for pyautogui (Settings → Privacy).

### Summary by platform

| Platform | Tested / target | Known limitations |
|----------|-----------------|-------------------|
| Ubuntu 22.04 / 24.04 / **26.04** + GNOME (Wayland) | **Yes** — Mutter D-Bus idle + uinput | Re-login after install (`uinput` group) |
| Ubuntu MATE (GTK3, X11) | Yes — XScreenSaver + uinput (v1.4.1) | MATE Wayland not verified |
| Windows 10/11 | **Yes** — WinAPI idle + pyautogui + `kps.exe` | F1–F12 hotkey on Windows only |
| macOS 12+ | Implemented | Accessibility; see [Open tasks](#open-tasks) |

## Quick start

Clone the repository:

    git clone https://github.com/alanjmrt94/kps
    cd kps

### Linux (Debian/Ubuntu)

Install and run in one step:

    ./run

Install only:

    ./scripts/install.sh

Then manually:

    source .venv/bin/activate
    python kps.py

### Windows

Double-click or from CMD/PowerShell:

    run.bat

Install only:

    scripts\install.bat

### macOS

    ./run-macos

Install only:

    ./scripts/install-macos.sh

## Manual usage

After installation:

    python3 kps.py

Use `-h` for options. Examples:

    python3 kps.py -t 10
    python3 kps.py -p 3 -v
    python3 kps.py -q
    python3 kps.py -n -t 5          # dry-run: probe idle without moving the mouse
    python3 kps.py -d --pid-file /tmp/kps.pid   # background (Linux)
    python3 kps.py --keyboard-only  # Shift only, no cursor movement
    python3 kps.py --keyboard       # mouse and keyboard in parallel
    python3 kps.py --inhibit-only   # OS idle/sleep inhibit only
    python3 kps.py --profile work
    python3 kps.py doctor
    python3 kps.py autostart enable

### Config file

Copy `config.example.toml` to `~/.config/kps/config.toml` (Linux) or `%APPDATA%\kps\config.toml` (Windows).
The CLI overrides the file. Example profiles: `[profiles.work]`, `[profiles.night]`.

```toml
[kps]
pulse = "mouse"          # mouse | keyboard | both | inhibit
profile = "work"

[profiles.work]
pulse = "both"
start = "09:00"
end = "18:00"
```

    mkdir -p ~/.config/kps
    cp config.example.toml ~/.config/kps/config.toml

Autostart (Linux, useful with the AppImage):

    kps autostart enable    # ~/.config/autostart + systemd --user
    kps autostart status
    kps autostart disable

Diagnose the environment (uinput, D-Bus idle, inhibit tool, AppImage signature):

    kps doctor

Stop the daemon on Linux:

    kill -USR1 $(cat /tmp/kps.pid)
    # or
    kill -TERM $(cat /tmp/kps.pid)

## Installation details

| Platform | Install script | pip requirements | Launcher |
|----------|----------------|------------------|----------|
| Linux | `scripts/install.sh` | `scripts/requirements.txt` | `run` |
| Windows | `scripts/install.bat` | `scripts/requirements-windows.txt` | `run.bat` |
| macOS | `scripts/install-macos.sh` | `scripts/requirements-macos.txt` | `run-macos` |

### Linux system packages (minimum)

`install.sh` installs **only if missing** (6 apt packages):

* `python3`, `python3-pip`, `python3-venv`
* `libglib2.0-bin` — D-Bus client (`gdbus`) for idle on Wayland/GNOME
* `libx11-6`, `libxss1` — XScreenSaver fallback on X11

It also configures `/dev/uinput` via udev (`scripts/udev-rules/40-uinput.rules`). **No** PyGObject, build-essential, or `-dev` packages.

### Packaging (end users, no Python install)

| Platform | Build | Output | Required icon |
|----------|-------|--------|---------------|
| Windows | `scripts\build_windows.bat` | `dist\kps.exe` | `assets/icons/kps.ico` |
| macOS | `bash scripts/build_macos.sh` | `dist/kps.app` | `assets/icons/kps.icns` |
| Linux | `./scripts/build_appimage.sh` | `dist/kps-*.AppImage` (+ `.zsync`) | `assets/icons/linux/kps.png` + `hicolor/` |

**Icon suite:** already under `assets/icons/`. Check with `./scripts/verify_icons.sh`.

**Development** (venv): `./run` · **AppImage** (no Python): `./run-appimage` or `./dist/kps-*.AppImage`

The AppImage is built on Ubuntu 18.04 (glibc 2.27) via Docker when the host is newer, covering Ubuntu 18.04–26.04. It includes a static runtime (no `libfuse2`) and, when published, a `.zsync` for AppImageUpdate.

**GPG signature:** the build signs the AppImage with the project key if it is in the local keyring (`KPS_GPG_KEY_ID`, default `73140C59FF3EBE5D`). To skip: `KPS_APPIMAGE_SIGN=0`.

```bash
# Verify a downloaded AppImage (do not set APPIMAGE_EXTRACT_AND_RUN)
./kps-x86_64.AppImage --appimage-signature

# Import the repo public key
gpg --import keys/kps-signing-key.asc
# Fingerprint: 5077A813F9AE818752168EA173140C59FF3EBE5D
# Key ID: 73140C59FF3EBE5D
# https://keys.openpgp.org
```

After `install.bat` / `install-macos.sh` / `install.sh`, run your platform build script. On macOS, **Accessibility** may be required for `pyautogui`. On Linux the AppImage still needs **gdbus** and **uinput** permissions on the host (see below).

### Python dependencies (pip)

**Linux** (`scripts/requirements.txt`):

* `pynput` (+ `wheel`, `setuptools`)
* D-Bus idle and uinput are **internal modules** (`utils/dbus_idle.py`, `utils/uinput_device.py`)

**Windows** (`scripts/requirements-windows.txt`):

* `pyautogui`, `pynput`

**macOS** (`scripts/requirements-macos.txt`):

* `pyautogui`, `pynput`, `pyobjc-framework-Quartz`

All Python packages are installed from **PyPI** into `.venv` at the project root (`pip install kps-idle` is also available; the command is still `kps`).

### Linux: uinput permissions (no sudo at runtime)

kps moves the cursor via `/dev/uinput`. **sudo is not used at runtime.**

1. Run `./scripts/install.sh` (or `./run`). The script:
   - loads the `uinput` kernel module
   - installs the udev rule in `/etc/udev/rules.d/40-uinput.rules`
   - adds your user to the `uinput` group
2. **Log out and back in** (or reboot) so the group takes effect.
3. Verify access:

       ls -l /dev/uinput
       groups

   You should see the `uinput` group and `crw-rw----` permissions with group `uinput`.

4. On start, `kps.py` checks imports and opens uinput **without sudo**. If that fails, it prints the next step.

**udev rule** (`scripts/udev-rules/40-uinput.rules`):

    SUBSYSTEM=="misc", KERNEL=="uinput", MODE="0660", GROUP="uinput"

## Development

Editable install with dev dependencies:

    pip install -e ".[dev]"

Tests and lint:

    pytest          # coverage ≥ 95% on Linux CI (~296 tests)
    pylint kps.py utils/*.py tests/*.py

GitHub CI runs the same checks on every push/PR to `main`/`master`: `lint`, `mypy`, `test-linux` (3.10–3.12), `test-windows`, and **`build-appimage`** (downloadable artifact).

Install as a global command (after `pip install .`):

    kps -h

## Project layout (install/run)

```
kps/
├── README.md              # English docs
├── README-es.md           # Spanish docs
├── CHANGES.md             # Release notes (Spanish)
├── config.example.toml    # Sample profiles (work / night)
├── run                    # Linux: install + run
├── run-appimage           # Linux: run AppImage in dist/
├── run.bat                # Windows: install + run
├── run-macos              # macOS: install + run
├── kps.py                 # Main program
├── assets/
│   ├── image_base.png     # Icon source (PNG)
│   ├── image_base.icns    # Icon source (macOS, optional)
│   └── icons/             # Generated suite (ICO, ICNS, hicolor, tray)
├── scripts/
│   ├── install.sh         # Linux install / --uninstall
│   ├── install.bat        # Windows install
│   ├── install-macos.sh   # macOS install
│   ├── build_appimage.sh  # Linux AppImage
│   ├── build_macos.sh     # macOS .app
│   ├── build_windows.bat  # Windows .exe
│   ├── kps.spec           # PyInstaller Windows
│   ├── kps-macos.spec     # PyInstaller macOS
│   ├── kps-linux.spec     # PyInstaller Linux (AppImage)
│   ├── verify_icons.sh    # Verify icons before packaging
│   ├── requirements*.txt
│   └── udev-rules/
│       └── 40-uinput.rules
├── keys/
│   └── kps-signing-key.asc  # GPG public key (AppImage / commits)
└── utils/                 # Core (cli, runner, inhibit, doctor, tray, …)
```

**v2.2.0** — `--inhibit-only`. **v2.1.0** — profiles, tray, doctor, autostart, bilingual docs.

## Open tasks

Work still needed after v2.2.0:

* **macOS 12+ validation** — run `dist/kps.app` (or `./run-macos`): Quartz idle, pyautogui, and **Accessibility** (Settings → Privacy).
* **Apple notarization** of the `.app` (`codesign` / `notarytool`; Apple Developer account). The Linux AppImage is already GPG-signed at build time.

If you can do the macOS validation, please open a [pull request](https://github.com/alanjmrt94/kps/pulls) with what you tested (OS version, idle backend, movement, Accessibility) so we can mark it confirmed.

## Older releases

Release v1.1.6:

* Auto install dependencies depending on OS platform and Python version
* Add version utilities
* Fix strings and typos
* Show kps version
