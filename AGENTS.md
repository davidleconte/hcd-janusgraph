# AGENTS.md

**Last Verified**: 2026-02-20
**Applies To**: This repository runtime and contributor workflows
**Authoritative Status**: [docs/project-status.md](docs/project-status.md)

This file provides guidance to agents when working with code in this repository.

---

## Operational Control Summary (Authoritative)

### 1) Authoritative commands

Use the commands below as the primary operational source of truth.

| Task | Authoritative Command |
|---|---|
| Deterministic full setup + proof | `bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json` |
| Repeatable pipeline (direct) | `bash scripts/testing/run_demo_pipeline_repeatable.sh` |
| Deploy full stack | `cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh` |
| Stop full stack | `cd config/compose && bash ../../scripts/deployment/stop_full_stack.sh` |
| Local CI-equivalent quality gates | See `.github/workflows/quality-gates.yml` and run equivalent commands in order |
| Podman preflight/isolation checks | `bash scripts/validation/preflight_check.sh --strict` and `bash scripts/validation/validate_podman_isolation.sh --strict` |

### 2) Execution profiles

| Profile | Purpose | Command/Entry Point |
|---|---|---|
| `dev-fast` | Quick local work without full proof | `bash scripts/testing/run_demo_pipeline_repeatable.sh --skip-notebooks` |
| `deterministic-proof` | Canonical deterministic verdict | `bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json` |
| `ci-quality` | Lint/type/coverage/doc quality gates | `.github/workflows/quality-gates.yml` equivalent local commands |
| `integration-full` | Full integration test pass with live services | `pytest tests/integration/ -v` after deploy and Vault setup |

### 3) Determinism contract

Deterministic pass criteria:
- Wrapper status file exists at `exports/deterministic-status.json`.
- `exit_code` is `0`.
- Notebook report exists and all notebooks are `PASS`.
- Determinism artifact verification passes (checksums/baseline behavior).

Gate code semantics (from pipeline behavior):
- `G0_PRECHECK`: preflight/isolation failure
- `G2_CONNECTION`: no reachable Podman connection
- `G3_RESET`: deterministic reset failure
- `G5_DEPLOY_VAULT`: deploy/readiness/Vault-related failure
- `G6_RUNTIME_CONTRACT`: runtime contract/fingerprint failure
- `G7_SEED`: graph seed/validation failure
- `G8_NOTEBOOKS`: notebook run/report failure
- `G9_DETERMINISM`: deterministic artifact mismatch/failure

### 4) Secrets and test runtime contract

Mandatory for auth/session-sensitive tests and runtime:
- `api_jwt_secret` must be configured (runtime enforces fail-fast).

Recommended test runtime exports:
```bash
export API_JWT_SECRET="test-jwt-secret-not-for-production"
export api_jwt_secret="$API_JWT_SECRET"
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="${VAULT_ROOT_TOKEN:-}"
```

If running full integration:
```bash
export PULSAR_INTEGRATION=1
```

### 5) Environment repair playbook (known breakages)

If ABI mismatch appears (`numpy.dtype size changed`):
```bash
conda activate janusgraph-analysis
uv pip install --force-reinstall "numpy==2.2.6" "pandas==2.2.3"
python -c "import numpy,pandas,sklearn; print(numpy.__version__, pandas.__version__, sklearn.__version__)"
```

If missing runtime deps for tests:
```bash
conda activate janusgraph-analysis
uv pip install email-validator slowapi opentelemetry-exporter-jaeger
```

### 6) Docs authority policy

Authoritative runtime docs:
- `AGENTS.md`
- `README.md`
- `QUICKSTART.md`
- `docs/project-status.md`
- `docs/prod-secure-overrides.md`
- canonical scripts under `scripts/deployment/` and `scripts/testing/`

Legacy/historical docs must be explicitly marked non-authoritative and/or archived.

### 7) Skill invocation examples

Recommended chains:
1. Deterministic incident: `deterministic-proof-orchestrator` -> `podman-wxd-runtime-doctor` -> `dependency-abi-compat-guard`
2. Quality incident: `quality-gate-repair-assistant` -> `auth-secrets-hardening` -> `notebook-determinism-enforcer`
3. Business validation: `business-scenario-regression` -> `banking-compliance-evidence-packager` -> `docs-authority-enforcer`

### 8) Change safety rules

- Prefer minimal, deterministic-safe patches first.
- Separate operational fixes from broad formatting sweeps where possible.
- For notebook edits, preserve business semantics and only remove nondeterminism.
- Do not weaken security/startup validation to make tests pass; fix test runtime contract instead.

### 9) Owner and review cadence

| Section | Owner | Review Cadence |
|---|---|---|
| Authoritative Commands | Platform Engineering | Monthly |
| Determinism Contract | Platform + QA | Weekly |
| Secrets/Test Contract | Security + API Owners | Weekly |
| Repair Playbook | Platform Engineering | Monthly |
| Docs Authority Policy | Docs + Platform | Monthly |
| Skills Catalog | Platform Engineering | Monthly |

## Environment Setup

### Conda Environment (REQUIRED)

**CRITICAL:** Always activate the correct conda environment before running Python commands:

```bash
# Activate the janusgraph-analysis environment
conda activate janusgraph-analysis

# Verify activation
which python  # Should show conda env path
python --version  # Should show Python 3.11+
```

**All Python commands in this document assume the conda environment is activated.**

### Conda Environment Variables (Pre-configured)

The `janusgraph-analysis` environment has the following variables pre-configured:

| Variable | Value | Purpose |
|----------|-------|---------|
| `JANUSGRAPH_PORT` | `18182` | JanusGraph Gremlin server port (podman mapped port) |
| `JANUSGRAPH_USE_SSL` | `false` | Disable SSL for local development |
| `OPENSEARCH_USE_SSL` | `false` | Disable SSL for OpenSearch in dev (security plugin disabled) |

