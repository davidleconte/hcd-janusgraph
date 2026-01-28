# Deployment Guide

**File**: docs/DEPLOYMENT.md  
**Created**: 2026-01-28T10:36:45.123  
**Author**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117

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
podman-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

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

**Signature**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
