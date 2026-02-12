# RTO/RPO Targets - HCD + JanusGraph Banking Platform

**Date:** 2026-02-11  
**Version:** 1.0  
**Status:** Active  
**Review Cycle:** Quarterly

---

## Executive Summary

This document defines Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO) for the HCD + JanusGraph Banking Compliance Platform. These targets guide disaster recovery planning, backup strategies, and infrastructure investments.

**Key Targets:**
- **Critical Services RTO:** 4 hours
- **Critical Services RPO:** 15 minutes
- **Standard Services RTO:** 24 hours
- **Standard Services RPO:** 1 hour

---

## Definitions

### Recovery Time Objective (RTO)

**Definition:** Maximum acceptable time to restore a service after a disruption.

**Measurement:** Time from incident detection to full service restoration.

**Example:** If RTO = 4 hours, service must be fully operational within 4 hours of failure.

### Recovery Point Objective (RPO)

**Definition:** Maximum acceptable data loss measured in time.

**Measurement:** Time between last backup and failure point.

**Example:** If RPO = 15 minutes, maximum data loss is 15 minutes of transactions.

---

## Service Classification

### Tier 1: Critical Services (RTO: 4h, RPO: 15min)

**Services:**
- JanusGraph Server (graph database)
- HCD/Cassandra (storage backend)
- OpenSearch (search/analytics)
- Analytics API (REST API)

**Business Impact:**
- Direct customer impact
- Revenue loss
- Regulatory reporting delays
- Compliance violations

**Justification:**
- Core banking operations depend on these services
- Real-time fraud detection requires immediate availability
- AML compliance requires continuous monitoring
- Customer-facing features affected

### Tier 2: Important Services (RTO: 8h, RPO: 1h)

**Services:**
- Pulsar (event streaming)
- Graph/Vector Consumers
- Prometheus (monitoring)
- Grafana (dashboards)

**Business Impact:**
- Operational efficiency reduced
- Monitoring gaps
- Event processing delays
- Analytics delays

**Justification:**
- Support core services but not customer-facing
- Can operate in degraded mode temporarily
- Data can be replayed from backups
- Monitoring can tolerate brief gaps

### Tier 3: Standard Services (RTO: 24h, RPO: 4h)

**Services:**
- Jupyter Lab (analysis)
- Visualization tools (Graphexp, Visualizer)
- AlertManager
- Vault (secrets management)

**Business Impact:**
- Internal tools unavailable
- Analysis delayed
- Alert notifications delayed
- Manual workarounds required

**Justification:**
- Internal tools only
- No direct customer impact
- Can operate without for extended periods
- Secrets cached in running services

### Tier 4: Non-Critical Services (RTO: 72h, RPO: 24h)

**Services:**
- Gremlin Console
- CQLSH Client
- Development tools

**Business Impact:**
- Developer productivity reduced
- Troubleshooting delayed
- No customer impact

**Justification:**
- Development/debugging tools only
- Alternative tools available
- Can be rebuilt quickly

---

## RTO/RPO Matrix

| Service | Tier | RTO | RPO | Backup Frequency | Retention |
|---------|------|-----|-----|------------------|-----------|
| **JanusGraph** | 1 | 4h | 15min | Every 15min | 30 days |
| **HCD/Cassandra** | 1 | 4h | 15min | Every 15min | 30 days |
| **OpenSearch** | 1 | 4h | 15min | Every 15min | 30 days |
| **Analytics API** | 1 | 4h | 15min | Config only | 30 days |
| **Pulsar** | 2 | 8h | 1h | Hourly | 14 days |
| **Consumers** | 2 | 8h | 1h | Config only | 14 days |
| **Prometheus** | 2 | 8h | 1h | Daily | 90 days |
| **Grafana** | 2 | 8h | 1h | Daily | 30 days |
| **Jupyter** | 3 | 24h | 4h | Daily | 7 days |
| **Visualizers** | 3 | 24h | 4h | Config only | 7 days |
| **Vault** | 3 | 24h | 4h | Daily | 90 days |
| **Dev Tools** | 4 | 72h | 24h | None | N/A |

