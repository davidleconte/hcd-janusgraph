# Baseline Protection Test Plan (Go/No-Go Framework)

**Date:** 2026-03-27  
**Created (UTC):** 2026-03-27T13:17:53Z  
**Created (Local):** 2026-03-27 14:17:53 CET  
**POC:** Platform Engineering + Domain Engineering + Compliance  
**Status:** Active (Pre-Change Control Plan)  
**TL;DR:** This plan defines exact validation commands, domain pass/fail thresholds, and backup/restore procedures so improvements can proceed without breaking determinism, notebooks, data generation, ingestion/integration, or OpenSearch behavior.

---

## 1) Go/No-Go Policy

A change batch is **GO** only if all mandatory gates below pass.

### Mandatory gates
1. Deterministic wrapper pass (`exit_code=0`)
2. Notebook run integrity pass (no error-cell regressions)
3. Data generation sanity pass (seeded reproducibility unchanged for baseline fixtures)
4. Integration/API contract pass (no schema/ID drift)
5. OpenSearch search/vector compatibility pass

If any mandatory gate fails => **NO-GO** and execute rollback path (Section 7).

---

## 2) Domain Test Matrix (Exact Commands + Pass/Fail Thresholds)

> **Environment precondition**
>
> ```bash
> conda activate janusgraph-analysis
> export API_JWT_SECRET="test-jwt-secret-not-for-production"
> export api_jwt_secret="$API_JWT_SECRET"
> export VAULT_ADDR="http://localhost:8200"
> export VAULT_TOKEN="${VAULT_ROOT_TOKEN:-}"
> ```

## A) Determinism & Runtime Contract (Critical)

### Command
```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

### Pass criteria
- Command exits `0`
- `exports/deterministic-status.json` exists
- `exit_code` in status file is `0`
- Determinism verification and drift checks pass
- No gate failure codes (`G0`–`G10`)

### Fail criteria
- Non-zero exit code
- Missing status artifact
- Any gate fail or drift mismatch against canonical baseline

---

## B) Notebook Execution & Output Integrity (Critical)

### Command
```bash
bash scripts/testing/run_demo_pipeline_repeatable.sh
```

### Pass criteria
- Notebook report artifact exists in latest `exports/demo-*/`
- Banking + exploratory notebook suite completes with no error-cell regressions
- No notebook previously PASS becomes FAIL

### Fail criteria
- Missing notebook report
- Any notebook runtime failure or new error cells
- Integrity validation fails

---

## C) Data Generation Reproducibility (Critical)

### Command
```bash
conda run -n janusgraph-analysis PYTHONPATH=. \
  python -m pytest banking/data_generators/tests -v --no-cov
```

### Pass criteria
- Generator tests pass
- Seeded deterministic tests pass
- No referential-integrity regression in generated entities/events

### Fail criteria
- Deterministic test mismatch
- ID/linkage regressions
- Generator exceptions or schema breakage

---

## D) Streaming Ingestion & Integration Safety (High)

### Command
```bash
conda run -n janusgraph-analysis PYTHONPATH=. \
  python -m pytest banking/streaming/tests -v --no-cov
```

### Optional integration command (if services up)
```bash
conda run -n janusgraph-analysis PYTHONPATH=. VAULT_ADDR=$VAULT_ADDR VAULT_TOKEN=$VAULT_TOKEN \
  python -m pytest tests/integration/ -v --no-cov --timeout=120
```

### Pass criteria
- Streaming unit tests pass
- No event schema compatibility break
- Integration tests do not introduce new failures in ingest paths

### Fail criteria
- Consumer/producer contract failures
- Topic payload mismatch or deserialization errors
- New ingestion-path integration failures

---

## E) API/Repository Contract Stability (High)

### Command
```bash
conda run -n janusgraph-analysis PYTHONPATH=. \
  python -m pytest tests/unit -v --no-cov
```

### Pass criteria
- Unit tests pass for API/repository layers
- Existing response contracts for notebooks remain compatible

### Fail criteria
- Contract-related unit failures
- Breaking field/shape changes impacting notebooks or integrations

---

## F) OpenSearch Compatibility & Search Behavior (High)

### Command
```bash
conda run -n janusgraph-analysis PYTHONPATH=. OPENSEARCH_USE_SSL=false \
  python -m pytest tests/integration -k opensearch -v --no-cov --timeout=120
