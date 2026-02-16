#!/bin/bash
# File: scripts/security/fix_vault_policy.sh
# Created: 2026-01-29
# Purpose: Fix Vault policy creation issue for KV v2 with UI support

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VAULT_KEYS_FILE="$PROJECT_ROOT/.vault-keys"
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

podman_exec() {
    podman --remote --connection "$PODMAN_CONNECTION" exec "$@"
}

echo -e "${BLUE}🔧 Fixing Vault Policy for KV v2 with UI Support${NC}"
echo "=================================================="
echo ""

if [ ! -f "$VAULT_KEYS_FILE" ]; then
    echo -e "${YELLOW}⚠️  Vault keys file not found${NC}"
    exit 1
fi

# Source the vault keys
source "$VAULT_KEYS_FILE"

echo "1️⃣  Creating comprehensive policy file for KV v2..."
cat > /tmp/janusgraph-policy.hcl <<'POLICY_EOF'
# KV v2 uses /data/ in the path for actual secrets
# Read access to janusgraph secrets (KV v2)
path "janusgraph/data/*" {
  capabilities = ["read", "list"]
}

# Metadata access (for listing)
path "janusgraph/metadata/*" {
  capabilities = ["read", "list"]
}

# UI access to mounts (required by vault CLI)
path "sys/internal/ui/mounts" {
  capabilities = ["read"]
}

path "sys/internal/ui/mounts/*" {
  capabilities = ["read"]
}

# Allow token lookup and renewal
path "auth/token/lookup-self" {
  capabilities = ["read"]
}

path "auth/token/renew-self" {
  capabilities = ["update"]
}
POLICY_EOF

echo "2️⃣  Copying policy to Vault container..."
podman --remote --connection "$PODMAN_CONNECTION" cp /tmp/janusgraph-policy.hcl vault-server:/tmp/janusgraph-policy.hcl

echo "3️⃣  Creating policy with ROOT token..."
podman_exec -e VAULT_TOKEN=$VAULT_ROOT_TOKEN vault-server \
    vault policy write janusgraph-policy /tmp/janusgraph-policy.hcl

echo "4️⃣  Creating new application token..."
NEW_APP_TOKEN=$(podman_exec -e VAULT_TOKEN=$VAULT_ROOT_TOKEN vault-server \
    vault token create \
    -policy=janusgraph-policy \
    -ttl=720h \
    -renewable=true \
    -format=json | jq -r '.auth.client_token')

echo "5️⃣  Updating .vault-keys file..."
# Check if VAULT_APP_TOKEN already exists
if grep -q "^VAULT_APP_TOKEN=" "$VAULT_KEYS_FILE"; then
    # Replace existing token
    sed -i.bak "s/^VAULT_APP_TOKEN=.*/VAULT_APP_TOKEN=$NEW_APP_TOKEN/" "$VAULT_KEYS_FILE"
else
    # Append new token
    echo "" >> "$VAULT_KEYS_FILE"
    echo "# Application Token (with janusgraph-policy):" >> "$VAULT_KEYS_FILE"
    echo "VAULT_APP_TOKEN=$NEW_APP_TOKEN" >> "$VAULT_KEYS_FILE"
fi

echo ""
echo -e "${GREEN}✅ Policy fixed for KV v2 with UI support${NC}"
echo ""
echo "New application token: ${NEW_APP_TOKEN:0:10}..."
echo ""
echo "Test it:"
echo "  source ./scripts/security/vault_access.sh"
echo "  podman exec -e VAULT_TOKEN=\$VAULT_TOKEN vault-server vault kv get janusgraph/admin"
echo ""
echo "Note: Added sys/internal/ui/mounts access for Vault CLI compatibility"
echo ""

# Cleanup
rm /tmp/janusgraph-policy.hcl

# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
