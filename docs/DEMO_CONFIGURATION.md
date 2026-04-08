# Demo-Specific Configuration Guide

**Purpose:** Comprehensive documentation of all configuration choices optimized for demo execution

**Last Updated:** 2026-04-08  
**Applies To:** Version 1.4.0+

---

## Quick Reference

| Setting | Value | Location | Purpose |
|---------|-------|----------|---------|
| DEMO_SEED | 42 | `run_demo_pipeline_repeatable.sh` | Reproducible data generation |
| JANUSGRAPH_PORT | 18182 | `environment.yml` | Podman-mapped port |
| JANUSGRAPH_USE_SSL | false | `environment.yml` | Demo stability (no certs) |
| OPENSEARCH_USE_SSL | false | `environment.yml` | Demo stability (no certs) |
| COMPOSE_PROJECT_NAME | janusgraph-demo | `.env` | Podman isolation |
| DEMO_NOTEBOOK_TOTAL_TIMEOUT | 420 | `run_demo_pipeline_repeatable.sh` | 7 min per notebook |
| DEMO_NOTEBOOK_CELL_TIMEOUT | 180 | `run_demo_pipeline_repeatable.sh` | 3 min per cell |

---

## Environment Variables

### Conda Environment (Pre-configured)

Set in `environment.yml`:
```yaml
variables:
  JANUSGRAPH_PORT: "18182"
  JANUSGRAPH_USE_SSL: "false"
  OPENSEARCH_USE_SSL: "false"
```

**Activation:**
```bash
conda activate janusgraph-analysis
echo $JANUSGRAPH_PORT      # Should show: 18182
echo $JANUSGRAPH_USE_SSL   # Should show: false
```

### Deterministic Settings

Set in `scripts/testing/run_demo_pipeline_repeatable.sh`:
```bash
DEMO_SEED=42                          # Fixed seed for reproducibility
DEMO_DETERMINISTIC_MODE=1             # Enable all determinism features
DEMO_STREAMING_DETERMINISTIC_IDS=1    # Deterministic event IDs
PYTHONHASHSEED=0                      # Deterministic hash ordering
DEMO_RESET_STATE=1                    # Clean state between runs
```

### Podman Isolation

Required for multi-project environments:
```bash
export COMPOSE_PROJECT_NAME=janusgraph-demo
export PODMAN_CONNECTION=podman-wxd  # Or your machine name
```

**Verification:**
```bash
podman ps --filter "name=janusgraph-demo"
# All containers should be prefixed with: janusgraph-demo_
```

---

## SSL/TLS Configuration

### Demo Mode (Current - Recommended)

**Configuration:**
- SSL disabled for JanusGraph, OpenSearch
- No certificate management required
- Suitable for local demos and development

**Why Disabled:**
- Avoids certificate generation complexity
- Eliminates certificate expiration issues
- Simplifies troubleshooting
- Faster connection establishment

**Security Note:** Demo mode is for **local development only**. Never use in production or on public networks.

### Production Mode (Future)

**When to Enable:**
- Production deployments
- Staging environments
- Public-facing demos
- Compliance requirements

**How to Enable:**
```bash
# 1. Generate certificates
./scripts/security/generate_certificates.sh

# 2. Update environment
export JANUSGRAPH_USE_SSL=true
export OPENSEARCH_USE_SSL=true

# 3. Deploy with production overlay
cd config/compose
podman-compose -f docker-compose.full.yml -f docker-compose.prod.yml up -d
```

---

## Service Resource Limits

Configured in `config/compose/docker-compose.full.yml`:

```yaml
hcd-server:
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 8G
      reservations:
        cpus: '2.0'
        memory: 4G
```

**Minimum Requirements:**
- **CPU:** 8 cores (12 recommended for deterministic pipeline)
- **RAM:** 16GB (24GB recommended)
- **Disk:** 50GB available

**Podman Machine Configuration:**
```bash
podman machine init \
  --cpus 12 \
  --memory 24576 \
  --disk-size 250 \
  --now
```

---

## Data Generation Configuration

### Volume Settings (Demo-Optimized)

Small volumes for fast execution:
```python
# In notebooks and scripts
person_count = 5-100        # Varies by notebook
company_count = 2-20        # Varies by notebook
account_count = 10-200      # Varies by notebook
transaction_count = 20-1000 # Varies by notebook
communication_count = 5-50  # Varies by notebook
```

### Seed Management

