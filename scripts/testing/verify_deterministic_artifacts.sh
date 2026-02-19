#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

OUT_DIR="${1:-${DEMO_FIXED_OUTPUT_ROOT:-}}"
if [[ -z "${OUT_DIR}" ]]; then
    echo "Usage: verify_deterministic_artifacts.sh <output-dir>"
    exit 1
fi

if [[ ! -d "${OUT_DIR}" ]]; then
    echo "Output directory not found: ${OUT_DIR}"
    exit 1
fi

CHECKSUM_FILE="${OUT_DIR}/checksums.txt"
GATE_FILE="${OUT_DIR}/determinism_gate.json"
BASELINE_DIR="${DEMO_BASELINE_DIR:-${PROJECT_ROOT}/exports/determinism-baselines}"
REQUIRE_EXISTING_BASELINE="${DEMO_REQUIRE_EXISTING_BASELINE:-0}"

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

manifest_value() {
    local key="$1"
    local manifest_path="${OUT_DIR}/run_manifest.json"
    if [[ ! -f "${manifest_path}" ]]; then
        echo "unknown"
        return
    fi
    grep -o "\"${key}\":\"[^\"]*\"" "${manifest_path}" | head -n 1 | cut -d'"' -f4 || echo "unknown"
}

main() {
    local file file_hash base_name
    local commit_sha seed baseline_file gate_status

    if [[ ! -f "${OUT_DIR}/runtime_package_fingerprint.txt" ]]; then
        echo "❌ Missing required runtime package fingerprint: ${OUT_DIR}/runtime_package_fingerprint.txt"
        exit 1
    fi

    local -a files=(
        "${OUT_DIR}/notebook_run_report.tsv"
        "${OUT_DIR}/image_digests.txt"
        "${OUT_DIR}/dependency_fingerprint.txt"
        "${OUT_DIR}/runtime_package_fingerprint.txt"
        "${OUT_DIR}/deterministic_manifest.json"
    )

    : > "${CHECKSUM_FILE}"
    for file in "${files[@]}"; do
        if [[ -f "${file}" ]]; then
            base_name="$(basename "${file}")"
            if [[ "${base_name}" == "notebook_run_report.tsv" ]]; then
                file_hash="$(hash_notebook_report_canonical "${file}")"
            else
                file_hash="$(hash_file "${file}")"
            fi
            printf "%s  %s\n" "${file_hash}" "${base_name}" >> "${CHECKSUM_FILE}"
        fi
    done

    commit_sha="$(manifest_value "commit_sha")"
    seed="$(manifest_value "seed")"
    if [[ "${seed}" == "unknown" || -z "${seed}" ]]; then
        seed="${DEMO_SEED:-42}"
    fi

    mkdir -p "${BASELINE_DIR}"
    baseline_file="${BASELINE_DIR}/${commit_sha}_${seed}.checksums"

    if [[ ! -f "${baseline_file}" ]]; then
        if [[ "${REQUIRE_EXISTING_BASELINE}" == "1" ]]; then
            echo "❌ Determinism baseline missing (strict mode): ${baseline_file}"
            cat > "${GATE_FILE}" <<EOF
{"result":"fail","mode":"baseline_missing","baseline":"${baseline_file}"}
EOF
            exit 1
        fi

        cp "${CHECKSUM_FILE}" "${baseline_file}"
        gate_status="baseline_created"
        echo "ℹ️  Determinism baseline created: ${baseline_file}"
        cat > "${GATE_FILE}" <<EOF
{"result":"pass","mode":"${gate_status}","baseline":"${baseline_file}"}
EOF
        exit 0
    fi

    if cmp -s "${CHECKSUM_FILE}" "${baseline_file}"; then
        gate_status="matched"
        echo "✅ Determinism checksums match baseline"
        cat > "${GATE_FILE}" <<EOF
{"result":"pass","mode":"${gate_status}","baseline":"${baseline_file}"}
EOF
        exit 0
    fi

    echo "❌ Determinism checksum mismatch against baseline"
    diff -u "${baseline_file}" "${CHECKSUM_FILE}" || true
    cat > "${GATE_FILE}" <<EOF
{"result":"fail","mode":"mismatch","baseline":"${baseline_file}"}
EOF
    exit 1
}

main "$@"
