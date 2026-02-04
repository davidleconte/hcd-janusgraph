# HCD Scripts

Scripts for managing and validating HCD/Cassandra deployment for JanusGraph.

**Author:** David LECONTE - IBM Worldwide  
**Date:** 2026-01-29

## Overview

This directory contains scripts for:
- Creating JanusGraph keyspace with production settings
- Validating HCD deployment
- Monitoring cluster health

## Scripts

### 1. init_production_keyspace.cql

**Purpose:** Create JanusGraph keyspace with production-ready replication settings.

**Usage:**

```bash
# From host (development)
podman exec -i janusgraph-demo_hcd-server_1 cqlsh < scripts/hcd/init_production_keyspace.cql

# From container
cqlsh -f /path/to/init_production_keyspace.cql

# With authentication
podman exec -i janusgraph-demo_hcd-server_1 cqlsh -u cassandra -p password < scripts/hcd/init_production_keyspace.cql
```

**Configuration:**

Edit the file to adjust replication settings:

```sql
-- Production (multi-node)
CREATE KEYSPACE IF NOT EXISTS janusgraph
WITH replication = {
    'class': 'NetworkTopologyStrategy',
    'datacenter1': 3
}
AND durable_writes = true;

-- Development (single-node)
CREATE KEYSPACE IF NOT EXISTS janusgraph
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
}
AND durable_writes = true;
```

**When to Use:**
- Before first JanusGraph startup
- When changing replication strategy
- After cluster expansion (adjust RF)

**Notes:**
- JanusGraph auto-creates keyspace if missing
- Use this script for explicit control over replication
- Tables are created automatically by JanusGraph

### 2. validate_deployment.py

**Purpose:** Comprehensive validation of HCD deployment for JanusGraph.

**Prerequisites:**
```bash
# Activate conda environment
conda activate janusgraph-analysis

# Install dependencies
uv pip install cassandra-driver
```

**Usage:**

```bash
# Basic validation (localhost)
python scripts/hcd/validate_deployment.py

# With custom host
python scripts/hcd/validate_deployment.py --hosts hcd-server --port 9042

# With authentication
python scripts/hcd/validate_deployment.py \
    --username cassandra \
    --password password

# Multiple hosts (for cluster)
python scripts/hcd/validate_deployment.py \
    --hosts "host1,host2,host3" \
    --datacenter datacenter1

# Using environment variables
export HCD_HOST=localhost
export HCD_PORT=19042
export HCD_USERNAME=cassandra
export HCD_PASSWORD=password
python scripts/hcd/validate_deployment.py
```

**Validates:**
- ✅ HCD connection
- ✅ Keyspace existence and configuration
- ✅ JanusGraph tables created
- ✅ Replication settings
- ✅ Cluster health

**Exit Codes:**
- 0: All validations passed
- 1: One or more validations failed

**Example Output:**
```
============================================================
HCD Deployment Validation
============================================================
Connecting to HCD cluster at ['localhost']:9042...
✅ Connected to HCD cluster

Validating keyspace: janusgraph
✅ Keyspace 'janusgraph' exists
   Replication: {'class': 'SimpleStrategy', 'replication_factor': '1'}
   ⚠️  Using SimpleStrategy with RF=1 (development only)

Validating JanusGraph tables in keyspace: janusgraph
   Found 9 tables
   ✅ edgestore
   ✅ edgestore_lock_
   ✅ graphindex
   ...

Validating cluster health...
   Cluster name: HCD-Cluster
   Nodes: 1
   - 172.17.0.2 (DC: datacenter1, Rack: rack1)
     ✅ UP
   ✅ All nodes are UP

============================================================
Validation Summary
============================================================
Passed: 3/3
✅ All validations passed
```

### 3. health_check.sh

**Purpose:** Comprehensive health monitoring for HCD cluster.

**Usage:**

```bash
# Basic health check
bash scripts/hcd/health_check.sh

# With custom configuration
HCD_HOST=localhost HCD_PORT=19042 bash scripts/hcd/health_check.sh

# With custom container name
CONTAINER_NAME=my-hcd-container bash scripts/hcd/health_check.sh

# Check specific keyspace
KEYSPACE=my_keyspace bash scripts/hcd/health_check.sh
```

**Checks:**

1. **Container Status** (if running from host)
2. **Cluster Status** (nodetool status)
   - Nodes UP/DOWN
   - Node count
3. **CQL Connectivity**
4. **Keyspace Existence**
   - Replication configuration
5. **JanusGraph Tables**
   - Critical tables present
   - Table count
6. **Disk Usage**
   - Total space used
   - SSTable count
7. **Compaction Status**
   - Pending compactions
8. **Gossip Protocol**
9. **Memory Usage**
   - Heap utilization
   - Warnings for >75% usage

**Exit Codes:**
- 0: Healthy (all checks passed)
- 1: Critical errors
- 2: Warnings only

