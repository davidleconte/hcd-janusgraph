# Baseline Assessment Matrix (Pre-Implementation Safety Baseline)

**Date:** 2026-03-27  
**Created (UTC):** 2026-03-27T13:17:53Z  
**Created (Local):** 2026-03-27 14:17:53 CET  
**POC:** Platform Engineering + Domain Engineering + Compliance  
**Status:** Active (Control Baseline)  
**TL;DR:** This matrix defines what is currently working and what must remain stable before implementing fraud-realism improvements.

---

## 1) Decision-Ready Baseline Matrix

| Domain / Variable | Current Status | Confirmed Working (Evidence) | Accuracy / Correctness Confidence | Determinism Confidence | Efficiency / Performance | Key Constraints (Must Not Break) | Validation Guards | Improvement Readiness | Required Guardrails Before Changes |
|---|---|---|---|---|---|---|---|---|---|
| Deterministic wrapper + gate pipeline | Working | `CHECKPOINT_20260326.md` shows full gate pass and wrapper exit `0` | High (orchestration correctness) | High | Notebook-ready observed ~16 min class run | Gate order, reset behavior, canonical baseline alignment | `scripts/deployment/deterministic_setup_and_proof_wrapper.sh` + status artifact + drift checks | Safe now | Mandatory deterministic rerun after every change batch |
| Notebook runtime execution | Working | `19/19 PASS`, `cells_with_error=0` in checkpoint and notebook report references | High (execution correctness) | High | Acceptable under current SLA | No notebook runtime regression | Repeatable notebook pipeline + notebook integrity checks | Safe now | Keep notebook pass-rate as release gate |
| Notebook analytical decision quality | Partial | Scenario breadth exists across sanctions/AML/fraud/TBML/UBO/time-travel | Medium (several scenarios demo-oriented) | Medium-High | N/A (quality-focused) | Existing outputs must remain runnable while hardening logic | Scenario docs + fraud realism audit review | Needs pre-work | Add decision/rationale/action output contract before logic refactors |
| Data generation determinism | Working | Seeded generation, reference timestamp model, stable orchestration patterns | High (for reproducibility) | High | Good for demo volume | Seed behavior, ID stability, referential integrity | Generator tests + seed validation + deterministic pipeline | Safe now | Golden baseline snapshots for generator outputs before edits |
| Data generation realism/scope | Partial | Broad synthetic coverage and pattern injection available | Medium (illustrative vs adversarial realism) | High | Adequate for current demos | Do not alter baseline dataset semantics unintentionally | Data loader + smoke tests | Needs pre-work | Add new patterns additively before modifying existing ones |
| Streaming ingestion (Pulsar -> graph/search) | Working | Streaming flow operational in existing module/tested integration paths | Medium-High | Medium (timing sensitivity) | Good, with lag-governance still maturing | Schema compatibility, idempotent consumer behavior | Integration tests + runtime checks | Safe with caution | Add contract tests + replay/idempotency assertions |
| Cross-system data integration consistency | Partial / At risk | Current IDs/topics integrate across demo paths | Medium (mapping drift risk during upgrades) | High (seeded IDs) | N/A | Preserve IDs, topic names, payload fields, notebooks assumptions | Existing integration tests + notebook runs | Needs pre-work | Explicit cross-system contract matrix prior to logic changes |
| OpenSearch behavior (incl. vector) | Working | Current sanctions/search flows operational in notebook ecosystem | Medium (needs richer explainability and multi-factor signals) | High (deterministic input path) | Moderate; query tuning headroom | Preserve index mappings/fields and query compatibility | Integration tests + notebook checks | Safe with caution | Lock mappings + run relevance regression set before changes |
| API/repository contract stability | Working | Current API/repository integration supports demos | Medium-High | High | Acceptable | No breaking response contract for notebooks | Unit + integration tests | Safe now | Add response contract tests before modifying schemas |
| Documentation/checkpoint evidence chain | Working | Indexed docs + checkpoint trail + latest audit documents present | High (traceability quality) | High | N/A | Claims must remain evidence-backed | Checkpoint updates + project status discipline | Safe now | Require evidence update in same change set as behavior changes |

---

## 2) Non-Negotiable Invariants

1. Deterministic baseline contract remains intact (canonical drift behavior unchanged).
2. Pipeline gates and ordering remain semantically unchanged unless explicitly governed.
3. Notebook runtime reliability remains at `19/19 PASS` with no error-cell regressions.
4. Seeded reproducibility stays stable (seed, ID behavior, reference timestamp assumptions).
5. Cross-system identity consistency remains intact (generator -> stream -> graph -> search -> notebooks/API).
6. OpenSearch mapping and query compatibility remain stable.
7. Security/runtime constraints are not weakened to pass tests.
8. Every major change includes updated evidence and checkpoint traceability.

---

## 3) Risk-Ranked Pre-Implementation Checklist

## Critical
1. Capture immutable pre-change evidence bundle (status, notebook report, seed logs, key metrics).
2. Enforce go/no-go gate sequence (deterministic wrapper + notebooks + targeted integration checks).
3. Freeze event/index/notebook contract assumptions before edits.

## High
4. Define decision-grade acceptance criteria per notebook prior to domain logic changes.
5. Add OpenSearch relevance regression checks on a fixed query set.
6. Add cross-system ID lineage assertions.

## Medium
7. Standardize notebook explainability block (confidence/rationale/action).
8. Add false-positive governance placeholders per scenario family.
9. Track timing budgets by phase to catch performance regressions.

---

## 4) Sequenced Improvement Plan (Low Regression Risk)

1. **Phase 0 — Baseline freeze:** capture evidence + activate strict go/no-go checks.
2. **Phase 1 — Non-invasive notebook contract hardening:** decision/rationale/action outputs, PII-safe formatting.
3. **Phase 2 — Controlled logic upgrades:** sanctions + UBO + TBML improvements with incremental validation.
4. **Phase 3 — Add missing scenarios (additive):** APP mule, ATO, corporate invoice fraud as new modules/notebooks.
5. **Phase 4 — Decision safety hardening:** alert quality KPIs, case evidence export, drift governance.

---

## 5) Linkage

- Detailed domain realism findings: `docs/operations/fraud-realism-audit-2026-03-27.md`
- Notebook remediation tracker: `docs/operations/notebook-business-audit-remediation-plan.md`
- Deterministic acceptance baseline: `docs/operations/determinism-acceptance-criteria-checklist.md`
- Runtime timing SLA: `docs/operations/time-to-notebook-ready-sla.md`
