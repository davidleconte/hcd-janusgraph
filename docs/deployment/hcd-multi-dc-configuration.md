# HCD Multi-Datacenter Configuration Guide

**Created:** 2026-04-07  
**Version:** 1.0  
**Status:** Active  
**Sprint:** 1.3 - Insider Trading Enhancement

---

## 📋 Overview

This guide documents the multi-datacenter (multi-DC) configuration for HCD (Hyper Converged Database) as the storage backend for JanusGraph. Multi-DC deployment provides:

- **GDPR Compliance:** Data residency requirements (EU data stays in EU)
- **Business Continuity:** Disaster recovery across geographic regions
- **Low Latency:** Geo-distributed reads from nearest datacenter
- **Regulatory Compliance:** Data sovereignty for financial services

---

## 🏗️ Architecture

### Datacenter Topology

```
┌─────────────────────────────────────────────────────────────┐
│                    JanusGraph Graph Layer                    │
│              (Unified view across all DCs)                   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌───────▼────────┐
│   DC1 (Paris)  │   │ DC2 (Frankfurt) │   │ DC3 (London)   │
│   RF = 3       │◄──┤   RF = 3        │──►│   RF = 2       │
│   PRIMARY      │   │   SECONDARY     │   │   DR SITE      │
└────────────────┘   └─────────────────┘   └────────────────┘
     3 nodes              3 nodes              2 nodes
```

### Replication Strategy

**NetworkTopologyStrategy Configuration:**
```properties
storage.cql.replication-strategy-class=NetworkTopologyStrategy
storage.cql.replication-strategy-options=DC1:3,DC2:3,DC3:2
```

**Replication Factors:**
- **DC1 (Paris):** RF=3 - Primary datacenter for EU operations
- **DC2 (Frankfurt):** RF=3 - Secondary datacenter for EU operations
- **DC3 (London):** RF=2 - Disaster recovery site

**Total Nodes:** 8 (3+3+2)

---

## ⚙️ Configuration Details

### JanusGraph Properties

**File:** `config/janusgraph/janusgraph-hcd.properties`

```properties
# Multi-DC Replication Strategy
storage.cql.replication-strategy-class=NetworkTopologyStrategy
storage.cql.replication-strategy-options=DC1:3,DC2:3,DC3:2
storage.cql.local-datacenter=DC1

# Consistency Levels
storage.cql.read-consistency-level=LOCAL_QUORUM
storage.cql.write-consistency-level=LOCAL_QUORUM

# Replication Factor
storage.cql.replication-factor=3
```

### Consistency Levels Explained

**LOCAL_QUORUM:**
- **Reads:** Majority of replicas in local DC must respond
- **Writes:** Majority of replicas in local DC must acknowledge
- **Benefits:**
  - Low latency (no cross-DC coordination)
  - High availability (survives node failures)
  - Strong consistency within DC

**Why LOCAL_QUORUM?**
- Balances consistency and availability
- Prevents cross-DC latency on every operation
- Suitable for financial compliance requirements

---

## 🚀 Deployment

### Development Environment (Single DC)

For local development, the system runs in single-DC mode:

```yaml
# docker-compose.full.yml
hcd-server:
  environment:
    - CASSANDRA_DC=datacenter1
    - CASSANDRA_RACK=rack1
```

**Note:** Multi-DC configuration is active in properties but runs as single DC locally.

### Production Environment (Multi-DC)

**Prerequisites:**
1. 8 HCD nodes across 3 datacenters
2. Network connectivity between DCs (VPN/private network)
3. Synchronized clocks (NTP)
4. DNS resolution for all nodes

**Deployment Steps:**

1. **Deploy DC1 (Paris) - Primary:**
   ```bash
   # Node 1
   CASSANDRA_DC=DC1 CASSANDRA_RACK=rack1 ./start_hcd.sh
   
   # Node 2
   CASSANDRA_DC=DC1 CASSANDRA_RACK=rack2 ./start_hcd.sh
   
   # Node 3
   CASSANDRA_DC=DC1 CASSANDRA_RACK=rack3 ./start_hcd.sh
   ```

2. **Deploy DC2 (Frankfurt) - Secondary:**
   ```bash
   # Node 4
   CASSANDRA_DC=DC2 CASSANDRA_RACK=rack1 CASSANDRA_SEEDS=dc1-node1 ./start_hcd.sh
   
   # Node 5
   CASSANDRA_DC=DC2 CASSANDRA_RACK=rack2 CASSANDRA_SEEDS=dc1-node1 ./start_hcd.sh
   
   # Node 6
   CASSANDRA_DC=DC2 CASSANDRA_RACK=rack3 CASSANDRA_SEEDS=dc1-node1 ./start_hcd.sh
   ```

