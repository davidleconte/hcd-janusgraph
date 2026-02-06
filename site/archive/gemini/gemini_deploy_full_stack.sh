#!/bin/bash
# Unified Deployment Script: HCD + JanusGraph + OpenSearch (Vector Stack)
# This script uses podman-compose to deploy the full integrated stack,
# ensuring configuration consistency and proper networking.
#
# Author: Gemini CLI Agent
# Date: 2026-01-28

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables
if [ -f ".env" ]; then
    source .env
else
    echo "⚠️ .env not found, using .env.example"
    source .env.example
fi

# Set defaults
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"
NETWORK_NAME="${NETWORK_NAME:-hcd-janusgraph-network}"

echo "==============================================================="
echo "Unified HCD + JanusGraph + OpenSearch Deployment"
echo "==============================================================="

# 1. Check podman connection
echo "Checking podman machine '$PODMAN_CONNECTION'வுகளை..."
if ! podman --remote --connection "$PODMAN_CONNECTION" ps >/dev/null 2>&1; then
    echo "❌ Podman machine '$PODMAN_CONNECTION' not accessible."
    exit 1
fi

# 2. Create Network if not exists
if ! podman --remote --connection "$PODMAN_CONNECTION" network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    echo "Creating network $NETWORK_NAME..."
    podman --remote --connection "$PODMAN_CONNECTION" network create "$NETWORK_NAME"
fi

# 3. Build Custom Images
echo "Building custom images (Jupyter, Visualizer, etc.)..."
# Note: Using the original Dockerfiles
podman --remote --connection "$PODMAN_CONNECTION" build -t localhost/jupyter-janusgraph:latest -f docker/jupyter/Dockerfile .
podman --remote --connection "$PODMAN_CONNECTION" build -t localhost/janusgraph-visualizer:latest -f docker/visualizer/Dockerfile .
podman --remote --connection "$PODMAN_CONNECTION" build -t localhost/graphexp:latest -f docker/graphexp/Dockerfile .
podman --remote --connection "$PODMAN_CONNECTION" build -t localhost/cqlsh-client:latest -f docker/cqlsh/Dockerfile .

# 4. Deploy Stack using podman-compose
echo "Deploying stack via podman-compose..."
# We combine the base, full (viz/monitoring), and banking (opensearch) compose files
podman-compose \
    -f config/compose/docker-compose.yml \
    -f config/compose/docker-compose.full.yml \
    -f config/compose/docker-compose.banking.yml \
    up -d

echo "==============================================================="
echo "✅ Deployment initiated."
echo "Wait a few minutes for services to stabilize."
echo ""
echo "Access points (default ports):"
echo "  - JanusGraph (Gremlin): ws://localhost:18182"
echo "  - Jupyter Lab:          http://localhost:8888"
echo "  - Grafana:              http://localhost:3001"
echo "  - OpenSearch:           (Use SSH Tunnel to 9200)"
echo "==============================================================="
