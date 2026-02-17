# Horizontal Scaling Strategy

**Date:** 2026-02-12
**Version:** 1.0
**Status:** Active

## TL;DR

This document describes how to scale the JanusGraph Analytics Platform horizontally across all tiers: API, graph database, storage backend, search, streaming, and caching.

---

## Architecture Overview

```
                    ┌──────────────┐
                    │  Load Balancer│
                    │  (HAProxy/   │
                    │   Nginx)     │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ API Pod 1│ │ API Pod 2│ │ API Pod N│
        │ (FastAPI)│ │ (FastAPI)│ │ (FastAPI)│
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │             │             │
     ┌───────┴─────────────┴─────────────┴───────┐
     │          JanusGraph Cluster                │
     │  ┌─────────┐ ┌─────────┐ ┌─────────┐     │
     │  │ Node 1  │ │ Node 2  │ │ Node N  │     │
     │  └─────────┘ └─────────┘ └─────────┘     │
     └───────────────────┬───────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │   HCD    │  │ OpenSearch│  │  Pulsar  │
    │ (Cass.)  │  │  Cluster │  │  Cluster │
    └──────────┘  └──────────┘  └──────────┘
```

---

## 1. API Tier (FastAPI)

### Scaling Method: Horizontal Pod Autoscaler (HPA)

The FastAPI application is **stateless** — all state lives in JanusGraph, OpenSearch, or Pulsar. This makes it trivially horizontally scalable.

### Configuration

```yaml
# kubernetes/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graph-analytics-api
spec:
  replicas: 3  # minimum
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      containers:
        - name: api
          image: graph-analytics-api:latest
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "2000m"
              memory: "2Gi"
          ports:
            - containerPort: 8000
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8000
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /readyz
              port: 8000
            periodSeconds: 5
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: graph-analytics-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Key Considerations

- **Session affinity**: Not required (stateless)
- **Rate limiting**: Use `SlowAPI` with Redis backend for distributed rate limiting across pods
- **Connection pooling**: Each pod maintains its own JanusGraph connection pool (configured via `Settings.connection_pool_size`)
- **Graceful shutdown**: `lifespan` context manager closes connections on SIGTERM

---

## 2. JanusGraph Tier

### Scaling Method: Add JanusGraph Instances

JanusGraph nodes are **stateless query processors** — they share the same HCD (Cassandra) backend and OpenSearch index.

| Topology | Nodes | Use Case |
|----------|-------|----------|
| Development | 1 | Local dev, CI |
| Staging | 2 | Integration testing |
| Production | 3-5 | Normal workloads |
| High-traffic | 5-10+ | Large-scale analytics |

### Configuration

Set `COMPOSE_FULL_STACK_FILE` to the full-stack compose file path before using this overlay.

```yaml
# compose-scale overlay
services:
  janusgraph-1:
    extends:
      file: ${COMPOSE_FULL_STACK_FILE}
      service: janusgraph
    environment:
      JANUSGRAPH_INSTANCE_ID: "jg-1"

  janusgraph-2:
    extends:
      file: ${COMPOSE_FULL_STACK_FILE}
      service: janusgraph
    environment:
      JANUSGRAPH_INSTANCE_ID: "jg-2"

  janusgraph-3:
    extends:
      file: ${COMPOSE_FULL_STACK_FILE}
      service: janusgraph
    environment:
      JANUSGRAPH_INSTANCE_ID: "jg-3"