These are automatically set when you activate the environment. To verify:

```bash
conda activate janusgraph-analysis
echo $JANUSGRAPH_PORT      # Should show: 18182
echo $JANUSGRAPH_USE_SSL   # Should show: false
echo $OPENSEARCH_USE_SSL   # Should show: false
```

To modify these values (if needed):

```bash
conda env config vars set JANUSGRAPH_PORT=18182 JANUSGRAPH_USE_SSL=false OPENSEARCH_USE_SSL=false
conda deactivate && conda activate janusgraph-analysis
```

### Additional Environment Variables (for full test suite)

The following environment variables are **required** to run the complete integration test suite:

| Variable | Value | Purpose |
|----------|-------|---------|
| `VAULT_ADDR` | `http://localhost:8200` | HashiCorp Vault address |
| `VAULT_TOKEN` | *(from `.vault-keys`)* | Vault root token for authentication |
| `PULSAR_INTEGRATION` | `1` | Enable real Pulsar integration tests |

**Vault credentials** are stored in `.vault-keys` (gitignored). After Vault initialization:

```bash
# Source Vault credentials
source .vault-keys
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=$VAULT_ROOT_TOKEN
export PULSAR_INTEGRATION=1

# Run full integration suite (202 tests, 0 skipped)
conda run -n janusgraph-analysis PYTHONPATH=. VAULT_ADDR=$VAULT_ADDR VAULT_TOKEN=$VAULT_TOKEN PULSAR_INTEGRATION=1 \
  python -m pytest tests/integration/ -v --no-cov --timeout=120
```

### Package Management (MANDATORY: uv)

**CRITICAL:** This project **REQUIRES** `uv` for all Python package management operations. Do not use `pip` directly.

#### Why uv?
- **10-100x faster** than pip
- Deterministic dependency resolution
- Better conflict detection
- Fully compatible with pip requirements.txt

#### Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Verify installation
uv --version
```

#### Environment Setup (MANDATORY)

**Option A: Conda + uv (Recommended)**

```bash
# Create conda environment
conda env create -f environment.yml
conda activate janusgraph-analysis

# Install packages with uv (MANDATORY)
uv pip install -r requirements.txt

# Verify
uv pip list
```

**Option B: uv venv (Pure Python)**

```bash
# Create virtual environment with uv
uv venv --python 3.11

# Activate
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
uv pip install -r requirements.txt
```

#### Adding Packages (MANDATORY: uv)

```bash
# Install packages with uv (MANDATORY)
uv pip install package-name

# Install with version constraint
uv pip install "package-name>=1.0.0,<2.0.0"

# Install from requirements file
uv pip install -r requirements.txt

# Install development dependencies
uv pip install -e ".[dev]"
```

#### Emergency Fallback (pip)

**ONLY use pip if uv is unavailable and you cannot install it:**

```bash
# Emergency fallback (NOT RECOMMENDED)
pip install package-name

# Document why uv couldn't be used
echo "Used pip because: [reason]" >> .pip-usage-log
```

### Container Orchestration (MANDATORY: Podman)

**CRITICAL:** This project **REQUIRES** `podman` and `podman-compose` for all container operations. Docker and docker-compose are **NOT SUPPORTED**.

#### Why Podman?

- **Rootless by default** - Better security, no daemon running as root
- **Daemonless architecture** - No single point of failure
- **Pod support** - Kubernetes-compatible pod management
- **Docker CLI compatible** - Same commands, better architecture

#### Installation

**macOS:**

```bash
# Install Podman Desktop (includes podman-compose)
brew install podman-desktop

# Or install separately
brew install podman podman-compose

# Initialize Podman machine
podman machine init --cpus 4 --memory 8192 --disk-size 50
podman machine start

# Verify
podman --version
podman-compose --version
```

**Linux:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y podman podman-compose

# RHEL/Fedora
sudo dnf install -y podman podman-compose

# Verify
podman --version
podman-compose --version
```

#### Podman Machine Configuration

**MANDATORY:** Configure Podman machine with sufficient resources:

```bash
# Check current machine
podman machine list

# Stop existing machine (if needed)
podman machine stop

# Remove existing machine (if reconfiguring)
podman machine rm

# Create new machine with proper resources
podman machine init \
  --cpus 4 \
  --memory 8192 \
  --disk-size 50 \
  --now

# Verify machine is running
podman machine list
# Should show: Running

# Test connection
podman ps
```

#### Deployment Commands (MANDATORY)

**ALWAYS use podman-compose, NEVER docker-compose:**

```bash
# Deploy full stack (CORRECT)
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d

# Check status (CORRECT)
podman ps --filter "label=project=janusgraph-demo"

# View logs (CORRECT)
podman logs janusgraph-demo_hcd-server_1

# Stop services (CORRECT)
podman-compose -p janusgraph-demo -f docker-compose.full.yml down
```

#### Docker Compatibility (DEPRECATED)

**DO NOT USE DOCKER COMMANDS:**

```bash
# ❌ WRONG - Do not use docker
docker ps
docker-compose up

# ✅ CORRECT - Use podman
podman ps
podman-compose up
```

**If you have Docker installed, create aliases to prevent accidental use:**

```bash
# Add to ~/.bashrc or ~/.zshrc
alias docker='echo "❌ Use podman instead of docker" && false'
alias docker-compose='echo "❌ Use podman-compose instead of docker-compose" && false'
```

#### Podman Isolation (MANDATORY)

**CRITICAL:** Always use project name for isolation:

