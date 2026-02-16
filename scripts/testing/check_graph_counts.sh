#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "${PROJECT_ROOT}/scripts/utils/podman_connection.sh"

# Validate HCD storage and JanusGraph traversal health in one command.

PODMAN_CONNECTION_VALUE="${PODMAN_CONNECTION:-}"
PODMAN_CONNECTION_VALUE="$(resolve_podman_connection "${PODMAN_CONNECTION_VALUE}")"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"

HCD_CONTAINER="${HCD_CONTAINER:-}"
CQL_CONTAINER="${CQL_CONTAINER:-}"
GREMLIN_CONTAINER="${GREMLIN_CONTAINER:-}"
CONTAINER_LIST=""

run_podman_ps() {
  podman --remote --connection "${PODMAN_CONNECTION_VALUE}" ps --format '{{.Names}}'
}

load_container_list() {
  if ! CONTAINER_LIST="$(run_podman_ps 2>&1)"; then
    echo "❌ Podman access failed for connection '${PODMAN_CONNECTION_VALUE}'"
    echo "❌ ${CONTAINER_LIST}"
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

container_is_running() {
  local name="$1"
  printf '%s\n' "${CONTAINER_LIST}" | grep -qx "${name}"
}

require_container_running() {
  local name="$1"
  local label="$2"

  if ! container_is_running "${name}"; then
    echo "❌ ${label} container is not running: ${name}"
    return 1
  fi
}

print_container_hint() {
  echo "💡 Running containers:"
  printf '%s\n' "${CONTAINER_LIST}" | sort | head -n 20
}

if ! load_container_list; then
  echo "❌ Verify Podman machine + socket path; environment example:"
    echo "   export PODMAN_CONNECTION=${PODMAN_CONNECTION_VALUE}"
    exit 1
fi

if [[ -z "${HCD_CONTAINER}" ]]; then
  if ! HCD_CONTAINER="$(resolve_container_name hcd-server)"; then
    echo "❌ Unable to resolve HCD container. Set HCD_CONTAINER explicitly."
    print_container_hint
    exit 1
  fi
elif ! container_is_running "${HCD_CONTAINER}"; then
  echo "❌ HCD_CONTAINER is set but not running: ${HCD_CONTAINER}"
  print_container_hint
  exit 1
fi

if [[ -z "${CQL_CONTAINER}" ]]; then
  if ! CQL_CONTAINER="$(resolve_container_name cqlsh-client)"; then
    echo "❌ Unable to resolve CQL client container. Set CQL_CONTAINER explicitly."
    print_container_hint
    exit 1
  fi
elif ! container_is_running "${CQL_CONTAINER}"; then
  echo "❌ CQL_CONTAINER is set but not running: ${CQL_CONTAINER}"
  print_container_hint
  exit 1
fi

if [[ -z "${GREMLIN_CONTAINER}" ]]; then
  if ! GREMLIN_CONTAINER="$(resolve_container_name jupyter)"; then
    if ! GREMLIN_CONTAINER="$(resolve_container_name gremlin-console)"; then
      if ! GREMLIN_CONTAINER="$(resolve_container_name jupyter-lab)"; then
        echo "❌ Unable to resolve a container for Gremlin checks. Set GREMLIN_CONTAINER explicitly."
        print_container_hint
        exit 1
      fi
    fi
  fi
elif ! container_is_running "${GREMLIN_CONTAINER}"; then
  echo "❌ GREMLIN_CONTAINER is set but not running: ${GREMLIN_CONTAINER}"
  print_container_hint
  exit 1
fi

echo "========================================"
echo "Live Graph Health Check"
echo "========================================"
echo "Podman connection: ${PODMAN_CONNECTION_VALUE}"
echo "CQL client:        ${CQL_CONTAINER}"
echo "HCD server:        ${HCD_CONTAINER}"
echo "Gremlin container:  ${GREMLIN_CONTAINER}"
echo ""

if ! require_container_running "${HCD_CONTAINER}" "HCD"; then
  print_container_hint
  exit 1
fi
if ! require_container_running "${CQL_CONTAINER}" "CQL"; then
  print_container_hint
  exit 1
fi
if ! require_container_running "${GREMLIN_CONTAINER}" "Gremlin"; then
  print_container_hint
  exit 1
fi

echo "✅ Containers are running"
echo ""

cql_query() {
  local cql="$1"
  podman --remote --connection "${PODMAN_CONNECTION_VALUE}" exec "${CQL_CONTAINER}" cqlsh hcd-server -e "${cql}"
}

cql_scalar() {
  local output="$1"
  echo "${output}" | awk '/^[[:space:]]*[0-9]+[[:space:]]*$/{print $1; exit}'
}

echo "1) Storage-layer checks (CQL)"
echo "   Keyspace: janusgraph"

raw_edge_rows="$(cql_query "SELECT COUNT(*) AS edge_rows FROM janusgraph.edgestore;")"
edge_rows="$(cql_scalar "${raw_edge_rows}")"

raw_id_rows="$(cql_query "SELECT COUNT(*) AS id_rows FROM janusgraph.janusgraph_ids;")"
id_rows="$(cql_scalar "${raw_id_rows}")"

raw_graphindex_rows="$(cql_query "SELECT COUNT(*) AS index_rows FROM janusgraph.graphindex;")"
graphindex_rows="$(cql_scalar "${raw_graphindex_rows}")"

echo "   - edgestore row count:     ${edge_rows:-N/A}"
echo "   - janusgraph_ids row count: ${id_rows:-N/A}"
echo "   - graphindex row count:    ${graphindex_rows:-N/A}"
echo ""

echo "2) Graph-layer checks (Gremlin)"
graph_counts="$(podman --remote --connection "${PODMAN_CONNECTION_VALUE}" exec "${GREMLIN_CONTAINER}" bash -lc "python - <<'PY'
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

g = traversal().withRemote(DriverRemoteConnection('ws://janusgraph-server:8182/gremlin', 'g'))
print(f\"vertices={g.V().count().next()}\")
print(f\"edges={g.E().count().next()}\")
PY")"

vertices="$(echo "${graph_counts}" | awk -F= '/^vertices=/{print $2}')"
edges="$(echo "${graph_counts}" | awk -F= '/^edges=/{print $2}')"

echo "   - vertex count: ${vertices:-N/A}"
echo "   - edge count:   ${edges:-N/A}"
echo ""

echo "3) Interpretation"
echo "   - edgestore_rows is a Cassandra storage statistic, not a direct JanusGraph edge count."
echo "   - janusgraph_ids approximates id/index metadata rows, not user entity records."
echo "   - graphindex_rows shows indexed property materialization volume."
echo "   - true entity/cardinality for demos is the Gremlin vertex and edge count above."

echo ""
echo "4) Demo health recommendation"
if [[ -n "${vertices:-}" && -n "${edges:-}" && "${vertices}" -gt 0 && "${edges}" -gt 0 ]]; then
  echo "   ✅ Graph has data and can answer traversals."
else
  echo "   ⚠️  Graph is empty or unreachable; expected >0 vertices and edges for full demos."
fi
