# Deployment Guide

**File**: docs/DEPLOYMENT.md
**Created**: 2026-01-28T10:36:45.123
**Author**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

---

## Overview

This guide covers deployment procedures for dev, staging, and production environments.

## Prerequisites

- Podman 4.9+ installed
- `.env` file configured
- All images built

## Development Deployment

```bash
# Use dev environment
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# Or with make
make deploy
```

## Staging Deployment

```bash
# Use staging config
cp config/environments/staging/.env.example .env
# Edit .env with staging values

# Deploy
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh
```

## Production Deployment

### Manual Deployment

```bash
# 1. Backup current data
bash scripts/backup/backup_volumes.sh

# 2. Use production config
cp config/environments/prod/.env.example .env
# Edit .env with production values

# 3. Deploy with health checks
cd config/compose
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo -f <full-stack-compose-file> -f <prod-compose-file> up -d

# 4. Verify deployment
bash scripts/testing/run_tests.sh

# 5. Monitor startup
watch podman ps
```

### GitHub Actions Deployment

Use the manual workflow trigger:

1. Go to Actions → Deploy to Production
2. Enter version (e.g., v1.0.0)
3. Type "CONFIRM"
4. Click Run workflow
5. Approve in environment settings

## Rollback Procedure

```bash
# 1. Stop current stack
bash scripts/deployment/stop_full_stack.sh

# 2. Restore from backup
bash scripts/backup/restore_volumes.sh /backups/janusgraph/hcd_<timestamp>

# 3. Deploy previous version
git checkout <previous-version>
bash scripts/deployment/deploy_full_stack.sh
```

---

**Signature**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

## Codex Fresh-Machine Deployment Sequence (2026-02-17)

Use this sequence when deploying from a new Podman machine state.

### 1) Validate machine and connection

```bash
podman machine list
podman system connection list
export PODMAN_CONNECTION=<active-connection>
podman --remote ps
```

### 2) Build mandatory local HCD image

```bash
podman build -t localhost/hcd:1.2.3 -f docker/hcd/Dockerfile .
```

### 3) Deploy with project isolation

```bash
cd config/compose
COMPOSE_PROJECT_NAME=janusgraph-demo podman-compose -p janusgraph-demo -f <full-stack-compose-file> up -d
```

### 4) Vault initialization/unseal (fresh environment)

If Vault reports `security barrier not initialized`, perform init/unseal against compose container name:

```bash
podman --remote exec -it janusgraph-demo_vault_1 vault operator init
podman --remote exec -it janusgraph-demo_vault_1 vault operator unseal <unseal-key-1>
podman --remote exec -it janusgraph-demo_vault_1 vault operator unseal <unseal-key-2>
podman --remote exec -it janusgraph-demo_vault_1 vault operator unseal <unseal-key-3>
```

### 5) Analytics API env contract

`analytics-api` must receive `OPENSEARCH_INITIAL_ADMIN_PASSWORD` and include runtime dependencies validated in remediation R-05 through R-13.

### 6) Deterministic live notebook proof

```bash
export DEMO_SEED=42
export DEMO_NOTEBOOK_TOTAL_TIMEOUT=1800
export DEMO_NOTEBOOK_CELL_TIMEOUT=300

PODMAN_CONNECTION=$PODMAN_CONNECTION bash scripts/testing/run_notebooks_live_repeatable.sh
```

Proof target: `15/15 PASS` with a generated `notebook_run_report.tsv` in `exports/<run-id>/`.

Reference: `docs/implementation/audits/codex-podman-wxd-fresh-machine-enforcement-matrix-2026-02-17.md`
