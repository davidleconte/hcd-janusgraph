#!/bin/bash
# =============================================================================
# Validate JanusGraph Data via Gremlin
# =============================================================================
# Purpose: Validate data exists in JanusGraph after notebook execution
# Usage:   ./scripts/testing/validate_gremlin_data.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

source "${PROJECT_ROOT}/scripts/utils/podman_connection.sh"

PODMAN_CONNECTION="${PODMAN_CONNECTION:-}"
if ! PODMAN_CONNECTION="$(resolve_podman_connection "${PODMAN_CONNECTION}")"; then
    echo "ERROR: Unable to resolve podman connection"
    exit 1
fi

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"
CONTAINER_NAME="${COMPOSE_PROJECT_NAME}_gremlin-console_1"

echo "Validating JanusGraph data..."
echo "Container: ${CONTAINER_NAME}"

# Check if container exists
if ! podman --remote --connection "${PODMAN_CONNECTION}" ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: Gremlin console container not running"
    exit 1
fi

# Run Gremlin queries to validate data
echo "Checking vertex counts by label..."

podman --remote --connection "${PODMAN_CONNECTION}" exec -i "${CONTAINER_NAME}" ./bin/gremlin.sh 2>&1 <<'EOF' | grep -v "^SLF4J\|^Caused by\|^WARN" || true
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().count()
g.V().group().by(label).count()
g.E().count()
:quit
EOF

echo "Checking specific labels..."
podman --remote --connection "${PODMAN_CONNECTION}" exec -i "${CONTAINER_NAME}" ./bin/gremlin.sh 2>&1 <<'EOF' | grep -v "^SLF4J\|^Caused by\|^WARN" || true
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().hasLabel('Person').count()
g.V().hasLabel('Company').count()
g.V().hasLabel('Account').count()
:quit
EOF

echo "✅ JanusGraph data validation complete"
exit 0
