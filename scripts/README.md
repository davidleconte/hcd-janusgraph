# Scripts Directory

This directory contains operational scripts for managing, deploying, and maintaining the HCD + JanusGraph banking compliance system.

**Date:** 2026-01-28
**Version:** 1.0
**Status:** Active

## Directory Structure

```
scripts/
├── backup/          # Data backup and recovery scripts
├── deployment/      # Deployment and startup scripts
├── init/            # Initialization and data loading scripts
├── maintenance/     # System maintenance scripts
├── monitoring/      # Monitoring and alerting scripts
├── security/        # Security configuration scripts
├── setup/           # Environment setup scripts
├── testing/         # Testing automation scripts
└── utils/           # Utility scripts and helpers
```

## Script Categories

### Backup Scripts (`backup/`)

Scripts for backing up and restoring graph data and system volumes.

#### [`backup_volumes.sh`](backup/backup_volumes.sh)

- **Purpose:** Backup Docker volumes to compressed archives
- **Usage:** `./backup_volumes.sh`
- **Output:** Creates timestamped backups in `./backups/` directory
- **Requirements:** Docker must be running

#### [`backup_volumes_encrypted.sh`](backup/backup_volumes_encrypted.sh)

- **Purpose:** Backup Docker volumes with encryption
- **Usage:** `./backup_volumes_encrypted.sh`
- **Output:** Creates encrypted, timestamped backups
- **Requirements:** Docker, GPG for encryption

#### [`export_graph.py`](backup/export_graph.py)

- **Purpose:** Export graph data to JSON format
- **Usage:** `python export_graph.py [--output FILE]`
- **Output:** JSON file containing graph vertices and edges
- **Requirements:** Python 3.11+, gremlinpython

#### [`restore_volumes.sh`](backup/restore_volumes.sh)

- **Purpose:** Restore Docker volumes from backup archives
- **Usage:** `./restore_volumes.sh <backup_file>`
- **Requirements:** Docker must be stopped

#### [`test_backup.sh`](backup/test_backup.sh)

- **Purpose:** Test backup and restore procedures
- **Usage:** `./test_backup.sh`
- **Output:** Validation report

### Deployment Scripts (`deployment/`)

Scripts for deploying and managing the full stack.

#### [`deploy_full_stack.sh`](deployment/deploy_full_stack.sh)

- **Purpose:** Deploy complete HCD + JanusGraph stack
- **Usage:** `cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh`
- **Components:** HCD, OpenSearch, JanusGraph, Jupyter, monitoring
- **Requirements:** Docker Compose, sufficient system resources
- **Note:** Must be run from `config/compose/` directory

#### [`deploy_aml_production.sh`](deployment/deploy_aml_production.sh)

- **Purpose:** Deploy AML/fraud detection modules to production
- **Usage:** `./deploy_aml_production.sh`
- **Components:** Sanctions screening, structuring detection, fraud detection
- **Requirements:** Full stack must be running

#### [`load_production_data.py`](deployment/load_production_data.py)

- **Purpose:** Load production banking data into graph
- **Usage:** `python load_production_data.py [--config FILE]`
- **Data:** Persons, companies, accounts, transactions, patterns
- **Requirements:** Python 3.11+, graph must be initialized

#### [`start_jupyter.sh`](deployment/start_jupyter.sh)

- **Purpose:** Start Jupyter notebook server
- **Usage:** `./start_jupyter.sh`
- **Access:** <http://localhost:8888>
- **Requirements:** Docker Compose

#### [`stop_full_stack.sh`](deployment/stop_full_stack.sh)

- **Purpose:** Gracefully stop all services
- **Usage:** `./stop_full_stack.sh`
- **Note:** Preserves data volumes

### Initialization Scripts (`init/`)

Scripts for initializing schema and loading sample data.

#### [`init_and_load.py`](init/init_and_load.py)

