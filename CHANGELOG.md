# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Note: historical entries may reference legacy `docker-compose.yml` naming and older port conventions.  
> Current supported runtime uses Podman + `podman-compose` from `config/compose` (see `QUICKSTART.md` and `docs/project-status.md`).

## [Unreleased]

### Added

- **Fully Deterministic Data Pipeline** — all generators now produce identical output given the same seed
  - `banking/data_generators/utils/deterministic.py` — seeded SHA-256 UUID counter + fixed reference timestamp (`2026-01-15T12:00:00Z`)
  - `reset_counter(0)` called automatically in `BaseGenerator.__init__` when seed is provided
  - All `uuid.uuid4()` default factories in `data_models.py` replaced with `seeded_uuid_hex()`
  - All `datetime.utcnow()` / `datetime.now()` in 9 generator files replaced with `REFERENCE_TIMESTAMP`
- **Repository Pattern** — `src/python/repository/graph_repository.py` centralizes all Gremlin traversals behind a typed interface (100% test coverage, 25 tests)
- **Test Suites for 0% Coverage Modules**
  - `tests/unit/init/test_initialize_graph.py` — 15 tests (87% coverage)
  - `tests/unit/loaders/test_janusgraph_loader.py` — 20 tests (44% coverage)
  - `tests/unit/repository/test_graph_repository.py` — 25 tests (100% coverage)
- **Streaming and Pipeline Reliability Test Expansion** — additional unit and integration tests for AML/fraud/streaming paths
  - Added integration utility helpers and coverage-focused unit tests (`tests/integration/_integration_test_utils.py`, `tests/unit/test_streaming_coverage.py`,
    `tests/unit/test_aml_enhanced.py`, `tests/unit/test_dlq_handler.py`, `tests/unit/test_notebook_compat.py`, etc.)
- **Notebook and Streaming Pipeline Assets** — updated execution-focused notebooks (`07_Insider_Trading_Detection_Demo`, `08_UBO_Discovery_Demo`, `11_Streaming_Pipeline_Demo`) and exploratory materials with current routing/compatibility fixes

### Fixed

- **Orchestrator test timeouts** — all `GenerationConfig` inline instances now set explicit `communication_count` (was defaulting to 5000, causing 90s+ per test); 19/19 orchestrator tests pass in 21s
- **E2E test timeouts** — same `communication_count` fix applied; 5/5 E2E tests pass in 10s
- **GenerationStats attribute mismatches** — tests updated to use actual attributes (`total_records`, `patterns_generated`, `generation_time_seconds`)
- **Export structure assertions** — tests updated to handle both `id` and `person_id` field names
- **Amount type casting** — `float()` applied to JSON-serialized Decimal amounts in statistical validation
- **Streaming and service integration gaps** — hardening updates in streaming producer/event handling and deployment/validation scripts
- **Authentication/session edge cases** — MFA and session lifecycle paths updated in API and security modules to reduce login/session flakiness
- **Vault bootstrap reliability** — improved initialization and policy flow handling across setup/security scripts

### Changed

- All 4 API routers (`health`, `fraud`, `aml`, `ubo`) refactored to use `GraphRepository` — zero inline Gremlin queries
- `dependencies.flatten_value_map()` now delegates to repository layer (backward compatible)
- Data generator test suite: **190 passed, 3 skipped, 0 failed** (previously 12 timeouts + attribute errors)
- **Deployment/test automation** scripts now include stricter podman/service lifecycle checks (`scripts/deployment`, `scripts/testing`, `scripts/validation`, `scripts/hcd/health_check.sh`)
- **Production readiness tooling** expanded (`scripts/security/credential_rotation_framework.py`, `scripts/validation/production_readiness_check.py`) to tighten preflight checks and credential policy handling

## [1.4.0] - 2026-02-14

### Fixed

- **Streaming orchestrator hang** — `test_orchestrator_with_real_pulsar` hung >120s because `GenerationConfig` defaults silently generated 8,500+ entities (5000 communications, 1000 trades, 500 travel, 2000 documents); zeroed unused counts in test config
- **`EntityProducer.flush()` blocking indefinitely** — added thread-based 5s timeout wrapper to prevent Pulsar C-level flush from hanging the test process
- **`EntityProducer.close()` slow cleanup** — reduced default timeout from 10s to 5s
- **Vault integration tests skipping** — reinitialized Vault (1/1 shares, KV v2 at `janusgraph`) after root token was lost between sessions
- **30+ integration test failures** across `test_vault_integration.py`, `test_credential_rotation.py`, `test_streaming_integration.py`, `test_fraud_detection_methods.py`, `test_e2e_streaming_enhanced.py`, `test_e2e_streaming_pipeline.py`
- **JanusGraph schema** — epoch Integer timestamps, lowercase vertex/edge labels (`account`, `person`, `transaction`, `made_transaction`, `received_transaction`, `owns_account`)
- **181 edges created** in JanusGraph for data-dependent fraud detection tests

