#!/usr/bin/env bash
# Empaqueta kps.app con PyInstaller (macOS).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
SPEC="${SCRIPT_DIR}/kps-macos.spec"

log() {
    printf '[kps build] %s\n' "$*"
}

die() {
    printf '[kps build] ERROR: %s\n' "$*" >&2
    exit 1
}

require_macos() {
    [[ "$(uname -s)" == "Darwin" ]] || die "Este script solo aplica en macOS."
}

ensure_venv() {
    if [[ ! -x "${VENV_DIR}/bin/python3" ]]; then
        die "No hay .venv. Ejecuta primero: bash scripts/install-macos.sh"
    fi
}

main() {
    require_macos
    ensure_venv

    bash "${SCRIPT_DIR}/verify_icons.sh" 2>/dev/null || true

    log "Instalando PyInstaller y dependencias de build..."
    "${VENV_DIR}/bin/pip" install -q --upgrade pip wheel setuptools
    "${VENV_DIR}/bin/pip" install -q pyinstaller
    "${VENV_DIR}/bin/pip" install -q -r "${SCRIPT_DIR}/requirements-macos.txt"

    log "Compilando kps.app..."
    "${VENV_DIR}/bin/pyinstaller" "${SPEC}" --noconfirm --clean

    log "Listo: ${PROJECT_ROOT}/dist/kps.app"
    log "Ejecutar: open dist/kps.app"
    log "Nota: concede Accesibilidad en Ajustes → Privacidad si pyautogui lo solicita."
}

main "$@"
