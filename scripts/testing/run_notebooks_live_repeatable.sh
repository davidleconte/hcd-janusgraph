#!/usr/bin/env bash

set -euo pipefail

function sanitize_malloc_logging() {
  if [[ -n "${MallocStackLogging+x}" ]]; then
    unset MallocStackLogging
  fi
  if [[ -n "${MallocStackLoggingNoCompact+x}" ]]; then
    unset MallocStackLoggingNoCompact
  fi
}

sanitize_malloc_logging

# Deterministic notebook execution wrapper for live demo runs.
#
# - Fixed environment + hash seed.
# - Bounded notebook timeout and per-cell timeout.
# - Fixed run id and output directories for reproducibility.
# - Post-run validation for execution-level errors.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "${PROJECT_ROOT}/scripts/utils/podman_connection.sh"
export PROJECT_ROOT

CONTAINER_NAME="${CONTAINER_NAME:-janusgraph-demo_jupyter_1}"
CONTAINER_OUT_ROOT="/workspace/exports"

PODMAN_CONNECTION_VALUE="${PODMAN_CONNECTION:-}"
if ! PODMAN_CONNECTION_VALUE="$(resolve_podman_connection "${PODMAN_CONNECTION_VALUE}")"; then
  echo "Unable to resolve a reachable podman connection for notebook execution."
  exit 1
fi
RUN_ID="${DEMO_RUN_ID:-${DEMO_FIXED_RUN_ID:-live-notebooks-stable-$(date -u +%Y%m%dT%H%M%SZ)}}"
DEMO_SEED="${DEMO_SEED:-42}"
DEMO_FORCE_MOCK_PULSAR="${DEMO_FORCE_MOCK_PULSAR:-}"
DEMO_STREAMING_DETERMINISTIC_IDS="${DEMO_STREAMING_DETERMINISTIC_IDS:-0}"
PYTHON_HASH_SEED="${PYTHON_HASH_SEED:-${PYTHONHASHSEED:-0}}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TIMEZONE="${TZ:-UTC}"

TOTAL_TIMEOUT_SEC="${DEMO_NOTEBOOK_TOTAL_TIMEOUT:-420}"
CELL_TIMEOUT_SEC="${DEMO_NOTEBOOK_CELL_TIMEOUT:-180}"

# Allow callers (like the repeatable pipeline) to force a deterministic output
# directory while keeping container path stable and predictable.
LOCAL_OUTDIR="${DEMO_FIXED_OUTPUT_ROOT:-${PROJECT_ROOT}/exports/${RUN_ID}}"
RUN_BASENAME="$(basename "${LOCAL_OUTDIR}")"
CONTAINER_OUTDIR="${CONTAINER_OUT_ROOT}/${RUN_BASENAME}"
REPORT_TSV="${LOCAL_OUTDIR}/notebook_run_report.tsv"

export DEMO_FIXED_RUN_ID="${RUN_ID}"
export DEMO_FIXED_OUTPUT_ROOT="${LOCAL_OUTDIR}"
export TZ="${TIMEZONE}"

mkdir -p "${LOCAL_OUTDIR}"

printf "notebook\tstatus\texit_code\ttimestamp\tduration_s\terror_cells\tlog\n" \
  > "${REPORT_TSV}"

if [[ -f "${PROJECT_ROOT}/.vault-keys" ]]; then
  # shellcheck disable=SC1091
  source "${PROJECT_ROOT}/.vault-keys"
fi

VAULT_TOKEN_VALUE="${VAULT_TOKEN:-${VAULT_ROOT_TOKEN:-}}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "python3 / python is required for notebook parsing."
    exit 1
  fi
fi

if [[ -z "${VAULT_TOKEN_VALUE}" ]]; then
  echo "ℹ️  VAULT_TOKEN not set; notebook runs that require Vault will use anonymous/host defaults."
fi

