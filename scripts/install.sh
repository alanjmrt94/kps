#!/usr/bin/env bash
# Instala dependencias de sistema y Python para kps en Linux (Debian/Ubuntu).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REQUIREMENTS="${SCRIPT_DIR}/requirements.txt"
UDEV_RULES="${SCRIPT_DIR}/udev-rules/40-uinput.rules"
VENV_DIR="${PROJECT_ROOT}/.venv"

# Runtime mínimo: Python, cliente D-Bus y libs X11 (solo si se usa XScreenSaver).
APT_PACKAGES=(
    python3
    python3-pip
    python3-venv
    libglib2.0-bin
    libx11-6
    libxss1
)

# No se desinstala python3 (suele ser dependencia del sistema).
APT_PACKAGES_UNINSTALL=(
    python3-pip
    python3-venv
    libglib2.0-bin
    libx11-6
    libxss1
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

apt_pkg_exists() {
    apt-cache show "$1" &>/dev/null
}

dbus_client_available() {
    command -v gdbus >/dev/null 2>&1 \
        || command -v busctl >/dev/null 2>&1 \
        || command -v dbus-send >/dev/null 2>&1
}

install_system_deps() {
    local missing=()
    local pkg

    for pkg in "${APT_PACKAGES[@]}"; do
        if is_pkg_installed "${pkg}"; then
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
    else
        log "Faltan ${#missing[@]} paquete(s) del sistema; instalando: ${missing[*]}"
        run_as_root apt-get update -qq
        run_as_root apt-get install -y --no-install-recommends "${missing[@]}"
    fi

    if dbus_client_available; then
        log "Cliente D-Bus disponible (gdbus/busctl/dbus-send)."
    else
        log "Aviso: no hay cliente D-Bus; idle en Wayland puede fallar."
    fi
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
        if [[ -f "${VENV_DIR}/pyvenv.cfg" ]] \
            && grep -q 'include-system-site-packages = true' "${VENV_DIR}/pyvenv.cfg"; then
            log "El venv usa paquetes del sistema (obsoleto); recreando ${VENV_DIR}..."
            rm -rf "${VENV_DIR}"
        else
            log "Usando entorno virtual existente en ${VENV_DIR}."
        fi
    fi

    if [[ ! -d "${VENV_DIR}" ]]; then
        log "Creando entorno virtual en ${VENV_DIR}..."
        python3 -m venv "${VENV_DIR}"
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

    log "Instalando dependencias pip desde ${REQUIREMENTS}..."
    "${py}" -m pip install -q --disable-pip-version-check -r "${REQUIREMENTS}"

    log "Verificando imports principales..."
    "${py}" - <<'PY'
from utils.dbus_idle import DBusIdleError
from utils.uinput_device import UInputDevice, REL_X
print("OK: dbus_idle, uinput_device")
PY
}

deactivate_venv() {
    if [[ -n "${VIRTUAL_ENV:-}" ]] && [[ "${VIRTUAL_ENV}" == "${VENV_DIR}" ]]; then
        log "Desactivando entorno virtual..."
        deactivate 2>/dev/null || true
    fi
}

remove_venv() {
    deactivate_venv
    if [[ -d "${VENV_DIR}" ]]; then
        log "Eliminando entorno virtual ${VENV_DIR}..."
        rm -rf "${VENV_DIR}"
        log "Entorno virtual eliminado."
    else
        log "No hay entorno virtual en ${VENV_DIR}."
    fi
}

confirm_action() {
    local assume_yes=$1
    local prompt=$2

    if [[ "${assume_yes}" == "true" ]]; then
        return 0
    fi

    printf '%s [y/N] ' "${prompt}"
    local answer
    read -r answer
    case "${answer}" in
        y | Y | yes | YES) return 0 ;;
        *) return 1 ;;
    esac
}

uninstall_system_deps() {
    local assume_yes=$1
    local mode=${2:-remove}
    local removable=()
    local pkg

    for pkg in "${APT_PACKAGES_UNINSTALL[@]}"; do
        if is_pkg_installed "${pkg}"; then
            removable+=("${pkg}")
        fi
    done

    if ((${#removable[@]} == 0)); then
        if [[ "${mode}" == "preview" ]]; then
            log "  - Paquetes apt: (ninguno instalado)"
        else
            log "No hay paquetes apt de kps instalados para desinstalar."
        fi
        return
    fi

    if [[ "${mode}" == "preview" ]]; then
        log "  - Paquetes apt: ${removable[*]}"
        return
    fi

    log "Desinstalando paquetes apt: ${removable[*]}"
    run_as_root apt-get remove -y --auto-remove "${removable[@]}"
    log "Paquetes apt desinstalados."
}

main_install() {
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

main_uninstall() {
    local assume_yes=false

    while ((${#} > 0)); do
        case "$1" in
            -y | --yes)
                assume_yes=true
                shift
                ;;
            -h | --help)
                cat <<'EOF'
Uso: install.sh --uninstall [-y|--yes]

  -y, --yes   No pedir confirmación interactiva
EOF
                exit 0
                ;;
            *)
                die "Opción desconocida en --uninstall: $1"
                ;;
        esac
    done

    require_linux
    require_apt

    log "Directorio del proyecto: ${PROJECT_ROOT}"
    log "Desinstalación de kps:"
    log "  - Eliminar ${VENV_DIR}"
    uninstall_system_deps "${assume_yes}" "preview"
    log "  - python3 no se desinstala (dependencia habitual del sistema)"
    log "  - La regla udev y el grupo uinput no se modifican"

    if ! confirm_action "${assume_yes}" "¿Continuar con la desinstalación?"; then
        log "Desinstalación cancelada."
        exit 0
    fi

    remove_venv
    uninstall_system_deps "true" "remove"

    log "Desinstalación completada."
}

usage() {
    cat <<'EOF'
Uso: install.sh [--uninstall [-y|--yes]]

  (sin args)     Instala dependencias de sistema y Python
  --uninstall    Elimina .venv y desinstala paquetes apt de kps (con confirmación)
  -y, --yes      Omitir confirmación (solo con --uninstall)
EOF
}

main() {
    case "${1:-}" in
        "")
            main_install
            ;;
        --uninstall)
            shift
            main_uninstall "$@"
            ;;
        -h | --help)
            usage
            ;;
        *)
            die "Opción desconocida: $1 (usa --help)"
            ;;
    esac
}

main "$@"
