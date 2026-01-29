# Disaster Recovery Plan
# JanusGraph Banking Compliance System

**Version:** 1.0  
**Date:** 2026-01-29  
**Status:** Active  
**Classification:** Confidential

## Executive Summary

This Disaster Recovery Plan (DRP) provides comprehensive procedures for recovering the JanusGraph Banking Compliance System from various disaster scenarios. The plan ensures business continuity, data integrity, and regulatory compliance during recovery operations.

## Recovery Objectives

### Recovery Time Objective (RTO)
- **Critical Systems:** 4 hours
- **Standard Systems:** 24 hours
- **Non-Critical Systems:** 72 hours

### Recovery Point Objective (RPO)
- **Transaction Data:** 15 minutes
- **Configuration Data:** 1 hour
- **Analytics Data:** 24 hours

### Service Level Objectives (SLO)
- **System Availability:** 99.9% uptime
- **Data Durability:** 99.999%
- **Recovery Success Rate:** 99%

## System Architecture Overview

### Critical Components

1. **JanusGraph Database**
   - Graph data storage
   - Transaction history
   - Relationship mapping

2. **HCD (Cassandra)**
   - Backend storage
   - Data persistence
   - Replication

3. **OpenSearch**
   - Full-text search
   - Vector similarity
   - Analytics queries

4. **HashiCorp Vault**
   - Secrets management
   - Encryption keys
   - Access tokens

5. **Monitoring Stack**
   - Prometheus
   - Grafana
   - AlertManager

## Disaster Scenarios

### Scenario 1: Single Node Failure

**Impact:** Low  
**RTO:** 1 hour  
**RPO:** 0 minutes (no data loss)

**Recovery Procedure:**
```bash
# 1. Identify failed node
docker ps -a | grep -v "Up"

# 2. Check logs
docker logs <container_id>

# 3. Restart container
docker-compose restart <service_name>

# 4. Verify recovery
docker-compose ps
curl http://localhost:8182/health
```

### Scenario 2: Complete Data Center Failure

**Impact:** High  
**RTO:** 4 hours  
**RPO:** 15 minutes

**Recovery Procedure:**

#### Phase 1: Assessment (15 minutes)
```bash
# 1. Verify disaster scope
ping <primary_datacenter>
ssh <backup_datacenter>

# 2. Activate disaster recovery team
# 3. Notify stakeholders
# 4. Begin recovery log
```

#### Phase 2: Infrastructure Recovery (1 hour)
```bash
# 1. Provision backup infrastructure
cd /backup/infrastructure
terraform apply -var-file=dr.tfvars

# 2. Deploy Docker Compose stack
cd /backup/compose
docker-compose -f docker-compose.prod.yml up -d

# 3. Verify services
./scripts/health_check.sh
```

#### Phase 3: Data Recovery (2 hours)
```bash
# 1. Restore HCD data
cd /backup/data/hcd
./restore_hcd.sh --date=latest

# 2. Restore JanusGraph schema
cd /backup/schema
./restore_schema.sh

# 3. Restore OpenSearch indices
cd /backup/opensearch
./restore_indices.sh

# 4. Verify data integrity
./scripts/verify_data.sh
```

#### Phase 4: Service Validation (45 minutes)
```bash
# 1. Run health checks
./scripts/comprehensive_health_check.sh

# 2. Validate data consistency
./scripts/data_consistency_check.sh

# 3. Test critical workflows
./scripts/test_critical_paths.sh

# 4. Update DNS/load balancers
./scripts/update_routing.sh
```

### Scenario 3: Data Corruption

**Impact:** Medium  
**RTO:** 2 hours  
**RPO:** 1 hour

**Recovery Procedure:**
```bash
# 1. Identify corruption scope
./scripts/detect_corruption.sh

# 2. Stop affected services
docker-compose stop janusgraph hcd

# 3. Restore from last known good backup
./scripts/restore_point_in_time.sh --timestamp="2026-01-29T00:00:00Z"

# 4. Replay transaction logs
./scripts/replay_transactions.sh --from="2026-01-29T00:00:00Z"

# 5. Verify data integrity
./scripts/verify_integrity.sh

# 6. Restart services
docker-compose start janusgraph hcd
```