```

### Pass criteria
- OpenSearch integration tests pass
- Existing vector/search flows remain functional
- No index mapping incompatibility introduced

### Fail criteria
- Mapping conflicts
- Query failures in existing scenarios
- Relevance behavior regression beyond approved tolerance envelope

---

## 3) Performance/SLA Safety Thresholds

### Primary threshold
- Time-to-notebook-ready total <= **17m target**
- Warning: `>17m and <=20m`
- Breach: `>20m`

Reference: `docs/operations/time-to-notebook-ready-sla.md`

### No-go trigger
- Any repeatable breach (`>20m`) on two consecutive controlled reruns after warm-up annotation

---

## 4) Minimum Change-Batch Validation Sequence

Run in this order for every implementation batch:

1. Deterministic wrapper (Section A)
2. Notebook repeatable pipeline (Section B)
3. Data generator tests (Section C)
4. Streaming tests (Section D)
5. API/unit tests (Section E)
6. OpenSearch integration checks (Section F)

**Rule:** stop at first failure; do not proceed to next stage until resolved.

---

## 5) Backup Strategy (Pre-Change)

## A) Git safety
1. Ensure clean baseline commit on `master`
2. Create feature branch for each improvement batch
3. Tag pre-change baseline:

```bash
git tag -a baseline-pre-improvements-2026-03-27 -m "Baseline before fraud-realism implementation"
git push origin baseline-pre-improvements-2026-03-27
```

## B) Artifact safety
Create backup directory for baseline evidence:

```bash
mkdir -p exports/baseline-backup-2026-03-27
cp -R exports/deterministic-status.json exports/baseline-backup-2026-03-27/ 2>/dev/null || true
cp -R exports/demo-* exports/baseline-backup-2026-03-27/ 2>/dev/null || true
```

## C) Config baseline snapshots
```bash
cp requirements.txt exports/baseline-backup-2026-03-27/requirements.txt.snapshot
cp requirements-dev.txt exports/baseline-backup-2026-03-27/requirements-dev.txt.snapshot
cp config/compose/docker-compose.full.yml exports/baseline-backup-2026-03-27/docker-compose.full.yml.snapshot
```

---

## 6) Restore Options

## Option 1: Fast code rollback (preferred)
```bash
git reset --hard baseline-pre-improvements-2026-03-27
git clean -fd
```

## Option 2: Restore specific files only
```bash
git checkout baseline-pre-improvements-2026-03-27 -- \
  docs/operations \
  scripts/testing \
  scripts/deployment \
  banking/notebooks \
  banking/data_generators \
  banking/streaming \
  src/python
```

## Option 3: Recover baseline artifacts
```bash
cp -R exports/baseline-backup-2026-03-27/* exports/
```

## Option 4: Full deterministic re-baseline verification
```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

---

## 7) Rollback Triggers (Automatic NO-GO)

Rollback is mandatory if any of the below occurs:

1. Deterministic wrapper fails or drift check fails
2. Notebook PASS set regresses
3. Data generator deterministic tests regress
4. Streaming/OpenSearch compatibility breaks
5. API contract breaks notebook/integration assumptions
6. Repeated SLA breach (`>20m`) not explained by accepted transient warm-up causes

---

## 8) Evidence & Audit Logging for Each Batch

For every implementation batch, attach:

- Commit hash and branch
- Deterministic status artifact path
- Notebook report path
- Test command outputs and pass/fail summary
- SLA timing result
- Decision: GO or NO-GO
- If NO-GO: rollback command executed + post-rollback verification result

---

## 9) Operational Notes

- Keep improvements **additive-first** (new scenarios before altering baseline scenario behavior).
- Do not modify determinism-sensitive files without explicit governance and review.
- Keep all readiness claims evidence-backed and checkpointed with timestamps.

---

## 10) Related Documents

- `docs/operations/baseline-assessment-matrix-2026-03-27.md`
- `docs/operations/fraud-realism-audit-2026-03-27.md`
- `docs/operations/notebook-business-audit-remediation-plan.md`
- `docs/operations/determinism-acceptance-criteria-checklist.md`
- `docs/operations/time-to-notebook-ready-sla.md`
