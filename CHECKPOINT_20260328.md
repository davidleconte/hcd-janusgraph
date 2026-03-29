# Session Checkpoint - 2026-03-28

**Date:** 2026-03-28 21:25:27 CET  
**Status:** FR-030/FR-031/FR-032 complete; FR-040 in progress  
**Scope:** Deterministic-safe realism upgrades through FR-022 + FR-032 completion and FR-040 evidence-export rollout

---

## ✅ Completed Work

### FR-020 — Sanctions weighted scoring
- Implemented weighted sanctions logic.
- Tests added/updated and validated.

### FR-021 — UBO recursive control rights
- Added control-rights qualification path.
- Added circular ownership risk penalty checks.
- Added deterministic ordering assertions in unit tests.

### FR-022 — TBML economic realism
- Added benchmark-first market anomaly logic.
- Added explicit `REASON_CODE: MARKET_PRICE_DEVIATION`.
- Added route-risk indicators.
- Execution board updated to mark FR-022 done with evidence.

### FR-030 — APP mule-chain (major additive slice delivered)
- Added analytics detector + tests:
  - `banking/analytics/detect_mule_chains.py`
  - `banking/analytics/tests/test_detect_mule_chains.py`
- Added pattern generator + orchestration integration:
  - `banking/data_generators/patterns/mule_chain_generator.py`
  - `banking/data_generators/patterns/__init__.py`
  - `banking/data_generators/orchestration/master_orchestrator.py`
  - `banking/data_generators/tests/test_patterns/test_pattern_generators.py`
- Added notebook:
  - `banking/notebooks/16_APP_Fraud_Mule_Chains.ipynb`

---

## 📓 Gate Results Snapshot

- `tests/unit/analytics/test_ubo_discovery.py` ✅
- `banking/analytics/tests/test_detect_tbml.py` ✅
- `banking/analytics/tests/test_detect_mule_chains.py` ✅
- `banking/data_generators/tests/test_patterns/test_pattern_generators.py` ✅
- `banking/data_generators/tests/test_orchestration/test_master_orchestrator.py` ✅

Repeatable pipeline:
- `bash scripts/testing/run_demo_pipeline_repeatable.sh --skip-preflight`
- Determinism drift:
  - `bash scripts/testing/detect_determinism_drift.sh exports/demo-20260328T195445Z`
  - ✅ No drift detected (matches canonical baseline)

---

## 🔧 Determinism/Baseline Controls Applied

- `scripts/testing/run_notebooks_live_repeatable.sh`
  - Canonical notebook set frozen to explicit list (01..15) to avoid additive notebook hash churn.
- `scripts/testing/verify_deterministic_artifacts.sh`
  - Baseline selection updated to prefer `CANONICAL_<seed>.checksums` when present, fallback to commit-specific baseline otherwise.

---

## 🧾 Artifacts Saved

- `SUMMARY_20260328.md` (full recap, score/grade, per-notebook impact, next steps)
- `CHECKPOINT_20260328.md` (this checkpoint)

---

## 📝 FR-030 / FR-040 Progress Update (2026-03-28)

### ✅ FR-030 — APP mule-chain scenario (DONE)
- Step 1 complete: `detect_mule_chains_as_records` contract tests added in `banking/analytics/tests/test_detect_mule_chains.py` (schema + deterministic sorting).
- Step 2 complete: `banking/notebooks/16_APP_Fraud_Mule_Chains.ipynb` upgraded to live graph-backed detection with deterministic fallback-safe execution.
- Step 3 complete: standardized case-evidence export block added to notebook 16:
  - JSON: `exports/evidence/mule_chains/{alert_id}_evidence.json`
  - CSV: `exports/evidence/mule_chains/mule_chain_alerts_summary.csv`

### ✅ FR-040 — Case evidence export standardization (DONE)
- Standardized evidence export pattern implemented for notebooks #01/#02/#03 and #16/#17/#18.
- Added deterministic JSON evidence + masked summary CSV exports across scenarios:
  - `exports/evidence/sanctions/`
  - `exports/evidence/aml_structuring/`
  - `exports/evidence/fraud_detection/`
  - `exports/evidence/mule_chains/`
  - `exports/evidence/ato/`
  - `exports/evidence/procurement/`
- Notebook gate evidence:
  - `bash scripts/testing/run_notebooks_live_repeatable.sh banking/notebooks/01_Sanctions_Screening_Demo.ipynb` ✅ PASS  
    Report: `exports/live-notebooks-stable-20260328T223930Z/notebook_run_report.tsv`
  - `bash scripts/testing/run_notebooks_live_repeatable.sh banking/notebooks/02_AML_Structuring_Detection_Demo.ipynb banking/notebooks/03_Fraud_Detection_Demo.ipynb` ✅ PASS  
    Report: `exports/live-notebooks-stable-20260328T224721Z/notebook_run_report.tsv`

