# Documentation Index

**Last Updated:** 2026-02-04  
**Project:** HCD + JanusGraph Banking Compliance Platform

Welcome to the comprehensive documentation index for the HCD + JanusGraph project. This index provides quick navigation to all project documentation organized by role and topic.

---

## 🚀 Quick Start

**New to the project?** Start here:

1. **[README](../README.md)** - Project overview and introduction
2. **[QUICKSTART](../QUICKSTART.md)** - Get started in 5 minutes
3. **[Setup Guide](guides/setup-guide.md)** - Detailed installation and configuration guide
4. **[AGENTS.md](../AGENTS.md)** - AI assistant guidance and project patterns

---

## 📚 Documentation by Role

### 👨‍💻 For Developers

#### Getting Started
- **[Setup Guide](guides/setup-guide.md)** - Complete development environment setup
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute to the project
- **[Code of Conduct](../CODE_OF_CONDUCT.md)** - Community guidelines

#### API & Integration
- **[API Reference](banking/guides/API_REFERENCE.md)** - Complete API documentation
- **[Gremlin API](api/GREMLIN_API.md)** - Graph traversal API reference
- **[Integration Guide](api/INTEGRATION_GUIDE.md)** - Third-party integration patterns

#### Development Guides
- **[Testing Guide](guides/testing-guide.md)** - Testing strategies and execution
- **[Code Refactoring](development/CODE_REFACTORING_GUIDE.md)** - Refactoring best practices
- **[Authentication Guide](security/AUTHENTICATION_GUIDE.md)** - Security authentication patterns
- **[Visualization Tools](guides/visualization-tools.md)** - Graph visualization tools (G.V() recommended for macOS Silicon)

#### Banking Module
- **[User Guide](banking/guides/USER_GUIDE.md)** - Banking module usage
- **[Advanced Analytics](banking/guides/ADVANCED_ANALYTICS_OLAP_GUIDE.md)** - OLAP and analytics
- **[Gremlin OLAP](banking/guides/GREMLIN_OLAP_ADVANCED_SCENARIOS.md)** - Advanced graph queries

### 🔧 For Operators

#### Deployment
- **[Deployment Guide](guides/deployment-guide.md)** - Production deployment procedures
- **[Production Deployment](banking/implementation/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md)** - Banking module deployment
- **[Production Verification](banking/implementation/deployment/PRODUCTION_SYSTEM_VERIFICATION.md)** - System verification

#### Operations
- **[Operations Runbook](operations/OPERATIONS_RUNBOOK.md)** - Day-to-day operations
- **[Monitoring Guide](operations/monitoring-guide.md)** - System monitoring and alerting
- **[Backup Procedures](operations/backup-procedures.md)** - Backup and restore procedures
- **[Disaster Recovery](operations/DISASTER_RECOVERY_PLAN.md)** - DR planning and execution

#### Security
- **[Security Policy](../SECURITY.md)** - Security guidelines and reporting
- **[TLS Deployment](operations/tls-deployment-guide.md)** - TLS/SSL configuration
- **[Incident Response](operations/incident-response-plan.md)** - Security incident procedures

### 🏗️ For Architects

#### Architecture
- **[System Architecture](architecture/system-architecture.md)** - Overall system design
- **[Banking Architecture](banking/architecture/ARCHITECTURE.md)** - Banking module architecture
- **[Enterprise Patterns](banking/architecture/ENTERPRISE_ADVANCED_PATTERNS_PLAN.md)** - Advanced design patterns

#### Architecture Decision Records (ADRs)
- **[ADR Index](architecture/README.md)** - All architecture decisions
- **[Event-Sourced Ingestion Architecture](architecture/EVENT_SOURCED_INGESTION_ARCHITECTURE.md)** - Pulsar-based dual ingestion for JanusGraph & OpenSearch
- **[ADR-005: JWT Authentication](architecture/ADR-005-jwt-authentication.md)**
- **[ADR-010: Distributed Tracing](architecture/ADR-010-distributed-tracing.md)**
- **[ADR-011: Query Caching](architecture/ADR-011-query-caching-strategy.md)**
- **[ADR Template](architecture/ADR-TEMPLATE.md)** - Template for new ADRs

#### Planning & Strategy
- **[Synthetic Data Generator Plan](banking/planning/SYNTHETIC_DATA_GENERATOR_PLAN.md)** - Data generation strategy
- **[Phase 8 Implementation Guide](banking/planning/PHASE8_IMPLEMENTATION_GUIDE.md)** - Implementation roadmap

### 📊 For Project Managers

#### Project Tracking
- **[Changelog](CHANGELOG.md)** - Version history and changes
- **[Implementation Phases](implementation/phases/)** - Phase completion summaries

