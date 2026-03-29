# Fraud Realism Ticketized Execution Board (Sprint-by-Sprint)

**Date:** 2026-03-27  
**Created (UTC):** 2026-03-27T13:24:29Z  
**Created (Local):** 2026-03-27 14:24:29 CET  
**POC:** Platform Engineering + Fraud Domain Engineering + Compliance  
**Status:** Active (Execution Board)  
**TL;DR:** Ticketized P0/P1/P2 plan to improve fraud realism while preserving deterministic behavior and current working integrations.

---

## 1) Baseline Score & Grade (Starting Point)

| Area | Baseline Score | Grade |
|---|---:|---|
| Deterministic Runtime & Gates | 96 | A |
| Notebook Runtime Stability | 94 | A- |
| Data Generation Reproducibility | 92 | A- |
| Data Integration Contract Stability | 84 | B |
| Streaming Ingestion Reliability | 86 | B+ |
| OpenSearch Compatibility | 85 | B |
| Fraud Realism / Decision Utility | 68 | C+ |
| Compliance-Ready Evidence Utility | 74 | B- |

**Overall Program Baseline:** **85/100 (B+)**

---

## 2) Gate Check Catalog (Reusable Per Ticket)

Use these exact checks based on scope touched by a ticket.

- **G-DET:** `bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json`
- **G-NBK:** `bash scripts/testing/run_demo_pipeline_repeatable.sh`
- **G-GEN:** `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/data_generators/tests -v --no-cov`
- **G-STR:** `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/streaming/tests -v --no-cov`
- **G-API:** `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest tests/unit -v --no-cov`
- **G-OS:** `conda run -n janusgraph-analysis PYTHONPATH=. OPENSEARCH_USE_SSL=false python -m pytest tests/integration -k opensearch -v --no-cov --timeout=120`

> Ticket completion requires all listed gate checks in the ticket row to pass.

---

## 3) Sprint Plan & Ticket Board

## Sprint 0 (Stabilization Harness) — Week 0-1

| Ticket ID | Priority | Title | Owner | Estimate | Dependencies | Scope | Exact Gate Checks | Done Criteria |
|---|---|---|---|---|---|---|---|---|
| FR-000 | P0 | Baseline evidence pack freeze | Platform | S | None | Archive baseline artifacts/config snapshots | G-DET, G-NBK | Baseline bundle archived and reproducible |
| FR-001 | P0 | Activate strict go/no-go workflow | Platform + QA | S | FR-000 | Enforce stop-on-fail validation sequence | G-DET, G-NBK, G-GEN | Documented + rehearsed workflow adopted |
| FR-002 | P0 | Contract freeze for IDs/events/index fields | Platform + Domain | M | FR-000 | Define immutable contract matrix | G-API, G-STR, G-OS | Contract matrix published and validated |

## Sprint 1 (Non-invasive Decision Output Hardening) — Weeks 1-3

| Ticket ID | Priority | Title | Owner | Estimate | Dependencies | Scope | Exact Gate Checks | Done Criteria |
|---|---|---|---|---|---|---|---|---|
| FR-010 | P0 | Standard notebook decision block template | Domain + Product | M | FR-001 | Decision + confidence + action block for P0/P1 notebooks | G-NBK | Template present and rendered in all target notebooks |
| FR-011 | P0 | PII masking utility and adoption | Platform + Compliance | M | FR-002 | Default masking in notebook outputs | G-NBK, G-API | No raw sensitive identifiers in notebook outputs |
| FR-012 | P0 | Reason-code explainability for sanctions/AML/fraud notebooks | Domain | M | FR-010 | Rationale fields and reason code sections | G-NBK | Outputs include reason codes and rationale text |

## Sprint 2 (Controlled Logic Upgrades) — Weeks 3-7