### Scenario 4: Security Breach

**Impact:** Critical  
**RTO:** Immediate containment, 8 hours full recovery  
**RPO:** 0 minutes

**Recovery Procedure:**

#### Immediate Actions (0-15 minutes)
```bash
# 1. Isolate affected systems
./scripts/security/isolate_systems.sh

# 2. Revoke all access tokens
./scripts/security/revoke_all_tokens.sh

# 3. Enable audit logging
./scripts/security/enable_full_audit.sh

# 4. Notify security team
./scripts/security/notify_incident.sh
```

#### Investigation (15 minutes - 2 hours)
```bash
# 1. Collect forensic data
./scripts/security/collect_forensics.sh

# 2. Analyze breach scope
./scripts/security/analyze_breach.sh

# 3. Identify compromised data
./scripts/security/identify_compromise.sh
```

#### Remediation (2-6 hours)
```bash
# 1. Rotate all secrets
./scripts/security/rotate_all_secrets.sh

# 2. Patch vulnerabilities
./scripts/security/apply_security_patches.sh

# 3. Rebuild compromised systems
./scripts/security/rebuild_systems.sh

# 4. Restore from clean backup
./scripts/security/restore_clean_backup.sh
```

#### Validation (6-8 hours)
```bash
# 1. Security scan
./scripts/security/comprehensive_scan.sh

# 2. Penetration testing
./scripts/security/pen_test.sh

# 3. Compliance verification
./scripts/security/verify_compliance.sh
```

## Backup Procedures

### Automated Backups

#### Daily Full Backup
```bash
#!/bin/bash
# /scripts/backup/daily_full_backup.sh

# HCD Snapshot
nodetool snapshot --tag daily_$(date +%Y%m%d)

# JanusGraph Export
./scripts/backup/export_graph.py --output=/backup/graph/daily_$(date +%Y%m%d)

# OpenSearch Snapshot
curl -X PUT "localhost:9200/_snapshot/daily/snapshot_$(date +%Y%m%d)"

# Vault Backup
vault operator raft snapshot save /backup/vault/daily_$(date +%Y%m%d).snap

# Verify backups
./scripts/backup/verify_backups.sh
```

#### Hourly Incremental Backup
```bash
#!/bin/bash
# /scripts/backup/hourly_incremental.sh

# Transaction logs
./scripts/backup/backup_transaction_logs.sh

# Configuration changes
./scripts/backup/backup_config_changes.sh

# Verify incremental
./scripts/backup/verify_incremental.sh
```

### Backup Retention Policy

```
Backup Type          Retention    Location
─────────────────────────────────────────────
Hourly Incremental   7 days       Local SSD
Daily Full           30 days      Network Storage
Weekly Full          90 days      Cloud Storage
Monthly Full         1 year       Archive Storage
Annual Full          7 years      Compliance Archive
```

### Backup Verification

```bash
#!/bin/bash
# /scripts/backup/verify_backups.sh

# 1. Check backup existence
ls -lh /backup/*/latest

# 2. Verify checksums
sha256sum -c /backup/checksums.txt

# 3. Test restore (sample)
./scripts/backup/test_restore.sh --sample

# 4. Log verification results
./scripts/backup/log_verification.sh
```

## Recovery Procedures

### Full System Recovery

