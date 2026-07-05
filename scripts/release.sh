#!/usr/bin/env bash
# Menú de publicación: GitHub Release, PyPI, AppImage y AppImageHub.
#
# Canales para kps:
#   1. GitHub Releases — binarios (AppImage) y notas de versión (principal)
#   2. PyPI — pip install kps (código + entry point; deps de plataforma vía install)
#   3. AppImage — adjunto al GitHub Release
#   4. AppImageHub — catálogo en https://github.com/AppImage/appimage.github.io
#      (PR con un archivo en data/; inspección automática en GitHub Actions)
#
# Uso: ./scripts/release.sh [appimagehub|github|pypi|appimage|all|verify]
#
# Variables de entorno:
#   PYPI_API_TOKEN  — token de PyPI (usuario twine: __token__)
#   TWINE_USERNAME / TWINE_PASSWORD — alternativa a PYPI_API_TOKEN
#   KPS_SKIP_TESTS=1 — no ejecutar pytest antes de publicar (opción "todo")
#   KPS_GITHUB_REPO — URL del repo (por defecto: gh repo view o alanjmrt94/kps)
#   KPS_APPIMAGEHUB_DATA — nombre del archivo en data/ (por defecto: kps)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

APPIMAGEHUB_UPSTREAM="AppImage/appimage.github.io"
APPIMAGEHUB_WORKDIR="${PROJECT_ROOT}/build/appimagehub-work"
APPIMAGEHUB_DATA_TEMPLATE="${SCRIPT_DIR}/appimage/appimagehub.data"
APPIMAGEHUB_DATA_NAME="${KPS_APPIMAGEHUB_DATA:-kps}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { printf '%b[kps release]%b %s\n' "${CYAN}" "${NC}" "$*" >&2; }
warn() { printf '%b[kps release]%b %s\n' "${YELLOW}" "${NC}" "$*" >&2; }
err() { printf '%b[kps release] ERROR:%b %s\n' "${RED}" "${NC}" "$*" >&2; }

confirm() {
    local prompt=$1
    local answer
    read -r -p "${prompt} [s/N]: " answer
    [[ "${answer}" =~ ^[sSyY]$ ]]
}

get_version() {
    grep -E '^Version = ' utils/const.py | sed -E 's/.*"([^"]+)".*/\1/'
}

get_pyproject_version() {
    grep -E '^version = ' pyproject.toml | sed -E 's/.*"([^"]+)".*/\1/'
}

check_versions_sync() {
    local v_const v_toml
    v_const="$(get_version)"
    v_toml="$(get_pyproject_version)"
    if [[ "${v_const}" != "${v_toml}" ]]; then
        err "Versión distinta: utils/const.py=${v_const}, pyproject.toml=${v_toml}"
        return 1
    fi
    printf '%s' "${v_const}"
}

extract_release_notes() {
    local version=$1
    local tmp
    tmp="$(mktemp)"
    awk -v ver="${version}" '
        $0 == "## " ver { found=1; next }
        found && /^---$/ { exit }
        found { print }
    ' CHANGES.md > "${tmp}"
    if [[ ! -s "${tmp}" ]]; then
        rm -f "${tmp}"
        err "No hay notas en CHANGES.md para la versión ${version} (sección ## ${version})"
        return 1
    fi
    cat "${tmp}"
    rm -f "${tmp}"
}

check_gh() {
    if ! command -v gh >/dev/null 2>&1; then
        err "Falta gh (GitHub CLI). Instálalo: https://cli.github.com/"
        return 1
    fi
    if ! gh auth status >/dev/null 2>&1; then
        err "gh no está autenticado. Ejecuta: gh auth login"
        return 1
    fi
    return 0
}

github_repo_url() {
    if [[ -n "${KPS_GITHUB_REPO:-}" ]]; then
        printf '%s' "${KPS_GITHUB_REPO}"
        return 0
    fi
    if check_gh 2>/dev/null; then
        gh repo view --json url -q .url 2>/dev/null && return 0
    fi
    printf '%s' "https://github.com/alanjmrt94/kps"
}

