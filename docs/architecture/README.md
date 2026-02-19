# Architecture Documentation

This directory contains architecture documentation including Architecture Decision Records (ADRs), system architecture, and deployment architecture for the HCD + JanusGraph Banking Compliance Platform.

---

## Core Architecture Documents

| Document | Description | Audience |
|----------|-------------|----------|
| **[Architecture Overview](architecture-overview.md)** | Single-page architecture summary for all stakeholders | All |
| **[System Architecture](system-architecture.md)** | Logical component architecture and data flow | Architects, Developers |
| **[Deployment Architecture](deployment-architecture.md)** | Container orchestration, networking, deployment topology | Operators, Architects |
| **[Operational Architecture](operational-architecture.md)** | Runtime topology, service communication, monitoring, incident response | Operators, SRE |
| **[Podman Isolation Architecture](podman-isolation-architecture.md)** | Five-layer isolation model and project boundaries | Operators, DevOps |
| **[Deterministic Deployment Architecture](deterministic-deployment-architecture.md)** | Gate-based validation system (G0-G9) for reproducible deployments | Operators, QA |
| **[Non-Determinism Analysis](non-determinism-analysis.md)** | Sources of variance and mitigation strategies | Architects, Developers |
| **[Service Startup Sequence](service-startup-sequence.md)** | Service dependencies and startup timing | Operators, SRE |
| **[Troubleshooting Architecture](troubleshooting-architecture.md)** | Systematic troubleshooting framework and procedures | Operators, Support |
| **[Streaming Architecture](streaming-architecture.md)** | Pulsar-based event streaming architecture | Architects, Developers |
| **[Data Flow Unified](data-flow-unified.md)** | Complete data flow with diagrams | Architects, Developers |

---

## Infrastructure Architecture Documents

| Document | Description | Audience |
|----------|-------------|----------|
| **[Terraform Multi-Cloud Architecture](terraform-multi-cloud-architecture.md)** | Multi-cloud IaC with 15 modules across 5 platforms (AWS, Azure, GCP, vSphere, Bare Metal) | Architects, DevOps, Platform Engineers |
| **[Kubernetes & Helm Architecture](kubernetes-helm-architecture.md)** | Helm charts, ArgoCD GitOps, multi-environment deployment strategy | Architects, DevOps, Kubernetes Admins |
| **[OpenShift Deployment Manifests](openshift-deployment-manifests.md)** | OpenShift-specific deployment configurations and routes | OpenShift Admins, DevOps |
| **[Horizontal Scaling Strategy](horizontal-scaling-strategy.md)** | Multi-cloud scaling procedures with HPA/VPA examples | Operators, SRE, Architects |

---

## Architecture Decision Records (ADRs)

This section contains Architecture Decision Records (ADRs) documenting significant architectural decisions made during the project development and remediation.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## ADR Format

Each ADR follows this structure:

- **Title**: Short noun phrase
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Context**: Forces at play (technical, political, social, project)
- **Decision**: Response to these forces
- **Consequences**: Context after applying the decision

## Index of ADRs

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-001](adr-001-janusgraph-as-graph-database.md) | Use JanusGraph as Graph Database | Accepted | 2026-01-15 |
| [ADR-002](adr-002-hcd-as-storage-backend.md) | Use HCD (Cassandra) as Storage Backend | Accepted | 2026-01-15 |
| [ADR-003](adr-003-docker-compose-deployment.md) | Compose for Development Deployment | Accepted | 2026-01-16 |
| [ADR-004](adr-004-python-client-library.md) | Python as Primary Client Language | Accepted | 2026-01-16 |
| [ADR-005](adr-005-jwt-authentication.md) | JWT-Based Authentication | Accepted | 2026-01-20 |
| [ADR-006](adr-006-rbac-authorization.md) | Role-Based Access Control (RBAC) | Accepted | 2026-01-20 |
| [ADR-007](adr-007-mfa-implementation.md) | TOTP-Based Multi-Factor Authentication | Accepted | 2026-01-21 |
| [ADR-008](adr-008-tls-encryption.md) | TLS/SSL Encryption for All Communications | Accepted | 2026-01-22 |
| [ADR-009](adr-009-prometheus-monitoring.md) | Prometheus and Grafana for Monitoring | Accepted | 2026-01-23 |
| [ADR-010](adr-010-distributed-tracing.md) | OpenTelemetry and Jaeger for Distributed Tracing | Accepted | 2026-01-24 |
| [ADR-011](adr-011-query-caching-strategy.md) | LRU-Based Query Caching | Accepted | 2026-01-25 |
| [ADR-012](adr-012-github-actions-cicd.md) | GitHub Actions for CI/CD Pipeline | Accepted | 2026-01-26 |
| [ADR-013](adr-013-podman-over-docker.md) | Podman Over Docker for Container Runtime | Accepted | 2026-02-19 |
| [ADR-014](adr-014-project-name-isolation.md) | Project-Name Isolation for Multi-Project Environments | Accepted | 2026-02-19 |
| [ADR-015](adr-015-deterministic-deployment.md) | Deterministic Deployment Strategy | Accepted | 2026-02-19 |
| [ADR-016](adr-016-gate-based-validation.md) | Gate-Based Validation Framework | Accepted | 2026-02-19 |

## Creating New ADRs

When creating a new ADR:

1. Copy the [ADR template](adr-template.md)
2. Number it sequentially (ADR-{NUMBER})
3. Fill in all sections
4. Submit for review
5. Update this index

## ADR Lifecycle

```
Proposed → Accepted → [Deprecated/Superseded]
```

- **Proposed**: Under discussion
- **Accepted**: Approved and implemented
- **Deprecated**: No longer recommended but still in use
- **Superseded**: Replaced by another ADR

## References

- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub Organization](https://adr.github.io/)