---

## Backup Strategy

### Automated Backups

**JanusGraph + HCD (Every 15 minutes)**
```bash
# Automated via cron
*/15 * * * * /scripts/backup/backup_janusgraph.sh

# Backup includes:
# - JanusGraph schema
# - HCD keyspace snapshots
# - Metadata and configuration
```

**OpenSearch (Every 15 minutes)**
```bash
# Automated via cron
*/15 * * * * /scripts/backup/backup_opensearch.sh

# Backup includes:
# - All indices
# - Index templates
# - Cluster settings
```

**Pulsar (Hourly)**
```bash
# Automated via cron
0 * * * * /scripts/backup/backup_pulsar.sh

# Backup includes:
# - Topic metadata
# - Namespace configuration
# - Subscription state
```

**Configuration (Daily)**
```bash
# Automated via cron
0 2 * * * /scripts/backup/backup_configs.sh

# Backup includes:
# - Docker compose files
# - Application configs
# - Environment variables (encrypted)
# - SSL certificates
```

### Backup Verification

**Automated Verification (Daily)**
```bash
# Test restore to staging environment
0 3 * * * /scripts/backup/verify_backups.sh

# Verification includes:
# - Restore test
# - Data integrity check
# - Schema validation
# - Performance test
```

**Manual Verification (Weekly)**
- Full restore to isolated environment
- Data consistency validation
- Application functionality test
- Performance baseline comparison

### Backup Storage

**Primary Storage:** Local NAS (on-premises)
- Retention: 7 days
- Access: Immediate
- Cost: Low

**Secondary Storage:** AWS S3 (cloud)
- Retention: 30 days
- Access: <1 hour
- Cost: Medium
- Encryption: AES-256

**Archive Storage:** AWS Glacier (long-term)
- Retention: 7 years (compliance)
- Access: 12-48 hours
- Cost: Very low
- Encryption: AES-256

---

## Recovery Procedures

### Tier 1: Critical Services (4h RTO)

**JanusGraph Recovery**

```bash
# 1. Stop failed instance (5 min)
podman-compose -p janusgraph-demo stop janusgraph-server

# 2. Restore latest backup (30 min)
./scripts/restore/restore_janusgraph.sh --backup-id latest

# 3. Verify data integrity (15 min)
./scripts/validation/verify_janusgraph_data.sh

# 4. Start service (5 min)
podman-compose -p janusgraph-demo start janusgraph-server

# 5. Validate functionality (15 min)
./scripts/validation/test_janusgraph_queries.sh

# Total: ~70 minutes (well under 4h RTO)
```

**HCD/Cassandra Recovery**

```bash
# 1. Stop failed node (5 min)
podman-compose -p janusgraph-demo stop hcd-server

# 2. Restore snapshot (45 min)
./scripts/restore/restore_hcd.sh --snapshot latest

# 3. Repair data (60 min)
nodetool repair janusgraph

# 4. Start node (5 min)
podman-compose -p janusgraph-demo start hcd-server

# 5. Validate (15 min)
./scripts/validation/test_hcd_connectivity.sh

# Total: ~130 minutes (well under 4h RTO)
```

**OpenSearch Recovery**

```bash
# 1. Stop failed instance (5 min)
podman-compose -p janusgraph-demo stop opensearch

# 2. Restore snapshot (30 min)
./scripts/restore/restore_opensearch.sh --snapshot latest

# 3. Reindex if needed (45 min)
./scripts/opensearch/reindex_all.sh

# 4. Start service (5 min)
podman-compose -p janusgraph-demo start opensearch

# 5. Validate (15 min)
./scripts/validation/test_opensearch_queries.sh

# Total: ~100 minutes (well under 4h RTO)
```