| Ticket ID | Priority | Title | Owner | Estimate | Dependencies | Scope | Exact Gate Checks | Done Criteria |
|---|---|---|---|---|---|---|---|---|
| FR-020 | P1 | Sanctions multi-factor weighted scoring ✅ DONE (2026-03-29) | Domain + Compliance | L | FR-012 | Name+DOB+country+association weighted model | G-NBK, G-OS, G-DET | Delivered weighted-scoring explainability in `banking/aml/sanctions_screening.py` (`weighted_score` + deterministic `reason_codes`: `SANCTION_NAME_MATCH`, `JURISDICTION_MATCH`, `ENTITY_TYPE_MATCH`) with contract tests in `banking/aml/tests/test_sanctions_screening.py`; evidence: `pytest banking/aml/tests/test_sanctions_screening.py -v --no-cov` (22 passed), notebook gate `exports/live-notebooks-stable-20260329T170901Z/notebook_run_report.tsv` (01_Sanctions_Screening_Demo.ipynb PASS), and deterministic proof run `exports/demo-20260329T170932Z/` (`drift_detection.log` PASS). |
| FR-021 | P1 | UBO recursive effective ownership/control rights ✅ DONE (2026-03-29) | Domain | L | FR-002 | Deterministic recursive effective-control logic | G-NBK, G-DET | Recursive effective ownership + control-rights qualification already implemented in `src/python/analytics/ubo_discovery.py` (`_calculate_effective_ownership`, `_has_control_rights`, deterministic UBO sorting); evidence: `pytest tests/unit/analytics/test_ubo_discovery.py -v --no-cov` (60 passed, includes control-rights + circular-risk + deterministic-ordering assertions), notebook gate `exports/live-notebooks-stable-20260329T173933Z/notebook_run_report.tsv` (08_UBO_Discovery_Demo.ipynb PASS), and deterministic proof artifacts `exports/demo-20260329T170932Z/` (`drift_detection.log` PASS). |
| FR-022 | P1 | TBML economic realism (price benchmark + route anomaly) ✅ DONE (2026-03-28) | Domain | L | FR-002 | Add economic anomaly checks to TBML flow | G-NBK, G-DET | Explicit economic anomaly flags added (`REASON_CODE: MARKET_PRICE_DEVIATION`, route-risk indicators); evidence: `pytest banking/analytics/tests/test_detect_tbml.py -v --no-cov` (60 passed) and `exports/demo-20260328T120423Z/drift_detection.log` (No drift) |
| FR-023 | P1 | Entity resolution confidence calibration ✅ DONE (2026-03-29) | Domain | M | FR-002 | Weighted linkage scoring and ambiguity classes | G-NBK, G-DET | ER engine uses multi-factor weighting (TaxID=0.40, SSN=0.40); Notebook 14 renders Merge Rationale cards + deterministic evidence export (`exports/evidence/entity_resolution/` with `ambiguity_class` labels); evidence: `pytest banking/analytics/tests/test_entity_resolution.py -v --no-cov` (8 passed), `exports/demo-20260329T104407Z/drift_detection.log` (No drift), `exports/demo-20260329T104407Z/notebook_run_report.tsv` (14_Entity_Resolution_Demo.ipynb PASS) |

## Sprint 3 (Missing Scenario Additions, Additive-First) — Weeks 7-12

