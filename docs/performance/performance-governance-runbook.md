# Performance Governance Runbook

**Version**: 1.0  
**Date**: 2026-02-20  
**Status**: Active

## Purpose

This runbook defines deterministic performance governance controls used by this repository:

1. Runtime SLO regression gate.
2. Startup/import-time budget regression gate.

Both gates are CI-blocking and deterministic-safe (median over repeated samples plus significant-breach rule).

## Gate Inventory

| Gate | Module | Baseline Config | CI Job |
|---|---|---|---|
| Runtime SLO gate | `src/python/performance/slo_gate.py` | `config/performance/slo_baseline.json` | `performance-slo` |
| Startup/import budget gate | `src/python/performance/startup_budget_gate.py` | `config/performance/startup_budget_baseline.json` | `startup-budget` |

## Local Execution

Activate the standard environment first:

```bash
conda activate janusgraph-analysis
```

Run runtime SLO gate:

```bash
PYTHONPATH=. python -m src.python.performance.slo_gate \
  --baseline config/performance/slo_baseline.json \
  --scenario credential_rotation \
  --output exports/performance/slo_gate_local.json
```

Run startup/import-time gate:

```bash
PYTHONPATH=. python -m src.python.performance.startup_budget_gate \
  --baseline config/performance/startup_budget_baseline.json \
  --scenario startup_import \
  --output exports/performance/startup_budget_gate_local.json
```

## Decision Semantics

Each gate fails only when both conditions are true:

1. Median metric breaches threshold.
2. Breach count across samples is greater than or equal to `significant_breach_count`.

This avoids false positives from one-off outliers while still blocking repeatable regressions.

## Triage Playbook

If either gate fails:

1. Open the JSON report from `exports/performance/`.
2. Identify breached metric and whether breach is `budget.*` or `regression.*`.
3. If `budget.*`:
   - Treat as hard performance defect.
   - Roll back recent changes in hot paths if needed.
4. If `regression.*`:
   - Compare current medians vs baseline medians.
   - Validate if change is intentional and justified.
5. For startup/import failures:
   - Check `slowest_import` output and `import_timings_ms` map.
   - Split heavy module imports or defer optional imports.
6. For runtime SLO failures:
   - Inspect response-time percentiles and request rate shifts.
   - Review batching, caching, and retry behavior changes.
7. If behavior change is intentional and accepted:
   - Re-baseline in `config/performance/*.json`.
   - Record rationale and evidence in docs before merge.

## Re-baselining Policy

Update baselines only when all conditions are met:

1. Deterministic notebook contract remains green (`15/15`).
2. Security and type/lint quality gates remain green.
3. Architectural reason for metric shift is documented.
4. Baseline update is reviewed as a dedicated change.

## Evidence Expectations

For each significant performance-related PR, attach:

1. `exports/performance/slo_gate_*.json`
2. `exports/performance/startup_budget_gate_*.json`
3. Short summary of changed thresholds (if any)

## References

1. `.github/workflows/quality-gates.yml`
2. `config/performance/slo_baseline.json`
3. `config/performance/startup_budget_baseline.json`
4. `docs/project-status.md`
