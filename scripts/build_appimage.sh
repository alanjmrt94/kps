#!/usr/bin/env bash
# Empaqueta kps como AppImage (Linux, usuario final sin Python/pip).
#
# Compatibilidad: se construye contra glibc 2.27 (Ubuntu 18.04) para correr
# en Ubuntu 18.04–26.04. Si el host tiene glibc más nuevo y hay Docker,
# el build se reejecuta dentro de ubuntu:18.04.
#
# Usa appimagetool moderno (runtime type-2 estático: sin libfuse2 en el host)
# e incrusta update info + .zsync para AppImageUpdate.
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
# Máximo glibc aceptable en el host de build (Ubuntu 18.04 = 2.27).
MAX_BUILD_GLIBC="2.27"
DOCKER_IMAGE="${KPS_APPIMAGE_DOCKER_IMAGE:-ubuntu:18.04}"
UPDATE_OWNER="${KPS_APPIMAGE_UPDATE_OWNER:-alanjmrt94}"
UPDATE_REPO="${KPS_APPIMAGE_UPDATE_REPO:-kps}"

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

host_glibc_version() {
    # Ej.: "ldd (Ubuntu GLIBC 2.27-3ubuntu1) 2.27" → 2.27
    ldd --version 2>/dev/null | head -n 1 | grep -oE '[0-9]+\.[0-9]+' | tail -n 1
}

version_gt() {
    # true si $1 > $2 (semver mayor.menor)
    local IFS=.
    # shellcheck disable=SC2206
    local a=($1) b=($2)
    local i
    for i in 0 1; do
        local ai=${a[i]:-0} bi=${b[i]:-0}
        if ((ai > bi)); then return 0; fi
        if ((ai < bi)); then return 1; fi
    done
    return 1
}

maybe_reexec_in_docker() {
    if [[ "${KPS_APPIMAGE_NATIVE:-}" == "1" || "${KPS_APPIMAGE_IN_DOCKER:-}" == "1" ]]; then
        return 0
    fi
    local glibc
    glibc="$(host_glibc_version || true)"
    if [[ -z "${glibc}" ]]; then
        warn_glibc_unknown
        return 0
    fi
    if ! version_gt "${glibc}" "${MAX_BUILD_GLIBC}"; then
        log "glibc del host: ${glibc} (OK ≤ ${MAX_BUILD_GLIBC})"
        return 0
    fi
    if ! command -v docker >/dev/null 2>&1; then
        die "Host glibc ${glibc} > ${MAX_BUILD_GLIBC}. Instala Docker o define KPS_APPIMAGE_NATIVE=1 (no correrá en Ubuntu 18.04)."
    fi
    log "Host glibc ${glibc} > ${MAX_BUILD_GLIBC}; reejecutando en ${DOCKER_IMAGE}..."
    mkdir -p "${DIST_DIR}" "${PROJECT_ROOT}/build"
    docker run --rm --network host \
        -e KPS_APPIMAGE_IN_DOCKER=1 \
        -e KPS_APPIMAGE_UPDATE_OWNER="${UPDATE_OWNER}" \
        -e KPS_APPIMAGE_UPDATE_REPO="${UPDATE_REPO}" \
        -v "${PROJECT_ROOT}:/src:ro" \
        -v "${DIST_DIR}:/out" \
        -v "${PROJECT_ROOT}/build:/build" \
        "${DOCKER_IMAGE}" \
        bash -lc "$(cat <<'EOS'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates wget curl \
    gcc g++ make pkg-config file binutils zsync xz-utils xvfb \
    libx11-dev libxss-dev libgtk-3-0 libgdk-pixbuf2.0-0 \
    libgirepository1.0-dev libcairo2-dev \
    >/dev/null
# appindicator: nombre clásico en 18.04; ayatana en distros más nuevas
apt-get install -y -qq libappindicator3-1 gir1.2-appindicator3-0.1 \
    >/dev/null 2>&1 \
    || apt-get install -y -qq libayatana-appindicator3-1 gir1.2-ayatanaappindicator3-0.1 \
    >/dev/null

# Python 3.10 portable (glibc antigua; deadsnakes ya no publica 3.10 en 18.04)
arch="$(uname -m)"
case "${arch}" in
  x86_64|amd64) arch=x86_64; py_triple=x86_64-unknown-linux-gnu ;;
  aarch64|arm64) arch=aarch64; py_triple=aarch64-unknown-linux-gnu ;;
  *) echo "arch no soportada: ${arch}" >&2; exit 1 ;;
