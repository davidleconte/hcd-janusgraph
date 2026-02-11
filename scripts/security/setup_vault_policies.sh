#!/bin/bash
# File: scripts/security/setup_vault_policies.sh
# Created: 2026-02-11
# Purpose: Setup Vault policies and create service-specific tokens
# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
# Phase: Phase 2 - Infrastructure Security

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
POLICIES_DIR="$PROJECT_ROOT/config/vault/policies"
VAULT_KEYS_FILE="$PROJECT_ROOT/.vault-keys"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Vault Policy Setup${NC}"
echo "====================="
echo ""

# Check if Vault is initialized
if [ ! -f "$VAULT_KEYS_FILE" ]; then
    echo -e "${RED}❌ Vault not initialized${NC}"
    echo "Run ./scripts/security/init_vault.sh first"
    exit 1
fi

# Source Vault credentials
source "$VAULT_KEYS_FILE"
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=$VAULT_ROOT_TOKEN

# Check Vault connection
if ! podman exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server vault status >/dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to Vault${NC}"
    echo "Ensure Vault container is running and unsealed"
    exit 1
fi

echo -e "${GREEN}✅ Connected to Vault${NC}"
echo ""

# Function to apply policy
apply_policy() {
    local policy_name=$1
    local policy_file=$2
    
    echo -e "${BLUE}📋 Applying policy: ${policy_name}${NC}"
    
    # Copy policy to container
    podman cp "$policy_file" vault-server:/tmp/policy.hcl
    
    # Apply policy
    if podman exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server \
        vault policy write "$policy_name" /tmp/policy.hcl >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Policy applied: ${policy_name}${NC}"
    else
        echo -e "${RED}❌ Failed to apply policy: ${policy_name}${NC}"
        return 1
    fi
}

# Function to create token for policy
create_token() {
    local policy_name=$1
    local description=$2
    local ttl=${3:-720h}  # Default 30 days
    
    echo -e "${BLUE}🔑 Creating token for: ${description}${NC}"
    
    local token=$(podman exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server \
        vault token create \
        -policy="$policy_name" \
        -ttl="$ttl" \
        -renewable=true \
        -display-name="$description" \
        -format=json | jq -r '.auth.client_token')
    
    if [ -n "$token" ] && [ "$token" != "null" ]; then
        echo -e "${GREEN}✅ Token created${NC}"
        echo "$token"
    else
        echo -e "${RED}❌ Failed to create token${NC}"
        return 1
    fi
}

# Apply policies
echo -e "${BLUE}1️⃣  Applying Vault Policies${NC}"
echo ""

apply_policy "janusgraph-api" "$POLICIES_DIR/janusgraph-api-policy.hcl"
apply_policy "monitoring" "$POLICIES_DIR/monitoring-policy.hcl"
apply_policy "admin" "$POLICIES_DIR/admin-policy.hcl"

echo ""

# Create service tokens
echo -e "${BLUE}2️⃣  Creating Service Tokens${NC}"
echo ""

API_TOKEN=$(create_token "janusgraph-api" "JanusGraph API Service" "720h")
MONITORING_TOKEN=$(create_token "monitoring" "Monitoring Services" "720h")
ADMIN_TOKEN=$(create_token "admin" "Administrative Operations" "168h")  # 7 days

echo ""

# Save tokens to file
TOKENS_FILE="$PROJECT_ROOT/.vault-service-tokens"
cat > "$TOKENS_FILE" <<EOF
# Vault Service Tokens
# Generated: $(date)
#
# ⚠️  SECURITY WARNING ⚠️
# These tokens provide access to Vault secrets
# Store securely and NEVER commit to version control
#

# JanusGraph API Service Token (read-only access to admin/opensearch)
VAULT_API_TOKEN=$API_TOKEN

# Monitoring Services Token (read-only access to grafana/prometheus)
VAULT_MONITORING_TOKEN=$MONITORING_TOKEN

# Administrative Token (full access for credential rotation)
VAULT_ADMIN_TOKEN=$ADMIN_TOKEN

# Usage Examples:
# 
# For API service:
#   export VAULT_TOKEN=\$VAULT_API_TOKEN
#   vault kv get janusgraph/admin
#
# For monitoring:
#   export VAULT_TOKEN=\$VAULT_MONITORING_TOKEN
#   vault kv get janusgraph/grafana
#
# For admin operations:
#   export VAULT_TOKEN=\$VAULT_ADMIN_TOKEN
#   vault kv put janusgraph/admin password="new_password"
EOF

chmod 600 "$TOKENS_FILE"

echo ""
echo "===================================="
echo -e "${GREEN}✅ Vault Policy Setup Complete${NC}"
echo "===================================="
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "  • 3 policies created:"
echo "    - janusgraph-api (read-only: admin, opensearch)"
echo "    - monitoring (read-only: grafana, prometheus)"
echo "    - admin (full access for rotation)"
echo ""
echo "  • 3 service tokens created:"
echo "    - API Token (30 days, renewable)"
echo "    - Monitoring Token (30 days, renewable)"
echo "    - Admin Token (7 days, renewable)"
echo ""
echo -e "${BLUE}🔑 Tokens Location:${NC}"
echo "  • Service tokens: $TOKENS_FILE"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT SECURITY NOTES:${NC}"
echo "  1. Store $TOKENS_FILE securely"
echo "  2. Never commit .vault-service-tokens to version control"
echo "  3. Rotate admin token weekly"
echo "  4. Renew service tokens before expiry"
echo "  5. Use least-privilege tokens in production"
echo ""
echo -e "${BLUE}📖 Next Steps:${NC}"
echo "  1. Update application .env files:"
echo "     echo \"VAULT_TOKEN=\$VAULT_API_TOKEN\" >> .env"
echo ""
echo "  2. Test token access:"
echo "     source $TOKENS_FILE"
echo "     export VAULT_TOKEN=\$VAULT_API_TOKEN"
echo "     vault kv get janusgraph/admin"
echo ""
echo "  3. Configure services to use appropriate tokens"
echo ""
echo -e "${BLUE}🔄 Token Renewal:${NC}"
echo "  vault token renew \$VAULT_API_TOKEN"
echo ""

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117

# Made with Bob
