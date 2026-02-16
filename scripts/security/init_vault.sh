#!/bin/bash
# File: scripts/security/init_vault.sh
# Created: 2026-01-28
# Purpose: Initialize and configure HashiCorp Vault for secrets management

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

podman_cmd() {
    podman --remote --connection "$PODMAN_CONNECTION" "$@"
}

podman_exec() {
    podman_cmd exec "$@"
}

echo -e "${BLUE}🔐 HashiCorp Vault Initialization${NC}"
echo "===================================="
echo ""

# Check if Vault container is running
if ! podman_cmd ps | grep -q vault-server; then
    echo -e "${RED}❌ Vault container is not running${NC}"
    echo "Start the full stack first:"
    echo "  cd config/compose && podman-compose -f docker-compose.full.yml up -d vault"
    exit 1
fi

echo -e "${GREEN}✅ Vault container is running${NC}"
echo ""

# Wait for Vault to be ready
echo "⏳ Waiting for Vault to be ready..."
for i in {1..30}; do
    if podman_exec vault-server vault status >/dev/null 2>&1 || [ $? -eq 2 ]; then
        break
    fi
    sleep 1
done

# Check if Vault is already initialized
if podman_exec vault-server vault status 2>&1 | grep -q "Initialized.*true"; then
    echo -e "${YELLOW}⚠️  Vault is already initialized${NC}"
    echo ""
    echo "To re-initialize Vault:"
    echo "  1. Stop the container: podman stop vault-server"
    echo "  2. Remove the data: podman volume rm hcd-janusgraph_vault-data"
    echo "  3. Restart: podman-compose -f config/compose/docker-compose.full.yml up -d vault"
    echo "  4. Run this script again"
    exit 0
fi

echo -e "${BLUE}1️⃣  Initializing Vault...${NC}"
INIT_OUTPUT=$(podman_exec vault-server vault operator init -key-shares=5 -key-threshold=3 -format=json)

# Extract keys and root token
UNSEAL_KEY_1=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[0]')
UNSEAL_KEY_2=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[1]')
UNSEAL_KEY_3=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[2]')
UNSEAL_KEY_4=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[3]')
UNSEAL_KEY_5=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[4]')
ROOT_TOKEN=$(echo "$INIT_OUTPUT" | jq -r '.root_token')

# Save keys securely
VAULT_KEYS_FILE="$PROJECT_ROOT/.vault-keys"
cat > "$VAULT_KEYS_FILE" <<EOF
# HashiCorp Vault Initialization Keys
# Generated: $(date)
#
# ⚠️  CRITICAL SECURITY WARNING ⚠️
# These keys provide access to all secrets in Vault
# Store them securely and NEVER commit to version control
#
# Unseal Keys (need 3 of 5 to unseal):
VAULT_UNSEAL_KEY_1=$UNSEAL_KEY_1
VAULT_UNSEAL_KEY_2=$UNSEAL_KEY_2
VAULT_UNSEAL_KEY_3=$UNSEAL_KEY_3
VAULT_UNSEAL_KEY_4=$UNSEAL_KEY_4
VAULT_UNSEAL_KEY_5=$UNSEAL_KEY_5

# Root Token (full admin access):
VAULT_ROOT_TOKEN=$ROOT_TOKEN

# Usage:
# export VAULT_ADDR=http://localhost:8200
# export VAULT_TOKEN=$ROOT_TOKEN
# vault status
EOF

chmod 600 "$VAULT_KEYS_FILE"

echo -e "${GREEN}✅ Vault initialized${NC}"
echo -e "${YELLOW}⚠️  Keys saved to: $VAULT_KEYS_FILE${NC}"
echo ""

# Unseal Vault
echo -e "${BLUE}2️⃣  Unsealing Vault...${NC}"
podman_exec vault-server vault operator unseal "$UNSEAL_KEY_1" >/dev/null
podman_exec vault-server vault operator unseal "$UNSEAL_KEY_2" >/dev/null
podman_exec vault-server vault operator unseal "$UNSEAL_KEY_3" >/dev/null

echo -e "${GREEN}✅ Vault unsealed${NC}"
echo ""

# Login with root token
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=$ROOT_TOKEN

# Enable KV secrets engine
echo -e "${BLUE}3️⃣  Enabling KV secrets engine...${NC}"
podman_exec -e VAULT_TOKEN=$ROOT_TOKEN vault-server vault secrets enable -path=janusgraph kv-v2

echo -e "${GREEN}✅ KV secrets engine enabled at: janusgraph/${NC}"
echo ""

# Create initial secrets
echo -e "${BLUE}4️⃣  Creating initial secrets...${NC}"

# Generate secure random passwords
ADMIN_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)
HCD_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)
GRAFANA_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)

# Store secrets in Vault
podman_exec -e VAULT_TOKEN=$ROOT_TOKEN vault-server vault kv put janusgraph/admin \
    username=admin \
    password="$ADMIN_PASSWORD"

podman_exec -e VAULT_TOKEN=$ROOT_TOKEN vault-server vault kv put janusgraph/hcd \
    username=cassandra \
    password="$HCD_PASSWORD"

podman_exec -e VAULT_TOKEN=$ROOT_TOKEN vault-server vault kv put janusgraph/grafana \
    username=admin \
    password="$GRAFANA_PASSWORD"

podman_exec -e VAULT_TOKEN=$ROOT_TOKEN vault-server vault kv put janusgraph/opensearch \
    username=admin \
    password="$ADMIN_PASSWORD"

echo -e "${GREEN}✅ Initial secrets created${NC}"
echo ""

# Create policy for applications
echo -e "${BLUE}5️⃣  Creating access policy...${NC}"