## ✅ FR-030 Gate Sequence Evidence (Completed)

1. `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/analytics/tests/test_detect_mule_chains.py -v --no-cov`  
   - ✅ 11 passed

2. `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/data_generators/tests/test_patterns/test_pattern_generators.py banking/data_generators/tests/test_orchestration/test_master_orchestrator.py -v --no-cov`  
   - ✅ 41 passed

3. `bash scripts/testing/run_demo_pipeline_repeatable.sh --skip-preflight`  
   - ✅ Completed successfully  
   - Evidence directory: `exports/demo-20260328T203655Z/`

4. `bash scripts/testing/detect_determinism_drift.sh exports/demo-20260328T203655Z`  
   - ✅ No drift detected (matches canonical baseline)

## 🧪 FR-031 Kickoff Evidence (2026-03-28)

1. `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/analytics/tests/test_detect_ato.py -v --no-cov`  
   - ✅ 7 passed

2. `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/analytics/tests/test_detect_ato.py banking/analytics/tests/test_detect_mule_chains.py -v --no-cov`  
   - ✅ 18 passed

3. FR-031 kickoff slice delivered:
   - `banking/analytics/detect_ato.py` (new detector with deterministic alert IDs + notebook-ready records API)
   - `banking/analytics/tests/test_detect_ato.py` (new deterministic/schema/sort contract tests)
   - `banking/analytics/__init__.py` updated exports (`ATOAlert`, `ATODetector`)
   - `banking/notebooks/17_Account_Takeover_ATO_Demo.ipynb` (new ATO investigator-cockpit scaffold with live attempt + deterministic fallback + standardized export `exports/evidence/ato/`)

4. Notebook gate execution:
   - `bash scripts/testing/run_notebooks_live_repeatable.sh banking/notebooks/17_Account_Takeover_ATO_Demo.ipynb`
   - ✅ PASS (0 error cells, 5s)
   - Report: `exports/live-notebooks-stable-20260328T212744Z/notebook_run_report.tsv`

5. Streaming gate execution (`G-STR`):
   - `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/streaming/tests -v --no-cov`
   - ✅ PASS (270 passed)

6. Deterministic proof execution (`G-DET`):
   - `bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json`
   - ✅ PASS (`exports/deterministic-status.json` shows `exit_code: 0`)
   - Run artifacts: `exports/demo-20260328T213636Z/`
   - Drift check: ✅ `exports/demo-20260328T213636Z/drift_detection.log` (no drift)

## ✅ FR-032 Evidence (2026-03-28)

1. `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/analytics/tests/test_detect_procurement.py -v --no-cov`  
   - ✅ 7 passed

2. `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/analytics/tests/test_detect_procurement.py banking/analytics/tests/test_detect_ato.py banking/analytics/tests/test_detect_mule_chains.py -v --no-cov`  
   - ✅ 25 passed

3. FR-032 slice delivered:
   - `banking/analytics/detect_procurement.py` (new deterministic procurement/vendor fraud detector + records API)
   - `banking/analytics/tests/test_detect_procurement.py` (new deterministic/schema/sort contract tests)
   - `banking/analytics/__init__.py` updated exports (`ProcurementFraudAlert`, `ProcurementFraudDetector`)
   - `banking/notebooks/18_Corporate_Vendor_Fraud_Demo.ipynb` (new procurement investigator-cockpit scaffold with live attempt + deterministic fallback + standardized export `exports/evidence/procurement/`)

4. Notebook gate execution:
   - `bash scripts/testing/run_notebooks_live_repeatable.sh banking/notebooks/18_Corporate_Vendor_Fraud_Demo.ipynb`
   - ✅ PASS (0 error cells, 5s)
   - Report: `exports/live-notebooks-stable-20260328T220229Z/notebook_run_report.tsv`

5. Generator gate execution (`G-GEN`):
   - `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/data_generators/tests -v --no-cov`
   - ✅ PASS (286 passed)

6. Deterministic proof execution (`G-DET`):
   - `bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json`
   - ✅ PASS (`exports/deterministic-status.json` shows `exit_code: 0`)
   - Run artifacts: `exports/demo-20260328T220806Z/`
   - Drift check: ✅ `exports/demo-20260328T220806Z/drift_detection.log` (no drift)

## 📊 FR-041 & FR-042 Governance Update (2026-03-29)