esac
PY_VER="3.10.22"
PY_TAG="20261001"
PY_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PY_TAG}/cpython-${PY_VER}+${PY_TAG}-${py_triple}-install_only.tar.gz"
mkdir -p /opt
wget -q -O /tmp/python.tgz "${PY_URL}"
tar -xzf /tmp/python.tgz -C /opt
export PATH="/opt/python/bin:${PATH}"
# El Python portable trae CFLAGS de un gcc nuevo; el de 18.04 no los entiende.
export CC="${CC:-gcc}"
export CXX="${CXX:-g++}"
export CFLAGS="${CFLAGS:--O3 -fstack-protector -fPIC -fno-omit-frame-pointer}"
export CXXFLAGS="${CXXFLAGS:-${CFLAGS}}"
export LDFLAGS="${LDFLAGS:-}"
python3 --version

rm -rf /work
mkdir -p /work
cp -a /src/. /work/kps
cd /work/kps
rm -rf .venv dist build
ln -sfn /build build
mkdir -p dist
python3 -m venv .venv
# DISPLAY fake para que PyInstaller pueda importar pystray al empaquetar
Xvfb :99 -screen 0 1024x768x24 >/tmp/xvfb.log 2>&1 &
export DISPLAY=:99
bash scripts/build_appimage.sh
cp -a "dist/kps-${arch}.AppImage" /out/
# Recoger .zsync aunque appimagetool lo deje fuera de dist/
find . -maxdepth 3 -name "kps-${arch}.AppImage.zsync" -type f -exec cp -a {} /out/ \;
ls -la /out/
echo BUILD_OK
EOS
)"
    exit 0
}

warn_glibc_unknown() {
    log "AVISO: no se pudo detectar la glibc del host; se construye en nativo."
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
    # appimagetool moderno: embebe type2-runtime estático (sin libfuse2 en el destino)
    url="https://github.com/AppImage/appimagetool/releases/download/continuous/${tool_name}"

    mkdir -p "${TOOLS_DIR}"
    if [[ ! -x "${APPIMAGETOOL}" ]]; then
        log "Descargando ${tool_name} (AppImage/appimagetool)..."
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
    local req="${SCRIPT_DIR}/requirements-appimage.txt"
    log "Instalando PyInstaller y dependencias (incl. bandeja)..."
    "${VENV_DIR}/bin/pip" install -q --upgrade pip wheel setuptools
    "${VENV_DIR}/bin/pip" install -q pyinstaller
    "${VENV_DIR}/bin/pip" install -q -r "${req}"

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
    # AppImageHub busca kps.png en cualquier */128x128/* y guarda todas las
    # coincidencias en una sola variable. El árbol hicolor del bundle
    # (PyInstaller) duplica el de usr/share/icons y el test aborta en readlink.
    strip_bundled_hicolor "${bundle_dest}"

    # Sin argumentos → bandeja (AppImageHub lanza el AppImage sin flags).
    cat > "${APPDIR}/AppRun" <<'EOF'
#!/bin/sh
set -e
APPDIR="$(readlink -f "$(dirname "$0")")"
export APPDIR
export PATH="${APPDIR}/usr/lib/kps:${PATH}"
export LD_LIBRARY_PATH="${APPDIR}/usr/lib/kps${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
if [ "$#" -eq 0 ]; then
    set -- --tray
fi
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

    assert_single_catalog_icon
}

