# Deterministic Gate Alert and Runbook Mapping

**Version:** 1.0  
**Date:** 2026-02-20  
**Status:** Active

## Purpose

This document is the operational mapping between deterministic gate failures and response actions.
It closes `CODEX-P2-004` by defining one alert class per gate and deterministic triage commands.

Machine-readable source: `config/monitoring/deterministic-gate-alert-map.yml`.

## Detection Inputs

1. `exports/deterministic-status.json` (wrapper status report)
2. `failed_gate.txt` (pipeline failure code file)
3. CI quality gate logs (`performance-slo`, `startup-budget`)

## Alert Mapping (G0-G9)

| Failure Code | Alert Name | Severity | Primary Owner | First Deterministic Action |
|---|---|---|---|---|
| `G0_PRECHECK` | `DeterministicGateG0PrecheckFailed` | warning | Platform Engineering | `bash scripts/validation/preflight_check.sh --strict` |
| `G2_CONNECTION` | `DeterministicGateG2ConnectionFailed` | critical | Platform Engineering | `podman system connection list` |
| `G3_RESET` | `DeterministicGateG3ResetFailed` | warning | Platform Engineering | `bash scripts/testing/run_demo_pipeline_repeatable.sh --skip-preflight` |
| `G5_DEPLOY_VAULT` | `DeterministicGateG5DeployVaultFailed` | critical | Platform Engineering | `cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh` |
| `G6_RUNTIME_CONTRACT` | `DeterministicGateG6RuntimeContractFailed` | critical | Security + API Owners | `python scripts/validation/validate_env_contract.py --env-file .env.example --compose-env-file config/compose/.env.example` |
| `G7_SEED` | `DeterministicGateG7SeedFailed` | warning | Data Platform | `bash scripts/testing/check_graph_counts.sh` |
| `G8_NOTEBOOKS` | `DeterministicGateG8NotebooksFailed` | warning | QA + Domain Engineering | `bash scripts/testing/run_notebooks_live_repeatable.sh` |
| `G9_DETERMINISM` | `DeterministicGateG9DeterminismFailed` | critical | Platform + QA | `bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json` |

## Deterministic Triage Steps by Gate

### `G0_PRECHECK`

1. Run:
```bash
bash scripts/validation/preflight_check.sh --strict
bash scripts/validation/validate_podman_isolation.sh --strict
```
2. Fix missing runtime prerequisites and rerun deterministic wrapper.

### `G2_CONNECTION`

1. Run:
```bash
podman system connection list
podman machine list
bash scripts/validation/preflight_check.sh --strict
```
2. Ensure `PODMAN_CONNECTION` points to an active machine and rerun.

### `G3_RESET`

1. Run:
```bash
bash scripts/testing/run_demo_pipeline_repeatable.sh --skip-preflight
```
2. If reset still fails, inspect compose resources and retry deterministic wrapper.

### `G5_DEPLOY_VAULT`

1. Run:
```bash
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
podman ps
```
2. Inspect unhealthy container logs and recover stack before rerun.

### `G6_RUNTIME_CONTRACT`

1. Run:
```bash
python scripts/validation/validate_env_contract.py \
  --env-file .env.example \
  --compose-env-file config/compose/.env.example
```
2. Confirm required secrets are set (`api_jwt_secret`, Vault contract env), then rerun deterministic wrapper.

### `G7_SEED`

1. Run:
```bash
bash scripts/testing/check_graph_counts.sh
bash scripts/testing/run_demo_pipeline_repeatable.sh --skip-preflight --skip-reset --skip-deploy
```
2. Verify graph write path and seed data integrity before rerun.

### `G8_NOTEBOOKS`

1. Run:
```bash
bash scripts/testing/run_notebooks_live_repeatable.sh
```
2. Inspect notebook logs from exported run directory, fix deterministic notebook failures, rerun.

### `G9_DETERMINISM`

1. Run:
```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```
2. Compare current artifacts with baseline and resolve drift before accepting baseline updates.

## CI Quality Gate Alerts

| CI Job | Alert Name | Severity | Runbook |
|---|---|---|---|
| `performance-slo` | `QualityGatePerformanceSLOFailed` | warning | `docs/performance/performance-governance-runbook.md` |
| `startup-budget` | `QualityGateStartupBudgetFailed` | warning | `docs/performance/performance-governance-runbook.md` |

## Escalation SLA

| Severity | Ack Target | Stabilization Target |
|---|---|---|
| critical | 15 minutes | 4 hours |
| warning | 1 hour | 1 business day |

## References

1. `docs/operations/operations-runbook.md`
2. `docs/architecture/deterministic-deployment-architecture.md`
3. `docs/performance/performance-governance-runbook.md`
4. `config/monitoring/deterministic-gate-alert-map.yml`
