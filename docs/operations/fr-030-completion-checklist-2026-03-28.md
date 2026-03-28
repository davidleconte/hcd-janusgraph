# FR-030 Completion Checklist & Next-Commit File Plan

**Date:** 2026-03-28  
**POC:** David Leconte / AdaL  
**Status:** In progress (Step 1 + Step 2 complete; Step 3 active)  

## TL;DR
FR-030 slice foundation is complete (detector + generator + additive notebook scaffold).  
Step 1 (analytics records API + unit-test contract) and Step 2 (Notebook #16 graph-backed path with deterministic fallback) are complete.  
Current focus is Step 3: standardized case-evidence export output plus governance evidence updates.

---

## 1) Objective for Next Commit

Deliver **FR-030 business-complete behavior** while preserving deterministic baseline integrity:

1. Notebook #16 moves from mocked chain to graph-backed detection path(s).
2. Notebook output includes standardized **case-evidence block** (decision + reason codes + evidence payload).
3. FR-030 status and gate evidence are recorded in governance docs.
4. Canonical determinism gates remain green (no baseline drift).

---

## 2) Exact File-by-File Implementation Plan

## A. `banking/analytics/detect_mule_chains.py`
**Goal:** Expose a stable, notebook-friendly detection/evidence API on top of current detector primitives.

### Changes
- Add a public method that returns serialized alert records suitable for dataframe/reporting, e.g.:
  - `detect_mule_chains_as_records(...) -> List[Dict[str, Any]]`
- Ensure record fields include:
  - `alert_id`, `victim_account_id`, `mule_account_ids`, `cash_out_account_id`,
  - `hop_count`, `total_value`, `average_hop_minutes`, `risk_score`,
  - `reason_codes`, `rationale`, `evidence_summary`.
- Keep deterministic alert-id generation untouched.

### Acceptance
- Existing tests continue to pass.
- New helper method has dedicated unit tests for stable schema and values.

---

## B. `banking/analytics/tests/test_detect_mule_chains.py`
**Goal:** Lock the new FR-030 completion behavior with deterministic assertions.

### Add tests
- `test_detect_mule_chains_as_records_schema`
- `test_detect_mule_chains_as_records_reason_codes_present`
- `test_detect_mule_chains_as_records_deterministic_for_same_input`

### Acceptance
- FR-030 detector test suite passes cleanly.
- No regressions in existing tests.

---

## C. `banking/notebooks/16_APP_Fraud_Mule_Chains.ipynb`
**Goal:** Convert from mocked payload to graph-backed path(s) with fallback-safe execution.

### Changes
- Add cell to initialize notebook via `init_notebook(check_env=True, check_services=False)`.
- Add data retrieval path:
  - primary: fetch candidate path data from graph query outputs (through detector method or a notebook-local query cell),
  - fallback: deterministic mock path only when no graph candidates are found (do not fail notebook run).
- Render:
  - table view of alerts/evidence records,
  - `render_decision_block(...)`,
  - `render_reason_codes_block(...)`,
  - `mask_pii(...)` applied to account identifiers.

### Acceptance
- Notebook executes successfully inside repeatable pipeline context.
- Output contains decision and explainability blocks.
- No raw sensitive IDs shown in display cells.

---

## D. `docs/operations/fraud-realism-ticketized-execution-board-2026-03-27.md`
**Goal:** Reflect FR-030 progress status and planned remaining acceptance checks.

### Changes
- Update FR-030 row from pending to:
  - `IN PROGRESS (Slice 2)` or `DONE` if all gates are passed in this commit.
- Add concise evidence references:
  - detector test run
  - pipeline run directory
  - drift check output

### Acceptance
- Board status aligns with repo state and gate evidence.

---

## E. `CHECKPOINT_20260328.md`
**Goal:** Keep operational continuity.

### Changes
- Append FR-030 next-commit execution note:
  - what changed,
  - gate outcomes,
  - next pending actions (if any).

### Acceptance
- Checkpoint remains actionable and current.

---

## 3) Gate Commands (Exact)

Run in this order after implementation:

```bash
conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/analytics/tests/test_detect_mule_chains.py -v --no-cov
```

```bash
conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/data_generators/tests/test_patterns/test_pattern_generators.py banking/data_generators/tests/test_orchestration/test_master_orchestrator.py -v --no-cov
```

```bash
bash scripts/testing/run_demo_pipeline_repeatable.sh --skip-preflight
```

```bash
bash scripts/testing/detect_determinism_drift.sh exports/demo-<LATEST_RUN_DIR>
```

---

## 4) Commit Scope Rules for This Next Commit

- Include only FR-030 completion artifacts and corresponding docs/checkpoint updates.
- Exclude incidental notebook-rendered binary image diffs unless explicitly required.
- Keep canonical baseline files unchanged unless explicitly using determinism-override governance.

---

## 5) Definition of Done (FR-030)

FR-030 can be marked **DONE** when all are true:

- Detector exposes notebook-ready evidence records.
- Notebook #16 runs with graph-backed path and standardized decision/reason-code output.
- FR-030 tests pass.
- Repeatable pipeline completes.
- Drift check reports no canonical drift.
- Execution board + checkpoint updated with evidence references.
