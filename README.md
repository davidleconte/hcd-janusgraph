# HCD + JanusGraph Containerized Stack

**File**: README.md
**Created**: 2026-01-28T10:36:00.123
**Last Updated**: 2026-02-18
**Last Verified**: 2026-02-18
**Applies To**: Podman-based local deployment (`podman-compose`) with `COMPOSE_PROJECT_NAME=janusgraph-demo`
**Authoritative Status**: [docs/project-status.md](docs/project-status.md)
**Author**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

---

## Overview

Production-ready containerized stack combining **HyperConverged Database (HCD) 1.2.3** with **JanusGraph** for scalable graph database operations. Fully integrated with Jupyter Lab, monitoring (Prometheus/Grafana), and visualization tools.

### Key Features

✅ **Production-Ready**: Health checks, resource limits, graceful shutdown
✅ **Security Hardened**: SSL/TLS encryption, HashiCorp Vault integration, secrets management
✅ **Advanced Monitoring**: Prometheus + Grafana + AlertManager + JanusGraph metrics exporter
✅ **Automated CI/CD**: GitHub Actions workflows for testing and deployment
✅ **Comprehensive Testing**: Current verified test counts and readiness evidence are maintained in [docs/project-status.md](docs/project-status.md)
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

**Option A: Conda + uv (Recommended)**

```bash
# Create environment from file
conda env create -f environment.yml

# Activate
conda activate janusgraph-analysis

# Install dependencies (mandatory package manager: uv)
uv pip install -r requirements.txt
```

**Option B: uv virtual environment (no conda)**

```bash
# Create virtual environment and install
uv venv --python 3.11
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

**Emergency fallback only (when uv is unavailable): pip**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Deterministic Full Demo Pipeline (MBP Pro)

### Canonical deterministic command (CI-equivalent)

Use this command to run the full deterministic setup + notebook proof with status JSON:

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate janusgraph-analysis
export PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd-root}"
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

Direct pipeline invocation remains available:

```bash
./scripts/testing/run_demo_pipeline_repeatable.sh --skip-notebooks
./scripts/testing/run_demo_pipeline_repeatable.sh --skip-data-generators
./scripts/testing/run_demo_pipeline_repeatable.sh --skip-graph-seed
./scripts/testing/run_demo_pipeline_repeatable.sh --skip-preflight
./scripts/testing/run_demo_pipeline_repeatable.sh --skip-deploy
./scripts/testing/run_demo_pipeline_repeatable.sh --dry-run
```

Outputs land under `exports/<RUN_ID>/` and include:

```bash
preflight.log
podman_isolation.log
deploy.log
health.log
seed_graph.log
notebooks.log
notebook_run_report.tsv
data_generators_smoke.log
services_snapshot.log
runtime_package_fingerprint.log
runtime_package_fingerprint.txt
notebook_determinism_contracts.log
pipeline_summary.txt
```

`notebook_run_report.tsv` includes notebook-level timeout/exit-code/error-cell metrics.
`services_snapshot.log` captures container status/ports and startup timestamps for audit evidence.
`runtime_package_fingerprint.txt` captures deterministic Jupyter runtime package/ABI fingerprint evidence.

Force a specific run id with:

```bash
DEMO_PIPELINE_RUN_ID=demo-2026-02-16 ./scripts/testing/run_demo_pipeline_repeatable.sh
```

For an already-running stack (useful during demos/validation), use:

```bash
./scripts/testing/run_demo_pipeline_repeatable.sh \
  --skip-preflight \
  --skip-deploy
