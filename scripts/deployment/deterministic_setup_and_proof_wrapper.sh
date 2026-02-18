#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PIPELINE_SCRIPT="${ROOT_DIR}/scripts/testing/run_demo_pipeline_repeatable.sh"
STATUS_REPORT=""
PASSTHRU_ARGS=()
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: scripts/deployment/deterministic_setup_and_proof_wrapper.sh [options] [pipeline args...]

Options:
  --status-report <path>   Write JSON status report to the provided path.
  --dry-run                Print ordered execution plan without running pipeline.
  -h, --help               Show this help.

All unknown options/arguments are passed through to:
  scripts/testing/run_demo_pipeline_repeatable.sh
EOF
}

while (($# > 0)); do
  case "$1" in
    --status-report)
      if (($# < 2)); then
        echo "--status-report requires a path" >&2
        exit 2
      fi
      STATUS_REPORT="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      PASSTHRU_ARGS+=("--dry-run")
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      PASSTHRU_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ ! -x "${PIPELINE_SCRIPT}" ]]; then
  echo "Pipeline runner not executable: ${PIPELINE_SCRIPT}" >&2
  exit 1
fi

: "${COMPOSE_PROJECT_NAME:=janusgraph-demo}"
export COMPOSE_PROJECT_NAME

if [[ ${DRY_RUN} -eq 1 ]]; then
  echo "Deterministic wrapper dry-run"
  echo "1. Validate canonical runner availability"
  echo "2. Export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}"
  echo "3. Execute scripts/testing/run_demo_pipeline_repeatable.sh with passthrough args"
  echo "4. Emit optional status report"
  exit 0
fi

set +e
"${PIPELINE_SCRIPT}" "${PASSTHRU_ARGS[@]}"
EXIT_CODE=$?
set -e

if [[ -n "${STATUS_REPORT}" ]]; then
  mkdir -p "$(dirname "${STATUS_REPORT}")"
  RUN_TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")"
  ARGS_STR=""
  if [[ ${#PASSTHRU_ARGS[@]} -gt 0 ]]; then
    ARGS_STR="$(printf '%q ' "${PASSTHRU_ARGS[@]}")"
  fi
  cat > "${STATUS_REPORT}" <<EOF
{
  "timestamp_utc": "${RUN_TIMESTAMP}",
  "wrapper": "scripts/deployment/deterministic_setup_and_proof_wrapper.sh",
  "pipeline_script": "scripts/testing/run_demo_pipeline_repeatable.sh",
  "compose_project_name": "${COMPOSE_PROJECT_NAME}",
  "args": "${ARGS_STR}",
  "exit_code": ${EXIT_CODE}
}
EOF
fi

exit "${EXIT_CODE}"
