#!/bin/bash
# Cleanup Script - Removes all containers, networks, and volumes
# Use this when you need to completely reset the stack

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
fi

# Set project name
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"

echo "=========================================="
echo "Cleanup and Reset"
echo "=========================================="
echo ""
echo "This will remove:"
echo "  • All containers for project: $COMPOSE_PROJECT_NAME"
echo "  • All volumes (DATA WILL BE LOST)"
echo "  • All networks"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Stopping and removing containers..."
cd "$PROJECT_ROOT/config/compose"
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.full.yml down -v 2>/dev/null || true

echo "Removing any orphaned containers..."
podman stop -a 2>/dev/null || true
podman rm -f $(podman ps -aq) 2>/dev/null || true

echo "Pruning networks..."
podman network prune -f

echo ""
echo "✅ Cleanup complete"
echo ""
echo "To deploy fresh stack:"
echo "  bash scripts/deployment/deploy_with_compose.sh"
echo ""