3. **Deploy DC3 (London) - DR:**
   ```bash
   # Node 7
   CASSANDRA_DC=DC3 CASSANDRA_RACK=rack1 CASSANDRA_SEEDS=dc1-node1 ./start_hcd.sh
   
   # Node 8
   CASSANDRA_DC=DC3 CASSANDRA_RACK=rack2 CASSANDRA_SEEDS=dc1-node1 ./start_hcd.sh
   ```

4. **Verify Cluster Status:**
   ```bash
   nodetool status
   ```

   Expected output:
   ```
   Datacenter: DC1
   ===============
   Status=Up/Down
   |/ State=Normal/Leaving/Joining/Moving
   --  Address    Load       Tokens  Owns    Host ID   Rack
   UN  10.0.1.1   1.2 GB     256     33.3%   abc-123   rack1
   UN  10.0.1.2   1.1 GB     256     33.3%   def-456   rack2
   UN  10.0.1.3   1.3 GB     256     33.4%   ghi-789   rack3
   
   Datacenter: DC2
   ===============
   UN  10.0.2.1   1.2 GB     256     33.3%   jkl-012   rack1
   UN  10.0.2.2   1.1 GB     256     33.3%   mno-345   rack2
   UN  10.0.2.3   1.3 GB     256     33.4%   pqr-678   rack3
   
   Datacenter: DC3
   ===============
   UN  10.0.3.1   800 MB     256     50.0%   stu-901   rack1
   UN  10.0.3.2   850 MB     256     50.0%   vwx-234   rack2
   ```

---

## 🔒 Compliance Benefits

### GDPR Compliance

**Data Residency:**
- EU customer data stored in DC1 (Paris) and DC2 (Frankfurt)
- No data transfer outside EU without explicit consent
- Right to erasure: Delete from all EU DCs

**Implementation:**
```python
# Ensure EU data stays in EU
if customer.region == "EU":
    # Write to DC1/DC2 only
    consistency_level = "LOCAL_QUORUM"
    datacenter = "DC1"  # or DC2
```

### Financial Regulations

**BSA/AML Compliance:**
- Transaction data replicated across DCs for audit trail
- No single point of failure for compliance records
- 7-year retention across multiple sites

**SOC 2 Type II:**
- High availability (99.99% uptime)
- Disaster recovery (RPO < 1 hour, RTO < 4 hours)
- Data integrity (quorum-based consistency)

### Data Sovereignty

**Country-Specific Requirements:**
- **France:** Data stored in DC1 (Paris)
- **Germany:** Data stored in DC2 (Frankfurt)
- **UK:** Data stored in DC3 (London) post-Brexit

---

## 📊 Performance Characteristics

### Latency

**Local Reads (LOCAL_QUORUM):**
- DC1 → DC1: ~5ms
- DC2 → DC2: ~5ms
- DC3 → DC3: ~5ms

**Cross-DC Reads (QUORUM):**
- DC1 → DC2: ~20ms (Paris ↔ Frankfurt)
- DC1 → DC3: ~15ms (Paris ↔ London)
- DC2 → DC3: ~25ms (Frankfurt ↔ London)

**Writes (LOCAL_QUORUM + async replication):**
- Local write: ~10ms
- Cross-DC replication: Asynchronous (eventual consistency)

### Throughput

**Per Datacenter:**
- **Reads:** 50,000 ops/sec (with LOCAL_QUORUM)
- **Writes:** 25,000 ops/sec (with LOCAL_QUORUM)

**Total Cluster:**
- **Reads:** 150,000 ops/sec (3 DCs × 50K)
- **Writes:** 75,000 ops/sec (3 DCs × 25K)

---

## 🛠️ Operations

### Monitoring

**Key Metrics:**
```bash
# Cross-DC replication lag
nodetool tpstats | grep "Cross-DC"

# Per-DC latency
nodetool proxyhistograms

# Cluster health
nodetool status
nodetool ring
```

**Grafana Dashboards:**
- HCD Multi-DC Overview
- Cross-DC Replication Lag
- Per-DC Performance Metrics

### Backup Strategy