```

### Load Balancing

Use a TCP load balancer (HAProxy/Nginx) in front of JanusGraph WebSocket endpoints:

```nginx
upstream janusgraph {
    least_conn;
    server janusgraph-1:8182;
    server janusgraph-2:8182;
    server janusgraph-3:8182;
}
```

---

## 3. Storage Backend (HCD/Cassandra)

### Scaling Method: Add Cassandra Nodes

HCD (Hyper-Converged Database) scales by adding nodes to the ring. Data is automatically rebalanced.

| Cluster Size | Replication Factor | Consistency | Fault Tolerance |
|-------------|-------------------|-------------|-----------------|
| 3 nodes | RF=3 | QUORUM | 1 node failure |
| 5 nodes | RF=3 | QUORUM | 2 node failures |
| 7 nodes | RF=3 | QUORUM | 3 node failures |

### Steps to Add a Node

1. Configure new node with matching `cluster_name` and seed nodes
2. Start the node — it auto-joins and streams data
3. Run `nodetool status` to verify
4. Run `nodetool cleanup` on existing nodes to remove migrated data

### JanusGraph Keyspace Configuration

```cql
ALTER KEYSPACE janusgraph
WITH replication = {
  'class': 'NetworkTopologyStrategy',
  'dc1': 3
};
```

---

## 4. Search (OpenSearch)

### Scaling Method: Add Data/Search Nodes

| Node Type | Role | Scaling |
|-----------|------|---------|
| Manager | Cluster coordination | 3 (fixed, odd number) |
| Data | Index storage | Scale with data volume |
| Search | Query processing | Scale with query load |
| Ingest | Document processing | Scale with write load |

### Index Configuration for Scale

```json
{
  "settings": {
    "number_of_shards": 5,
    "number_of_replicas": 1,
    "refresh_interval": "5s"
  }
}
```

**Shard sizing guideline**: 10-50 GB per shard, max 20 shards per GB of heap.

---

## 5. Streaming (Apache Pulsar)

### Scaling Method: Add Brokers and Bookies

| Component | Scaling | Purpose |
|-----------|---------|---------|
| Brokers | Horizontal | Message routing, topic ownership |
| Bookies | Horizontal | Message storage |
| ZooKeeper | 3-5 (fixed) | Metadata coordination |

### Topic Partitioning

For high-throughput topics, increase partitions:

```bash
bin/pulsar-admin topics create-partitioned-topic \
  persistent://public/banking/transactions-events \
  --partitions 8
```

**Partition guidelines**:
- 1 partition: < 1K msg/s
- 4 partitions: 1K-10K msg/s
- 8-16 partitions: 10K-100K msg/s
- 32+ partitions: > 100K msg/s

---

## 6. Query Cache (Distributed)

### Current: In-Process Cache

The `QueryCache` class provides per-instance caching. This works for single-instance deployments.

### Recommended: Redis-Backed Distributed Cache

For multi-instance API deployments, replace the in-process cache with Redis:

```python
# Future implementation sketch
class RedisQueryCache(QueryCache):
    def __init__(self, redis_url: str, **kwargs):
        super().__init__(**kwargs)
        self.redis = redis.Redis.from_url(redis_url)

    def get(self, key: str) -> Optional[Any]:
        cached = self.redis.get(f"qcache:{key}")
        if cached:
            self.stats.hits += 1
            return pickle.loads(cached)
        self.stats.misses += 1
        return None
```

### Redis Cluster Configuration

```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
```

---

## 7. Capacity Planning

### Per-Component Resource Requirements

| Component | CPU (cores) | Memory (GB) | Storage | Network |
|-----------|------------|-------------|---------|---------|
| API Pod | 0.5-2 | 0.5-2 | Minimal | Low |
| JanusGraph | 2-4 | 4-8 | Minimal | Medium |
| HCD Node | 4-8 | 16-32 | SSD (IOPS) | High |
| OpenSearch Node | 2-4 | 8-16 | SSD | Medium |
| Pulsar Broker | 2-4 | 4-8 | Minimal | High |
| Pulsar Bookie | 2-4 | 4-8 | SSD (throughput) | High |

### Scaling Triggers

| Metric | Threshold | Action |
|--------|-----------|--------|
| API CPU > 70% | Sustained 5 min | Add API pods |
| API P95 latency > 500ms | Sustained 5 min | Add API pods or JanusGraph nodes |
| JanusGraph query queue > 100 | Sustained 1 min | Add JanusGraph nodes |
| Cassandra read latency P99 > 50ms | Sustained 5 min | Add Cassandra nodes |
| OpenSearch search latency P95 > 200ms | Sustained 5 min | Add OpenSearch search nodes |
| Pulsar backlog > 10K messages | Sustained 1 min | Add consumers or partitions |
| Disk usage > 75% | Any | Add storage nodes |

---

## 8. Deployment Checklist

- [ ] Load balancer configured with health checks
- [ ] API pods set to minimum 3 replicas
- [ ] HPA configured with CPU/memory targets
- [ ] JanusGraph connection pool sized per pod (default: 8)
- [ ] Distributed rate limiting (Redis) if multi-pod
- [ ] Monitoring alerts for scaling triggers
- [ ] Cassandra replication factor matches cluster size
- [ ] OpenSearch shard count appropriate for data volume
- [ ] Pulsar topic partitions match throughput requirements
- [ ] Graceful shutdown handlers verified
- [ ] Rolling update strategy configured (zero downtime)

---

## Related Documentation

- [Operations Runbook](../operations/operations-runbook.md)
- [Production Readiness Audit](../implementation/production-readiness-audit-2026.md)
- [Monitoring & Alerting](../operations/monitoring-alerting.md)
