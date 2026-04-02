# Project Status and Verification Baseline

**Date:** 2026-04-02  
**Version:** 1.4.0  
**Status:** Active

---

## Purpose

This is the single source of truth for current project readiness statements in root documentation (`README.md`, `QUICKSTART.md`, `AGENTS.md`).

To prevent drift, root docs should link here instead of duplicating numeric pass/coverage/grade claims.

## Current Verified Baseline (2026-04-02)

- Runtime standard: Podman + `podman-compose` (no Docker runtime commands in runbooks).
- Deployment standard: run from `config/compose` with explicit project isolation (`COMPOSE_PROJECT_NAME=janusgraph-demo`).
- Podman connection standard: set `PODMAN_CONNECTION` to the active machine connection in your environment.
- Determinism status: canonical deterministic setup/proof is enforced via `scripts/deployment/deterministic_setup_and_proof_wrapper.sh` with strict notebook determinism checks enabled by default.
- Latest deterministic proof run: `exports/deterministic-status.json` reports `exit_code=0` (timestamp `2026-04-02T10:40:09.3NZ`), pipeline run id `demo-20260402T101618Z`.
- Notebook determinism baseline: PASS from `exports/demo-20260402T101618Z/notebook_run_report.tsv`.
- Coverage gate baseline: enforced `--cov-fail-under=70` in CI and local pytest defaults.
- Type-check baseline: canonical mypy path is `mypy src/python banking/ --ignore-missing-imports`.
- Performance governance baseline: deterministic CI gates for runtime SLO and startup/import budgets are configured in `.github/workflows/quality-gates.yml`.
- Observability baseline: deterministic gate failures (`G0`/`G2`/`G3`/`G5`/`G6`/`G7`/`G8`/`G9`) are mapped to alert classes and triage runbooks in `docs/operations/deterministic-gate-alert-runbook-mapping.md` with machine mapping in `config/monitoring/deterministic-gate-alert-map.yml`.
- Local performance and CI-equivalent quality details are maintained in run/workflow artifacts and should be referenced from the latest verification evidence for this snapshot (`demo-20260402T101618Z`) instead of duplicating dated numeric summaries here.

## Determinism Track

Authoritative implementation and planning docs:

1. `docs/implementation/audits/codex-podman-wxd-deployment-live-notebook-proof-remediation-log-2026-02-17.md`
2. `docs/implementation/remediation/codex-full-deterministic-setup-and-run-motion-plan-2026-02-17.md`
3. `docs/implementation/audits/codex-podman-wxd-fresh-machine-enforcement-matrix-2026-02-17.md`

## Latest Verification Evidence (2026-04-02)

1. `exports/deterministic-status.json` (exit_code `0`, run `demo-20260402T101618Z`)
2. `exports/demo-20260402T101618Z/pipeline_summary.txt`
3. `exports/demo-20260402T101618Z/notebook_run_report.tsv`
4. `exports/demo-20260402T101618Z/determinism.log`
5. `exports/demo-20260402T101618Z/drift_detection.log`
6. `exports/demo-20260402T101618Z/kpi_drift.log`
7. `exports/demo-20260402T101618Z/kpi_trends.log`
8. `exports/demo-20260402T101618Z/kpi_bundle.log`

## Update Policy

- Update this file whenever a deployment proof run, full notebook run, or CI quality baseline changes.
- Keep historical detail in audit/remediation docs; keep this file concise and current.
- Root docs must reference this file for status assertions.
