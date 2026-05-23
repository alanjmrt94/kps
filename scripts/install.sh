#!/usr/bin/env bash
# Instala dependencias de sistema y Python para kps en Linux (Debian/Ubuntu).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REQUIREMENTS="${SCRIPT_DIR}/requirements.txt"
LOCAL_UINPUT="${PROJECT_ROOT}/libs/python-uinput-1.0.1"
UDEV_RULES="${LOCAL_UINPUT}/udev-rules/40-uinput.rules"
VENV_DIR="${PROJECT_ROOT}/.venv"

APT_PACKAGES=(
    build-essential
    pkg-config
    python3
    python3-dev
    python3-pip
    python3-venv
    python3-gi
    python3-gi-cairo
    gir1.2-gtk-4.0
    gir1.2-gio-2.0
    gobject-introspection
    libgirepository1.0-dev
    libcairo2
    libcairo2-dev
    libxt-dev
    libx11-dev
    libxss-dev
    libudev-dev
)

log() {
    printf '[kps install] %s\n' "$*"
}

die() {
    printf '[kps install] ERROR: %s\n' "$*" >&2
    exit 1
}

require_linux() {
    if [[ "$(uname -s)" != "Linux" ]]; then
        die "Este script solo aplica en Linux."
    fi
}

require_apt() {
    command -v apt-get >/dev/null 2>&1 || die "Se requiere apt-get (Debian/Ubuntu)."
}

run_as_root() {
    if [[ "${EUID}" -eq 0 ]]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        die "Se necesitan permisos de root o sudo para instalar paquetes del sistema."
    fi
}

install_system_deps() {
    log "Actualizando índice de paquetes..."
    run_as_root apt-get update -qq

    log "Instalando dependencias del sistema..."
    run_as_root apt-get install -y --no-install-recommends "${APT_PACKAGES[@]}"
}

load_uinput_module() {
    if [[ ! -e /dev/uinput ]]; then
        log "Cargando módulo del kernel uinput..."
        run_as_root modprobe uinput || log "No se pudo cargar uinput; puede requerir reinicio o permisos extra."
    fi
}

setup_uinput_permissions() {
    if [[ ! -f "${UDEV_RULES}" ]]; then
        log "Regla udev no encontrada en ${UDEV_RULES}; se omite configuración de permisos."
        return
    fi

    local udev_dest="/etc/udev/rules.d/40-uinput.rules"
    if [[ ! -f "${udev_dest}" ]] || ! cmp -s "${UDEV_RULES}" "${udev_dest}"; then
        log "Instalando regla udev para /dev/uinput..."
        run_as_root cp "${UDEV_RULES}" "${udev_dest}"
        run_as_root udevadm control --reload-rules
        run_as_root udevadm trigger --subsystem-match=misc --action=add
    fi

    if ! getent group uinput >/dev/null 2>&1; then
        log "Creando grupo uinput..."
        run_as_root groupadd -r uinput
    fi

    local target_user="${SUDO_USER:-${USER}}"
    if [[ -n "${target_user}" ]] && id -nG "${target_user}" | grep -qw uinput; then
        log "El usuario ${target_user} ya pertenece al grupo uinput."
    elif [[ -n "${target_user}" ]]; then
        log "Agregando ${target_user} al grupo uinput (requiere cerrar sesión para aplicar)..."
        run_as_root usermod -aG uinput "${target_user}"
    fi
}

ensure_venv() {
    if [[ ! -d "${VENV_DIR}" ]]; then
        log "Creando entorno virtual en ${VENV_DIR}..."
        python3 -m venv "${VENV_DIR}"
    else
        log "Usando entorno virtual existente en ${VENV_DIR}."
    fi
}

install_python_uinput() {
  local pip="${VENV_DIR}/bin/pip"

  log "Instalando python-uinput desde PyPI..."
  if "${pip}" install "python-uinput>=0.11.2"; then
    return 0
  fi

  if [[ -d "${LOCAL_UINPUT}" ]]; then
    log "PyPI falló; instalando python-uinput local desde ${LOCAL_UINPUT}..."
    "${pip}" install "${LOCAL_UINPUT}"
    return 0
  fi

  die "No se pudo instalar python-uinput."
}

install_python_deps() {
    [[ -f "${REQUIREMENTS}" ]] || die "No se encontró ${REQUIREMENTS}."

    ensure_venv

    local pip="${VENV_DIR}/bin/pip"
    log "Actualizando pip..."
    "${pip}" install --upgrade pip wheel setuptools

    log "Instalando dependencias desde ${REQUIREMENTS}..."
    # python-uinput se instala aparte por el fallback local vendoreado.
    grep -Ev '^[[:space:]]*(#|$)|^python-uinput' "${REQUIREMENTS}" | "${pip}" install -r /dev/stdin

    install_python_uinput

    log "Verificando imports principales..."
    "${VENV_DIR}/bin/python3" - <<'PY'
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gio, GLib, GObject
import uinput
print("OK: gi, Gdk, Gio, uinput")
PY
}

main() {
    require_linux
    require_apt

    log "Directorio del proyecto: ${PROJECT_ROOT}"

    install_system_deps
    load_uinput_module
    setup_uinput_permissions
    install_python_deps

    log "Instalación completada."
    log "Ejecuta: ${VENV_DIR}/bin/python3 ${PROJECT_ROOT}/kps.py"
    if [[ -n "${SUDO_USER:-}" ]] || [[ -n "${USER:-}" ]]; then
        log "Si acabas de unirte al grupo uinput, cierra sesión y vuelve a entrar."
    fi
}

main "$@"