### ✅ FR-041: Alert Quality KPI Governance (Completed)
1. Governance utility delivered:
   - `banking/analytics/governance.py` (precision-proxy computation + deterministic summary export + metric emission helpers)
   - `banking/streaming/metrics.py` adds Prometheus gauge `alert_quality_precision_proxy{scenario,detector}`.
2. Sanctions notebook wiring:
   - `banking/notebooks/01_Sanctions_Screening_Demo.ipynb` now exports deterministic KPI summary and emits the Prometheus precision metric from summary.
3. Validation evidence:
   - `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/analytics/tests/test_governance.py -v --no-cov` ✅ 6 passed
   - `bash scripts/testing/run_notebooks_live_repeatable.sh banking/notebooks/01_Sanctions_Screening_Demo.ipynb` ✅ PASS  
     Report: `exports/live-notebooks-stable-20260329T085022Z/notebook_run_report.tsv`

### ✅ FR-042: Alert Behavior Drift Monitoring (Completed 2026-03-29)
1. Automated drift detection delivered:
   - `scripts/testing/detect_kpi_drift.py` added and integrated into `scripts/testing/run_demo_pipeline_repeatable.sh`.
   - Deterministic verdict artifact emitted per run: `<run_dir>/kpi_drift_verdict.json`.
2. Policy and thresholds:
   - Warning threshold: `0.90`
   - High-severity threshold: `0.80`
   - Operating mode: **Report-only** for P2 (pipeline continues by default; optional `--enforce` for hard-fail mode).
3. Full-run evidence (`demo-20260329T093747Z`):
   - Pipeline summary: `exports/demo-20260329T093747Z/pipeline_summary.txt`
   - Drift step log: `exports/demo-20260329T093747Z/kpi_drift.log`
   - Verdict artifact: `exports/demo-20260329T093747Z/kpi_drift_verdict.json`
   - Observed signal: sanctions precision proxy `0.6667` below critical threshold, surfaced in artifact/log without blocking pipeline.
4. Validation:
   - `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest tests/unit/test_detect_kpi_drift.py -v --no-cov` ✅ 4 passed

## 🆔 FR-023: Entity Resolution Confidence Calibration (Completed 2026-03-29)

1. Logic hardening delivered:
   - `banking/analytics/entity_resolution.py` upgraded to deterministic multi-factor weighted linkage scoring.
   - Standard identity weighting calibrated for high-confidence matches: SSN `0.40`, TaxID `0.40`, Passport `0.30`, DOB `0.10`, Name `0.10`.
2. Investigator cockpit upgrade:
   - `banking/notebooks/14_Entity_Resolution_Demo.ipynb` now renders Merge Rationale cards with explicit "Merge" vs "Review" decision framing.
   - Deterministic evidence export added under `exports/evidence/entity_resolution/` including `ambiguity_class` labels for reviewability.
3. Validation evidence:
   - `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/analytics/tests/test_entity_resolution.py -v --no-cov` ✅ 8 passed
4. Full-pipeline proof evidence (`demo-20260329T104407Z`):
   - Pipeline summary: `exports/demo-20260329T104407Z/pipeline_summary.txt`
   - Drift check: ✅ `exports/demo-20260329T104407Z/drift_detection.log` (no drift vs canonical baseline)
   - KPI drift gate: ✅ `exports/demo-20260329T104407Z/kpi_drift.log` (report-only mode)
   - Notebook report: ✅ `exports/demo-20260329T104407Z/notebook_run_report.tsv` (`14_Entity_Resolution_Demo.ipynb` PASS, 0 error cells)

## 📈 FR-043: KPI Trend Aggregation & Weekly Evidence Rollup (Completed 2026-03-29)

1. Aggregator engine delivered:
   - `scripts/testing/aggregate_kpi_trends.py` scans historical `exports/demo-*/kpi_drift_verdict.json` artifacts and emits deterministic trend rollups.
2. Pipeline integration delivered:
   - `scripts/testing/run_demo_pipeline_repeatable.sh` now includes `KPI Trend Aggregation` as a deterministic gate step and summary step-list entry.
3. Validation delivered:
   - `tests/unit/test_aggregate_kpi_trends.py` added (3 tests).
   - `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest tests/unit/test_aggregate_kpi_trends.py tests/unit/test_detect_kpi_drift.py -v --no-cov` ✅ 7 passed.
