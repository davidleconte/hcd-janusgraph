# Operations Runbook

## Document Information

- **Document Version:** 2.0.0
- **Last Updated:** 2026-02-19
- **Owner:** Operations Team
- **Review Cycle:** Quarterly
- **Status:** Active - Canonical Deterministic Runtime Runbook
- **Canonical Runtime Path:** `scripts/deployment/deterministic_setup_and_proof_wrapper.sh`
- **Canonical Pipeline:** `scripts/testing/run_demo_pipeline_repeatable.sh`
- **Authoritative Status:** `docs/project-status.md`

---

## Executive Summary

This runbook provides comprehensive operational procedures for the HCD JanusGraph Banking Compliance Platform, based on the **deterministic deployment system** and **gate-based validation framework**. All procedures align with the canonical scripts and architecture documentation.

### Quick Reference

| Emergency | Contact | Response Time |
|-----------|---------|---------------|
| P0 - System Down | ops-oncall@example.com | 15 minutes |
| P1 - Critical Issue | ops-senior@example.com | 1 hour |
| P2 - Major Issue | ops-lead@example.com | 4 hours |
| P3 - Minor Issue | ops-team@example.com | 1 business day |

### Canonical Commands

| Task | Command |
|------|---------|
| **Deterministic Deployment** | `bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json` |
| **Deploy Full Stack** | `cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh` |
| **Stop Full Stack** | `cd config/compose && bash ../../scripts/deployment/stop_full_stack.sh` |
| **Health Check** | `bash scripts/testing/check_graph_counts.sh` |
| **Preflight Validation** | `bash scripts/validation/preflight_check.sh --strict` |
| **Isolation Validation** | `bash scripts/validation/validate_podman_isolation.sh --strict` |

---

## Table of Contents