```bash
#!/bin/bash
# /scripts/recovery/full_system_recovery.sh

set -e

echo "=== Full System Recovery Started ==="
echo "Timestamp: $(date)"

# 1. Prepare infrastructure
echo "Step 1: Preparing infrastructure..."
./scripts/recovery/prepare_infrastructure.sh

# 2. Restore HCD
echo "Step 2: Restoring HCD..."
./scripts/recovery/restore_hcd.sh --backup=latest

# 3. Restore JanusGraph
echo "Step 3: Restoring JanusGraph..."
./scripts/recovery/restore_janusgraph.sh --backup=latest

# 4. Restore OpenSearch
echo "Step 4: Restoring OpenSearch..."
./scripts/recovery/restore_opensearch.sh --backup=latest

# 5. Restore Vault
echo "Step 5: Restoring Vault..."
./scripts/recovery/restore_vault.sh --backup=latest

# 6. Restore configurations
echo "Step 6: Restoring configurations..."
./scripts/recovery/restore_configs.sh

# 7. Start services
echo "Step 7: Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# 8. Wait for services
echo "Step 8: Waiting for services..."
./scripts/recovery/wait_for_services.sh

# 9. Verify recovery
echo "Step 9: Verifying recovery..."
./scripts/recovery/verify_recovery.sh

# 10. Run smoke tests
echo "Step 10: Running smoke tests..."
./scripts/recovery/smoke_tests.sh

echo "=== Full System Recovery Complete ==="
echo "Recovery Time: $SECONDS seconds"
```

### Point-in-Time Recovery

```bash
#!/bin/bash
# /scripts/recovery/point_in_time_recovery.sh

TARGET_TIME=$1

echo "=== Point-in-Time Recovery to $TARGET_TIME ==="

# 1. Find appropriate backup
BACKUP=$(./scripts/recovery/find_backup.sh --before="$TARGET_TIME")

# 2. Restore base backup
./scripts/recovery/restore_backup.sh --backup="$BACKUP"

# 3. Replay transaction logs
./scripts/recovery/replay_logs.sh --from="$BACKUP" --to="$TARGET_TIME"

# 4. Verify consistency
./scripts/recovery/verify_consistency.sh --target="$TARGET_TIME"

echo "=== Point-in-Time Recovery Complete ==="
```

## Testing Procedures

### Monthly DR Drill

```bash
#!/bin/bash
# /scripts/testing/monthly_dr_drill.sh

echo "=== Monthly Disaster Recovery Drill ==="
echo "Date: $(date)"

# 1. Simulate failure
echo "Simulating failure scenario..."
./scripts/testing/simulate_failure.sh --scenario=datacenter_failure

# 2. Execute recovery
echo "Executing recovery procedures..."
time ./scripts/recovery/full_system_recovery.sh

# 3. Validate recovery
echo "Validating recovery..."
./scripts/testing/validate_recovery.sh

# 4. Measure metrics
echo "Measuring recovery metrics..."
./scripts/testing/measure_rto_rpo.sh

# 5. Generate report
echo "Generating drill report..."
./scripts/testing/generate_drill_report.sh

echo "=== DR Drill Complete ==="
```

### Quarterly Failover Test

```bash
#!/bin/bash
# /scripts/testing/quarterly_failover_test.sh

echo "=== Quarterly Failover Test ==="

# 1. Prepare secondary site
./scripts/testing/prepare_secondary.sh

# 2. Sync data
./scripts/testing/sync_to_secondary.sh

# 3. Execute failover
./scripts/testing/execute_failover.sh

# 4. Validate secondary
./scripts/testing/validate_secondary.sh

# 5. Failback to primary
./scripts/testing/failback_to_primary.sh

# 6. Document results
./scripts/testing/document_failover_test.sh

echo "=== Failover Test Complete ==="
```

## Communication Plan

### Notification Hierarchy

```
Level 1: System Administrators (Immediate)
Level 2: Engineering Team (15 minutes)
Level 3: Management (30 minutes)
Level 4: Stakeholders (1 hour)
Level 5: Customers (As needed)
```

### Communication Templates

#### Initial Incident Notification
```
SUBJECT: [INCIDENT] System Outage - JanusGraph Banking System

SEVERITY: [Critical/High/Medium/Low]
START TIME: [Timestamp]
AFFECTED SYSTEMS: [List]
IMPACT: [Description]
ESTIMATED RECOVERY: [Time]

ACTIONS TAKEN:
- [Action 1]
- [Action 2]

NEXT UPDATE: [Time]

Contact: [On-call engineer]
```

