# Release Note — UBO Hardening, Evidence Export Maturity, and Deterministic Proof

**Date:** 2026-04-02  
**Branch:** `master`  
**Status:** Completed

## TL;DR
Delivered and validated a full hardening slice across UBO traversal safety, circular-ownership API visibility, and deterministic multi-page case PDF evidence export. The canonical deterministic wrapper rerun passed end-to-end (`exit_code=0`) with latest evidence captured under `demo-20260402T101618Z`.

## Included commits
- `93b0201` — feat(api): harden UBO depth limits and traversal timeout fallback  
- `83234b8` — docs(status): sync version baseline and notebook inventory  
- `cc3d778` — feat(ubo): expose circular ownership flag through API response  
- `1059d80` — feat(reporting): harden deterministic PDF exporter with multi-page support  
- `6f78cdf` — docs(release): update checkpoint and deterministic proof evidence baseline  
- `c0afbf8` — fix(entity-resolution): restore class-level ATTRIBUTE_WEIGHTS compatibility alias  
- `6114819` — docs(status): remove stale dated baseline bullets from project status

## Functional outcome
- UBO API now supports safer deep traversal usage:
  - request/router bounds aligned to `max_depth <= 50`
  - repository traversal guarded with deterministic 15s timeout and direct-owner fallback
- Circular ownership detection now exposed in API contract:
  - `has_circular_ownership` propagated analytics → repository → API response
- Case evidence PDF export upgraded:
  - deterministic multi-page rendering
  - single-page truncation behavior removed
  - bundle integration remains compatible (`--pdf`)

## Deterministic verification outcome
- Canonical wrapper rerun completed successfully:
  - `exports/deterministic-status.json` → `exit_code: 0`
- Pipeline completed through deterministic gates, including:
  - notebook pass
  - artifact verification
  - drift detection
  - KPI drift/trend/bundle generation
- Run directory:
  - `exports/demo-20260402T101618Z`

## Verification references
- Wrapper status: `exports/deterministic-status.json`
- Pipeline summary: `exports/demo-20260402T101618Z/pipeline_summary.txt`
- Notebook report: `exports/demo-20260402T101618Z/notebook_run_report.tsv`
- Determinism checks:
  - `exports/demo-20260402T101618Z/determinism.log`
  - `exports/demo-20260402T101618Z/drift_detection.log`
- Governance artifacts:
  - `exports/demo-20260402T101618Z/kpi_drift.log`
  - `exports/demo-20260402T101618Z/kpi_trends.log`
  - `exports/demo-20260402T101618Z/kpi_bundle.log`