```bash
# MANDATORY: Set project name
export COMPOSE_PROJECT_NAME="janusgraph-demo"

# Deploy with project name
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d

# This ensures:
# - Containers: janusgraph-demo_hcd-server_1
# - Networks: janusgraph-demo_hcd-janusgraph-network
# - Volumes: janusgraph-demo_hcd-data
```

**See:** [PODMAN_ISOLATION.md](.bob/rules-plan/PODMAN_ISOLATION.md) for complete isolation requirements.

### CLI Tools & Consoles

The following CLI tools and consoles are available for interacting with services:

| Tool | Container | Access |
|------|-----------|--------|
| **CQLSH** (HCD/Cassandra) | `cqlsh-client` | `podman exec -it janusgraph-demo_cqlsh-client_1 cqlsh hcd-server` |
| **Gremlin Console** | `gremlin-console` | `podman exec -it janusgraph-demo_gremlin-console_1 bin/gremlin.sh` |
| **Pulsar CLI** | `pulsar-cli` | `podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin ...` |
| **OpenSearch Dashboards** | `opensearch-dashboards` | <http://localhost:5601> |

#### CQLSH (Cassandra Query Language Shell)

```bash
# Interactive CQL session
podman exec -it janusgraph-demo_cqlsh-client_1 cqlsh hcd-server

# Run CQL command directly
podman exec janusgraph-demo_cqlsh-client_1 cqlsh hcd-server -e "DESCRIBE KEYSPACES"
podman exec janusgraph-demo_cqlsh-client_1 cqlsh hcd-server -e "SELECT * FROM janusgraph.edgestore LIMIT 5"
```

#### Gremlin Console (JanusGraph Graph Queries)

```bash
# Start interactive Gremlin console
podman exec -it janusgraph-demo_gremlin-console_1 bin/gremlin.sh

# Inside Gremlin console:
:remote connect tinkerpop.server conf/remote-connect.properties
:remote console
g.V().count()
g.V().hasLabel('Person').limit(5).valueMap()
```

#### Pulsar CLI (Message Streaming)

```bash
# List topics
podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin topics list public/banking

# List namespaces
podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin namespaces list public

# Check topic stats
podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin topics stats persistent://public/banking/persons-events

# Consume messages (debugging)
podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-client consume -s test-sub persistent://public/banking/persons-events -n 5
```

#### OpenSearch Dashboards (Web UI)

Access at <http://localhost:5601> for:

- Index management
- Query console (Dev Tools)
- Visualizations
- Index pattern creation

### Podman/Docker Deployment (REQUIRED)

**CRITICAL:** Always use project name to ensure isolation from other projects on the same Podman machine:

```bash
# MUST run from config/compose directory
cd config/compose

# Deploy with project name for isolation
COMPOSE_PROJECT_NAME="janusgraph-demo"
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d

# This automatically prefixes all resources:
# - Containers: janusgraph-demo_hcd-server_1
# - Networks: janusgraph-demo_hcd-janusgraph-network
# - Volumes: janusgraph-demo_hcd-data
```

**IMPORTANT:** The compose file uses relative paths for Dockerfiles. You MUST run podman-compose from the `config/compose` directory, otherwise Dockerfile paths will be incorrect.

**Why This Matters:**

- Prevents name conflicts with other projects
- Isolates volumes (prevents data mixing)
- Isolates networks (prevents cross-project communication)
- Allows multiple projects on same Podman machine

**Verification:**

```bash
# Check isolation
podman ps --format "{{.Names}}" | grep janusgraph-demo
podman network ls | grep janusgraph-demo
podman volume ls | grep janusgraph-demo
```

**See:** [`config/compose/docker-compose.full.yml`](config/compose/docker-compose.full.yml) for complete analysis

---

## Quick Reference

### Essential Commands

```bash
# ALWAYS activate conda environment first
conda activate janusgraph-analysis

# Deploy full stack (MUST run from config/compose)
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh

# Run all tests (requires conda env)
pytest tests/ -v --cov=src --cov=banking

# Run data generator tests (requires conda env)
cd banking/data_generators/tests && ./run_tests.sh [smoke|unit|integration|performance|coverage]

# Generate security certificates
./scripts/security/generate_certificates.sh

# Initialize Vault
./scripts/security/init_vault.sh

# Run validation checks before deployment
./scripts/validation/preflight_check.sh

# Run with auto-fix for common issues
./scripts/validation/preflight_check.sh --fix
```

### Validation Scripts

**Run before every deployment:**

```bash
# Full preflight check (recommended)
./scripts/validation/preflight_check.sh

# Auto-fix common issues
./scripts/validation/preflight_check.sh --fix

# Individual checks
./scripts/validation/check_python_env.sh        # Python environment
./scripts/validation/validate_podman_isolation.sh  # Podman isolation
```

### Project Status

- **Project Status:** See `docs/project-status.md` for current verified readiness, test counts, and evidence links.
- **Verification Metrics:** Maintained in `docs/project-status.md` (do not duplicate numeric metrics in this file).
- **Security:** Enterprise-grade (SSL/TLS, Vault, Audit Logging, Startup Validation)
- **Compliance:** GDPR, SOC 2, BSA/AML, PCI DSS ready
- **CI Quality Gates:** 8 workflows (coverage, docstrings, security, types, lint)
- **Streaming:** Pulsar integration with timeout-protected flush/close (5s defaults)

---

## Project-Specific Commands

### Deployment

**Deploy must run from config/compose directory**:

```bash
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
```

**Stop full stack**:

```bash
cd config/compose && bash ../../scripts/deployment/stop_full_stack.sh
```

**Deploy with monitoring**:

```bash
./scripts/monitoring/deploy_monitoring.sh
```

### Testing

**IMPORTANT:** All test commands require conda environment activation:

```bash
conda activate janusgraph-analysis
```

