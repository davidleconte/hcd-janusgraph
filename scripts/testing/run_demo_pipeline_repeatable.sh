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
#
#   # Skip strict preflight check (useful when services are already
#   # running and you want deterministic live verification of the stack)
#   ./run_demo_pipeline_repeatable.sh --skip-preflight
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "${PROJECT_ROOT}/scripts/utils/podman_connection.sh"

RUN_ID="${DEMO_PIPELINE_RUN_ID:-demo-$(date -u +%Y%m%dT%H%M%SZ)}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"
DEMO_SEED="${DEMO_SEED:-42}"
NOTEBOOK_TIMEOUT="${DEMO_NOTEBOOK_TOTAL_TIMEOUT:-420}"
NOTEBOOK_CELL_TIMEOUT="${DEMO_NOTEBOOK_CELL_TIMEOUT:-180}"
MAX_HEALTH_WAIT_SEC="${MAX_HEALTH_WAIT_SEC:-300}"
REPORT_DIR="${PROJECT_ROOT}/exports/${RUN_ID}"
DEMO_DETERMINISTIC_MODE="${DEMO_DETERMINISTIC_MODE:-1}"
DEMO_RESET_STATE="${DEMO_RESET_STATE:-1}"
DEMO_BASELINE_DIR="${DEMO_BASELINE_DIR:-${PROJECT_ROOT}/exports/determinism-baselines}"
FAILED_GATE_FILE="${REPORT_DIR}/failed_gate.txt"

SKIP_NOTEBOOKS=false
SKIP_DATA_GENERATORS=false
SKIP_GRAPH_SEED=false
SKIP_DEPLOY=false
SKIP_PREFLIGHT=false
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
        --skip-preflight)
            SKIP_PREFLIGHT=true
            shift
            ;;
        --skip-graph-seed)
            SKIP_GRAPH_SEED=true
            shift
            ;;
        --skip-deploy)
            SKIP_DEPLOY=true
            shift
            ;;
        --no-reset)
            DEMO_RESET_STATE=0
            shift
            ;;
        --deterministic-off)
            DEMO_DETERMINISTIC_MODE=0
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
  --skip-preflight        Skip preflight checks.
  --skip-graph-seed       Skip JanusGraph demo seed check/load.
  --skip-deploy           Skip full stack deployment (assume services already up).
  --no-reset              Disable deterministic state reset before deploy.
  --deterministic-off     Disable deterministic artifact verification.
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

if [[ "$DRY_RUN" == "true" ]]; then
    PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"
else
    PODMAN_CONNECTION="${PODMAN_CONNECTION:-}"
    if ! PODMAN_CONNECTION="$(resolve_podman_connection "${PODMAN_CONNECTION}")"; then
        echo "❌ Unable to resolve a reachable podman connection."
        mkdir -p "${REPORT_DIR}"
        echo "G2_CONNECTION" > "${FAILED_GATE_FILE}"
        exit 1
    fi
fi
RESOLVED_PODMAN_CONNECTION="${PODMAN_CONNECTION}"

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
        case "${step}" in
            "Preflight Validation"|"Podman Isolation Validation")
                echo "G0_PRECHECK" > "${FAILED_GATE_FILE}"
                ;;
            "Deterministic State Reset")
                echo "G3_RESET" > "${FAILED_GATE_FILE}"
                ;;
            "Deploy Full Stack")
                echo "G5_DEPLOY_VAULT" > "${FAILED_GATE_FILE}"
                ;;
            "Runtime Contracts Validation")
                echo "G6_RUNTIME_CONTRACT" > "${FAILED_GATE_FILE}"
                ;;
            "Seed/Validate Demo Graph Data")
                echo "G7_SEED" > "${FAILED_GATE_FILE}"
                ;;
            "Run Live Notebooks (Repeatable)")
                echo "G8_NOTEBOOKS" > "${FAILED_GATE_FILE}"
                ;;
            "Determinism Artifact Verification")
                echo "G9_DETERMINISM" > "${FAILED_GATE_FILE}"
                ;;
            *)
                echo "G5_PIPELINE" > "${FAILED_GATE_FILE}"
                ;;
        esac
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

