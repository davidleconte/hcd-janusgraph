# HCD + JanusGraph Containerized Stack

**File**: README.md
**Created**: 2026-01-28T10:36:00.123
**Author**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

---

## Overview

Production-ready containerized stack combining **HyperConverged Database (HCD) 1.2.3** with **JanusGraph** for scalable graph database operations. Fully integrated with Jupyter Lab, monitoring (Prometheus/Grafana), and visualization tools.

### Key Features

✅ **Production-Ready**: Health checks, resource limits, graceful shutdown
✅ **Security Hardened**: SSL/TLS encryption, HashiCorp Vault integration, secrets management
✅ **Advanced Monitoring**: Prometheus + Grafana + AlertManager + JanusGraph metrics exporter
✅ **Automated CI/CD**: GitHub Actions workflows for testing and deployment
✅ **Comprehensive Testing**: 610+ unit tests (+ co-located module tests), unit/integration/E2E/performance suites
✅ **Resilience**: Circuit breaker, retry with exponential backoff, startup validation
✅ **Observability**: OpenTelemetry tracing, structured JSON logging, PII-sanitized logs
✅ **Backup & Restore**: Automated backup scripts with encryption support
✅ **Multi-Environment**: Separate configs for dev/staging/prod
✅ **Complete Documentation**: Setup, testing, operations, and production readiness guides

---

## Prerequisites

### Required Software

