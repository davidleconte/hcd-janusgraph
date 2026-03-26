# Time-to-Notebook-Ready SLA

**Date:** 2026-03-26  
**POC:** Platform Engineering (Determinism/Runtime)  
**Status:** Active  
**Reference run:** `exports/demo-20260326T182810Z`  
**TL;DR:** Target end-to-end time from deterministic scratch reset to notebook-ready with seeded data is **≤ 17 minutes** (warning at > 17m, breach at > 20m).

---

## 1) SLA Definition

**Service objective:**  
From pipeline start to the point where notebooks can be executed with validated seeded data (post-deploy, post-contract checks, post-seed, prereq proof complete).

**Primary SLO:**  
- **Notebook-ready total time:** `<= 17m 00s` (target)

**Operational thresholds:**  
- **Warning:** `> 17m 00s` and `<= 20m 00s`
- **Breach:** `> 20m 00s`

---

## 2) Phase Targets (Budget Model)

| Phase | Target | Warning | Breach | Notes |
|---|---:|---:|---:|---|
| Deterministic reset | <= 2m 00s | > 2m 30s | > 3m 00s | Includes state cleanup and reset validation |
| Deploy + readiness + runtime contracts | <= 8m 00s | > 9m 00s | > 10m 00s | Includes image/build pull effects and health convergence |
| Seed + validate graph data | <= 6m 00s | > 7m 00s | > 8m 00s | Includes sanctions/enrichment and write verification |
| Notebook prereq proof + handoff | <= 1m 00s | > 1m 30s | > 2m 00s | Final readiness gate before notebook start |
| **Total notebook-ready** | **<= 17m 00s** | **> 17m to 20m** | **> 20m** | Canonical SLA outcome |

---

## 3) Baseline Observation (Reference Run)

From `demo-20260326T182810Z`:
- Approx notebook-ready: **~16m 08s**
- First notebook execution timestamp: `2026-03-26T18:44:18Z`
- Seed loader reported total time: `352.9s` (~5m53s)

Interpretation:
- Current baseline is **within target SLA**.
- Largest contributors remain deploy/readiness and seed phase runtime.

---

## 4) Measurement Contract

**Required evidence artifacts per run:**
- `exports/<run-id>/pipeline_summary.txt`
- `exports/<run-id>/seed_graph.log`
- `exports/<run-id>/notebook_run_report.tsv`
- `exports/deterministic-status.json`

**Pass condition for timing SLA:**
1. Deterministic wrapper exit code `0`
2. All gating checks pass
3. Notebook-ready total `<= 17m`
4. Notebook execution report present (first execution timestamp available)

---

## 5) Runbook Actions on Warning/Breach

### Warning band (>17m to 20m)
- Capture phase deltas and identify dominant phase.
- Check cold-cache behavior (image/model pulls) and annotate run metadata.
- Re-run once to distinguish transient warm-up from regression.

### Breach band (>20m)
- Open incident against deterministic runtime.
- Attach full gate timings and logs from the four evidence artifacts.
- Trigger targeted remediation:
  - Podman machine resource verification (12 CPU / 24 GB / 250 GB)
  - Deploy/readiness diagnostics
  - Seed performance diagnostics (embedding/model download path, I/O bottlenecks)
- Revalidate with a clean deterministic rerun.

---

## 6) Review Cadence

- **Weekly:** verify p50/p95 notebook-ready timing against SLA.
- **On dependency/runtime changes:** mandatory deterministic rerun and SLA re-baseline check.
- **On breaches:** post-incident action items tracked before release gate clearance.