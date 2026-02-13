# Cross-Region Disaster Recovery Guide

**Date:** 2026-02-12
**Version:** 1.0
**Status:** Active

## TL;DR

This document defines the cross-region DR strategy for the JanusGraph Banking platform, covering RTO/RPO targets, failover procedures, and automated recovery scripts.

## Recovery Objectives

| Tier | Component | RPO | RTO | Strategy |
|------|-----------|-----|-----|----------|
| 1 | JanusGraph (graph data) | 15 min | 30 min | Active-passive with Cassandra multi-DC replication |
| 1 | HCD/Cassandra | 0 (sync replication) | 15 min | Multi-DC NetworkTopologyStrategy (RF=3 per DC) |
| 2 | OpenSearch (search index) | 1 hr | 1 hr | Cross-cluster replication + snapshot restore |
| 2 | Pulsar (event stream) | 5 min | 30 min | Geo-replication between clusters |
| 3 | API servers | N/A (stateless) | 5 min | DNS failover + OpenShift multi-cluster |
| 3 | Monitoring stack | 1 hr | 1 hr | Thanos/Cortex for Prometheus; Grafana backup |

## Architecture

```
Region A (Primary)                    Region B (Standby)
┌─────────────────────┐              ┌─────────────────────┐
│  OpenShift Cluster   │              │  OpenShift Cluster   │
│  ┌───────────────┐  │   sync       │  ┌───────────────┐  │
│  │ Cassandra DC-A │──┼──────────────┼──│ Cassandra DC-B │  │
│  └───────────────┘  │              │  └───────────────┘  │
│  ┌───────────────┐  │   geo-rep    │  ┌───────────────┐  │
│  │  Pulsar DC-A   │──┼──────────────┼──│  Pulsar DC-B   │  │
│  └───────────────┘  │              │  └───────────────┘  │
│  ┌───────────────┐  │   CCR        │  ┌───────────────┐  │
│  │ OpenSearch A   │──┼──────────────┼──│ OpenSearch B   │  │
│  └───────────────┘  │              │  └───────────────┘  │
│  ┌───────────────┐  │              │  ┌───────────────┐  │
│  │ JanusGraph API │  │              │  │ JanusGraph API │  │
│  └───────────────┘  │              │  └───────────────┘  │
└─────────────────────┘              └─────────────────────┘
         │                                      │
         └──────── Global Load Balancer ────────┘
                   (Route 53 / GLB)
```

## 1. Cassandra Multi-DC Replication

### Setup

```cql
-- Create keyspace with NetworkTopologyStrategy
CREATE KEYSPACE janusgraph WITH replication = {
  'class': 'NetworkTopologyStrategy',
  'dc-primary': 3,
  'dc-standby': 3
};

-- Verify replication
DESCRIBE KEYSPACE janusgraph;
```

### JanusGraph Configuration

```properties
# janusgraph-server.properties (primary)
storage.backend=cql
storage.cql.local-datacenter=dc-primary
storage.cql.replication-strategy-class=NetworkTopologyStrategy
storage.cql.replication-strategy-options=dc-primary,3,dc-standby,3
storage.cql.read-consistency-level=LOCAL_QUORUM
storage.cql.write-consistency-level=LOCAL_QUORUM
```

### Monitoring Replication Lag

```bash
# Check replication lag via nodetool
podman exec cassandra-node nodetool netstats | grep -A5 "Pool"

# Verify all nodes are UN (Up/Normal)
podman exec cassandra-node nodetool status
```

## 2. Pulsar Geo-Replication

### Setup

```bash
# On primary cluster: enable geo-replication to standby
pulsar-admin namespaces set-clusters public/banking \
  --clusters primary-cluster,standby-cluster

# Verify
pulsar-admin namespaces get-clusters public/banking
```

### Topic-Level Configuration

```bash
# Critical topics: synchronous replication
pulsar-admin topics set-replication-clusters \
  persistent://public/banking/transactions-events \
  --clusters primary-cluster,standby-cluster

# Non-critical topics: async with higher throughput
pulsar-admin namespaces set-deduplication public/banking --enable
```

## 3. OpenSearch Cross-Cluster Replication

### Setup

```json
PUT _plugins/_replication/_autofollow
{
  "leader_alias": "primary-opensearch",
  "name": "banking-indices-rule",
  "pattern": "janusgraph-*",
  "use_roles": {
    "leader_cluster_role": "cross_cluster_replication_leader_full_access",
    "follower_cluster_role": "cross_cluster_replication_follower_full_access"
  }
}
```