strip_bundled_hicolor() {
    local bundle_dest=$1
    local rel found=0
    for rel in \
        "_internal/assets/icons/linux/hicolor" \
        "assets/icons/linux/hicolor"
    do
        if [[ -d "${bundle_dest}/${rel}" ]]; then
            log "Quitando iconos hicolor del bundle (${rel})."
            rm -rf "${bundle_dest}/${rel}"
            found=1
        fi
    done
    if [[ "${found}" -eq 0 ]]; then
        log "AVISO: el bundle no traía árbol hicolor."
    fi
}

assert_single_catalog_icon() {
    local matches count
    matches="$(find "${APPDIR}" -name 'kps.png' -path '*/128x128/*' | sort)"
    count="$(printf '%s\n' "${matches}" | grep -c . || true)"
    if [[ "${count}" -ne 1 ]]; then
        die "AppImageHub exige un único kps.png en */128x128/* (hay ${count}):
${matches}"
    fi
    log "Icono de catálogo: ${matches}"
}

update_information() {
    local arch
    arch="$(detect_arch)"
    printf 'gh-releases-zsync|%s|%s|latest|kps-*%s.AppImage.zsync' \
        "${UPDATE_OWNER}" "${UPDATE_REPO}" "${arch}"
}

build_appimage() {
    local arch output update_info
    arch="$(detect_arch)"
    output="${DIST_DIR}/kps-${arch}.AppImage"
    update_info="$(update_information)"

    mkdir -p "${DIST_DIR}"
    rm -f "${output}" "${output}.zsync"
    log "Generando ${output}..."
    log "Update information: ${update_info}"
    if ! command -v zsyncmake >/dev/null 2>&1; then
        log "AVISO: zsyncmake no está instalado; appimagetool puede omitir el .zsync"
    fi
    ARCH="${arch}" APPIMAGE_EXTRACT_AND_RUN=1 \
        "${APPIMAGETOOL}" -u "${update_info}" "${APPDIR}" "${output}"
    chmod +x "${output}"
    log "Listo: ${output}"
    # appimagetool a veces deja el .zsync en el cwd, no junto al AppImage.
    collect_zsync_file "${output}"
}

collect_zsync_file() {
    local output=$1
    local name found
    name="$(basename "${output}").zsync"
    if [[ -f "${output}.zsync" ]]; then
        log "zsync: ${output}.zsync"
        return 0
    fi
    for found in \
        "${PROJECT_ROOT}/${name}" \
        "${PWD}/${name}" \
        "${DIST_DIR}/${name}" \
        "${APPIMAGE_DIR}/${name}"
    do
        if [[ -f "${found}" ]]; then
            mv -f "${found}" "${output}.zsync"
            log "zsync: ${output}.zsync (movido desde ${found})"
            return 0
        fi
    done
    found="$(find "${PROJECT_ROOT}" -maxdepth 3 -name "${name}" -type f -print -quit 2>/dev/null || true)"
    if [[ -n "${found}" ]]; then
        mv -f "${found}" "${output}.zsync"
        log "zsync: ${output}.zsync (movido desde ${found})"
        return 0
    fi
    log "AVISO: no se generó ${output}.zsync (instala el paquete zsync)"
}

print_usage() {
    log ""
    log "Cómo ejecutar (usuario final):"
    log "  ${DIST_DIR}/kps-$(detect_arch).AppImage          # bandeja (default)"
    log "  ${DIST_DIR}/kps-$(detect_arch).AppImage -h"
    log "  ./run-appimage -h"
    log ""
    log "Publicar también el .zsync junto al AppImage en GitHub Releases."
}

main() {
    require_linux
    maybe_reexec_in_docker
    ensure_venv
    warn_icons
    build_pyinstaller
    ensure_appimagetool
    assemble_appdir
    build_appimage
    print_usage
}

main "$@"
