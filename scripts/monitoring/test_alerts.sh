#!/bin/bash
# File: scripts/monitoring/test_alerts.sh
# Created: 2026-01-28T10:32:16.456
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
#
# Test Prometheus alerting configuration

set -euo pipefail

echo "🧪 Testing Prometheus alerts..."

# Check Prometheus is running
if ! curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "❌ Prometheus is not running"
    echo "   Start with: podman-compose -f docker-compose.full.yml up -d prometheus"
    exit 1
fi

# Check alerts are loaded
echo "Checking alerts configuration..."
alerts=$(curl -s http://localhost:9090/api/v1/rules | jq -r '.data.groups[].rules[].name' 2>/dev/null)

if [ -z "$alerts" ]; then
    echo "❌ No alerts configured"
    exit 1
fi

echo "✅ Configured alerts:"
echo "$alerts" | sed 's/^/   - /'

echo ""
echo "View alerts: http://localhost:9090/alerts"

# Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
