#!/bin/bash
# File: scripts/utils/cleanup_podman.sh
# Created: 2026-01-28
# Purpose: Cleanup of JanusGraph project Podman resources
# WARNING: This script removes containers, volumes, and networks for this project

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project-specific prefixes
PROJECT_PREFIXES=("janusgraph" "hcd" "opensearch" "vault" "prometheus" "grafana" "alertmanager" "jupyter")

echo -e "${YELLOW}🧹 JanusGraph Project Cleanup${NC}"
echo "=================================="
echo ""
echo -e "${RED}⚠️  WARNING: This will remove:${NC}"
echo "  - All project containers (janusgraph, hcd, opensearch, vault, etc.)"
echo "  - All project volumes (data will be LOST)"
echo "  - All project networks"
echo ""
echo -e "${BLUE}ℹ️  Only resources matching project prefixes will be removed:${NC}"
for prefix in "${PROJECT_PREFIXES[@]}"; do
    echo "  - $prefix*"
done
echo ""
read -p "Type 'DELETE' to confirm cleanup: " confirm

if [ "$confirm" != "DELETE" ]; then
    echo -e "${GREEN}Cleanup cancelled${NC}"
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo ""

# Stop project containers
echo "1️⃣  Stopping project containers..."
for prefix in "${PROJECT_PREFIXES[@]}"; do
    podman ps --format "{{.Names}}" | grep "^${prefix}" | xargs -r podman stop 2>/dev/null || true
done

# Remove project containers
echo "2️⃣  Removing project containers..."
for prefix in "${PROJECT_PREFIXES[@]}"; do
    podman ps -a --format "{{.Names}}" | grep "^${prefix}" | xargs -r podman rm -f 2>/dev/null || true
done

# Remove project pods
echo "3️⃣  Removing project pods..."
for prefix in "${PROJECT_PREFIXES[@]}"; do
    podman pod ps --format "{{.Name}}" | grep "^${prefix}" | xargs -r podman pod rm -f 2>/dev/null || true
done

# Remove project volumes
echo "4️⃣  Removing project volumes..."
for prefix in "${PROJECT_PREFIXES[@]}"; do
    podman volume ls --format "{{.Name}}" | grep "^${prefix}" | xargs -r podman volume rm -f 2>/dev/null || true
done

# Remove project networks
echo "5️⃣  Removing project networks..."
for prefix in "${PROJECT_PREFIXES[@]}"; do
    podman network ls --format "{{.Name}}" | grep "^${prefix}" | xargs -r podman network rm 2>/dev/null || true
done

# Prune unused resources (safe - only removes unused)
echo "6️⃣  Pruning unused resources..."
podman system prune -f 2>/dev/null || true

echo ""
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""
echo "Next steps:"
echo "  1. cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh"
echo "  2. Wait 90 seconds for services to start"
echo "  3. ./scripts/security/init_vault.sh"

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
