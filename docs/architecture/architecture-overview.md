# Architecture Overview

## Document Information

- **Document Version:** 1.0.0
- **Last Updated:** 2026-02-19
- **Owner:** Architecture Team
- **Status:** Active - Single-Page Architecture Summary
- **Audience:** All stakeholders (executives, architects, developers, operators)

---

## Executive Summary

The **HCD JanusGraph Banking Compliance Platform** is a graph-based analytics system designed for banking compliance, fraud detection, and anti-money laundering (AML) analysis. It combines **Apache Cassandra (HCD)**, **JanusGraph**, **OpenSearch**, and **Apache Pulsar** to provide real-time graph analytics with deterministic deployment and comprehensive monitoring.

**Key Characteristics:**
- **Deterministic Deployment:** 95% reproducibility with gate-based validation (G0-G9)
- **Event-Driven Architecture:** Pulsar-based streaming with graph and vector consumers
- **Comprehensive Monitoring:** Prometheus, Grafana, AlertManager with 31 alert rules
- **Enterprise Security:** Vault secrets management, SSL/TLS, audit logging
- **Banking Compliance:** GDPR, SOC 2, BSA/AML, PCI DSS ready

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT APPLICATIONS                          │
│  Jupyter Lab │ GraphExp │ Visualizer │ OpenSearch Dashboards    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                     APPLICATION LAYER                            │
│  Analytics API │ Graph Consumer │ Vector Consumer               │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                     CORE SERVICES LAYER                          │
│  JanusGraph Server │ Apache Pulsar │ OpenSearch                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                     FOUNDATION LAYER                             │
│  HCD (Cassandra) │ HashiCorp Vault │ Podman Runtime            │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                     MONITORING & SECURITY                        │
│  Prometheus │ Grafana │ AlertManager │ JanusGraph Exporter      │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Layers

| Layer | Components | Purpose | Key Technologies |
|-------|-----------|---------|------------------|
| **Foundation** | HCD, Vault, Podman | Infrastructure and secrets | Cassandra, Vault, Podman |
| **Core Services** | JanusGraph, Pulsar, OpenSearch | Graph, streaming, search | JanusGraph, Pulsar, OpenSearch |
| **Application** | Analytics API, Consumers | Business logic and integration | FastAPI, Python |
| **Client** | Jupyter, Visualizers, Dashboards | User interfaces | Jupyter, React, Angular |
| **Monitoring** | Prometheus, Grafana, AlertManager | Observability | Prometheus, Grafana |

---

## Key Components

### 1. Graph Database (JanusGraph + HCD)

**Purpose:** Store and query graph data for banking relationships

**Components:**
- **JanusGraph Server:** Graph database engine (Gremlin queries)
- **HCD (Cassandra):** Distributed storage backend
- **OpenSearch:** Full-text search and indexing

**Key Features:**
- ACID transactions
- Distributed storage
- Gremlin query language
- Full-text search integration

**Ports:**
- JanusGraph: 18182 (Gremlin WebSocket)
- HCD: 19042 (CQL), 17199 (JMX)
- OpenSearch: 9200 (REST API)

### 2. Event Streaming (Apache Pulsar)

**Purpose:** Event-driven architecture for real-time data ingestion

**Components:**
- **Pulsar Broker:** Message broker
- **Graph Consumer:** Writes events to JanusGraph
- **Vector Consumer:** Writes events to OpenSearch

**Key Features:**
- Multi-tenancy
- Geo-replication
- Message deduplication
- Dead letter queue (DLQ)

**Topics:**
- `persons-events`
- `accounts-events`
- `transactions-events`
- `companies-events`
- `communications-events`
- `dlq-events`

**Ports:**
- Pulsar: 6650 (Binary), 8081 (HTTP Admin)

### 3. Analytics API (FastAPI)

**Purpose:** RESTful API for graph analytics and queries

**Key Features:**
- JWT authentication
- Rate limiting (SlowAPI)
- OpenTelemetry tracing
- Comprehensive error handling

