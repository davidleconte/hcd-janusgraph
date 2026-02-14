#!/bin/bash
"""
Import Security Dashboard to Grafana
=====================================

Imports the security dashboard JSON into Grafana instance.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Created: 2026-02-11
Phase: Phase 2 - Infrastructure Security (Final 15%)

Usage:
    ./scripts/monitoring/import_security_dashboard.sh
    ./scripts/monitoring/import_security_dashboard.sh --grafana-url http://localhost:3001
"""

set -euo pipefail

# Configuration
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
DASHBOARD_FILE="config/monitoring/dashboards/security-dashboard.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --grafana-url)
            GRAFANA_URL="$2"
            shift 2
            ;;
        --user)
            GRAFANA_USER="$2"
            shift 2
            ;;
        --password)
            GRAFANA_PASSWORD="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --grafana-url URL    Grafana URL (default: http://localhost:3001)"
            echo "  --user USER          Grafana username (default: admin)"
            echo "  --password PASS      Grafana password (default: admin)"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log_info "Starting Security Dashboard import..."
log_info "Grafana URL: $GRAFANA_URL"

# Check if dashboard file exists
if [[ ! -f "$DASHBOARD_FILE" ]]; then
    log_error "Dashboard file not found: $DASHBOARD_FILE"
    exit 1
fi

# Check if Grafana is accessible
log_info "Checking Grafana connectivity..."
if ! curl -s -f -o /dev/null "$GRAFANA_URL/api/health"; then
    log_error "Cannot connect to Grafana at $GRAFANA_URL"
    log_error "Please ensure Grafana is running"
    exit 1
fi
log_info "✓ Grafana is accessible"

# Check if Prometheus datasource exists
log_info "Checking Prometheus datasource..."
DATASOURCE_CHECK=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    "$GRAFANA_URL/api/datasources/name/prometheus" \
    -w "%{http_code}" -o /dev/null)

if [[ "$DATASOURCE_CHECK" != "200" ]]; then
    log_warn "Prometheus datasource not found, creating..."
    
    # Create Prometheus datasource
    curl -s -X POST \
        -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "prometheus",
            "type": "prometheus",
            "url": "http://prometheus:9090",
            "access": "proxy",
            "isDefault": true
        }' \
        "$GRAFANA_URL/api/datasources" > /dev/null
    
    log_info "✓ Prometheus datasource created"
else
    log_info "✓ Prometheus datasource exists"
fi

# Prepare dashboard payload
log_info "Preparing dashboard payload..."
DASHBOARD_JSON=$(cat "$DASHBOARD_FILE")
PAYLOAD=$(jq -n \
    --argjson dashboard "$DASHBOARD_JSON" \
    '{
        dashboard: $dashboard,
        overwrite: true,
        message: "Imported via import_security_dashboard.sh"
    }')

# Import dashboard
log_info "Importing dashboard..."
RESPONSE=$(curl -s -X POST \
    -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "$GRAFANA_URL/api/dashboards/db")

# Check response
if echo "$RESPONSE" | jq -e '.status == "success"' > /dev/null 2>&1; then
    DASHBOARD_UID=$(echo "$RESPONSE" | jq -r '.uid')
    DASHBOARD_URL="$GRAFANA_URL/d/$DASHBOARD_UID"
    
    log_info "✓ Dashboard imported successfully!"
    log_info ""
    log_info "Dashboard URL: $DASHBOARD_URL"
    log_info ""
    log_info "Dashboard includes:"
    log_info "  • Credential rotation status (JanusGraph, OpenSearch)"
    log_info "  • Credential rotation rate and duration"
    log_info "  • Query validation metrics"
    log_info "  • Security event timeline"
    log_info "  • Failed authentication attempts"
    log_info "  • Vault access patterns"
    log_info "  • Failure rate gauges"
    log_info "  • Certificate expiry monitoring"
    log_info ""
    log_info "Access the dashboard at: $DASHBOARD_URL"
else
    log_error "Failed to import dashboard"
    log_error "Response: $RESPONSE"
    exit 1
fi

# Verify dashboard is accessible
log_info "Verifying dashboard accessibility..."
VERIFY_RESPONSE=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    "$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID" \
    -w "%{http_code}" -o /dev/null)

if [[ "$VERIFY_RESPONSE" == "200" ]]; then
    log_info "✓ Dashboard is accessible"
else
    log_warn "Dashboard imported but verification failed (HTTP $VERIFY_RESPONSE)"
fi

log_info ""
log_info "Import complete! 🎉"
log_info ""
log_info "Next steps:"
log_info "1. Ensure Prometheus is scraping security metrics"
log_info "2. Verify metrics are being collected:"
log_info "   - credential_rotation_total"
log_info "   - query_validation_total"
log_info "   - vault_access_total"
log_info "   - authentication_failed_total"
log_info "3. Configure alert rules in AlertManager"
log_info "4. Test dashboard panels with real data"

exit 0

# Made with Bob