- **Podman** 4.9+ ([Install](https://podman.io/getting-started/installation))
- **Python** 3.11+ ([Install](https://www.python.org/downloads/))
- **Git** ([Install](https://git-scm.com/downloads))
- **8GB+ RAM** recommended
- **20GB+ disk space**

### HCD Distribution (Git LFS)

The HCD (HyperConverged Database) distribution is included via **Git LFS** in the `vendor/` directory.

After cloning, create a symlink so Docker can find it:

```bash
# Pull LFS files (if not done automatically)
git lfs pull

# Create symlink at project root
ln -sf vendor/hcd-1.2.3 hcd-1.2.3

# Verify
ls hcd-1.2.3/bin/hcd  # Should show the HCD binary
```

> **Note**: If `git lfs` is not installed, see [Git LFS Installation](https://git-lfs.github.com/).

### Verify Prerequisites

```bash
# Run preflight check (recommended)
./scripts/validation/preflight_check.sh

# Or verify manually
podman --version      # 4.9+
python3 --version     # 3.11+
ls hcd-1.2.3/bin/hcd  # Should show HCD binary
```

---

## Quick Start

### Option 1: Demo Quick Start (Recommended for Demos)

**One-command setup with automatic password generation:**

```bash
# 1. Clone repository
git clone https://github.com/davidleconte/hcd-janusgraph.git
cd hcd-janusgraph

# 2. Set up HCD symlink (included via Git LFS)
git lfs pull
ln -sf vendor/hcd-1.2.3 hcd-1.2.3

# 3. One-command demo deployment
./scripts/deployment/demo_quickstart.sh

# Credentials will be saved to demo-credentials.txt
# Services will be deployed automatically
```

**Or step-by-step:**

```bash
# Generate passwords and create .env file
./scripts/deployment/setup_demo_env.sh

# Review generated credentials
cat demo-credentials.txt

# Deploy services
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
```

⚠️ **Demo credentials are for demonstration only. Never use in production!**

### Option 2: Manual Setup (Production)

```bash
# 1. Clone repository
git clone https://github.com/davidleconte/hcd-janusgraph.git
cd hcd-janusgraph

# 2. Set up HCD symlink (included via Git LFS)
git lfs pull
ln -sf vendor/hcd-1.2.3 hcd-1.2.3

# 3. Create .env file and set passwords manually
cp .env.example .env
# Edit .env and set all passwords (see .env.example for requirements)

# 4. Deploy stack (MUST run from config/compose directory)
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# Or use Makefile (handles directory change automatically)
cd ../..
make deploy

# 5. Verify installation
make test

# 6. Access Jupyter
open http://localhost:8888
```

📚 **See [QUICKSTART.md](QUICKSTART.md) for detailed commands and troubleshooting**
📚 **See [docs/DEMO_SETUP_GUIDE.md](docs/DEMO_SETUP_GUIDE.md) for demo setup details**

### Python Environment Setup

Choose ONE of these installation methods:

**Option A: Conda (Recommended)**

```bash
# Create environment from file
conda env create -f environment.yml

# Activate
conda activate janusgraph-analysis
```

**Option B: pip**

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development (includes testing tools)
pip install -e ".[dev]"
```

**Option C: uv (Fast)**

```bash
# Create virtual environment and install
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Production Deployment

For production environments with security hardening:

```bash
# 1. Set required environment variables (will fail if not set)
export HCD_KEYSTORE_PASSWORD=your-secure-password
export JANUSGRAPH_TRUSTSTORE_PASSWORD=your-secure-password
export GRAFANA_ADMIN_PASSWORD=your-secure-password
export OPENSEARCH_ADMIN_PASSWORD=your-secure-password

# 2. Generate certificates
./scripts/security/generate_certificates.sh

# 3. Deploy with security overlay
cd config/compose
podman-compose -f docker-compose.full.yml -f docker-compose.prod.yml up -d
```

See `config/compose/docker-compose.prod.yml` for security hardening details.

---

## Project Structure

```
hcd-tarball-janusgraph/
├── .github/              # CI/CD workflows, issue/PR templates
├── config/               # All configuration files
│   ├── compose/          # Docker compose files
│   ├── environments/     # Multi-environment configs
│   ├── janusgraph/       # JanusGraph configuration
│   └── monitoring/       # Prometheus/Grafana configs
├── docker/               # Dockerfiles for all services
├── scripts/              # Automation scripts
│   ├── deployment/       # Deploy/stop scripts
│   ├── backup/           # Backup/restore scripts
│   ├── monitoring/       # Monitoring setup
│   ├── testing/          # Test scripts
│   └── maintenance/      # Maintenance tasks
├── src/                  # Source code
│   ├── python/           # Python modules
│   └── groovy/           # Groovy scripts
├── tests/                # Test suites
│   ├── integration/      # Integration tests
│   ├── unit/             # Unit tests
│   └── fixtures/         # Test fixtures
├── docs/                 # Documentation
├── notebooks/            # Jupyter notebooks
└── data/                 # Data files
```

Total: **8 directories + 11 core files** (vs 43 files at root before restructuring!)

---

## Core Components

### Services

| Service | Description | Port |
|---------|-------------|------|
| **HCD** | Cassandra-based distributed database | 19042 (9142 TLS) |
| **JanusGraph** | Graph database | 18182 |
| **Analytics API** | FastAPI analytics service | 8001 |
| **Jupyter Lab** | Interactive notebooks | 8888 |
| **Prometheus** | Metrics collection | 9090 |
| **Grafana** | Monitoring dashboards | 3001 |
| **AlertManager** | Alert routing and notifications | 9093 |
| **JanusGraph Exporter** | Custom metrics exporter | 9091 |
| **Vault** | Secrets management | 8200 |
| **Visualizer** | Graph visualization | 3000 |
| **Graphexp** | Graph explorer | 8080 |
| **OpenSearch** | Full-text search & vector DB | 9200 |
| **OpenSearch Dashboards** | OpenSearch Web UI | 5601 |
| **Pulsar** | Message streaming | 6650, 8081 |
| **Graph Consumer** | JanusGraph ingestion service | - |
| **Vector Consumer** | OpenSearch ingestion service | - |

### CLI Tools & Consoles

| Tool | Container | Access |
|------|-----------|--------|
| **CQLSH** | cqlsh-client | `podman exec -it janusgraph-demo_cqlsh-client_1 cqlsh hcd-server` |
| **Gremlin Console** | gremlin-console | `podman exec -it janusgraph-demo_gremlin-console_1 bin/gremlin.sh` |
| **Pulsar CLI** | pulsar-cli | `podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin ...` |
| **OpenSearch Dashboards** | opensearch-dashboards | <http://localhost:5601> |

📚 **See [QUICKSTART.md](QUICKSTART.md) for detailed CLI usage examples**

### Analytics API

REST API for graph-based analytics including UBO discovery, AML detection, and fraud analysis.

**Base URL**: `http://localhost:8001`

**Documentation**:

- OpenAPI Docs: <http://localhost:8001/docs>
- ReDoc: <http://localhost:8001/redoc>

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/stats` | GET | Graph statistics (vertex/edge counts) |
| `/api/v1/ubo/discover` | POST | Discover Ultimate Beneficial Owners |
| `/api/v1/ubo/network/{company_id}` | GET | Get ownership network for visualization |
| `/api/v1/aml/structuring` | POST | Detect structuring (smurfing) patterns |
| `/api/v1/fraud/rings` | POST | Detect fraud ring patterns |

**Example Usage**:

```bash
# Health check
curl http://localhost:8001/health

# Graph statistics
curl http://localhost:8001/stats

# Discover UBOs for a company
curl -X POST http://localhost:8001/api/v1/ubo/discover \
  -H "Content-Type: application/json" \
  -d '{"company_id": "COMP-001", "ownership_threshold": 0.25}'

# Detect structuring patterns
curl -X POST http://localhost:8001/api/v1/aml/structuring \
  -H "Content-Type: application/json" \
  -d '{"time_window_days": 30, "threshold_amount": 10000}'
```

### Sample Data

Pre-loaded graph includes:

- **5 people** (Alice, Bob, Carol, David, Eve)
- **3 companies** (DataStax, Acme Corp, TechStart)
- **3 products** (JanusGraph, Cloud Service Platform, Analytics Engine)
- **19 relationships** (knows, worksFor, created, uses)

---

## Documentation

### Core Documentation

| Document | Description |
|----------|-------------|
| **[QUICKSTART.md](QUICKSTART.md)** | Essential commands, URLs, troubleshooting |
| **[docs/INDEX.md](docs/INDEX.md)** | Central documentation index and navigation |
| **[AGENTS.md](AGENTS.md)** | AI agent guidance and project patterns |

### Production Readiness

| Document | Description |
|----------|-------------|
| **[Production Readiness Audit](docs/implementation/production-readiness-audit-2026.md)** | Comprehensive system audit (A+ grade, 99/100) |
| **[6-Week Roadmap](docs/implementation/production-readiness-audit-2026.md)** | Production roadmap (Complete) |
| **[Week 1: Security](docs/implementation/WEEK1_COMPLETE_SUMMARY_2026-02-11.md)** | SSL/TLS + Vault implementation ✅ |
| **[Week 2: Monitoring](docs/implementation/WEEK2_DAY12_COMPLETE_SUMMARY.md)** | AlertManager + metrics exporter ✅ |
| **[Week 3-4: Testing](docs/implementation/WEEK3_COMPLETE_SUMMARY.md)** | Test coverage (82%) ✅ |

### Banking & Compliance

| Document | Description |
|----------|-------------|
| **[Banking User Guide](docs/banking/USER_GUIDE.md)** | Complete banking system guide |
| **[AML Setup](docs/banking/setup/01_AML_PHASE1_SETUP.md)** | Anti-Money Laundering configuration |
| **[Technical Spec](docs/banking/planning/technical-spec-complete.md)** | Banking use cases specification |

### Operations

| Document | Description |
|----------|-------------|
| **[Operations Runbook](docs/operations/operations-runbook.md)** | Day-to-day operations guide |
| **[Monitoring Guide](docs/operations/monitoring-guide.md)** | Monitoring and alerting setup |
| **[Backup Procedures](docs/operations/backup-procedures.md)** | Backup and restore procedures |

---

## Requirements

- **Podman** 4.9+ (or Docker with Compose plugin)
- **Python** 3.11+
- **Git**
- **8GB+ RAM** recommended
- **20GB+ disk space**

---

## CI/CD

### GitHub Actions Workflows

- **CI** (`ci.yml`): Lint, test, build, integration tests, security scan
- **Security** (`security.yml`): CodeQL, secret scan, dependency check, image scan
- **Deploy Dev** (`deploy-dev.yml`): Auto-deploy to development
- **Deploy Prod** (`deploy-prod.yml`): Manual production deployment with approval

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

---

## Security

Report security vulnerabilities to: [team@example.com](mailto:team@example.com)

See [SECURITY.md](SECURITY.md) for our security policy.

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## Acknowledgments

- **HCD (HyperConverged Database)** by DataStax
- **JanusGraph** - Open-source graph database
- **Apache TinkerPop** - Graph computing framework

---

## Support

- **Issues**: [GitHub Issues](https://github.com/davidleconte/hcd-janusgraph/issues)
- **Discussions**: [GitHub Discussions](https://github.com/davidleconte/hcd-janusgraph/discussions)
- **Email**: <team@example.com>

---

**Version**: 2.0.0
**Status**: ✅ Production-ready (Grade: A+, 99/100)
**Last Updated**: 2026-02-07
**Production Readiness**: All phases complete - 670+ tests, 82% coverage

---

**Signature**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