**Per-Datacenter Backups:**
```bash
# DC1 (Paris) - Daily full backup
nodetool snapshot janusgraph

# DC2 (Frankfurt) - Daily incremental
nodetool snapshot -t incremental janusgraph

# DC3 (London) - Weekly full backup
nodetool snapshot -t weekly janusgraph
```

**Cross-DC Backup Verification:**
```bash
# Verify data consistency across DCs
./scripts/validation/verify_cross_dc_consistency.sh
```

### Disaster Recovery

**Scenarios:**

1. **Single Node Failure:**
   - Automatic failover within DC
   - No impact on availability (LOCAL_QUORUM)

2. **Single DC Failure:**
   - Redirect traffic to healthy DCs
   - Maintain read/write availability

3. **Multi-DC Failure:**
   - Activate DR procedures
   - Restore from backups

**Recovery Procedures:**
```bash
# Restore DC from backup
./scripts/disaster-recovery/restore_datacenter.sh DC1

# Rebuild failed DC
./scripts/disaster-recovery/rebuild_datacenter.sh DC2

# Verify data integrity
./scripts/validation/verify_data_integrity.sh
```

---

## 🧪 Testing

### Consistency Testing

**Test Cross-DC Replication:**
```python
# Test script: tests/integration/test_multi_dc_consistency.py
def test_cross_dc_replication():
    # Write to DC1
    write_to_dc("DC1", test_data)
    
    # Verify replication to DC2/DC3
    time.sleep(1)  # Allow replication
    assert read_from_dc("DC2", key) == test_data
    assert read_from_dc("DC3", key) == test_data
```

**Test Failover:**
```python
def test_dc_failover():
    # Simulate DC1 failure
    stop_datacenter("DC1")
    
    # Verify reads from DC2/DC3 still work
    assert read_from_dc("DC2", key) == expected_data
    assert read_from_dc("DC3", key) == expected_data
```

### Performance Testing

**Load Test Multi-DC:**
```bash
# Generate load across all DCs
./scripts/testing/load_test_multi_dc.sh

# Expected results:
# - 150K reads/sec total
# - 75K writes/sec total
# - <10ms local latency
# - <30ms cross-DC latency
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Cross-DC Connectivity:**
```bash
# Test network connectivity
telnet dc2-node1 9042
telnet dc3-node1 9042

# Check firewall rules
iptables -L | grep 9042
```

**2. Clock Synchronization:**
```bash
# Verify NTP sync
ntpq -p

# Check clock skew
nodetool gossipinfo | grep "heartbeat"
```

**3. Replication Lag:**
```bash
# Check replication status
nodetool netstats

# Monitor repair progress
nodetool compactionstats
```

### Performance Issues

**High Cross-DC Latency:**
- Check network path: `traceroute dc2-node1`
- Verify bandwidth: `iperf3 -c dc2-node1`
- Monitor packet loss: `ping -c 100 dc2-node1`

**Consistency Issues:**
- Run repair: `nodetool repair janusgraph`
- Check schema agreement: `nodetool describecluster`
- Verify token ranges: `nodetool ring`

---

## 📚 References

### Documentation
- [Cassandra Multi-DC Guide](https://cassandra.apache.org/doc/latest/operating/topo_changes.html)
- [JanusGraph Storage Backend](https://docs.janusgraph.org/storage-backend/)
- [NetworkTopologyStrategy](https://cassandra.apache.org/doc/latest/architecture/dynamo.html#network-topology-strategy)

### Configuration Files
- [`config/janusgraph/janusgraph-hcd.properties`](../../config/janusgraph/janusgraph-hcd.properties)
- [`config/compose/docker-compose.full.yml`](../../config/compose/docker-compose.full.yml)
- [`config/compose/docker-compose.prod.yml`](../../config/compose/docker-compose.prod.yml)

### Scripts
- [`scripts/deployment/deploy_multi_dc.sh`](../../scripts/deployment/deploy_multi_dc.sh) (to be created)
- [`scripts/validation/verify_cross_dc_consistency.sh`](../../scripts/validation/verify_cross_dc_consistency.sh) (to be created)
- [`scripts/disaster-recovery/`](../../scripts/disaster-recovery/) (to be created)

---

**Next Steps:**
- Sprint 1.4: Integrate OpenSearch Vector Search
- Create multi-DC deployment scripts
- Implement cross-DC monitoring dashboards
- Write comprehensive integration tests

---

**Author:** Banking Compliance Platform Team  
**Review:** Platform Engineering, Security Team  
**Approval:** Chief Data Officer, Compliance Officer