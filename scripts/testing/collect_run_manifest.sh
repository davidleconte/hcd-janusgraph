#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "${PROJECT_ROOT}/scripts/utils/podman_connection.sh"

OUT_DIR="${1:-${DEMO_FIXED_OUTPUT_ROOT:-}}"
if [[ -z "${OUT_DIR}" ]]; then
    RUN_ID_FALLBACK="${DEMO_RUN_ID:-${DEMO_FIXED_RUN_ID:-manifest-$(date -u +%Y%m%dT%H%M%SZ)}}"
    OUT_DIR="${PROJECT_ROOT}/exports/${RUN_ID_FALLBACK}"
fi

mkdir -p "${OUT_DIR}"

RUN_ID="${DEMO_RUN_ID:-${DEMO_FIXED_RUN_ID:-$(basename "${OUT_DIR}")}}"
SEED_VALUE="${DEMO_SEED:-42}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"
PODMAN_CONNECTION="${PODMAN_CONNECTION:-}"
if ! PODMAN_CONNECTION="$(resolve_podman_connection "${PODMAN_CONNECTION}")"; then
    echo "❌ Unable to resolve a reachable podman connection"
    exit 1
fi

MANIFEST_FILE="${OUT_DIR}/run_manifest.json"
DETERMINISTIC_MANIFEST_FILE="${OUT_DIR}/deterministic_manifest.json"
IMAGE_DIGESTS_FILE="${OUT_DIR}/image_digests.txt"
DEPENDENCY_FINGERPRINT_FILE="${OUT_DIR}/dependency_fingerprint.txt"

hash_file() {
    local path="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "${path}" | awk '{print $1}'
        return
    fi
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "${path}" | awk '{print $1}'
        return
    fi
    echo "no-hash-tool"
}

hash_notebook_report_canonical() {
    local report_path="$1"
    if [[ ! -f "${report_path}" ]]; then
        echo "missing"
        return
    fi

    local tmp
    tmp="$(mktemp)"
    # Keep only stable fields: notebook, status, exit_code, error_cells.
    # Sort to avoid accidental ordering drift.
    awk -F'\t' 'BEGIN{OFS="\t"} NR>1 {print $1,$2,$3,$6}' "${report_path}" | LC_ALL=C sort > "${tmp}"
    hash_file "${tmp}"
    rm -f "${tmp}"
}

collect_images() {
    : > "${IMAGE_DIGESTS_FILE}"
    while IFS= read -r name; do
        if [[ -z "${name}" ]]; then
            continue
        fi
        podman --remote --connection "${PODMAN_CONNECTION}" inspect "${name}" \
            --format '{{.Name}}|{{.Config.Image}}|{{.Image}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
            >> "${IMAGE_DIGESTS_FILE}" 2>/dev/null || true
    done < <(podman --remote --connection "${PODMAN_CONNECTION}" ps \
        --filter "label=io.podman.compose.project=${PROJECT_NAME}" \
        --format '{{.Names}}')
}

collect_dependency_fingerprint() {
    : > "${DEPENDENCY_FINGERPRINT_FILE}"
    local candidate
    for candidate in \
        "${PROJECT_ROOT}/pyproject.toml" \
        "${PROJECT_ROOT}/uv.lock" \
        "${PROJECT_ROOT}/requirements.txt" \
        "${PROJECT_ROOT}/docker/api/Dockerfile" \
        "${PROJECT_ROOT}/docker/jupyter/environment.yml"; do
        if [[ -f "${candidate}" ]]; then
            printf "%s\t%s\n" "$(hash_file "${candidate}")" "${candidate#"${PROJECT_ROOT}"/}" \
                >> "${DEPENDENCY_FINGERPRINT_FILE}"
        fi
    done
}

file_hash_or_missing() {
    local target="$1"
    if [[ -f "${target}" ]]; then
        hash_file "${target}"
    else
        echo "missing"
    fi
}

main() {
    local commit_sha generated_at
    local notebook_report_hash image_digests_hash dependency_hash
    commit_sha="$(git -C "${PROJECT_ROOT}" rev-parse HEAD 2>/dev/null || echo unknown)"
    generated_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    collect_images
    collect_dependency_fingerprint

    notebook_report_hash="$(hash_notebook_report_canonical "${OUT_DIR}/notebook_run_report.tsv")"
    image_digests_hash="$(file_hash_or_missing "${IMAGE_DIGESTS_FILE}")"
    dependency_hash="$(file_hash_or_missing "${DEPENDENCY_FINGERPRINT_FILE}")"

    cat > "${MANIFEST_FILE}" <<EOF
{
  "run_id":"${RUN_ID}",
  "commit_sha":"${commit_sha}",
  "seed":"${SEED_VALUE}",
  "generated_at_utc":"${generated_at}",
  "compose_project_name":"${PROJECT_NAME}",
  "podman_connection":"${PODMAN_CONNECTION}",
  "image_digests_file":"$(basename "${IMAGE_DIGESTS_FILE}")",
  "dependency_fingerprint_file":"$(basename "${DEPENDENCY_FINGERPRINT_FILE}")",
  "deterministic_manifest_file":"$(basename "${DETERMINISTIC_MANIFEST_FILE}")",
  "notebook_report_file":"notebook_run_report.tsv",
  "summary_file":"pipeline_summary.txt"
}
EOF

    cat > "${DETERMINISTIC_MANIFEST_FILE}" <<EOF
{
  "commit_sha":"${commit_sha}",
  "seed":"${SEED_VALUE}",
  "compose_project_name":"${PROJECT_NAME}",
  "image_digests_sha256":"${image_digests_hash}",
  "dependency_fingerprint_sha256":"${dependency_hash}",
  "notebook_report_sha256":"${notebook_report_hash}"
}
EOF

    echo "✅ Run manifest written: ${MANIFEST_FILE}"
}

main "$@"