4. Full-run evidence (`demo-20260329T112934Z`):
   - Pipeline summary: `exports/demo-20260329T112934Z/pipeline_summary.txt` (includes `kpi-trend-aggregation`).
   - Step log: `exports/demo-20260329T112934Z/kpi_trends.log` (KPI Trend Aggregation PASS).
   - Persistent artifact: `exports/evidence/governance/kpi_trend_report.json` (`runs_evaluated: 4`, `overall_avg_precision_proxy: 0.6667`, `status_counts: {"FAIL": 3, "NO_DATA": 1}`).

## 📦 FR-044: Scheduled KPI Evidence Bundling (Completed 2026-03-29)

1. Bundling engine delivered:
   - `scripts/testing/bundle_governance_evidence.py` generates deterministic governance handoff artifacts from trend/drift outputs.
2. Pipeline integration delivered:
   - `scripts/testing/run_demo_pipeline_repeatable.sh` now includes `KPI Evidence Bundling` and `kpi-evidence-bundling` in the summary step list.
3. Validation delivered:
   - `tests/unit/test_bundle_governance_evidence.py` added (3 tests).
   - `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest tests/unit/test_bundle_governance_evidence.py tests/unit/test_aggregate_kpi_trends.py tests/unit/test_detect_kpi_drift.py -v --no-cov` ✅ 10 passed.
4. Artifact generation verified:
   - `conda run -n janusgraph-analysis PYTHONPATH=. python3 scripts/testing/bundle_governance_evidence.py` ✅ success (`latest_run=demo-20260329T112934Z`, `files=6`).
   - Summary artifact: `exports/evidence/governance/weekly_governance_summary.md`
   - Bundle artifact: `exports/evidence/governance/governance_evidence_bundle.tar.gz`.

## 🛡️ FR-020: Sanctions Multi-factor Weighted Scoring (Completed 2026-03-29)

1. Model contract upgrade delivered:
   - `banking/aml/sanctions_screening.py` now exposes `weighted_score` and `reason_codes` on `SanctionMatch`.
2. Detector logic upgrade delivered:
   - `screen_customer` now emits deterministic weighted reason codes:
     - `SANCTION_NAME_MATCH`
     - `JURISDICTION_MATCH`
     - `ENTITY_TYPE_MATCH`
3. Validation delivered:
   - `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/aml/tests/test_sanctions_screening.py -v --no-cov` ✅ 22 passed.
4. Gate evidence:
   - Notebook gate: `bash scripts/testing/run_notebooks_live_repeatable.sh banking/notebooks/01_Sanctions_Screening_Demo.ipynb` ✅ PASS  
     Report: `exports/live-notebooks-stable-20260329T170901Z/notebook_run_report.tsv`
   - Deterministic proof: `bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json` ✅ PASS  
     Artifacts: `exports/demo-20260329T170932Z/` (`drift_detection.log` PASS).

## 🧭 FR-021: UBO Recursive Effective Ownership/Control Rights (Completed 2026-03-29)

1. Recursive/control-rights logic confirmed:
   - `src/python/analytics/ubo_discovery.py` already implements recursive effective ownership (`_calculate_effective_ownership`) and de-facto control-rights qualification (`_has_control_rights`), with deterministic UBO ordering in `find_ubos_for_company`.
2. Validation delivered:
   - `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest tests/unit/analytics/test_ubo_discovery.py -v --no-cov` ✅ 60 passed.
3. Gate evidence:
   - Notebook gate: `bash scripts/testing/run_notebooks_live_repeatable.sh banking/notebooks/08_UBO_Discovery_Demo.ipynb` ✅ PASS  
     Report: `exports/live-notebooks-stable-20260329T173933Z/notebook_run_report.tsv`
   - Deterministic proof: `bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json` ✅ PASS  
     Artifacts: `exports/demo-20260329T170932Z/` (`drift_detection.log` PASS).

## 📄 FR-045: Case Evidence PDF Exporter (Step 1, In Progress 2026-03-29)

1. Reporting engine delivered:
   - New deterministic PDF generator: `scripts/reporting/generate_case_pdf.py`.
2. Bundle integration delivered:
   - `scripts/testing/bundle_governance_evidence.py` now supports optional `--pdf` and `--pdf-output-dir` to generate and include PDF artifacts in the weekly governance bundle.
3. Validation delivered:
   - `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest tests/unit/test_generate_case_pdf.py tests/unit/test_bundle_governance_evidence.py -v --no-cov` ✅ 6 passed.
4. Artifact generation verified:
   - `conda run -n janusgraph-analysis PYTHONPATH=. python3 scripts/testing/bundle_governance_evidence.py --pdf` ✅ success (`files=8`, `pdfs=2`).
   - PDF artifacts emitted under `exports/evidence/governance/pdf/` and included in `exports/evidence/governance/governance_evidence_bundle.tar.gz`.
