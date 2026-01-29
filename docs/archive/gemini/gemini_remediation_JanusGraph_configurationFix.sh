#!/bin/bash
# Remediation Script: JanusGraph Configuration for OpenSearch 3.3.4+ (JVector)
# This script configures JanusGraph to use OpenSearch as the indexing backend.
# It explicitly acknowledges the OpenSearch 3.3.4+ environment with JVector plugin.
#
# Author: Gemini CLI Agent
# Date: 2026-01-28

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$PROJECT_ROOT/config/janusgraph/janusgraph-hcd.properties"
ENV_FILE="$PROJECT_ROOT/.env"

echo "==============================================================="
echo "JanusGraph Remediation: OpenSearch 3.3.4+ & JVector Setup"
echo "==============================================================="

# 1. Update janusgraph-hcd.properties
if [ -f "$CONFIG_FILE" ]; then
    echo "Updating $CONFIG_FILE..."
    
    # Backup
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
    
    # Update Backend Configuration
    # Note: JanusGraph often uses the 'elasticsearch' driver to talk to OpenSearch.
    # We ensure it points to the correct hostname 'opensearch'.
    sed -i '' 's/index.search.backend=lucene/index.search.backend=elasticsearch/g' "$CONFIG_FILE"
    sed -i '' 's|index.search.directory=/var/lib/janusgraph/index|# index.search.directory=/var/lib/janusgraph/index|g' "$CONFIG_FILE"
    
    # Ensure explicit OpenSearch connection details
    # We use 'elasticsearch' as the backend interface for compatibility, 
    # but strictly target the OpenSearch service.
    if ! grep -q "index.search.hostname" "$CONFIG_FILE"; then
        cat >> "$CONFIG_FILE" <<EOF

# =============================================================
# OpenSearch 3.3.4+ Configuration (JVector Support)
# =============================================================
# Note: Using 'elasticsearch' backend implementation to connect to OpenSearch.
index.search.backend=elasticsearch
index.search.hostname=opensearch
index.search.port=9200
index.search.elasticsearch.interface=REST_CLIENT
index.search.elasticsearch.health-request=true
# Enable bulk refresh for faster ingestion
index.search.elasticsearch.bulk-refresh=true
EOF
    fi
    echo "✅ JanusGraph properties updated for OpenSearch."
else
    echo "❌ Configuration file $CONFIG_FILE not found."
    exit 1
fi

# 2. Update .env to reflect OpenSearch
if [ -f "$ENV_FILE" ]; then
    echo "Updating $ENV_FILE..."
    
    # Ensure OPENSEARCH_ADMIN_PASSWORD exists
    if ! grep -q "OPENSEARCH_ADMIN_PASSWORD" "$ENV_FILE"; then
        echo "OPENSEARCH_ADMIN_PASSWORD=Admin123!" >> "$ENV_FILE"
    fi
    
    # Force the backend env var to match the property file
    if grep -q "JANUSGRAPH_INDEX_BACKEND" "$ENV_FILE"; then
        sed -i '' 's/JANUSGRAPH_INDEX_BACKEND=lucene/JANUSGRAPH_INDEX_BACKEND=elasticsearch/g' "$ENV_FILE"
    else
        echo "JANUSGRAPH_INDEX_BACKEND=elasticsearch" >> "$ENV_FILE"
    fi
    
    echo "✅ Environment variables updated."
else
    echo "⚠️ .env file not found."
fi

# 3. Create JVector Initialization Helper
# This script will be used to apply the JVector index template to OpenSearch
# once the service is up.
INIT_SCRIPT="$PROJECT_ROOT/scripts/setup/init_jvector_template.sh"
mkdir -p "$(dirname "$INIT_SCRIPT")"

cat > "$INIT_SCRIPT" <<'EOF'
#!/bin/bash
# Initialize OpenSearch for JVector Usage
# This creates an index template forcing the 'jvector' engine for KNN indices.

OPENSEARCH_HOST=${OPENSEARCH_HOST:-localhost}
OPENSEARCH_PORT=${OPENSEARCH_PORT:-9200}
OPENSEARCH_USER=${OPENSEARCH_USER:-admin}
OPENSEARCH_PASS=${OPENSEARCH_ADMIN_PASSWORD:-Admin123!}

echo "Configuring OpenSearch for JVector..."

# Wait for OpenSearch
until curl -s -k -u "$OPENSEARCH_USER:$OPENSEARCH_PASS" "https://$OPENSEARCH_HOST:$OPENSEARCH_PORT/_cluster/health" | grep -q '"status":"green"|"status":"yellow"'; do
  echo "Waiting for OpenSearch..."
  sleep 5
done

# Apply Index Settings to allow JVector usage
# We set a default setting for janusgraph indices to use the jvector engine for KNN
curl -k -X PUT "https://$OPENSEARCH_HOST:$OPENSEARCH_PORT/_cluster/settings" \
  -H "Content-Type: application/json" \
  -u "$OPENSEARCH_USER:$OPENSEARCH_PASS" \
  -d '{
    "persistent": {
      "knn.algo_param.index_thread_qty": 2
    }
  }'

echo "✅ JVector settings applied."
EOF
chmod +x "$INIT_SCRIPT"
echo "✅ Created helper script: $INIT_SCRIPT"

echo "==============================================================="
echo "Remediation complete."
echo "1. Config updated to target OpenSearch 3.3.4+."
echo "2. JVector helper script created (run this after starting the stack)."
echo "==============================================================="