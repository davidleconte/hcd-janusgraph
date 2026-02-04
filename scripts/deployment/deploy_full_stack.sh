#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/.env" || source "$PROJECT_ROOT/.env.example"
# Deploy Full HCD + JanusGraph Visualization Stack
# Platform: macOS M3 Pro (Sequoia 26.2)
# Podman machine: configurable via .env

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables if .env exists
if [ -f ".env" ]; then
    source .env
fi

# Set defaults
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"
PODMAN_PLATFORM="${PODMAN_PLATFORM:-linux/arm64}"
HCD_CQL_PORT="${HCD_CQL_PORT:-19042}"
JANUSGRAPH_GREMLIN_PORT="${JANUSGRAPH_GREMLIN_PORT:-18182}"
JANUSGRAPH_MGMT_PORT="${JANUSGRAPH_MGMT_PORT:-18184}"
JUPYTER_PORT="${JUPYTER_PORT:-8888}"
VISUALIZER_PORT="${VISUALIZER_PORT:-3000}"
GRAPHEXP_PORT="${GRAPHEXP_PORT:-8080}"
PROMETHEUS_PORT="${PROMETHEUS_PORT:-9090}"
GRAFANA_PORT="${GRAFANA_PORT:-3001}"
NETWORK_NAME="${NETWORK_NAME:-hcd-janusgraph-network}"

echo "=========================================="
echo "HCD + JanusGraph Full Stack Deployment"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Podman Connection: $PODMAN_CONNECTION"
echo "  Platform: $PODMAN_PLATFORM"
echo ""

# Check podman-wxd is running
echo "1. Checking podman machine..."
if ! podman --remote --connection $PODMAN_CONNECTION ps >/dev/null 2>&1; then
    echo "❌ Podman machine '$PODMAN_CONNECTION' not accessible"
    echo "   Start it with: podman machine start $PODMAN_CONNECTION"
    exit 1
fi
echo "✅ Podman machine accessible"
echo ""

# Create exports directory
echo "2. Creating directories..."
mkdir -p exports notebooks
echo "✅ Directories created"
echo ""

# Build visualization images
echo "3. Building container images..."
echo "   This may take 10-15 minutes on first run..."

# Build Jupyter
echo "   Building Jupyter Lab (conda-forge)..."
# ============================================================================
# DEPLOYMENT
# ============================================================================
echo "3. Deploying Full Stack via Podman Compose..."
echo "   This will build custom images (OpenSearch w/ JVector, Visualization tools)"
echo "   and start all services with dependencies managed."

cd "$PROJECT_ROOT/config/compose"

# Set project name for isolation
export COMPOSE_PROJECT_NAME="janusgraph-demo"

# Run podman-compose
# --build ensures we pick up the new Dockerfiles (OpenSearch JVector, etc)
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d --build

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed."
    exit 1
fi

echo "✅ Deployment commands sent successfully."
echo ""
echo "   • Total Expected:     90-270 seconds (1.5-4.5 minutes)"
echo ""
echo "   Current wait: 90 seconds for core services..."
echo "   (Services continue initializing in background)"
echo ""
sleep 90
echo "✅ Core services should be ready (check health with: podman ps)"
echo ""

# Display access information
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "📊 WEB INTERFACES:"
echo "   Jupyter Lab:          http://localhost:$JUPYTER_PORT"
echo "   JanusGraph Visualizer: http://localhost:$VISUALIZER_PORT"
echo "   Graphexp:             http://localhost:$GRAPHEXP_PORT"
echo "   Grafana:              http://localhost:$GRAFANA_PORT (admin/admin)"
echo "   Prometheus:           http://localhost:$PROMETHEUS_PORT"
echo ""
echo "🔌 API ENDPOINTS:"
echo "   JanusGraph Gremlin:   ws://localhost:$JANUSGRAPH_GREMLIN_PORT/gremlin"
echo "   HCD CQL:              localhost:$HCD_CQL_PORT"
echo "   HCD JMX:              localhost:17199"
echo ""
echo "💻 CLI ACCESS:"
echo "   Gremlin Console:"
echo "     podman --remote --connection $PODMAN_CONNECTION exec -it janusgraph-server ./bin/gremlin.sh"
echo ""
echo "   CQL Shell:"
echo "     podman --remote --connection $PODMAN_CONNECTION exec -it cqlsh-client cqlsh"
echo ""
echo "📁 SHARED DIRECTORIES:"
echo "   Notebooks: $PWD/notebooks"
echo "   Exports:   $PWD/exports"
echo ""
echo "📖 See FULL_STACK_ACCESS.md for detailed documentation"
echo ""
echo "To stop all services:"
echo "   ./stop_full_stack.sh"
echo ""
