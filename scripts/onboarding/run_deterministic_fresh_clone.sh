#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${PROJECT_ROOT}/scripts/utils/podman_connection.sh"

RUN_ID="fresh-clone-$(date -u +%Y%m%dT%H%M%SZ)"
SEED="42"
PODMAN_MACHINE="podman-wxd"
PODMAN_CPUS="4"
PODMAN_MEMORY_MB="8192"
PODMAN_DISK_GB="50"
STRICT_DETERMINISM="1"
RESET_STATE="1"
SKIP_NOTEBOOKS="0"
JSON_OUTPUT="0"

PROJECT_NAME="janusgraph-demo"
CONDA_ENV_NAME="janusgraph-analysis"
NOTEBOOK_TOTAL_TIMEOUT="${DEMO_NOTEBOOK_TOTAL_TIMEOUT:-1800}"
NOTEBOOK_CELL_TIMEOUT="${DEMO_NOTEBOOK_CELL_TIMEOUT:-300}"
DEMO_BASELINE_DIR="${DEMO_BASELINE_DIR:-${PROJECT_ROOT}/exports/determinism-baselines}"

FAILED_GATE="null"
CURRENT_GATE="none"
START_EPOCH="$(date +%s)"
STARTED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --run-id)
            RUN_ID="$2"
            shift 2
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        --podman-machine)
            PODMAN_MACHINE="$2"
            shift 2
            ;;
        --podman-cpus)
            PODMAN_CPUS="$2"
            shift 2
            ;;
        --podman-memory-mb)
            PODMAN_MEMORY_MB="$2"
            shift 2
            ;;
        --podman-disk-gb)
            PODMAN_DISK_GB="$2"
            shift 2
            ;;
        --strict-determinism)
            STRICT_DETERMINISM="1"
            shift
            ;;
        --no-reset)
            RESET_STATE="0"
            shift
            ;;
        --skip-notebooks)
            SKIP_NOTEBOOKS="1"
            shift
            ;;
        --json)
            JSON_OUTPUT="1"
            shift
            ;;
        --help|-h)
            cat <<'EOF'
Usage: run_deterministic_fresh_clone.sh [OPTIONS]

Options:
  --run-id <id>             Set run id for artifacts.
  --seed <int>              Deterministic seed (default: 42).
  --podman-machine <name>   Podman machine name (default: podman-wxd).
  --podman-cpus <int>       Podman machine CPU count (default: 4).
  --podman-memory-mb <int>  Podman memory MB (default: 8192).
  --podman-disk-gb <int>    Podman disk size GB (default: 50).
  --strict-determinism      Enable strict deterministic mode (default).
  --no-reset                Disable state reset before pipeline run.
  --skip-notebooks          Skip notebook execution.
  --json                    Print final status JSON.
  --help, -h                Show this help.
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

REPORT_DIR="${PROJECT_ROOT}/exports/${RUN_ID}"
STATUS_FILE="${REPORT_DIR}/status.json"
mkdir -p "${REPORT_DIR}"

log() {
    echo "[INFO] $*"
}

to_json_string_or_null() {
    local value="$1"
    if [[ "${value}" == "null" ]]; then
        echo "null"
    else
        printf '"%s"' "${value}"
    fi
}

service_state() {
    local service="$1"
    local prefixed="${PROJECT_NAME}_${service}_1"
    local container_name=""

    if [[ -z "${PODMAN_CONNECTION:-}" ]]; then
        echo "unknown"
        return
    fi

    if podman --remote --connection "${PODMAN_CONNECTION}" ps --format '{{.Names}}' | grep -qx "${prefixed}"; then
        container_name="${prefixed}"
    elif podman --remote --connection "${PODMAN_CONNECTION}" ps --format '{{.Names}}' | grep -qx "${service}"; then
        container_name="${service}"
    else
        echo "unavailable"
        return
    fi

    podman --remote --connection "${PODMAN_CONNECTION}" inspect "${container_name}" \
        --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' 2>/dev/null \
        || echo "unknown"
}

