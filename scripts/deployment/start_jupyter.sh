#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/.env" || source "$PROJECT_ROOT/.env.example"
# Quick Start: Jupyter Lab for JanusGraph Analysis
# Platform: macOS M3 Pro, Podman

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables if .env exists
if [ -f ".env" ]; then
    source .env
fi

# Set defaults
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"
PODMAN_PLATFORM="${PODMAN_PLATFORM:-linux/arm64}"
JUPYTER_PORT="${JUPYTER_PORT:-8888}"
NETWORK_NAME="${NETWORK_NAME:-hcd-janusgraph-network}"

echo "🚀 Starting Jupyter Lab..."
echo ""

# Check if already running
if podman --remote --connection $PODMAN_CONNECTION ps | grep -q "jupyter-lab"; then
    echo "✅ Jupyter Lab is already running"
    echo "   Access: http://localhost:$JUPYTER_PORT"
    exit 0
fi
fi

# Check if image exists
if ! podman --remote --connection $PODMAN_CONNECTION images | grep -q "jupyter-janusgraph"; then
    echo "❌ Jupyter Lab image not found"
    echo "   Building image (this takes 5-10 minutes)..."
    podman --remote --connection $PODMAN_CONNECTION build \
        --platform $PODMAN_PLATFORM \
        -f Dockerfile.jupyter \
        -t localhost/jupyter-janusgraph:latest \
        .
    echo "✅ Image built successfully"
fi

# Start container
echo "Starting Jupyter Lab container..."
podman --remote --connection $PODMAN_CONNECTION run -d \
    --name jupyter-lab \
    --hostname jupyter-lab \
    --network hcd-janusgraph-network \
    -p 8888:8888 \
    -v "$SCRIPT_DIR/notebooks:/workspace/notebooks:Z" \
    -v "$SCRIPT_DIR/exports:/workspace/exports:Z" \
    -e GREMLIN_URL=ws://janusgraph-server:8182/gremlin \
    -e HCD_HOST=hcd-server \
    -e HCD_PORT=9042 \
    localhost/jupyter-janusgraph:latest

# Wait for startup
echo "Waiting for Jupyter Lab to start..."
sleep 5

echo ""
echo "=========================================="
echo "✅ Jupyter Lab Started!"
echo "=========================================="
echo ""
echo "📊 Access: http://localhost:8888"
echo ""
echo "📁 Notebooks: $SCRIPT_DIR/notebooks"
echo "📁 Exports:   $SCRIPT_DIR/exports"
echo ""
echo "🧪 Sample Notebook: 01_janusgraph_exploration.ipynb"
echo ""
echo "📖 Full Guide: FULL_STACK_ACCESS.md"
echo ""
echo "To stop:"
echo "  podman --remote --connection $PODMAN_CONNECTION stop jupyter-lab"
echo ""

# Open in browser
open http://localhost:8888 2>/dev/null || echo "Open manually: http://localhost:8888"