**Data generator tests require specific directory**:

```bash
conda activate janusgraph-analysis
cd banking/data_generators/tests && ./run_tests.sh [smoke|unit|integration|performance|coverage]
```

**Single test execution** (pytest must be run from tests directory):

```bash
conda activate janusgraph-analysis
cd banking/data_generators/tests
pytest test_core/test_person_generator.py::TestPersonGeneratorFunctional::test_required_fields_present -v
```

**Integration tests** (requires services running):

```bash
# Activate conda environment
conda activate janusgraph-analysis

# Deploy services first
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
sleep 90  # Wait for services to be ready

# Run integration tests
cd ../..
pytest tests/integration/ -v
```

**Run all tests with coverage**:

```bash
conda activate janusgraph-analysis
pytest -v --cov=src --cov=banking --cov-report=html --cov-report=term-missing
```

**Install test dependencies with uv**:

```bash
conda activate janusgraph-analysis
uv pip install pytest pytest-cov pytest-mock pytest-asyncio pytest-benchmark
```

### Security

**Generate SSL/TLS certificates**:

```bash
./scripts/security/generate_certificates.sh
```

**Initialize HashiCorp Vault**:

```bash
./scripts/security/init_vault.sh
```

**Access Vault secrets**:

```bash
source ./scripts/security/vault_access.sh
podman exec -e VAULT_TOKEN=$VAULT_APP_TOKEN vault-server vault kv get janusgraph/admin
```

---

## Critical Non-Obvious Patterns

### Data Generators

**Generators are fully deterministic with seeds** — all generators inherit from BaseGenerator. When a seed is provided, three mechanisms ensure identical output across runs:

1. `Faker.seed(seed)` + `random.seed(seed)` for all random values
2. `reset_counter(0)` resets the seeded UUID counter (SHA-256 based)
3. All timestamps use `REFERENCE_TIMESTAMP = 2026-01-15T12:00:00Z` instead of `datetime.now()`

```python
generator = PersonGenerator(seed=42)  # Fully deterministic output
```

**IMPORTANT: Always set `communication_count` in test configs** — `GenerationConfig` defaults to `communication_count=200`. For large-scale tests, set explicitly:

```python
config = GenerationConfig(
    seed=42,
    person_count=10,
    communication_count=10,  # Override default 200 for fast tests
)
```

**Pattern generators require ALL entity lists** - cannot inject patterns without complete context:

```python
pattern_gen.inject_pattern(
    persons=persons,      # Required
    companies=companies,  # Required
    accounts=accounts,    # Required
    trades=trades,        # Required
    communications=communications  # Required
)
```

### Testing

**Test fixtures add parent to sys.path** - conftest.py line 18 modifies path, don't duplicate:

```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

**Integration tests skip if services unavailable** - tests use pytest.skip() when JanusGraph/OpenSearch not running, not pytest.mark.skipif

**Pytest markers defined in conftest.py** - use @pytest.mark.slow, @pytest.mark.integration, @pytest.mark.benchmark

**Test coverage requires --cov flag** - pyproject.toml sets default coverage options but must run from project root for correct paths

### Docker & Deployment

**Docker compose files use relative context** - dockerfile paths in compose files are relative to compose file location, not project root:

```yaml
context: .  # This is config/compose/, not project root
dockerfile: ../../docker/hcd/Dockerfile  # Must go up two levels
```

**Makefile deploy changes directory** - deploy target CDs into config/compose before running script:

```make
deploy:
 @cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
```

**HCD JMX ports intentionally not exposed** - security requirement, must use SSH tunnel:

```yaml
# - "7199:7199"  # JMX - Use SSH tunnel instead
```

### Security

**Default passwords MUST be changed** - never use 'changeit' or placeholder passwords in production:

```bash
# .env.example contains placeholders - MUST be replaced
JANUSGRAPH_PASSWORD=YOUR_SECURE_PASSWORD_HERE_MINIMUM_12_CHARACTERS  # CHANGE THIS
HCD_KEYSTORE_PASSWORD=changeit  # CHANGE THIS
```

**Vault secrets are stored in KV v2** - access paths differ from storage paths:

```bash
# CLI access path
vault kv get janusgraph/admin

# Actual storage path (internal)
janusgraph/data/admin
```

---

## Code Style (Non-Standard)

### Python Standards

- **Line length:** 100 (not 88 or 120)
- **Python version:** 3.11 required (not 3.9+)
- **Type hints:** Required (disallow_untyped_defs = true in mypy config)
- **Excluded from linting:** Notebooks and hcd-1.2.3 (see pyproject.toml extend-exclude)

### Code Quality Requirements

- All functions must have type hints
- All public functions must have docstrings
- Use Black formatter with line length 100
- Use isort for import sorting
- No hardcoded credentials (use environment variables or Vault)

### Code Quality Tools

**Pre-commit hooks** (`.pre-commit-config.yaml`):

```bash
uv pip install pre-commit && pre-commit install
pre-commit run --all-files
```

**Code analysis with uv**:

```bash
uv tool run vulture src/ banking/ --min-confidence 80   # Dead code
uv tool run radon cc src/ banking/ -s -a                # Complexity
uv tool run bandit -r src/ banking/ -ll                 # Security scan
uv tool run pip-audit                                   # Dependency vulnerabilities
uv tool run autoflake --in-place --remove-all-unused-imports --recursive src/ banking/
```

**CI Quality Gates** (`.github/workflows/quality-gates.yml`):

- Test coverage ≥70% (current enforced gate)
- Docstring coverage ≥80%
- Security scan (bandit)
- Type checking (mypy)
- Code linting (ruff)

**Startup Validation** (`src/python/utils/startup_validation.py`):
Rejects default passwords: `changeit`, `password`, `YOUR_*_HERE`, `PLACEHOLDER`

---

## Banking Module Structure

### Import Patterns

**Synthetic data generators in banking/data_generators/** have specific import pattern:

```python
from banking.data_generators.core import PersonGenerator
from banking.data_generators.orchestration import MasterOrchestrator, GenerationConfig
```

**Compliance modules**:

```python
from banking.compliance.audit_logger import get_audit_logger, AuditEventType
from banking.compliance.compliance_reporter import ComplianceReporter
```

### Module Organization

```
src/python/
├── repository/        # Graph Repository Pattern (centralizes all Gremlin queries)
│   ├── __init__.py
│   └── graph_repository.py   # GraphRepository class (100% test coverage)
├── api/
│   ├── routers/       # Thin HTTP handlers (use GraphRepository, no inline Gremlin)
│   ├── models.py      # Pydantic request/response models
│   └── dependencies.py # Connection management, auth, rate limiting
├── analytics/         # UBO discovery, graph analytics
├── client/            # Low-level JanusGraph client
├── config/            # Centralized pydantic-settings
├── init/              # Schema init & sample data loading
└── utils/             # Resilience, tracing, validation, logging

