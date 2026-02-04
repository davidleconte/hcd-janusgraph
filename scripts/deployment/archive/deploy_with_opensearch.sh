#!/bin/bash
# Full Stack Deployment with OpenSearch + JVector Plugin
# Combines docker-compose.full.yml + docker-compose.banking.yml

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
else
    echo "⚠️  No .env file found, using .env.example defaults"
    source "$PROJECT_ROOT/.env.example"
fi

# Validate OpenSearch password
if [ -z "${OPENSEARCH_ADMIN_PASSWORD:-}" ] || [ "$OPENSEARCH_ADMIN_PASSWORD" = "YOUR_SECURE_PASSWORD_HERE_MINIMUM_12_CHARACTERS" ]; then
    echo "❌ ERROR: OPENSEARCH_ADMIN_PASSWORD not set or using default"
    echo "   Set a secure password in .env file:"
    echo "   OPENSEARCH_ADMIN_PASSWORD=your-secure-password-min-12-chars"
    exit 1
fi

# Set project name for isolation (REQUIRED per AGENTS.md)
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"

echo "=========================================="
echo "HCD + JanusGraph + OpenSearch Stack"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Project Name: $COMPOSE_PROJECT_NAME"
echo "  Working Directory: $PROJECT_ROOT"
echo ""

# Change to compose directory (REQUIRED - relative Dockerfile paths)
cd "$PROJECT_ROOT/config/compose"

# Step 1: Clean up any existing containers
echo "1. Cleaning up existing containers..."
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.full.yml down -v 2>/dev/null || true
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.banking.yml down -v 2>/dev/null || true
echo "✅ Cleanup complete"
echo ""

# Step 2: Build all images
echo "2. Building container images..."
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.full.yml build
echo "✅ Images built"
echo ""

# Step 3: Start core services first (HCD, Vault)
echo "3. Starting core services (HCD, Vault)..."
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.full.yml up -d hcd-server vault
echo "   Waiting for HCD to be healthy (60s)..."
sleep 60

