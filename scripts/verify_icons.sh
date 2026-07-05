#!/usr/bin/env bash
# Comprueba qué iconos de assets/icons están presentes.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICONS="${SCRIPT_DIR}/../assets/icons"

log() { printf '[kps icons] %s\n' "$*"; }
warn() { printf '[kps icons] AVISO: %s\n' "$*" >&2; }

check_file() {
    local label=$1
    local path=$2
    if [[ -f "${path}" ]]; then
        log "OK  ${label}: ${path#${ICONS}/}"
        return 0
    fi
    warn "FALTA ${label}: ${path#${ICONS}/}"
    return 1
}

missing=0

log "Verificando suite en ${ICONS}..."
echo

check_file "Windows (.exe)" "${ICONS}/kps.ico" || ((missing++)) || true
check_file "macOS (.app)" "${ICONS}/kps.icns" || ((missing++)) || true
check_file "Linux AppImage (256)" "${ICONS}/linux/kps.png" || ((missing++)) || true
check_file "Bandeja (--tray)" "${ICONS}/kps-tray.png" || ((missing++)) || true

for size in 16 32 48 64 128 256 512; do
    check_file "hicolor ${size}x${size}" \
        "${ICONS}/linux/hicolor/${size}x${size}/apps/kps.png" || ((missing++)) || true
done

echo
if ((missing == 0)); then
    log "Suite completa."
    exit 0
fi

log "${missing} archivo(s) pendiente(s). Ver assets/icons/README.md"
exit 0
