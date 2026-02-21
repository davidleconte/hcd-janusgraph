# ADAL - AI Agent Guidance for Deterministic Setup

**Version:** 1.0
**Date:** 2026-02-21
**Purpose:** Quick reference for AI agents working on this project

---

## Quick Start for AI Agents

### 1. Mandatory Podman Setup

```bash
# Create Podman machine with deterministic resources (ONLY supported config)
podman machine init \
  --cpus 12 \
  --memory 24576 \   # 24 GB
  --disk-size 250 \  # 250 GB
  --now
```

### 2. Deterministic Command

```bash
# Canonical deterministic setup + proof
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

### 3. Validation Scripts

```bash
# Preflight check
bash scripts/validation/preflight_check.sh --strict

# Podman isolation
bash scripts/validation/validate_podman_isolation.sh --strict

# Kebab-case validation
bash scripts/validation/validate-kebab-case.sh
```

---

## Common Tasks

| Task | Command |
|------|---------|
| Deploy full stack | `cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh` |
| Run notebooks | `bash scripts/testing/run_notebooks_live_repeatable.sh` |
| Quality gates | `pytest tests/ -v --cov=src --cov=banking` |
| Fix kebab-case | `bash scripts/maintenance/rename-to-kebab-case.sh` |

---

## Key Files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Full project guidance |
| `docs/architecture/adr-015-deterministic-deployment.md` | Determinism strategy |
| `docs/documentation-standards.md` | Naming conventions (kebab-case) |

---

## Gate Codes

| Code | Meaning |
|------|---------|
| G0_PRECHECK | Preflight/isolation failure |
| G2_CONNECTION | Podman unreachable |
| G3_RESET | Deterministic reset failure |
| G5_DEPLOY_VAULT | Deployment failure |
| G6_RUNTIME_CONTRACT | Runtime contract failure |
| G7_SEED | Graph seed failure |
| G8_NOTEBOOKS | Notebook execution failure |
| G9_DETERMINISM | Determinism artifact mismatch |

---

## Notes for AI Agents

- Always use kebab-case for documentation files
- Never modify system caches or use deprecated commands
- Use `podman-compose` not `docker-compose`
- Always run from `config/compose` directory for deployment
- Set `COMPOSE_PROJECT_NAME=janusgraph-demo` for isolation
