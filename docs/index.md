# Documentation Index

**Last Updated:** 2026-02-18
**Project:** HCD + JanusGraph Banking Compliance Platform

Welcome to the comprehensive documentation index for the HCD + JanusGraph project. This index provides quick navigation to all project documentation organized by role and topic.

---

## 🚀 Quick Start

**New to the project?** Start here:

1. **README** (see repo root) - Project overview and introduction
2. **[Quick Start](../QUICKSTART.md)** - Canonical deterministic quick start
3. **[Setup Guide](guides/setup-guide.md)** - Detailed installation and configuration guide
4. **AGENTS.md** (see repo root) - AI assistant guidance and project patterns
5. **[FAQ](FAQ.md)** - Frequently Asked Questions

---

## 📚 Documentation by Role

### 👨‍💻 For Developers

#### Getting Started

- **[Setup Guide](guides/setup-guide.md)** - Complete development environment setup
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute to the project
- **Code of Conduct** (see repo root) - Community guidelines

#### API & Integration

- **[API Reference](banking/guides/api-reference.md)** - Complete API documentation
- **[Gremlin API](api/gremlin-api.md)** - Graph traversal API reference
- **[Integration Guide](api/integration-guide.md)** - Third-party integration patterns

#### Development Guides

- **[Testing Guide](guides/testing-guide.md)** - Testing strategies and execution
- **[Code Refactoring](development/code-refactoring-guide.md)** - Refactoring best practices
- **[Authentication Guide](security/authentication-guide.md)** - Security authentication patterns
- **[Visualization Tools](guides/visualization-tools.md)** - Graph visualization tools (G.V() recommended for macOS Silicon)

#### Banking Module

- **[User Guide](banking/guides/user-guide.md)** - Banking module usage
- **[Streaming Architecture](architecture/streaming-architecture.md)** - Event streaming with Pulsar (Producer, Consumer, DLQ, Metrics)
- **[Advanced Analytics](banking/guides/advanced-analytics-olap-guide.md)** - OLAP and analytics
- **[Gremlin OLAP](banking/guides/gremlin-olap-advanced-scenarios.md)** - Advanced graph queries

### 🔧 For Operators

#### Deployment

- **[Deployment Guide](guides/deployment-guide.md)** - Production deployment procedures
- **[Production Deployment](banking/implementation/deployment/production-deployment-guide.md)** - Banking module deployment
- **[Production Verification](banking/implementation/deployment/production-system-verification.md)** - System verification

#### Operations

- **[Operations Runbook](operations/operations-runbook.md)** - Day-to-day operations
- **[Monitoring Guide](operations/monitoring-guide.md)** - System monitoring and alerting
- **[Backup Procedures](operations/backup-procedures.md)** - Backup and restore procedures
- **[Disaster Recovery](operations/disaster-recovery.md)** - DR planning and execution

#### Security

- **Security Policy** (see repo root) - Security guidelines and reporting
- **[TLS Deployment](operations/tls-deployment-guide.md)** - TLS/SSL configuration
- **[Incident Response](operations/incident-response-plan.md)** - Security incident procedures

### 🏗️ For Architects

#### Architecture

- **[System Architecture](architecture/system-architecture.md)** - Overall system design
- **[Banking Architecture](banking/architecture/architecture.md)** - Banking module architecture
- **[Enterprise Patterns](banking/architecture/enterprise-advanced-patterns-plan.md)** - Advanced design patterns

#### Data Flow & Pipeline

- **[Unified Data Flow](architecture/data-flow-unified.md)** - Complete data flow with ASCII & Mermaid diagrams (ID consistency, topic structure, DLQ)
- **[Streaming Architecture](architecture/streaming-architecture.md)** - Real-time streaming pipeline architecture with Pulsar
- **[Event-Sourced Ingestion Architecture](architecture/event-sourced-ingestion-architecture.md)** - Pulsar-based dual ingestion for JanusGraph & OpenSearch

#### Architecture Decision Records (ADRs)

- **[ADR Index](architecture/README.md)** - All architecture decisions
- **[Pulsar Implementation Plan](architecture/pulsar-implementation-plan.md)** - 6-week implementation plan with tasks, idempotency analysis, CDC requirements
- **[ADR-005: JWT Authentication](architecture/adr-005-jwt-authentication.md)**
- **[ADR-010: Distributed Tracing](architecture/adr-010-distributed-tracing.md)**
- **[ADR-011: Query Caching](architecture/adr-011-query-caching-strategy.md)**
- **[ADR Template](architecture/adr-template.md)** - Template for new ADRs

#### Planning & Strategy

- **[Synthetic Data Generator Plan](banking/planning/synthetic-data-generator-plan.md)** - Data generation strategy
- **[Banking Implementation Phases](banking/implementation/phases/README.md)** - Active phase docs and archived phase iterations

### 📊 For Project Managers

#### Project Tracking

