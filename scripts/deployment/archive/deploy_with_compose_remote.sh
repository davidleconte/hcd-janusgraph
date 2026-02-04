#!/bin/bash
# Deterministic Deployment Script using podman-compose
# PODMAN-WXD REMOTE VERSION - Ensures deployment on podman-wxd machine
# Ensures project isolation and reliable startup

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

# Set project name for isolation (REQUIRED per AGENTS.md)
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"

# Configure Podman connection for remote machine
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"

echo "=========================================="
echo "HCD + JanusGraph Stack Deployment"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Project Name: $COMPOSE_PROJECT_NAME"
echo "  Podman Connection: $PODMAN_CONNECTION"
echo "  Working Directory: $PROJECT_ROOT"
echo ""

# Step 1: Detect and configure Podman connection
echo "1. Detecting Podman connection..."

# Check if connection exists
if ! podman system connection list | grep -q "^${PODMAN_CONNECTION}"; then
    echo "❌ ERROR: Podman connection '${PODMAN_CONNECTION}' not found"
    echo "   Available connections:"
    podman system connection list
    exit 1
fi

# Get the socket URI for the connection
CONTAINER_HOST=$(podman system connection list --format json | jq -r ".[] | select(.Name == \"${PODMAN_CONNECTION}\") | .URI")

if [ -z "$CONTAINER_HOST" ]; then
    echo "❌ ERROR: Could not retrieve socket URI for connection '${PODMAN_CONNECTION}'"
    exit 1
fi

# Export for podman-compose
export CONTAINER_HOST

echo "✅ Podman connection configured"
echo "   Connection: $PODMAN_CONNECTION"
echo "   Socket: $CONTAINER_HOST"
echo ""

# Step 2: Validate connection
echo "2. Validating remote connection..."

if ! podman info > /dev/null 2>&1; then
    echo "❌ ERROR: Cannot connect to Podman machine"
    echo "   Check if podman machine is running:"
    echo "   podman machine list"
    echo "   Start with: podman machine start ${PODMAN_CONNECTION}"
    exit 1
fi

# Get machine info
MACHINE_NAME=$(podman info --format json | jq -r '.host.remoteSocket.path' 2>/dev/null || echo "local")
echo "✅ Connected to Podman machine"
echo "   Machine: $MACHINE_NAME"
echo ""

# Change to compose directory (REQUIRED - relative Dockerfile paths)
cd "$PROJECT_ROOT/config/compose"

# Step 3: Clean up any existing containers
echo "3. Cleaning up existing containers..."
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.full.yml down -v 2>/dev/null || true
echo "✅ Cleanup complete"
echo ""

# Step 4: Build all images (use cache for speed)
echo "4. Building container images..."
echo "   NOTE: Building on remote machine may take longer"
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.full.yml build
echo "✅ Images built"
echo ""

# Step 5: Start core services first (HCD, Vault)
echo "5. Starting core services (HCD, Vault)..."
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.full.yml up -d hcd-server vault
echo "   Waiting for HCD to be healthy (60s)..."
sleep 60

# Step 6: Initialize Vault if not already done
echo "6. Checking Vault initialization..."
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

# Step 7: Start remaining services
echo "7. Starting all remaining services..."
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.full.yml up -d
echo "✅ All services started"
echo ""

# Step 8: Wait for services to be ready
echo "8. Waiting for services to be ready..."
echo "   Expected startup times:"
echo "   • HCD:              Already running"
echo "   • JanusGraph:       20-60 seconds"
echo "   • Visualization:    10-30 seconds"
echo "   • Monitoring:       10-20 seconds"
echo ""
echo "   Waiting 60 seconds for initialization..."
sleep 60
echo ""

# Step 9: Validate services on remote machine
echo "9. Validating services on remote machine..."
echo "   Checking containers on: $PODMAN_CONNECTION"
FAILED_SERVICES=()

# Check each critical service
for service in hcd-server janusgraph-server vault prometheus grafana; do
    CONTAINER_NAME="${COMPOSE_PROJECT_NAME}_${service}_1"
    if ! podman ps --filter "name=$CONTAINER_NAME" --filter "status=running" | grep -q "$service"; then
        FAILED_SERVICES+=("$service")
        echo "   ❌ $service not running"
    else
        echo "   ✅ $service running"
        # Show which machine the container is on
        CONTAINER_HOST_INFO=$(podman inspect $CONTAINER_NAME --format '{{.HostConfig.NetworkMode}}' 2>/dev/null || echo "unknown")
        echo "      Network: $CONTAINER_HOST_INFO"
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
echo "Podman Machine: $PODMAN_CONNECTION"
echo ""
echo "📊 WEB INTERFACES:"
echo "   Jupyter Lab:           http://localhost:8888"
echo "   JanusGraph Visualizer: http://localhost:3000"
echo "   Graphexp:              http://localhost:8080"
echo "   Grafana:               http://localhost:3001 (admin/admin)"
echo "   Prometheus:            http://localhost:9090"
echo "   Vault:                 http://localhost:8200"
echo ""
echo "🔌 API ENDPOINTS:"
echo "   JanusGraph Gremlin:    ws://localhost:18182/gremlin"
echo "   HCD CQL:               localhost:19042"
echo ""
echo "💻 CLI ACCESS:"
echo "   Gremlin Console:"
echo "     podman exec -it ${COMPOSE_PROJECT_NAME}_janusgraph-server_1 ./bin/gremlin.sh"
echo ""
echo "   CQL Shell:"
echo "     podman exec -it ${COMPOSE_PROJECT_NAME}_cqlsh-client_1 cqlsh"
echo ""
echo "🛑 TO STOP:"
echo "   cd config/compose && CONTAINER_HOST=$CONTAINER_HOST podman-compose -p $COMPOSE_PROJECT_NAME down"
echo ""
echo "🔐 VAULT KEYS:"
echo "   Location: $PROJECT_ROOT/.vault-keys/"
echo "   ⚠️  Keep these secure! Add .vault-keys/ to .gitignore"
echo ""
echo "ℹ️  NOTE: All containers are running on Podman machine: $PODMAN_CONNECTION"
echo ""
