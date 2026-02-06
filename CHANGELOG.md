# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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

**Signature**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