| Ticket ID | Priority | Title | Owner | Estimate | Dependencies | Scope | Exact Gate Checks | Done Criteria |
|---|---|---|---|---|---|---|---|---|
| FR-030 | P1 | APP mule-chain scenario notebook/module ✅ DONE (2026-03-28) | Domain | L | FR-001 | Additive new scenario (no baseline mutation) | G-NBK, G-GEN, G-DET | Runnable scenario with case-evidence output block; evidence: `pytest banking/analytics/tests/test_detect_mule_chains.py -q --no-cov` (11 passed), notebook #16 upgraded to live graph-backed retrieval + deterministic fallback, standardized export path `exports/evidence/mule_chains/` |
| FR-031 | P1 | Account takeover (ATO) scenario ✅ DONE (2026-03-28) | Domain + Platform | L | FR-030 | Device/session/beneficiary novelty risk pattern | G-NBK, G-STR, G-DET | FR-031 slice delivered: `banking/analytics/detect_ato.py`, `banking/analytics/tests/test_detect_ato.py`, `banking/notebooks/17_Account_Takeover_ATO_Demo.ipynb`, and analytics exports in `banking/analytics/__init__.py`; evidence: detector gate (`pytest banking/analytics/tests/test_detect_ato.py -v --no-cov`) 7 passed, combined analytics gate (18 passed), notebook gate PASS with report `exports/live-notebooks-stable-20260328T212744Z/notebook_run_report.tsv`, `G-STR` (`pytest banking/streaming/tests -v --no-cov`) PASS (270 passed), and `G-DET` PASS via `scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json` (`exit_code: 0`, artifacts `exports/demo-20260328T213636Z/`) |
| FR-032 | P1 | Corporate invoice/vendor fraud scenario ✅ DONE (2026-03-28) | Domain | L | FR-030 | Collusion + duplicate invoice graph patterns | G-NBK, G-GEN, G-DET | FR-032 slice delivered: `banking/analytics/detect_procurement.py`, `banking/analytics/tests/test_detect_procurement.py`, `banking/notebooks/18_Corporate_Vendor_Fraud_Demo.ipynb`, and analytics exports wired in `banking/analytics/__init__.py`; evidence: procurement detector gate (`pytest banking/analytics/tests/test_detect_procurement.py -v --no-cov`) 7 passed, combined analytics gate (25 passed), notebook gate PASS with report `exports/live-notebooks-stable-20260328T220229Z/notebook_run_report.tsv`, generator gate (`pytest banking/data_generators/tests -v --no-cov`) 286 passed, deterministic proof `scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json` PASS (`exit_code: 0`, artifacts `exports/demo-20260328T220806Z/`) |

## Sprint 4 (Governance, Evidence, Drift Controls) — Weeks 12+

| Ticket ID | Priority | Title | Owner | Estimate | Dependencies | Scope | Exact Gate Checks | Done Criteria |
|---|---|---|---|---|---|---|---|---|
| FR-040 | P2 | Case evidence export standardization ✅ DONE (2026-03-28) | Compliance + Platform | M | FR-020, FR-021, FR-022 | Regulator-ready findings schema and export block | G-NBK, G-API | Standardized evidence export now implemented across core and new fraud scenarios: notebooks 01/02/03/16/17/18 export deterministic case artifacts to `exports/evidence/{sanctions|aml_structuring|fraud_detection|mule_chains|ato|procurement}/` with required schema fields (`alert_id`, `timestamp`, `detector`, `decision`, `confidence`, `risk_score`, `victim_id`, `reason_codes`, `evidence_summary`) plus masked summary CSVs; evidence: targeted live gate `bash scripts/testing/run_notebooks_live_repeatable.sh banking/notebooks/02_AML_Structuring_Detection_Demo.ipynb banking/notebooks/03_Fraud_Detection_Demo.ipynb` PASS with report `exports/live-notebooks-stable-20260328T224721Z/notebook_run_report.tsv` (both PASS, 0 error cells) and prior sanctions validation in `exports/live-notebooks-stable-20260328T223930Z/notebook_run_report.tsv` |
| FR-041 | P2 | Alert quality KPI governance dashboard ✅ DONE (2026-03-29) | Product + Domain | M | FR-040 | Precision proxy metrics and governance dashboard scaffold | G-NBK, G-API | FR-041 delivered with deterministic KPI utilities (`banking/analytics/governance.py`), Prometheus gauge wiring (`alert_quality_precision_proxy{scenario,detector}`), sanctions notebook export+emit path, and dashboard scaffold `config/grafana/dashboards/alert-quality-governance.json`; evidence: `pytest banking/analytics/tests/test_governance.py -v --no-cov` (6 passed), `bash scripts/testing/run_notebooks_live_repeatable.sh banking/notebooks/01_Sanctions_Screening_Demo.ipynb` PASS (`exports/live-notebooks-stable-20260329T085022Z/notebook_run_report.tsv`) |
| FR-042 | P2 | Alert behavior drift monitoring ✅ DONE (2026-03-29) | Platform + Domain | M | FR-041 | Automated KPI drift detection and verdict generation | G-DET, G-NBK | `scripts/testing/detect_kpi_drift.py` integrated into repeatable pipeline with deterministic verdict artifact `kpi_drift_verdict.json`; policy set to report-only for P2 (`--enforce` optional). Evidence: full gate run `exports/demo-20260329T093747Z/`, step log `exports/demo-20260329T093747Z/kpi_drift.log`, verdict `exports/demo-20260329T093747Z/kpi_drift_verdict.json` (Sanctions precision 0.6667 below critical threshold, surfaced without blocking pipeline). |
| FR-043 | P2 | KPI trend aggregation and weekly evidence rollup ✅ DONE (2026-03-29) | Platform + Domain | M | FR-042 | Cross-run KPI trend artifact + governance evidence rollup | G-API, G-NBK | FR-043 delivered with automated time-series aggregation script (`scripts/testing/aggregate_kpi_trends.py`) and persistent trend report `exports/evidence/governance/kpi_trend_report.json`; evidence: pipeline run `demo-20260329T112934Z` confirms successful historical rollup across 4 runs; unit tests `tests/unit/test_aggregate_kpi_trends.py` (3 passed). |
| FR-044 | P2 | Scheduled/packaged weekly KPI evidence bundle ✅ DONE (2026-03-29) | Platform + Domain | M | FR-043 | Deterministic rollup summary (MD) and evidence tarball | G-NBK, G-DET | Delivered `scripts/testing/bundle_governance_evidence.py` and integrated `KPI Evidence Bundling` into repeatable pipeline; evidence: run `demo-20260329T112934Z` produced `exports/evidence/governance/weekly_governance_summary.md` and `exports/evidence/governance/governance_evidence_bundle.tar.gz`; validation: `pytest tests/unit/test_bundle_governance_evidence.py tests/unit/test_aggregate_kpi_trends.py tests/unit/test_detect_kpi_drift.py -v --no-cov` (10 passed). |
| FR-045 | P2 | Case evidence PDF exporter ✅ DONE (2026-03-29) | Platform + Compliance | M | FR-044 | Deterministic PDF rendering + optional bundle inclusion | G-API, G-NBK | FR-045 delivered with deterministic PDF generator `scripts/reporting/generate_case_pdf.py` and optional `--pdf` integration in `scripts/testing/bundle_governance_evidence.py`; evidence: `pytest tests/unit/test_generate_case_pdf.py tests/unit/test_bundle_governance_evidence.py -v --no-cov` (6 passed), full repeatable pipeline run `exports/demo-20260329T175235Z/` (PASS), and PDF-enabled bundle refresh `python3 scripts/testing/bundle_governance_evidence.py --pdf` (`latest_run=demo-20260329T175235Z`, `files=8`, `pdfs=2`). |

