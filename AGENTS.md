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

### Package Management

**Use `uv` for package management when possible** (faster than pip):

```bash
# Install packages with uv (preferred)
uv pip install package-name

# Install from requirements
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt

# Fallback to pip if uv unavailable
pip install package-name
```
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

**See:** [`docs/implementation/remediation/NETWORK_ISOLATION_ANALYSIS.md`](docs/implementation/remediation/NETWORK_ISOLATION_ANALYSIS.md) for complete analysis


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
```

### Project Status
- **Production Readiness:** A+ (98/100) ✅
- **Test Coverage:** 82% (170+ tests)
- **Security:** Enterprise-grade (SSL/TLS, Vault, Audit Logging)
- **Compliance:** GDPR, SOC 2, BSA/AML, PCI DSS ready

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
└── fraud/             # Fraud detection
```

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

**Current coverage: 82%** (exceeds 80% target):
```
Module                          Coverage    Tests
──────────────────────────────────────────────────
PersonGenerator                 92%         20+
CompanyGenerator                96%         18
AccountGenerator                91%         20
CommunicationGenerator          95%         43
AML Structuring Detection       80%         30+
Fraud Detection                 80%         35+
Integration Workflows           80%         25+
Audit Logger                    98%         28
──────────────────────────────────────────────────
OVERALL                         82%         170+
```

---

## Documentation Structure and Standards

### File Naming

**Documentation follows strict organization** - see [`docs/DOCUMENTATION_STANDARDS.md`](docs/DOCUMENTATION_STANDARDS.md) for complete standards

**File naming convention is kebab-case** - all documentation files use kebab-case:
```
✅ user-guide.md, api-reference.md, phase-8-complete.md
❌ USER_GUIDE.md, ApiReference.md, user_guide.md
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
├── DOCUMENTATION_STANDARDS.md  # Standards guide
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
- [`docs/banking/guides/USER_GUIDE.md`](docs/banking/guides/USER_GUIDE.md) - Banking system user guide
- [`docs/operations/OPERATIONS_RUNBOOK.md`](docs/operations/OPERATIONS_RUNBOOK.md) - Operations procedures

### Implementation Reports
- Week 1: Security Hardening (A-, 90/100)
- Week 2: Monitoring & Observability (A, 95/100)
- Week 3-4: Test Coverage Expansion (A+, 98/100)
- Week 6: Compliance Documentation (A+, 98/100)

---

**Last Updated:** 2026-01-29  
**Version:** 2.0  
**Status:** Active