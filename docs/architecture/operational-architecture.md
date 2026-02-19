# Operational Architecture

## Document Information

- **Document Version:** 1.0.0
- **Last Updated:** 2026-02-19
- **Owner:** Operations Team & Architecture Team
- **Status:** Active
- **Related:** [architecture-overview.md](architecture-overview.md), [Operations Runbook](../operations/operations-runbook.md), [Service Startup Sequence](service-startup-sequence.md)

---

## Executive Summary

This document defines the **operational architecture** of the HCD JanusGraph Banking Compliance Platform, describing how the system operates in production. It covers runtime topology, service communication patterns, data flow, monitoring integration, incident response, capacity planning, and performance characteristics.

**Key Focus Areas:**
- **Runtime Topology:** How services are deployed and connected
- **Service Communication:** Inter-service communication patterns
- **Data Flow:** How data moves through the system
- **Monitoring Integration:** Observability and alerting
- **Incident Response:** Operational incident handling
- **Capacity Planning:** Resource requirements and scaling

---

## Table of Contents

1. [Runtime Topology](#1-runtime-topology)
2. [Service Communication](#2-service-communication)
3. [Data Flow](#3-data-flow)
4. [Monitoring Integration](#4-monitoring-integration)
5. [Incident Response](#5-incident-response)
6. [Capacity Planning](#6-capacity-planning)
7. [Performance Characteristics](#7-performance-characteristics)

---

## 1. Runtime Topology

### 1.1 Production Deployment Model

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL ACCESS                           │
│  Users → Load Balancer → API Gateway → Services                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                     PODMAN RUNTIME                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PROJECT: janusgraph-demo                                 │  │
│  │  NETWORK: janusgraph-demo_hcd-janusgraph-network         │  │
│  │                                                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │  Analytics  │  │   Jupyter   │  │ Visualizers │      │  │
│  │  │     API     │  │     Lab     │  │  GraphExp   │      │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │  │
│  │         │                 │                 │             │  │
│  │  ┌──────┴─────────────────┴─────────────────┴──────┐    │  │
│  │  │           JanusGraph Server                      │    │  │
│  │  │           (Gremlin Queries)                      │    │  │
│  │  └──────┬───────────────────────────────┬───────────┘    │  │
│  │         │                               │                 │  │
│  │  ┌──────┴──────┐              ┌────────┴────────┐        │  │
│  │  │     HCD     │              │   OpenSearch    │        │  │
│  │  │ (Cassandra) │              │   (Indexing)    │        │  │
│  │  └─────────────┘              └─────────────────┘        │  │
│  │                                                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │   Pulsar    │  │   Vault     │  │ Prometheus  │      │  │
│  │  │ (Streaming) │  │  (Secrets)  │  │ (Metrics)   │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Network Topology

**Network:** `janusgraph-demo_hcd-janusgraph-network` (bridge mode)

**Network Segments:**

| Segment | Services | Purpose |
|---------|----------|---------|
| **Data Layer** | HCD, OpenSearch | Persistent storage |
| **Core Layer** | JanusGraph, Pulsar | Core services |
| **Application Layer** | Analytics API, Consumers | Business logic |
| **Client Layer** | Jupyter, Visualizers, Dashboards | User interfaces |
| **Infrastructure Layer** | Vault, Prometheus, Grafana | Infrastructure services |

**Network Isolation:**
- All services in single bridge network (development)
- Production: Separate networks per layer
- No direct external access to data layer
- API Gateway for external access

### 1.3 Service Distribution

**19 Services Across 5 Layers:**

```
Foundation Layer (3 services)
├── vault (secrets management)
├── hcd-server (distributed storage)
└── opensearch (search and indexing)

Core Services Layer (4 services)
├── janusgraph-server (graph database)
├── pulsar (message broker)
├── opensearch-dashboards (search UI)
└── gremlin-console (admin tool)

Application Layer (5 services)
├── analytics-api (REST API)
├── jupyter (notebooks)
├── graph-consumer (Pulsar → JanusGraph)
├── vector-consumer (Pulsar → OpenSearch)
└── cqlsh-client (admin tool)

Monitoring Layer (5 services)
├── prometheus (metrics collection)
├── grafana (visualization)
├── alertmanager (alerting)
├── janusgraph-exporter (custom metrics)
└── pulsar-cli (admin tool)

Visualization Layer (2 services)
├── janusgraph-visualizer (graph visualization)
└── graphexp (graph exploration)
```

### 1.4 Resource Allocation

**Total Resources (Development):**
- **CPU:** 17.0 cores (limits), 10.0 cores (actual usage)
- **Memory:** 36 GB (limits), 20 GB (actual usage)
- **Disk:** 50 GB (Podman machine)

**Resource Distribution:**

| Service | CPU Limit | Memory Limit | Actual Usage |
|---------|-----------|--------------|--------------|
| **hcd-server** | 4.0 | 8G | 3.5 / 6G |
| **janusgraph-server** | 2.0 | 6G | 1.5 / 4G |
| **opensearch** | 2.0 | 4G | 1.0 / 2G |
| **pulsar** | 2.0 | 4G | 1.0 / 2G |
| **jupyter** | 2.0 | 4G | 0.5 / 1G |
| **analytics-api** | 1.0 | 2G | 0.3 / 512M |
| **Other services** | 4.0 | 8G | 2.2 / 4.5G |

**Production Recommendations:**
- **CPU:** 32 cores minimum
- **Memory:** 64 GB minimum
- **Disk:** 500 GB minimum (SSD)

---

## 2. Service Communication

### 2.1 Communication Patterns

**Synchronous Communication (Request/Response):**

```
Client → Analytics API → JanusGraph → HCD
                      ↓
                  OpenSearch
```

**Asynchronous Communication (Event-Driven):**

```
Data Generator → Pulsar Topics → Graph Consumer → JanusGraph
                               ↓
                          Vector Consumer → OpenSearch
```

**Administrative Communication:**

```
Operator → Gremlin Console → JanusGraph
        ↓
     CQLSH Client → HCD
        ↓
     Pulsar CLI → Pulsar
```

### 2.2 Communication Protocols

| Source | Destination | Protocol | Port | Purpose |
|--------|-------------|----------|------|---------|
| **Analytics API** | JanusGraph | WebSocket | 8182 | Gremlin queries |
| **JanusGraph** | HCD | CQL | 9042 | Data storage |
| **JanusGraph** | OpenSearch | HTTP | 9200 | Indexing |
| **Graph Consumer** | JanusGraph | WebSocket | 8182 | Event ingestion |
| **Graph Consumer** | Pulsar | Binary | 6650 | Event consumption |
| **Vector Consumer** | OpenSearch | HTTP | 9200 | Vector storage |
| **Vector Consumer** | Pulsar | Binary | 6650 | Event consumption |
| **Prometheus** | JanusGraph Exporter | HTTP | 8000 | Metrics scraping |
| **Prometheus** | HCD | JMX | 7199 | Metrics scraping |
| **Grafana** | Prometheus | HTTP | 9090 | Metrics queries |
| **Jupyter** | JanusGraph | WebSocket | 8182 | Interactive queries |
| **Visualizers** | JanusGraph | WebSocket | 8182 | Graph visualization |

### 2.3 Service Dependencies

**Critical Path (Startup):**

```
Vault → HCD → JanusGraph → Analytics API
                         ↓
                      Jupyter
```

**Parallel Paths:**

```
Pulsar → Graph Consumer → JanusGraph
      ↓
   Vector Consumer → OpenSearch
```

**Monitoring Path:**

```
Services → Exporters → Prometheus → Grafana
                    ↓
                AlertManager
```

### 2.4 Communication Resilience

**Retry Policies:**

| Service | Retry Strategy | Max Retries | Backoff |
|---------|---------------|-------------|---------|
| **Analytics API** | Exponential | 3 | 1s, 2s, 4s |
| **Graph Consumer** | Exponential | 5 | 1s, 2s, 4s, 8s, 16s |
| **Vector Consumer** | Exponential | 5 | 1s, 2s, 4s, 8s, 16s |
| **JanusGraph Exporter** | Linear | 3 | 5s, 5s, 5s |

**Circuit Breakers:**
- Analytics API: 5 failures in 10s → open for 30s
- Consumers: 10 failures in 60s → open for 60s

**Timeouts:**
- API requests: 30s
- Gremlin queries: 60s
- Consumer processing: 120s
- Health checks: 10s

---

## 3. Data Flow

### 3.1 Write Path (Event-Driven)

```
1. Data Generator
   ↓ (produces events)
2. Pulsar Topics
   ├─→ persons-events
   ├─→ accounts-events
   ├─→ transactions-events
   ├─→ companies-events
   └─→ communications-events
   ↓ (consumed by)
3. Consumers
   ├─→ Graph Consumer → JanusGraph → HCD (graph storage)
   └─→ Vector Consumer → OpenSearch (vector storage)
```

**Write Throughput:**
- **Pulsar:** 10,000 events/sec
- **Graph Consumer:** 1,000 vertices/sec
- **Vector Consumer:** 2,000 documents/sec

**Write Latency:**
- **Pulsar publish:** < 10ms (P95)
- **Graph write:** < 50ms (P95)
- **Vector write:** < 20ms (P95)

### 3.2 Read Path (Query-Driven)

```
1. Client (Jupyter, API, Visualizer)
   ↓ (sends query)
2. JanusGraph Server
   ├─→ HCD (graph traversal)
   └─→ OpenSearch (full-text search)
   ↓ (returns results)
3. Client (receives results)
```

**Read Throughput:**
- **Simple queries:** 200 qps
- **Complex queries:** 50 qps
- **Full-text search:** 500 qps

**Read Latency:**
- **Simple queries:** < 50ms (P95)
- **Complex queries:** < 500ms (P95)
- **Full-text search:** < 100ms (P95)

### 3.3 Data Lifecycle

**Data Ingestion:**

```
Raw Data → Validation → Enrichment → Pulsar → Consumers → Storage
```

**Data Processing:**

```
Storage → Query → Transform → Aggregate → Results
```

**Data Archival:**

```
Storage → Backup → Compression → Encryption → Cloud Storage
```

**Data Retention:**
- **Hot data:** 30 days (in-memory cache)
- **Warm data:** 90 days (SSD storage)
- **Cold data:** 1 year (HDD storage)
- **Archive:** 7 years (cloud storage)

### 3.4 Data Consistency

**Consistency Model:**
- **JanusGraph:** Eventual consistency (tunable)
- **HCD:** Tunable consistency (default: LOCAL_QUORUM)
- **OpenSearch:** Eventual consistency
- **Pulsar:** At-least-once delivery

**Consistency Guarantees:**
- **Writes:** Acknowledged after replication
- **Reads:** May see stale data (< 1s)
- **Transactions:** ACID within single graph transaction

---

## 4. Monitoring Integration

### 4.1 Metrics Collection Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    METRICS SOURCES                           │
├─────────────────────────────────────────────────────────────┤
│  JanusGraph → JanusGraph Exporter → Prometheus              │
│  HCD → JMX Exporter → Prometheus                            │
│  OpenSearch → Native Metrics → Prometheus                   │
│  Pulsar → Native Metrics → Prometheus                       │
│  Analytics API → FastAPI Metrics → Prometheus               │
│  Podman → cAdvisor → Prometheus                             │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    PROMETHEUS                                │
│  - Metrics storage (15 days retention)                      │
│  - Alert evaluation (31 rules)                              │
│  - Query engine (PromQL)                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────┴────────┐            ┌────────┴────────┐
│    GRAFANA      │            │  ALERTMANAGER   │
│  - Dashboards   │            │  - Routing      │
│  - Visualization│            │  - Grouping     │
│  - Queries      │            │  - Notification │
└─────────────────┘            └─────────────────┘
```

### 4.2 Key Metrics

**System Metrics:**
- `node_cpu_seconds_total` - CPU usage
- `node_memory_MemAvailable_bytes` - Available memory
- `node_disk_io_time_seconds_total` - Disk I/O
- `node_network_receive_bytes_total` - Network RX
- `node_network_transmit_bytes_total` - Network TX

**JanusGraph Metrics:**
- `janusgraph_vertices_total` - Total vertices
- `janusgraph_edges_total` - Total edges
- `janusgraph_query_duration_seconds` - Query latency
- `janusgraph_errors_total` - Error count
- `janusgraph_connection_status` - Connection health

**Application Metrics:**
- `http_requests_total` - Request count
- `http_request_duration_seconds` - Request latency
- `http_requests_in_progress` - Active requests
- `http_response_size_bytes` - Response size

**Business Metrics:**
- `banking_transactions_total` - Transaction count
- `banking_aml_alerts_total` - AML alert count
- `banking_fraud_detections_total` - Fraud detection count

### 4.3 Alert Rules (31 Total)

**System Health (8 rules):**
- ServiceDown
- HighCPUUsage (> 80%)
- HighMemoryUsage (> 90%)
- DiskSpaceLow (< 15%)
- HighDiskIO (> 80%)
- NetworkSaturation (> 80%)
- HighLoadAverage (> 4.0)
- SystemRestart

**JanusGraph (4 rules):**
- HighQueryLatency (P95 > 1s)
- HighErrorRate (> 5%)
- ConnectionPoolExhaustion (> 90%)
- SlowQueries (> 10/min)

**Security (8 rules):**
- HighFailedAuthRate (> 10/min)
- UnauthorizedAccess (> 5/min)
- CertificateExpiring (< 30 days)
- VaultSealed
- SuspiciousActivity
- DataExfiltration
- PrivilegeEscalation
- SecurityPolicyViolation

**Performance (3 rules):**
- HighResponseTime (P95 > 2s)
- High5xxErrorRate (> 1%)
- LowThroughput (< 50 qps)

**Cassandra (3 rules):**
- CassandraNodeDown
- HighLatency (P95 > 100ms)
- HighPendingTasks (> 1000)

**Compliance (2 rules):**
- ComplianceScoreLow (< 80%)
- AuditLogGap (> 1 hour)

**Backup (3 rules):**
- BackupFailed
- BackupStale (> 24 hours)
- BackupSizeMismatch (> 20% variance)

### 4.4 Dashboards

**System Overview Dashboard:**
- Service status (up/down)
- Resource utilization (CPU, memory, disk)
- Network traffic
- Error rates

**JanusGraph Performance Dashboard:**
- Query latency (P50, P95, P99)
- Throughput (qps)
- Error rate
- Connection pool status
- Vertex/edge counts

**API Performance Dashboard:**
- Request latency
- Request rate
- Error rate
- Response size
- Active connections

**Security Monitoring Dashboard:**
- Failed authentication attempts
- Unauthorized access attempts
- Certificate expiry status
- Vault status
- Audit log status

**Compliance Dashboard:**
- Compliance score
- AML alerts
- Fraud detections
- Audit log completeness
- Data retention status

---

## 5. Incident Response

### 5.1 Incident Response Flow

```
1. DETECTION
   ├─→ Automated (Prometheus alerts)
   ├─→ Manual (User reports)
   └─→ Monitoring (Dashboard observation)
   ↓
2. TRIAGE
   ├─→ Classify severity (P0-P3)
   ├─→ Identify affected services
   └─→ Estimate impact
   ↓
3. INVESTIGATION
   ├─→ Check logs (podman logs)
   ├─→ Check metrics (Grafana)
   ├─→ Check health (health checks)
   └─→ Identify root cause
   ↓
4. MITIGATION
   ├─→ Apply fix (restart, config change)
   ├─→ Implement workaround
   └─→ Communicate status
   ↓
5. RESOLUTION
   ├─→ Verify fix
   ├─→ Monitor for recurrence
   └─→ Document incident
   ↓
6. POST-MORTEM
   ├─→ Root cause analysis
   ├─→ Lessons learned
   └─→ Action items
```

### 5.2 Incident Classification

| Priority | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **P0** | System down, data loss | 15 minutes | Complete outage, G5 failure |
| **P1** | Critical functionality impaired | 1 hour | G8 failure, high error rate |
| **P2** | Major functionality degraded | 4 hours | G7 failure, slow queries |
| **P3** | Minor issues | 1 business day | G9 failure, warnings |

### 5.3 Incident Response Procedures

**P0 Incident (System Down):**

```bash
# 1. Acknowledge alert
# 2. Check service status
podman ps --filter "label=io.podman.compose.project=janusgraph-demo"

# 3. Check logs
podman logs janusgraph-demo_service_1 --tail 100

# 4. Attempt restart
podman restart janusgraph-demo_service_1

# 5. If restart fails, redeploy
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# 6. Escalate if not resolved in 15 minutes
```

**P1 Incident (High Error Rate):**

```bash
# 1. Check error logs
podman logs janusgraph-demo_service_1 | grep -i error

# 2. Check metrics
curl http://localhost:9090/api/v1/query?query=rate(errors_total[5m])

# 3. Identify error pattern
# 4. Apply fix or workaround
# 5. Monitor for improvement
# 6. Escalate if not resolved in 1 hour
```

### 5.4 Escalation Path

```
L1 (On-Call Engineer)
    ↓ (30 min)
L2 (Senior Engineer)
    ↓ (2 hours)
L3 (Team Lead)
    ↓ (4 hours)
L4 (Engineering Manager)
    ↓ (Critical)
L5 (CTO)
```

### 5.5 Communication During Incidents

**Internal Communication:**
- Slack channel: #incidents
- Status page: internal.status.example.com
- Email: ops-team@example.com

**External Communication:**
- Status page: status.example.com
- Email: support@example.com
- Twitter: @example_status

**Communication Frequency:**
- P0: Every 15 minutes
- P1: Every 30 minutes
- P2: Every 2 hours
- P3: Daily

---

## 6. Capacity Planning

### 6.1 Current Capacity

**Development Environment:**
- **CPU:** 4 cores (Podman machine)
- **Memory:** 8 GB (Podman machine)
- **Disk:** 50 GB (Podman machine)
- **Network:** 1 Gbps (local)

**Capacity Utilization:**
- **CPU:** 60-70% average, 90% peak
- **Memory:** 50-60% average, 80% peak
- **Disk:** 30-40% usage
- **Network:** < 10% utilization

### 6.2 Production Capacity Requirements

**Minimum Production:**
- **CPU:** 32 cores
- **Memory:** 64 GB
- **Disk:** 500 GB SSD
- **Network:** 10 Gbps

**Recommended Production:**
- **CPU:** 64 cores
- **Memory:** 128 GB
- **Disk:** 1 TB SSD
- **Network:** 10 Gbps

**High-Availability Production:**
- **CPU:** 128 cores (across 3 nodes)
- **Memory:** 256 GB (across 3 nodes)
- **Disk:** 2 TB SSD (per node)
- **Network:** 10 Gbps (per node)

### 6.3 Scaling Strategies

**Vertical Scaling (Single Node):**

```bash
# Increase Podman machine resources
podman machine stop
podman machine set --cpus 8 --memory 16384
podman machine start

# Update service limits in docker-compose.yml
services:
  hcd-server:
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
```

**Horizontal Scaling (Multi-Node):**

```yaml
# Scale JanusGraph servers
services:
  janusgraph-server:
    deploy:
      replicas: 3

# Scale Cassandra nodes
services:
  hcd-server:
    deploy:
      replicas: 3
```

**Auto-Scaling (Kubernetes):**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: janusgraph-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: janusgraph-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 6.4 Capacity Monitoring

**Key Capacity Metrics:**
- CPU utilization trend
- Memory utilization trend
- Disk usage trend
- Network bandwidth trend
- Query latency trend
- Throughput trend

**Capacity Alerts:**
- CPU > 80% for 10 minutes
- Memory > 90% for 5 minutes
- Disk > 85% usage
- Network > 80% saturation
- Query latency increasing trend
- Throughput decreasing trend

### 6.5 Growth Projections

**Expected Growth (Next 12 Months):**
- **Data volume:** 3x growth
- **Query volume:** 2x growth
- **User count:** 2x growth

**Capacity Requirements (12 Months):**
- **CPU:** 96 cores (3x current)
- **Memory:** 192 GB (3x current)
- **Disk:** 1.5 TB (3x current)
- **Network:** 10 Gbps (same)

---

## 7. Performance Characteristics

### 7.1 Latency Targets

| Operation | Target (P95) | Typical | Max Acceptable |
|-----------|--------------|---------|----------------|
| **Simple query** | < 50ms | 30-40ms | 100ms |
| **Complex query** | < 500ms | 200-400ms | 1000ms |
| **Write operation** | < 100ms | 50-80ms | 200ms |
| **Full-text search** | < 100ms | 50-80ms | 200ms |
| **API request** | < 200ms | 100-150ms | 500ms |

### 7.2 Throughput Targets

| Operation | Target | Typical | Peak |
|-----------|--------|---------|------|
| **Read queries** | > 100 qps | 150-200 qps | 500 qps |
| **Write operations** | > 50 wps | 100-150 wps | 300 wps |
| **API requests** | > 200 rps | 300-400 rps | 1000 rps |
| **Event ingestion** | > 1000 eps | 2000-3000 eps | 10000 eps |

### 7.3 Availability Targets

| Service | Target | Typical | Downtime/Year |
|---------|--------|---------|---------------|
| **JanusGraph** | 99.9% | 99.95% | 8.76 hours |
| **HCD** | 99.9% | 99.95% | 8.76 hours |
| **Analytics API** | 99.5% | 99.8% | 43.8 hours |
| **Overall System** | 99.5% | 99.7% | 43.8 hours |

### 7.4 Performance Optimization

**Query Optimization:**
- Use indexes for frequent queries
- Limit result sets
- Use pagination
- Cache frequent queries
- Optimize traversal patterns

**Write Optimization:**
- Batch writes
- Use async writes
- Optimize schema
- Use appropriate consistency level
- Minimize transaction scope

**Resource Optimization:**
- Right-size containers
- Use resource limits
- Monitor resource usage
- Scale proactively
- Optimize JVM settings

---

## Appendices

### Appendix A: Service Endpoints

| Service | Internal | External | Protocol |
|---------|----------|----------|----------|
| **Analytics API** | analytics-api:8001 | localhost:8001 | HTTP |
| **JanusGraph** | janusgraph-server:8182 | localhost:18182 | WebSocket |
| **HCD** | hcd-server:9042 | localhost:19042 | CQL |
| **OpenSearch** | opensearch:9200 | localhost:9200 | HTTP |
| **Pulsar** | pulsar:6650 | localhost:6650 | Binary |
| **Vault** | vault:8200 | localhost:8200 | HTTP |
| **Prometheus** | prometheus:9090 | localhost:9090 | HTTP |
| **Grafana** | grafana:3000 | localhost:3001 | HTTP |

### Appendix B: Related Documentation

- **Architecture:**
  - [architecture-overview.md](architecture-overview.md)
  - [Deployment Architecture](deployment-architecture.md)
  - [Service Startup Sequence](service-startup-sequence.md)
  - [Troubleshooting Architecture](troubleshooting-architecture.md)

- **Operations:**
  - [Operations Runbook](../operations/operations-runbook.md)
  - [Disaster Recovery Plan](../operations/disaster-recovery-plan.md)

---

**Document Classification:** Internal - Operations  
**Next Review Date:** 2026-05-19  
**Document Owner:** Operations Team & Architecture Team  
**Version:** 1.0.0

---

## Change Log

### Version 1.0.0 (2026-02-19)
- Initial version
- Complete operational architecture
- Runtime topology and service communication
- Data flow and monitoring integration
- Incident response and capacity planning
- Performance characteristics