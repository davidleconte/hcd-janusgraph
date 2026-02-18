#!/bin/bash
# File: deploy_monitoring.sh
# Created: 2026-01-29
# Purpose: Deploy and test Week 2 monitoring stack

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying Week 2 Monitoring Stack${NC}"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/config/compose/docker-compose.full.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.full.yml not found${NC}"
    exit 1
fi

# Step 1: Build the exporter image
echo -e "${BLUE}1️⃣  Building JanusGraph exporter image...${NC}"
cd "$PROJECT_ROOT"
podman build -f docker/Dockerfile.exporter -t localhost/janusgraph-exporter:1.0.0 .
echo -e "${GREEN}✅ Exporter image built${NC}"
echo ""

# Step 2: Start the monitoring stack
echo -e "${BLUE}2️⃣  Starting monitoring services...${NC}"
cd "$PROJECT_ROOT/config/compose"
podman-compose -f docker-compose.full.yml up -d prometheus alertmanager janusgraph-exporter grafana
echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Step 3: Wait for services to be healthy
echo -e "${BLUE}3️⃣  Waiting for services to be healthy...${NC}"
sleep 10

# Check Prometheus
echo -n "  Checking Prometheus... "
if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Check AlertManager
echo -n "  Checking AlertManager... "
if curl -sf http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Check Grafana
echo -n "  Checking Grafana... "
if curl -sf http://localhost:3001/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Check Exporter
echo -n "  Checking JanusGraph Exporter... "
if curl -sf http://localhost:8000/metrics > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo ""

# Step 4: Verify Prometheus targets
echo -e "${BLUE}4️⃣  Verifying Prometheus targets...${NC}"
TARGETS=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job): \(.health)"')
echo "$TARGETS"
echo ""

# Step 5: Check if exporter is collecting metrics
echo -e "${BLUE}5️⃣  Checking JanusGraph exporter metrics...${NC}"
METRICS=$(curl -s http://localhost:8000/metrics | grep -E "^janusgraph_" | head -5)
if [ -n "$METRICS" ]; then
    echo -e "${GREEN}✅ Exporter is collecting metrics:${NC}"
    echo "$METRICS"
else
    echo -e "${YELLOW}⚠️  No metrics found yet (JanusGraph may not be running)${NC}"
fi
echo ""

# Step 6: Display access information
echo -e "${BLUE}📊 Access Information${NC}"
echo "===================="
echo ""
echo -e "${GREEN}Prometheus:${NC}     http://localhost:9090"
echo -e "${GREEN}AlertManager:${NC}   http://localhost:9093"
echo -e "${GREEN}Grafana:${NC}        http://localhost:3001 (admin/admin)"
echo -e "${GREEN}Exporter:${NC}       http://localhost:8000/metrics"
echo ""

# Step 7: Quick tests
echo -e "${BLUE}🧪 Quick Tests${NC}"
echo "=============="
echo ""

echo "1. Test Prometheus query:"
echo "   curl 'http://localhost:9090/api/v1/query?query=up' | jq"
echo ""

echo "2. Test AlertManager status:"
echo "   curl http://localhost:9093/api/v2/status | jq"
echo ""

echo "3. View exporter metrics:"
echo "   curl http://localhost:8000/metrics | grep janusgraph"
echo ""

echo "4. Test alert (will appear in AlertManager UI):"
echo "   curl -X POST http://localhost:9093/api/v1/alerts -d '[{\"labels\":{\"alertname\":\"TestAlert\",\"severity\":\"warning\"},\"annotations\":{\"summary\":\"Test\",\"description\":\"Test alert\"}}]'"
echo ""

# Step 8: Next steps
echo -e "${BLUE}📝 Next Steps${NC}"
echo "============="
echo ""
echo "1. Configure Slack webhook in .env:"
echo "   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
echo ""
echo "2. Configure SMTP in .env:"
echo "   SMTP_PASSWORD=your-smtp-password"
echo ""
echo "3. Restart AlertManager to apply changes:"
echo "   podman restart alertmanager"
echo ""
echo "4. Test notifications:"
echo "   See scripts/monitoring/test_alerts.sh"
echo ""

echo -e "${GREEN}✅ Monitoring stack deployed successfully!${NC}"

# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