- **Purpose:** Initialize schema and load sample data
- **Usage:** `python init_and_load.py`
- **Requirements:** Python 3.11+, JanusGraph running

#### [`init_sample_schema.groovy`](init/init_sample_schema.groovy)

- **Purpose:** Groovy script to create sample graph schema
- **Usage:** Executed via Gremlin console or Python client
- **Schema:** Basic vertex and edge labels

#### [`load_data.py`](init/load_data.py)

- **Purpose:** Load data from CSV/JSON files
- **Usage:** `python load_data.py --input <file>`
- **Formats:** CSV, JSON
- **Requirements:** Python 3.11+

#### [`load_sample_data.groovy`](init/load_sample_data.groovy)

- **Purpose:** Groovy script to load sample graph data
- **Usage:** Executed via Gremlin console
- **Data:** Sample vertices and edges

### Maintenance Scripts (`maintenance/`)

Scripts for routine system maintenance.

#### [`cleanup_logs.sh`](maintenance/cleanup_logs.sh)

- **Purpose:** Clean up old log files
- **Usage:** `./cleanup_logs.sh [--days N]`
- **Default:** Removes logs older than 30 days
- **Locations:** Docker logs, application logs

#### [`rotate_secrets.sh`](maintenance/rotate_secrets.sh)

- **Purpose:** Rotate security credentials
- **Usage:** `./rotate_secrets.sh`
- **Updates:** Database passwords, API keys, certificates
- **Requirements:** Admin privileges

#### [`clear_notebook_outputs.sh`](maintenance/clear_notebook_outputs.sh)

- **Purpose:** Clear execution outputs from Jupyter notebooks
- **Usage:** `./clear_notebook_outputs.sh`
- **Output:** Clears outputs from banking and exploratory notebooks
- **Why:** Prevents hardcoded paths from being committed
- **Requirements:** Jupyter installed, conda environment activated

### Monitoring Scripts (`monitoring/`)

Scripts for setting up monitoring and alerts.

#### [`setup_alerts.sh`](monitoring/setup_alerts.sh)

- **Purpose:** Configure Prometheus alerting rules
- **Usage:** `./setup_alerts.sh`
- **Alerts:** System health, performance, security
- **Requirements:** Prometheus running

#### [`test_alerts.sh`](monitoring/test_alerts.sh)

- **Purpose:** Test alerting configuration
- **Usage:** `./test_alerts.sh`
- **Output:** Alert validation report

### Security Scripts (`security/`)

Scripts for security configuration.

#### [`generate_certificates.sh`](security/generate_certificates.sh)

- **Purpose:** Generate SSL/TLS certificates
- **Usage:** `./generate_certificates.sh`
- **Output:** Certificates in `config/certs/`
- **Validity:** 365 days (configurable)

### Setup Scripts (`setup/`)

Scripts for environment setup and configuration.

#### [`install_phase5_dependencies.sh`](setup/install_phase5_dependencies.sh)

- **Purpose:** Install ML/AI dependencies for Phase 5
- **Usage:** `./install_phase5_dependencies.sh`
- **Packages:** sentence-transformers, scikit-learn, numpy
- **Requirements:** Python 3.11+, pip

### Testing Scripts (`testing/`)

Scripts for running automated tests.

#### [`run_tests.sh`](testing/run_tests.sh)

- **Purpose:** Run all test suites
- **Usage:** `./run_tests.sh [unit|integration|performance|all]`
- **Output:** Test results and coverage report
- **Requirements:** pytest, test dependencies

#### [`run_integration_tests.sh`](testing/run_integration_tests.sh)

- **Purpose:** Run integration tests only
- **Usage:** `./run_integration_tests.sh`
- **Requirements:** Full stack must be running

#### [`run_notebooks_live_repeatable.sh`](testing/run_notebooks_live_repeatable.sh)

