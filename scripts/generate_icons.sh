#!/usr/bin/env bash
# Genera la suite de iconos desde assets/image_base.png
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PY="${PROJECT_ROOT}/.venv/bin/python3"
SOURCE="${PROJECT_ROOT}/assets/image_base.png"

log() { printf '[kps icons] %s\n' "$*"; }
die() { printf '[kps icons] ERROR: %s\n' "$*" >&2; exit 1; }

usage() {
    cat <<EOF
Uso: $(basename "$0") [--source RUTA] [--skip-icns]

Genera en assets/icons/:
  kps.ico, kps.icns (si es posible), kps-tray.png,
  linux/kps.png, linux/hicolor/*/apps/kps.png

Imagen base por defecto: assets/image_base.png
ICNS opcional: assets/image_base.icns → assets/icons/kps.icns
Requiere: Pillow (pip install Pillow o ./scripts/install.sh)
EOF
}

main() {
    local extra_args=()

    while ((${#} > 0)); do
        case "$1" in
            -h | --help)
                usage
                exit 0
                ;;
            --source)
                [[ $# -ge 2 ]] || die "Falta valor para --source"
                SOURCE="$2"
                shift 2
                ;;
            --skip-icns)
                extra_args+=(--skip-icns)
                shift
                ;;
            *)
                die "Opción desconocida: $1 (usa --help)"
                ;;
        esac
    done

    [[ -f "${SOURCE}" ]] || die "No se encontró la imagen base: ${SOURCE}"

    if [[ ! -x "${VENV_PY}" ]]; then
        die "No hay .venv. Ejecuta ./scripts/install.sh o crea el venv primero."
    fi

    log "Instalando Pillow si falta..."
    "${VENV_PY}" -m pip install -q Pillow

    log "Generando iconos desde ${SOURCE}..."
    "${VENV_PY}" "${SCRIPT_DIR}/generate_icons.py" --source "${SOURCE}" "${extra_args[@]}"
}

main "$@"