BANKING_NOTEBOOKS=(
  banking/notebooks/*.ipynb
)

EXPLORATORY_NOTEBOOKS=(
  notebooks-exploratory/*.ipynb
)

TARGET_NOTEBOOKS=("$@")

check_container() {
  if ! podman --remote --connection "${PODMAN_CONNECTION_VALUE}" ps --filter "name=${CONTAINER_NAME}" --format '{{.Names}}' | \
    grep -q "^${CONTAINER_NAME}$"; then
    echo "Container '${CONTAINER_NAME}' is not running (connection: ${PODMAN_CONNECTION_VALUE})."
    echo "Start the full stack and retry before running this script."
    exit 1
  fi
}

detect_error_cells() {
  local notebook_file="$1"
  if [[ ! -f "${notebook_file}" ]]; then
    echo 0
    return
  fi

  env -u MallocStackLogging -u MallocStackLoggingNoCompact "${PYTHON_BIN}" - "$notebook_file" <<'PY'
import json
import sys


path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

error_cells = 0
for cell in nb.get("cells", []):
    for output in cell.get("outputs", []) or []:
        if output.get("output_type") == "error":
            error_cells += 1

print(error_cells)
PY
}

run_notebook() {
  local src="$1"
  local base
  local stem
  local container_src
  local out
  local log
  local start_ts
  local start_s
  local end_s
  local duration_s
  local rc
  local status
  local error_cells

  base=$(basename "$src")
  stem="${base%.ipynb}"
  if [[ "${src}" == notebooks-exploratory/* ]]; then
    container_src="/workspace/notebooks-exploratory/${base}"
  else
    container_src="/workspace/${src}"
  fi
  out="${CONTAINER_OUTDIR}/${stem}.executed.ipynb"
  log="${LOCAL_OUTDIR}/${stem}.log"
  start_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  start_s=$(date +%s)

  local -a env_args=(
    -e "PYTHONHASHSEED=${PYTHON_HASH_SEED}"
    -e "TZ=${TIMEZONE}"
    -e "LANG=C.UTF-8"
    -e "LC_ALL=C.UTF-8"
    -e "PYTHONPATH=/workspace:/workspace/banking:/workspace/src/python"
    -e "MPLBACKEND=Agg"
    -e "OPENSEARCH_USE_SSL=false"
    -e "VAULT_ADDR=http://vault:8200"
    -e "PULSAR_INTEGRATION=1"
    -e "PULSAR_URL=pulsar://pulsar:6650"
    -e "JANUSGRAPH_HOST=janusgraph-server"
    -e "JANUSGRAPH_PORT=8182"
    -e "OPENSEARCH_HOST=opensearch"
    -e "DEMO_SEED=${DEMO_SEED}"
    -e "DEMO_STREAMING_DETERMINISTIC_IDS=${DEMO_STREAMING_DETERMINISTIC_IDS}"
    -e "DEMO_FIXED_RUN_ID=${RUN_ID}"
    -e "DEMO_FIXED_OUTPUT_DIR=${CONTAINER_OUTDIR}/${stem}"
  )

  if [[ -n "${VAULT_TOKEN_VALUE}" ]]; then
    env_args+=( -e "VAULT_TOKEN=${VAULT_TOKEN_VALUE}" )
  fi

  if [[ -n "${DEMO_FORCE_MOCK_PULSAR}" ]]; then
    env_args+=( -e "DEMO_FORCE_MOCK_PULSAR=${DEMO_FORCE_MOCK_PULSAR}" )
  fi

  local cmd=(
    timeout "${TOTAL_TIMEOUT_SEC}"
    env
    -u MallocStackLogging
    -u MallocStackLoggingNoCompact
    podman
    --remote
    --connection
    "${PODMAN_CONNECTION_VALUE}"
    exec
    "${env_args[@]}"
    "${CONTAINER_NAME}"
    bash
    -lc
    "cd /workspace && conda run -n janusgraph-analysis python -m jupyter nbconvert --to notebook --execute ${container_src} --ExecutePreprocessor.kernel_name=python3 --ExecutePreprocessor.timeout=${CELL_TIMEOUT_SEC} --log-level INFO --output ${out}"
  )

  if "${cmd[@]}" > "${log}" 2>&1; then
    rc=0
    status="PASS"
  else
    rc=$?
    status="FAIL"
  fi

  end_s=$(date +%s)
  duration_s=$((end_s - start_s))
  error_cells=$(detect_error_cells "${LOCAL_OUTDIR}/${stem}.executed.ipynb")

  if [[ "${rc}" -eq 124 ]]; then
    status="TIMEOUT"
  fi

  if [[ "${status}" == "PASS" && "${error_cells}" -gt 0 ]]; then
    status="ERROR"
  fi

  printf "%s\t%s\t%s\t%s\t%d\t%d\t%s\n" \
    "${base}" "${status}" "${rc}" "${start_ts}" "${duration_s}" "${error_cells}" "${log}" \
    >> "${REPORT_TSV}"

  echo "${status}: ${base} (cells_with_error=${error_cells}, rc=${rc}, secs=${duration_s})"
}

main() {
  check_container

  if [[ "${#TARGET_NOTEBOOKS[@]}" -gt 0 ]]; then
    for nb in "${TARGET_NOTEBOOKS[@]}"; do
      if [[ -f "${nb}" ]]; then
        run_notebook "${nb}"
      else
        echo "SKIP: ${nb} (not found on host)"
      fi
    done
  else
    while IFS= read -r nb; do
      if [[ -f "${nb}" ]]; then
        run_notebook "${nb}"
      fi
    done < <(printf '%s\n' "${BANKING_NOTEBOOKS[@]}" | LC_ALL=C sort)

    while IFS= read -r nb; do
      if [[ -f "${nb}" ]]; then
        run_notebook "${nb}"
      fi
    done < <(printf '%s\n' "${EXPLORATORY_NOTEBOOKS[@]}" | LC_ALL=C sort)
  fi

  echo ""
  echo "📄 Report: ${REPORT_TSV}"
  echo "👁️  Tail:" 
  tail -n 20 "${REPORT_TSV}"
}

main "$@"