- **Changelog** - Version history and changes (see root `CHANGELOG.md`)
- **[Implementation Phases](implementation/phases/)** - Phase completion summaries
- **[Remediation Baseline](implementation/remediation-plan-workingB-plus.md)** - Current prioritized backlog and delivery plan

#### Audits & Reports

- **[Audit Reports](implementation/audits/)** - Security and code audits
- **[Codex Documentation Obsolescence Audit (2026-02-17)](implementation/audits/codex-documentation-obsolescence-audit-2026-02-17.md)** - Full docs audit and archival ledger
- **[Codex Executive Summary (2026-02-17)](implementation/audits/codex-podman-wxd-deployment-live-notebook-proof-executive-summary-2026-02-17.md)** - Deployment recovery and notebook proof closure
- **[Codex Remediation Log (2026-02-17)](implementation/audits/codex-podman-wxd-deployment-live-notebook-proof-remediation-log-2026-02-17.md)** - Issue-by-issue solutions and evidence
- **[Comprehensive Project Audit (2026-02-16)](implementation/audits/comprehensive-project-audit-2026-02-16.md)** - Current consolidated technical baseline
- **[Remediation Plans](implementation/remediation/)** - Issue remediation tracking
- **[Codex Full Deterministic Setup and Run Motion Plan (2026-02-17)](implementation/remediation/codex-full-deterministic-setup-and-run-motion-plan-2026-02-17.md)** - Detailed implementation plan for end-to-end deterministic runs

#### Gap Analysis

- **[Banking Gap Analysis](banking/planning/gap-analysis.md)** - Requirements analysis
- **[Technical Specifications](technical-specifications.md)** - Detailed specifications

### 🔒 For Compliance Teams

#### Compliance Documentation

- **[GDPR Compliance](compliance/gdpr-compliance.md)** - GDPR requirements
- **[SOC2 Controls](compliance/soc2-controls.md)** - SOC2 compliance
- **[Data Retention Policy](compliance/data-retention-policy.md)** - Data retention rules

#### Banking Compliance

- **[AML Setup](banking/setup/01-aml-phase1-setup.md)** - Anti-Money Laundering setup
- **[Banking Overview](banking/setup/00-overview.md)** - Banking module overview

---

## 📖 Documentation by Topic

### Infrastructure & Deployment

- [Setup Guide](guides/setup-guide.md)
- [Deployment Guide](guides/deployment-guide.md)
- [TLS Deployment](operations/tls-deployment-guide.md)
- [Backup Procedures](operations/backup-procedures.md)
- [Disaster Recovery](operations/disaster-recovery.md)

### Monitoring & Operations

- [Monitoring Guide](operations/monitoring-guide.md)
- [Operations Runbook](operations/operations-runbook.md)
- [Incident Response](operations/incident-response-plan.md)
- [Infrastructure Optimization](performance/infrastructure-optimization.md)

### Development & Testing

- [Contributing Guidelines](CONTRIBUTING.md)
- [Testing Guide](guides/testing-guide.md)
- [Code Refactoring](development/code-refactoring-guide.md)
- [Authentication Guide](security/authentication-guide.md)

### Banking & Compliance

- [Banking User Guide](banking/guides/user-guide.md)
- [Banking API Reference](banking/guides/api-reference.md)
- [AML Setup](banking/setup/01-aml-phase1-setup.md)
- [Advanced Analytics](banking/guides/advanced-analytics-olap-guide.md)

### Architecture & Design

- [System Architecture](architecture/system-architecture.md)
- [Banking Architecture](banking/architecture/architecture.md)
- [ADR Index](architecture/README.md)
- [Enterprise Patterns](banking/architecture/enterprise-advanced-patterns-plan.md)

---

## 🔍 Finding Documentation

### By File Type

- **Guides:** Step-by-step instructions for specific tasks
- **References:** Comprehensive API and configuration documentation
- **ADRs:** Architecture decisions and rationale
- **Runbooks:** Operational procedures and troubleshooting
- **Plans:** Strategic planning and roadmaps

### Search Tips

1. **Use your IDE's search:** Most effective for finding specific terms
2. **Check the relevant role section:** Documentation is organized by user role
3. **Start with README files:** Each directory has a README with overview
4. **Follow cross-references:** Documents link to related content

### Common Searches

- **"How do I deploy?"** → [Deployment Guide](guides/deployment-guide.md)
- **"How do I test?"** → [Testing Guide](guides/testing-guide.md)
- **"What's the architecture?"** → [System Architecture](architecture/system-architecture.md)
- **"How do I use the banking module?"** → [Banking User Guide](banking/guides/user-guide.md)
- **"How do I monitor?"** → [Monitoring Guide](operations/monitoring-guide.md)

---

## 📁 Directory Structure

