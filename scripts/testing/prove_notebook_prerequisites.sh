#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "${PROJECT_ROOT}/scripts/utils/podman_connection.sh"

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"
PODMAN_CONNECTION_VALUE="${PODMAN_CONNECTION:-}"
REPORT_PATH_HOST="${PROJECT_ROOT}/exports/notebook-prereq-proof.json"

usage() {
  cat <<'EOF'
Usage: scripts/testing/prove_notebook_prerequisites.sh [--report <path>]

Runs deterministic notebook prerequisite checks and proofs:
1) HCD/Cassandra storage checks via cqlsh
2) JanusGraph traversal checks via gremlin-python
3) OpenSearch indexing + sanctions baseline seed + relevance assertions
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --report)
      if [[ $# -lt 2 ]]; then
        echo "--report requires a path"
        exit 2
      fi
      REPORT_PATH_HOST="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 2
      ;;
  esac
done

if [[ "${REPORT_PATH_HOST}" != /* ]]; then
  REPORT_PATH_HOST="${PROJECT_ROOT}/${REPORT_PATH_HOST}"
fi
REPORT_PATH_HOST="$(cd "$(dirname "${REPORT_PATH_HOST}")" && pwd)/$(basename "${REPORT_PATH_HOST}")"

PODMAN_CONNECTION_VALUE="$(resolve_podman_connection "${PODMAN_CONNECTION_VALUE}")"

CONTAINER_LIST="$(
  podman --remote --connection "${PODMAN_CONNECTION_VALUE}" ps --format '{{.Names}}'
)"

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

require_running_container() {
  local name="$1"
  local label="$2"
  if [[ -z "${name}" ]]; then
    echo "❌ Unable to resolve ${label} container."
    exit 1
  fi
  if ! printf '%s\n' "${CONTAINER_LIST}" | grep -qx "${name}"; then
    echo "❌ ${label} container is not running: ${name}"
    exit 1
  fi
}

HCD_CONTAINER="$(resolve_container_name hcd-server || true)"
CQL_CONTAINER="$(resolve_container_name cqlsh-client || true)"
JUPYTER_CONTAINER="$(resolve_container_name jupyter || true)"
if [[ -z "${JUPYTER_CONTAINER}" ]]; then
  JUPYTER_CONTAINER="$(resolve_container_name jupyter-lab || true)"
fi
OPENSEARCH_CONTAINER="$(resolve_container_name opensearch || true)"

require_running_container "${HCD_CONTAINER}" "HCD"
require_running_container "${CQL_CONTAINER}" "CQL client"
require_running_container "${JUPYTER_CONTAINER}" "Jupyter"
require_running_container "${OPENSEARCH_CONTAINER}" "OpenSearch"

cql_query() {
  local cql="$1"
  podman --remote --connection "${PODMAN_CONNECTION_VALUE}" exec "${CQL_CONTAINER}" \
    cqlsh hcd-server -e "${cql}"
}

cql_scalar() {
  local output="$1"
  echo "${output}" | awk '/^[[:space:]]*[0-9]+[[:space:]]*$/{print $1; exit}'
}

edgestore_rows="$(
  cql_scalar "$(cql_query "SELECT COUNT(*) FROM janusgraph.edgestore;")"
)"
id_rows="$(
  cql_scalar "$(cql_query "SELECT COUNT(*) FROM janusgraph.janusgraph_ids;")"
)"
graphindex_rows="$(
  cql_scalar "$(cql_query "SELECT COUNT(*) FROM janusgraph.graphindex;")"
)"

if [[ -z "${edgestore_rows}" || -z "${id_rows}" || -z "${graphindex_rows}" ]]; then
  echo "❌ Failed to read deterministic CQL proof counts."
  exit 1
fi

if [[ "${REPORT_PATH_HOST}" == "${PROJECT_ROOT}"/* ]]; then
  REPORT_PATH_CONTAINER="/workspace/${REPORT_PATH_HOST#${PROJECT_ROOT}/}"
else
  echo "❌ Report path must be inside project root: ${PROJECT_ROOT}"
  exit 1
fi

mkdir -p "$(dirname "${REPORT_PATH_HOST}")"

echo "========================================"
echo "Notebook Prerequisite Proof"
echo "========================================"
echo "Podman connection:  ${PODMAN_CONNECTION_VALUE}"
echo "Project name:       ${COMPOSE_PROJECT_NAME}"
echo "CQL container:      ${CQL_CONTAINER}"
echo "Jupyter container:  ${JUPYTER_CONTAINER}"
echo "OpenSearch container:${OPENSEARCH_CONTAINER}"
echo "Report path:        ${REPORT_PATH_HOST}"
echo ""
echo "1) HCD/Cassandra storage checks"
echo "   edgestore_rows=${edgestore_rows}"
echo "   janusgraph_ids_rows=${id_rows}"
echo "   graphindex_rows=${graphindex_rows}"
echo ""

podman --remote --connection "${PODMAN_CONNECTION_VALUE}" exec \
  -e "PYTHONHASHSEED=0" \
  -e "TZ=UTC" \
  -e "DEMO_CQL_EDGESTORE_ROWS=${edgestore_rows}" \
  -e "DEMO_CQL_ID_ROWS=${id_rows}" \
  -e "DEMO_CQL_GRAPHINDEX_ROWS=${graphindex_rows}" \
  -e "DEMO_PROOF_REPORT_PATH=${REPORT_PATH_CONTAINER}" \
  "${JUPYTER_CONTAINER}" \
  bash -lc "cd /workspace && conda run -n janusgraph-analysis python - <<'PY'
import json
import os
from datetime import datetime, timezone

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from opensearchpy import OpenSearch

from banking.aml.sanctions_screening import SanctionsScreener


def as_int(name: str) -> int:
    return int(os.environ.get(name, '0'))


def main() -> None:
    report_path = os.environ['DEMO_PROOF_REPORT_PATH']
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    cql_counts = {
        'edgestore_rows': as_int('DEMO_CQL_EDGESTORE_ROWS'),
        'janusgraph_ids_rows': as_int('DEMO_CQL_ID_ROWS'),
        'graphindex_rows': as_int('DEMO_CQL_GRAPHINDEX_ROWS'),
    }

    g = traversal().withRemote(
        DriverRemoteConnection('ws://janusgraph-server:8182/gremlin', 'g')
    )
    janusgraph_counts = {
        'vertices': int(g.V().count().next()),
        'edges': int(g.E().count().next()),
        'persons': int(g.V().hasLabel('person').count().next()),
        'companies': int(g.V().hasLabel('company').count().next()),
        'accounts': int(g.V().hasLabel('account').count().next()),
    }

    if janusgraph_counts['vertices'] <= 0 or janusgraph_counts['edges'] <= 0:
        raise SystemExit('Graph cardinality check failed: expected non-zero vertices and edges')

    os_client = OpenSearch(
        hosts=[{'host': 'opensearch', 'port': 9200}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
    )

    indices = os_client.cat.indices(format='json')
    index_counts = {
        row.get('index'): int(row.get('docs.count', '0') or 0)
        for row in indices
        if row.get('index') and not row.get('index', '').startswith('.')
    }

    sanctions_index = 'sanctions_list'
    if os_client.indices.exists(index=sanctions_index):
        os_client.indices.delete(index=sanctions_index)

    screener = SanctionsScreener(
        opensearch_host='opensearch',
        opensearch_port=9200,
        index_name=sanctions_index,
    )

    sanctions_data = [
        {
            'name': 'John Doe',
            'entity_id': 'SANC-001',
            'sanctions_list': 'OFAC',
            'entity_type': 'person',
            'country': 'US',
            'aliases': ['Jonathan Doe', 'J. Doe'],
            'date_added': '2024-01-15T00:00:00Z',
        },
        {
            'name': 'Jane Smith',
            'entity_id': 'SANC-002',
            'sanctions_list': 'UN',
            'entity_type': 'person',
            'country': 'UK',
            'aliases': ['J Smith'],
            'date_added': '2024-03-01T00:00:00Z',
        },
        {
            'name': 'Mohammed Al-Rashid',
            'entity_id': 'SANC-003',
            'sanctions_list': 'EU',
            'entity_type': 'person',
            'country': 'SY',
            'aliases': ['M. Al Rashid'],
            'date_added': '2023-11-10T00:00:00Z',
        },
        {
            'name': 'Global Trade Front LLC',
            'entity_id': 'SANC-004',
            'sanctions_list': 'OFAC',
            'entity_type': 'company',
            'country': 'AE',
            'aliases': ['GTF LLC'],
            'date_added': '2023-09-22T00:00:00Z',
        },
        {
            'name': 'Ivan Petrov',
            'entity_id': 'SANC-005',
            'sanctions_list': 'UK-HMT',
            'entity_type': 'person',
            'country': 'RU',
            'aliases': ['I. Petrov'],
            'date_added': '2024-02-05T00:00:00Z',
        },
        {
            'name': 'Baltic Shadow Shipping',
            'entity_id': 'SANC-006',
            'sanctions_list': 'UN',
            'entity_type': 'company',
            'country': 'PA',
            'aliases': ['BSS'],
            'date_added': '2023-12-17T00:00:00Z',
        },
    ]

    loaded = screener.load_sanctions_list(sanctions_data)
    stats = screener.get_statistics()
    if loaded != len(sanctions_data):
        raise SystemExit(f'Sanctions load mismatch: expected {len(sanctions_data)}, got {loaded}')
    if stats.get('total_entities') != len(sanctions_data):
        raise SystemExit(
            f\"Sanctions index count mismatch: expected {len(sanctions_data)}, got {stats.get('total_entities')}\"
        )

    by_list_resp = os_client.search(
        index=sanctions_index,
        body={
            'size': 0,
            'aggs': {'by_list': {'terms': {'field': 'sanctions_list', 'size': 20}}},
        },
    )
    by_list = {
        b['key']: int(b['doc_count'])
        for b in by_list_resp['aggregations']['by_list']['buckets']
    }

    term_resp = os_client.search(
        index=sanctions_index,
        body={'query': {'term': {'name.keyword': 'John Doe'}}, 'size': 1},
    )
    exact_term_hits = int(term_resp['hits']['total']['value'])
    if exact_term_hits < 1:
        raise SystemExit('OpenSearch exact term query failed for John Doe')

    exact = screener.screen_customer(customer_id='T-001', customer_name='John Doe')
    fuzzy = screener.screen_customer(customer_id='T-002', customer_name='Jon Doe')
    abbr = screener.screen_customer(customer_id='T-003', customer_name='J. Doe')
    clear = screener.screen_customer(customer_id='T-004', customer_name='Alice Johnson')

    if not exact.is_match or not exact.matches or exact.matches[0].sanctioned_name != 'John Doe':
        raise SystemExit('Exact sanctions relevance check failed for John Doe')
    if exact.matches[0].similarity_score < 0.95:
        raise SystemExit('Exact sanctions score below 0.95 threshold')
    if not fuzzy.matches or fuzzy.matches[0].similarity_score < 0.80:
        raise SystemExit('Fuzzy sanctions score below 0.80 threshold for Jon Doe')
    if not abbr.matches or abbr.matches[0].similarity_score < 0.80:
        raise SystemExit('Abbreviated sanctions score below 0.80 threshold for J. Doe')
    if clear.is_match:
        raise SystemExit('False-positive sanctions match for Alice Johnson')

    proof = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'PASS',
        'cql_storage_counts': cql_counts,
        'janusgraph_counts': janusgraph_counts,
        'opensearch': {
            'index_counts': index_counts,
            'sanctions_stats': stats,
            'sanctions_by_list': by_list,
            'exact_term_hits_john_doe': exact_term_hits,
            'screening_checks': {
                'john_doe': {
                    'is_match': exact.is_match,
                    'top_name': exact.matches[0].sanctioned_name if exact.matches else None,
                    'top_score': round(exact.matches[0].similarity_score, 4) if exact.matches else 0.0,
                    'risk': exact.matches[0].risk_level if exact.matches else 'none',
                },
                'jon_doe': {
                    'is_match': fuzzy.is_match,
                    'top_name': fuzzy.matches[0].sanctioned_name if fuzzy.matches else None,
                    'top_score': round(fuzzy.matches[0].similarity_score, 4) if fuzzy.matches else 0.0,
                    'risk': fuzzy.matches[0].risk_level if fuzzy.matches else 'none',
                },
                'j_doe': {
                    'is_match': abbr.is_match,
                    'top_name': abbr.matches[0].sanctioned_name if abbr.matches else None,
                    'top_score': round(abbr.matches[0].similarity_score, 4) if abbr.matches else 0.0,
                    'risk': abbr.matches[0].risk_level if abbr.matches else 'none',
                },
                'alice_johnson': {
                    'is_match': clear.is_match,
                    'top_name': clear.matches[0].sanctioned_name if clear.matches else None,
                    'top_score': round(clear.matches[0].similarity_score, 4) if clear.matches else 0.0,
                    'risk': clear.matches[0].risk_level if clear.matches else 'none',
                },
            },
        },
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(proof, f, indent=2, sort_keys=True)

    print('✅ Notebook prerequisite proof complete')
    print(f\"   report={report_path}\")
    print(
        f\"   graph_vertices={janusgraph_counts['vertices']} graph_edges={janusgraph_counts['edges']} \"
        f\"sanctions_entities={stats['total_entities']}\"
    )


if __name__ == '__main__':
    main()
PY"

echo ""
echo "✅ Notebook prerequisite proof complete"
echo "   ${REPORT_PATH_HOST}"