**Endpoints:**
- `/health` - Health check
- `/api/v1/persons` - Person queries
- `/api/v1/accounts` - Account queries
- `/api/v1/transactions` - Transaction queries
- `/api/v1/ubo` - Ultimate Beneficial Owner discovery
- `/api/v1/aml` - AML detection

**Port:** 8001

### 4. Secrets Management (HashiCorp Vault)

**Purpose:** Centralized secrets management

**Key Features:**
- KV v2 secrets engine
- Dynamic secrets
- Audit logging
- Policy-based access control

**Secrets Stored:**
- Database credentials
- API keys
- JWT secrets
- SSL/TLS certificates

**Port:** 8200

### 5. Monitoring Stack

**Purpose:** Observability and alerting

**Components:**
- **Prometheus:** Metrics collection and storage
- **Grafana:** Visualization and dashboards
- **AlertManager:** Alert routing and notification
- **JanusGraph Exporter:** Custom metrics exporter

**Key Metrics:**
- Query latency (P50, P95, P99)
- Error rates
- Throughput (queries/sec)
- Resource utilization (CPU, memory, disk)

**Ports:**
- Prometheus: 9090
- Grafana: 3001
- AlertManager: 9093
- JanusGraph Exporter: 8000

---

## Deployment Architecture

### Deterministic Deployment

**Canonical Command:**

```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

**Gate-Based Validation (G0-G9):**

| Gate | Name | Purpose | Failure Code |
|------|------|---------|--------------|
| **G0** | Preflight | Environment validation | `G0_PRECHECK` |
| **G2** | Connection | Podman connectivity | `G2_CONNECTION` |
| **G3** | Reset | State reset | `G3_RESET` |
| **G5** | Deploy/Vault | Service deployment | `G5_DEPLOY_VAULT` |
| **G6** | Runtime Contract | Runtime validation | `G6_RUNTIME_CONTRACT` |
| **G7** | Seed | Graph seeding | `G7_SEED` |
| **G8** | Notebooks | Notebook execution | `G8_NOTEBOOKS` |
| **G9** | Determinism | Artifact verification | `G9_DETERMINISM` |

**Deployment Time:** 5-10 minutes (typical)

### Container Orchestration

**Technology:** Podman + Podman Compose

**Why Podman:**
- Rootless containers (better security)
- Daemonless architecture (no single point of failure)
- Pod support (Kubernetes-compatible)
- Docker CLI compatible

**Project Isolation:**

```bash
export COMPOSE_PROJECT_NAME="janusgraph-demo"
```

All resources prefixed with project name:
- Containers: `janusgraph-demo_service_1`
- Networks: `janusgraph-demo_hcd-janusgraph-network`
- Volumes: `janusgraph-demo_hcd-data`

### Service Startup Sequence

**5 Phases (90-270 seconds total):**

1. **Foundation (0-60s):** Vault, HCD, OpenSearch
2. **Core Services (60-120s):** JanusGraph, Pulsar, Dashboards
3. **Applications (120-180s):** Analytics API, Jupyter, Consumers
4. **Monitoring (180-240s):** Prometheus, Grafana, Exporters
5. **Visualization (240-270s):** Visualizer, GraphExp

**Critical Path:** Vault (10s) → HCD (180s) → JanusGraph (90s) → Analytics API (15s) = 295s

---

## Data Architecture

### Graph Schema

**Vertex Types:**
- `Person` - Individual customers
- `Company` - Corporate entities
- `Account` - Bank accounts
- `Transaction` - Financial transactions
- `Communication` - Customer communications

**Edge Types:**
- `OWNS` - Person/Company owns Account
- `TRANSACTS_WITH` - Account to Account transactions
- `COMMUNICATES_WITH` - Person to Person communications
- `EMPLOYED_BY` - Person employed by Company
- `CONTROLS` - Ultimate beneficial ownership

### Data Flow

```
Data Generators
    ↓
Pulsar Topics
    ↓
