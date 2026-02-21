#!/bin/bash
# =============================================================================
# Generate Determinism Manifest
# =============================================================================
# Purpose: Create comprehensive determinism manifest with checksums from all layers
# Usage:   ./scripts/testing/generate_determinism_manifest.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="${1:-${DEMO_FIXED_OUTPUT_ROOT:-${PROJECT_ROOT}/exports/deterministic}}"

mkdir -p "${OUTPUT_DIR}"

echo "Generating determinism manifest..."

# 1. Generator output checksums
echo "1. Generator outputs..."
if [ -d "${PROJECT_ROOT}/output" ]; then
    find "${PROJECT_ROOT}/output" -type f -name "*.json" -exec sha256sum {} \; > "${OUTPUT_DIR}/generator_outputs.sha256" 2>/dev/null || true
fi

# 2. Graph state checksums (requires JanusGraph)
echo "2. Graph state..."
echo "# JanusGraph vertex counts" > "${OUTPUT_DIR}/graph_state.sha256"
echo "g.V().count()=TBD" >> "${OUTPUT_DIR}/graph_state.sha256"

# 3. CQL data checksums (requires HCD)
echo "3. CQL data..."
echo "# HCD table counts" > "${OUTPUT_DIR}/cql_data.sha256"
echo "vertex.count=TBD" >> "${OUTPUT_DIR}/cql_data.sha256"

# 4. OpenSearch index checksums
echo "4. OpenSearch indices..."
echo "# OpenSearch document counts" > "${OUTPUT_DIR}/opensearch_indices.sha256"
echo "persons.count=TBD" >> "${OUTPUT_DIR}/opensearch_indices.sha256"

# 5. Create unified manifest
cat > "${OUTPUT_DIR}/determinism_manifest.json" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "seed": "${DEMO_SEED:-42}",
  "components": {
    "generator_outputs": "generator_outputs.sha256",
    "graph_state": "graph_state.sha256", 
    "cql_data": "cql_data.sha256",
    "opensearch_indices": "opensearch_indices.sha256"
  },
  "notes": "Run validation scripts to populate actual checksums"
}
EOF

echo "✅ Determinism manifest created: ${OUTPUT_DIR}/determinism_manifest.json"