banking/
├── data_generators/     # Synthetic data generation
│   ├── core/           # Base generators (Person, Company, Account)
│   ├── events/         # Event generators (Transaction, Communication)
│   ├── patterns/       # Fraud/AML pattern injection
│   ├── loaders/        # JanusGraph data loader
│   └── orchestration/  # Master orchestrator
├── compliance/         # Compliance infrastructure
│   ├── audit_logger.py        # Audit logging (30+ event types)
│   └── compliance_reporter.py # Compliance reporting
├── aml/               # Anti-Money Laundering detection
├── fraud/             # Fraud detection
└── streaming/         # Pulsar event streaming
    ├── events.py             # EntityEvent schema
    ├── producer.py           # Event publisher
    ├── graph_consumer.py     # JanusGraph consumer
    ├── vector_consumer.py    # OpenSearch consumer
    ├── dlq_handler.py        # Dead Letter Queue
    └── metrics.py            # Prometheus metrics
```

### Streaming Module

**Streaming module in banking/streaming/** provides Pulsar-based event streaming:

```python
from banking.streaming import StreamingOrchestrator, StreamingConfig
from banking.streaming import EntityProducer, create_person_event

# Using StreamingOrchestrator (recommended)
config = StreamingConfig(
    seed=42,
    person_count=100,
    pulsar_url="pulsar://localhost:6650",
    output_dir=Path("./output")
)
with StreamingOrchestrator(config) as orchestrator:
    stats = orchestrator.generate_all()

# Direct event publishing
producer = EntityProducer(pulsar_url="pulsar://localhost:6650")
event = create_person_event(person_id="p-123", name="John", payload={...})
producer.send(event)
producer.close()
```

**Key streaming patterns:**

- `StreamingConfig` extends `GenerationConfig` - all generator options available
- `use_mock_producer=True` for testing without Pulsar
- Entity IDs are consistent across Pulsar, JanusGraph, and OpenSearch
- Topics: `persons-events`, `accounts-events`, `transactions-events`, etc.

**Environment variables:**

- `PULSAR_URL`: Pulsar broker URL (default: `pulsar://localhost:6650`)
- `OPENSEARCH_USE_SSL`: Set to `false` for local dev

**Testing streaming:**

```bash
# Unit tests
PYTHONPATH=. pytest banking/streaming/tests/ -v

# E2E tests (requires services)
PYTHONPATH=. OPENSEARCH_USE_SSL=false pytest tests/integration/test_e2e_streaming.py -v
```

**Documentation:** See [`banking/streaming/README.md`](banking/streaming/README.md) for full details.

---

## Test Location Convention

Tests are distributed across multiple locations by design:

| Location | Purpose | Run Command |
|----------|---------|-------------|
| `tests/unit/` | Unit tests for `src/python/` modules | `pytest tests/unit/ -v` |
| `tests/integration/` | E2E tests requiring running services | `pytest tests/integration/ -v` |
| `tests/benchmarks/` | Performance benchmarks | `pytest tests/benchmarks/ -v` |
| `tests/performance/` | Load tests | `pytest tests/performance/ -v` |
| `banking/data_generators/tests/` | Generator-specific tests (co-located) | `cd banking/data_generators/tests && ./run_tests.sh` |
| `banking/analytics/tests/` | Analytics module tests (co-located) | `pytest banking/analytics/tests/ -v` |
| `banking/compliance/tests/` | Compliance module tests (co-located) | `pytest banking/compliance/tests/ -v` |
| `banking/streaming/tests/` | Streaming module tests (co-located) | `pytest banking/streaming/tests/ -v` |
| `banking/tests/` | Cross-module banking integration tests | `pytest banking/tests/ -v` |

**Convention:** Infrastructure tests go in `tests/`. Domain-specific tests are co-located with their modules in `banking/*/tests/`. All paths are registered in `pyproject.toml` `[tool.pytest.ini_options].testpaths`.

**Run all tests:** `pytest` (uses testpaths from pyproject.toml)

---

## Testing Gotchas

### Test Execution

**Integration tests require services** - must deploy full stack first:

```bash
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
sleep 90
cd ../.. && pytest tests/integration/ -v
```

**Performance tests are marked as slow**:

```bash
# Skip slow tests
pytest -v -m "not slow"

# Run only slow tests
pytest -v -m "slow"
```

### Test Coverage

Current test/pass/coverage counts are intentionally centralized in [`docs/project-status.md`](docs/project-status.md):