### Tier 2: Important Services (8h RTO)

**Pulsar Recovery**

```bash
# 1. Stop failed instance (5 min)
podman-compose -p janusgraph-demo stop pulsar

# 2. Restore configuration (10 min)
./scripts/restore/restore_pulsar_config.sh

# 3. Recreate topics (15 min)
./scripts/pulsar/recreate_topics.sh

# 4. Start service (5 min)
podman-compose -p janusgraph-demo start pulsar

# 5. Replay events from backup (120 min)
./scripts/pulsar/replay_events.sh --from-backup

# Total: ~155 minutes (well under 8h RTO)
```

### Tier 3: Standard Services (24h RTO)

**Vault Recovery**

```bash
# 1. Deploy new Vault instance (30 min)
./scripts/deploy/deploy_vault.sh

# 2. Restore backup (15 min)
./scripts/restore/restore_vault.sh --backup latest

# 3. Unseal Vault (10 min)
./scripts/vault/unseal_vault.sh

# 4. Validate secrets (15 min)
./scripts/validation/test_vault_secrets.sh

# Total: ~70 minutes (well under 24h RTO)
```

---

## Disaster Recovery Scenarios

### Scenario 1: Single Service Failure

**Example:** JanusGraph server crashes

**Detection:** Prometheus alert (< 1 minute)

**Response:**
1. Automated restart attempt (5 min)
2. If restart fails, page on-call engineer (5 min)
3. Engineer investigates and restores from backup (60 min)
4. Validate and monitor (30 min)

**Total RTO:** ~100 minutes (within 4h target)

**Data Loss:** 0-15 minutes (within RPO target)

### Scenario 2: Data Center Failure

**Example:** Complete data center outage

**Detection:** Multiple service alerts (< 5 minutes)

**Response:**
1. Activate DR site (30 min)
2. Restore all Tier 1 services from S3 backups (120 min)
3. Restore Tier 2 services (180 min)
4. Update DNS to point to DR site (15 min)
5. Validate all services (45 min)

**Total RTO:** ~390 minutes (6.5 hours)

**Data Loss:** 15-30 minutes (acceptable for DR scenario)

### Scenario 3: Data Corruption

**Example:** Corrupted JanusGraph data

**Detection:** Data validation alerts (< 30 minutes)

**Response:**
1. Identify corruption scope (30 min)
2. Stop affected services (10 min)
3. Restore from last known good backup (60 min)
4. Replay transactions from Pulsar (90 min)
5. Validate data integrity (60 min)

**Total RTO:** ~250 minutes (4.2 hours)

**Data Loss:** 0 minutes (full replay from Pulsar)

### Scenario 4: Ransomware Attack

**Example:** Ransomware encrypts production data

**Detection:** Anomaly detection (< 15 minutes)

**Response:**
1. Isolate affected systems immediately (5 min)
2. Activate incident response team (15 min)
3. Assess damage scope (60 min)
4. Restore from immutable backups (180 min)
5. Security hardening and validation (120 min)

**Total RTO:** ~380 minutes (6.3 hours)

**Data Loss:** 15-30 minutes (last clean backup)

---

## Monitoring & Alerting

### RTO/RPO Monitoring

**Backup Success Rate**
```yaml
# Prometheus alert
- alert: BackupFailure
  expr: backup_success_rate < 0.95
  for: 1h
  annotations:
    summary: "Backup success rate below 95%"
    description: "RPO targets at risk"
```

**Backup Age**
```yaml
# Prometheus alert
- alert: BackupTooOld
  expr: (time() - backup_last_success_timestamp) > 1800
  annotations:
    summary: "Backup older than 30 minutes"
    description: "RPO target exceeded for Tier 1 services"
```

**Recovery Time Tracking**
```yaml
# Prometheus metric
recovery_time_seconds{service="janusgraph",tier="1"}
```

### SLA Dashboard

**Grafana Dashboard:** RTO/RPO Compliance

