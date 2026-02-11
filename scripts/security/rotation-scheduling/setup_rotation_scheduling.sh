#!/bin/bash
# Setup Credential Rotation Scheduling
# This script installs systemd timers for automated credential rotation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "=== Credential Rotation Scheduling Setup ==="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (for systemd installation)"
   echo "   Run: sudo bash $0"
   exit 1
fi

# 1. Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install hvac requests || {
    echo "❌ Failed to install Python dependencies"
    exit 1
}

# 2. Create log directory
echo "📁 Creating log directory..."
mkdir -p /var/log
touch /var/log/credential-rotation.log
chmod 640 /var/log/credential-rotation.log

# 3. Create Vault token environment file
echo "🔐 Setting up Vault token..."
VAULT_TOKEN_FILE="/etc/janusgraph/vault-token.env"
mkdir -p /etc/janusgraph

if [[ ! -f "$VAULT_TOKEN_FILE" ]]; then
    echo "Creating Vault token file at $VAULT_TOKEN_FILE"
    echo "# Vault authentication token for credential rotation" > "$VAULT_TOKEN_FILE"
    echo "VAULT_APP_TOKEN=your-vault-token-here" >> "$VAULT_TOKEN_FILE"
    chmod 600 "$VAULT_TOKEN_FILE"
    echo "⚠️  IMPORTANT: Edit $VAULT_TOKEN_FILE and add your Vault token"
else
    echo "✅ Vault token file already exists"
fi

# 4. Copy systemd service and timer files
echo "📋 Installing systemd units..."
cp "$SCRIPT_DIR/credential-rotation.service" /etc/systemd/system/
cp "$SCRIPT_DIR/credential-rotation.timer" /etc/systemd/system/

# 5. Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# 6. Enable and start timer
echo "⏰ Enabling credential rotation timer..."
systemctl enable credential-rotation.timer
systemctl start credential-rotation.timer

# 7. Verify installation
echo ""
echo "=== Verification ==="
systemctl status credential-rotation.timer --no-pager || true

echo ""
echo "=== Next Scheduled Run ==="
systemctl list-timers credential-rotation.timer --no-pager || true

echo ""
echo "✅ Credential rotation scheduling setup complete!"
echo ""
echo "📝 Next Steps:"
echo "   1. Edit $VAULT_TOKEN_FILE and add your Vault token"
echo "   2. Test rotation manually: systemctl start credential-rotation.service"
echo "   3. Check logs: journalctl -u credential-rotation.service -f"
echo "   4. Verify timer: systemctl list-timers"
echo ""
echo "⏰ Rotation Schedule:"
echo "   - Frequency: Monthly (1st day of month at 2 AM)"
echo "   - Randomization: Up to 1 hour delay"
echo "   - Services: All (JanusGraph, OpenSearch, Grafana, Pulsar, Certificates)"
echo ""
echo "🔧 Management Commands:"
echo "   - Start now:     sudo systemctl start credential-rotation.service"
echo "   - Check status:  sudo systemctl status credential-rotation.timer"
echo "   - View logs:     sudo journalctl -u credential-rotation.service"
echo "   - Disable:       sudo systemctl disable credential-rotation.timer"
echo ""

# Made with Bob