```
Module                          Coverage    Notes
──────────────────────────────────────────────────────
python.config                   98%         ✅ Excellent
python.client                   97%         ✅ Excellent
python.utils                    88%         ✅ Good
python.api                      75%         ✅ Good
data_generators.utils           76%         ✅ Good
streaming                       28%         Integration-tested (202 E2E tests)
aml                             25%         Integration-tested
compliance                      25%         Integration-tested
fraud                           23%         Integration-tested
data_generators.patterns        13%         Pattern injection tested
analytics                        0%         Planned
──────────────────────────────────────────────────────
Integration test status is tracked in [`docs/project-status.md`](docs/project-status.md) and referenced evidence logs.
```

> **Note**: Line coverage (~18%) is lower than test count suggests because
> the codebase includes many infrastructure modules (monitoring, security,
> performance) not yet under unit test. Critical paths (client, config,
> API, streaming E2E) are well-covered.
### Advanced Testing Patterns

**Exception handling tests use custom exception hierarchy** - all exceptions inherit from [`JanusGraphException`](src/python/client/exceptions.py:15):

```python
from src.python.client.exceptions import (
    JanusGraphException,
    ConnectionError,
    QueryError,
    ValidationError
)

# Test exception hierarchy
def test_exception_hierarchy():
    assert issubclass(ConnectionError, JanusGraphException)
    assert issubclass(QueryError, JanusGraphException)
    
# Test structured error information
def test_error_details():
    error = QueryError(
        message="Invalid query",
        query="g.V().invalid()",
        error_code="QUERY_001"
    )
    assert error.query == "g.V().invalid()"
    assert error.error_code == "QUERY_001"
```

**Property-based testing with Hypothesis** - use for testing invariants:

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=1, max_value=1000))
def test_person_generator_count(count):
    """Property: Generator produces exactly N persons."""
    generator = PersonGenerator(seed=42)
    persons = generator.generate(count)
    assert len(persons) == count
    
@given(st.text(min_size=1, max_size=100))
def test_name_validation(name):
    """Property: Valid names are accepted."""
    if name.strip() and not any(c.isdigit() for c in name):
        validator = NameValidator()
        assert validator.validate(name) is True
```

**Performance benchmarking with pytest-benchmark** - establish baselines:

```python
def test_query_performance(benchmark, graph_client):
    """Benchmark: Vertex count query < 100ms."""
    result = benchmark(lambda: graph_client.execute("g.V().count()"))
    assert result < 100  # milliseconds
    
def test_batch_insert_performance(benchmark):
    """Benchmark: 1000 vertices in < 5 seconds."""
    def insert_batch():
        generator = PersonGenerator(seed=42)
        persons = generator.generate(1000)
        loader = JanusGraphLoader()
        loader.load_persons(persons)
    
    result = benchmark(insert_batch)
    assert result < 5.0  # seconds
```

**Mutation testing validates test effectiveness** - use mutmut to verify tests catch bugs:

```bash
# Run mutation testing on specific module
mutmut run --paths-to-mutate=src/python/client/janusgraph_client.py

# Show surviving mutants (tests didn't catch)
mutmut results

# Apply specific mutation to see what changed
mutmut show 5
```

**Performance regression tests track baselines** - see [`tests/benchmarks/test_performance_regression.py`](tests/benchmarks/test_performance_regression.py:1):

```python
@pytest.mark.benchmark(group="vertex-operations")
def test_vertex_count_baseline(benchmark, graph_client):
    """Baseline: Vertex count < 50ms (P95)."""
    result = benchmark(graph_client.count_vertices)
    assert result.stats.mean < 0.050  # 50ms mean
    assert result.stats.max < 0.100   # 100ms max
```

**Test markers for organization** - defined in [`conftest.py`](tests/conftest.py:1):

```python
# Available markers
@pytest.mark.slow          # Long-running tests (>1s)
@pytest.mark.integration   # Requires running services
@pytest.mark.benchmark     # Performance benchmarks
@pytest.mark.mutation      # Mutation testing
@pytest.mark.property      # Property-based tests

# Run specific marker groups
pytest -v -m "not slow"              # Skip slow tests
pytest -v -m "integration"           # Only integration tests
pytest -v -m "benchmark"             # Only benchmarks
pytest -v -m "property or mutation"  # Property or mutation tests
```


---

## Documentation Structure and Standards

### File Naming

**Documentation follows strict organization** - see [`docs/documentation-standards.md`](docs/documentation-standards.md) for complete standards

**File naming convention is kebab-case** - all documentation files use kebab-case:

```
✅ user-guide.md, api-reference.md, phase-8-complete.md
❌ user-guide.md, ApiReference.md, user_guide.md
```

**Exceptions to kebab-case** - only these root-level files use UPPERCASE:

```
README.md, LICENSE, CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, AGENTS.md
```

### Directory Structure

**Documentation directory structure** - organized by purpose, not format:

```
docs/
├── INDEX.md                    # Central navigation (start here)
├── documentation-standards.md  # Standards guide
├── [core-docs].md             # Core documentation
├── api/                        # API documentation
├── architecture/               # Architecture decisions (ADRs)
├── banking/                    # Banking domain docs
│   ├── guides/                # User/developer guides
│   ├── architecture/          # Banking architecture
│   ├── implementation/        # Implementation tracking
│   ├── planning/              # Planning documents
│   └── setup/                 # Setup guides
├── compliance/                 # Compliance documentation
├── implementation/             # Project implementation
│   ├── audits/                # Audit reports
│   ├── phases/                # Phase summaries
│   └── remediation/           # Remediation plans
└── archive/                    # Historical documents
```

### Documentation Requirements

**Every directory must have README.md** - provides overview and navigation:

```markdown
# Directory Name

Brief description of directory purpose.

## Contents
- List of key files
- Subdirectory descriptions