#### Audits & Reports
- **[Audit Reports](implementation/audits/)** - Security and code audits
- **[Executive Summary](implementation/audits/EXECUTIVE_SUMMARY.md)** - High-level findings
- **[Remediation Plans](implementation/remediation/)** - Issue remediation tracking

#### Gap Analysis
- **[Banking Gap Analysis](banking/planning/gap-analysis.md)** - Requirements analysis
- **[Technical Specifications](banking/planning/technical-spec.md)** - Detailed specifications

### 🔒 For Compliance Teams

#### Compliance Documentation
- **[GDPR Compliance](compliance/GDPR_COMPLIANCE.md)** - GDPR requirements
- **[SOC2 Controls](compliance/SOC2_CONTROLS.md)** - SOC2 compliance
- **[Data Retention Policy](compliance/DATA_RETENTION_POLICY.md)** - Data retention rules

#### Banking Compliance
- **[AML Setup](banking/setup/01_AML_PHASE1_SETUP.md)** - Anti-Money Laundering setup
- **[Banking Overview](banking/setup/00_OVERVIEW.md)** - Banking module overview

---

## 📖 Documentation by Topic

### Infrastructure & Deployment
- [Setup Guide](guides/setup-guide.md)
- [Deployment Guide](guides/deployment-guide.md)
- [TLS Deployment](operations/tls-deployment-guide.md)
- [Backup Procedures](operations/backup-procedures.md)
- [Disaster Recovery](operations/DISASTER_RECOVERY_PLAN.md)

### Monitoring & Operations
- [Monitoring Guide](operations/monitoring-guide.md)
- [Operations Runbook](operations/OPERATIONS_RUNBOOK.md)
- [Incident Response](operations/incident-response-plan.md)
- [Infrastructure Optimization](performance/INFRASTRUCTURE_OPTIMIZATION.md)

### Development & Testing
- [Contributing Guidelines](CONTRIBUTING.md)
- [Testing Guide](guides/testing-guide.md)
- [Code Refactoring](development/CODE_REFACTORING_GUIDE.md)
- [Authentication Guide](security/AUTHENTICATION_GUIDE.md)

### Banking & Compliance
- [Banking User Guide](banking/guides/USER_GUIDE.md)
- [Banking API Reference](banking/guides/API_REFERENCE.md)
- [AML Setup](banking/setup/01_AML_PHASE1_SETUP.md)
- [Advanced Analytics](banking/guides/ADVANCED_ANALYTICS_OLAP_GUIDE.md)

### Architecture & Design
- [System Architecture](architecture/system-architecture.md)
- [Banking Architecture](banking/architecture/ARCHITECTURE.md)
- [ADR Index](architecture/README.md)
- [Enterprise Patterns](banking/architecture/ENTERPRISE_ADVANCED_PATTERNS_PLAN.md)

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
- **"How do I use the banking module?"** → [Banking User Guide](banking/guides/USER_GUIDE.md)
- **"How do I monitor?"** → [Monitoring Guide](operations/monitoring-guide.md)

---

## 📁 Directory Structure

```
docs/
├── INDEX.md                    # This file - central navigation
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── DOCUMENTATION_STANDARDS.md  # Documentation standards
├── TECHNICAL_SPECIFICATIONS.md # Technical specs
│
├── api/                        # API documentation
│   ├── GREMLIN_API.md
│   ├── INTEGRATION_GUIDE.md
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
│   ├── GDPR_COMPLIANCE.md
│   ├── SOC2_CONTROLS.md
│   └── DATA_RETENTION_POLICY.md
│
├── development/                # Development guides
│   └── CODE_REFACTORING_GUIDE.md
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
├── operations/                 # Operations documentation
│   ├── OPERATIONS_RUNBOOK.md
│   ├── monitoring-guide.md
│   ├── backup-procedures.md
│   ├── tls-deployment-guide.md
│   ├── incident-response-plan.md
│   └── DISASTER_RECOVERY_PLAN.md
│
├── performance/                # Performance docs
│   └── INFRASTRUCTURE_OPTIMIZATION.md
│
├── security/                   # Security documentation
│   └── AUTHENTICATION_GUIDE.md
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
2. **Operations Runbook:** [OPERATIONS_RUNBOOK.md](operations/OPERATIONS_RUNBOOK.md)
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

## 📅 Maintenance

This index is maintained by the project team and updated with each major release.

**Review Schedule:** Monthly  
**Last Review:** 2026-02-04  
**Next Review:** 2026-03-04

---

**Questions?** Check [Operations Runbook](operations/OPERATIONS_RUNBOOK.md) or open an issue.