1. [Deterministic Operations](#1-deterministic-operations)
2. [Daily Operations](#2-daily-operations)
3. [Health Checks](#3-health-checks)
4. [Monitoring and Alerting](#4-monitoring-and-alerting)
5. [Gate-Based Troubleshooting](#5-gate-based-troubleshooting)
6. [Maintenance Procedures](#6-maintenance-procedures)
7. [Backup and Recovery](#7-backup-and-recovery)
8. [Scaling Operations](#8-scaling-operations)
9. [Security Operations](#9-security-operations)
10. [Incident Response](#10-incident-response)

---

## 1. Deterministic Operations

### 1.1 Canonical Deployment Command

**The single source of truth for deployment:**

```bash
# Full deterministic deployment with proof
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

**What this does:**
1. Validates environment (G0: Preflight)
2. Resets state deterministically (G3: Reset)
3. Deploys full stack (G5: Deploy/Vault)
4. Validates runtime contracts (G6: Runtime Contract)
5. Seeds graph data (G7: Seed)
6. Runs live notebooks (G8: Notebooks)
7. Verifies deterministic artifacts (G9: Determinism)

**Expected Duration:** 5-10 minutes (depending on hardware)

**Success Criteria:**
- Exit code: 0
- Status report exists at `exports/deterministic-status.json`
- All gates pass (G0-G9)
- Notebook report shows all `PASS`

### 1.2 Gate-Based Validation System

The deployment uses a **10-gate validation system** (G0-G9):

| Gate | Name | Purpose | Failure Code |
|------|------|---------|--------------|
| **G0** | Preflight | Environment validation | `G0_PRECHECK` |
| **G1** | (Reserved) | Future use | - |
| **G2** | Connection | Podman connectivity | `G2_CONNECTION` |
| **G3** | Reset | State reset | `G3_RESET` |
| **G4** | (Reserved) | Future use | - |
| **G5** | Deploy/Vault | Service deployment | `G5_DEPLOY_VAULT` |
| **G6** | Runtime Contract | Runtime validation | `G6_RUNTIME_CONTRACT` |
| **G7** | Seed | Graph seeding | `G7_SEED` |
| **G8** | Notebooks | Notebook execution | `G8_NOTEBOOKS` |
| **G9** | Determinism | Artifact verification | `G9_DETERMINISM` |

**See:** [`docs/architecture/deterministic-deployment-architecture.md`](../architecture/deterministic-deployment-architecture.md) for complete gate definitions.

### 1.3 Deployment Profiles

**Profile 1: Full Deterministic Proof (Production)**

```bash
# Complete deterministic deployment with all validations
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

**Profile 2: Fast Development (Skip Notebooks)**

```bash
# Deploy services only, skip notebook execution
bash scripts/testing/run_demo_pipeline_repeatable.sh --skip-notebooks
```

**Profile 3: Service Restart (No Reset)**

```bash
# Restart services without state reset
bash scripts/testing/run_demo_pipeline_repeatable.sh \
  --skip-preflight \
  --no-reset
```

**Profile 4: Validation Only (Services Running)**

```bash
# Validate running services without redeployment
bash scripts/testing/run_demo_pipeline_repeatable.sh \
  --skip-deploy \
  --skip-preflight
```

### 1.4 Environment Variables

**Required for deterministic operations:**

```bash
# Project isolation (MANDATORY)
export COMPOSE_PROJECT_NAME="janusgraph-demo"

# Podman connection (auto-resolved if not set)
export PODMAN_CONNECTION="podman-wxd"

# Deterministic seed (default: 42)
export DEMO_SEED=42

# Timeouts (seconds)
export DEMO_NOTEBOOK_TOTAL_TIMEOUT=420
export DEMO_NOTEBOOK_CELL_TIMEOUT=180
export MAX_HEALTH_WAIT_SEC=300
```

**Optional for advanced control:**

```bash
# Disable state reset (use with caution)
export DEMO_RESET_STATE=0

# Disable determinism verification
export DEMO_DETERMINISTIC_MODE=0

# Custom baseline directory
export DEMO_BASELINE_DIR="./exports/determinism-baselines"
```

### 1.5 Checking Deployment Status

**Check if deployment succeeded:**

```bash
# Check status report
cat exports/deterministic-status.json

# Expected output:
# {
#   "timestamp_utc": "2026-02-19T12:00:00.000Z",
#   "wrapper": "scripts/deployment/deterministic_setup_and_proof_wrapper.sh",
#   "pipeline_script": "scripts/testing/run_demo_pipeline_repeatable.sh",
#   "compose_project_name": "janusgraph-demo",
#   "args": "",
#   "exit_code": 0
# }
```

**Check which gate failed (if any):**

```bash
# Find latest run directory
LATEST_RUN=$(ls -t exports/ | grep "demo-" | head -1)

# Check failed gate
cat "exports/${LATEST_RUN}/failed_gate.txt"

# Possible values:
# - "none" = all gates passed
# - "G0_PRECHECK" = preflight failed
# - "G2_CONNECTION" = podman connection failed
# - "G3_RESET" = state reset failed
# - "G5_DEPLOY_VAULT" = deployment failed
# - "G6_RUNTIME_CONTRACT" = runtime validation failed
# - "G7_SEED" = graph seeding failed
# - "G8_NOTEBOOKS" = notebook execution failed
# - "G9_DETERMINISM" = determinism verification failed
```

**Check service status:**

```bash
# List all services in project
podman --remote ps --filter "label=io.podman.compose.project=janusgraph-demo"

# Check specific service health
podman --remote inspect janusgraph-demo_hcd-server_1 --format '{{.State.Status}}'
podman --remote inspect janusgraph-demo_jupyter_1 --format '{{.State.Status}}'
```

---

## 2. Daily Operations

### 2.1 Morning Checklist

**Automated morning health check:**

```bash
#!/bin/bash
# scripts/operations/morning_checklist.sh

echo "=== Morning Health Check ==="
echo "Date: $(date)"

# 1. Check deterministic status
echo "\n1. Last Deterministic Run:"
if [[ -f exports/deterministic-status.json ]]; then
    cat exports/deterministic-status.json | jq '.timestamp_utc, .exit_code'
else
    echo "   No recent deterministic run found"
fi

# 2. Check service status
echo "\n2. Service Status:"
podman --remote ps --filter "label=io.podman.compose.project=janusgraph-demo" \
    --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 3. Check disk space
echo "\n3. Disk Space:"
df -h | grep -E '(Filesystem|podman)'

# 4. Check recent errors (last hour)
echo "\n4. Recent Errors:"
podman --remote logs janusgraph-demo_hcd-server_1 --since 1h 2>&1 | grep -i error | tail -10

# 5. Check graph health
echo "\n5. Graph Health:"
bash scripts/testing/check_graph_counts.sh

# 6. Check certificate expiry
echo "\n6. Certificate Status:"
if [[ -f config/ssl/janusgraph.crt ]]; then
    openssl x509 -in config/ssl/janusgraph.crt -noout -enddate
fi

echo "\n=== Health Check Complete ==="
```

### 2.2 Log Review

**Daily log review procedure:**

```bash
# Check for errors in last 24 hours
podman --remote logs janusgraph-demo_hcd-server_1 --since 24h 2>&1 | \
    grep -i "error\|exception\|fatal" | tail -50

# Check JanusGraph server logs
podman --remote logs janusgraph-demo_jupyter_1 --since 24h 2>&1 | \
    grep -i "error" | tail -50

# Check authentication failures
podman --remote logs janusgraph-demo_analytics-api_1 --since 24h 2>&1 | \
    grep "auth.*fail" | wc -l

# Check Vault logs
podman --remote logs janusgraph-demo_vault_1 --since 24h 2>&1 | \
    grep -i "error\|denied" | tail -20
```

### 2.3 Metrics Review

**Key metrics to review daily:**

```bash
# Query latency P95 (Prometheus)
curl -s 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(query_duration_seconds_bucket[24h]))' | \
    jq '.data.result[0].value[1]'

# Error rate
curl -s 'http://localhost:9090/api/v1/query?query=rate(query_errors_total[24h])/rate(query_total[24h])*100' | \
    jq '.data.result[0].value[1]'

# Throughput
curl -s 'http://localhost:9090/api/v1/query?query=rate(query_total[24h])' | \
    jq '.data.result[0].value[1]'

# Resource utilization
podman --remote stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## 3. Health Checks

### 3.1 Automated Health Check Script

**Comprehensive health check:**

```bash
#!/usr/bin/env bash
# scripts/operations/health_check.sh

set -euo pipefail

PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"

echo "=== Health Check Report - $(date) ==="
echo "Project: $PROJECT_NAME"
echo "Connection: $PODMAN_CONNECTION"
echo ""

# Check Podman connection
echo "1. Podman Connection:"
if podman --remote --connection "$PODMAN_CONNECTION" ps >/dev/null 2>&1; then
    echo "   ✅ Connected"
else
    echo "   ❌ Connection failed"
    exit 1
fi

# Check services
echo "2. Service Status:"
SERVICES=(
    "janusgraph-demo_hcd-server_1"
    "janusgraph-demo_vault_1"
    "janusgraph-demo_analytics-api_1"
    "janusgraph-demo_jupyter_1"
    "janusgraph-demo_pulsar_1"
)

ALL_HEALTHY=true
for service in "${SERVICES[@]}"; do
    STATUS=$(podman --remote inspect "$service" --format '{{.State.Status}}' 2>/dev/null || echo "missing")
    if [[ "$STATUS" == "running" ]]; then
        echo "   ✅ $service: running"
    else
        echo "   ❌ $service: $STATUS"
        ALL_HEALTHY=false
    fi
done

# Check graph connectivity
echo "3. Graph Connectivity:"
if bash scripts/testing/check_graph_counts.sh >/dev/null 2>&1; then
    echo "   ✅ Graph accessible"
else
    echo "   ❌ Graph not accessible"
    ALL_HEALTHY=false
fi

# Check Vault
echo "4. Vault Status:"
VAULT_STATUS=$(podman --remote exec janusgraph-demo_vault_1 vault status -format=json 2>/dev/null | jq -r '.sealed' || echo "error")
if [[ "$VAULT_STATUS" == "false" ]]; then
    echo "   ✅ Vault unsealed"
elif [[ "$VAULT_STATUS" == "true" ]]; then
    echo "   ⚠️  Vault sealed (needs unseal)"
    ALL_HEALTHY=false
else
    echo "   ❌ Vault error"
    ALL_HEALTHY=false
fi

echo ""
if [[ "$ALL_HEALTHY" == "true" ]]; then
    echo "✅ All systems healthy"
    exit 0
else
    echo "❌ Some systems unhealthy"
    exit 1
fi
```

### 3.2 Component-Specific Health Checks

**HCD/Cassandra:**

```bash
# Check node status
podman --remote exec janusgraph-demo_hcd-server_1 nodetool status

# Check if accepting connections
podman --remote exec janusgraph-demo_hcd-server_1 \
    cqlsh -e "SELECT now() FROM system.local;"

# Check keyspace
podman --remote exec janusgraph-demo_hcd-server_1 \
    cqlsh -e "DESCRIBE KEYSPACES;"
```

**JanusGraph:**

```bash
# Check graph counts
bash scripts/testing/check_graph_counts.sh

# Check via Gremlin console
podman --remote exec janusgraph-demo_gremlin-console_1 \
    bin/gremlin.sh -e "g.V().count()"
```

**Vault:**

```bash
# Check seal status
podman --remote exec janusgraph-demo_vault_1 vault status

# Check secrets (requires VAULT_TOKEN)
source .vault-keys
podman --remote exec -e VAULT_TOKEN=$VAULT_ROOT_TOKEN \
    janusgraph-demo_vault_1 vault kv list janusgraph/
```

**Pulsar:**

```bash
# List topics
podman --remote exec janusgraph-demo_pulsar-cli_1 \
    bin/pulsar-admin topics list public/banking

# Check topic stats
podman --remote exec janusgraph-demo_pulsar-cli_1 \
    bin/pulsar-admin topics stats persistent://public/banking/persons-events
```

---

## 4. Monitoring and Alerting

### 4.1 Alert Response Procedures

**Critical Alerts (P0):**

1. **System Down (G5_DEPLOY_VAULT failure)**
   - Acknowledge alert immediately
   - Check service status: `podman --remote ps`
   - Review deployment logs: `cat exports/demo-*/deploy.log`
   - Attempt deterministic redeployment
   - Escalate if not resolved in 15 minutes

2. **Data Loss Risk**
   - Stop all writes immediately
   - Assess backup status: `ls -lh /backups/`
   - Contact database team
   - Do not attempt recovery without approval

3. **Security Breach**
   - Isolate affected systems
   - Preserve evidence: `podman --remote logs > incident.log`
   - Contact security team immediately
   - Follow incident response plan

**High Priority Alerts (P1):**

1. **High Error Rate (G8_NOTEBOOKS failure)**
   - Check notebook report: `cat exports/demo-*/notebook_run_report.tsv`
   - Identify failing notebooks
   - Review notebook logs: `cat exports/demo-*/notebooks.log`
   - Check for data issues or service degradation

2. **Performance Degradation**
   - Check resource utilization: `podman --remote stats`
   - Review slow query log
   - Check for long-running queries
   - Consider scaling if needed

### 4.2 Monitoring Stack Access

**Access monitoring services:**

```bash
# Prometheus
open http://localhost:9090

# Grafana (admin/admin)
open http://localhost:3001

# AlertManager
open http://localhost:9093

# JanusGraph Exporter metrics
curl http://localhost:9091/metrics
```

---

## 5. Gate-Based Troubleshooting

### 5.1 Gate Failure Diagnosis

**Identify which gate failed:**

```bash
# Find latest run
LATEST_RUN=$(ls -t exports/ | grep "demo-" | head -1)

# Check failed gate
FAILED_GATE=$(cat "exports/${LATEST_RUN}/failed_gate.txt")

echo "Failed gate: $FAILED_GATE"

# View relevant log
case "$FAILED_GATE" in
    G0_PRECHECK)
        cat "exports/${LATEST_RUN}/preflight.log"
        ;;
    G2_CONNECTION)
        echo "Podman connection failed"
        podman system connection list
        ;;
    G3_RESET)
        cat "exports/${LATEST_RUN}/state_reset.log"
        ;;
    G5_DEPLOY_VAULT)
        cat "exports/${LATEST_RUN}/deploy.log"
        ;;
    G6_RUNTIME_CONTRACT)
        cat "exports/${LATEST_RUN}/runtime_contracts.log"
        ;;
    G7_SEED)
        cat "exports/${LATEST_RUN}/seed_graph.log"
        ;;
    G8_NOTEBOOKS)
        cat "exports/${LATEST_RUN}/notebooks.log"
        cat "exports/${LATEST_RUN}/notebook_run_report.tsv"
        ;;
    G9_DETERMINISM)
        cat "exports/${LATEST_RUN}/determinism.log"
        ;;
esac
```

### 5.2 Gate-Specific Recovery Procedures

**G0: Preflight Failure**

```bash
# Run preflight check manually
bash scripts/validation/preflight_check.sh --strict

# Common issues:
# - uv not installed: curl -LsSf https://astral.sh/uv/install.sh | sh
# - podman not installed: brew install podman podman-compose
# - podman machine not running: podman machine start
# - conda env not activated: conda activate janusgraph-analysis
```

**G2: Connection Failure**

```bash
# Check podman connections
podman system connection list

# Check podman machine
podman machine list

# Start machine if stopped
podman machine start

# Test connection
podman --remote ps
```

**G3: Reset Failure**

```bash
# Manual state reset
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml down -v

# Check for stuck containers
podman --remote ps -a | grep janusgraph-demo

# Force remove if needed
podman --remote rm -f $(podman --remote ps -a -q --filter "label=io.podman.compose.project=janusgraph-demo")
```

**G5: Deploy/Vault Failure**

```bash
# Check deployment logs
cat exports/demo-*/deploy.log | tail -100

# Common issues:
# - Port conflicts: Check if ports 8182, 9042, 8200 are in use
# - Image build failure: Check docker/hcd/Dockerfile
# - Volume permission issues: Check podman machine disk space

# Manual deployment
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh
```

**G6: Runtime Contract Failure**

```bash
# Check runtime contracts
bash scripts/testing/check_runtime_contracts.sh

# Common issues:
# - Missing API_JWT_SECRET: export API_JWT_SECRET="test-secret"
# - Missing dependencies: conda activate janusgraph-analysis && uv pip install -r requirements.txt
```

**G7: Seed Failure**

```bash
# Check seed logs
cat exports/demo-*/seed_graph.log

# Manual seed
bash scripts/testing/seed_demo_graph.sh

# Verify graph data
bash scripts/testing/check_graph_counts.sh
```

**G8: Notebooks Failure**

```bash
# Check notebook report
cat exports/demo-*/notebook_run_report.tsv

# Identify failing notebooks
awk -F'\t' '$2 != "PASS" && NR>1 {print $1, $2, $3}' exports/demo-*/notebook_run_report.tsv

# Run single notebook manually
conda activate janusgraph-analysis
jupyter nbconvert --to notebook --execute notebooks/01_Basic_Graph_Operations.ipynb
```

**G9: Determinism Failure**

```bash
# Check determinism logs
cat exports/demo-*/determinism.log

# Common issues:
# - Baseline missing: First run creates baseline
# - Artifact mismatch: Check for non-deterministic code
# - Timing issues: Increase timeouts

# Regenerate baseline
rm -rf exports/determinism-baselines
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json
```

### 5.3 Troubleshooting Flowchart

```
Deployment Failed?
    |
    ├─> Check failed_gate.txt
    |
    ├─> G0_PRECHECK?
    |   └─> Run preflight_check.sh --strict
    |       └─> Fix environment issues
    |
    ├─> G2_CONNECTION?
    |   └─> Check podman machine status
    |       └─> Start machine or fix connection
    |
    ├─> G3_RESET?
    |   └─> Manual cleanup: podman-compose down -v
    |       └─> Remove stuck containers
    |
    ├─> G5_DEPLOY_VAULT?
    |   └─> Check deploy.log
    |       └─> Fix port conflicts or image issues
    |
    ├─> G6_RUNTIME_CONTRACT?
    |   └─> Check runtime_contracts.log
    |       └─> Fix missing secrets or dependencies
    |
    ├─> G7_SEED?
    |   └─> Check seed_graph.log
    |       └─> Verify graph connectivity
    |
    ├─> G8_NOTEBOOKS?
    |   └─> Check notebook_run_report.tsv
    |       └─> Debug failing notebooks
    |
    └─> G9_DETERMINISM?
        └─> Check determinism.log
            └─> Regenerate baseline or fix non-determinism
```

**See:** [`docs/architecture/deterministic-deployment-architecture.md`](../architecture/deterministic-deployment-architecture.md) for complete gate troubleshooting.

---

## 6. Maintenance Procedures

### 6.1 Routine Maintenance Schedule

| Task | Frequency | Day/Time | Duration | Command |
|------|-----------|----------|----------|---------|
| Health check | Daily | 9:00 AM | 5 min | `bash scripts/operations/health_check.sh` |
| Log review | Daily | 10:00 AM | 15 min | Review logs for errors |
| Backup verification | Daily | 3:00 AM | 30 min | `bash scripts/backup/test_backup.sh` |
| Security updates | Weekly | Sunday 2:00 AM | 2 hours | Update images and redeploy |
| Performance review | Weekly | Monday 10:00 AM | 1 hour | Review metrics in Grafana |
| Deterministic proof | Weekly | Monday 11:00 AM | 10 min | Run full deterministic deployment |
| Capacity planning | Monthly | 1st Monday | 2 hours | Review resource usage trends |
| DR test | Quarterly | TBD | 4 hours | Full disaster recovery drill |

### 6.2 Planned Maintenance Procedure

**Pre-Maintenance:**

1. Schedule maintenance window (off-peak hours)
2. Notify stakeholders 48 hours in advance
3. Create backup: `bash scripts/backup/backup_volumes.sh`
4. Prepare rollback plan
5. Review maintenance steps

**During Maintenance:**

```bash
# 1. Stop services gracefully
cd config/compose
bash ../../scripts/deployment/stop_full_stack.sh

# 2. Perform maintenance tasks
# (updates, configuration changes, etc.)

# 3. Deploy with deterministic validation
cd ../..
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
    --status-report exports/deterministic-status.json

# 4. Verify health
bash scripts/operations/health_check.sh

# 5. Run smoke tests
bash scripts/testing/check_graph_counts.sh
```

**Post-Maintenance:**

1. Verify all services healthy
2. Check deterministic status report
3. Monitor for issues (1 hour)
4. Update maintenance log
5. Notify stakeholders of completion

### 6.3 Certificate Renewal

**Procedure:**

```bash
# Check certificate expiry
openssl x509 -in config/ssl/janusgraph.crt -noout -enddate

# Regenerate certificates
bash scripts/security/generate_certificates.sh

# Redeploy services
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# Verify new certificate
openssl s_client -connect localhost:18182 -showcerts < /dev/null
```

---

## 7. Backup and Recovery

### 7.1 Backup Procedures

**Daily Backup:**

```bash
#!/bin/bash
# scripts/backup/daily_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/daily"
PROJECT_NAME="janusgraph-demo"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup Cassandra snapshots
podman --remote exec janusgraph-demo_hcd-server_1 nodetool snapshot

# Copy snapshots
podman --remote cp janusgraph-demo_hcd-server_1:/var/lib/cassandra/data \
    "$BACKUP_DIR/cassandra_$DATE"

# Backup Vault data
podman --remote cp janusgraph-demo_vault_1:/vault/data \
    "$BACKUP_DIR/vault_$DATE"

# Compress backups
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" \
    "$BACKUP_DIR/cassandra_$DATE" \
    "$BACKUP_DIR/vault_$DATE"

# Encrypt backup
gpg --encrypt --recipient ops@example.com \
    "$BACKUP_DIR/backup_$DATE.tar.gz"

# Upload to cloud storage (if configured)
# aws s3 cp "$BACKUP_DIR/backup_$DATE.tar.gz.gpg" s3://backups/janusgraph/

# Clean up local files older than 7 days
find "$BACKUP_DIR" -name "*.tar.gz*" -mtime +7 -delete

echo "Backup completed: backup_$DATE.tar.gz.gpg"
```

### 7.2 Recovery Procedures

**Full System Recovery:**

```bash
#!/bin/bash
# scripts/backup/restore.sh

BACKUP_FILE=$1

if [[ -z "$BACKUP_FILE" ]]; then
    echo "Usage: $0 <backup_file.tar.gz.gpg>"
    exit 1
fi

# Stop services
cd config/compose
bash ../../scripts/deployment/stop_full_stack.sh

# Restore from backup
gpg --decrypt "$BACKUP_FILE" | tar -xzf - -C /tmp/restore

# Copy data back
podman --remote cp /tmp/restore/cassandra_* \
    janusgraph-demo_hcd-server_1:/var/lib/cassandra/data

podman --remote cp /tmp/restore/vault_* \
    janusgraph-demo_vault_1:/vault/data

# Start services with deterministic validation
cd ../..
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
    --status-report exports/deterministic-status.json

# Verify recovery
bash scripts/operations/health_check.sh
```

---

## 8. Scaling Operations

### 8.1 Horizontal Scaling

**Not currently supported in single-node deployment.**

For production horizontal scaling:
- Deploy to Kubernetes/OpenShift using Helm charts in `helm/`
- Use StatefulSets for Cassandra
- Use Deployments for JanusGraph servers
- Configure load balancer for API endpoints

### 8.2 Vertical Scaling

**Increase resources for Podman machine:**

```bash
# Stop machine
podman machine stop

# Remove machine
podman machine rm

# Create new machine with more resources
podman machine init \
    --cpus 8 \
    --memory 16384 \
    --disk-size 100 \
    --now

# Redeploy
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
    --status-report exports/deterministic-status.json
```

**Increase container resources:**

Edit `config/compose/docker-compose.full.yml`:

```yaml
services:
  hcd-server:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
```

Then redeploy:

```bash
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh
```

---

## 9. Security Operations

### 9.1 Security Monitoring

**Daily Security Checks:**

```bash
# Check for failed authentication attempts
podman --remote logs janusgraph-demo_analytics-api_1 | \
    grep "authentication failed" | wc -l

# Check for suspicious activity
podman --remote logs janusgraph-demo_hcd-server_1 | \
    grep -E "DROP|DELETE|TRUNCATE" | tail -20

# Review Vault audit log
podman --remote exec janusgraph-demo_vault_1 \
    cat /vault/logs/audit.log | tail -50

# Check certificate expiry
openssl x509 -in config/ssl/janusgraph.crt -noout -enddate
```

### 9.2 Security Incident Response

**Immediate Actions:**

1. Isolate affected systems
2. Preserve evidence: `podman --remote logs > incident-$(date +%Y%m%d).log`
3. Contact security team
4. Follow incident response plan in `SECURITY.md`

**Post-Incident:**

1. Conduct root cause analysis
2. Update security procedures
3. Rotate credentials: `bash scripts/security/rotate_credentials.sh`
4. Update documentation

---

## 10. Incident Response

### 10.1 Incident Classification

| Priority | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **P0** | System down, data loss | 15 minutes | Complete outage, G5 failure |
| **P1** | Critical functionality impaired | 1 hour | G8 failure, high error rate |
| **P2** | Major functionality degraded | 4 hours | Performance issues, G7 failure |
| **P3** | Minor issues | 1 business day | UI bugs, minor errors |

### 10.2 Incident Response Steps

1. **Detect and Alert**
   - Automated monitoring alerts
   - User reports
   - Health check failures
   - Gate failures in deterministic deployment

2. **Assess and Classify**
   - Determine severity (P0-P3)
   - Identify failed gate (G0-G9)
   - Estimate impact
   - Check status report: `cat exports/deterministic-status.json`

3. **Respond and Mitigate**
   - Follow gate-specific recovery procedure
   - Implement workarounds
   - Communicate status to stakeholders

4. **Resolve and Recover**
   - Fix root cause
   - Run deterministic deployment to verify
   - Monitor for recurrence

5. **Document and Learn**
   - Write incident report
   - Conduct post-mortem
   - Update runbooks and procedures

### 10.3 Escalation Matrix

| Level | Role | Contact | When to Escalate |
|-------|------|---------|------------------|
| **L1** | On-Call Engineer | ops-oncall@example.com | Initial response |
| **L2** | Senior Engineer | ops-senior@example.com | Not resolved in 30 min |
| **L3** | Team Lead | ops-lead@example.com | Not resolved in 2 hours |
| **L4** | Engineering Manager | eng-manager@example.com | Critical impact > 4 hours |
| **L5** | CTO | cto@example.com | Business-critical outage |

---

## Appendices

### Appendix A: Command Reference

**Quick Commands:**

```bash
# Deterministic deployment
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
    --status-report exports/deterministic-status.json

# Deploy full stack
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh

# Stop full stack
cd config/compose && bash ../../scripts/deployment/stop_full_stack.sh

# Health check
bash scripts/operations/health_check.sh

# Check graph
bash scripts/testing/check_graph_counts.sh

# View logs
podman --remote logs -f janusgraph-demo_hcd-server_1

# Check status
podman --remote ps --filter "label=io.podman.compose.project=janusgraph-demo"

# Execute command in container
podman --remote exec janusgraph-demo_hcd-server_1 bash

# Check failed gate
cat exports/demo-*/failed_gate.txt

# View deployment status
cat exports/deterministic-status.json
```

### Appendix B: Contact Information

- **Operations Team:** ops-team@example.com
- **On-Call:** ops-oncall@example.com (24/7)
- **Security Team:** security@example.com
- **Database Team:** dba@example.com
- **Platform Team:** platform@example.com

### Appendix C: Related Documentation

- **Architecture:**
  - [Deployment Architecture](../architecture/deployment-architecture.md)
  - [Deterministic Deployment Architecture](../architecture/deterministic-deployment-architecture.md)
  - [Podman Isolation Architecture](../architecture/podman-isolation-architecture.md)
  - [Gate-Based Validation (ADR-016)](../architecture/adr-016-gate-based-validation.md)

- **Operations:**
  - [Disaster Recovery Plan](disaster-recovery-plan.md)
  - [Security Monitoring](../monitoring/security-monitoring.md)
  - [Project Status](../project-status.md)

- **Development:**
  - [AGENTS.md](../../.bob/rules-code/AGENTS.md) - Agent operational rules
  - [QUICKSTART.md](../../QUICKSTART.md) - Quick start guide
  - [README.md](../../README.md) - Project overview

---

**Document Classification:** Internal - Operational  
**Next Review Date:** 2026-05-19  
**Document Owner:** Operations Team  
**Version:** 2.0.0 (Deterministic Operations)

---

## Change Log

### Version 2.0.0 (2026-02-19)
- **Major rewrite** to align with deterministic deployment system
- Added gate-based troubleshooting procedures (G0-G9)
- Integrated canonical deployment commands
- Added deterministic operation profiles
- Updated all procedures to use podman commands
- Added gate-specific recovery procedures
- Removed legacy docker-compose references
- Added comprehensive troubleshooting flowchart
- Updated health checks to use deterministic scripts
- Added deployment status checking procedures

### Version 1.0.0 (2026-02-18)
- Initial version with legacy procedures
- Basic health checks and monitoring
- Traditional deployment procedures
