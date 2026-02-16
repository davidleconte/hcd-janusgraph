#!/usr/bin/env bash

set -euo pipefail

# =============================================================================
# Repeatable Demo Pipeline Runner
# =============================================================================
# Goal:
#   Provide a deterministic one-command pathway that starts services, waits for
#   readiness, validates graph health, and executes all live notebooks with
#   bounded runtimes.
#
# Usage examples:
#   # Full deterministic run
#   ./run_demo_pipeline_repeatable.sh
#
#   # Skip notebooks (services + smoke checks only)
#   ./run_demo_pipeline_repeatable.sh --skip-notebooks
#
#   # Skip data generator smoke tests
#   ./run_demo_pipeline_repeatable.sh --skip-data-generators
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

RUN_ID="${DEMO_PIPELINE_RUN_ID:-demo-$(date -u +%Y%m%dT%H%M%SZ)}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"
DEMO_SEED="${DEMO_SEED:-42}"
NOTEBOOK_TIMEOUT="${DEMO_NOTEBOOK_TOTAL_TIMEOUT:-420}"
NOTEBOOK_CELL_TIMEOUT="${DEMO_NOTEBOOK_CELL_TIMEOUT:-180}"
MAX_HEALTH_WAIT_SEC="${MAX_HEALTH_WAIT_SEC:-300}"
REPORT_DIR="${PROJECT_ROOT}/exports/${RUN_ID}"

SKIP_NOTEBOOKS=false
SKIP_DATA_GENERATORS=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-notebooks)
            SKIP_NOTEBOOKS=true
            shift
            ;;
        --skip-data-generators)
            SKIP_DATA_GENERATORS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            cat <<'EOF'
Usage: run_demo_pipeline_repeatable.sh [OPTIONS]

Options:
  --skip-notebooks        Skip notebook execution step.
  --skip-data-generators  Skip data generator smoke tests.
  --dry-run               Print commands only, do not execute.
  --help, -h              Show this help.
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage."
            exit 1
            ;;
    esac
done

sanitize_malloc_logging() {
    if [[ -n "${MallocStackLogging+x}" ]]; then
        unset MallocStackLogging
    fi
    if [[ -n "${MallocStackLoggingNoCompact+x}" ]]; then
        unset MallocStackLoggingNoCompact
    fi
}

run_cmd() {
    local step="$1"
    local cmd_desc="$2"
    local log_file="$3"
    shift 3

    echo "[STEP] ${step}"
    echo "       ${cmd_desc}"
    echo "       log: ${log_file}"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY-RUN: $*"
        return 0
    fi

    if ! "$@" >"${log_file}" 2>&1; then
        echo "❌ ${step} failed"
        echo "--- Last 80 lines: ${log_file} ---"
        tail -n 80 "${log_file}" || true
        return 1
    fi
    echo "✅ ${step} complete"
}

if [[ -f "$PROJECT_ROOT/.env" ]]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env"
fi

if [[ -f "$PROJECT_ROOT/.vault-keys" ]]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.vault-keys"
fi

mkdir -p "${REPORT_DIR}"
export COMPOSE_PROJECT_NAME="$PROJECT_NAME"
export PODMAN_CONNECTION="$PODMAN_CONNECTION"

export DEMO_FIXED_RUN_ID="$RUN_ID"
export DEMO_FIXED_OUTPUT_ROOT="$REPORT_DIR"
export DEMO_SEED="$DEMO_SEED"
export DEMO_NOTEBOOK_TOTAL_TIMEOUT="$NOTEBOOK_TIMEOUT"
export DEMO_NOTEBOOK_CELL_TIMEOUT="$NOTEBOOK_CELL_TIMEOUT"

sanitize_malloc_logging

cd "$PROJECT_ROOT"

run_cmd "Preflight Validation" \
    "scripts/validation/preflight_check.sh --strict" \
    "${REPORT_DIR}/preflight.log" \
    bash scripts/validation/preflight_check.sh --strict

run_cmd "Podman Isolation Validation" \
    "scripts/validation/validate_podman_isolation.sh --strict" \
    "${REPORT_DIR}/podman_isolation.log" \
    bash scripts/validation/validate_podman_isolation.sh --strict

run_cmd "Deploy Full Stack" \
    "cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh" \
    "${REPORT_DIR}/deploy.log" \
    bash -c "cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh"

if [[ "$DRY_RUN" == "false" ]]; then
    echo "[STEP] Waiting for service readiness"
    health_failed=true
    for attempt in $(seq 1 "$MAX_HEALTH_WAIT_SEC"); do
        if bash scripts/testing/check_graph_counts.sh >"${REPORT_DIR}/health.log" 2>&1; then
            health_failed=false
            break
        fi
        echo "   waiting for services... ${attempt}/${MAX_HEALTH_WAIT_SEC}"
        sleep 2
    done

    if [[ "$health_failed" == "true" ]]; then
        echo "❌ Services did not become healthy in time."
        tail -n 120 "${REPORT_DIR}/health.log" || true
        exit 1
    fi
    echo "✅ Services healthy"
fi

if [[ "$SKIP_NOTEBOOKS" == "false" ]]; then
    run_cmd "Run Live Notebooks (Repeatable)" \
        "scripts/testing/run_notebooks_live_repeatable.sh" \
        "${REPORT_DIR}/notebooks.log" \
        bash scripts/testing/run_notebooks_live_repeatable.sh

    if [[ "$DRY_RUN" == "false" ]]; then
        notebook_report="${REPORT_DIR}/notebook_run_report.tsv"
        if [[ ! -f "$notebook_report" ]]; then
            echo "❌ Notebook report not found: ${notebook_report}"
            exit 1
        fi

        non_pass_count="$(awk -F'\t' '$2 != "PASS" && NR>1 {count += 1} END {print count+0}' "$notebook_report")"
        if [[ "${non_pass_count}" -gt 0 ]]; then
            echo "❌ Notebook run finished with failures:"
            awk -F'\t' '$2 != "PASS" && NR>1 {print "   " $1 " -> " $2 ", rc=" $3 }' "$notebook_report"
            exit 1
        fi
        echo "✅ All notebooks passed in repeatable run"
    else
        echo "⏭️  Dry-run mode: skipping notebook report validation."
    fi
else
    echo "⏭️  Skipping notebook execution"
fi

if [[ "$SKIP_DATA_GENERATORS" == "false" ]]; then
    run_cmd "Data Generator Smoke Tests" \
        "Data generator non-slow/integration/benchmark tests (coverage gate disabled)" \
        "${REPORT_DIR}/data_generators_smoke.log" \
        bash -lc "cd banking/data_generators/tests && conda run -n janusgraph-analysis pytest -m \"not slow and not integration and not benchmark\" --override-ini addopts='' -q"
fi

SUMMARY_FILE="${REPORT_DIR}/pipeline_summary.txt"
{
    echo "Run ID: ${RUN_ID}"
    echo "Project: ${PROJECT_NAME}"
    echo "Podman connection: ${PODMAN_CONNECTION}"
    echo "Report directory: ${REPORT_DIR}"
    echo "Steps: preflight, isolation, deploy, service-boot, notebooks, data-generators"
} > "${SUMMARY_FILE}"

echo "✅ Repeatable demo pipeline complete"
echo "   Summary: ${SUMMARY_FILE}"
