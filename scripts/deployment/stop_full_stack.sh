#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/.env" || source "$PROJECT_ROOT/.env.example"
# Stop Full HCD + JanusGraph Visualization Stack

# Load environment variables if .env exists
if [ -f ".env" ]; then
    source .env
fi

# Set defaults
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"

echo "Stopping all containers..."

# Stop visualization containers
podman --remote --connection $PODMAN_CONNECTION stop jupyter-lab janusgraph-visualizer graphexp cqlsh-client 2>/dev/null || true

# Stop monitoring containers
podman --remote --connection $PODMAN_CONNECTION stop prometheus grafana 2>/dev/null || true

# Stop core containers (optional - uncomment if needed)
# podman --remote --connection $PODMAN_CONNECTION stop janusgraph-server hcd-server 2>/dev/null || true

echo "✅ Visualization and monitoring containers stopped"
echo ""
echo "Core containers (HCD + JanusGraph) are still running."
echo "To stop them as well:"
echo "  podman --remote --connection $PODMAN_CONNECTION stop janusgraph-server hcd-server"
echo ""
echo "To remove stopped containers:"
echo "  podman --remote --connection $PODMAN_CONNECTION rm jupyter-lab janusgraph-visualizer graphexp cqlsh-client prometheus grafana"
