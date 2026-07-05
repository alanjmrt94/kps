#!/usr/bin/env bash
# Correcciones automáticas (autopep8) + verificación pylint y mypy.
#
# Pylint no tiene modo --fix; autopep8 corrige estilo PEP 8 alineado con .pylintrc
# (max-line-length=100). Luego pylint y mypy igual que en CI.
#
# Uso:
#   ./scripts/lint.sh              # fix + pylint + mypy
#   ./scripts/lint.sh --fix        # solo autopep8
#   ./scripts/lint.sh --check      # solo pylint + mypy
#   ./scripts/lint.sh --help
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

MAX_LINE_LENGTH=100
DO_FIX=1
DO_CHECK=1

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { printf '%b[kps lint]%b %s\n' "${CYAN}" "${NC}" "$*" >&2; }
warn() { printf '%b[kps lint]%b %s\n' "${YELLOW}" "${NC}" "$*" >&2; }
err() { printf '%b[kps lint] ERROR:%b %s\n' "${RED}" "${NC}" "$*" >&2; }

usage() {
    cat <<'EOF'
Uso: ./scripts/lint.sh [opciones]

Opciones:
  (sin args)   autopep8 en todos los .py, luego pylint y mypy
  --fix        solo correcciones automáticas (autopep8)
  --check      solo pylint y mypy (sin modificar archivos)
  -h, --help   esta ayuda

Excluye: .venv/, build/, dist/, __pycache__/
EOF
}

parse_args() {
    case "${1:-}" in
        "" ) ;;
        --fix)
            DO_CHECK=0
            ;;
        --check)
            DO_FIX=0
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            err "Opción desconocida: ${1}"
            usage >&2
            exit 1
            ;;
    esac
}

python_bin() {
    if [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
        printf '%s' "${PROJECT_ROOT}/.venv/bin/python"
    else
        printf '%s' "python3"
    fi
}

ensure_tools() {
    local py pip
    py="$(python_bin)"
    pip="${py%python}pip"
    if [[ ! -x "${pip}" ]]; then
        pip="python3 -m pip"
    fi
    if [[ "${DO_FIX}" -eq 1 ]]; then
        "${pip}" install -q autopep8 2>/dev/null || "${py}" -m pip install -q autopep8
    fi
    if [[ "${DO_CHECK}" -eq 1 ]]; then
        "${pip}" install -q ".[dev]" 2>/dev/null || "${py}" -m pip install -q ".[dev]"
    fi
}

collect_py_files() {
  PY_FILES=()
  while IFS= read -r -d '' file; do
      PY_FILES+=("${file}")
  done < <(
      find "${PROJECT_ROOT}" -type f -name '*.py' \
          ! -path '*/.venv/*' \
          ! -path '*/build/*' \
          ! -path '*/dist/*' \
          ! -path '*/__pycache__/*' \
          -print0 | sort -z
  )
  if [[ ${#PY_FILES[@]} -eq 0 ]]; then
      err "No se encontraron archivos .py."
      exit 1
  fi
}

run_autopep8() {
    local py autopep8_bin
    py="$(python_bin)"
    autopep8_bin="${py%python}autopep8"
    if [[ ! -x "${autopep8_bin}" ]]; then
        autopep8_bin="${py}"
        autopep8_args=(-m autopep8)
    else
        autopep8_args=()
    fi
    log "autopep8 (${#PY_FILES[@]} archivos, max-line-length=${MAX_LINE_LENGTH})..."
    "${autopep8_bin}" "${autopep8_args[@]}" \
        --in-place \
        --max-line-length="${MAX_LINE_LENGTH}" \
        --aggressive \
        "${PY_FILES[@]}"
    log "autopep8 terminado."
}

run_pylint() {
    local py
    py="$(python_bin)"
    log "pylint (${#PY_FILES[@]} archivos)..."
    "${py}" -m pylint "${PY_FILES[@]}"
}

run_mypy() {
    local py
    py="$(python_bin)"
    log "mypy (pyproject.toml)..."
    "${py}" -m mypy
}

main() {
    parse_args "${1:-}"
    if [[ ! -f "${PROJECT_ROOT}/pyproject.toml" ]]; then
        err "Ejecuta desde el repositorio kps."
        exit 1
    fi
    ensure_tools
    collect_py_files
    log "Archivos Python: ${#PY_FILES[@]}"

    local status=0
    if [[ "${DO_FIX}" -eq 1 ]]; then
        run_autopep8
    fi
    if [[ "${DO_CHECK}" -eq 1 ]]; then
        run_pylint || status=1
        run_mypy || status=1
    fi

    if [[ "${status}" -eq 0 ]]; then
        log "OK."
    else
        err "Hay errores de lint o tipos."
    fi
    exit "${status}"
}

main "$@"
