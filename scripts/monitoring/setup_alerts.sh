#!/bin/bash
# File: scripts/monitoring/setup_alerts.sh
# Created: 2026-01-28T10:32:16.012
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
#
# Setup Prometheus alerting rules

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔔 Setting up Prometheus alerts..."

# Create alerts.yml
cat > "$PROJECT_ROOT/config/monitoring/alerts.yml" << 'ALERTS_EOF'
# File: config/monitoring/alerts.yml
# Created: 2026-01-28T10:32:16.234
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

groups:
  - name: janusgraph_alerts
    interval: 30s
    rules:
      - alert: JanusGraphDown
        expr: up{job="janusgraph"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "JanusGraph is down"
          description: "JanusGraph instance {{ $labels.instance }} has been down for more than 1 minute"

      - alert: HCDNodeDown
        expr: cassandra_cluster_live_nodes < 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "HCD node is down"
          description: "HCD cluster has {{ $value }} live nodes (expected >= 1)"

      - alert: HighMemoryUsage
        expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage ({{ $value | humanizePercentage }})"
          description: "Container {{ $labels.name }} is using {{ $value | humanizePercentage }} of memory"

      - alert: SlowQueries
        expr: rate(janusgraph_query_duration_seconds_sum[5m]) / rate(janusgraph_query_duration_seconds_count[5m]) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow query performance (avg {{ $value }}s)"
          description: "JanusGraph queries are taking an average of {{ $value }} seconds"
ALERTS_EOF

echo "✅ Alerts configured: config/monitoring/alerts.yml"
echo ""
echo "To apply alerts:"
echo "  1. Restart Prometheus container"
echo "  2. Verify: http://localhost:9090/alerts"

# Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