#### Recovery Complete Notification
```
SUBJECT: [RESOLVED] System Recovery Complete

INCIDENT: [ID]
DURATION: [Time]
ROOT CAUSE: [Description]
RECOVERY ACTIONS: [Summary]

POST-INCIDENT REVIEW: [Date/Time]

All systems operational.
```

## Roles and Responsibilities

### Disaster Recovery Team

**DR Coordinator**
- Overall recovery coordination
- Stakeholder communication
- Decision authority

**Infrastructure Lead**
- Infrastructure recovery
- Service deployment
- Network configuration

**Data Lead**
- Data restoration
- Integrity verification
- Consistency checks

**Security Lead**
- Security assessment
- Access control
- Compliance verification

**Application Lead**
- Application recovery
- Functional testing
- User acceptance

## Post-Recovery Procedures

### Post-Incident Review

```markdown
# Post-Incident Review Template

## Incident Summary
- **Incident ID:** [ID]
- **Date/Time:** [Timestamp]
- **Duration:** [Time]
- **Severity:** [Level]

## Timeline
- [Time] - Incident detected
- [Time] - Team notified
- [Time] - Recovery started
- [Time] - Services restored
- [Time] - Validation complete

## Root Cause Analysis
[Detailed analysis]

## Recovery Actions
1. [Action 1]
2. [Action 2]

## What Went Well
- [Item 1]
- [Item 2]

## What Needs Improvement
- [Item 1]
- [Item 2]

## Action Items
- [ ] [Action 1] - Owner: [Name] - Due: [Date]
- [ ] [Action 2] - Owner: [Name] - Due: [Date]

## Lessons Learned
[Summary]
```

### Recovery Metrics

```bash
#!/bin/bash
# /scripts/metrics/calculate_recovery_metrics.sh

# Actual RTO
ACTUAL_RTO=$((RECOVERY_END - INCIDENT_START))

# Actual RPO
ACTUAL_RPO=$((INCIDENT_START - LAST_BACKUP))

# Data Loss
DATA_LOSS=$(./scripts/metrics/calculate_data_loss.sh)

# Recovery Success Rate
SUCCESS_RATE=$(./scripts/metrics/calculate_success_rate.sh)

# Generate metrics report
cat > /reports/recovery_metrics.txt <<EOF
Recovery Metrics Report
=======================
Date: $(date)

Actual RTO: $ACTUAL_RTO seconds
Target RTO: $TARGET_RTO seconds
RTO Met: $([ $ACTUAL_RTO -le $TARGET_RTO ] && echo "YES" || echo "NO")

Actual RPO: $ACTUAL_RPO seconds
Target RPO: $TARGET_RPO seconds
RPO Met: $([ $ACTUAL_RPO -le $TARGET_RPO ] && echo "YES" || echo "NO")

Data Loss: $DATA_LOSS records
Recovery Success Rate: $SUCCESS_RATE%
EOF
```

## Appendices

### A. Emergency Contacts

```
Role                    Name            Phone           Email
─────────────────────────────────────────────────────────────────
DR Coordinator          [Name]          [Phone]         [Email]
Infrastructure Lead     [Name]          [Phone]         [Email]
Data Lead              [Name]          [Phone]         [Email]
Security Lead          [Name]          [Phone]         [Email]
Application Lead       [Name]          [Phone]         [Email]
```

### B. System Dependencies

```
Component          Dependencies                    Critical
──────────────────────────────────────────────────────────────
JanusGraph         HCD, OpenSearch                 Yes
HCD                None                            Yes
OpenSearch         None                            Yes
Vault              None                            Yes
Prometheus         All services                    No
Grafana            Prometheus                      No
```

### C. Recovery Checklists

See: [`RECOVERY_CHECKLISTS.md`](RECOVERY_CHECKLISTS.md)

### D. Runbook References

See: [`OPERATIONS_RUNBOOK.md`](OPERATIONS_RUNBOOK.md)

---

**Document Control:**
- **Version:** 1.0
- **Last Updated:** 2026-01-29
- **Next Review:** 2026-04-29
- **Owner:** Infrastructure Team
- **Approved By:** [Name], [Title]