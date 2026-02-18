# Codex Podman-WXD Fresh Machine Enforcement Matrix

**Date:** 2026-02-17
**Version:** 1.0
**Status:** Active
**Source of truth:** `docs/implementation/audits/codex-podman-wxd-deployment-live-notebook-proof-remediation-log-2026-02-17.md`

## Purpose

This matrix enforces, in canonical operator/developer documentation, every remediation item proven during the Podman-WXD recovery and full live notebook proof run.

## Enforcement Matrix (R-01 to R-18)

| Remediation ID | Enforced requirement | Canonical documentation location | Enforcement state |
|---|---|---|---|
| R-01 | Podman machine must be running before any deployment action | `docs/guides/setup-guide.md`, `docs/operations/operations-runbook.md` | Enforced |
| R-02 | Build `localhost/hcd:1.2.3` locally from repo root before deploy on fresh machine | `docs/guides/deployment-guide.md`, `docs/guides/setup-guide.md` | Enforced |
| R-03 | Vault must be initialized/unsealed on new environment | `docs/guides/deployment-guide.md`, `docs/operations/operations-runbook.md` | Enforced |
| R-04 | Use compose-prefixed Vault container name (`janusgraph-demo_vault_1`) for manual init/unseal fallback | `docs/operations/operations-runbook.md` | Enforced |
| R-05 | `analytics-api` runtime includes `slowapi` | `docs/development/deployment-verification.md` | Enforced |
| R-06 | `analytics-api` runtime includes `pydantic-settings`, `python-json-logger`, `pyjwt` | `docs/development/deployment-verification.md` | Enforced |
| R-07 | API image includes `banking` package path | `docs/development/deployment-verification.md` | Enforced |
| R-08 | `/var/log/janusgraph` writable by runtime user in API container | `docs/development/deployment-verification.md` | Enforced |
| R-09 | API runtime includes `pyotp` | `docs/development/deployment-verification.md` | Enforced |
| R-10 | API runtime includes `qrcode[pil]` | `docs/development/deployment-verification.md` | Enforced |
| R-11 | `OPENSEARCH_INITIAL_ADMIN_PASSWORD` must be injected into `analytics-api` env | `docs/guides/deployment-guide.md`, `docs/development/deployment-verification.md` | Enforced |
| R-12 | API runtime includes OpenTelemetry core/exporter/instrumentation dependencies | `docs/development/deployment-verification.md` | Enforced |
| R-13 | API runtime includes `requests` (OTEL requests instrumentation dependency) | `docs/development/deployment-verification.md` | Enforced |
| R-14 | Notebook proof must run on active Podman connection (validated run used `podman-wxd-root`) | `docs/guides/deployment-guide.md`, `docs/operations/operations-runbook.md` | Enforced |
| R-15 | Exploratory notebooks path must resolve to `/workspace/notebooks-exploratory` with compose mount present | `docs/development/deployment-verification.md`, `scripts/README.md` | Enforced |
| R-16 | Jupyter runtime must include `pydantic`, `pydantic-settings`, `email-validator` for live notebook imports | `docs/development/deployment-verification.md` | Enforced |
| R-17 | TBML notebook must handle empty stats map safely (`.get` defaults) | `docs/development/deployment-verification.md` | Enforced |
| R-18 | Insider notebook must handle empty/missing DataFrame columns safely | `docs/development/deployment-verification.md` | Enforced |

## Deterministic Full-Run Baseline

Use this canonical sequence for fresh-machine proof runs:

1. Validate machine and active connection (`podman machine list`, `podman system connection list`).
2. Export active connection (`export PODMAN_CONNECTION=<active-connection>`).
3. Build HCD local image from repo root (`podman build -t localhost/hcd:1.2.3 -f docker/hcd/Dockerfile .`).
4. Deploy stack from `config/compose` with project isolation (`janusgraph-demo`).
5. Initialize and unseal Vault when required.
6. Validate service health (`vault`, `analytics-api`, `jupyter`, `hcd-server`, `janusgraph`).
7. Run deterministic notebook proof (`scripts/testing/run_notebooks_live_repeatable.sh`).
8. Archive `notebook_run_report.tsv` evidence under `exports/<run-id>/`.

## Proven reference evidence

- Final full sweep result: **15/15 PASS, 0 FAIL**
- Evidence artifact: `exports/live-notebooks-final-20260217T170000Z/notebook_run_report.tsv`


## P0 Governance Enforcement Addendum (2026-02-18)

| Remediation ID | Enforced requirement | Canonical documentation location | Enforcement state |
|---|---|---|---|
| R-19 | CI deterministic-sensitive path protection is required on PRs | `.github/workflows/determinism-guard.yml`, `scripts/validation/check_determinism_sensitive_paths.sh` | Enforced |
| R-20 | One canonical deterministic command wrapper is required for proof runs | `README.md`, `QUICKSTART.md`, `AGENTS.md` | Enforced |
| R-21 | CI quality and security checks are hard-fail in reusable gates | `.github/workflows/quality-gates.yml`, `.github/workflows/security-scan.yml` | Enforced |
| R-22 | Placeholder deployment workflows are replaced with explicit validation/gate semantics | `.github/workflows/deploy-dev.yml`, `.github/workflows/deploy-prod.yml` | Enforced |