**Panels:**
1. Backup success rate (last 24h)
2. Time since last successful backup
3. Recovery time history
4. RPO violations (last 30 days)
5. RTO violations (last 30 days)
6. Backup storage utilization

---

## Compliance & Reporting

### Monthly RTO/RPO Report

**Metrics:**
- Backup success rate
- Average recovery time
- RPO violations
- RTO violations
- Root cause analysis

**Distribution:**
- Operations team
- Management
- Compliance team
- Audit committee

### Quarterly DR Drill

**Objectives:**
- Validate recovery procedures
- Test backup integrity
- Measure actual RTO/RPO
- Train operations team
- Identify improvements

**Scenarios:**
- Single service failure
- Multi-service failure
- Data center failure
- Data corruption

**Success Criteria:**
- All Tier 1 services recovered within RTO
- Data loss within RPO
- All procedures documented
- Team trained and confident

---

## Cost Analysis

### Backup Storage Costs

| Storage Tier | Capacity | Monthly Cost | Annual Cost |
|--------------|----------|--------------|-------------|
| Local NAS | 5 TB | $200 | $2,400 |
| AWS S3 | 10 TB | $230 | $2,760 |
| AWS Glacier | 50 TB | $200 | $2,400 |
| **Total** | **65 TB** | **$630** | **$7,560** |

### DR Infrastructure Costs

| Component | Monthly Cost | Annual Cost |
|-----------|--------------|-------------|
| DR site (standby) | $2,000 | $24,000 |
| Network connectivity | $500 | $6,000 |
| Monitoring tools | $300 | $3,600 |
| **Total** | **$2,800** | **$33,600** |

### Total Annual Cost: $41,160

**Cost per Hour of Downtime Prevented:** ~$5,000
**ROI:** 121x (based on average downtime cost of $250,000/hour)

---

## Continuous Improvement

### Quarterly Review

**Review Items:**
- RTO/RPO targets still appropriate?
- Backup strategy effective?
- Recovery procedures tested?
- New risks identified?
- Technology changes needed?

**Action Items:**
- Update targets if needed
- Improve procedures
- Invest in automation
- Train team

### Annual Assessment

**Assessment Areas:**
- Business continuity plan
- Disaster recovery plan
- Backup and recovery strategy
- Infrastructure resilience
- Team readiness

**Deliverables:**
- Updated RTO/RPO targets
- Improved recovery procedures
- Enhanced monitoring
- Training plan

---

## Appendix

### A. Backup Script Locations

- JanusGraph: `scripts/backup/backup_janusgraph.sh`
- HCD: `scripts/backup/backup_hcd.sh`
- OpenSearch: `scripts/backup/backup_opensearch.sh`
- Pulsar: `scripts/backup/backup_pulsar.sh`
- Configs: `scripts/backup/backup_configs.sh`

### B. Restore Script Locations

- JanusGraph: `scripts/restore/restore_janusgraph.sh`
- HCD: `scripts/restore/restore_hcd.sh`
- OpenSearch: `scripts/restore/restore_opensearch.sh`
- Pulsar: `scripts/restore/restore_pulsar.sh`
- Vault: `scripts/restore/restore_vault.sh`

### C. Validation Script Locations

- JanusGraph: `scripts/validation/verify_janusgraph_data.sh`
- HCD: `scripts/validation/test_hcd_connectivity.sh`
- OpenSearch: `scripts/validation/test_opensearch_queries.sh`
- Full stack: `scripts/validation/preflight_check.sh`

### D. Contact Information

**On-Call Engineer:** +1-XXX-XXX-XXXX  
**Operations Manager:** operations@example.com  
**Incident Commander:** incident@example.com  
**Escalation:** escalation@example.com

---

**Document Owner:** Operations Team  
**Last Updated:** 2026-02-11  
**Next Review:** 2026-05-11 (Quarterly)  
**Version:** 1.0