### Changed

- `EntityProducer.flush()` now accepts `timeout` parameter (default: 5s) with thread-based timeout protection
- `EntityProducer.close()` default timeout reduced from 10s to 5s
- Integration test suite: **202 passed, 0 skipped, 0 failed** (previously 150 passed, 52 skipped)
- Vault client exception propagation and path detection improved
- OpenSearch health check uses correct SSL/credential defaults

### Added (previous)

- **Documentation Quality Improvements**
  - FAQ.md with common questions and answers
  - Markdownlint configuration (`.markdownlint.json`)
  - CI workflow for documentation linting (`.github/workflows/docs-lint.yml`)
  - Documentation coverage analyzer (`scripts/docs/doc_coverage.py`)
  - AI-powered semantic search for docs (`scripts/docs/setup_doc_search.py`)
  - Markdown link check configuration

### Changed

- OLAP guide enhanced with "Why OpenSearch vs Spark" section
- Notebooks guide updated with OpenSearch aggregation details
- System architecture updated with OLAP notes

## [1.3.0] - 2026-02-09

### Added

- **Centralized Configuration** via `pydantic-settings` (`src/python/config/settings.py`)
- **Resilience Utilities** — `CircuitBreaker` and `retry_with_backoff` (`src/python/utils/resilience.py`)
- **FastAPI Hardening** — rate limiting (`slowapi`), structured JSON logging, liveness/readiness probes, global error handlers, JWT/API key authentication middleware
- **API Pagination** for fraud rings and structuring endpoints
- **Expanded Makefile** with 12 dev targets (format, lint, typecheck, coverage, etc.)
- `py.typed` markers for PEP 561 compliance
- `banking/__init__.py` package marker

### Changed

- `JanusGraphClient` now requires `username`/`password` for authentication
- `CircuitBreaker` uses `CircuitBreakerConfig` dataclass instead of keyword args
- Module-level constants in `src/python/api/main.py` replaced with `get_settings()`
- `structuring_detection.py` and `fraud_detection.py` refactored to use connection pooling and context managers
- Dependencies consolidated in `pyproject.toml`
- PII removed from 90+ files

### Fixed

- All 572 unit/integration tests passing
- Test serialization fixed (`GraphSONSerializersV3d0` for JanusGraph custom types)
- Stale `__class__` double-underscore test case removed (pattern intentionally unblocked for Gremlin `__` traversals)

## [1.2.1] - 2026-02-09

### Fixed

- **CRITICAL**: TypeError in `fraud_detection.py` `check_velocity()` — missing required args
- **CRITICAL**: Gremlin `__` anonymous traversals falsely blocked by query validation regex
- **CRITICAL**: 118 deprecated `datetime.utcnow()` calls replaced with `datetime.now(timezone.utc)` across 30 files
- 337 f-string logging calls converted to lazy `%s` formatting across 27 files
- Connection-per-call anti-pattern in `structuring_detection.py` and `fraud_detection.py` — now use connection pooling with context manager support
- `sys.path.insert()` hacks removed from `structuring_detection.py` and `fraud_detection.py`
- Hardcoded `avg_confidence: 0.75` in `evaluate_model()` now computed from actual predictions
- Naive `datetime.now()` in test fixture (`conftest.py`) now timezone-aware

### Removed

- `__main__` demo blocks from 9 library modules (-374 lines)
- PII (phone numbers, personal emails) from 90 files (166 instances)
- Redundant `requirements*.txt` files (8 files replaced with pointers to `pyproject.toml`)

### Added

- `banking/__init__.py` — package now installable via `uv pip install -e ".[all]"`
- `[tool.setuptools.packages.find]` in `pyproject.toml` for proper package discovery
- `detect-secrets` hook in `.pre-commit-config.yaml` with `.secrets.baseline`
- Test location convention documented in `AGENTS.md`
- Connection pooling with `connect()`/`disconnect()`/context manager in detection modules

---

## [1.0.0] - 2026-01-29

### Changed - Data Models (BREAKING CHANGES)