```

### Determinism controls in this pipeline

1. **Preflight gates first**
   - Environment and Podman isolation checks run before deployment.
2. **Bounded execution**
   - Notebook total runtime and per-cell runtime are capped.
   - On timeout, failing notebooks are isolated and flagged.
3. **Repeatable inputs**
   - Fixed seed (`DEMO_SEED`) and fixed output root (`DEMO_PIPELINE_RUN_ID`).
   - Post-run check for notebook output cells of type `error`.
   - Optional demo graph auto-seed step (`seed_demo_graph.sh`) ensures a deterministic dataset
     exists before notebook execution.

### Data generator / notebook impact map

Data generators are shared modules across notebooks; they are configured with different parameters per notebook.

| Notebook | Main data path | Services required | Failure impact |
|---|---|---|---|
| `01_Sanctions_Screening_Demo.ipynb` | Core/person data paths | JanusGraph, HCD | Empty sanctions dataset |
| `02_AML_Structuring_Detection_Demo.ipynb` | Core + event + pattern data | JanusGraph, HCD | Pattern injection mismatch |
| `03_Fraud_Detection_Demo.ipynb` | Core + event data | JanusGraph, HCD | Missing fraud signals |
| `04_Customer_360_View_Demo.ipynb` | Core relationship graph | JanusGraph, HCD | Broken entity links |
| `05_Advanced_Analytics_OLAP_Demo.ipynb` | Analytical graph queries | JanusGraph | Query shape drift |
| `06_TBML_Detection_Demo.ipynb` | Pattern + transaction flow | JanusGraph, OpenSearch (optional) | Detection window drift |
| `07_Insider_Trading_Detection_Demo.ipynb` | Pattern + behavior data | JanusGraph | Missing pattern seeds |
| `08_UBO_Discovery_Demo.ipynb` | UBO + ownership graph | JanusGraph | Missing owner/beneficiary fields |
| `09_API_Integration_Demo.ipynb` | Seeded graph + API calls | JanusGraph, HCD, API surface | API contract mismatch |
| `10_Integrated_Architecture_Demo.ipynb` | Full architecture walkthrough | JanusGraph, HCD, OpenSearch, Pulsar | Service dependency timing |
| `11_Streaming_Pipeline_Demo.ipynb` | Streaming orchestrator + Pulsar topics + consumers | JanusGraph, HCD, OpenSearch, Pulsar | Topic routing / consumer lag |
| Exploratory notebooks | Depends on selected demo path | Same as selected demo | Notebook-specific |

### How to read the output

1. `preflight.log` and `podman_isolation.log`: startup gating.
2. `health.log`: confirm storage + traversal health before notebooks.
3. `seed_graph.log`: ensures minimal required graph dataset is present.
4. `notebook_run_report.tsv`: every notebook should be `PASS`.
5. `data_generators_smoke.log`: generator stability smoke test status.
6. `pipeline_summary.txt`: one-command post-run summary.

### Deterministic full live verification (recommended)

Use this command on a running stack when you need one complete, auditable end-to-end pass:

```bash
export DEMO_PIPELINE_RUN_ID=demo-live-$(date -u +%Y%m%dT%H%M%SZ)
export PODMAN_CONNECTION=<your-podman-connection>
export COMPOSE_PROJECT_NAME=janusgraph-demo

./scripts/testing/run_demo_pipeline_repeatable.sh \
  --skip-preflight \
  --skip-data-generators
```

`--skip-preflight` is useful when ports are intentionally occupied by your already-running demo stack; it still records all health/notebook artifacts and validates notebook results.

### Service health snapshot for evidence capture

After or during verification:

```bash
podman --remote ps --filter "name=janusgraph-demo_" --format "table {{.Names}} {{.Status}}"
podman --remote inspect janusgraph-demo_jupyter_1 --format "Status={{.State.Status}} StartedAt={{.State.StartedAt}}"
scripts/testing/check_graph_counts.sh
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

### Business Documentation

| Document | Description |
|----------|-------------|
| **[Business Documentation Index](docs/business/README.md)** | Complete business documentation navigation |
| **[Executive Summary](docs/business/executive-summary.md)** | 1-page investment overview (599% ROI, 1.2-month payback) |
| **[Comprehensive Business Case](docs/business/comprehensive-business-case.md)** | Complete investment justification with financial analysis |
| **[TCO Analysis](docs/business/tco-analysis.md)** | 3-year cost breakdown ($1.38M total) |
| **[ROI Calculator](docs/business/roi-calculator.md)** | Financial returns analysis ($8.3M NPV, 985% IRR) |
| **[Business User Guide](docs/business/business-user-guide.md)** | Complete user guide with 6 banking use cases |
| **[Banking & Financial Services Guide](docs/business/banking-financial-services-guide.md)** | Industry-specific use cases and compliance |

### Architecture Documentation

| Document | Description |
|----------|-------------|
| **[System Architecture](docs/architecture/system-architecture.md)** | Logical component architecture and data flow |
| **[Deployment Architecture](docs/architecture/deployment-architecture.md)** | Container orchestration, networking, and deployment topology |
| **[Podman Isolation Architecture](docs/architecture/podman-isolation-architecture.md)** | Five-layer isolation model and project boundaries |
| **[Streaming Architecture](docs/architecture/streaming-architecture.md)** | Pulsar-based event streaming architecture |

### Production Readiness

| Document | Description |
|----------|-------------|
| **[Production Readiness Audit](docs/implementation/production-readiness-audit-2026.md)** | Comprehensive system audit (historical baseline) |
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
| **[Compliance Certifications Portfolio](docs/business/compliance-certifications-portfolio.md)** | GDPR, SOC 2, BSA/AML, PCI DSS (98/100 score) |
| **[Risk Management Framework](docs/business/risk-management-framework.md)** | 77 risks identified, 100% mitigation |
| **[Data Governance Framework](docs/business/data-governance-framework.md)** | Data quality, security, privacy (96.5/100 score) |

### Operations