- **Purpose:** Run all banking + exploratory notebooks in live mode with deterministic settings
- **Usage:** `./run_notebooks_live_repeatable.sh`
- **Output:** `notebook_run_report.tsv` with status, runtime, and error-cell counts per notebook
- **Controls:**
  - `DEMO_RUN_ID`
  - `DEMO_SEED`
  - `DEMO_FORCE_MOCK_PULSAR` (`1` to force mock streaming in Notebook 11)
  - `DEMO_NOTEBOOK_TOTAL_TIMEOUT`
  - `DEMO_NOTEBOOK_CELL_TIMEOUT`
- **Requirements:** Jupyter service must be reachable and service stack running

#### [`test_phase5_setup.py`](testing/test_phase5_setup.py)

- **Purpose:** Validate Phase 5 ML/AI setup
- **Usage:** `python test_phase5_setup.py`
- **Checks:** Dependencies, OpenSearch vector support, embeddings

### Utility Scripts (`utils/`)

Helper scripts and utilities.

#### [`secrets_manager.py`](utils/secrets_manager.py)

- **Purpose:** Manage encrypted secrets
- **Usage:** `python secrets_manager.py [get|set|list] <key> [value]`
- **Storage:** Encrypted in `.secrets/`
- **Requirements:** Python 3.11+, cryptography

#### [`validation.sh`](utils/validation.sh)

- **Purpose:** Validate system configuration
- **Usage:** `./validation.sh`
- **Checks:** Dependencies, ports, permissions, configuration files

## Usage Guidelines

### Running Scripts

1. **Check Requirements:** Ensure all prerequisites are met
2. **Review Documentation:** Read script header comments for details
3. **Test First:** Use test scripts before production operations
4. **Monitor Output:** Watch for errors and warnings
5. **Verify Results:** Confirm operations completed successfully

### Best Practices

- **Always backup** before running maintenance scripts
- **Test in development** before running in production
- **Review logs** after script execution
- **Use version control** for script modifications
- **Document changes** in script headers

### Common Workflows

#### Initial Setup

```bash
# 1. Install dependencies
./scripts/setup/install_phase5_dependencies.sh

# 2. Generate certificates
./scripts/security/generate_certificates.sh

# 3. Deploy stack
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh

# 4. Initialize schema and load data
python scripts/init/init_and_load.py
```

#### Daily Operations

```bash
# Check system health
./scripts/utils/validation.sh

# Run tests
./scripts/testing/run_tests.sh all

# Backup data
./scripts/backup/backup_volumes.sh
```

#### Maintenance

```bash
# Clean up logs
./scripts/maintenance/cleanup_logs.sh --days 30

# Rotate secrets (monthly)
./scripts/maintenance/rotate_secrets.sh
```

## Troubleshooting

### Common Issues

**Script Permission Denied**

```bash
chmod +x scripts/path/to/script.sh
```

**Docker Not Running**

```bash
docker ps  # Check if Docker is running
sudo systemctl start docker  # Start Docker (Linux)
```

**Python Dependencies Missing**

```bash
pip install -r requirements.txt
```

**Port Already in Use**

```bash
# Check what's using the port
lsof -i :8182  # JanusGraph
lsof -i :9200  # OpenSearch

# Stop conflicting service or change port in config
```

## Related Documentation

- [Deployment Guide](../docs/DEPLOYMENT.md)
- [Setup Guide](../docs/SETUP.md)
- [Testing Guide](../docs/TESTING.md)
- [Backup Guide](../docs/BACKUP.md)
- [Monitoring Guide](../docs/MONITORING.md)

## Contributing

When adding new scripts:

1. Place in appropriate subdirectory
2. Follow naming convention: `verb_noun.sh` or `verb_noun.py`
3. Add header comment with purpose, usage, requirements
4. Make executable: `chmod +x script.sh`
5. Update this README
6. Add tests if applicable
7. Document in relevant guides

## Support

For issues or questions:

- Check [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
- Review script comments and documentation
- Check logs in `logs/` directory
- Consult [Documentation Index](../docs/INDEX.md)
