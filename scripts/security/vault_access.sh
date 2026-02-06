#!/bin/bash
# File: scripts/security/vault_access.sh
# Created: 2026-01-29
# Purpose: Helper script to access Vault with proper credentials

# Only set strict mode if not being sourced
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    set -euo pipefail
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VAULT_KEYS_FILE="$PROJECT_ROOT/.vault-keys"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ ! -f "$VAULT_KEYS_FILE" ]; then
    echo -e "${YELLOW}⚠️  Vault keys file not found: $VAULT_KEYS_FILE${NC}"
    echo "Run ./scripts/security/init_vault.sh first"
    exit 1
fi

# Source the vault keys
source "$VAULT_KEYS_FILE"

# Export for current shell
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=$VAULT_APP_TOKEN

echo -e "${BLUE}🔐 Vault Access Helper${NC}"
echo "======================="
echo ""
echo -e "${GREEN}✅ Environment configured${NC}"
echo "  VAULT_ADDR: $VAULT_ADDR"
echo "  VAULT_TOKEN: ${VAULT_TOKEN:0:10}..."
echo ""
echo "Available commands:"
echo "  1. List secrets:"
echo "     podman exec -e VAULT_TOKEN=\$VAULT_TOKEN vault-server vault kv list janusgraph/"
echo ""
echo "  2. Get admin credentials:"
echo "     podman exec -e VAULT_TOKEN=\$VAULT_TOKEN vault-server vault kv get janusgraph/admin"
echo ""
echo "  3. Get HCD credentials:"
echo "     podman exec -e VAULT_TOKEN=\$VAULT_TOKEN vault-server vault kv get janusgraph/hcd"
echo ""
echo "  4. Get Grafana credentials:"
echo "     podman exec -e VAULT_TOKEN=\$VAULT_TOKEN vault-server vault kv get janusgraph/grafana"
echo ""
echo "Run these commands in your current shell, or source this script:"
echo "  source ./scripts/security/vault_access.sh"
echo ""

# If sourced, export variables for the shell
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    echo -e "${GREEN}✅ Variables exported to your shell${NC}"
    echo "You can now use: podman exec -e VAULT_TOKEN=\$VAULT_TOKEN vault-server vault kv get janusgraph/admin"
fi

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