write_status_file() {
    local rc="$1"
    local result failed_gate_json ended_at_utc end_epoch duration
    local notebook_report total_nb pass_nb fail_nb
    local vault_status analytics_status jupyter_status hcd_status janusgraph_status

    ended_at_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    end_epoch="$(date +%s)"
    duration=$((end_epoch - START_EPOCH))

    if [[ "${rc}" -eq 0 ]]; then
        result="PASS"
    else
        result="FAIL"
    fi

    notebook_report="${REPORT_DIR}/notebook_run_report.tsv"
    total_nb=0
    pass_nb=0
    fail_nb=0
    if [[ -f "${notebook_report}" ]]; then
        total_nb="$(awk 'NR>1 {count += 1} END {print count+0}' "${notebook_report}")"
        pass_nb="$(awk -F'\t' 'NR>1 && $2=="PASS" {count += 1} END {print count+0}' "${notebook_report}")"
        fail_nb=$((total_nb - pass_nb))
    fi

    vault_status="$(service_state vault)"
    analytics_status="$(service_state analytics-api)"
    jupyter_status="$(service_state jupyter)"
    hcd_status="$(service_state hcd-server)"
    janusgraph_status="$(service_state janusgraph-server)"

    failed_gate_json="$(to_json_string_or_null "${FAILED_GATE}")"

    cat > "${STATUS_FILE}" <<EOF
{
  "run_id":"${RUN_ID}",
  "commit_sha":"$(git -C "${PROJECT_ROOT}" rev-parse HEAD 2>/dev/null || echo unknown)",
  "seed":"${SEED}",
  "result":"${result}",
  "failed_gate":${failed_gate_json},
  "started_at_utc":"${STARTED_AT_UTC}",
  "ended_at_utc":"${ended_at_utc}",
  "duration_seconds":${duration},
  "services":{
    "vault":"${vault_status}",
    "analytics_api":"${analytics_status}",
    "jupyter":"${jupyter_status}",
    "hcd_server":"${hcd_status}",
    "janusgraph":"${janusgraph_status}"
  },
  "notebooks":{
    "total":${total_nb},
    "pass":${pass_nb},
    "fail":${fail_nb}
  },
  "determinism_gate":"$(if [[ -f "${REPORT_DIR}/determinism_gate.json" ]]; then grep -o '"result":"[^"]*"' "${REPORT_DIR}/determinism_gate.json" | cut -d'"' -f4 || true; else echo "unknown"; fi)"
}
EOF
}

on_exit() {
    local rc=$?
    local final_rc
    trap - EXIT
    if [[ "${rc}" -ne 0 && "${FAILED_GATE}" == "null" ]]; then
        FAILED_GATE="${CURRENT_GATE}"
    fi

    if [[ "${rc}" -eq 0 ]]; then
        final_rc=0
    else
        case "${FAILED_GATE}" in
            G0_PRECHECK|G3_ENV)
                final_rc=10
                ;;
            G1_PODMAN|G2_CONNECTION)
                final_rc=20
                ;;
            G4_BUILD|G5_PIPELINE|G5_DEPLOY_VAULT|G3_RESET)
                final_rc=30
                ;;
            G6_RUNTIME_CONTRACT|G7_SEED)
                final_rc=40
                ;;
            G8_NOTEBOOKS)
                final_rc=50
                ;;
            G9_DETERMINISM)
                final_rc=60
                ;;
            *)
                final_rc=1
                ;;
        esac
    fi

    write_status_file "${rc}"
    if [[ "${JSON_OUTPUT}" == "1" ]]; then
        cat "${STATUS_FILE}" || true
    fi
    if [[ "${final_rc}" -eq 0 ]]; then
        echo "✅ PASS run_id=${RUN_ID} status=${STATUS_FILE}"
    else
        echo "❌ FAIL run_id=${RUN_ID} failed_gate=${FAILED_GATE} exit_code=${final_rc} status=${STATUS_FILE}"
    fi
    exit "${final_rc}"
}

trap on_exit EXIT

run_gate() {
    local gate="$1"
    shift
    CURRENT_GATE="${gate}"
    echo "[${gate}]"
    if ! "$@"; then
        if [[ "${FAILED_GATE}" == "null" ]]; then
            FAILED_GATE="${gate}"
        fi
        return 1
    fi
}

check_prereqs() {
    local cmd
    for cmd in podman podman-compose conda; do
        if ! command -v "${cmd}" >/dev/null 2>&1; then
            echo "Missing required command: ${cmd}"
            return 1
        fi
    done
}

normalize_memory_mb() {
    local value="$1"
    if [[ ! "${value}" =~ ^[0-9]+$ ]]; then
        echo ""
        return
    fi
    if (( value > 131072 )); then
        echo $((value / 1024 / 1024))
    else
        echo "${value}"
    fi
}

normalize_disk_gb() {
    local value="$1"
    if [[ ! "${value}" =~ ^[0-9]+$ ]]; then
        echo ""
        return
    fi
    if (( value > 1024 )); then
        echo $((value / 1024 / 1024 / 1024))
    else
        echo "${value}"
    fi
}

