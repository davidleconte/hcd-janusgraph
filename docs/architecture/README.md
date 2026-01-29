# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) documenting significant architectural decisions made during the HCD JanusGraph project development and remediation.

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
| [ADR-001](ADR-001-janusgraph-as-graph-database.md) | Use JanusGraph as Graph Database | Accepted | 2026-01-15 |
| [ADR-002](ADR-002-hcd-as-storage-backend.md) | Use HCD (Cassandra) as Storage Backend | Accepted | 2026-01-15 |
| [ADR-003](ADR-003-docker-compose-deployment.md) | Docker Compose for Development Deployment | Accepted | 2026-01-16 |
| [ADR-004](ADR-004-python-client-library.md) | Python as Primary Client Language | Accepted | 2026-01-16 |
| [ADR-005](ADR-005-jwt-authentication.md) | JWT-Based Authentication | Accepted | 2026-01-20 |
| [ADR-006](ADR-006-rbac-authorization.md) | Role-Based Access Control (RBAC) | Accepted | 2026-01-20 |
| [ADR-007](ADR-007-mfa-implementation.md) | TOTP-Based Multi-Factor Authentication | Accepted | 2026-01-21 |
| [ADR-008](ADR-008-tls-encryption.md) | TLS/SSL Encryption for All Communications | Accepted | 2026-01-22 |
| [ADR-009](ADR-009-prometheus-monitoring.md) | Prometheus and Grafana for Monitoring | Accepted | 2026-01-23 |
| [ADR-010](ADR-010-distributed-tracing.md) | OpenTelemetry and Jaeger for Distributed Tracing | Accepted | 2026-01-24 |
| [ADR-011](ADR-011-query-caching-strategy.md) | LRU-Based Query Caching | Accepted | 2026-01-25 |
| [ADR-012](ADR-012-github-actions-cicd.md) | GitHub Actions for CI/CD Pipeline | Accepted | 2026-01-26 |

## Creating New ADRs

When creating a new ADR:

1. Copy the [ADR template](ADR-TEMPLATE.md)
2. Number it sequentially (ADR-XXX)
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