# Keep the resolved runtime connection even if .env defines PODMAN_CONNECTION.
PODMAN_CONNECTION="${RESOLVED_PODMAN_CONNECTION}"

mkdir -p "${REPORT_DIR}"
: > "${FAILED_GATE_FILE}"
export COMPOSE_PROJECT_NAME="$PROJECT_NAME"
export PODMAN_CONNECTION="$PODMAN_CONNECTION"

export DEMO_RUN_ID="$RUN_ID"
export DEMO_FIXED_RUN_ID="$RUN_ID"
export DEMO_FIXED_OUTPUT_ROOT="$REPORT_DIR"
export DEMO_SEED="$DEMO_SEED"
export DEMO_NOTEBOOK_TOTAL_TIMEOUT="$NOTEBOOK_TIMEOUT"
export DEMO_NOTEBOOK_CELL_TIMEOUT="$NOTEBOOK_CELL_TIMEOUT"
export DEMO_DETERMINISTIC_MODE="$DEMO_DETERMINISTIC_MODE"
export DEMO_RESET_STATE="$DEMO_RESET_STATE"
export DEMO_BASELINE_DIR="$DEMO_BASELINE_DIR"

sanitize_malloc_logging

cd "$PROJECT_ROOT"

if [[ "$DEMO_DETERMINISTIC_MODE" == "1" && "$DEMO_RESET_STATE" == "1" && "$SKIP_DEPLOY" == "false" ]]; then
    run_cmd "Deterministic State Reset" \
        "cd config/compose && podman-compose -p ${PROJECT_NAME} -f docker-compose.full.yml down -v" \
        "${REPORT_DIR}/state_reset.log" \
        bash -lc "cd config/compose && podman-compose -p ${PROJECT_NAME} -f docker-compose.full.yml down -v || true"
fi

if [[ "$SKIP_PREFLIGHT" == "false" ]]; then
    run_cmd "Preflight Validation" \
        "scripts/validation/preflight_check.sh --strict" \
        "${REPORT_DIR}/preflight.log" \
        bash scripts/validation/preflight_check.sh --strict
    run_cmd "Podman Isolation Validation" \
        "scripts/validation/validate_podman_isolation.sh --strict" \
        "${REPORT_DIR}/podman_isolation.log" \
        bash scripts/validation/validate_podman_isolation.sh --strict
else
    echo "⏭️  Skipping strict preflight and podman isolation validation"
fi

if [[ "$SKIP_DEPLOY" == "false" ]]; then
    run_cmd "Deploy Full Stack" \
        "cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh" \
        "${REPORT_DIR}/deploy.log" \
        bash -c "cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh"
else
    echo "⏭️  Skipping full stack deployment"
fi

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
        echo "G5_DEPLOY_VAULT" > "${FAILED_GATE_FILE}"
        echo "❌ Services did not become healthy in time."
        tail -n 120 "${REPORT_DIR}/health.log" || true
        exit 1
    fi
    echo "✅ Services healthy"

    {
        echo "=== service snapshot: podman ps (label filter) ==="
        podman --remote --connection "${PODMAN_CONNECTION}" ps --filter "label=io.podman.compose.project=${PROJECT_NAME}" --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        echo "=== service snapshot: inspect key services ==="
        podman --remote --connection "${PODMAN_CONNECTION}" inspect janusgraph-demo_jupyter_1 --format '{{.Name}} state={{.State.Status}} started={{.State.StartedAt}}'
        podman --remote --connection "${PODMAN_CONNECTION}" inspect janusgraph-demo_hcd-server_1 --format '{{.Name}} state={{.State.Status}} started={{.State.StartedAt}}'
        podman --remote --connection "${PODMAN_CONNECTION}" inspect janusgraph-demo_pulsar_1 --format '{{.Name}} state={{.State.Status}} started={{.State.StartedAt}}'
    } > "${REPORT_DIR}/services_snapshot.log"