# Step 4: Initialize Vault if not already done
echo "4. Checking Vault initialization..."
if podman exec ${COMPOSE_PROJECT_NAME}_vault_1 vault status 2>&1 | grep -q "not initialized"; then
    echo "   Initializing Vault..."
    VAULT_INIT=$(podman exec ${COMPOSE_PROJECT_NAME}_vault_1 vault operator init -key-shares=1 -key-threshold=1 -format=json)
    VAULT_UNSEAL_KEY=$(echo "$VAULT_INIT" | jq -r '.unseal_keys_b64[0]')
    VAULT_ROOT_TOKEN=$(echo "$VAULT_INIT" | jq -r '.root_token')
    
    # Save to secure location
    mkdir -p "$PROJECT_ROOT/.vault-keys"
    chmod 700 "$PROJECT_ROOT/.vault-keys"
    echo "$VAULT_UNSEAL_KEY" > "$PROJECT_ROOT/.vault-keys/unseal-key"
    echo "$VAULT_ROOT_TOKEN" > "$PROJECT_ROOT/.vault-keys/root-token"
    chmod 600 "$PROJECT_ROOT/.vault-keys"/*
    
    # Unseal Vault
    podman exec ${COMPOSE_PROJECT_NAME}_vault_1 vault operator unseal "$VAULT_UNSEAL_KEY"
    echo "   ✅ Vault initialized and unsealed"
    echo "   ⚠️  IMPORTANT: Vault keys saved to $PROJECT_ROOT/.vault-keys/"
else
    echo "   Vault already initialized"
    # Try to unseal if sealed
    if podman exec ${COMPOSE_PROJECT_NAME}_vault_1 vault status 2>&1 | grep -q "Sealed.*true"; then
        if [ -f "$PROJECT_ROOT/.vault-keys/unseal-key" ]; then
            VAULT_UNSEAL_KEY=$(cat "$PROJECT_ROOT/.vault-keys/unseal-key")
            podman exec ${COMPOSE_PROJECT_NAME}_vault_1 vault operator unseal "$VAULT_UNSEAL_KEY"
            echo "   ✅ Vault unsealed"
        else
            echo "   ⚠️  Vault is sealed but unseal key not found. Manual unseal required."
        fi
    fi
fi
echo ""

# Step 5: Start OpenSearch (before JanusGraph - it may use it as index backend)
echo "5. Starting OpenSearch..."
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.banking.yml up -d opensearch
echo "   Waiting for OpenSearch to be healthy (60s)..."
sleep 60
echo "✅ OpenSearch started"
echo ""

# Step 6: Install JVector plugin
echo "6. Installing JVector plugin..."
if podman exec ${COMPOSE_PROJECT_NAME}_opensearch_1 test -f /tmp/jvector-install.sh; then
    echo "   Running JVector installation script..."
    podman exec ${COMPOSE_PROJECT_NAME}_opensearch_1 bash /tmp/jvector-install.sh
    echo "   ✅ JVector plugin installed"
    echo "   Restarting OpenSearch to load plugin..."
    podman restart ${COMPOSE_PROJECT_NAME}_opensearch_1
    sleep 30
    echo "   ✅ OpenSearch restarted"
else
    echo "   ⚠️  JVector install script not found at /tmp/jvector-install.sh"
    echo "   Check: config/opensearch/jvector-install.sh exists and is mounted"
fi
echo ""

# Step 7: Start remaining services
echo "7. Starting all remaining services..."
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.full.yml up -d
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.banking.yml up -d opensearch-dashboards
echo "✅ All services started"
echo ""

# Step 8: Wait for services to be ready
echo "8. Waiting for services to be ready..."
echo "   Expected startup times:"
echo "   • HCD:              Already running"
echo "   • OpenSearch:       Already running"
echo "   • JanusGraph:       20-60 seconds"
echo "   • Visualization:    10-30 seconds"
echo "   • Monitoring:       10-20 seconds"
echo ""
echo "   Waiting 60 seconds for initialization..."
sleep 60
echo ""

# Step 9: Validate services
echo "9. Validating service health..."
FAILED_SERVICES=()

# Check each critical service
for service in hcd-server janusgraph-server vault prometheus grafana opensearch; do
    CONTAINER_NAME="${COMPOSE_PROJECT_NAME}_${service}_1"
    if ! podman ps --filter "name=$CONTAINER_NAME" --filter "status=running" | grep -q "$service"; then
        FAILED_SERVICES+=("$service")
        echo "   ❌ $service not running"
    else
        echo "   ✅ $service running"
    fi
done

echo ""

if [ ${#FAILED_SERVICES[@]} -gt 0 ]; then
    echo "=========================================="
    echo "⚠️  DEPLOYMENT INCOMPLETE"
    echo "=========================================="
    echo ""
    echo "Failed services: ${FAILED_SERVICES[*]}"
    echo ""
    echo "To debug, check logs:"
    for service in "${FAILED_SERVICES[@]}"; do
        echo "  podman logs ${COMPOSE_PROJECT_NAME}_${service}_1"
    done
    echo ""
    exit 1
fi

# Display access information
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "Project: $COMPOSE_PROJECT_NAME"
echo ""
echo "📊 WEB INTERFACES:"
echo "   Jupyter Lab:           http://localhost:8888"
echo "   JanusGraph Visualizer: http://localhost:3000"
echo "   Graphexp:              http://localhost:8080"
echo "   Grafana:               http://localhost:3001 (admin/admin)"
echo "   Prometheus:            http://localhost:9090"
echo "   Vault:                 http://localhost:8200"
echo ""
echo "🔍 OPENSEARCH (Banking Features):"
echo "   OpenSearch API:        SSH Tunnel Required (security)"
echo "   OpenSearch Dashboards: SSH Tunnel Required (security)"
echo ""
echo "   To access OpenSearch locally:"
echo "   1. Expose ports temporarily:"
echo "      cd config/compose"
echo "      # Uncomment ports in docker-compose.banking.yml"
echo "      podman-compose -p $COMPOSE_PROJECT_NAME restart opensearch opensearch-dashboards"
echo ""
echo "   2. OR use SSH tunnel (recommended):"
echo "      ssh -L 9200:localhost:9200 -L 5601:localhost:5601 user@host"
echo ""
echo "🔌 API ENDPOINTS:"
echo "   JanusGraph Gremlin:    ws://localhost:18182/gremlin"
echo "   HCD CQL:               localhost:19042"
echo "   OpenSearch:            http://localhost:9200 (via tunnel)"
echo ""
echo "💻 CLI ACCESS:"
echo "   Gremlin Console:"
echo "     podman exec -it ${COMPOSE_PROJECT_NAME}_janusgraph-server_1 ./bin/gremlin.sh"
echo ""
echo "   CQL Shell:"
echo "     podman exec -it ${COMPOSE_PROJECT_NAME}_cqlsh-client_1 cqlsh"
echo ""
echo "   OpenSearch CLI:"
echo "     podman exec -it ${COMPOSE_PROJECT_NAME}_opensearch_1 bash"
echo ""
echo "🛑 TO STOP:"
echo "   cd config/compose"
echo "   podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml down"
echo "   podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.banking.yml down"
echo ""
echo "🔐 CREDENTIALS:"
echo "   Vault keys: $PROJECT_ROOT/.vault-keys/"
echo "   OpenSearch: admin / \$OPENSEARCH_ADMIN_PASSWORD"
echo ""