┌───────────────┬───────────────┐
│               │               │
Graph Consumer  Vector Consumer │
    ↓               ↓           │
JanusGraph      OpenSearch      │
    ↓               ↓           │
Analytics API   Dashboards      │
    ↓               ↓           │
Jupyter Lab     Visualizers     │
```

### Data Generation

**Deterministic Generation:**
- Seed-based (default: 42)
- Reference timestamp (2026-01-15T12:00:00Z)
- Seeded UUID generation (SHA-256 based)

**Synthetic Data:**
- Persons: 100-10,000
- Companies: 10-1,000
- Accounts: 200-20,000
- Transactions: 1,000-100,000
- Communications: 200-20,000

---

## Security Architecture

### Defense in Depth

**Layer 1: Network Security**
- Isolated Podman network
- Port mapping (internal → external)
- No direct external access to databases

**Layer 2: Authentication & Authorization**
- JWT-based API authentication
- Vault-managed secrets
- Policy-based access control

**Layer 3: Encryption**
- SSL/TLS for all external connections
- Encrypted backups (GPG)
- Vault transit encryption

**Layer 4: Audit & Compliance**
- Comprehensive audit logging (30+ event types)
- Compliance reporting (GDPR, SOC 2, BSA/AML, PCI DSS)
- Immutable audit trail

**Layer 5: Startup Validation**
- Rejects default passwords
- Validates required secrets
- Enforces security policies

### Secrets Management

**Vault Hierarchy:**

```
janusgraph/
├── admin          # Admin credentials
├── api            # API keys and JWT secrets
├── monitoring     # Monitoring credentials
└── ssl            # SSL/TLS certificates
```

**Access Control:**
- Admin policy: Full access
- API policy: Read-only application secrets
- Monitoring policy: Read-only monitoring secrets

---

## Monitoring & Observability

### Metrics Collection

**Sources:**
- JanusGraph Exporter (custom metrics)
- Prometheus Node Exporter (system metrics)
- Podman metrics (container metrics)
- Application metrics (FastAPI, Pulsar)

**Key Metrics:**
- `janusgraph_vertices_total` - Total vertex count
- `janusgraph_edges_total` - Total edge count
- `janusgraph_query_duration_seconds` - Query latency histogram
- `janusgraph_errors_total` - Errors by type
- `janusgraph_connection_status` - Connection health

### Alert Rules (31 Total)

**Categories:**
- System Health (8 rules): ServiceDown, HighCPUUsage, DiskSpaceLow
- JanusGraph (4 rules): HighQueryLatency, HighErrorRate
- Security (8 rules): HighFailedAuthRate, CertificateExpiring
- Performance (3 rules): HighResponseTime, High5xxErrorRate
- Cassandra (3 rules): CassandraNodeDown, HighLatency
- Compliance (2 rules): ComplianceScoreLow, AuditLogGap
- Backup (3 rules): BackupFailed, BackupStale

### Dashboards

**Grafana Dashboards:**
- System Overview
- JanusGraph Performance
- Cassandra Metrics
- API Performance
- Security Monitoring
- Compliance Dashboard

---

## Key Architectural Decisions

### ADR-013: Podman Over Docker

**Decision:** Use Podman instead of Docker for container orchestration

**Rationale:**
- Rootless containers (better security)
- Daemonless architecture (no single point of failure)
- Pod support (Kubernetes-compatible)
- Better resource isolation

**Status:** Accepted

### ADR-014: Project-Name Isolation

**Decision:** Use `COMPOSE_PROJECT_NAME` for resource isolation

**Rationale:**
- Prevents conflicts with other projects
- Enables multiple projects on same machine
- Clear resource ownership
- Easy cleanup per project

**Status:** Accepted

### ADR-015: Deterministic Deployment

**Decision:** Implement controlled determinism for deployments

**Rationale:**
- Reproducible deployments
- Easier debugging
- Consistent testing
- Artifact verification

**Status:** Accepted

### ADR-016: Gate-Based Validation

**Decision:** Use gate-based validation framework (G0-G9)

**Rationale:**
- Systematic validation
- Clear failure points
- Easier troubleshooting
- Consistent deployment process

**Status:** Accepted

---

## Performance Characteristics

### Expected Performance

| Metric | Target | Typical | Notes |
|--------|--------|---------|-------|
| **Query Latency (P95)** | < 100ms | 50-80ms | Simple traversals |
| **Query Latency (P99)** | < 500ms | 200-400ms | Complex traversals |
| **Throughput** | > 100 qps | 150-200 qps | Concurrent queries |
| **Startup Time** | < 10 min | 5-7 min | Full stack deployment |
| **Error Rate** | < 1% | 0.1-0.5% | Under normal load |

### Resource Requirements

**Minimum (Development):**
- CPU: 4 cores
- Memory: 8 GB
- Disk: 50 GB

**Recommended (Production):**
- CPU: 8 cores
- Memory: 16 GB
- Disk: 100 GB

**Scaling:**
- Horizontal: Add JanusGraph/Cassandra nodes
- Vertical: Increase Podman machine resources

---

## Compliance & Regulatory

### Supported Regulations

**GDPR (General Data Protection Regulation):**
- Right to access (Article 15)
- Right to erasure (Article 17)
- Right to data portability (Article 20)
- Records of processing activities (Article 30)

**SOC 2 Type II:**
- Access control reports
- Audit logging
- Change management
- Incident response

**BSA/AML (Bank Secrecy Act / Anti-Money Laundering):**
- Suspicious Activity Reports (SAR)
- Currency Transaction Reports (CTR)
- Customer Due Diligence (CDD)
- Enhanced Due Diligence (EDD)

**PCI DSS (Payment Card Industry Data Security Standard):**
- Audit reports
- Access control
- Encryption
- Monitoring

### Compliance Features

**Audit Logging:**
- 30+ event types
- Immutable audit trail
- Structured logging (JSON)
- Retention policies

**Compliance Reporting:**
- Automated report generation
- GDPR Article 30 reports
- SOC 2 access control reports
- BSA/AML SAR reports
- PCI DSS audit reports

---

## Quick Reference

### Essential Commands

```bash
# Deploy full stack (deterministic)
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json

