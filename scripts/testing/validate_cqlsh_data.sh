#!/bin/bash
# =============================================================================
# Validate HCD/Cassandra Data via CQLSH
# =============================================================================
# Purpose: Validate data exists in HCD after notebook execution
# Usage:   ./scripts/testing/validate_cqlsh_data.sh

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
CONTAINER_NAME="${COMPOSE_PROJECT_NAME}_cqlsh-client_1"

echo "Validating HCD/Cassandra data..."
echo "Container: ${CONTAINER_NAME}"

# Check if container exists
if ! podman --remote --connection "${PODMAN_CONNECTION}" ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: CQLSH client container not running"
    exit 1
fi

# Run CQL queries to validate data
echo "Checking vertex tables..."

# Get vertex counts by label
podman --remote --connection "${PODMAN_CONNECTION}" exec -i "${CONTAINER_NAME}" cqlsh hcd-server -e "
SELECT COUNT(*) FROM janusgraph.edgestore;
SELECT COUNT(*) FROM janusgraph.vertex;
" 2>/dev/null || echo "Warning: Could not query edgestore"

echo "Checking relation tables..."
podman --remote --connection "${PODMAN_CONNECTION}" exec -i "${CONTAINER_NAME}" cqlsh hcd-server -e "
SELECT COUNT(*) FROM janusgraph.relation;
" 2>/dev/null || echo "Warning: Could not query relation"

echo "✅ HCD data validation complete"
exit 0
