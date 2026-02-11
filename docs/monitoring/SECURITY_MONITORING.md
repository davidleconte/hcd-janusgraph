# Security Monitoring Guide

**Date:** 2026-02-11  
**Version:** 1.0  
**Status:** Active  
**Phase:** Phase 2 - Infrastructure Security (Complete)

## Overview

This guide covers the comprehensive security monitoring infrastructure for the HCD + JanusGraph Banking Compliance Platform, including credential rotation monitoring, query validation tracking, Vault access auditing, and security event alerting.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Metrics](#metrics)
3. [Dashboards](#dashboards)
4. [Alerts](#alerts)
5. [Integration Tests](#integration-tests)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Monitoring Stack                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Credential  │───▶│  Prometheus  │───▶│   Grafana    │  │
│  │   Rotation   │    │   Exporter   │    │  Dashboard   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │    Query     │───▶│  Prometheus  │───▶│ AlertManager │  │
│  │  Validation  │    │    Server    │    │              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │    Vault     │───▶│   Security   │                       │
│  │    Access    │    │    Events    │                       │
│  └──────────────┘    └──────────────┘                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Metrics Collection**: Security components emit Prometheus metrics
2. **Scraping**: Prometheus scrapes metrics every 15 seconds
3. **Storage**: Metrics stored in Prometheus TSDB
4. **Visualization**: Grafana queries Prometheus for dashboard display
5. **Alerting**: AlertManager evaluates rules and sends notifications

---

## Metrics

### Credential Rotation Metrics

#### `credential_rotation_total`
**Type:** Counter  
**Labels:** `service`, `status`  
**Description:** Total number of credential rotations

```promql
# Success rate by service
rate(credential_rotation_total{status="success"}[5m])

# Failure rate by service
rate(credential_rotation_total{status="failed"}[5m])
```

#### `credential_rotation_duration_seconds`
**Type:** Histogram  
**Labels:** `service`  
**Buckets:** 1, 5, 10, 30, 60, 120, 300 seconds  
**Description:** Credential rotation duration

```promql
# 95th percentile duration
histogram_quantile(0.95, 
  rate(credential_rotation_duration_seconds_bucket[5m])
)

# 99th percentile duration
histogram_quantile(0.99,
  rate(credential_rotation_duration_seconds_bucket[5m])
)
```

#### `credential_rotation_status`
**Type:** Gauge  
**Labels:** `service`  
**Values:** 1 (success), 0 (failed)  
**Description:** Current rotation status

```promql
# Current status for all services
credential_rotation_status
```

### Query Validation Metrics

#### `query_validation_total`
**Type:** Counter  
**Labels:** `result`  
**Description:** Total query validations

```promql
# Blocked query rate
rate(query_validation_total{result="blocked"}[5m])

# Allowed query rate
rate(query_validation_total{result="allowed"}[5m])

# Block rate percentage
rate(query_validation_total{result="blocked"}[5m]) /
rate(query_validation_total[5m])
```

#### `query_validation_duration_seconds`
**Type:** Histogram  
**Buckets:** 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0 seconds  
**Description:** Query validation latency

```promql
# 95th percentile validation latency
histogram_quantile(0.95,
  rate(query_validation_duration_seconds_bucket[5m])
)
```

### Vault Access Metrics

#### `vault_access_total`
**Type:** Counter  
**Labels:** `operation`, `path`, `status`  
**Description:** Total Vault access operations

```promql
# Read operations by path
rate(vault_access_total{operation="read"}[5m])

# Write operations by path
rate(vault_access_total{operation="write"}[5m])

# Error rate
rate(vault_access_total{status="error"}[5m]) /
rate(vault_access_total[5m])
```

### Authentication Metrics

#### `authentication_failed_total`
**Type:** Counter  
**Labels:** `service`, `reason`  
**Description:** Failed authentication attempts

```promql
# Failed auth rate by service
rate(authentication_failed_total[5m])

# Failed auth by reason
sum by (reason) (rate(authentication_failed_total[5m]))
```

### Security Event Metrics

#### `security_event_total`
**Type:** Counter  
**Labels:** `event_type`, `service`, `severity`  
**Description:** Security events

```promql
# High severity events
rate(security_event_total{severity="high"}[5m])

# Critical events
rate(security_event_total{severity="critical"}[5m])
```

### Certificate Metrics

#### `certificate_expiry_timestamp`
**Type:** Gauge  
**Labels:** `certificate_name`  
**Description:** Certificate expiry timestamp (Unix epoch)

```promql
# Days until expiry
(certificate_expiry_timestamp - time()) / 86400

# Certificates expiring in < 30 days
(certificate_expiry_timestamp - time()) / 86400 < 30
```

---

## Dashboards

### Security Dashboard

**Location:** `config/monitoring/dashboards/security-dashboard.json`  
**UID:** `security-dashboard`  
**URL:** `http://localhost:3001/d/security-dashboard`

#### Panels

1. **Credential Rotation Status** (Gauges)
   - JanusGraph rotation status
   - OpenSearch rotation status
   - Real-time success/failure indication

2. **Credential Rotation Rate** (Time Series)
   - Success rate by service
   - Failure rate by service
   - 5-minute rolling average

3. **Credential Rotation Duration** (Time Series)
   - p95 duration by service
   - p99 duration by service
   - Duration trends over time

4. **Query Validation Metrics** (Stacked Time Series)
   - Allowed queries (green)
   - Blocked queries (red)
   - Validation rate trends

5. **Security Event Timeline** (Table)
   - Recent security events
   - Event type, service, severity
   - Sortable by timestamp

6. **Failed Authentication Attempts** (Time Series)
   - Failed auth rate by service
   - Failed auth by reason
   - Spike detection

7. **Vault Access Patterns** (Time Series)
   - Read operations by path
   - Write operations by path
   - Access rate trends

8. **Failure Rate Gauges**
   - Query validation failure rate
   - Credential rotation failure rate
   - Threshold indicators

9. **Certificate Expiry** (Gauge)
   - Days until certificate expiration
   - Warning thresholds (30, 7 days)
   - Critical threshold (expired)

10. **Vault Access Error Rate** (Gauge)
    - Vault access error percentage
    - Error rate threshold indicators

#### Import Dashboard

```bash
# Import dashboard to Grafana
./scripts/monitoring/import_security_dashboard.sh

# With custom Grafana URL
./scripts/monitoring/import_security_dashboard.sh --grafana-url http://grafana:3001

# With authentication
./scripts/monitoring/import_security_dashboard.sh \
  --user admin \
  --password secure_password
```

---

## Alerts

### Alert Rules

**Location:** `config/monitoring/security-alert-rules.yml`

#### Credential Rotation Alerts

| Alert | Severity | Threshold | Description |
|-------|----------|-----------|-------------|
| `CredentialRotationFailed` | Critical | Any failure | Rotation failed for service |
| `CredentialRotationHighDuration` | Warning | > 120s (p95) | Rotation taking too long |
| `CredentialRotationStale` | Warning | > 30 days | Credentials not rotated |

#### Query Validation Alerts

| Alert | Severity | Threshold | Description |
|-------|----------|-----------|-------------|
| `HighQueryValidationFailureRate` | Warning | > 10% | High block rate |
| `SuspiciousQueryPattern` | Critical | Any injection | Injection attempt detected |
| `QueryValidationHighLatency` | Warning | > 100ms (p95) | Validation latency high |

#### Vault Access Alerts

| Alert | Severity | Threshold | Description |
|-------|----------|-----------|-------------|
| `VaultAccessFailureSpike` | Critical | > 1 error/sec | High error rate |
| `UnauthorizedVaultAccess` | Critical | Any unauthorized | Unauthorized access attempt |
| `VaultAccessAnomalousPattern` | Warning | 3x normal rate | Unusual access pattern |

#### Authentication Alerts

| Alert | Severity | Threshold | Description |
|-------|----------|-----------|-------------|
| `HighFailedAuthenticationRate` | Warning | > 5 failures/sec | High failure rate |
| `BruteForceAttackDetected` | Critical | > 10 failures/sec | Potential brute force |

#### Certificate Alerts

| Alert | Severity | Threshold | Description |
|-------|----------|-----------|-------------|
| `CertificateExpiringSoon` | Warning | < 30 days | Certificate expiring |
| `CertificateExpiringCritical` | Critical | < 7 days | Certificate expiring soon |
| `CertificateExpired` | Critical | Expired | Certificate has expired |

### Alert Configuration

```yaml
# Load alert rules into Prometheus
prometheus:
  rule_files:
    - /etc/prometheus/security-alert-rules.yml

# Configure AlertManager
alertmanager:
  receivers:
    - name: 'security-team'
      email_configs:
        - to: 'security@example.com'
      slack_configs:
        - channel: '#security-alerts'
          api_url: 'https://hooks.slack.com/services/...'
      pagerduty_configs:
        - service_key: 'your-pagerduty-key'
```

---

## Integration Tests

### Test Suite

**Location:** `tests/integration/test_credential_rotation.py`

#### Test Coverage

- ✅ Password generation (uniqueness, complexity)
- ✅ Service health checks (JanusGraph, OpenSearch, Grafana, Pulsar)
- ✅ Vault operations (read, write, backup)
- ✅ Credential rotation (all services)
- ✅ Rollback scenarios
- ✅ Health check validation
- ✅ Vault integration
- ✅ Concurrent operations
- ✅ Error handling
- ✅ Metrics recording

#### Running Tests

```bash
# Run all integration tests
pytest tests/integration/test_credential_rotation.py -v

# Run specific test class
pytest tests/integration/test_credential_rotation.py::TestCredentialRotation -v

# Run with coverage
pytest tests/integration/test_credential_rotation.py --cov=scripts.security -v

# Skip slow tests
pytest tests/integration/test_credential_rotation.py -v -m "not slow"
```

---

## Deployment

### Prerequisites

1. **Prometheus** running and scraping metrics
2. **Grafana** accessible at configured URL
3. **AlertManager** configured for notifications
4. **Vault** initialized and accessible
5. **Services** deployed and healthy

### Deployment Steps

#### 1. Deploy Monitoring Stack

```bash
# Deploy Prometheus, Grafana, AlertManager
./scripts/monitoring/deploy_monitoring.sh
```

#### 2. Configure Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'janusgraph-exporter'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 15s

  - job_name: 'security-metrics'
    static_configs:
      - targets: ['localhost:9091']
    scrape_interval: 15s
```

#### 3. Load Alert Rules

```bash
# Copy alert rules to Prometheus
cp config/monitoring/security-alert-rules.yml /etc/prometheus/

# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload
```

#### 4. Import Grafana Dashboard

```bash
# Import security dashboard
./scripts/monitoring/import_security_dashboard.sh

# Verify dashboard is accessible
curl -u admin:admin http://localhost:3001/api/dashboards/uid/security-dashboard
```

#### 5. Verify Metrics Collection

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Query sample metrics
curl 'http://localhost:9090/api/v1/query?query=credential_rotation_total'

# Check AlertManager status
curl http://localhost:9093/api/v1/status
```

---

## Troubleshooting

### Common Issues

#### Metrics Not Appearing

**Symptom:** Dashboard panels show "No data"

**Solutions:**
1. Verify Prometheus is scraping targets:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

2. Check exporter is running:
   ```bash
   curl http://localhost:8000/metrics
   ```

3. Verify metric names match dashboard queries:
   ```bash
   curl 'http://localhost:9090/api/v1/label/__name__/values'
   ```

#### Alerts Not Firing

**Symptom:** Expected alerts not triggering

**Solutions:**
1. Verify alert rules are loaded:
   ```bash
   curl http://localhost:9090/api/v1/rules
   ```

2. Check alert evaluation:
   ```bash
   curl http://localhost:9090/api/v1/alerts
   ```

3. Verify AlertManager configuration:
   ```bash
   curl http://localhost:9093/api/v1/status
   ```

#### Dashboard Import Fails

**Symptom:** Dashboard import script fails

**Solutions:**
1. Verify Grafana is accessible:
   ```bash
   curl http://localhost:3001/api/health
   ```

2. Check Prometheus datasource exists:
   ```bash
   curl -u admin:admin http://localhost:3001/api/datasources
   ```

3. Validate dashboard JSON:
   ```bash
   jq . config/monitoring/dashboards/security-dashboard.json
   ```

#### High Metric Cardinality

**Symptom:** Prometheus performance degradation

**Solutions:**
1. Review metric labels and reduce cardinality
2. Increase Prometheus retention settings
3. Use recording rules for expensive queries
4. Consider metric aggregation

### Debug Commands

```bash
# Check Prometheus configuration
promtool check config /etc/prometheus/prometheus.yml

# Validate alert rules
promtool check rules /etc/prometheus/security-alert-rules.yml

# Test alert rule expression
promtool query instant http://localhost:9090 \
  'rate(credential_rotation_total{status="failed"}[5m]) > 0'

# View Grafana logs
podman logs janusgraph-demo_grafana_1

# View Prometheus logs
podman logs janusgraph-demo_prometheus_1

# View AlertManager logs
podman logs janusgraph-demo_alertmanager_1
```

---

## Best Practices

### Metric Collection

1. **Use appropriate metric types:**
   - Counter for cumulative values (rotations, errors)
   - Gauge for current values (status, expiry time)
   - Histogram for distributions (duration, latency)

2. **Keep label cardinality low:**
   - Avoid high-cardinality labels (IDs, timestamps)
   - Use aggregation for detailed data
   - Consider recording rules for expensive queries

3. **Set appropriate scrape intervals:**
   - 15s for real-time metrics
   - 1m for less critical metrics
   - 5m for slow-changing metrics

### Dashboard Design

1. **Organize by audience:**
   - Security team: Threats, incidents, compliance
   - Operations: Performance, availability, errors
   - Developers: Debugging, troubleshooting

2. **Use appropriate visualizations:**
   - Time series for trends
   - Gauges for current status
   - Tables for detailed data
   - Heatmaps for distributions

3. **Set meaningful thresholds:**
   - Green: Normal operation
   - Yellow: Warning, attention needed
   - Red: Critical, immediate action required

### Alert Configuration

1. **Avoid alert fatigue:**
   - Set appropriate thresholds
   - Use `for` duration to reduce noise
   - Group related alerts
   - Implement alert routing

2. **Provide actionable information:**
   - Clear summary and description
   - Runbook links
   - Suggested actions
   - Context and impact

3. **Test alerts regularly:**
   - Verify alert rules fire correctly
   - Test notification channels
   - Review alert history
   - Update thresholds based on experience

---

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Credential Rotation Framework](../../scripts/security/credential_rotation_framework.py)
- [JanusGraph Exporter](../../scripts/monitoring/janusgraph_exporter.py)

---

**Last Updated:** 2026-02-11  
**Maintained By:** Security & Operations Team  
**Review Cycle:** Quarterly

# Made with Bob