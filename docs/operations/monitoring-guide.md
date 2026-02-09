# Monitoring Guide

**File**: docs/MONITORING.md  
**Created**: 2026-01-28T11:06:00.123  
**Author**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

---

## Overview

This guide covers monitoring configuration for the HCD + JanusGraph stack.

## Monitoring Stack

### Components
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notification

### Access URLs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

---

## Prometheus Configuration

### Setup Alerts

Run the setup script:

bash scripts/monitoring/setup_alerts.sh

This creates config/monitoring/alerts.yml with rules for:
- JanusGraph service down
- HCD node down
- High memory usage
- Slow query performance

### Test Alerts

bash scripts/monitoring/test_alerts.sh

### View Alerts

Open http://localhost:9090/alerts

---

## Grafana Dashboards

### Initial Setup

1. Login: http://localhost:3001 (admin/admin)
2. Change password on first login
3. Add Prometheus datasource:
   - Go to Configuration > Data Sources
   - Add Prometheus
   - URL: http://prometheus:9090
   - Save and Test

### Import Dashboards

Pre-built dashboards available in:
- config/monitoring/grafana/dashboards/

Import via:
1. Dashboards > Import
2. Upload JSON file
3. Select Prometheus datasource
4. Save

---

## Key Metrics

### JanusGraph Metrics
- Query latency
- Transaction count
- Cache hit rate
- Connection pool status

### HCD Metrics
- Cluster status
- Read/write latency
- Compaction activity
- Storage usage

### System Metrics
- CPU usage
- Memory usage
- Disk I/O
- Network traffic

---

## Alert Configuration

### Alert Rules

Located in config/monitoring/alerts.yml:

Critical Alerts:
- Service down (1 minute)
- HCD node down (1 minute)

Warning Alerts:
- High memory usage (5 minutes)
- Slow queries (5 minutes)

### Notification Channels

Configure in Alertmanager:
- Email
- Slack
- PagerDuty
- Webhook

---

## Log Aggregation

### Container Logs

View logs:

podman logs -f janusgraph-server
podman logs -f hcd-server

### Log Rotation

Automatic rotation configured in docker-compose:

logging:
  driver: json-file
  options:
    max-size: 10m
    max-file: 3

### Centralized Logging (Optional)

Add Loki + Promtail for log aggregation:
- Loki: Log storage
- Promtail: Log shipper
- View in Grafana

---

## Troubleshooting

### Prometheus Not Scraping

Check targets: http://localhost:9090/targets

Common issues:
- Service not exposing metrics
- Network connectivity
- Incorrect service names

### Grafana Can't Connect to Prometheus

Check datasource configuration:
- URL: http://prometheus:9090 (container name)
- Network: hcd-janusgraph-network

### No Data in Dashboards

Verify:
- Prometheus has targets
- Time range in Grafana
- Query syntax

---

## Best Practices

1. **Monitor Everything**: Services, resources, application metrics
2. **Set Meaningful Alerts**: Avoid alert fatigue
3. **Document Runbooks**: What to do when alerts fire
4. **Regular Review**: Check metrics weekly
5. **Capacity Planning**: Track trends for resource planning

---

**Signature**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