ensure_podman_machine() {
    local machine_exists current_cpu current_mem current_disk
    local norm_mem norm_disk

    machine_exists="0"
    if podman machine inspect "${PODMAN_MACHINE}" >/dev/null 2>&1; then
        machine_exists="1"
    fi

    if [[ "${machine_exists}" == "0" ]]; then
        log "Creating podman machine '${PODMAN_MACHINE}'"
        podman machine init "${PODMAN_MACHINE}" \
            --cpus "${PODMAN_CPUS}" \
            --memory "${PODMAN_MEMORY_MB}" \
            --disk-size "${PODMAN_DISK_GB}"
    fi

    podman machine start "${PODMAN_MACHINE}" >/dev/null 2>&1 || true

    current_cpu="$(podman machine inspect "${PODMAN_MACHINE}" --format '{{.CPUs}}' 2>/dev/null || true)"
    current_mem="$(podman machine inspect "${PODMAN_MACHINE}" --format '{{.Memory}}' 2>/dev/null || true)"
    current_disk="$(podman machine inspect "${PODMAN_MACHINE}" --format '{{.DiskSize}}' 2>/dev/null || true)"

    norm_mem="$(normalize_memory_mb "${current_mem}")"
    norm_disk="$(normalize_disk_gb "${current_disk}")"

    if [[ -n "${current_cpu}" && -n "${norm_mem}" && -n "${norm_disk}" ]]; then
        if [[ "${current_cpu}" != "${PODMAN_CPUS}" || "${norm_mem}" != "${PODMAN_MEMORY_MB}" || "${norm_disk}" != "${PODMAN_DISK_GB}" ]]; then
            echo "Podman machine spec mismatch: have cpu=${current_cpu} mem_mb=${norm_mem} disk_gb=${norm_disk}, expected cpu=${PODMAN_CPUS} mem_mb=${PODMAN_MEMORY_MB} disk_gb=${PODMAN_DISK_GB}"
            return 1
        fi
    fi
}

resolve_active_connection() {
    local conn=""

    for conn in "${PODMAN_MACHINE}-root" "${PODMAN_MACHINE}"; do
        if podman --remote --connection "${conn}" ps >/dev/null 2>&1; then
            PODMAN_CONNECTION="${conn}"
            export PODMAN_CONNECTION
            log "Using podman connection: ${PODMAN_CONNECTION}"
            return 0
        fi
    done

    if ! PODMAN_CONNECTION="$(resolve_podman_connection "${PODMAN_CONNECTION:-}")"; then
        echo "Failed to resolve a reachable podman connection"
        return 1
    fi
    if [[ -z "${PODMAN_CONNECTION}" ]]; then
        echo "Resolved podman connection is empty"
        return 1
    fi
    export PODMAN_CONNECTION
    log "Using podman connection: ${PODMAN_CONNECTION}"
}

ensure_conda_env() {
    if conda env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME}"; then
        conda env update -n "${CONDA_ENV_NAME}" -f "${PROJECT_ROOT}/environment.yml" --prune
    else
        conda env create -f "${PROJECT_ROOT}/environment.yml"
    fi

    if ! conda run -n "${CONDA_ENV_NAME}" uv --version >/dev/null 2>&1; then
        conda install -n "${CONDA_ENV_NAME}" -c conda-forge -y uv
    fi

    conda run -n "${CONDA_ENV_NAME}" uv lock --check
    conda run -n "${CONDA_ENV_NAME}" uv pip install -r "${PROJECT_ROOT}/requirements-dev.txt"
}

build_required_images() {
    cd "${PROJECT_ROOT}"
    podman build -t localhost/hcd:1.2.3 -f docker/hcd/Dockerfile .
}

run_pipeline() {
    local -a args=()
    local failed_gate_file
    if [[ "${SKIP_NOTEBOOKS}" == "1" ]]; then
        args+=(--skip-notebooks)
    fi

    cd "${PROJECT_ROOT}"
    failed_gate_file="${REPORT_DIR}/failed_gate.txt"
    if ! DEMO_PIPELINE_RUN_ID="${RUN_ID}" \
        DEMO_SEED="${SEED}" \
        DEMO_NOTEBOOK_TOTAL_TIMEOUT="${NOTEBOOK_TOTAL_TIMEOUT}" \
        DEMO_NOTEBOOK_CELL_TIMEOUT="${NOTEBOOK_CELL_TIMEOUT}" \
        DEMO_DETERMINISTIC_MODE="${STRICT_DETERMINISM}" \
        DEMO_RESET_STATE="${RESET_STATE}" \
        DEMO_BASELINE_DIR="${DEMO_BASELINE_DIR}" \
        COMPOSE_PROJECT_NAME="${PROJECT_NAME}" \
        PODMAN_CONNECTION="${PODMAN_CONNECTION}" \
        bash scripts/testing/run_demo_pipeline_repeatable.sh "${args[@]}"; then
        if [[ -f "${failed_gate_file}" ]]; then
            FAILED_GATE="$(tr -d '[:space:]' < "${failed_gate_file}")"
            if [[ -z "${FAILED_GATE}" ]]; then
                FAILED_GATE="G5_PIPELINE"
            fi
        else
            FAILED_GATE="G5_PIPELINE"
        fi
        return 1
    fi
}

run_gate G0_PRECHECK check_prereqs
run_gate G1_PODMAN ensure_podman_machine
run_gate G2_CONNECTION resolve_active_connection
run_gate G3_ENV ensure_conda_env
run_gate G4_BUILD build_required_images
run_gate G5_PIPELINE run_pipeline

FAILED_GATE="null"
CURRENT_GATE="none"