# Create policy file first
cat > /tmp/janusgraph-policy.hcl <<'POLICY_EOF'
# Read access to janusgraph secrets
path "janusgraph/*" {
  capabilities = ["read", "list"]
}

# Allow token renewal
path "auth/token/renew-self" {
  capabilities = ["update"]
}
POLICY_EOF

# Copy policy to container and apply
podman_cmd cp /tmp/janusgraph-policy.hcl vault-server:/tmp/janusgraph-policy.hcl
podman_exec -e VAULT_TOKEN=$ROOT_TOKEN vault-server vault policy write janusgraph-policy /tmp/janusgraph-policy.hcl
rm /tmp/janusgraph-policy.hcl

echo -e "${GREEN}✅ Policy created: janusgraph-policy${NC}"
echo ""

# Create application token
echo -e "${BLUE}6️⃣  Creating application token...${NC}"
APP_TOKEN=$(podman_exec -e VAULT_TOKEN=$ROOT_TOKEN vault-server vault token create \
    -policy=janusgraph-policy \
    -ttl=720h \
    -renewable=true \
    -format=json | jq -r '.auth.client_token')

echo -e "${GREEN}✅ Application token created${NC}"
echo ""

# Save application token
cat >> "$VAULT_KEYS_FILE" <<EOF

# Application Token (read-only access to janusgraph/* secrets):
VAULT_APP_TOKEN=$APP_TOKEN
EOF

# Create .env file with Vault configuration
ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
fi

# Add Vault configuration to .env
if ! grep -q "VAULT_ADDR" "$ENV_FILE"; then
    cat >> "$ENV_FILE" <<EOF

# ------------------------------------------------------------------------------
# HashiCorp Vault Configuration
# ------------------------------------------------------------------------------
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=$APP_TOKEN

# For production, use AppRole authentication instead of tokens
# VAULT_ROLE_ID=your-role-id
# VAULT_SECRET_ID=your-secret-id
EOF
    echo -e "${GREEN}✅ Vault configuration added to .env${NC}"
fi

# Create secure credentials log (before displaying summary)
CREDENTIALS_LOG="$PROJECT_ROOT/.vault-credentials.log"
chmod 600 "$CREDENTIALS_LOG" 2>/dev/null || true

cat > "$CREDENTIALS_LOG" << 'CRED_EOF'
Vault Initialization Credentials
Generated: $(date)

SENSITIVE - KEEP SECURE AND DELETE AFTER TRANSFER

Root Token: $ROOT_TOKEN
App Token: $APP_TOKEN

Generated Passwords:
  - JanusGraph admin: $ADMIN_PASSWORD
  - HCD cassandra: $HCD_PASSWORD
  - Grafana admin: $GRAFANA_PASSWORD

Keys File: $VAULT_KEYS_FILE

IMPORTANT: Transfer these credentials to secure storage, then delete this file.
CRED_EOF

# Expand variables in the log file
eval "cat > \"$CREDENTIALS_LOG\" << 'CRED_EOF'
Vault Initialization Credentials
Generated: $(date)

SENSITIVE - KEEP SECURE AND DELETE AFTER TRANSFER

Root Token: $ROOT_TOKEN
App Token: $APP_TOKEN

Generated Passwords:
  - JanusGraph admin: $ADMIN_PASSWORD
  - HCD cassandra: $HCD_PASSWORD
  - Grafana admin: $GRAFANA_PASSWORD

Keys File: $VAULT_KEYS_FILE

IMPORTANT: Transfer these credentials to secure storage, then delete this file.
CRED_EOF"

chmod 400 "$CREDENTIALS_LOG"

# Summary
echo ""
echo "===================================="
echo -e "${GREEN}✅ Vault Setup Complete${NC}"
echo "===================================="
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "  • Vault initialized with 5 unseal keys (threshold: 3)"
echo "  • KV secrets engine enabled at: janusgraph/"
echo "  • Initial secrets created for all services"
echo "  • Access policy created: janusgraph-policy"
echo "  • Application token generated"
echo ""
echo -e "${BLUE}🔑 Credentials Location:${NC}"
echo "  • Keys file: $VAULT_KEYS_FILE"
echo "  • Credentials log: $CREDENTIALS_LOG (read-only)"
echo ""
echo -e "${RED}⚠️  CREDENTIALS NOT DISPLAYED FOR SECURITY${NC}"
echo "  • View credentials: cat $CREDENTIALS_LOG"
echo "  • After securing, delete: rm $CREDENTIALS_LOG"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT SECURITY NOTES:${NC}"
echo "  1. Store $VAULT_KEYS_FILE securely (encrypted backup)"
echo "  2. Never commit .vault-keys or .env to version control"
echo "  3. Distribute unseal keys to different trusted individuals"
echo "  4. Rotate the root token after initial setup"
echo "  5. Use AppRole authentication for production"
echo ""
echo -e "${BLUE}📖 Next Steps:${NC}"
echo "  1. Secure credentials:"
echo "     cat $CREDENTIALS_LOG  # Review credentials"
echo "     # Transfer to secure password manager"
echo "     rm $CREDENTIALS_LOG   # Delete after securing"
echo ""
echo "  2. Test Vault access:"
echo "     source ./scripts/security/vault_access.sh"
echo "     vault kv get janusgraph/admin"
echo ""
echo "  2. Update application code to use Vault:"
echo "     from scripts.utils.secrets_manager import SecretsManager"
echo "     sm = SecretsManager(backend='vault')"
echo "     password = sm.get_secret('janusgraph/admin:password')"
echo ""
echo "  3. Restart services with new credentials"
echo ""
echo -e "${BLUE}🌐 Vault UI:${NC}"
echo "  http://localhost:8200/ui"
echo "  Token: $ROOT_TOKEN"
echo ""

# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
