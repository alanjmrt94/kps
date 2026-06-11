#!/usr/bin/env bash
# Instala dependencias de sistema y Python para kps en Linux (Debian/Ubuntu).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REQUIREMENTS="${SCRIPT_DIR}/requirements.txt"
UDEV_RULES="${SCRIPT_DIR}/udev-rules/40-uinput.rules"
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
    gir1.2-glib-2.0
    gir1.2-girepository-2.0-dev
    gobject-introspection
    libgirepository-2.0-dev
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

is_pkg_installed() {
    dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -q "install ok installed"
}

is_pkg_satisfied() {
    local pkg=$1

    if is_pkg_installed "${pkg}"; then
        return 0
    fi

    # En Ubuntu reciente GIO viene dentro del GIR de GLib
    if [[ "${pkg}" == "gir1.2-gio-2.0" ]] && is_pkg_installed "gir1.2-glib-2.0"; then
        return 0
    fi

    return 1
}

apt_pkg_exists() {
    apt-cache show "$1" &>/dev/null
}

install_system_deps() {
    local missing=()
    local pkg

    for pkg in "${APT_PACKAGES[@]}"; do
        if is_pkg_satisfied "${pkg}"; then
            continue
        fi
        if ! apt_pkg_exists "${pkg}"; then
            log "Aviso: el paquete ${pkg} no existe en apt; se omite."
            continue
        fi
        missing+=("${pkg}")
    done

    if ((${#missing[@]} == 0)); then
        log "Dependencias de Ubuntu/Debian ya instaladas."
        return
    fi

    log "Faltan ${#missing[@]} paquete(s) del sistema; instalando: ${missing[*]}"
    run_as_root apt-get update -qq
    run_as_root apt-get install -y --no-install-recommends "${missing[@]}"
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
    if [[ -d "${VENV_DIR}" ]]; then
        if [[ ! -f "${VENV_DIR}/pyvenv.cfg" ]] \
            || ! grep -q 'include-system-site-packages = true' "${VENV_DIR}/pyvenv.cfg"; then
            log "El venv existente no incluye paquetes del sistema; recreando ${VENV_DIR}..."
            rm -rf "${VENV_DIR}"
        else
            log "Usando entorno virtual existente en ${VENV_DIR}."
        fi
    fi

    if [[ ! -d "${VENV_DIR}" ]]; then
        log "Creando entorno virtual en ${VENV_DIR} (--system-site-packages)..."
        python3 -m venv --system-site-packages "${VENV_DIR}"
    fi

    if [[ ! -x "${VENV_DIR}/bin/python3" ]]; then
        die "No se encontró ${VENV_DIR}/bin/python3 tras crear el venv."
    fi

    log "Activando entorno virtual..."
    # shellcheck source=/dev/null
    source "${VENV_DIR}/bin/activate"
}

venv_python() {
    echo "${VENV_DIR}/bin/python3"
}

install_python_deps() {
    [[ -f "${REQUIREMENTS}" ]] || die "No se encontró ${REQUIREMENTS}."

    ensure_venv

    local py
    py="$(venv_python)"

    log "Actualizando pip..."
    "${py}" -m pip install -q --disable-pip-version-check --upgrade pip wheel setuptools

    log "Instalando dependencias pip desde ${REQUIREMENTS} (PyGObject/pycairo vía apt)..."
    "${py}" -m pip install -q --disable-pip-version-check -r "${REQUIREMENTS}"

    log "Verificando imports principales..."
    "${py}" - <<'PY'
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio
import uinput
print("OK: Gio, uinput")
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
    log "O usa: ${PROJECT_ROOT}/run"
    if [[ -n "${SUDO_USER:-}" ]] || [[ -n "${USER:-}" ]]; then
        log "Si acabas de unirte al grupo uinput, cierra sesión y vuelve a entrar."
    fi
}

main "$@"