github_release_has_appimage() {
    local tag=$1
    gh release view "${tag}" --json assets -q '.assets[].name' 2>/dev/null | grep -qi '\.AppImage'
}

appimagehub_entry_exists_upstream() {
    gh api "repos/${APPIMAGEHUB_UPSTREAM}/contents/data/${APPIMAGEHUB_DATA_NAME}" >/dev/null 2>&1
}

appimagehub_fetch_upstream_content() {
    gh api "repos/${APPIMAGEHUB_UPSTREAM}/contents/data/${APPIMAGEHUB_DATA_NAME}" -q .content \
        | tr -d '\n' | base64 -d 2>/dev/null
}

appimagehub_build_data_content() {
    local mode=$1
    local repo_url content
    repo_url="$(github_repo_url)"
    if [[ "${mode}" == "new" ]]; then
        if [[ -f "${APPIMAGEHUB_DATA_TEMPLATE}" ]]; then
            cat "${APPIMAGEHUB_DATA_TEMPLATE}"
            return 0
        fi
        printf '%s\n' "${repo_url}"
        return 0
    fi
    content="$(appimagehub_fetch_upstream_content)"
    if [[ -z "${content}" ]]; then
        err "No se pudo leer data/${APPIMAGEHUB_DATA_NAME} en ${APPIMAGEHUB_UPSTREAM}."
        return 1
    fi
    if grep -qE '^#[[:space:]]*$' <<< "${content}"; then
        grep -vE '^#[[:space:]]*$' <<< "${content}"
    else
        printf '%s\n#' "${content}"
    fi
}

appimagehub_ensure_fork() {
    local fork_owner upstream_repo
    fork_owner="$(gh api user -q .login)"
    upstream_repo="${APPIMAGEHUB_UPSTREAM##*/}"
    if ! gh repo view "${fork_owner}/${upstream_repo}" >/dev/null 2>&1; then
        log "Creando fork ${fork_owner}/${upstream_repo}..."
        gh repo fork "${APPIMAGEHUB_UPSTREAM}" --clone=false >/dev/null
    fi
    printf '%s' "${fork_owner}"
}

appimagehub_prepare_worktree() {
    local fork_owner branch=$1
    fork_owner="$(appimagehub_ensure_fork)"
    rm -rf "${APPIMAGEHUB_WORKDIR}"
    git clone --depth 1 "https://github.com/${fork_owner}/appimage.github.io.git" "${APPIMAGEHUB_WORKDIR}"
    cd "${APPIMAGEHUB_WORKDIR}"
    git remote add upstream "https://github.com/${APPIMAGEHUB_UPSTREAM}.git" 2>/dev/null || true
    git fetch --depth 1 upstream master
    git checkout -B "${branch}" FETCH_HEAD
    cd "${PROJECT_ROOT}"
}

submit_appimagehub_pr() {
    local mode=$1
    local fork_owner branch pr_title pr_body data_file content pr_url tag
    check_gh || return 1
    VERSION="$(check_versions_sync || get_version)"
    tag="v${VERSION}"

    if ! github_release_has_appimage "${tag}"; then
        warn "El release ${tag} no tiene un .AppImage adjunto."
        warn "AppImageHub descarga el binario con wget; la inspección fallará sin release público."
        if ! confirm "¿Continuar con el PR a AppImageHub?"; then
            return 1
        fi
    fi

    case "${mode}" in
        new)
            branch="add-${APPIMAGEHUB_DATA_NAME}"
            pr_title="Add ${APPIMAGEHUB_DATA_NAME}"
            pr_body="$(cat <<EOF
Add kps to the AppImage catalog.

Repository: $(github_repo_url)
Release: $(github_repo_url)/releases/tag/${tag}