| Document | Description |
|----------|-------------|
| **[Operations Runbook](docs/operations/operations-runbook.md)** | Day-to-day operations guide |
| **[Monitoring Guide](docs/operations/monitoring-guide.md)** | Monitoring and alerting setup |
| **[Backup Procedures](docs/operations/backup-procedures.md)** | Backup and restore procedures |
| **[SLA Documentation](docs/business/sla-documentation.md)** | Service level commitments (99.9% availability, <200ms response) |
| **[Capacity Planning Guide](docs/business/capacity-planning-guide.md)** | 12-month forecast and 27% cost optimization |
| **[Business Continuity & DR Plan](docs/business/business-continuity-disaster-recovery-plan.md)** | BC/DR procedures (4-hour RTO, 1-hour RPO) |
| **[Business Value Dashboard](docs/business/business-value-dashboard.md)** | Real-time metrics and KPIs for all stakeholders |

---

## Demo Determinism and Generator Impact

### Simple mental model

Think of data generators like a shared kitchen:
- **Generators are shared tools** (`PersonGenerator`, `TransactionGenerator`, `CompanyGenerator`, ...).
- **Notebooks are recipes** that use some of those tools.
- If you change one generator, every recipe that uses that generator can change.

So: not one generator per notebook, but many notebooks can use the same generator family.

### What this means in this project (now)

| Notebook | Direct generator usage | Shared generator impact surface |
|----------|-----------------------|-------------------------------|
| `banking/notebooks/11_Streaming_Pipeline_Demo.ipynb` | `StreamingOrchestrator`, `StreamingConfig`, `EntityEvent` factories | Uses `MasterOrchestrator` and all core/event/pattern generators through one shared path (`banking/data_generators/orchestration/master_orchestrator.py`) |
| `banking/notebooks/10_Integrated_Architecture_Demo.ipynb` | `create_person_event` | Uses `banking/streaming/events.py` mapping and topic routing only |
| Other banking demos | No direct data generator imports | Usually read/consume already-loaded/served data; any core generator change only impacts them when shared orchestrator services are used upstream |

### Notebook #11 impact and stability

- Notebook 11 is special because it **creates and publishes an end-to-end synthetic data stream** in one run.
- It is deterministic by default when you keep `seed=42`, but non-deterministic effects can still come from runtime state:
  - temporary folders and file paths,
  - service availability (real Pulsar vs mock producer branch),
  - timing and retries from external services.

### Repeatable live pipeline (implemented)

Use:

```bash
cd /Users/david.leconte/Documents/Work/Demos/hcd-tarball-janusgraph
./scripts/testing/run_notebooks_live_repeatable.sh
```

What it enforces for demo runs:

1. Fixed execution shape
   - stable run id: `DEMO_RUN_ID`
   - stable random seed: `DEMO_SEED` (default `42`)
   - stable hash seed: `PYTHONHASHSEED=0`
   - optional mock-only streaming mode: `DEMO_FORCE_MOCK_PULSAR=1` (forces deterministic mock producer in Notebook 11)

2. Deterministic runtime boundaries
   - notebook-level timeout: `DEMO_NOTEBOOK_TOTAL_TIMEOUT` (default `420s`)
   - per-cell timeout: `DEMO_NOTEBOOK_CELL_TIMEOUT` (default `180s`)

3. Post-run validation
   - each executed notebook is checked for `output_type: "error"`
   - a consolidated report is written to `exports/<run_id>/notebook_run_report.tsv`

Example (full control):

```bash
DEMO_RUN_ID=stable-2026-02-16 \
DEMO_SEED=42 \
DEMO_FORCE_MOCK_PULSAR=1 \
DEMO_NOTEBOOK_TOTAL_TIMEOUT=600 \
DEMO_NOTEBOOK_CELL_TIMEOUT=200 \
PODMAN_CONNECTION=<your-podman-connection> \
./scripts/testing/run_notebooks_live_repeatable.sh
```

This gives you a strong, repeatable demo baseline without touching generator logic.

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

Report security vulnerabilities via: [GitHub private security advisory](https://github.com/davidleconte/hcd-janusgraph/security/advisories/new)

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
- **Owner**: <https://github.com/davidleconte>

---

**Version**: 2.0.0
**Status**: See [docs/project-status.md](docs/project-status.md) for current verified readiness.
**Last Updated**: 2026-02-07
**Production Readiness**: Current verified metrics are centralized in [docs/project-status.md](docs/project-status.md).

---

**Signature**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

## Codex Canonical Deterministic Command (P0 Governance)

For deterministic full setup + proof runs, use this canonical command path:

```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

Optional passthrough examples:

```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --dry-run
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --skip-notebooks
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --skip-preflight --skip-deploy
```

This wrapper is governance-only and delegates execution to `scripts/testing/run_demo_pipeline_repeatable.sh`.

## Codex CI Deterministic Gate

CI now includes a dedicated deterministic proof workflow:

- Workflow: `.github/workflows/deterministic-proof.yml`
- Required command path: `scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json`
- Artifacts: `deterministic-status.json`, `notebook_run_report.tsv`, `pipeline_summary.txt`, determinism/runtime logs

Repository admins must mark `Deterministic Proof / deterministic-proof` as a required branch-protection check on `master`/`main`.
