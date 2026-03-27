# Documentation Index

**Date:** 2026-03-26  
**Status:** Active  
**Project:** HCD + JanusGraph Banking Compliance Platform  
**TL;DR:** This is the canonical documentation entry point. Use this page to navigate by role, topic, and operational objective.

---

## 1) Start Here (Authoritative Entry Points)

1. **[README](../README.md)** - Project overview and quick orientation  
2. **[QUICKSTART](../QUICKSTART.md)** - Deterministic setup and first successful run  
3. **[Project Status](project-status.md)** - Current verified readiness and baseline  
4. **[AGENTS](../AGENTS.md)** - Operational rules, canonical commands, and runtime policy  
5. **[CHANGELOG](../CHANGELOG.md)** - Release and change history  

---

## 2) Role-Based Navigation

## Developers
- [Setup Guide](guides/setup-guide.md)
- [Testing Guide](guides/testing-guide.md)
- [API Integration Guide](api/integration-guide.md)
- [Gremlin API](api/gremlin-api.md)
- [Code Refactoring Guide](development/code-refactoring-guide.md)
- [Visualization Tools](guides/visualization-tools.md)

## Operators / SRE / Platform
- [Operations Runbook](operations/operations-runbook.md)
- [Monitoring Guide](operations/monitoring-guide.md)
- [Incident Response Plan](operations/incident-response-plan.md)
- [Backup Procedures](operations/backup-procedures.md)
- [Disaster Recovery](operations/disaster-recovery.md)
- [TLS Deployment Guide](operations/tls-deployment-guide.md)
- [Deterministic Gate Alert Mapping](operations/deterministic-gate-alert-runbook-mapping.md)
- [Time-to-Notebook-Ready SLA](operations/time-to-notebook-ready-sla.md)
- [Runbook Improvement Plan (30-60-90)](operations/runbook-improvement-plan-30-60-90.md)

## Banking Domain / Analysts
- [Banking Docs Home](banking/README.md)
- [Banking User Guide](banking/guides/user-guide.md)
- [Notebook Scenarios Summary](banking/guides/notebook-scenarios-business-technical-summary.md)
- [Advanced Analytics OLAP Guide](banking/guides/advanced-analytics-olap-guide.md)
- [Gremlin OLAP Advanced Scenarios](banking/guides/gremlin-olap-advanced-scenarios.md)
- [Notebook Business Audit Remediation Plan](operations/notebook-business-audit-remediation-plan.md)

## Security / Compliance
- [GDPR Compliance](compliance/gdpr-compliance.md)
- [SOC2 Controls](compliance/soc2-controls.md)
- [Data Retention Policy](compliance/data-retention-policy.md)
- [Authentication Guide](security/authentication-guide.md)
- [Business Compliance Portfolio](business/compliance-certifications-portfolio.md)
- [Risk Management Framework](business/risk-management-framework.md)

## Architects / Technical Leadership
- [Architecture Index](architecture/README.md)
- [System Architecture](architecture/system-architecture.md)
- [Deployment Architecture](architecture/deployment-architecture.md)
- [Podman Isolation Architecture](architecture/podman-isolation-architecture.md)
- [Streaming Architecture](architecture/streaming-architecture.md)
- [Unified Data Flow](architecture/data-flow-unified.md)
- [Horizontal Scaling Strategy](architecture/horizontal-scaling-strategy.md)

## Product / PM / Business Stakeholders
- [Business Docs Index](business/README.md)
- [Executive Summary](business/executive-summary.md)
- [Comprehensive Business Case](business/comprehensive-business-case.md)
- [ROI Calculator](business/roi-calculator.md)
- [TCO Analysis](business/tco-analysis.md)
- [SLA Documentation](business/sla-documentation.md)

---

## 3) Topic-Based Navigation

## Determinism and Release Readiness
- [Project Status](project-status.md)
- [Determinism Acceptance Criteria Checklist](operations/determinism-acceptance-criteria-checklist.md)
- [Deterministic Behavior: Expected Outputs](operations/deterministic-behavior-expected-outputs.md)
- [Time-to-Notebook-Ready SLA](operations/time-to-notebook-ready-sla.md)
- [Runbook Improvement Plan (30-60-90)](operations/runbook-improvement-plan-30-60-90.md)

## Banking Notebook Delivery and Business Outcomes
- [Notebook Scenarios Summary](banking/guides/notebook-scenarios-business-technical-summary.md)
- [Notebook Business Audit Remediation Plan](operations/notebook-business-audit-remediation-plan.md)
- [Banking Gap Analysis](banking/planning/gap-analysis.md)

## Implementation Evidence and Audits
- [Implementation Index](implementation/README.md)
- [Audit Reports](implementation/audits/)
- [Phase Summaries](implementation/phases/)
- [Remediation Plans](implementation/remediation/)

## API and Integration
- [API Directory](api/)
- [Gremlin API](api/gremlin-api.md)
- [Integration Guide](api/integration-guide.md)

---

## 4) Directory Map

- [docs/api/](api/)
- [docs/architecture/](architecture/)
- [docs/banking/](banking/)
- [docs/business/](business/)
- [docs/compliance/](compliance/)
- [docs/development/](development/)
- [docs/guides/](guides/)
- [docs/implementation/](implementation/)
- [docs/operations/](operations/)
- [docs/performance/](performance/)
- [docs/security/](security/)
- [docs/archive/](archive/)

> Note: `docs/archive/` contains historical and superseded artifacts and should not be treated as primary operational guidance unless explicitly referenced.

---

## 5) Documentation Standards and Maintenance

- [Documentation Standards](documentation-standards.md)
- [Contributing](../CONTRIBUTING.md)

### Maintenance Rules
1. Add new docs in the correct domain directory.
2. Use kebab-case filenames (except standard root exceptions like README.md).
3. Use relative links only.
4. Update this index when adding new high-value or authoritative documents.
5. Keep numeric/project-readiness claims centralized in `docs/project-status.md`.

---

## 6) Quick Search and Coverage

- Generate coverage report:  
  `python scripts/docs/doc_coverage.py --report`
- Build doc search index (if configured):  
  `python scripts/docs/setup_doc_search.py --index`

---

## 7) Canonical Deterministic Command

```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json
```

For operational interpretation of outcomes, use:
- [Operations Runbook](operations/operations-runbook.md)
- [Deterministic Gate Alert Mapping](operations/deterministic-gate-alert-runbook-mapping.md)
