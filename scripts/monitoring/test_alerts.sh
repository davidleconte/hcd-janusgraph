#!/bin/bash
# File: test_alerts.sh
# Created: 2026-01-29
# Purpose: Test AlertManager notifications

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing AlertManager Notifications${NC}"
echo "======================================"
echo ""

# Check if AlertManager is running
if ! curl -sf http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo -e "${RED}❌ AlertManager is not running${NC}"
    echo "Start it with: podman-compose -f config/compose/docker-compose.full.yml up -d alertmanager"
    exit 1
fi

echo -e "${GREEN}✅ AlertManager is running${NC}"
echo ""

# Test 1: Warning alert
echo -e "${BLUE}1️⃣  Sending test WARNING alert...${NC}"
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestWarningAlert",
      "severity": "warning",
      "service": "test",
      "cluster": "hcd-janusgraph"
    },
    "annotations": {
      "summary": "Test warning alert",
      "description": "This is a test warning alert to verify notification routing"
    },
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'"
  }]'
echo ""
echo -e "${GREEN}✅ Warning alert sent${NC}"
echo ""

# Test 2: Critical alert
echo -e "${BLUE}2️⃣  Sending test CRITICAL alert...${NC}"
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestCriticalAlert",
      "severity": "critical",
      "service": "test",
      "cluster": "hcd-janusgraph"
    },
    "annotations": {
      "summary": "Test critical alert",
      "description": "This is a test critical alert to verify immediate notification"
    },
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'"
  }]'
echo ""
echo -e "${GREEN}✅ Critical alert sent${NC}"
echo ""

# Test 3: Security alert
echo -e "${BLUE}3️⃣  Sending test SECURITY alert...${NC}"
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestSecurityAlert",
      "severity": "warning",
      "category": "security",
      "service": "test",
      "cluster": "hcd-janusgraph"
    },
    "annotations": {
      "summary": "Test security alert",
      "description": "This is a test security alert to verify security team routing"
    },
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'"
  }]'
echo ""
echo -e "${GREEN}✅ Security alert sent${NC}"
echo ""

# Test 4: Compliance alert
echo -e "${BLUE}4️⃣  Sending test COMPLIANCE alert...${NC}"
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestComplianceAlert",
      "severity": "warning",
      "category": "compliance",
      "service": "test",
      "cluster": "hcd-janusgraph"
    },
    "annotations": {
      "summary": "Test compliance alert",
      "description": "This is a test compliance alert to verify compliance team routing"
    },
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'"
  }]'
echo ""
echo -e "${GREEN}✅ Compliance alert sent${NC}"
echo ""

# Check alerts in AlertManager
echo -e "${BLUE}5️⃣  Checking alerts in AlertManager...${NC}"
ALERTS=$(curl -s http://localhost:9093/api/v2/alerts | jq -r '.[] | "\(.labels.alertname) (\(.labels.severity)): \(.status.state)"')
echo "$ALERTS"
echo ""

# Display next steps
echo -e "${BLUE}📋 Next Steps${NC}"
echo "============="
echo ""
echo "1. Check AlertManager UI:"
echo "   http://localhost:9093"
echo ""
echo "2. Check your configured notification channels:"
echo "   - Email inbox (if SMTP configured)"
echo "   - Slack channel (if webhook configured)"
echo ""
echo "3. Alerts should route as follows:"
echo "   - Warning → team-notifications (email + Slack #janusgraph-alerts)"
echo "   - Critical → critical-alerts (email + Slack #janusgraph-critical)"
echo "   - Security → security-team (email + Slack #security-alerts)"
echo "   - Compliance → compliance-team (email only)"
echo ""
echo "4. To resolve alerts, send with endsAt:"
echo "   curl -X POST http://localhost:9093/api/v1/alerts -d '[{...\"endsAt\":\"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\"}]'"
echo ""

echo -e "${GREEN}✅ Test alerts sent successfully!${NC}"
echo ""
echo -e "${YELLOW}⚠️  Note: Notifications will only be sent if SMTP/Slack are configured in .env${NC}"

# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
