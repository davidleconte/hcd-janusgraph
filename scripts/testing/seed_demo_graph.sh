#!/usr/bin/env bash

set -euo pipefail

# =============================================================================
# Deterministic Demo Graph Seed Helper
# =============================================================================
# Ensures JanusGraph contains a minimal runnable dataset before notebook/demo runs.
#
# Why:
#   Several notebook and integration tests assume at least a small base graph with
#   person/company/product labels and common sample entities (e.g. Alice Johnson).
#   Running on a fresh stack leaves JanusGraph empty, which causes false failures
#   in strict assertions and notebook runbooks.
# =============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"
DEMO_REQUIRED_MIN_VERTICES="${DEMO_REQUIRED_MIN_VERTICES:-11}"
DEMO_REQUIRED_MIN_PERSONS="${DEMO_REQUIRED_MIN_PERSONS:-5}"

CONTAINER_LIST=""
GREMLIN_CONTAINER="${GREMLIN_CONTAINER:-}"

run_podman_ps() {
  PODMAN_CONNECTION="${PODMAN_CONNECTION}" \
    podman --remote ps --format '{{.Names}}'
}

load_container_list() {
  if ! CONTAINER_LIST="$(run_podman_ps 2>&1)"; then
    echo "[ERROR] Podman access failed for connection '${PODMAN_CONNECTION}'"
    echo "   ${CONTAINER_LIST}"
    return 1
  fi
}

resolve_container_name() {
  local service_name="$1"
  local candidate_with_prefix="${COMPOSE_PROJECT_NAME}_${service_name}_1"

  if printf '%s\n' "${CONTAINER_LIST}" | grep -qx "${candidate_with_prefix}"; then
    echo "${candidate_with_prefix}"
    return 0
  fi

  if printf '%s\n' "${CONTAINER_LIST}" | grep -qx "${service_name}"; then
    echo "${service_name}"
    return 0
  fi

  return 1
}

run_gremlin() {
  local script="$1"
  local output

  if ! output="$(PODMAN_CONNECTION="${PODMAN_CONNECTION}" podman --remote exec -i "${GREMLIN_CONTAINER}" ./bin/gremlin.sh 2>&1 <<EOF
:remote connect tinkerpop.server conf/remote.yaml
:remote console
${script}
:quit
EOF
)"; then
    echo "${output}"
    return 1
  fi

  echo "${output}"
}

query_gremlin_scalar() {
  local query="$1"
  local raw
  local value
  local cleaned

  if ! raw="$(run_gremlin "${query}")"; then
    return 1
  fi

  cleaned="$(printf '%s\n' "${raw}" | sed -E 's/\x1B\[[0-9;]*[A-Za-z]//g')"
  value="$(printf '%s\n' "${cleaned}" | grep '^==>' | sed 's/^==>[[:space:]]*//' | tail -n 1)"
  if [[ -z "${value}" ]]; then
    echo "[ERROR] Gremlin query produced no result"
    return 1
  fi
  echo "${value}"
}

query_gremlin_ok() {
  local query="$1"
  local expected_min="$2"
  local value
  local -i min_value

  min_value="${expected_min}"
  if ! value="$(query_gremlin_scalar "${query}")"; then
    return 1
  fi

  if [[ ! "${value}" =~ ^[0-9]+$ ]]; then
    echo "[ERROR] Gremlin scalar is not numeric: ${value}"
    return 1
  fi

  if (( value < min_value )); then
    echo "[ERROR] Query below threshold. query=${query}, got=${value}, min=${expected_min}"
    return 1
  fi

  return 0
}

run_gremlin_file() {
  local file_path="$1"
  local script

  if [[ ! -f "${file_path}" ]]; then
    echo "[ERROR] File not found: ${file_path}"
    return 1
  fi

  script="$(tr '\n' ';' < "${file_path}")"
  run_gremlin "${script}"
}