# Deploy full stack (manual)
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh

# Stop full stack
cd config/compose && bash ../../scripts/deployment/stop_full_stack.sh

# Health check
bash scripts/operations/check_all_health.sh

# Check graph
bash scripts/testing/check_graph_counts.sh

# View logs
podman logs janusgraph-demo_service_1 --tail 100

# Check status
podman ps --filter "label=io.podman.compose.project=janusgraph-demo"
```

### Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Jupyter Lab** | http://localhost:8888 | Token in logs |
| **GraphExp** | http://localhost:8080 | None |
| **Visualizer** | http://localhost:3000 | None |
| **OpenSearch Dashboards** | http://localhost:5601 | None (dev mode) |
| **Prometheus** | http://localhost:9090 | None |
| **Grafana** | http://localhost:3001 | admin/admin |
| **AlertManager** | http://localhost:9093 | None |
| **Analytics API** | http://localhost:8001 | JWT required |
| **Vault** | http://localhost:8200 | Token in .vault-keys |

### Port Reference

| Service | Internal | External | Protocol |
|---------|----------|----------|----------|
| **HCD** | 9042 | 19042 | CQL |
| **JanusGraph** | 8182 | 18182 | WebSocket |
| **OpenSearch** | 9200 | 9200 | HTTP |
| **Pulsar** | 6650 | 6650 | Binary |
| **Analytics API** | 8001 | 8001 | HTTP |
| **Vault** | 8200 | 8200 | HTTP |
| **Prometheus** | 9090 | 9090 | HTTP |
| **Grafana** | 3000 | 3001 | HTTP |

---

## Documentation Map

### For Architects

**Core Architecture:**
- [System Architecture](system-architecture.md) - Detailed system design
- [Deployment Architecture](deployment-architecture.md) - Deployment model
- [Deterministic Deployment Architecture](deterministic-deployment-architecture.md) - Deterministic deployment
- [Service Startup Sequence](service-startup-sequence.md) - Service dependencies

**Architecture Decisions:**
- [ADR-013: Podman Over Docker](adr-013-podman-over-docker.md)
- [ADR-014: Project-Name Isolation](adr-014-project-name-isolation.md)
- [ADR-015: Deterministic Deployment](adr-015-deterministic-deployment.md)
- [ADR-016: Gate-Based Validation](adr-016-gate-based-validation.md)

### For Operators

**Operations:**
- [Operations Runbook](../operations/operations-runbook.md) - Daily operations
- [Troubleshooting Architecture](troubleshooting-architecture.md) - Systematic troubleshooting
- [Podman Isolation Architecture](podman-isolation-architecture.md) - Container isolation

**Guides:**
- [Deployment Guide](../guides/deployment-guide.md)
- [Troubleshooting Guide](../guides/troubleshooting-guide.md)

### For Developers

**Development:**
- [QUICKSTART.md](../../QUICKSTART.md) - Quick start guide
- [README.md](../../README.md) - Project overview
- [AGENTS.md](../../.bob/rules-code/AGENTS.md) - Agent operational rules

**API Documentation:**
- [REST API](../api/rest-api.md)
- [Gremlin API](../api/gremlin-api.md)
- [Python Client](../api/python-client.md)

### For Compliance

**Compliance:**
- [AML Detection](../banking/aml-detection.md)
- [Fraud Detection](../banking/fraud-detection.md)
- [User Guide](../banking/guides/user-guide.md)

---

## Getting Started

### New Team Member Onboarding

**Day 1: Setup**
1. Read this overview
2. Install prerequisites (uv, podman, conda)
3. Clone repository
4. Run preflight check

**Day 2: Deploy**
1. Deploy full stack
2. Explore Jupyter notebooks
3. Try GraphExp visualizer
4. Review monitoring dashboards

**Day 3: Learn**
1. Read architecture documentation
2. Review ADRs
3. Understand gate-based validation
4. Practice troubleshooting

**Week 1: Contribute**
1. Make first code change
2. Run deterministic deployment
3. Review operations runbook
4. Join on-call rotation

### Quick Start

```bash
# 1. Install prerequisites
curl -LsSf https://astral.sh/uv/install.sh | sh
brew install podman podman-compose

