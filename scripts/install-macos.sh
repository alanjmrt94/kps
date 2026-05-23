#!/usr/bin/env bash
# Instala dependencias de Python para kps en macOS.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REQUIREMENTS="${SCRIPT_DIR}/requirements-macos.txt"
VENV_DIR="${PROJECT_ROOT}/.venv"

log() {
    printf '[kps install] %s\n' "$*"
}

die() {
    printf '[kps install] ERROR: %s\n' "$*" >&2
    exit 1
}

require_macos() {
    if [[ "$(uname -s)" != "Darwin" ]]; then
        die "Este script solo aplica en macOS."
    fi
}

find_python() {
    if command -v python3 >/dev/null 2>&1; then
        command -v python3
        return
    fi
    die "Se requiere python3. Instala Xcode CLI o Homebrew: brew install python3"
}

install_system_deps() {
    if ! command -v python3 >/dev/null 2>&1; then
        if command -v brew >/dev/null 2>&1; then
            log "Instalando python3 con Homebrew..."
            brew install python3
        else
            die "python3 no encontrado. Instala Homebrew o Xcode Command Line Tools."
        fi
    else
        log "python3 ya disponible."
    fi
}

ensure_venv() {
    local python_bin
    python_bin="$(find_python)"

    if [[ ! -d "${VENV_DIR}" ]]; then
        log "Creando entorno virtual en ${VENV_DIR}..."
        "${python_bin}" -m venv "${VENV_DIR}"
    else
        log "Usando entorno virtual existente en ${VENV_DIR}."
    fi

    log "Activando entorno virtual..."
    # shellcheck source=/dev/null
    source "${VENV_DIR}/bin/activate"
}

install_python_deps() {
    [[ -f "${REQUIREMENTS}" ]] || die "No se encontró ${REQUIREMENTS}."

    ensure_venv

    log "Actualizando pip..."
    python -m pip install --upgrade pip wheel setuptools

    log "Instalando dependencias desde ${REQUIREMENTS} (PyPI)..."
    python -m pip install -r "${REQUIREMENTS}"

    log "Verificando imports principales..."
    python - <<'PY'
import pyautogui
from Quartz import CGEventSourceSecondsSinceLastEventType
print("OK: pyautogui, Quartz")
PY
}

main() {
    require_macos

    log "Directorio del proyecto: ${PROJECT_ROOT}"

    install_system_deps
    install_python_deps

    log "Instalación completada."
    log "Ejecuta: ${VENV_DIR}/bin/python3 ${PROJECT_ROOT}/kps.py"
    log "O usa: ${PROJECT_ROOT}/run-macos"
}

main "$@"
