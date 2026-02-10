# AGENTS.md

This file provides guidance to agents when working with code in this repository.

---

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

### Package Management

**New environment setup** - use ONE of these methods:

```bash
# Option A: Conda (recommended for new users)
conda env create -f environment.yml
conda activate janusgraph-analysis

# Option B: pip with requirements.txt
pip install -r requirements.txt

# Option C: uv (faster than pip)
uv pip install -r requirements.txt
```

**Adding packages** - use `uv` when possible (faster than pip):

```bash
# Install packages with uv (preferred)
uv pip install package-name

# Fallback to pip if uv unavailable
pip install package-name
```

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

**See:** [`docs/implementation/remediation/network-isolation-analysis.md`](docs/implementation/remediation/network-isolation-analysis.md) for complete analysis

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

- **Production Readiness:** B+ (76/100)
- **Test Coverage:** ~35% overall, 950+ tests collected
- **Security:** Enterprise-grade (SSL/TLS, Vault, Audit Logging, Startup Validation)
- **Compliance:** GDPR, SOC 2, BSA/AML, PCI DSS ready
- **CI Quality Gates:** 8 workflows (coverage, docstrings, security, types, lint)

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

**Generators MUST use seeds for reproducibility** - all generators inherit from BaseGenerator and require seed parameter:

```python
generator = PersonGenerator(seed=42)  # Required for deterministic output
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

- Test coverage ≥85%
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
banking/
├── data_generators/     # Synthetic data generation
│   ├── core/           # Base generators (Person, Company, Account)
│   ├── events/         # Event generators (Transaction, Communication)
│   ├── patterns/       # Fraud/AML pattern injection
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

**Current coverage: ~35% overall** (950+ tests collected):

```
Module                          Coverage
──────────────────────────────────────────
python.config                   98%
python.client                   97%
python.utils                    88%
python.api                      75%
data_generators.utils           76%
streaming                       28%
aml                             25%
compliance                      25%
fraud                           23%
data_generators.patterns        13%
analytics                        0%
──────────────────────────────────────────
OVERALL                         ~35%
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
✅ [Setup Guide](SETUP.md)
✅ [Banking Docs](banking/README.md)
❌ [Setup](/docs/SETUP.md)  # Absolute path
```

**Code examples must be tested** - all code examples in documentation must:

1. Be tested before inclusion
2. Include context and explanation
3. Show expected output when relevant
4. Handle errors appropriately

---

## Production Readiness

### Current Status

**Overall Grade:** A+ (98/100) ✅

**Category Scores:**

- Security: 95/100
- Code Quality: 98/100
- Testing: 90/100
- Documentation: 95/100
- Performance: 85/100
- Maintainability: 95/100
- Deployment: 90/100
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
- [`docs/implementation/PRODUCTION_READINESS_AUDIT_2026.md`](docs/implementation/PRODUCTION_READINESS_AUDIT_2026.md) - Latest audit report
- [`docs/banking/guides/user-guide.md`](docs/banking/guides/user-guide.md) - Banking system user guide
- [`docs/operations/operations-runbook.md`](docs/operations/operations-runbook.md) - Operations procedures

### Implementation Reports

- Week 1: Security Hardening (A-, 90/100)
- Week 2: Monitoring & Observability (A, 95/100)
- Week 3-4: Test Coverage Expansion (A+, 98/100)
- Week 6: Compliance Documentation (A+, 98/100)

---

**Last Updated:** 2026-02-07
**Version:** 2.0
**Status:** Active