## 4. Failover Procedures

### Automated Failover (< 30 min RTO)

```bash
#!/bin/bash
# scripts/dr/failover.sh
set -euo pipefail

STANDBY_CLUSTER="standby-cluster"
PRIMARY_CLUSTER="primary-cluster"

echo "=== INITIATING FAILOVER TO ${STANDBY_CLUSTER} ==="

# Step 1: Verify standby health
echo "[1/5] Verifying standby cluster health..."
oc --context=${STANDBY_CLUSTER} get nodes
oc --context=${STANDBY_CLUSTER} get pods -n janusgraph-banking

# Step 2: Promote Cassandra standby DC
echo "[2/5] Promoting Cassandra DC..."
oc --context=${STANDBY_CLUSTER} exec cassandra-0 -- \
  cqlsh -e "ALTER KEYSPACE janusgraph WITH replication = {
    'class': 'NetworkTopologyStrategy',
    'dc-standby': 3
  };"

# Step 3: Switch Pulsar consumers
echo "[3/5] Switching Pulsar consumers..."
oc --context=${STANDBY_CLUSTER} scale deployment pulsar-consumer --replicas=3

# Step 4: Promote OpenSearch follower indices
echo "[4/5] Promoting OpenSearch indices..."
curl -X POST "https://opensearch-standby:9200/_plugins/_replication/janusgraph-vertices/_stop" \
  -H "Content-Type: application/json" -d '{}'

# Step 5: Update DNS / Global LB
echo "[5/5] Updating DNS to point to standby..."
# Using Route 53 (AWS) or equivalent
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.banking.example.com",
        "Type": "CNAME",
        "TTL": 60,
        "ResourceRecords": [{"Value": "'${STANDBY_CLUSTER_ENDPOINT}'"}]
      }
    }]
  }'

echo "=== FAILOVER COMPLETE ==="
```

### Failback Procedure

1. Restore primary cluster infrastructure
2. Re-establish Cassandra replication (`nodetool rebuild -- dc-primary`)
3. Re-enable Pulsar geo-replication
4. Resume OpenSearch CCR (primary as follower temporarily)
5. Run consistency checks between regions
6. Switch DNS back to primary
7. Restore original replication topology

## 5. Backup Strategy

| Component | Method | Frequency | Retention |
|-----------|--------|-----------|-----------|
| Cassandra | Snapshot + incremental | Daily full, hourly incremental | 30 days |
| OpenSearch | Snapshot to S3/MinIO | Every 6 hours | 14 days |
| Pulsar | Topic offload to S3 | Continuous | 90 days |
| Vault secrets | `vault operator raft snapshot` | Daily | 90 days |
| Configs/manifests | Git (this repo) | Every commit | Indefinite |

### Backup Script

```bash
#!/bin/bash
# scripts/dr/backup.sh
DATE=$(date +%Y%m%d-%H%M%S)

# Cassandra snapshot
podman exec cassandra-node nodetool snapshot -t "backup-${DATE}" janusgraph

# OpenSearch snapshot
curl -X PUT "localhost:9200/_snapshot/s3_backup/snapshot-${DATE}?wait_for_completion=true"

# Vault snapshot
podman exec vault-server vault operator raft snapshot save "/vault/snapshots/vault-${DATE}.snap"

echo "Backup ${DATE} complete"
```

## 6. DR Testing Schedule

| Test | Frequency | Duration | Scope |
|------|-----------|----------|-------|
| Backup restore | Monthly | 2 hours | Single component |
| Failover drill | Quarterly | 4 hours | Full stack |
| Chaos engineering | Monthly | 1 hour | Random component failure |
| Full DR exercise | Annually | 8 hours | Complete region failover |

## 7. Runbook Checklist

- [ ] Standby cluster provisioned and healthy
- [ ] Cassandra multi-DC replication verified (nodetool status)
- [ ] Pulsar geo-replication active (admin API check)
- [ ] OpenSearch CCR indices in sync (replication stats)
- [ ] DNS TTL set to 60s for fast failover
- [ ] Failover script tested in staging
- [ ] On-call team trained on failover procedure
- [ ] Monitoring alerts configured for replication lag
- [ ] Backup restore tested within last 30 days
