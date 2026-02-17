# Project Status and Verification Baseline

**Date:** 2026-02-17  
**Version:** 1.0  
**Status:** Active

---

## Purpose

This is the single source of truth for current project readiness statements in root documentation (`README.md`, `QUICKSTART.md`, `AGENTS.md`).

To prevent drift, root docs should link here instead of duplicating numeric pass/coverage/grade claims.

## Current Verified Baseline (2026-02-17)

- Runtime standard: Podman + `podman-compose` (no Docker runtime commands in runbooks).
- Deployment standard: run from `config/compose` with explicit project isolation (`COMPOSE_PROJECT_NAME=janusgraph-demo`).
- Podman connection standard: set `PODMAN_CONNECTION` to the active machine connection in your environment.
- Determinism status: strongly repeatable, but not yet fully deterministic end-to-end.

## Determinism Track

Authoritative implementation and planning docs:

1. `docs/implementation/audits/codex-podman-wxd-deployment-live-notebook-proof-remediation-log-2026-02-17.md`
2. `docs/implementation/remediation/codex-full-deterministic-setup-and-run-motion-plan-2026-02-17.md`
3. `docs/implementation/audits/codex-podman-wxd-fresh-machine-enforcement-matrix-2026-02-17.md`

## Update Policy

- Update this file whenever a deployment proof run, full notebook run, or CI quality baseline changes.
- Keep historical detail in audit/remediation docs; keep this file concise and current.
- Root docs must reference this file for status assertions.