## Related Documentation
- Links to related docs
```

**Central documentation index** - use [`docs/INDEX.md`](docs/INDEX.md) for navigation:

- Role-based navigation (Developers, Operators, Architects, PMs, Compliance)
- Topic-based organization
- Search tips and common queries

**Documentation must include metadata** - all docs should have:

```markdown
# Document Title

**Date:** YYYY-MM-DD
**Version:** X.Y (if applicable)
**Status:** Draft | Active | Deprecated

Brief overview...
```

**Use relative links in documentation** - always use relative paths:

```markdown
✅ [Setup Guide](QUICKSTART.md)
✅ [Banking Docs](banking/README.md)
❌ [Setup](/docs/QUICKSTART.md)  # Absolute path
```

**Code examples must be tested** - all code examples in documentation must:

1. Be tested before inclusion
2. Include context and explanation
3. Show expected output when relevant
4. Handle errors appropriately

---

## Production Readiness

### Current Status

**Overall Status:** See [`docs/project-status.md`](docs/project-status.md) for the current verified baseline.

**Category Scores:**

- Security: 95/100
- Code Quality: 98/100
- Testing: See `docs/project-status.md`
- Documentation: 95/100
- Performance: 85/100
- Maintainability: 95/100
- Deployment: See `docs/project-status.md`
- Compliance: 98/100

### Before Production Deployment

**Critical Items:**

1. Replace all default passwords ('changeit', placeholders)
2. Add startup validation to reject default credentials
3. Complete MFA implementation
4. Schedule external security audit
5. Conduct disaster recovery drill

**Recommended Items:**

1. Document horizontal scaling strategy
2. Complete DR testing documentation
3. Standardize Python version requirements
4. Implement query optimization tools

### Production Checklist

```markdown
- [ ] SSL/TLS certificates generated and installed
- [ ] All default passwords replaced with strong credentials
- [ ] Vault initialized and secrets migrated
- [ ] Monitoring stack deployed (Prometheus, Grafana, AlertManager)
- [ ] Audit logging enabled and tested
- [ ] Backup procedures tested
- [ ] Disaster recovery plan validated
- [ ] External security audit completed
- [ ] Compliance documentation reviewed
- [ ] Operations team trained
```

---

## Compliance & Security

### Audit Logging

**30+ audit event types** covering:

- Authentication (login, logout, failed_auth, MFA)
- Authorization (access_granted, access_denied)
- Data access (query, create, update, delete)
- GDPR requests (access, deletion, portability)
- AML alerts (SAR filing, CTR reporting)
- Security events (incidents, violations)

**Usage example:**

```python
from banking.compliance.audit_logger import get_audit_logger

audit_logger = get_audit_logger()
audit_logger.log_data_access(
    user="analyst@example.com",
    resource="customer:12345",
    action="query",
    result="success",
    metadata={"query": "g.V().has('customerId', '12345')"}
)
```

### Compliance Reporting

**Automated reports for:**

- GDPR Article 30 (Records of Processing Activities)
- SOC 2 Type II (Access Control Reports)
- BSA/AML (Suspicious Activity Reports)
- PCI DSS (Audit Reports)

**Generate reports:**

```python
from banking.compliance.compliance_reporter import generate_compliance_report

report = generate_compliance_report(
    report_type="gdpr",
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 1, 31),
    output_file="/reports/gdpr_january_2026.json"
)
```

---

## Monitoring & Observability

### Metrics Collection

**JanusGraph Exporter** collects:

- `janusgraph_vertices_total` - Total vertex count
- `janusgraph_edges_total` - Total edge count
- `janusgraph_query_duration_seconds` - Query latency histogram
- `janusgraph_errors_total` - Errors by type
- `janusgraph_connection_status` - Connection health

### Alert Rules

**31 alert rules** across 6 categories:

- System Health (8 rules): ServiceDown, HighCPUUsage, DiskSpaceLow
- JanusGraph (4 rules): HighQueryLatency, HighErrorRate
- Security (8 rules): HighFailedAuthRate, CertificateExpiring
- Performance (3 rules): HighResponseTime, High5xxErrorRate
- Cassandra (3 rules): CassandraNodeDown, HighLatency
- Compliance (2 rules): ComplianceScoreLow, AuditLogGap
- Backup (3 rules): BackupFailed, BackupStale

### Access Monitoring

```bash
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
# AlertManager: http://localhost:9093
# JanusGraph Exporter: http://localhost:9091/metrics
```

---

## Common Issues & Solutions

### Deployment Issues

**Issue:** Services fail to start

```bash
# Solution: Check logs and ensure ports are available
podman logs janusgraph
podman logs hcd
netstat -an | grep 8182  # Check if port is in use
```

**Issue:** Integration tests fail with "Service not available"

```bash
# Solution: Ensure services are running and healthy
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
sleep 90  # Wait for services to be ready
curl http://localhost:8182?gremlin=g.V().count()  # Test JanusGraph
```

### Security Issues

**Issue:** Vault access denied

```bash
# Solution: Fix Vault policy and use correct token
./scripts/security/fix_vault_policy.sh
source ./scripts/security/vault_access.sh
```

**Issue:** SSL/TLS certificate errors

```bash
# Solution: Regenerate certificates
./scripts/security/generate_certificates.sh
# Restart services
cd config/compose && podman-compose restart
```

### Testing Issues

**Issue:** Tests fail with import errors

```bash
# Solution: Ensure you're in the correct directory
cd banking/data_generators/tests  # For data generator tests
cd /path/to/project/root  # For other tests
```

**Issue:** Coverage report not generated

```bash
# Solution: Run from project root with --cov flag
pytest --cov=src --cov=banking --cov-report=html
```

---

## Additional Resources

### Key Documentation

- [`README.md`](README.md) - Project overview and quick start
- [`docs/INDEX.md`](docs/INDEX.md) - Central documentation index
- [`docs/implementation/PRODUCTION_READINESS_AUDIT_2026.md`](docs/implementation/production-readiness-audit-2026.md) - Latest audit report
- [`docs/banking/guides/user-guide.md`](docs/banking/guides/user-guide.md) - Banking system user guide
- [`docs/operations/operations-runbook.md`](docs/operations/operations-runbook.md) - Operations procedures

### Implementation Reports

- Week 1: Security Hardening (historical milestone)
- Week 2: Monitoring & Observability (A, 95/100)
- Week 3-4: Test Coverage Expansion (historical milestone)
- Week 6: Compliance Documentation (historical milestone)

---

**Last Updated:** 2026-02-18
**Version:** 2.2
**Status:** Active

## Deterministic Setup Governance (P0, Codex)

Use this canonical command for deterministic setup/proof orchestration:

```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