---

## 4) Priority Definitions

- **P0:** Mandatory safety/value preconditions; must complete first.
- **P1:** High-value realism improvements with controlled risk.
- **P2:** Governance and scaling maturity improvements.

---

## 5) Progress Scoring Model (Factual Measurement)

Update these after each sprint:

1. **Safety Score (40%)**  
   - Determinism pass, notebook pass, contract stability.

2. **Realism Score (35%)**  
   - Scenario quality uplift, explainability, decision usefulness.

3. **Evidence Score (15%)**  
   - Case export readiness and traceability quality.

4. **Operational Score (10%)**  
   - SLA adherence and regression-free delivery cadence.

### Grade bands
- **A:** 92-100
- **A-:** 88-91
- **B+:** 84-87
- **B:** 80-83
- **C+:** 72-79
- **C:** 65-71
- **D/F:** <65

---

## 6) Current vs Target

| Metric | Current | Target after Sprint 2 | Target after Sprint 4 |
|---|---:|---:|---:|
| Overall Program Score | 85 (B+) | >=89 (A-) | >=92 (A) |
| Fraud Realism Score | 68 (C+) | >=78 (B) | >=85 (B+/A-) |
| Evidence Utility Score | 74 (B-) | >=82 (B) | >=90 (A-) |
| Deterministic Reliability | 96 (A) | >=96 (A) | >=96 (A) |
| Notebook Runtime Stability | 94 (A-) | >=94 (A-) | >=94 (A-) |

---

## 7) Related Documents

- `docs/operations/do-not-break-remediation-improvement-plan-2026-03-27.md`
- `docs/operations/baseline-assessment-matrix-2026-03-27.md`
- `docs/operations/baseline-protection-test-plan.md`
- `docs/operations/fraud-realism-audit-2026-03-27.md`
