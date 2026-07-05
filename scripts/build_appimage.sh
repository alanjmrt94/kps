#!/usr/bin/env bash
# Empaqueta kps como AppImage (Linux, usuario final sin Python/pip).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
SPEC="${SCRIPT_DIR}/kps-linux.spec"
APPIMAGE_DIR="${PROJECT_ROOT}/build/appimage"
APPDIR="${APPIMAGE_DIR}/kps.AppDir"
DIST_DIR="${PROJECT_ROOT}/dist"
TOOLS_DIR="${PROJECT_ROOT}/build/tools"
APPIMAGETOOL="${TOOLS_DIR}/appimagetool"
ICONS_ROOT="${PROJECT_ROOT}/assets/icons"

log() {
    printf '[kps build] %s\n' "$*"
}

die() {
    printf '[kps build] ERROR: %s\n' "$*" >&2
    exit 1
}

require_linux() {
    [[ "$(uname -s)" == "Linux" ]] || die "Este script solo aplica en Linux."
}

detect_arch() {
    local machine
    machine="$(uname -m)"
    case "${machine}" in
        x86_64 | amd64) echo "x86_64" ;;
        aarch64 | arm64) echo "aarch64" ;;
        *) die "Arquitectura no soportada para AppImage: ${machine}" ;;
    esac
}

ensure_venv() {
    if [[ ! -x "${VENV_DIR}/bin/python3" ]]; then
        die "No hay .venv. Ejecuta primero: ./scripts/install.sh o ./run"
    fi
}

warn_icons() {
    if [[ -x "${SCRIPT_DIR}/verify_icons.sh" ]]; then
        bash "${SCRIPT_DIR}/verify_icons.sh" || true
    fi
}

ensure_appimagetool() {
    local arch tool_name url
    arch="$(detect_arch)"
    tool_name="appimagetool-${arch}.AppImage"
    url="https://github.com/AppImage/AppImageKit/releases/download/continuous/${tool_name}"

    mkdir -p "${TOOLS_DIR}"
    if [[ ! -x "${APPIMAGETOOL}" ]]; then
        log "Descargando ${tool_name}..."
        if command -v wget >/dev/null 2>&1; then
            wget -q -O "${APPIMAGETOOL}" "${url}"
        elif command -v curl >/dev/null 2>&1; then
            curl -fsSL -o "${APPIMAGETOOL}" "${url}"
        else
            die "Se requiere wget o curl para descargar appimagetool."
        fi
        chmod +x "${APPIMAGETOOL}"
    fi
}

build_pyinstaller() {
    log "Instalando PyInstaller y dependencias..."
    "${VENV_DIR}/bin/pip" install -q --upgrade pip wheel setuptools
    "${VENV_DIR}/bin/pip" install -q pyinstaller
    "${VENV_DIR}/bin/pip" install -q -r "${SCRIPT_DIR}/requirements.txt"

    log "Compilando bundle onedir (dist/kps/)..."
    rm -rf "${PROJECT_ROOT}/dist/kps" "${PROJECT_ROOT}/build/kps"
    "${VENV_DIR}/bin/pyinstaller" "${SPEC}" --noconfirm --clean
    [[ -x "${DIST_DIR}/kps/kps" ]] || die "No se generó ${DIST_DIR}/kps/kps"
}

assemble_appdir() {
    local bundle_dest="${APPDIR}/usr/lib/kps"
    local app_png="${ICONS_ROOT}/linux/kps.png"
    local hicolor="${ICONS_ROOT}/linux/hicolor"
    local desktop="${SCRIPT_DIR}/appimage/io.github.alanjmrt94.kps.desktop"
    local appdata="${SCRIPT_DIR}/appimage/io.github.alanjmrt94.kps.appdata.xml"
    local desktop_id="io.github.alanjmrt94.kps.desktop"

    log "Montando AppDir en ${APPDIR}..."
    rm -rf "${APPDIR}"
    mkdir -p "${bundle_dest}" "${APPDIR}/usr/share/applications" "${APPDIR}/usr/share/metainfo"

    cp -a "${DIST_DIR}/kps/." "${bundle_dest}/"

    cat > "${APPDIR}/AppRun" <<'EOF'
#!/bin/sh
set -e
APPDIR="$(readlink -f "$(dirname "$0")")"
export APPDIR
export PATH="${APPDIR}/usr/lib/kps:${PATH}"
export LD_LIBRARY_PATH="${APPDIR}/usr/lib/kps:${LD_LIBRARY_PATH}"
exec "${APPDIR}/usr/lib/kps/kps" "$@"
EOF
    chmod +x "${APPDIR}/AppRun"

    cp "${desktop}" "${APPDIR}/${desktop_id}"
    cp "${desktop}" "${APPDIR}/usr/share/applications/${desktop_id}"
    cp "${appdata}" "${APPDIR}/usr/share/metainfo/io.github.alanjmrt94.kps.appdata.xml"

    if [[ -d "${hicolor}" ]] && find "${hicolor}" -name 'kps.png' -print -quit | grep -q .; then
        log "Instalando iconos hicolor en AppDir..."
        mkdir -p "${APPDIR}/usr/share/icons"
        cp -a "${hicolor}" "${APPDIR}/usr/share/icons/"
    else
        log "AVISO: sin assets/icons/linux/hicolor/**/kps.png"
    fi

    if [[ -f "${app_png}" ]]; then
        cp "${app_png}" "${APPDIR}/kps.png"
        cp "${app_png}" "${APPDIR}/.DirIcon"
        chmod 644 "${APPDIR}/.DirIcon"
        mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"
        cp "${app_png}" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/kps.png"
    else
        log "AVISO: falta assets/icons/linux/kps.png (256×256) para icono del AppImage."
    fi
}

build_appimage() {
    local arch output
    arch="$(detect_arch)"
    output="${DIST_DIR}/kps-${arch}.AppImage"

    mkdir -p "${DIST_DIR}"
    log "Generando ${output}..."
    ARCH="${arch}" APPIMAGE_EXTRACT_AND_RUN=1 "${APPIMAGETOOL}" "${APPDIR}" "${output}"
    chmod +x "${output}"
    log "Listo: ${output}"
}

print_usage() {
    log ""
    log "Cómo ejecutar (usuario final):"
    log "  ${DIST_DIR}/kps-$(detect_arch).AppImage -h"
    log "  ./run-appimage -h          (desde la raíz del proyecto; sin libfuse2)"
    log "  APPIMAGE_EXTRACT_AND_RUN=1 ./dist/kps-*.AppImage   (sin ./run-appimage)"
    log ""
    log "Iconos: coloca la suite en assets/icons/ (ver assets/icons/README.md)"
}

main() {
    require_linux
    ensure_venv
    warn_icons
    build_pyinstaller
    ensure_appimagetool
    assemble_appdir
    build_appimage
    print_usage
}

main "$@"