- **BREAKING**: Entity models now use inherited `id` field from BaseEntity instead of entity-specific IDs
  - `Person.person_id` → `Person.id`
  - `Company.company_id` → `Company.id`
  - `Account.account_id` → `Account.id`
  - `Transaction.transaction_id` remains separate from `Transaction.id` (both exist)
  - **Migration**: Update all code references from `.person_id`, `.company_id`, `.account_id` to `.id`
  - **Impact**: Affects data generators, tests, and any external code using these models
  - See `banking/data_generators/utils/data_models.py` for updated BaseEntity structure

### Added - Week 4: Test Coverage Improvements

- Comprehensive unit tests for Validator class (276 lines, 100% coverage)
- Fixed all data generator tests (44/46 passing, 96% success rate)
- Enhanced test fixtures in conftest.py with better documentation
- Added `small_orchestrator` fixture for backward compatibility

### Added - Week 1: Security Hardening

- **SSL/TLS enabled by default** in docker-compose.yml
- HashiCorp Vault container integration for secrets management
- Vault initialization script (scripts/security/init_vault.sh)
- Vault configuration file (config/vault/config.hcl)
- TLS certificate generation script (scripts/security/generate_certificates.sh)
- hvac library (2.1.0) for Vault Python integration
- Comprehensive Week 1 implementation guide
- Production readiness roadmap (6-week plan)

### Added - Code Quality

- Comprehensive input validation with Validator class
- Shared authentication utility (src/python/utils/auth.py)
- Enhanced security validation for all user inputs
- Module-level constants for validation limits
- IPv6 hostname validation support
- Privileged port checking
- File path validation with path traversal detection
- Password strength validation
- URL validation with scheme restrictions
- Environment variable name validation
- Alternative Grafana dashboard with working Prometheus metrics
- Comprehensive project audit report identifying P0/P1/P2 issues
- P0_FIXES.md documentation
- docs/SETUP.md - Detailed setup guide (240 lines)
- docs/MONITORING.md - Monitoring configuration (185 lines)
- docs/BACKUP.md - Backup/restore procedures (223 lines)
- docs/TROUBLESHOOTING.md - Common issues (474 lines)
- docs/CONTRIBUTING.md - Contribution guidelines (311 lines)
- notebooks/01_quickstart.ipynb - Quick introduction
- notebooks/03_advanced_queries.ipynb - Advanced patterns
- config/monitoring/grafana/dashboards/prometheus-system.json

### Fixed

- **P0 CRITICAL**: Replaced all GitHub organization placeholders (13 occurrences)
- **P0 CRITICAL**: Replaced all email placeholders (6 occurrences)
- **P0 CRITICAL**: Updated CODEOWNERS with actual GitHub username
- Gremlin syntax in Python load_data.py (child traversal bug)
- Test script paths after project restructuring
- Deployment script and Dockerfile paths for new structure
- All 46 files updated with full signature format

### Changed - Security (BREAKING CHANGES)

- **BREAKING**: SSL/TLS now enabled by default for all services
- **BREAKING**: HCD now uses port 9142 (TLS) as default, 9042 for backward compatibility
- **BREAKING**: JanusGraph requires TLS certificates in /etc/janusgraph/certs/
- **BREAKING**: Services now require VAULT_ADDR and VAULT_TOKEN environment variables
- docker-compose.yml updated to mount TLS certificates
- .env.example updated with TLS and Vault configuration
- .gitignore updated to exclude .vault-keys and vault data

### Changed - Code Quality

- Updated signature globally to include full IBM title and contact details
- Added timestamps to 10 Python files
- Project restructured from 43 root files to 8 organized directories
- GitHub integration complete (workflows, templates, Dependabot)
- **BREAKING**: JanusGraphClient now requires authentication (username/password)
- **BREAKING**: validate_port() now rejects privileged ports by default (use allow_privileged=True)
- **BREAKING**: sanitize_string() parameter renamed from allow_special_chars to allow_whitespace
- Enhanced .env.example with clearer placeholder passwords
- Improved .gitignore to exclude test credentials and certificate files
- JanusGraphClient validates ca_certs file path if provided
- JanusGraphClient validates timeout range with warnings for extreme values
- Query logging now sanitizes bindings to prevent sensitive data exposure

### Security

- Enhanced Gremlin query validation with SQL injection and XSS detection
- Added path traversal detection in file path validation
- Improved password strength requirements (min 12 chars, complexity rules)
- CA certificate file validation before SSL connection
- Privileged port detection to prevent accidental root requirement
- All placeholders resolved - ready for GitHub push
- No hardcoded secrets in codebase
- Security reporting procedures documented

---
