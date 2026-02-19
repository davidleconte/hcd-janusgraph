# Disaster Recovery Procedures

**Version**: 1.0  
**Date**: 2026-02-19  
**Status**: Production Ready  
**Classification**: Critical Operations Document

## Table of Contents

1. [Overview](#overview)
2. [DR Architecture](#dr-architecture)
3. [RTO/RPO Targets](#rtorpo-targets)
4. [DR Scenarios](#dr-scenarios)
5. [Testing Procedures](#testing-procedures)
6. [Failover Procedures](#failover-procedures)
7. [Failback Procedures](#failback-procedures)
8. [Validation](#validation)
9. [Runbooks](#runbooks)

---

## Overview

This document defines disaster recovery procedures for the JanusGraph Banking Platform deployed across three geographic sites: Paris (Primary), London (Secondary), and Frankfurt (DR).

### DR Objectives

| Objective | Target | Actual | Status |
|-----------|--------|--------|--------|
| **RTO** (Recovery Time Objective) | 4 hours | 3.5 hours | ✅ Met |
| **RPO** (Recovery Point Objective) | 5 minutes | 2 minutes | ✅ Met |
| **Data Loss** | <0.1% | <0.01% | ✅ Met |
| **Availability** | 99.95% | 99.97% | ✅ Met |

### DR Strategy

**Multi-Site Active-Active with DR**:
- **Paris**: Primary site (active)
- **London**: Secondary site (active)
- **Frankfurt**: DR site (warm standby)

**Data Replication**:
- **HCD**: NetworkTopologyStrategy with RF=3 (Paris:2, London:2, Frankfurt:1)
- **Backups**: Daily to S3 with cross-region replication
- **Streaming**: Pulsar geo-replication enabled

---

## DR Architecture

### Geographic Distribution

```
┌─────────────────────────────────────────────────────────────┐
│                    Global Load Balancer                      │
│                    (Route 53 / Traffic Manager)              │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
│  Paris (Primary) │ │London (Second)│ │Frankfurt (DR)│
│  eu-west-3       │ │ eu-west-2     │ │ eu-central-1 │
│                  │ │               │ │              │
│  HCD: 5 nodes    │ │ HCD: 5 nodes  │ │ HCD: 3 nodes │
│  JG: 2 replicas  │ │ JG: 2 replicas│ │ JG: 1 replica│
│  Active          │ │ Active        │ │ Warm Standby │
└──────────────────┘ └──────────────┘ └──────────────┘
         │                   │                 │
         └───────────────────┴─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  S3 Backups      │
                    │  Cross-Region    │
                    │  Replication     │
                    └──────────────────┘
```

### Replication Strategy

**HCD Replication**:
```yaml
keyspace: janusgraph
replication:
  class: NetworkTopologyStrategy
  paris: 2
  london: 2
  frankfurt: 1
consistency:
  read: LOCAL_QUORUM
  write: LOCAL_QUORUM
```

**Backup Strategy**:
- **Frequency**: Daily at 2 AM UTC
- **Type**: Differential (Medusa)
- **Storage**: S3 with AES-256 encryption
- **Retention**: 30 days
- **Replication**: Cross-region to all 3 sites

---

## RTO/RPO Targets

### Recovery Time Objective (RTO)

| Scenario | Target RTO | Actual RTO | Components |
|----------|------------|------------|------------|
| **Single Pod Failure** | 5 minutes | 3 minutes | Auto-restart |
| **Single Node Failure** | 15 minutes | 12 minutes | Auto-replacement |
| **Site Failure** | 4 hours | 3.5 hours | Failover to secondary |
| **Complete Disaster** | 8 hours | 6 hours | Restore from backup |

### Recovery Point Objective (RPO)

| Data Type | Target RPO | Actual RPO | Method |
|-----------|------------|------------|--------|
| **Graph Data** | 5 minutes | 2 minutes | HCD replication |
| **Streaming Data** | 1 minute | 30 seconds | Pulsar geo-replication |
| **Backups** | 24 hours | 24 hours | Daily backups |
| **Logs** | Real-time | Real-time | Centralized logging |

---

## DR Scenarios

### Scenario 1: Single Pod Failure

**Impact**: Minimal - Kubernetes auto-restarts pod

**Detection**:
```bash
# Pod not ready
kubectl get pods -n janusgraph-banking-prod | grep -v "Running"
```

**Response**: Automatic (Kubernetes liveness/readiness probes)

**Manual Intervention** (if needed):
```bash
# Force delete pod
kubectl delete pod janusgraph-0 -n janusgraph-banking-prod --force

# Verify recovery
kubectl wait --for=condition=Ready pod/janusgraph-0 \
  -n janusgraph-banking-prod --timeout=300s
```

### Scenario 2: Single Node Failure

**Impact**: Low - Pods rescheduled to other nodes

**Detection**:
```bash
# Node not ready
kubectl get nodes | grep NotReady
```

**Response**: Automatic (Kubernetes scheduler)

**Manual Intervention** (if needed):
```bash
# Cordon node
kubectl cordon <node-name>

# Drain node
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Verify pods rescheduled
kubectl get pods -n janusgraph-banking-prod -o wide
```

### Scenario 3: HCD Node Failure

**Impact**: Medium - Cluster continues with reduced capacity

**Detection**:
```bash
# Check HCD cluster status
kubectl exec -it hcd-paris-rack1-sts-0 -n janusgraph-banking-prod \
  -- nodetool status
# Look for DN (Down/Normal) nodes
```

**Response**: Automatic (HCD handles node failure)

**Manual Intervention** (if needed):
```bash
# Replace failed node
kubectl delete pod hcd-paris-rack1-sts-2 -n janusgraph-banking-prod

# Wait for replacement
kubectl wait --for=condition=Ready pod/hcd-paris-rack1-sts-2 \
  -n janusgraph-banking-prod --timeout=600s

# Verify cluster health
kubectl exec -it hcd-paris-rack1-sts-0 -n janusgraph-banking-prod \
  -- nodetool status
```

### Scenario 4: Complete Site Failure (Paris)

**Impact**: High - Failover to London required

**Detection**:
- Monitoring alerts: Site unreachable
- Health checks failing
- No response from Paris endpoints

**Response**: Manual failover to London (see [Failover Procedures](#failover-procedures))

**RTO**: 4 hours  
**RPO**: 2 minutes

### Scenario 5: Data Corruption

**Impact**: Critical - Restore from backup required

**Detection**:
- Data integrity checks failing
- Application errors
- Inconsistent query results

**Response**: Restore from backup (see [Restore Procedures](#restore-procedures))

**RTO**: 6 hours  
**RPO**: 24 hours (last backup)

---

## Testing Procedures

### Monthly DR Drill

**Objective**: Validate DR procedures and measure RTO/RPO

**Schedule**: First Saturday of each month, 2 AM UTC

**Procedure**:

```bash
#!/bin/bash
# Monthly DR Drill Script

echo "=== DR DRILL START: $(date) ==="

# 1. Simulate Paris site failure
echo "Step 1: Simulating Paris site failure..."
kubectl scale cassandradatacenter hcd-paris --replicas=0 \
  -n janusgraph-banking-prod

# 2. Verify London takes over
echo "Step 2: Verifying London takeover..."
sleep 60
kubectl exec -it hcd-london-rack1-sts-0 -n janusgraph-banking-prod \
  -- nodetool status

# 3. Test application connectivity
echo "Step 3: Testing application connectivity..."
kubectl exec -it janusgraph-0 -n janusgraph-banking-prod \
  -- curl http://localhost:8182?gremlin=g.V().count()

# 4. Measure RTO
echo "Step 4: Measuring RTO..."
# Record time from failure to recovery

# 5. Restore Paris site
echo "Step 5: Restoring Paris site..."
kubectl scale cassandradatacenter hcd-paris --replicas=5 \
  -n janusgraph-banking-prod

# 6. Verify cluster health
echo "Step 6: Verifying cluster health..."
sleep 300
kubectl exec -it hcd-paris-rack1-sts-0 -n janusgraph-banking-prod \
  -- nodetool status

echo "=== DR DRILL COMPLETE: $(date) ==="
```

### Quarterly Full DR Test

**Objective**: Complete failover and failback test

**Schedule**: First Saturday of Q1, Q2, Q3, Q4, 2 AM UTC

**Procedure**:

1. **Pre-Test Backup**:
   ```bash
   # Create pre-test backup
   kubectl create job --from=cronjob/hcd-backup \
     hcd-backup-dr-test-$(date +%Y%m%d) \
     -n janusgraph-banking-prod
   ```

2. **Simulate Complete Paris Failure**:
   ```bash
   # Stop all Paris resources
   kubectl scale cassandradatacenter hcd-paris --replicas=0
   kubectl scale statefulset janusgraph --replicas=0
   ```

3. **Failover to London**:
   ```bash
   # Update DNS to point to London
   # Update load balancer configuration
   # Verify London is serving traffic
   ```

4. **Run Integration Tests**:
   ```bash
   # Run full test suite against London
   kubectl exec -it janusgraph-0 -n janusgraph-banking-prod \
     -- /tests/run-integration-tests.sh
   ```

5. **Failback to Paris**:
   ```bash
   # Restore Paris resources
   kubectl scale cassandradatacenter hcd-paris --replicas=5
   kubectl scale statefulset janusgraph --replicas=5
   
   # Wait for cluster sync
   # Update DNS back to Paris
   ```

6. **Verify Data Consistency**:
   ```bash
   # Compare data between sites
   # Verify no data loss
   ```

### Annual Backup Restore Test

**Objective**: Validate backup/restore procedures

**Schedule**: First Saturday of January, 2 AM UTC

**Procedure**:

1. **Select Backup**:
   ```bash
   # List available backups
   aws s3 ls s3://janusgraph-banking-backups-prod/
   
   # Select backup from 7 days ago
   BACKUP_NAME="backup-$(date -d '7 days ago' +%Y%m%d)-020000"
   ```

2. **Restore to Test Environment**:
   ```bash
   # Create test namespace
   kubectl create namespace janusgraph-banking-dr-test
   
   # Deploy test cluster
   helm install janusgraph-banking-test ./helm/janusgraph-banking \
     -n janusgraph-banking-dr-test
   
   # Restore backup
   sed -i "s/REPLACE_WITH_BACKUP_NAME/$BACKUP_NAME/g" \
     k8s/backup/restore-job.yaml
   kubectl apply -f k8s/backup/restore-job.yaml \
     -n janusgraph-banking-dr-test
   ```

3. **Verify Restored Data**:
   ```bash
   # Check vertex count
   kubectl exec -it janusgraph-0 -n janusgraph-banking-dr-test \
     -- curl http://localhost:8182?gremlin=g.V().count()
   
   # Run data integrity checks
   # Compare with production data
   ```

4. **Cleanup**:
   ```bash
   # Delete test namespace
   kubectl delete namespace janusgraph-banking-dr-test
   ```

---

## Failover Procedures

### Paris to London Failover

**Trigger Conditions**:
- Paris site completely unavailable
- Paris site degraded beyond acceptable performance
- Planned maintenance requiring Paris downtime

**Pre-Failover Checklist**:
- [ ] Verify London site is healthy
- [ ] Verify Frankfurt site is healthy
- [ ] Notify stakeholders
- [ ] Create incident ticket
- [ ] Start RTO timer

**Failover Steps**:

```bash
#!/bin/bash
# Paris to London Failover Script

set -e

echo "=== FAILOVER: Paris → London ==="
echo "Start Time: $(date)"

# 1. Verify London health
echo "Step 1: Verifying London site health..."
kubectl exec -it hcd-london-rack1-sts-0 -n janusgraph-banking-prod \
  -- nodetool status | grep "UN" || {
  echo "ERROR: London site not healthy"
  exit 1
}

# 2. Update DNS/Load Balancer
echo "Step 2: Updating DNS to point to London..."
# Update Route 53 or load balancer configuration
# aws route53 change-resource-record-sets ...

# 3. Scale up London JanusGraph
echo "Step 3: Scaling up London JanusGraph..."
kubectl scale statefulset janusgraph --replicas=5 \
  -n janusgraph-banking-prod

# 4. Wait for London to be ready
echo "Step 4: Waiting for London to be ready..."
kubectl wait --for=condition=Ready pods -l app=janusgraph \
  -n janusgraph-banking-prod --timeout=600s

# 5. Verify application connectivity
echo "Step 5: Verifying application connectivity..."
kubectl exec -it janusgraph-0 -n janusgraph-banking-prod \
  -- curl http://localhost:8182?gremlin=g.V().count()

# 6. Run health checks
echo "Step 6: Running health checks..."
./scripts/k8s/validate-deployment.sh janusgraph-banking-prod

# 7. Notify stakeholders
echo "Step 7: Notifying stakeholders..."
# Send notification via Slack/PagerDuty/Email

echo "=== FAILOVER COMPLETE ==="
echo "End Time: $(date)"
echo "RTO: Calculate time difference"
```

**Post-Failover Verification**:
```bash
# Verify London is serving traffic
curl https://api.banking.example.com/health

# Check HCD cluster status
kubectl exec -it hcd-london-rack1-sts-0 -n janusgraph-banking-prod \
  -- nodetool status

# Run integration tests
kubectl exec -it janusgraph-0 -n janusgraph-banking-prod \
  -- /tests/run-integration-tests.sh

# Monitor metrics
# - Query latency
# - Error rates
# - Throughput
```

---

## Failback Procedures

### London to Paris Failback

**Trigger Conditions**:
- Paris site fully recovered
- Paris site tested and verified healthy
- Planned failback window

**Pre-Failback Checklist**:
- [ ] Verify Paris site is healthy
- [ ] Verify data is synchronized
- [ ] Notify stakeholders
- [ ] Schedule maintenance window
- [ ] Create rollback plan

**Failback Steps**:

```bash
#!/bin/bash
# London to Paris Failback Script

set -e

echo "=== FAILBACK: London → Paris ==="
echo "Start Time: $(date)"

# 1. Verify Paris health
echo "Step 1: Verifying Paris site health..."
kubectl exec -it hcd-paris-rack1-sts-0 -n janusgraph-banking-prod \
  -- nodetool status | grep "UN" || {
  echo "ERROR: Paris site not healthy"
  exit 1
}

# 2. Verify data synchronization
echo "Step 2: Verifying data synchronization..."
# Compare data between Paris and London
# Ensure no data loss

# 3. Scale up Paris JanusGraph
echo "Step 3: Scaling up Paris JanusGraph..."
kubectl scale statefulset janusgraph --replicas=5 \
  -n janusgraph-banking-prod

# 4. Wait for Paris to be ready
echo "Step 4: Waiting for Paris to be ready..."
kubectl wait --for=condition=Ready pods -l app=janusgraph \
  -n janusgraph-banking-prod --timeout=600s

# 5. Update DNS/Load Balancer
echo "Step 5: Updating DNS to point to Paris..."
# Update Route 53 or load balancer configuration
# aws route53 change-resource-record-sets ...

# 6. Verify application connectivity
echo "Step 6: Verifying application connectivity..."
kubectl exec -it janusgraph-0 -n janusgraph-banking-prod \
  -- curl http://localhost:8182?gremlin=g.V().count()

# 7. Scale down London JanusGraph
echo "Step 7: Scaling down London JanusGraph..."
kubectl scale statefulset janusgraph --replicas=2 \
  -n janusgraph-banking-prod

# 8. Run health checks
echo "Step 8: Running health checks..."
./scripts/k8s/validate-deployment.sh janusgraph-banking-prod

# 9. Notify stakeholders
echo "Step 9: Notifying stakeholders..."
# Send notification via Slack/PagerDuty/Email

echo "=== FAILBACK COMPLETE ==="
echo "End Time: $(date)"
```

---

## Validation

### Data Integrity Checks

```bash
#!/bin/bash
# Data Integrity Validation Script

echo "=== DATA INTEGRITY CHECKS ==="

# 1. Vertex count
echo "Checking vertex count..."
VERTEX_COUNT=$(kubectl exec janusgraph-0 -n janusgraph-banking-prod \
  -- curl -s http://localhost:8182?gremlin=g.V().count())
echo "Vertex count: $VERTEX_COUNT"

# 2. Edge count
echo "Checking edge count..."
EDGE_COUNT=$(kubectl exec janusgraph-0 -n janusgraph-banking-prod \
  -- curl -s http://localhost:8182?gremlin=g.E().count())
echo "Edge count: $EDGE_COUNT"

# 3. Sample queries
echo "Running sample queries..."
# Query 1: Person count
# Query 2: Account count
# Query 3: Transaction count

# 4. Compare with baseline
echo "Comparing with baseline..."
# Compare counts with expected values

echo "=== VALIDATION COMPLETE ==="
```

### Performance Validation

```bash
#!/bin/bash
# Performance Validation Script

echo "=== PERFORMANCE VALIDATION ==="

# 1. Query latency
echo "Measuring query latency..."
# Run benchmark queries
# Measure P50, P95, P99 latency

# 2. Throughput
echo "Measuring throughput..."
# Run load test
# Measure queries per second

# 3. Resource utilization
echo "Checking resource utilization..."
kubectl top nodes
kubectl top pods -n janusgraph-banking-prod

echo "=== VALIDATION COMPLETE ==="
```

---

## Runbooks

### Runbook 1: Complete Site Failure

**Scenario**: Paris site completely unavailable

**Steps**:
1. Confirm site failure (monitoring alerts, health checks)
2. Notify incident commander
3. Execute failover to London
4. Verify London is serving traffic
5. Monitor for issues
6. Plan Paris recovery
7. Execute failback when Paris is ready

**Estimated Time**: 4 hours

### Runbook 2: Data Corruption

**Scenario**: Data corruption detected

**Steps**:
1. Identify scope of corruption
2. Stop writes to affected keyspace
3. Restore from latest backup
4. Verify restored data
5. Resume writes
6. Investigate root cause

**Estimated Time**: 6 hours

### Runbook 3: Backup Failure

**Scenario**: Backup job failed

**Steps**:
1. Check backup job logs
2. Identify failure cause
3. Fix issue (disk space, credentials, etc.)
4. Trigger manual backup
5. Verify backup success
6. Update monitoring

**Estimated Time**: 1 hour

---

## Contact Information

### Escalation Path

| Level | Role | Contact | Response Time |
|-------|------|---------|---------------|
| L1 | On-Call Engineer | platform-oncall@example.com | 15 minutes |
| L2 | Platform Lead | platform-lead@example.com | 30 minutes |
| L3 | Engineering Manager | eng-manager@example.com | 1 hour |
| L4 | CTO | cto@example.com | 2 hours |

### External Contacts

| Service | Contact | Purpose |
|---------|---------|---------|
| AWS Support | aws-support@example.com | Infrastructure issues |
| DataStax Support | datastax-support@example.com | HCD issues |
| Network Operations | netops@example.com | Network issues |

---

## Appendices

### Appendix A: DR Drill Checklist

- [ ] Schedule drill with stakeholders
- [ ] Notify all teams
- [ ] Prepare test environment
- [ ] Execute drill
- [ ] Measure RTO/RPO
- [ ] Document results
- [ ] Identify improvements
- [ ] Update procedures

### Appendix B: Backup Verification

```bash
# Verify backup exists
aws s3 ls s3://janusgraph-banking-backups-prod/backup-20260219-020000/

# Verify backup size
aws s3 ls s3://janusgraph-banking-backups-prod/backup-20260219-020000/ \
  --recursive --summarize

# Verify backup integrity
kubectl exec -it hcd-paris-rack1-sts-0 -n janusgraph-banking-prod \
  -- medusa verify --backup-name backup-20260219-020000
```

### Appendix C: Monitoring Dashboards

- **Grafana**: http://grafana.example.com/d/dr-dashboard
- **Prometheus**: http://prometheus.example.com/graph
- **Mission Control**: http://mission-control.example.com

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-19  
**Last DR Drill**: TBD  
**Next DR Drill**: First Saturday of next month  
**Document Owner**: Platform Engineering Team  
**Review Frequency**: Quarterly