Determinism-sensitive paths are protected by CI guard (`.github/workflows/determinism-guard.yml`) and script (`scripts/validation/check_determinism_sensitive_paths.sh`).

Protected scope includes:
- `requirements.lock.txt`
- `environment.yml`
- `config/compose/docker-compose.full.yml`
- `banking/streaming/events.py`
- notebook execution scripts and notebook directories

Override requires explicit token: `[determinism-override]` plus reviewer approval.

---

## MCP Servers Policy

**Status:** Active  
**Default Mode:** Read-only  
**Determinism Priority:** Mandatory (no MCP action may weaken deterministic setup/proof behavior)

### Approved MCP servers

| Server | Purpose | Allowed operations | Forbidden operations | Owner |
|---|---|---|---|---|
| GitHub MCP | CI/PR/workflow visibility | Read workflow status, job logs, artifacts metadata, PR/commit status | Force-push, branch protection changes, repo settings changes | Platform |
| Docs/File MCP | Canonical docs/status retrieval | Read `README.md`, `QUICKSTART.md`, `docs/project-status.md`, implementation/audit docs | Direct file mutation through MCP | Platform |
| Podman MCP | Runtime health visibility | Read machine/container status, inspect, logs, health checks | Container/image delete, compose up/down, restart/kill (unless explicitly approved by user) | DevOps |
| Observability MCP | Metrics/log evidence | Read Prometheus/Grafana/Loki queries and dashboards | Alert/rule edits, datasource changes, retention/config changes | SRE |
| Security MCP | Audit/security evidence | Read dependency scan/secret scan/vuln outputs | Secret writes/rotations, policy mutations, credential export | Security |

### Mandatory rules

1. Read-only by default for all MCP servers.
2. Any state-changing MCP action requires explicit user request in the current conversation.
3. Never expose secrets/tokens/keys in outputs; redact by default.
4. Never run MCP actions that alter seed/state/runtime ordering unless explicitly requested.
5. Every MCP-derived claim must include source and timestamp.
6. If MCP data conflicts with canonical scripts, canonical scripts are authoritative.
7. If MCP is unavailable, fallback to local deterministic scripts and command-line checks.

### Evidence format (required)

For every MCP-based status statement, include:

- `Source`: server + endpoint/resource
- `Timestamp`: ISO-8601 UTC
- `Scope`: environment/project (for example `podman-wxd`, `janusgraph-demo`)
- `Verdict`: pass/fail/unknown
- `Notes`: concise interpretation

### Change control

1. Adding a new MCP server requires update to this section and security owner approval.
2. Expanding permissions from read-only requires explicit documented approval in PR.
3. Determinism-sensitive permissions must be reviewed by Platform + Security.

---

## Project Skills (Repository-Local)

To improve delivery speed and consistency for this banking graph platform, use the repository-local skills below.

### Skill catalog

| Skill | Path | Use when |
|---|---|---|
| `deterministic-proof-orchestrator` | `skills/deterministic-proof-orchestrator/SKILL.md` | Running or repairing canonical deterministic setup/proof pipeline |
| `podman-wxd-runtime-doctor` | `skills/podman-wxd-runtime-doctor/SKILL.md` | Podman machine/connection/services are unstable or unclear |
| `notebook-determinism-enforcer` | `skills/notebook-determinism-enforcer/SKILL.md` | Notebook determinism sweep finds hard/warn patterns |
| `auth-secrets-hardening` | `skills/auth-secrets-hardening/SKILL.md` | Auth/session tests fail due secret requirements |
| `dependency-abi-compat-guard` | `skills/dependency-abi-compat-guard/SKILL.md` | Python ABI/import breakage appears (numpy/pandas/sklearn/torch stack) |
| `quality-gate-repair-assistant` | `skills/quality-gate-repair-assistant/SKILL.md` | Local/CI quality gates fail and need prioritized repair |
| `banking-compliance-evidence-packager` | `skills/banking-compliance-evidence-packager/SKILL.md` | Need AML/KYC/UBO evidence bundle for audit/stakeholders |
| `business-scenario-regression` | `skills/business-scenario-regression/SKILL.md` | Validate business-critical banking analytics behavior/regressions |
| `docs-authority-enforcer` | `skills/docs-authority-enforcer/SKILL.md` | Commands/services/ports docs drift from implemented runtime |

### Usage rules

1. Treat these skills as preferred runbooks before ad-hoc troubleshooting.
2. For deterministic work, always start with `deterministic-proof-orchestrator`.
3. For platform failures, chain: `podman-wxd-runtime-doctor` -> `dependency-abi-compat-guard` -> `quality-gate-repair-assistant`.
4. For banking validation, chain: `business-scenario-regression` -> `banking-compliance-evidence-packager`.
5. When docs change, run `docs-authority-enforcer` before merge.