```
docs/
├── index.md                    # This file - central navigation
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── documentation-standards.md  # Documentation standards
├── technical-specifications.md # Technical specs
│
├── api/                        # API documentation
│   ├── gremlin-api.md
│   ├── integration-guide.md
│   └── openapi.yaml
│
├── architecture/               # Architecture decisions
│   ├── system-architecture.md
│   ├── ADR-*.md
│   └── README.md
│
├── banking/                    # Banking module docs
│   ├── README.md
│   ├── guides/                # User and developer guides
│   ├── architecture/          # Banking architecture
│   ├── implementation/        # Implementation docs
│   ├── planning/              # Planning documents
│   └── setup/                 # Setup guides
│
├── compliance/                 # Compliance documentation
│   ├── gdpr-compliance.md
│   ├── soc2-controls.md
│   └── data-retention-policy.md
│
├── development/                # Development guides
│   └── code-refactoring-guide.md
│
├── guides/                     # General guides
│   ├── setup-guide.md
│   ├── deployment-guide.md
│   ├── testing-guide.md
│   └── visualization-tools.md
│
├── implementation/             # Implementation tracking
│   ├── audits/                # Audit reports
│   ├── phases/                # Phase summaries
│   └── remediation/           # Remediation plans
│
├── archive/                    # Historical documentation
│   └── 2026-02/               # February 2026 archive
│       ├── weekly-summaries/  # Historical progress reports
│       ├── phase-iterations/  # Superseded phase docs
│       ├── duplicates/        # Duplicate content
│       ├── audits/            # Obsolete audits
│       ├── remediation/       # Completed remediation
│       ├── misc/              # Miscellaneous obsolete files
│       └── README.md          # Archive index
│
├── operations/                 # Operations documentation
│   ├── operations-runbook.md
│   ├── monitoring-guide.md
│   ├── backup-procedures.md
│   ├── tls-deployment-guide.md
│   ├── incident-response-plan.md
│   └── disaster-recovery-plan.md
│
├── performance/                # Performance docs
│   └── infrastructure-optimization.md
│
├── security/                   # Security documentation
│   └── authentication-guide.md
│
├── strategic/                  # Strategic analysis
│   └── REBUILD_VS_REMEDIATION_ANALYSIS_2026-01-30.md
│
└── archive/                    # Historical documents
```

---

## 🆘 Getting Help

### Documentation Issues

- **Missing documentation?** Check if it's in progress or [create an issue](https://github.com/your-org/your-repo/issues)
- **Outdated content?** Submit a pull request with updates
- **Unclear instructions?** Open an issue with specific questions

### Support Channels

1. **Documentation:** Start here - most questions are answered
2. **Operations Runbook:** [operations-runbook.md](operations/operations-runbook.md)
3. **GitHub Issues:** For bugs and feature requests
4. **Team Chat:** For real-time assistance

---

## 📝 Contributing to Documentation

We welcome documentation improvements! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Documentation Standards

- Use clear, concise language
- Include code examples where appropriate
- Add cross-references to related documents
- Keep formatting consistent
- Update this index when adding new documents

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test all links and examples
5. Submit a pull request

---

## 🛠️ Documentation Tools

### Quality Assurance

- **Markdownlint**: Linting configuration in `.markdownlint.json`
- **Link Checker**: Configuration in `.markdown-link-check.json`
- **CI Workflow**: Automated checks in `.github/workflows/docs-lint.yml`

### Coverage & Search

- **Doc Coverage**: `python scripts/docs/doc_coverage.py --report`
- **AI Search**: `python scripts/docs/setup_doc_search.py --index` (requires OpenSearch)

### Building Documentation Site

```bash
# Install MkDocs with Material theme
pip install mkdocs-material pymdown-extensions mkdocs-mermaid2-plugin

# Serve locally
mkdocs serve

# Build static site
mkdocs build
```

---

## 📅 Maintenance

This index is maintained by the project team and updated with each major release.

**Review Schedule:** Monthly
**Last Review:** 2026-02-06
**Next Review:** 2026-03-06

---

**Questions?** Check [Operations Runbook](operations/operations-runbook.md) or open an issue.

## Codex Fresh-Machine Enforcement Update (2026-02-17)

New canonical deterministic deployment enforcement reference:

- [Codex Podman-WXD Fresh Machine Enforcement Matrix (2026-02-17)](implementation/audits/codex-podman-wxd-fresh-machine-enforcement-matrix-2026-02-17.md)

Use this matrix with these operational docs:

- [Setup Guide](guides/setup-guide.md)
- [Deployment Guide](guides/deployment-guide.md)
- [Deployment Verification](development/deployment-verification.md)
- [Operations Runbook](operations/operations-runbook.md)

## Deterministic Setup and Proof (Canonical)

- Canonical command: `bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json`
- Deterministic plan: [implementation/remediation/codex-full-deterministic-setup-and-run-motion-plan-2026-02-17.md](implementation/remediation/codex-full-deterministic-setup-and-run-motion-plan-2026-02-17.md)
- Enforcement matrix: [implementation/audits/codex-podman-wxd-fresh-machine-enforcement-matrix-2026-02-17.md](implementation/audits/codex-podman-wxd-fresh-machine-enforcement-matrix-2026-02-17.md)
- Deployment verification: [development/deployment-verification.md](development/deployment-verification.md)
