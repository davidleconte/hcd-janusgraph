# HCD + JanusGraph Banking Compliance System
# Technical Specifications Document

**Version:** 1.0.0  
**Date:** 2026-01-30  
**Status:** Complete Outline/Template  
**Author:** IBM Bob (AdaL)  
**Project:** Hierarchical Content Delivery + JanusGraph Banking Compliance System

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-30 | IBM Bob | Initial comprehensive outline based on audit findings |

### Document Purpose

This technical specifications document provides a complete architectural and implementation blueprint for the HCD + JanusGraph Banking Compliance System. It serves as the authoritative reference for system architects, developers, DevOps engineers, security teams, and QA teams.

### Related Documents

- [`docs/implementation/audits/COMPREHENSIVE_PROJECT_AUDIT_2026-01-30.md`](implementation/audits/COMPREHENSIVE_PROJECT_AUDIT_2026-01-30.md) - Current state audit
- [`docs/implementation/audits/EXTENDED_AUDIT_FINDINGS_2026-01-30.md`](implementation/audits/EXTENDED_AUDIT_FINDINGS_2026-01-30.md) - Extended findings
- [`.bob/rules-plan/PODMAN_ISOLATION.md`](../.bob/rules-plan/PODMAN_ISOLATION.md) - Container isolation rules
- [`AGENTS.md`](../AGENTS.md) - Development guidelines

---

## Table of Contents