**Fixed Seed (Deterministic):**
```python
from banking.data_generators.orchestration import GenerationConfig

config = GenerationConfig(
    seed=42,  # Fixed for reproducibility
    person_count=100,
)
```

**Random Seed (Non-Deterministic):**
```python
import time
config = GenerationConfig(
    seed=int(time.time()),  # Different each run
    person_count=100,
)
```

---

## Troubleshooting Guide

### Issue: Notebooks Timeout

**Symptoms:**
- Notebooks fail with timeout error
- Execution exceeds 7 minutes

**Solutions:**
```bash
# Option 1: Increase timeout
export DEMO_NOTEBOOK_TOTAL_TIMEOUT=600  # 10 minutes

# Option 2: Reduce data volume
# Edit notebook cells to reduce person_count, transaction_count, etc.

# Option 3: Check system resources
podman stats  # Monitor CPU/memory usage
```

### Issue: SSL Certificate Errors

**Symptoms:**
- Connection refused errors
- Certificate validation failures

**Solutions:**
```bash
# Verify SSL is disabled
echo $JANUSGRAPH_USE_SSL  # Should be: false
echo $OPENSEARCH_USE_SSL  # Should be: false

# If enabled, disable it
conda env config vars set JANUSGRAPH_USE_SSL=false OPENSEARCH_USE_SSL=false
conda deactivate && conda activate janusgraph-analysis
```

### Issue: Podman Connection Fails

**Symptoms:**
- "Cannot connect to Podman" errors
- Services not starting

**Solutions:**
```bash
# Check machine status
podman machine list

# If stopped, start it
podman machine start

# Verify connection
podman ps

# If still failing, recreate machine
podman machine stop
podman machine rm
podman machine init --cpus 12 --memory 24576 --disk-size 250 --now
```

### Issue: Port Conflicts

**Symptoms:**
- "Port already in use" errors
- Services fail to start

**Solutions:**
```bash
# Check what's using the port
lsof -i :18182  # JanusGraph
lsof -i :9200   # OpenSearch
lsof -i :19042  # HCD

# Verify project isolation
podman ps --filter "name=janusgraph-demo"

# If another project is running, stop it
podman-compose -p other-project down
```

---

## Demo Execution Checklist

### Pre-Demo Setup (5 minutes)

- [ ] Conda environment activated: `conda activate janusgraph-analysis`
- [ ] Podman machine running: `podman machine list` shows "Running"
- [ ] Project isolation set: `echo $COMPOSE_PROJECT_NAME` shows "janusgraph-demo"
- [ ] SSL disabled: `echo $JANUSGRAPH_USE_SSL` shows "false"
- [ ] Sufficient resources: 12 CPUs, 24GB RAM available
- [ ] Clean state: No containers from previous runs

### Deployment (2 minutes)

```bash
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh
sleep 90  # Wait for services
```

### Verification (1 minute)

- [ ] All services running: `podman ps --filter "name=janusgraph-demo"`
- [ ] OpenSearch healthy: `curl http://localhost:9200/_cluster/health`
- [ ] JanusGraph responsive: `curl http://localhost:8182?gremlin=g.V().count()`
- [ ] Graph seeded: Vertex count > 0

### Notebook Execution (6 minutes)

```bash
cd ../..
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

### Post-Demo Cleanup (1 minute)

```bash
cd config/compose
bash ../../scripts/deployment/stop_full_stack.sh
```

---

## Performance Expectations

### Baseline Metrics (2026-04-02)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Total notebook time | <10 min | 6 min | ✅ Excellent |
| Notebook success rate | 100% | 100% (19/19) | ✅ Perfect |
| Error count | 0 | 0 | ✅ Perfect |
| Service startup | <90 sec | ~90 sec | ✅ Good |
| Graph seed time | <30 sec | ~20 sec | ✅ Excellent |
| Memory usage (peak) | <20GB | ~16GB | ✅ Good |
| CPU usage (avg) | <80% | ~60% | ✅ Good |

---

## Related Documentation

- [README.md](../README.md) - Project overview
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
- [AGENTS.md](../AGENTS.md) - AI agent guidance
- [docs/project-status.md](project-status.md) - Current status
- [docs/IMPLEMENTATION_PLAN_2026-04-08.md](IMPLEMENTATION_PLAN_2026-04-08.md) - Enhancement plan

---

**Maintained By:** Platform Engineering Team  
**Review Cadence:** Monthly  
**Last Review:** 2026-04-08