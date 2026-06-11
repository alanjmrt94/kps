#!/usr/bin/env bash
# Instala y habilita kps como servicio systemd de usuario (Linux).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
UNIT_NAME="kps.service"
TEMPLATE="${SCRIPT_DIR}/kps-user.service"
USER_UNIT_DIR="${HOME}/.config/systemd/user"
VENV_PY="${PROJECT_ROOT}/.venv/bin/python3"
KPS_PY="${PROJECT_ROOT}/kps.py"

log() { printf '[kps systemd] %s\n' "$*"; }

if [[ "$(uname -s)" != "Linux" ]]; then
    log "ERROR: solo disponible en Linux."
    exit 1
fi

if [[ ! -x "${VENV_PY}" ]]; then
    log "ERROR: no existe ${VENV_PY}. Ejecuta ./run o ./scripts/install.sh primero."
    exit 1
fi

mkdir -p "${USER_UNIT_DIR}"
EXEC_START="${VENV_PY} ${KPS_PY}"
sed "s|@KPS_EXEC_START@|${EXEC_START}|g" "${TEMPLATE}" > "${USER_UNIT_DIR}/${UNIT_NAME}"

systemctl --user daemon-reload
systemctl --user enable "${UNIT_NAME}"
log "Servicio instalado en ${USER_UNIT_DIR}/${UNIT_NAME}"
log "Iniciar: systemctl --user start kps"
log "Estado:  systemctl --user status kps"
log "Logs:    journalctl --user -u kps -f"