**Example Output:**
```
========================================
HCD Health Check
========================================
Host: localhost:19042
Keyspace: janusgraph
Container: janusgraph-demo_hcd-server_1

1. Checking container status...
✅ Container is running

2. Checking cluster status...
✅ Nodetool accessible
   Nodes UP: 1
✅ All nodes operational

3. Checking CQL connectivity...
✅ CQL connection successful

4. Checking keyspace: janusgraph...
✅ Keyspace exists
   Replication: {'class': 'SimpleStrategy', 'replication_factor': '1'}

5. Checking JanusGraph tables...
✅ Found 9 tables in janusgraph
   ✓ edgestore
   ✓ graphindex
   ✓ janusgraph_ids
   ✓ system_properties

6. Checking disk usage...
✅ Disk usage: 2.5 MB
   SSTables: 12

7. Checking compaction status...
✅ No pending compactions

8. Checking gossip protocol...
✅ Gossip protocol active

9. Checking memory usage...
   Heap: 1024MB / 4096MB (25.0%)
✅ Memory usage normal

========================================
Health Check Complete
========================================

Status: HEALTHY - All systems operational
```

**Automated Monitoring:**

Add to cron for periodic checks:
```bash
# Check every 5 minutes
*/5 * * * * /path/to/scripts/hcd/health_check.sh >> /var/log/hcd-health.log 2>&1

# Alert on failures
*/5 * * * * /path/to/scripts/hcd/health_check.sh || mail -s "HCD Health Check Failed" admin@example.com
```

**Integration with Deployment:**

Can be integrated into deployment scripts:
```bash
# Wait for HCD to be healthy
until bash scripts/hcd/health_check.sh; do
    echo "Waiting for HCD to be healthy..."
    sleep 10
done
echo "HCD is ready!"
```

## Workflow

### First-Time Deployment

```bash
# 1. Deploy stack
bash scripts/deployment/deploy_with_opensearch.sh

# 2. Wait for HCD to start
sleep 60

# 3. Create keyspace (optional - JanusGraph auto-creates)
podman exec -i janusgraph-demo_hcd-server_1 cqlsh < scripts/hcd/init_production_keyspace.cql

# 4. Validate deployment
conda activate janusgraph-analysis
python scripts/hcd/validate_deployment.py

# 5. Check health
bash scripts/hcd/health_check.sh
```

### Regular Monitoring

```bash
# Quick health check
bash scripts/hcd/health_check.sh

# Full validation
python scripts/hcd/validate_deployment.py
```

### Troubleshooting

**Problem:** Validation fails with "Cannot connect to HCD"

**Solution:**
```bash
# Check container is running
podman ps | grep hcd

# Check port mapping
podman port janusgraph-demo_hcd-server_1

# Check logs
podman logs janusgraph-demo_hcd-server_1

# Test connection
podman exec janusgraph-demo_hcd-server_1 nodetool status
```

**Problem:** Keyspace not found

**Solution:**
```bash
# JanusGraph creates keyspace on first start
# Start JanusGraph and wait for initialization
podman logs janusgraph-demo_janusgraph-server_1

# Or create manually
podman exec -i janusgraph-demo_hcd-server_1 cqlsh < scripts/hcd/init_production_keyspace.cql
```

**Problem:** Health check shows high memory usage

**Solution:**
```bash
# Check JVM heap settings
podman exec janusgraph-demo_hcd-server_1 cat /opt/hcd/conf/cassandra-env.sh | grep MAX_HEAP_SIZE

# Adjust in docker-compose.full.yml:
# environment:
#   - MAX_HEAP_SIZE=8G
#   - HEAP_NEWSIZE=1600M

# Restart
cd config/compose
podman-compose -p janusgraph-demo restart hcd-server
```

## Dependencies

### init_production_keyspace.cql
- HCD/Cassandra running
- cqlsh available in container

### validate_deployment.py
- Python 3.11+
- cassandra-driver package
- Network access to HCD port (9042)

### health_check.sh
- Bash shell
- podman CLI (if running from host)
- nodetool (in container)
- cqlsh (in container)
- bc (for floating-point math)

## Related Documentation

- [AGENTS.md](../../AGENTS.md) - Deployment guidelines
- [docker-compose.full.yml](../../config/compose/docker-compose.full.yml) - HCD service configuration
- [Service Startup Reliability Fix](../../docs/implementation/remediation/SERVICE_STARTUP_RELIABILITY_FIX.md) - Deployment fixes

## Notes

1. **Auto-Creation**: JanusGraph automatically creates keyspace and tables on first start. These scripts provide explicit control for production.

2. **Replication Strategy**: 
   - Development: SimpleStrategy, RF=1
   - Production: NetworkTopologyStrategy, RF=3+

3. **Validation Timing**: Run validation AFTER JanusGraph first start to see tables.

4. **Health Checks**: Integrate into monitoring systems (Prometheus, Nagios, etc.)

5. **Security**: Use authentication in production (set HCD_USERNAME and HCD_PASSWORD)

## Support

For issues or questions:
- Check logs: `podman logs janusgraph-demo_hcd-server_1`
- Review documentation: [docs/](../../docs/)
- Validate deployment: `python scripts/hcd/validate_deployment.py`
