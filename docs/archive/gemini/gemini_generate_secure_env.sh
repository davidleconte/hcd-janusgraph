#!/bin/bash
# Secure Environment Configuration Generator
# This script generates strong random credentials and sets up the security environment.
# Adapted from the Security Audit findings.
#
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
# Date: 2026-01-28

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔐 Gemini Secure Environment Configuration Generator"
echo "===================================================="

# Check if .env already exists
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    echo "⚠️  WARNING: .env already exists."
    echo "If you want to regenerate, please back up and remove it first: mv .env .env.bak"
    exit 0
fi

# Check prerequisites
if ! command -v openssl &> /dev/null; then
    echo "❌ ERROR: openssl not found. Please install it."
    exit 1
fi

if ! command -v gpg &> /dev/null; then
    echo "❌ ERROR: gpg not found. Please install it."
    exit 1
fi

# Determine sed flag based on OS (Darwin/macOS vs Linux)
SED_EXT=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    SED_EXT="''"
fi

# 1. Initialize .env from example
if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    chmod 600 "$PROJECT_ROOT/.env"
    echo "✅ Created .env from .env.example"
else
    echo "❌ ERROR: .env.example not found."
    exit 1
fi

# 2. Generate strong random passwords
CREDENTIALS=(
    "GRAFANA_ADMIN_PASSWORD"
    "JANUSGRAPH_ADMIN_PASSWORD"
    "HCD_PASSWORD"
    "HCD_KEYSTORE_PASSWORD"
    "HCD_TRUSTSTORE_PASSWORD"
    "JANUSGRAPH_KEYSTORE_PASSWORD"
    "JANUSGRAPH_TRUSTSTORE_PASSWORD"
    "OPENSEARCH_ADMIN_PASSWORD"
    "SSL_KEYSTORE_PASSWORD"
    "SSL_TRUSTSTORE_PASSWORD"
)

echo "Generating random credentials..."
for var in "${CREDENTIALS[@]}"; do
    # Generate 32-character random string (alphanumeric)
    PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

    # Use appropriate sed syntax for macOS vs Linux
    if [ -n "$SED_EXT" ]; then
        sed -i '' "s|${var}=CHANGE_ME_STRONG_PASSWORD_HERE|${var}=${PASSWORD}|g" "$PROJECT_ROOT/.env"
    else
        sed -i "s|${var}=CHANGE_ME_STRONG_PASSWORD_HERE|${var}=${PASSWORD}|g" "$PROJECT_ROOT/.env"
    fi
    echo "   ✅ $var generated"
done

# 3. Setup GPG Key for Backup Encryption
echo "Checking GPG key for backups..."
BACKUP_EMAIL="backup@$(hostname)"
if ! gpg --list-keys "$BACKUP_EMAIL" &> /dev/null; then
    echo "Generating new GPG key for $BACKUP_EMAIL (this may take a moment)..."
    gpg --batch --gen-key <<EOF
%no-protection
Key-Type: RSA
Key-Length: 4096
Name-Real: HCD Backup
Name-Email: $BACKUP_EMAIL
Expire-Date: 1y
EOF
    echo "   ✅ GPG key generated."
fi

# Extract GPG Key ID and update .env
BACKUP_KEY=$(gpg --list-keys --with-colons "$BACKUP_EMAIL" | awk -F: '/^pub:/ { print $5 }' | head -1)

if [ -n "$BACKUP_KEY" ]; then
    if [ -n "$SED_EXT" ]; then
        sed -i '' "s|BACKUP_ENCRYPTION_KEY=CHANGE_ME_GPG_KEY_ID_HERE|BACKUP_ENCRYPTION_KEY=${BACKUP_KEY}|g" "$PROJECT_ROOT/.env"
    else
        sed -i "s|BACKUP_ENCRYPTION_KEY=CHANGE_ME_GPG_KEY_ID_HERE|BACKUP_ENCRYPTION_KEY=${BACKUP_KEY}|g" "$PROJECT_ROOT/.env"
    fi
    echo "   ✅ BACKUP_ENCRYPTION_KEY updated with ID: $BACKUP_KEY"
fi

echo "===================================================="
echo "🎉 Secure configuration successfully prepared!"
echo "Location: $PROJECT_ROOT/.env"
echo ""
echo "⚠️  IMPORTANT SECURITY REMINDERS:"
echo "   1. NEVER commit the .env file to version control."
echo "   2. Ensure the file permissions remain restricted (currently 600)."
echo "   3. These credentials will be used by the 'gemini_deploy_full_stack.sh' script."
echo "===================================================="
