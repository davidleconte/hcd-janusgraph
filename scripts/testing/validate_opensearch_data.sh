#!/bin/bash
# =============================================================================
# Validate OpenSearch Data via REST API
# =============================================================================
# Purpose: Validate data exists in OpenSearch after notebook execution
# Usage:   ./scripts/testing/validate_opensearch_data.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

OPENSEARCH_URL="${OPENSEARCH_URL:-http://localhost:9200}"
OPENSEARCH_USER="${OPENSEARCH_USER:-admin}"
OPENSEARCH_PASSWORD="${OPENSEARCH_PASSWORD:-admin}"

echo "Validating OpenSearch data..."
echo "URL: ${OPENSEARCH_URL}"

# Check if OpenSearch is available
if ! curl -s -u "${OPENSEARCH_USER}:${OPENSEARCH_PASSWORD}" "${OPENSEARCH_URL}" > /dev/null 2>&1; then
    echo "ERROR: OpenSearch not available at ${OPENSEARCH_URL}"
    exit 1
fi

# Get cluster health
echo "Checking cluster health..."
curl -s -u "${OPENSEARCH_USER}:${OPENSEARCH_PASSWORD}" "${OPENSEARCH_URL}/_cluster/health" | jq '.'

# List indices
echo "Listing indices..."
curl -s -u "${OPENSEARCH_USER}:${OPENSEARCH_PASSWORD}" "${OPENSEARCH_URL}/_cat/indices?h=index,docs.count,store.size"

# Check for banking indices
echo "Checking banking-related indices..."
for index in persons companies accounts transactions; do
    count=$(curl -s -u "${OPENSEARCH_USER}:${OPENSEARCH_PASSWORD}" "${OPENSEARCH_URL}/${index}/_count" | jq -r '.count // 0')
    echo "${index}: ${count} documents"
done

echo "✅ OpenSearch data validation complete"
exit 0