# 2. Initialize Podman machine
podman machine init --cpus 4 --memory 8192 --disk-size 50
podman machine start

# 3. Clone repository
git clone <repository-url>
cd hcd-tarball-janusgraph

# 4. Setup environment
conda env create -f environment.yml
conda activate janusgraph-analysis
uv pip install -r requirements.txt

# 5. Deploy
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json

# 6. Access services
open http://localhost:8888  # Jupyter Lab
open http://localhost:8080  # GraphExp
open http://localhost:3001  # Grafana
```

---

## Support & Contact

### Documentation

- **Architecture:** `docs/architecture/`
- **Operations:** `docs/operations/`
- **API:** `docs/api/`
- **Guides:** `docs/guides/`

### Contacts

- **Architecture Team:** architecture@example.com
- **Operations Team:** ops-team@example.com
- **On-Call:** ops-oncall@example.com (24/7)
- **Security Team:** security@example.com

### Issue Tracking

- **GitHub Issues:** <repository-url>/issues
- **Incident Reports:** ops-oncall@example.com
- **Security Issues:** security@example.com

---

**Document Classification:** Internal - Architecture  
**Next Review Date:** 2026-05-19  
**Document Owner:** Architecture Team  
**Version:** 1.0.0

---

## Change Log

### Version 1.0.0 (2026-02-19)
- Initial version
- Complete architecture overview
- Single-page summary for all stakeholders
- Quick reference and getting started guide
- Documentation map for all audiences