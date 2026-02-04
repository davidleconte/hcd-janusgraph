# Troubleshooting Guide

**Version**: 2.0  
**Created**: 2026-01-30

---

## Quick Diagnostics

### Check System Health

```bash
# Pulsar cluster
pulsar-admin brokers healthcheck
pulsar-admin topics stats persistent://banking/transactions/txn-events

# Graph loaders (if using Kubernetes)
kubectl get pods -l app=graph-loader
kubectl logs -l app=graph-loader --tail=100

# JanusGraph
curl http://localhost:8182/gremlin/status
```

---

## Common Issues

### 1. High Pulsar Backlog

**Symptoms**:
- Pulsar backlog > 10M messages
- Consumer lag increasing
- Slow graph updates

**Causes**:
- Insufficient consumer workers
- Graph write bottleneck
- HCD performance issues

**Solutions**:

```bash
# Check backlog
pulsar-admin topics stats persistent://banking/transactions/txn-events | grep backlog

# Scale up consumers (Kubernetes)
kubectl scale deployment graph-loader --replicas=50

# Check graph loader performance
kubectl top pods -l app=graph-loader
```

**Prevention**:
- Auto-scaling based on backlog size
- Monitor consumer processing rate
- Alert when backlog > threshold

---

### 2. Graph Write Failures

**Symptoms**:
- High transaction failure rate
- Consumer errors in logs
- Messages being redelivered

**Causes**:
- Schema violations (unique constraint, type mismatch)
- Transaction conflicts (MVCC)
- HCD unavailability
- Gremlin script errors

**Diagnosis**:

```bash
# Check consumer logs
kubectl logs graph-loader-pod-xxx | grep "Batch load failed"

# Check JanusGraph logs
kubectl logs janusgraph-pod-xxx | grep ERROR

# Check HCD RegionServer status
kubectl get pods -l app=hcd-regionserver
```

**Solutions**:

Schema violation:
```bash
# Check schema definition
gremlin> mgmt = graph.openManagement()
gremlin> mgmt.printSchema()
```

Transaction conflict:
- Increase retry limit
- Add exponential backoff
- Reduce batch size to lower conflict probability

HCD unavailability:
```bash
# Check HCD cluster
kubectl get pods -l app=hcd

# Check HCD Master logs
kubectl logs hcd-master-pod-xxx
```

---

### 3. Deduplication Not Working

**Symptoms**:
- Duplicate graph vertices/edges
- Same transaction_id appears multiple times

**Causes**:
- Broker deduplication disabled
- Producer not setting sequence_id
- Deduplication window expired

**Diagnosis**:

```bash
# Check broker config
pulsar-admin namespaces get-deduplication-snapshot-interval banking/transactions

# Check producer code
grep "sequence_id" producer.py
```

**Solutions**:

Enable deduplication:
```bash
pulsar-admin namespaces set-deduplication --enable banking/transactions
```

Fix producer:
```python
# Always set sequence_id
producer.send(
    content=data,
    sequence_id=transaction['event_id']  # Must be unique per transaction
)
```

---

### 4. HCD Performance Degradation

**Symptoms**:
- Slow graph writes
- HCD WAL size growing
- MemStore pressure

**Causes**:
- Large WAL not flushing
- Compaction storms
- Too many regions

**Diagnosis**:

```bash
# Check WAL size
du -sh /hbase/WALs

# Check MemStore size
grep "memstore" hcd-regionserver.log

# Check compaction queue
grep "compaction" hcd-regionserver.log
```

**Solutions**:

Force WAL flush:
```bash
# In HBase shell
flush 'janusgraph'
```

Tune HCD config:
```xml
<!-- hbase-site.xml -->
<property>
  <name>hbase.regionserver.hlog.blocksize</name>
  <value>134217728</value>  <!-- 128MB -->
</property>

<property>
  <name>hbase.hregion.memstore.flush.size</name>
  <value>134217728</value>  <!-- 128MB -->
</property>
```

---

### 5. Consumer Rebalancing Issues

**Symptoms**:
- Frequent consumer rebalances
- Processing stalls
- Messages redelivered

**Causes**:
- Consumer crashes
- Network issues
- Session timeout too short

**Diagnosis**:

```bash
# Check consumer logs
kubectl logs graph-loader-pod-xxx | grep "rebalance"

# Check Pulsar broker logs
kubectl logs pulsar-broker-pod-xxx | grep "rebalance"
```

**Solutions**:

Increase session timeout:
```python
consumer = client.subscribe(
    topic='...',
    subscription_name='...',
    consumer_type=ConsumerType.Key_Shared,
    # Increase timeout
    receiver_queue_size=1000,
    max_total_receiver_queue_size_across_partitions=50000
)
```

Fix consumer crashes:
- Add try-except around message processing
- Use negative ACK instead of crash
- Monitor memory usage

---

### 6. Out of Memory (OOM)

**Symptoms**:
- Consumer pods killed by OOM
- Graph loader crashes
- Slow processing

**Causes**:
- Large batch size
- Memory leak
- Insufficient memory limits

**Diagnosis**:

```bash
# Check memory usage
kubectl top pods -l app=graph-loader

# Check OOM events
kubectl describe pod graph-loader-pod-xxx | grep OOM
```

**Solutions**:

Reduce batch size:
```python
self.batch_size = 500  # Was 1000
```

Increase memory limits:
```yaml
resources:
  limits:
    memory: "4Gi"  # Was 2Gi
  requests:
    memory: "2Gi"  # Was 1Gi
```

---

### 7. Slow Queries

**Symptoms**:
- Graph queries take minutes
- OpenSearch indexing slow
- High CPU on JanusGraph

**Causes**:
- Missing indices
- Large result sets
- Unoptimized traversal

**Diagnosis**:

```bash
# Check query plan
gremlin> g.V().has('account', 'account_id', 'ACC_123').explain()

# Check indices
gremlin> mgmt = graph.openManagement()
gremlin> mgmt.getGraphIndexes(Vertex.class)
```

**Solutions**:

Add composite index:
```python
mgmt = graph.openManagement()
account_id = mgmt.getPropertyKey('account_id')
mgmt.buildIndex('byAccountId', Vertex.class) \
    .addKey(account_id) \
    .buildCompositeIndex()
mgmt.commit()

# Wait for index to become available
mgmt.awaitGraphIndexStatus(graph, 'byAccountId').call()
```

Optimize traversal:
```python
# Bad: Full scan
g.V().has('amount', gt(10000))

# Good: Use index
g.V().hasLabel('account').has('account_id', 'ACC_123').outE('transfer')
```

---

## Emergency Procedures

### Rollback Deployment

```bash
# Kubernetes
kubectl rollout undo deployment graph-loader

# Check status
kubectl rollout status deployment graph-loader
```

### Pause Message Processing

```bash
# Scale consumers to zero
kubectl scale deployment graph-loader --replicas=0

# Pulsar will buffer messages (up to retention limit)
```

### Clear Backlog (DANGEROUS)

```bash
# Only use in emergency (data loss)
pulsar-admin topics skip-all persistent://banking/transactions/txn-events \
  --subscription graph-loader-subscription
```

### Restart Cluster

```bash
# Pulsar
kubectl rollout restart deployment pulsar-broker
kubectl rollout restart statefulset pulsar-bookkeeper

# JanusGraph
kubectl rollout restart deployment janusgraph

# Graph loaders
kubectl rollout restart deployment graph-loader
```

---

## Debugging Commands

### Pulsar

```bash
# Topic stats
pulsar-admin topics stats persistent://banking/transactions/txn-events

# Consumer stats
pulsar-admin topics stats-internal persistent://banking/transactions/txn-events

# List subscriptions
pulsar-admin topics subscriptions persistent://banking/transactions/txn-events

# Peek messages
pulsar-admin topics peek-messages persistent://banking/transactions/txn-events \
  --subscription graph-loader-subscription \
  --count 10
```

### Graph Loaders

```bash
# Logs
kubectl logs -f graph-loader-pod-xxx

# Shell into pod
kubectl exec -it graph-loader-pod-xxx -- /bin/bash

# Check Python process
kubectl exec graph-loader-pod-xxx -- ps aux | grep python
```

### JanusGraph

```bash
# Gremlin console
kubectl exec -it janusgraph-pod-xxx -- /opt/janusgraph/bin/gremlin.sh

# Count vertices
gremlin> g.V().count()

# Count edges
gremlin> g.E().count()

# Check recent transactions
gremlin> g.V().hasLabel('account').has('account_id', 'ACC_123').outE('transfer').limit(10).valueMap()
```

### HCD

```bash
# HBase shell
kubectl exec -it hcd-master-pod-xxx -- hbase shell

# List tables
hbase> list

# Scan table (first 10 rows)
hbase> scan 'janusgraph', {LIMIT => 10}

# Get table status
hbase> status 'detailed'
```

---

## Performance Analysis

### Identify Bottleneck

```bash
# Pulsar throughput
pulsar-admin topics stats persistent://banking/transactions/txn-events | grep msgRateIn

# Consumer lag
pulsar-admin topics stats persistent://banking/transactions/txn-events | grep msgBacklog

# Graph write rate
kubectl logs graph-loader-pod-xxx | grep "Batch loaded successfully" | wc -l

# HCD write rate
grep "writes/s" hcd-regionserver.log
```

### Profiling

```python
# Add timing to consumer
import time

def _flush_batch(self):
    start = time.time()
    # ... batch processing ...
    duration = time.time() - start
    logger.info(f"Batch flush took {duration:.2f}s")
```

---

## Preventive Measures

### Monitoring

Set up alerts for:
- Backlog > 10M messages
- Consumer failure rate > 5%
- Graph write latency > 5s
- HCD WAL size > 10GB
- Memory usage > 80%

### Testing

Before deployment:
- Load test with expected throughput
- Test failure scenarios (consumer crash, HCD down)
- Verify auto-scaling works
- Test rollback procedure

### Documentation

Keep updated:
- Runbook for common issues
- Escalation contacts
- Recent changes log
- Known issues list

---

**Document Status**: Operations Guide  
**Version**: 2.0  
**Last Updated**: 2026-01-30