fi

run_cmd "Runtime Contracts Validation" \
    "scripts/testing/check_runtime_contracts.sh" \
    "${REPORT_DIR}/runtime_contracts.log" \
    bash scripts/testing/check_runtime_contracts.sh

if [[ "$SKIP_GRAPH_SEED" == "false" ]]; then
    run_cmd "Seed/Validate Demo Graph Data" \
        "scripts/testing/seed_demo_graph.sh" \
        "${REPORT_DIR}/seed_graph.log" \
        bash scripts/testing/seed_demo_graph.sh
else
    echo "⏭️  Skipping graph seed check"
fi

if [[ "$SKIP_NOTEBOOKS" == "false" ]]; then
    run_cmd "Run Live Notebooks (Repeatable)" \
        "scripts/testing/run_notebooks_live_repeatable.sh" \
        "${REPORT_DIR}/notebooks.log" \
        bash scripts/testing/run_notebooks_live_repeatable.sh

    if [[ "$DRY_RUN" == "false" ]]; then
        notebook_report="${REPORT_DIR}/notebook_run_report.tsv"

        if [[ ! -f "$notebook_report" ]]; then
            fallback_report="${PROJECT_ROOT}/exports/${RUN_ID}/notebook_run_report.tsv"
            if [[ -f "$fallback_report" ]]; then
                ln -sf "$fallback_report" "$notebook_report"
            fi
        fi

        if [[ ! -f "$notebook_report" ]]; then
            echo "G8_NOTEBOOKS" > "${FAILED_GATE_FILE}"
            echo "❌ Notebook report not found: ${notebook_report}"
            exit 1
        fi

        non_pass_count="$(awk -F'\t' '$2 != "PASS" && NR>1 {count += 1} END {print count+0}' "$notebook_report")"
        if [[ "${non_pass_count}" -gt 0 ]]; then
            echo "G8_NOTEBOOKS" > "${FAILED_GATE_FILE}"
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
    echo "Steps: reset, preflight, isolation, deploy, service-boot, runtime-contracts, service-snapshot, notebooks, data-generators, manifest, determinism"
    echo "SKIP_PREFLIGHT=${SKIP_PREFLIGHT}"
    echo "SKIP_DEPLOY=${SKIP_DEPLOY}"
    echo "SKIP_NOTEBOOKS=${SKIP_NOTEBOOKS}"
    echo "SKIP_DATA_GENERATORS=${SKIP_DATA_GENERATORS}"
    echo "SKIP_GRAPH_SEED=${SKIP_GRAPH_SEED}"
    echo "DEMO_DETERMINISTIC_MODE=${DEMO_DETERMINISTIC_MODE}"
    echo "DEMO_RESET_STATE=${DEMO_RESET_STATE}"
    echo "DEMO_BASELINE_DIR=${DEMO_BASELINE_DIR}"
} > "${SUMMARY_FILE}"

if [[ "$DRY_RUN" == "false" ]]; then
    run_cmd "Collect Run Manifest" \
        "scripts/testing/collect_run_manifest.sh ${REPORT_DIR}" \
        "${REPORT_DIR}/manifest.log" \
        bash scripts/testing/collect_run_manifest.sh "${REPORT_DIR}"

    if [[ "$DEMO_DETERMINISTIC_MODE" == "1" ]]; then
        run_cmd "Determinism Artifact Verification" \
            "scripts/testing/verify_deterministic_artifacts.sh ${REPORT_DIR}" \
            "${REPORT_DIR}/determinism.log" \
            bash -lc "DEMO_BASELINE_DIR='${DEMO_BASELINE_DIR}' bash scripts/testing/verify_deterministic_artifacts.sh '${REPORT_DIR}'"
    fi
fi

echo "none" > "${FAILED_GATE_FILE}"
echo "✅ Repeatable demo pipeline complete"
echo "   Summary: ${SUMMARY_FILE}"
