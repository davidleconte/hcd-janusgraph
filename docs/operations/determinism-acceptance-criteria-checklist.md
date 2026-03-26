# Determinism Acceptance Criteria Checklist (Release Gate)

**Date:** 2026-03-26  
**Version:** 1.0  
**Status:** Active  
**Created At:** 2026-03-26 20:06:37 CET

This checklist is the release-gate contract for deterministic pipeline integrity.  
Use it for PR reviews, release readiness, and incident triage.

---

## Scope (When this gate is required)

Apply this checklist when changes affect deterministic-sensitive paths, including:

- `requirements.lock.txt`, `environment.yml`, `uv.lock`
- `config/compose/docker-compose.full.yml`
- `scripts/testing/*.sh` (pipeline scripts)
- `exports/determinism-baselines/CANONICAL_*`
- `*.ipynb` notebooks
- runtime contracts, seed/load behavior, or deployment orchestration

---

## A. Environment & Runtime Preconditions

- [ ] Podman machine profile is deterministic-compliant (`12 CPU / 24 GiB / 250 GiB`)
- [ ] Correct conda env active: `janusgraph-analysis`
- [ ] `scripts/validation/check_prerequisites.sh` passes
- [ ] `scripts/validation/preflight_check.sh --strict` passes
- [ ] `scripts/validation/validate_podman_isolation.sh --strict` passes

---

## B. Pipeline Gate Completion

- [ ] Wrapper run executed:
      `bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json`
- [ ] `exports/deterministic-status.json` exists
- [ ] Final `exit_code` is `0`
- [ ] No failed gate marker remains (`failed_gate.txt` empty or absent for successful run)

---

## C. Notebook Determinism Proof

- [ ] Notebook prerequisite proof passes
- [ ] Notebook run report exists (`notebook_run_report.tsv`)
- [ ] All required notebooks are `PASS`
- [ ] `error_cells = 0` for every notebook
- [ ] Notebook output integrity validation passes

---

## D. Artifact & Drift Integrity

- [ ] Deterministic artifact verification passes
- [ ] Drift detection passes:
      `scripts/testing/detect_determinism_drift.sh <run_dir>`
- [ ] Canonical checksum pointer matches intended baseline state
- [ ] Any canonical pointer change includes explicit policy acknowledgment

---

## E. Change Control & Review Policy

- [ ] Determinism-sensitive updates include commit token: `[determinism-override]`
- [ ] Commit message includes:
      `Co-Authored-By: AdaL <adal@sylph.ai>`
- [ ] Diff is minimal and scoped (no unrelated churn)
- [ ] Security posture unchanged or improved (no weakened auth/startup checks)

---

## F. Evidence Pack (Required Artifacts)

Attach/reference these in PR or release notes:

- [ ] `exports/deterministic-status.json`
- [ ] run directory path (for logs and reports)
- [ ] notebook report + validation summary
- [ ] determinism verification + drift logs
- [ ] canonical baseline file reference if updated
- [ ] checkpoint note with timestamp and summary link

---

## PR Decision Rule

**PASS** = all sections A–F satisfied.  
**CONDITIONAL PASS** = only non-determinism-sensitive docs-only deltas.  
**FAIL** = any failed gate, notebook error cells, drift mismatch, or missing evidence artifacts.