run_seed_step() {
  local schema_file="${PROJECT_ROOT}/src/groovy/init_schema_remote.groovy"
  local data_file="${PROJECT_ROOT}/src/groovy/load_data_remote.groovy"
  local schema_output
  local data_output

  echo "[INFO] Initializing schema (idempotent)"
  if ! schema_output="$(run_gremlin_file "${schema_file}")"; then
    echo "${schema_output}"
    if ! echo "${schema_output}" | grep -qi "already"; then
      return 1
    fi
    echo "[INFO] Schema init raised an 'already' condition, continuing."
  fi

  echo "[INFO] Loading sample data"
  if ! data_output="$(run_gremlin_file "${data_file}")"; then
    echo "${data_output}"
    return 1
  fi

  echo "${data_output}"
}

main() {
  echo "[INFO] Verifying Gremlin container availability"

  if ! load_container_list; then
    return 1
  fi

  if [[ -z "${GREMLIN_CONTAINER}" ]]; then
    if ! GREMLIN_CONTAINER="$(resolve_container_name janusgraph-server)"; then
      if ! GREMLIN_CONTAINER="$(resolve_container_name gremlin-console)"; then
    echo "[ERROR] Unable to resolve Gremlin container"
        return 1
      fi
    fi
  fi

  if ! printf '%s\n' "${CONTAINER_LIST}" | grep -qx "${GREMLIN_CONTAINER}"; then
    echo "[ERROR] Gremlin container is not running: ${GREMLIN_CONTAINER}"
    return 1
  fi

  echo "[INFO] Gremlin container: ${GREMLIN_CONTAINER}"

  echo "[INFO] Checking if graph already contains seeded data"
  local total_vertices=0
  local person_count=0
  local required_person_count=0

  if ! total_vertices="$(query_gremlin_scalar "g.V().count().next()")"; then
    echo "[WARN] Could not read total vertex count; seeding graph."
    total_vertices="0"
  fi
  if ! person_count="$(query_gremlin_scalar "g.V().hasLabel('person').count().next()")"; then
    echo "[WARN] Could not read person count; seeding graph."
    person_count="0"
  fi
  if [[ -n "${DEMO_REQUIRED_PERSON:-}" ]]; then
    if ! required_person_count="$(query_gremlin_scalar "g.V().hasLabel('person').has('name', '${DEMO_REQUIRED_PERSON}').count().next()")"; then
      echo "[WARN] Could not read required-person check; seeding decision will use graph cardinality only."
      required_person_count="0"
    fi
  fi

  if [[ -n "${DEMO_REQUIRED_PERSON:-}" ]]; then
    echo "[INFO] Current graph: vertices=${total_vertices}, persons=${person_count}, ${DEMO_REQUIRED_PERSON}=${required_person_count}"
  else
    echo "[INFO] Current graph: vertices=${total_vertices}, persons=${person_count}"
  fi

  local need_seed="false"
  if ! query_gremlin_ok "g.V().count().next()" "${DEMO_REQUIRED_MIN_VERTICES}" >/dev/null 2>&1; then
    need_seed="true"
  fi
  if ! query_gremlin_ok "g.V().hasLabel('person').count().next()" "${DEMO_REQUIRED_MIN_PERSONS}" >/dev/null 2>&1; then
    need_seed="true"
  fi
  if [[ -n "${DEMO_REQUIRED_PERSON:-}" ]] && ! query_gremlin_ok "g.V().hasLabel('person').has('name', '${DEMO_REQUIRED_PERSON}').count().next()" "1" >/dev/null 2>&1; then
    echo "[WARN] Required seed entity '${DEMO_REQUIRED_PERSON}' missing. Continuing with cardinality-based seeding guard."
  fi

  if [[ "${need_seed}" == "false" ]]; then
    echo "[PASS] Demo seed check passed"
    return 0
  fi

  echo "[WARN] Demo dataset missing/incomplete. Running deterministic seed load."
  if ! run_seed_step; then
    echo "[ERROR] Failed to seed demo dataset."
    return 1
  fi

  if ! query_gremlin_ok "g.V().count().next()" "${DEMO_REQUIRED_MIN_VERTICES}" >/dev/null 2>&1; then
    echo "[ERROR] Post-seed vertex check failed"
    return 1
  fi
  if ! query_gremlin_ok "g.V().hasLabel('person').count().next()" "${DEMO_REQUIRED_MIN_PERSONS}" >/dev/null 2>&1; then
    echo "[ERROR] Post-seed person check failed"
    return 1
  fi

  echo "[PASS] Demo graph seed completed."
  return 0
}

main "$@"
