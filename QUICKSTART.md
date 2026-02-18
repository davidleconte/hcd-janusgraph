# HCD + JanusGraph Quick Start Guide

**File**: QUICKSTART.md
**Created**: 2026-01-28T10:35:00.123
**Last Updated**: 2026-02-17
**Last Verified**: 2026-02-17
**Applies To**: Podman-based local deployment with `COMPOSE_PROJECT_NAME=janusgraph-demo`
**Authoritative Status**: [docs/project-status.md](docs/project-status.md)
**Author**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Essential Commands](#essential-commands)
- [Important URLs](#important-urls)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Podman** 4.9+ ([Install](https://podman.io/getting-started/installation))
- **Python** 3.11+ ([Install](https://www.python.org/downloads/))
- **Git** ([Install](https://git-scm.com/downloads))
- **8GB+ RAM** recommended
- **20GB+ disk space**

### HCD Distribution (Git LFS)

The HCD distribution is included via **Git LFS** in `vendor/`. After cloning:

```bash
# 1. Pull LFS files (usually automatic, but verify)
git lfs pull

# 2. Create symlink at project root
ln -sf vendor/hcd-1.2.3 hcd-1.2.3

# 3. Verify
ls hcd-1.2.3/bin/hcd  # Should show the HCD binary
```

> **Note**: If `git lfs` is not installed, install it from [git-lfs.github.com](https://git-lfs.github.com/)

### Verify Installation

```bash
# Full preflight check (recommended)
./scripts/validation/preflight_check.sh

# Or manual verification
podman --version      # Should show 4.9+
python3 --version     # Should show 3.11+
ls hcd-1.2.3/bin/hcd  # Should show HCD binary
```

### Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Set PODMAN_CONNECTION to your machine name
```

---

## Essential Commands

### Makefile Commands (Recommended)

```bash
make help     # Show all commands
make build    # Build container images
make deploy   # Deploy full stack
make test     # Run tests
make clean    # Cleanup
```

### Direct Deployment

```bash
# Deploy full stack (MUST run from config/compose directory)
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# Or use podman-compose directly (MUST be in config/compose directory)
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d

# Check status
podman ps

# View logs
podman logs -f janusgraph-demo_janusgraph-server_1
```

### Stop Stack

```bash
bash scripts/deployment/stop_full_stack.sh
```

### Run Tests

```bash
bash scripts/testing/run_tests.sh
```

---

## Important URLs

### Core Services

| Service | URL | Description |
|---------|-----|-------------|
| **JanusGraph** | <http://localhost:18182> | Gremlin server |
| **HCD (CQL)** | localhost:19042 | Cassandra Query Language |
| **HCD (TLS)** | localhost:9142 | Cassandra with SSL/TLS |
| **Jupyter Lab** | <http://localhost:8888> | Interactive notebooks |

### Monitoring & Observability

| Service | URL | Description |
|---------|-----|-------------|
| **Grafana** | <http://localhost:3001> | Dashboards (admin/admin) |
| **Prometheus** | <http://localhost:9090> | Metrics collection |
| **AlertManager** | <http://localhost:9093> | Alert management |
| **JanusGraph Exporter** | <http://localhost:9091/metrics> | Custom metrics |

### Security & Secrets

| Service | URL | Description |
|---------|-----|-------------|
| **Vault** | <http://localhost:8200> | Secrets management |

### Visualization

| Service | URL | Description |
|---------|-----|-------------|
| **Visualizer** | <http://localhost:3000> | Graph visualization |
| **Graphexp** | <http://localhost:8080> | Graph explorer |
| **OpenSearch Dashboards** | <http://localhost:5601> | OpenSearch Web UI |

### CLI Tools & Consoles

| Tool | Container | Access Command |
|------|-----------|----------------|
| **CQLSH** | cqlsh-client | `podman exec -it janusgraph-demo_cqlsh-client_1 cqlsh hcd-server` |
| **Gremlin Console** | gremlin-console | `podman exec -it janusgraph-demo_gremlin-console_1 bin/gremlin.sh` |
| **Pulsar CLI** | pulsar-cli | `podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin ...` |

#### CQLSH (Cassandra Query Language Shell)

```bash
# Interactive CQL session
podman exec -it janusgraph-demo_cqlsh-client_1 cqlsh hcd-server

# Run CQL command directly
podman exec janusgraph-demo_cqlsh-client_1 cqlsh hcd-server -e "DESCRIBE KEYSPACES"
```

#### Gremlin Console (JanusGraph Graph Queries)

```bash
# Start interactive Gremlin console
podman exec -it janusgraph-demo_gremlin-console_1 bin/gremlin.sh

# Inside Gremlin console:
:remote connect tinkerpop.server conf/remote-connect.properties
:remote console
g.V().count()
```

#### Pulsar CLI (Message Streaming)

```bash
# List topics
podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin topics list public/banking

# Check topic stats
podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin topics stats persistent://public/banking/persons-events
```

### GitHub (when configured)

| Item | URL |
|------|-----|
| **Repository** | <https://github.com/davidleconte/hcd-janusgraph> |
| **Issues** | <https://github.com/davidleconte/hcd-janusgraph/issues> |
| **Pull Requests** | <https://github.com/davidleconte/hcd-janusgraph/pulls> |
| **Actions** | <https://github.com/davidleconte/hcd-janusgraph/actions> |
| **Security** | <https://github.com/davidleconte/hcd-janusgraph/security> |

---

## Common Tasks

### 1. Deploy Stack

```bash
# CRITICAL: Must run from config/compose directory
# Dockerfile paths in docker-compose.full.yml are relative to this location

# Full stack (HCD + JanusGraph + monitoring + visualization)
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# Or use podman-compose directly with project name for isolation
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d

# Wait for startup (60-90 seconds)
# Verify with: podman ps
```

### 2. Initialize Schema

```bash
# Schema is auto-initialized on first start
# To re-initialize:
python3 scripts/init/load_data.py
```

### 3. Access Jupyter

```bash
# Jupyter is included in full stack
# Or start separately:
bash scripts/deployment/start_jupyter.sh

# Get token:
podman logs jupyter-lab | grep token

# Open: http://localhost:8888
```

### 4. Query Graph (Python)

```python
from gremlin_python.driver import client

gc = client.Client('ws://localhost:18182/gremlin', 'g')

# Count vertices
v_count = gc.submit('g.V().count()').all().result()[0]
print(f"Vertices: {v_count}")

# Get all people
people = gc.submit("g.V().hasLabel('person').values('name')").all().result()
print(f"People: {people}")
```

### 5. Run CQL Query

```bash
# Connect to HCD via CQLSH client container
podman exec -it janusgraph-demo_cqlsh-client_1 cqlsh hcd-server

# List keyspaces
DESCRIBE KEYSPACES;

# Query JanusGraph keyspace
USE janusgraph;
DESCRIBE TABLES;
SELECT * FROM edgestore LIMIT 10;
```

### 6. Backup Data

```bash
# Create backup
bash scripts/backup/backup_volumes.sh

# Backups stored in: /backups/janusgraph/

# Restore from backup
bash scripts/backup/restore_volumes.sh /backups/janusgraph/hcd_20260128_103000
```

### 7. Monitor Stack

```bash
# Prometheus metrics
open http://localhost:9090

# Grafana dashboards
open http://localhost:3001
# Login: admin/admin

# AlertManager (alerts and notifications)
open http://localhost:9093

# JanusGraph custom metrics
curl http://localhost:9091/metrics

# View container logs
podman logs -f janusgraph-server
podman logs -f hcd-server
podman logs -f alertmanager
```

### 8. Security & Secrets Management

```bash
# Access Vault (after initialization)
source scripts/security/vault_access.sh

# View stored secrets
vault kv get janusgraph/hcd-credentials
vault kv get janusgraph/janusgraph-credentials

# SSL/TLS is enabled by default
# Certificates located in: config/ssl/

# For detailed security setup, see:
# docs/implementation/WEEK1_COMPLETE_SUMMARY_2026-02-11.md
```

### 9. Run Tests

```bash
# Run unit tests (no services required)
pytest tests/unit/ -v --cov=src --cov=banking --cov-report=html

# Run integration tests (requires running services)
pytest tests/integration/ -v -m integration

# Run performance tests
pytest tests/performance/ -v -m performance

# View coverage report
open htmlcov/index.html

# For detailed testing guide, see:
# docs/implementation/WEEK3_COMPLETE_SUMMARY.md
```

### 10. Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
# Edit code...

# 3. Run tests
make test

# 4. Commit
git add .
git commit -m "feat: add new feature"

# 5. Push
git push origin feature/my-feature

# 6. Create PR (GitHub)
gh pr create --title "Add new feature" --body "Description"
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
podman logs <container-name>

# Check if port is in use
lsof -i :<port>

# Restart container
podman restart <container-name>
```

### HCD Not Ready

```bash
# Wait for HCD to initialize (60-90s)
podman logs hcd-server

# Check cluster status
podman exec hcd-server nodetool status

# Should show: UN (Up/Normal)
```

### JanusGraph Connection Failed

```bash
# Verify JanusGraph is running
curl http://localhost:18182

# Check if HCD is ready first
podman exec hcd-server nodetool status

# Restart JanusGraph
podman restart janusgraph-server
```

### Vault Not Accessible

```bash
# Check Vault status
podman logs vault

# Initialize Vault (first time only)
bash scripts/security/init_vault.sh

# Unseal Vault (after restart)
# Use keys from vault-keys.json

# Access Vault
source scripts/security/vault_access.sh
```

### Test Failures

```bash
# Integration tests failing? Services might not be running
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# Wait for services to be healthy (60-90 seconds)
sleep 90

# Run tests again
pytest tests/integration/ -v

# For unit tests (no services needed)
pytest tests/unit/ -v
```

### SSL/TLS Certificate Issues

```bash
# Regenerate certificates
bash scripts/security/generate_certificates.sh

# Verify certificates
openssl x509 -in config/ssl/server.crt -text -noout

# Check certificate expiration
openssl x509 -in config/ssl/server.crt -noout -dates
```

### Schema Initialization Failed

```bash
# Check logs
podman logs janusgraph-server

# Manually initialize
python3 scripts/init/load_data.py

# Verify schema
python3 -c "
from gremlin_python.driver import client
gc = client.Client('ws://localhost:18182/gremlin', 'g')
labels = gc.submit('g.V().label().dedup()').all().result()
print(f'Labels: {labels}')
"
```

### Tests Fail

```bash
# Run tests with verbose output
pytest tests/ -v

# Check if services are running
podman ps

# Verify connectivity
python3 -c "
from gremlin_python.driver import client
try:
    gc = client.Client('ws://localhost:18182/gremlin', 'g')
    count = gc.submit('g.V().count()').all().result()[0]
    print(f'✅ Connected: {count} vertices')
except Exception as e:
    print(f'❌ Failed: {e}')
"
```

### Port Conflicts

```bash
# Check what's using a port
lsof -i :18182

# Stop conflicting process
kill <PID>

# Or change port in .env
vim .env
# JANUSGRAPH_PORT=28182
```

### Out of Memory

```bash
# Check container resource usage
podman stats

# Increase heap in .env
vim .env
# HCD_HEAP_SIZE=8G
# JANUSGRAPH_HEAP_SIZE=4G

# Restart stack
bash scripts/deployment/stop_full_stack.sh
bash scripts/deployment/deploy_full_stack.sh
```

---

## Quick Reference

### File Structure

```
hcd-tarball-janusgraph/
├── .github/              # GitHub workflows, templates
├── config/               # All configuration
│   ├── compose/          # Docker compose files
│   ├── environments/     # Environment configs
│   ├── janusgraph/       # JanusGraph configs
│   └── monitoring/       # Prometheus/Grafana
├── docker/               # Dockerfiles
├── scripts/              # Automation scripts
│   ├── deployment/       # Deploy/stop
│   ├── backup/           # Backup/restore
│   ├── monitoring/       # Alerts
│   ├── testing/          # Tests
│   └── maintenance/      # Cleanup
├── src/                  # Source code
├── tests/                # Test code
├── docs/                 # Documentation
├── notebooks/            # Jupyter notebooks
└── data/                 # Data files
```

### Key Files

- `.env` - Environment variables (NOT committed)
- `.env.example` - Environment template
- `Makefile` - Common commands
- `requirements.txt` - Python dependencies (pip)
- `environment.yml` - Conda environment definition
- `pyproject.toml` - Project metadata and all dependencies
- `config/compose/docker-compose.full.yml` - Full stack definition
- `SECURITY.md` - Security policy

### Environment Variables

```bash
# Core settings (.env)
PODMAN_CONNECTION=podman-machine-default
JANUSGRAPH_PORT=18182
HCD_PORT=19042
JUPYTER_PORT=8888
GRAFANA_PORT=3001
PROMETHEUS_PORT=9090

# Resource limits
HCD_HEAP_SIZE=4G
JANUSGRAPH_HEAP_SIZE=2G

# Network
NETWORK_NAME=hcd-janusgraph-network
```

---

## Getting Help

### Documentation

- **README.md** - Project overview
- **docs/SETUP.md** - Detailed setup
- **docs/TESTING.md** - Testing guide
- **docs/ARCHITECTURE.md** - System design
- **docs/TROUBLESHOOTING.md** - Common issues
- **docs/SECURITY.md** - Security guidelines

### Support Channels

- **Issues**: <https://github.com/davidleconte/hcd-janusgraph/issues>
- **Discussions**: <https://github.com/davidleconte/hcd-janusgraph/discussions>
- **Owner**: <https://github.com/davidleconte>

### External Resources

- [JanusGraph Docs](https://docs.janusgraph.org/)
- [HCD Documentation](https://docs.datastax.com/en/hcd/1.2/)
- [Gremlin Reference](https://tinkerpop.apache.org/docs/current/reference/)
- [Podman Guide](https://docs.podman.io/en/latest/)

---

## Next Steps

1. **Customize Configuration**: Edit `.env` for your environment
2. **Deploy Stack**: Run `make deploy`
3. **Verify Installation**: Run `make test`
4. **Explore Notebooks**: Open Jupyter at <http://localhost:8888>
5. **Set Up Monitoring**: Configure Grafana dashboards
6. **Enable Backups**: Set up automated backups
7. **Configure Alerts**: Set up Prometheus alerts

---

**Project Structure**: 8 directories + 11 core files
**Status**: ✅ Production-ready
**License**: MIT

---

**Signature**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

---

## Status and Verification

Current verified readiness, deployment evidence, and test baseline are maintained in [docs/project-status.md](docs/project-status.md).

## Codex Deterministic Full Setup and Proof (Canonical)

Use this command for the deterministic setup/proof path:

```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

Fast checks:

```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --dry-run
make deterministic-proof
```

For deterministic proof, this canonical path supersedes ad hoc command combinations.
