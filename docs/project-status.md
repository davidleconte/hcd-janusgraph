# Project Status and Verification Baseline

**Date:** 2026-02-20  
**Version:** 1.2  
**Status:** Active

---

## Purpose

This is the single source of truth for current project readiness statements in root documentation (`README.md`, `QUICKSTART.md`, `AGENTS.md`).

To prevent drift, root docs should link here instead of duplicating numeric pass/coverage/grade claims.

## Current Verified Baseline (2026-02-20)

- Runtime standard: Podman + `podman-compose` (no Docker runtime commands in runbooks).
- Deployment standard: run from `config/compose` with explicit project isolation (`COMPOSE_PROJECT_NAME=janusgraph-demo`).
- Podman connection standard: set `PODMAN_CONNECTION` to the active machine connection in your environment.
- Determinism status: canonical deterministic setup/proof is enforced via `scripts/deployment/deterministic_setup_and_proof_wrapper.sh` with strict notebook determinism checks enabled by default.
- Latest deterministic proof run: `exports/deterministic-status.json` reports `exit_code=0` (timestamp `2026-02-20T09:19:41.3NZ`), pipeline run id `demo-20260220T090523Z`.
- Notebook determinism baseline: `15/15` PASS from `exports/demo-20260220T090523Z/notebook_run_report.tsv`.
- Coverage gate baseline: enforced `--cov-fail-under=70` in CI and local pytest defaults.
- Type-check baseline: canonical mypy path is `mypy src/python banking/ --ignore-missing-imports`.
- Latest local CI-equivalent quality baseline (2026-02-20):
  - lock-sync export check: PASS
  - test gate: `2044 passed`, `18 deselected`, coverage `81.43%`
  - docstring coverage: `90.2%`
  - mypy: PASS (`Success: no issues found in 110 source files`)
  - ruff/black/isort: PASS

## Determinism Track

Authoritative implementation and planning docs:

1. `docs/implementation/audits/codex-podman-wxd-deployment-live-notebook-proof-remediation-log-2026-02-17.md`
2. `docs/implementation/remediation/codex-full-deterministic-setup-and-run-motion-plan-2026-02-17.md`
3. `docs/implementation/audits/codex-podman-wxd-fresh-machine-enforcement-matrix-2026-02-17.md`

## Latest Verification Evidence (2026-02-20)

1. `exports/deterministic-status.json`
2. `exports/demo-20260220T090523Z/pipeline_summary.txt`
3. `exports/demo-20260220T090523Z/notebook_run_report.tsv`
4. `exports/demo-20260220T090523Z/determinism.log`
5. `coverage.xml` (generated from latest quality-gate-equivalent run)

## Update Policy

- Update this file whenever a deployment proof run, full notebook run, or CI quality baseline changes.
- Keep historical detail in audit/remediation docs; keep this file concise and current.
- Root docs must reference this file for status assertions.