1. [System Architecture Specifications](#1-system-architecture-specifications)
2. [Data Model Specifications](#2-data-model-specifications)
3. [API Specifications](#3-api-specifications)
4. [Container Isolation Specifications](#4-container-isolation-specifications)
5. [Performance Specifications](#5-performance-specifications)
6. [Security Specifications](#6-security-specifications)
7. [Integration Specifications](#7-integration-specifications)
8. [Monitoring and Observability Specifications](#8-monitoring-and-observability-specifications)
9. [Deployment Specifications](#9-deployment-specifications)
10. [Testing Specifications](#10-testing-specifications)

---

# 1. System Architecture Specifications

## 1.1 Architecture Overview

### 1.1.1 System Purpose
Enterprise-grade graph database solution for banking compliance, AML detection, fraud detection, and customer 360° view.

### 1.1.2 Architecture Style
- Microservices-based containerized architecture
- Event-driven for real-time detection
- Graph-native data model
- Distributed storage with Cassandra backend
- Rootless containers for security

### 1.1.3 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Podman Machine (VM)                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              janusgraph-demo-core Pod                     │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │ │
│  │  │ HCD Server   │  │ JanusGraph   │  │ Gremlin      │   │ │
│  │  │ (Cassandra)  │  │ Server       │  │ Console      │   │ │
│  │  │ Port: 9042   │  │ Port: 8182   │  │              │   │ │
│  │  │ Port: 9142   │  │ Port: 8184   │  │              │   │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              janusgraph-demo-monitoring Pod               │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │ │
│  │  │ Prometheus   │  │ Grafana      │  │ AlertManager │   │ │
│  │  │ Port: 9090   │  │ Port: 3001   │  │ Port: 9093   │   │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 1.2 Container Specifications

### 1.2.1 HCD Container
- **Image**: `localhost/hcd:1.2.3`
- **Base**: Red Hat UBI 8
- **Resources**: 4GB RAM, 2 CPUs
- **Volumes**: data, commitlog, saved_caches, hints, logs
- **Ports**: 9042 (CQL), 9142 (CQL+TLS), 7000/7001 (inter-node)

### 1.2.2 JanusGraph Container
- **Image**: `docker.io/janusgraph/janusgraph:latest`
- **Resources**: 4GB RAM, 2 CPUs
- **Volumes**: db, index, logs
- **Ports**: 8182 (Gremlin), 8184 (Management)

### 1.2.3 Monitoring Stack
- **Prometheus**: Metrics collection (2GB RAM, 1 CPU)
- **Grafana**: Visualization (1GB RAM, 0.5 CPU)
- **AlertManager**: Alert routing (512MB RAM, 0.5 CPU)

## 1.3 Network Architecture

### 1.3.1 Network Topology
- **Network Name**: `janusgraph-demo-network`
- **Subnet**: `10.89.5.0/24`
- **Gateway**: `10.89.5.1`
- **Isolation**: Pod-level network namespaces

### 1.3.2 Port Mapping
| Service | Internal | External | Protocol |
|---------|----------|----------|----------|
| JanusGraph | 8182 | 8182 | WebSocket |
| HCD CQL | 9042 | 9042 | TCP |
| HCD CQL+TLS | 9142 | 9142 | TCP |
| Prometheus | 9090 | 9090 | HTTP |
| Grafana | 3000 | 3001 | HTTP |

## 1.4 Volume Management

### 1.4.1 Volume Naming Convention
Format: `{project}-{component}-{purpose}`

Example: `janusgraph-demo-hcd-data`

### 1.4.2 Critical Volumes
- `janusgraph-demo-hcd-data` (100GB) - Cassandra data
- `janusgraph-demo-janusgraph-db` (50GB) - Graph database
- `janusgraph-demo-vault-data` (5GB) - Encrypted secrets
- `janusgraph-demo-audit-logs` (20GB) - Audit trail

---

# 2. Data Model Specifications

## 2.1 Graph Schema

### 2.1.1 Vertex Types

#### Person Vertex
```groovy
label: 'person'
properties:
  - personId: String (UUID, unique, indexed)
  - firstName: String (indexed, mixed)
  - lastName: String (indexed, mixed)
  - dateOfBirth: Date (indexed, composite)
  - ssn: String (encrypted, unique)
  - email: String[] (indexed, mixed)
  - phone: String[] (indexed, mixed)
  - riskScore: Integer (0-100, indexed)
  - riskLevel: String (low/medium/high/critical, indexed)
  - pepStatus: Boolean (indexed)
  - sanctioned: Boolean (indexed)
  - createdAt: Timestamp
  - updatedAt: Timestamp
```

#### Company Vertex
```groovy
label: 'company'
properties:
  - companyId: String (UUID, unique, indexed)
  - legalName: String (indexed, mixed)
  - taxId: String (encrypted, unique)
  - incorporationDate: Date
  - incorporationCountry: String (ISO 3166-1, indexed)
  - industry: String (NAICS, indexed)
  - companyType: String (LLC/Corp/etc, indexed)
  - revenue: Double
  - riskScore: Integer (0-100, indexed)
  - riskLevel: String (indexed)
  - sanctioned: Boolean (indexed)
```

#### Account Vertex
```groovy
label: 'account'
properties:
  - accountId: String (UUID, unique, indexed)
  - accountNumber: String (encrypted, unique)
  - accountType: String (checking/savings/etc, indexed)
  - currency: String (ISO 4217, indexed)
  - balance: Double (indexed)
  - openDate: Date (indexed)
  - status: String (active/closed/frozen, indexed)
  - riskScore: Integer (0-100, indexed)
  - riskLevel: String (indexed)
```

#### Transaction Vertex
```groovy
label: 'transaction'
properties:
  - transactionId: String (UUID, unique, indexed)
  - transactionType: String (indexed)
  - amount: Double (indexed)
  - currency: String (ISO 4217, indexed)
  - timestamp: Timestamp (indexed)
  - description: String (mixed index)
  - fraudScore: Integer (0-100, indexed)
  - fraudFlag: Boolean (indexed)
  - amlFlag: Boolean (indexed)
  - structuringFlag: Boolean (indexed)
```

### 2.1.2 Edge Types

#### OWNS Edge
```groovy
label: 'OWNS'
direction: Person/Company → Account
properties:
  - ownershipType: String (primary/joint/beneficiary)
  - ownershipPercentage: Double (0-100)
  - startDate: Date
  - endDate: Date (optional)
```

#### TRANSACTED Edge
```groovy
label: 'TRANSACTED'
direction: Account → Transaction → Account
properties:
  - direction: String (debit/credit)
  - amount: Double
  - timestamp: Timestamp
```

#### RELATED_TO Edge
```groovy
label: 'RELATED_TO'
direction: Person ↔ Person
properties:
  - relationshipType: String (family/business/associate)
  - strength: Integer (0-100)
  - startDate: Date
```

## 2.2 Indexing Strategy

### 2.2.1 Composite Indexes
- **personByPersonId**: Unique index on personId
- **personByName**: Composite on lastName + firstName
- **personByRisk**: Composite on riskLevel + riskScore
- **transactionByTimestamp**: Range queries on timestamp
- **accountByTypeStatus**: Composite on accountType + status

### 2.2.2 Mixed Indexes (Elasticsearch)
- **personSearch**: Full-text on firstName, lastName, email
- **companySearch**: Full-text on legalName, tradeName
- **transactionSearch**: Full-text on description

## 2.3 Cardinality Constraints
- **SINGLE**: Most properties (one value per vertex)
- **LIST**: email, phone (multiple values allowed)
- **SET**: tags, categories (unique values only)

---

# 3. API Specifications

## 3.1 Gremlin API

### 3.1.1 Connection Endpoint
```
WebSocket: ws://localhost:8182/gremlin
WebSocket+TLS: wss://localhost:8182/gremlin
```

### 3.1.2 Authentication
```python
headers = {
    'Authorization': f'Bearer {jwt_token}'
}
```

### 3.1.3 Common Query Patterns

#### Find Person by ID
```groovy
g.V().has('person', 'personId', personId)
```

#### Find High-Risk Accounts
```groovy
g.V().hasLabel('account')
  .has('riskLevel', 'high')
  .has('riskScore', gt(75))
```

#### Find Transaction Path
```groovy
g.V().has('account', 'accountId', sourceId)
  .repeat(outE('TRANSACTED').inV())
  .until(has('accountId', targetId))
  .path()
```

#### Customer 360 View
```groovy
g.V().has('person', 'personId', personId)
  .project('person', 'accounts', 'transactions', 'relationships')
  .by(valueMap())
  .by(out('OWNS').valueMap().fold())
  .by(out('OWNS').out('TRANSACTED').valueMap().fold())
  .by(both('RELATED_TO').valueMap().fold())
```

## 3.2 REST API

### 3.2.1 Management API
```
Base URL: http://localhost:8184
```

#### Health Check
```http
GET /health
Response: 200 OK
{
  "status": "healthy",
  "components": {
    "storage": "UP",
    "index": "UP"
  }
}
```

#### Metrics
```http
GET /metrics
Response: 200 OK
{
  "vertices": 1000000,
  "edges": 5000000,
  "queries_per_second": 150
}
```

## 3.3 Python Client API

### 3.3.1 Client Initialization
```python
from src.python.client.janusgraph_client import JanusGraphClient

client = JanusGraphClient(
    url='ws://localhost:8182/gremlin',
    username='admin',
    password=os.getenv('JANUSGRAPH_PASSWORD')
)
```

### 3.3.2 Query Execution
```python
# Simple query
result = client.execute("g.V().count()")

# Parameterized query
result = client.execute(
    "g.V().has('person', 'personId', personId)",
    bindings={'personId': '550e8400-e29b-41d4-a716-446655440000'}
)
```

## 3.4 Error Handling

### 3.4.1 Error Codes
| Code | Description | Action |
|------|-------------|--------|
| 401 | Unauthorized | Check authentication token |
| 404 | Not Found | Verify vertex/edge exists |
| 500 | Server Error | Check server logs |
| 503 | Service Unavailable | Wait and retry |

### 3.4.2 Error Response Format
```json
{
  "error": {
    "code": 500,
    "message": "Internal server error",
    "details": "Connection to storage backend failed",
    "timestamp": "2026-01-30T10:00:00Z"
  }
}
```

---

# 4. Container Isolation Specifications

## 4.1 Five Layers of Isolation

**MANDATORY**: See [`.bob/rules-plan/PODMAN_ISOLATION.md`](../.bob/rules-plan/PODMAN_ISOLATION.md) for complete requirements.

### 4.1.1 Network Isolation
- Each pod has isolated network namespace
- Unique subnet per project: `10.89.X.0/24`
- No cross-pod communication without explicit policy

### 4.1.2 Volume Isolation
- All volumes prefixed with project name
- No shared volumes between projects
- Independent backup/restore per project

### 4.1.3 Resource Limits
- Explicit CPU/memory limits per pod
- Prevents resource starvation
- Monitoring of resource usage

### 4.1.4 Port Mapping
- Check for conflicts before deployment
- Document all exposed ports
- Use non-standard ports when possible

### 4.1.5 Label-Based Management
- All resources labeled with `project=janusgraph-demo`
- Easy filtering and cleanup
- Prevents accidental deletion

## 4.2 Pod Specifications

### 4.2.1 Core Pod
```bash
podman pod create \
  --name janusgraph-demo-core \
  --network janusgraph-demo-network \
  --cpus 8 \
  --memory 16g \
  --label project=janusgraph-demo \
  --label component=core
```

### 4.2.2 Monitoring Pod
```bash
podman pod create \
  --name janusgraph-demo-monitoring \
  --network janusgraph-demo-network \
  --cpus 2 \
  --memory 4g \
  --label project=janusgraph-demo \
  --label component=monitoring
```

## 4.3 Security Context

### 4.3.1 Rootless Containers
- All containers run as non-root user
- User namespace mapping
- No privileged containers

### 4.3.2 Capabilities
- Drop all capabilities by default
- Add only required capabilities
- Example: `CAP_NET_BIND_SERVICE` for port 80/443

### 4.3.3 Read-Only Filesystem
- Root filesystem read-only where possible
- Writable volumes for data only
- Prevents container modification

---

# 5. Performance Specifications

## 5.1 Performance Targets

### 5.1.1 Throughput Requirements
- **Queries per second**: 1000 QPS (sustained)
- **Peak load**: 5000 QPS (burst)
- **Write throughput**: 500 writes/second
- **Batch operations**: 10,000 vertices/second

### 5.1.2 Latency Targets
- **Simple queries** (vertex lookup): < 10ms (p95)
- **Complex queries** (3-hop traversal): < 100ms (p95)
- **Aggregations**: < 500ms (p95)
- **Full-text search**: < 50ms (p95)

### 5.1.3 Concurrent Users
- **Supported users**: 100 concurrent
- **Peak users**: 500 concurrent (burst)
- **Connection pool**: 200 connections

## 5.2 Query Optimization

### 5.2.1 Index Usage
- Always use indexed properties in `has()` steps
- Composite indexes for multi-property filters
- Mixed indexes for full-text search

### 5.2.2 Query Patterns
```groovy
// GOOD: Uses index
g.V().has('person', 'personId', id)

// BAD: Full scan
g.V().hasLabel('person').has('firstName', 'John')

// BETTER: Use composite index
g.V().has('person', 'lastName', 'Doe').has('firstName', 'John')
```

### 5.2.3 Batch Operations
```python
# Use batch for bulk inserts
batch = []
for data in dataset:
    batch.append(create_vertex_query(data))
    if len(batch) >= 1000:
        client.execute_batch(batch)
        batch = []
```

## 5.3 Caching Strategy

### 5.3.1 Query Cache
- **Location**: `src/python/performance/query_cache.py`
- **TTL**: 5 minutes for read queries
- **Size**: 1000 entries (LRU eviction)
- **Hit rate target**: > 80%

### 5.3.2 Vertex Cache
- **JanusGraph cache**: 50% of heap (2GB)
- **Cache type**: Guava cache
- **Expiration**: 10 minutes idle time

## 5.4 Scalability Parameters

### 5.4.1 Horizontal Scaling
- **HCD nodes**: 3-node cluster (RF=3)
- **JanusGraph nodes**: 3-node cluster
- **Load balancer**: HAProxy or Nginx

### 5.4.2 Vertical Scaling
- **HCD**: Up to 32GB RAM, 8 CPUs per node
- **JanusGraph**: Up to 16GB RAM, 4 CPUs per node
- **Monitoring**: Up to 8GB RAM, 2 CPUs

---

# 6. Security Specifications

## 6.1 Authentication

### 6.1.1 JWT Authentication
- **Token lifetime**: 1 hour
- **Refresh token**: 7 days
- **Algorithm**: RS256 (RSA with SHA-256)
- **Key rotation**: Every 90 days

### 6.1.2 User Management
```python
# User creation
create_user(
    username='analyst',
    password=hash_password(password),
    roles=['read', 'query'],
    mfa_enabled=True
)
```

### 6.1.3 MFA Requirements
- **Mandatory for**: Admin, write access
- **Optional for**: Read-only users
- **Methods**: TOTP (Google Authenticator), SMS

## 6.2 Authorization

### 6.2.1 Role-Based Access Control (RBAC)
| Role | Permissions |
|------|-------------|
| admin | Full access (read, write, delete, admin) |
| analyst | Read, query, export |
| auditor | Read audit logs only |
| developer | Read, write (non-production) |

### 6.2.2 Resource-Level Permissions
```python
# Check permission before query
if not user.has_permission('read', 'person'):
    raise PermissionDenied("User cannot read person vertices")
```

## 6.3 Data Encryption

### 6.3.1 Encryption at Rest
- **Storage**: AES-256 encryption for all volumes
- **Sensitive fields**: Additional field-level encryption (SSN, account numbers)
- **Key management**: HashiCorp Vault

### 6.3.2 Encryption in Transit
- **TLS version**: TLS 1.3 (minimum TLS 1.2)
- **Cipher suites**: Strong ciphers only (no RC4, 3DES)
- **Certificate rotation**: Every 90 days

### 6.3.3 Key Management
```bash
# Vault secret storage
vault kv put janusgraph/encryption \
  master_key="$(openssl rand -base64 32)" \
  rotation_date="2026-01-30"
```

## 6.4 Network Security

### 6.4.1 Firewall Rules
```bash
# Allow only required ports
iptables -A INPUT -p tcp --dport 8182 -j ACCEPT  # JanusGraph
iptables -A INPUT -p tcp --dport 9042 -j ACCEPT  # HCD
iptables -A INPUT -j DROP  # Block all others
```

### 6.4.2 Network Policies
- No direct internet access from containers
- Egress filtering for external APIs
- Internal-only communication for management ports

## 6.5 Secret Management

### 6.5.1 HashiCorp Vault
- **Endpoint**: `https://localhost:8200`
- **Authentication**: AppRole for applications
- **Secret rotation**: Automatic every 90 days

### 6.5.2 Secret Types
- Database passwords
- API keys
- Encryption keys
- SSL/TLS certificates

## 6.6 Compliance Requirements

### 6.6.1 GDPR Compliance
- **Right to access**: Customer 360 view API
- **Right to erasure**: Vertex deletion with cascade
- **Data portability**: Export to JSON/CSV
- **Consent management**: Consent vertex type

### 6.6.2 SOC 2 Type II
- **Access controls**: RBAC with audit logging
- **Change management**: Git-tracked schema changes
- **Monitoring**: 24/7 security monitoring
- **Incident response**: Documented procedures

### 6.6.3 BSA/AML Compliance
- **SAR filing**: Automated alert generation
- **CTR reporting**: Transaction monitoring
- **Record retention**: 5-year minimum
- **Audit trail**: Immutable audit logs

---

# 7. Integration Specifications

## 7.1 watsonx.data Integration

### 7.1.1 Spark Connector
```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("JanusGraph-Watsonx") \
    .config("spark.jars", "janusgraph-spark-connector.jar") \
    .getOrCreate()

# Read from JanusGraph
df = spark.read \
    .format("org.janusgraph.spark") \
    .option("storage.backend", "cql") \
    .option("storage.hostname", "hcd-server") \
    .load()
```

### 7.1.2 Data Export
```python
# Export vertices to Parquet
g.V().hasLabel('person') \
    .valueMap() \
    .toList() \
    .to_parquet('s3://bucket/persons.parquet')
```

## 7.2 External System Integration

### 7.2.1 REST API Integration
```python
# Webhook for external alerts
@app.route('/webhook/alert', methods=['POST'])
def receive_alert():
    alert_data = request.json
    create_alert_vertex(alert_data)
    return {'status': 'received'}, 200
```

### 7.2.2 Message Queue Integration
```python
# Kafka consumer for real-time transactions
consumer = KafkaConsumer(
    'transactions',
    bootstrap_servers=['kafka:9092']
)

for message in consumer:
    transaction = json.loads(message.value)
    create_transaction_vertex(transaction)
```

## 7.3 Data Ingestion Pipelines

### 7.3.1 Batch Ingestion
```bash
# Daily batch load
python scripts/deployment/load_production_data.py \
  --source s3://bucket/daily_data.csv \
  --batch-size 10000 \
  --parallel 4
```

### 7.3.2 Streaming Ingestion
```python
# Real-time stream processing
stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "transactions") \
    .load()

stream.writeStream \
    .foreachBatch(process_batch) \
    .start()
```

---

# 8. Monitoring and Observability Specifications

## 8.1 Metrics Collection

### 8.1.1 JanusGraph Metrics
```python
# Custom exporter: scripts/monitoring/janusgraph_exporter.py
janusgraph_vertices_total = Gauge('janusgraph_vertices_total', 'Total vertices')
janusgraph_edges_total = Gauge('janusgraph_edges_total', 'Total edges')
janusgraph_query_duration_seconds = Histogram('janusgraph_query_duration_seconds', 'Query latency')
janusgraph_errors_total = Counter('janusgraph_errors_total', 'Total errors', ['error_type'])
```

### 8.1.2 HCD Metrics
- **JMX metrics**: Via SSH tunnel to port 7199
- **Nodetool metrics**: `nodetool status`, `nodetool tpstats`
- **CQL metrics**: Query latency, throughput

### 8.1.3 System Metrics
- CPU usage per container
- Memory usage per container
- Disk I/O per volume
- Network traffic per pod

## 8.2 Logging Standards

### 8.2.1 Log Format
```json
{
  "timestamp": "2026-01-30T10:00:00Z",
  "level": "INFO",
  "service": "janusgraph",
  "message": "Query executed successfully",
  "query": "g.V().count()",
  "duration_ms": 15,
  "user": "analyst@example.com"
}
```

### 8.2.2 Log Levels
- **ERROR**: System errors, exceptions
- **WARN**: Degraded performance, retries
- **INFO**: Normal operations, queries
- **DEBUG**: Detailed debugging (non-production)

### 8.2.3 Log Retention
- **ERROR logs**: 90 days
- **WARN logs**: 30 days
- **INFO logs**: 7 days
- **DEBUG logs**: 1 day (non-production only)

## 8.3 Tracing Requirements

### 8.3.1 Distributed Tracing
- **Tool**: OpenTelemetry
- **Backend**: Jaeger
- **Sampling**: 10% of requests (100% for errors)

### 8.3.2 Trace Context
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("query_execution"):
    result = client.execute(query)
```

## 8.4 Alerting Thresholds

### 8.4.1 Critical Alerts
- **ServiceDown**: Any service unavailable > 1 minute
- **HighErrorRate**: Error rate > 5% for 5 minutes
- **DiskSpaceLow**: < 10% free space
- **CertificateExpiring**: < 7 days until expiration

### 8.4.2 Warning Alerts
- **HighCPUUsage**: > 80% for 10 minutes
- **HighMemoryUsage**: > 85% for 10 minutes
- **HighQueryLatency**: p95 > 200ms for 5 minutes
- **BackupFailed**: Backup job failed

## 8.5 Dashboard Configurations

### 8.5.1 Grafana Dashboards
- **System Overview**: CPU, memory, disk, network
- **JanusGraph Performance**: QPS, latency, errors
- **Security Monitoring**: Failed auth, suspicious activity
- **Compliance Dashboard**: Audit events, alerts

### 8.5.2 Dashboard Location
`config/grafana/dashboards/security-monitoring.json`

---

# 9. Deployment Specifications

## 9.1 Environment Configurations

### 9.1.1 Development Environment
```yaml
environment: development
resources:
  hcd: 2GB RAM, 1 CPU
  janusgraph: 2GB RAM, 1 CPU
  monitoring: 1GB RAM, 0.5 CPU
ssl_enabled: false
authentication: basic
```

### 9.1.2 Staging Environment
```yaml
environment: staging
resources:
  hcd: 4GB RAM, 2 CPUs
  janusgraph: 4GB RAM, 2 CPUs
  monitoring: 2GB RAM, 1 CPU
ssl_enabled: true
authentication: jwt
```

### 9.1.3 Production Environment
```yaml
environment: production
resources:
  hcd: 8GB RAM, 4 CPUs (3 nodes)
  janusgraph: 8GB RAM, 4 CPUs (3 nodes)
  monitoring: 4GB RAM, 2 CPUs
ssl_enabled: true
authentication: jwt + mfa
high_availability: true
backup_enabled: true
```

## 9.2 CI/CD Pipeline

### 9.2.1 Build Stage
```yaml
build:
  - name: Build HCD image
    command: podman build -t localhost/hcd:1.2.3 -f docker/hcd/Dockerfile .
  - name: Run unit tests
    command: pytest tests/unit/ -v
  - name: Run linters
    command: black --check . && isort --check . && mypy .
```

### 9.2.2 Test Stage
```yaml
test:
  - name: Deploy test environment
    command: bash scripts/deployment/deploy_full_stack.sh
  - name: Run integration tests
    command: pytest tests/integration/ -v
  - name: Run performance tests
    command: pytest tests/performance/ -v --benchmark-only
```

### 9.2.3 Deploy Stage
```yaml
deploy:
  - name: Tag images
    command: podman tag localhost/hcd:1.2.3 registry.example.com/hcd:1.2.3
  - name: Push images
    command: podman push registry.example.com/hcd:1.2.3
  - name: Deploy to production
    command: bash scripts/deployment/deploy_production.sh
```

## 9.3 Rollback Procedures

### 9.3.1 Automated Rollback
```bash
# If health checks fail after deployment
if ! check_health; then
    echo "Health check failed, rolling back..."
    podman-compose -p janusgraph-demo down
    podman-compose -p janusgraph-demo -f docker-compose.previous.yml up -d
fi
```

### 9.3.2 Manual Rollback
```bash
# Stop current deployment
podman-compose -p janusgraph-demo down

# Restore previous volumes
bash scripts/backup/restore_volumes.sh --date 2026-01-29

# Start previous version
podman-compose -p janusgraph-demo -f docker-compose.v1.0.0.yml up -d
```

## 9.4 Disaster Recovery

### 9.4.1 Backup Strategy
- **Frequency**: Hourly incremental, daily full
- **Retention**: 7 days hourly, 30 days daily, 90 days weekly
- **Location**: Encrypted S3-compatible storage
- **Verification**: Weekly restore test

### 9.4.2 Recovery Procedures
```bash
# 1. Stop services
podman-compose -p janusgraph-demo down

# 2. Restore volumes
bash scripts/backup/restore_volumes.sh --date 2026-01-29

# 3. Start services
podman-compose -p janusgraph-demo up -d

# 4. Verify data integrity
python scripts/hcd/validate_deployment.py
```

### 9.4.3 RTO/RPO Targets
- **Recovery Time Objective (RTO)**: 4 hours
- **Recovery Point Objective (RPO)**: 1 hour
- **Data Loss Tolerance**: < 1 hour of transactions

---

# 10. Testing Specifications

## 10.1 Unit Test Coverage

### 10.1.1 Coverage Requirements
- **Overall coverage**: > 80%
- **Critical modules**: > 90%
- **New code**: 100% coverage required

### 10.1.2 Test Organization
```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_generators/    # Data generator tests
│   ├── test_client/        # Client library tests
│   └── test_utils/         # Utility function tests
├── integration/            # Integration tests (require services)
│   ├── test_janusgraph/   # JanusGraph integration
│   ├── test_hcd/          # HCD integration
│   └── test_end_to_end/   # Full workflow tests
└── performance/            # Performance tests
    ├── test_benchmarks/   # Benchmark tests
    └── test_load/         # Load tests
```

## 10.2 Integration Test Scenarios

### 10.2.1 Data Generator Integration
```python
def test_person_generator_integration():
    """Test person generator creates valid vertices"""
    generator = PersonGenerator(seed=42)
    person = generator.generate()
    
    # Create vertex in JanusGraph
    vertex_id = client.create_vertex('person', person)
    
    # Verify vertex exists
    result = client.get_vertex(vertex_id)
    assert result['firstName'] == person['firstName']
```

### 10.2.2 AML Detection Integration
```python
def test_structuring_detection():
    """Test AML structuring pattern detection"""
    # Load test data
    load_structuring_pattern_data()
    
    # Run detection query
    results = detect_structuring_patterns()
    
    # Verify alerts generated
    assert len(results) > 0
    assert results[0]['pattern'] == 'structuring'
```

## 10.3 Performance Test Benchmarks

### 10.3.1 Query Performance
```python
@pytest.mark.benchmark
def test_vertex_lookup_performance(benchmark):
    """Benchmark vertex lookup by ID"""
    result = benchmark(
        client.get_vertex,
        vertex_id='550e8400-e29b-41d4-a716-446655440000'
    )
    
    # Assert p95 latency < 10ms
    assert benchmark.stats['mean'] < 0.010
```

### 10.3.2 Throughput Testing
```python
def test_write_throughput():
    """Test write throughput (vertices/second)"""
    start_time = time.time()
    vertices_created = 0
    
    for i in range(10000):
        client.create_vertex('person', generate_person())
        vertices_created += 1
    
    duration = time.time() - start_time
    throughput = vertices_created / duration
    
    # Assert > 500 vertices/second
    assert throughput > 500
```

## 10.4 Acceptance Criteria

### 10.4.1 Functional Acceptance
- [ ] All vertex types can be created
- [ ] All edge types can be created
- [ ] Indexes are used correctly
- [ ] Queries return expected results
- [ ] Authentication works
- [ ] Authorization enforced

### 10.4.2 Performance Acceptance
- [ ] Query latency < 100ms (p95)
- [ ] Throughput > 1000 QPS
- [ ] Write throughput > 500/sec
- [ ] Cache hit rate > 80%

### 10.4.3 Security Acceptance
- [ ] SSL/TLS enabled
- [ ] Authentication required
- [ ] Authorization enforced
- [ ] Audit logging working
- [ ] Secrets encrypted
- [ ] No default passwords

### 10.4.4 Operational Acceptance
- [ ] Monitoring dashboards working
- [ ] Alerts configured
- [ ] Backups running
- [ ] Logs collected
- [ ] Health checks passing
- [ ] Documentation complete

---

# Appendices

## Appendix A: Configuration Files

### A.1 Docker Compose
- **Location**: `config/compose/docker-compose.yml`
- **Purpose**: Container orchestration
- **Key settings**: Network, volumes, resource limits

### A.2 JanusGraph Configuration
- **Location**: `config/janusgraph/janusgraph-hcd-tls.properties`
- **Purpose**: JanusGraph server configuration
- **Key settings**: Storage backend, index backend, cache

### A.3 Prometheus Configuration
- **Location**: `config/monitoring/prometheus.yml`
- **Purpose**: Metrics collection
- **Key settings**: Scrape targets, retention

## Appendix B: Troubleshooting Guide

### B.1 Common Issues

#### Issue: Container fails to start
```bash
# Check logs
podman logs janusgraph-demo-hcd-server

# Check resource limits
podman stats janusgraph-demo-core

# Verify network
podman network inspect janusgraph-demo-network
```

#### Issue: Query timeout
```bash
# Check JanusGraph logs
podman logs janusgraph-demo-janusgraph-server

# Check HCD status
podman exec janusgraph-demo-hcd-server nodetool status

# Verify indexes
g.getManagement().printIndexes()
```

## Appendix C: Reference Architecture

### C.1 Audit Findings
- See: [`docs/implementation/audits/COMPREHENSIVE_PROJECT_AUDIT_2026-01-30.md`](implementation/audits/COMPREHENSIVE_PROJECT_AUDIT_2026-01-30.md)
- Critical issues identified: 14
- Production readiness: C+ (65/100)

### C.2 Isolation Rules
- See: [`.bob/rules-plan/PODMAN_ISOLATION.md`](../.bob/rules-plan/PODMAN_ISOLATION.md)
- Five layers of isolation
- Mandatory for all deployments

### C.3 Development Guidelines
- See: [`AGENTS.md`](../AGENTS.md)
- Python environment setup
- Testing requirements
- Code style standards

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-30 | IBM Bob | Initial comprehensive outline/template |

---

**END OF DOCUMENT**