The AppImage is attached to GitHub Releases as \`kps-x86_64.AppImage\`.
EOF
)"
            ;;
        refresh)
            if ! appimagehub_entry_exists_upstream; then
                err "No hay entrada en AppImageHub; usa modo alta nueva."
                return 1
            fi
            branch="refresh-${APPIMAGEHUB_DATA_NAME}-${VERSION}"
            pr_title="Update ${APPIMAGEHUB_DATA_NAME} (re-inspect)"
            pr_body="$(cat <<EOF
Trigger re-inspection for kps (metadata / AppImage update).

Repository: $(github_repo_url)
Release: $(github_repo_url)/releases/tag/${tag}

Per AppImageHub docs, a \`#\` line toggles catalog refresh when the URL is unchanged.
EOF
)"
            ;;
        *)
            err "Modo AppImageHub desconocido: ${mode}"
            return 1
            ;;
    esac

    content="$(appimagehub_build_data_content "${mode}")" || return 1
    appimagehub_prepare_worktree "${branch}" || return 1
    data_file="${APPIMAGEHUB_WORKDIR}/data/${APPIMAGEHUB_DATA_NAME}"
    mkdir -p "$(dirname "${data_file}")"
    printf '%s' "${content}" > "${data_file}"
    if [[ "${content}" != *$'\n' ]] && [[ -n "${content}" ]]; then
        printf '\n' >> "${data_file}"
    fi

    fork_owner="$(gh api user -q .login)"
    (
        cd "${APPIMAGEHUB_WORKDIR}"
        git add "data/${APPIMAGEHUB_DATA_NAME}"
        if git diff --cached --quiet; then
            err "Sin cambios respecto a upstream; no hay PR que enviar."
            exit 1
        fi
        git -c user.name="$(gh api user -q .name 2>/dev/null || echo kps-release)" \
            -c user.email="$(gh api user -q .email 2>/dev/null || echo "${fork_owner}@users.noreply.github.com")" \
            commit -m "${pr_title}"
        git push -u origin "${branch}" --force
    ) || return 1

    if gh pr list --repo "${APPIMAGEHUB_UPSTREAM}" --head "${fork_owner}:${branch}" --state open -q .number | grep -q .; then
        pr_url="$(gh pr list --repo "${APPIMAGEHUB_UPSTREAM}" --head "${fork_owner}:${branch}" --state open --json url -q '.[0].url')"
        log "PR abierto existente: ${pr_url}"
        return 0
    fi

    pr_url="$(gh pr create \
        --repo "${APPIMAGEHUB_UPSTREAM}" \
        --head "${fork_owner}:${branch}" \
        --base master \
        --title "${pr_title}" \
        --body "${pr_body}")"
    log "PR AppImageHub creado: ${pr_url}"
    log "Revisa el check de GitHub Actions en el PR (debe quedar verde)."
    log "Catálogo: https://appimage.github.io/${APPIMAGEHUB_DATA_NAME}/"
}

action_appimagehub() {
    check_versions_sync || return 1
    VERSION="$(get_version)"
    log "AppImageHub — versión ${VERSION}"
    local mode="new"
    if appimagehub_entry_exists_upstream; then
        echo ""
        echo "  a) Alta nueva (sobrescribe data/${APPIMAGEHUB_DATA_NAME} en tu fork)"
        echo "  r) Actualizar / re-inspeccionar (toggle línea #)"
        echo "  c) Cancelar"
        echo ""
        read -r -p "Modo [a/r/c]: " hub_choice
        case "${hub_choice}" in
            a|A) mode="new" ;;
            r|R) mode="refresh" ;;
            *) log "Cancelado."; return 0 ;;
        esac
    else
        log "Primera alta en AppImageHub (data/${APPIMAGEHUB_DATA_NAME})."
        log "URL: $(github_repo_url)"
        if ! confirm "¿Crear PR en ${APPIMAGEHUB_UPSTREAM}?"; then
            return 0
        fi
    fi
    submit_appimagehub_pr "${mode}"
}

check_pypi_credentials() {
    if [[ -n "${PYPI_API_TOKEN:-}" ]]; then
        export TWINE_USERNAME="${TWINE_USERNAME:-__token__}"
        export TWINE_PASSWORD="${TWINE_PASSWORD:-${PYPI_API_TOKEN}}"
        return 0
    fi
    if [[ -n "${TWINE_PASSWORD:-}" ]]; then
        export TWINE_USERNAME="${TWINE_USERNAME:-__token__}"
        return 0
    fi
    err "Define PYPI_API_TOKEN o TWINE_PASSWORD (token de PyPI)."
    err "Crea uno en: https://pypi.org/manage/account/token/"
    return 1
}

ensure_release_tools() {
    local pip_bin="${PROJECT_ROOT}/.venv/bin/pip"
    local py_bin="${PROJECT_ROOT}/.venv/bin/python"
    if [[ -x "${pip_bin}" && -x "${py_bin}" ]]; then
        "${pip_bin}" install -q build twine
        printf '%s' "${py_bin}"
        return 0
    fi
    if python3 -m pip install -q --user build twine 2>/dev/null; then
        printf '%s' "python3"
        return 0
    fi
    python3 -m pip install -q build twine
    printf '%s' "python3"
}

run_tests() {
    if [[ "${KPS_SKIP_TESTS:-}" == "1" ]]; then
        warn "KPS_SKIP_TESTS=1 — omitiendo tests."
        return 0
    fi
    log "Ejecutando tests (pytest)..."
    if [[ -x "${PROJECT_ROOT}/.venv/bin/pytest" ]]; then
        "${PROJECT_ROOT}/.venv/bin/pytest" -q
    else
        python3 -m pytest -q
    fi
}

build_pypi_artifacts() {
    local python_bin
    python_bin="$(ensure_release_tools)"
    log "Generando sdist y wheel en dist/..."
    rm -f dist/kps-*.tar.gz dist/kps-*.whl 2>/dev/null || true
    "${python_bin}" -m build
    ls -1 dist/kps-*.tar.gz dist/kps-*.whl >&2
}

upload_pypi() {
    local python_bin twine_bin
    check_pypi_credentials || return 1
    python_bin="$(ensure_release_tools)"
    twine_bin="${PROJECT_ROOT}/.venv/bin/twine"
    if [[ ! -x "${twine_bin}" ]]; then
        twine_bin="twine"
    fi
    if ! ls dist/kps-*.tar.gz dist/kps-*.whl >/dev/null 2>&1; then
        err "No hay artefactos PyPI en dist/. Ejecuta primero la opción PyPI o 'Todo'."
        return 1
    fi
    log "Subiendo a PyPI (producción)..."
    "${twine_bin}" upload dist/kps-*.tar.gz dist/kps-*.whl
    log "PyPI: https://pypi.org/project/kps/${VERSION}/"
}

build_appimage() {
    if [[ "$(uname -s)" != "Linux" ]]; then
        err "AppImage solo se construye en Linux."
        err "Alternativa: descarga el artefacto del job build-appimage en GitHub Actions."
        return 1
    fi
    log "Construyendo AppImage..."
    bash "${SCRIPT_DIR}/build_appimage.sh"
    local arch appimage
    arch="$(uname -m)"
    case "${arch}" in
        x86_64) arch="x86_64" ;;
        aarch64) arch="aarch64" ;;
        *) warn "Arquitectura ${arch}: el nombre del AppImage puede variar." ;;
    esac
    appimage="${PROJECT_ROOT}/dist/kps-${arch}.AppImage"
    if [[ ! -f "${appimage}" ]]; then
        appimage="$(ls -1 "${PROJECT_ROOT}"/dist/kps-*.AppImage 2>/dev/null | head -1)"
    fi
    if [[ -z "${appimage}" || ! -f "${appimage}" ]]; then
        err "No se encontró dist/kps-*.AppImage tras el build."
        return 1
    fi
    printf '%s' "${appimage}"
}

ensure_git_tag() {
    local tag="v${VERSION}"
    if git rev-parse "${tag}" >/dev/null 2>&1; then
        log "Tag local ${tag} ya existe."
    else
        if ! confirm "¿Crear tag anotado ${tag}?"; then
            err "Se necesita el tag ${tag} para el release."
            return 1
        fi
        git tag -a "${tag}" -m "kps ${VERSION}"
        log "Tag ${tag} creado."
    fi
    local remote_tag
    if git ls-remote --tags origin "refs/tags/${tag}" | grep -q "${tag}"; then
        log "Tag ${tag} ya está en origin."
    else
        if confirm "¿Publicar tag ${tag} en origin (git push)?"; then
            git push origin "${tag}"
        else
            warn "Sin push del tag, gh release puede fallar si el tag no está en remoto."
        fi
    fi
}

collect_release_assets() {
    RELEASE_ASSETS=()
    local f
    for f in dist/kps-*.AppImage dist/kps-*.tar.gz dist/kps-*.whl; do
        [[ -f "${f}" ]] && RELEASE_ASSETS+=("${f}")
    done
}

publish_github_release() {
    local notes_file tag asset
    tag="v${VERSION}"
    notes_file="$(mktemp)"
    extract_release_notes "${VERSION}" > "${notes_file}" || {
        rm -f "${notes_file}"
        return 1
    }

    collect_release_assets
    if [[ ${#RELEASE_ASSETS[@]} -eq 0 ]]; then
        warn "Sin binarios en dist/ — el release solo tendrá notas."
        if ! confirm "¿Continuar sin adjuntos?"; then
            rm -f "${notes_file}"
            return 1
        fi
    fi

    ensure_git_tag || {
        rm -f "${notes_file}"
        return 1
    }

    if gh release view "${tag}" >/dev/null 2>&1; then
        log "Release ${tag} ya existe — subiendo assets..."
        if [[ ${#RELEASE_ASSETS[@]} -gt 0 ]]; then
            gh release upload "${tag}" "${RELEASE_ASSETS[@]}" --clobber
        fi
        gh release edit "${tag}" --notes-file "${notes_file}"
    else
        log "Creando release ${tag}..."
        if [[ ${#RELEASE_ASSETS[@]} -gt 0 ]]; then
            gh release create "${tag}" \
                --title "kps ${VERSION}" \
                --notes-file "${notes_file}" \
                "${RELEASE_ASSETS[@]}"
        else
            gh release create "${tag}" \
                --title "kps ${VERSION}" \
                --notes-file "${notes_file}"
        fi
    fi
    rm -f "${notes_file}"
    local url
    url="$(gh release view "${tag}" --json url -q .url)"
    log "GitHub Release: ${url}"
}

action_pypi() {
    check_versions_sync || return 1
    VERSION="$(get_version)"
    log "Versión: ${VERSION}"
    if ! confirm "¿Generar y subir paquetes a PyPI?"; then
        return 0
    fi
    build_pypi_artifacts
    upload_pypi
}

action_appimage() {
    check_versions_sync || return 1
    VERSION="$(get_version)"
    local appimage
    appimage="$(build_appimage)" || return 1
    log "AppImage listo: ${appimage}"
    if check_gh && confirm "¿Adjuntar AppImage al GitHub Release v${VERSION}?"; then
        local tag="v${VERSION}"
        if gh release view "${tag}" >/dev/null 2>&1; then
            gh release upload "${tag}" "${appimage}" --clobber
            log "AppImage subido a ${tag}."
        else
            warn "No existe release ${tag}. Usa la opción 'GitHub Release' o 'Publicar todo'."
        fi
    fi
}

action_github() {
    check_versions_sync || return 1
    check_gh || return 1
    VERSION="$(get_version)"
    log "Versión: ${VERSION}"
    if ! confirm "¿Crear/actualizar GitHub Release v${VERSION}?"; then
        return 0
    fi
    publish_github_release
}

action_all() {
    check_versions_sync || return 1
    check_gh || return 1
    check_pypi_credentials || return 1
    VERSION="$(get_version)"
    log "Publicación completa — versión ${VERSION}"

    if [[ "${KPS_SKIP_TESTS}" != "1" ]]; then
        if confirm "¿Ejecutar tests antes de publicar?"; then
            run_tests
        fi
    fi

    if ! confirm "Esto construirá PyPI + AppImage (Linux) y publicará en PyPI y GitHub. ¿Continuar?"; then
        return 0
    fi

    build_pypi_artifacts
    if [[ "$(uname -s)" == "Linux" ]]; then
        build_appimage >/dev/null
    else
        warn "Omitiendo build AppImage (no estás en Linux). Sube el artefacto de CI manualmente si hace falta."
    fi
    upload_pypi
    publish_github_release
    if confirm "¿Enviar PR a AppImageHub (catálogo comunitario)?"; then
        if appimagehub_entry_exists_upstream; then
            submit_appimagehub_pr refresh || true
        else
            submit_appimagehub_pr new || true
        fi
    fi
    log "Publicación completa finalizada."
}

action_verify() {
    log "Comprobando requisitos..."
    local ok=0
    if v="$(check_versions_sync 2>/dev/null)"; then
        log "  Versión sincronizada: ${v}"
    else
        ok=1
    fi
    if check_gh 2>/dev/null; then
        log "  GitHub CLI: OK ($(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo '?'))"
    else
        warn "  GitHub CLI: no listo"
        ok=1
    fi
    if [[ -n "${PYPI_API_TOKEN:-}" || -n "${TWINE_PASSWORD:-}" ]]; then
        log "  Credenciales PyPI: definidas"
    else
        warn "  Credenciales PyPI: falta PYPI_API_TOKEN o TWINE_PASSWORD"
        ok=1
    fi
    if [[ "$(uname -s)" == "Linux" ]]; then
        log "  AppImage build: posible en este host"
    else
        warn "  AppImage build: solo en Linux (usa CI para el binario)"
    fi
    if command -v gh >/dev/null && gh release view "v$(get_version)" >/dev/null 2>&1; then
        log "  Release v$(get_version): ya existe en GitHub"
    else
        log "  Release v$(get_version): aún no publicado"
    fi
    if check_gh 2>/dev/null; then
        if appimagehub_entry_exists_upstream; then
            log "  AppImageHub: entrada data/${APPIMAGEHUB_DATA_NAME} publicada"
        else
            log "  AppImageHub: sin entrada (opción 6 para PR de alta)"
        fi
    fi
    return "${ok}"
}

show_menu() {
    VERSION="$(get_version 2>/dev/null || echo '?')"
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║     kps — publicación v${VERSION}              ║"
    echo "╠══════════════════════════════════════════╣"
    echo "║  1) GitHub Release (notas + assets)      ║"
    echo "║  2) PyPI (sdist + wheel)                 ║"
    echo "║  3) AppImage (build + opcional GH)       ║"
    echo "║  4) Publicar todo (2+3+1 + AppImageHub)  ║"
    echo "║  5) Verificar requisitos                 ║"
    echo "║  6) AppImageHub (PR al catálogo)         ║"
    echo "║  0) Salir                                ║"
    echo "╚══════════════════════════════════════════╝"
    echo ""
}

main() {
    if [[ ! -f "${PROJECT_ROOT}/pyproject.toml" ]]; then
        err "Ejecuta desde el repositorio kps (falta pyproject.toml)."
        exit 1
    fi

    if [[ $# -gt 0 ]]; then
        case "${1}" in
            github) action_github; exit $? ;;
            pypi) action_pypi; exit $? ;;
            appimage) action_appimage; exit $? ;;
            appimagehub) action_appimagehub; exit $? ;;
            all) action_all; exit $? ;;
            verify) action_verify; exit $? ;;
            -h|--help)
                echo "Uso: $0 [github|pypi|appimage|appimagehub|all|verify]"
                exit 0
                ;;
            *)
                err "Subcomando desconocido: ${1}"
                exit 1
                ;;
        esac
    fi

    while true; do
        show_menu
        read -r -p "Opción: " choice
        case "${choice}" in
            1) action_github || true ;;
            2) action_pypi || true ;;
            3) action_appimage || true ;;
            4) action_all || true ;;
            5) action_verify || true ;;
            6) action_appimagehub || true ;;
            0|q|Q) log "Salida."; exit 0 ;;
            *) warn "Opción no válida." ;;
        esac
        echo ""
        read -r -p "Pulsa Enter para continuar..." _
    done
}

main "$@"
