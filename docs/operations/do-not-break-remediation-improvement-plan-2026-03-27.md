# Do-Not-Break Remediation & Improvement Plan (Deterministic-Safe)

**Date:** 2026-03-27  
**Created (UTC):** 2026-03-27T13:24:29Z  
**Created (Local):** 2026-03-27 14:24:29 CET  
**POC:** Platform Engineering + Fraud Domain Engineering + Compliance  
**Status:** Active (Execution Blueprint)  
**TL;DR:** This plan upgrades fraud realism while preserving deterministic behavior, notebook stability, data generation correctness, ingestion/integration safety, and OpenSearch compatibility.

---

## 1) Baseline Scorecard (Current Factual Status)

| Domain | Score (/100) | Grade | Evidence Basis |
|---|---:|---|---|
| Deterministic Runtime & Gate Reliability | 96 | A | Wrapper pass, full gate pass, canonical baseline alignment, drift checks |
| Notebook Runtime Stability | 94 | A- | 19/19 pass, zero error cells |
| Data Generation Reproducibility | 92 | A- | Seeded generation behavior and deterministic patterns |
| Data Integration Contract Stability | 84 | B | Works today, but drift risk during logic upgrades |
| Streaming Ingestion Reliability | 86 | B+ | Functional path present; timing/triage guardrails need maturation |
| OpenSearch Functional Compatibility | 85 | B | Existing flows work; relevance/explainability hardening needed |
| Fraud Realism / Decision Utility | 68 | C+ | Broad scenario coverage, but several demo-grade outputs remain |
| Compliance-Ready Evidence Utility | 74 | B- | Strong documentation, partial case-evidence standardization |

### Overall Program Score
- **Current weighted score:** **85/100**
- **Current grade:** **B+**
- **Interpretation:** excellent platform backbone; partially productionized analytics/control layer.

---

## 2) Do-Not-Break Invariants (Non-Negotiable)

1. Deterministic wrapper + canonical drift behavior must remain PASS.
2. Notebook runtime reliability must remain at current pass-set with no regression.
3. Seeded reproducibility and identity consistency must remain stable.
4. Event, API, and index contracts must remain backward-compatible for current notebooks.
5. OpenSearch mappings and existing query paths must remain functional.
6. No security/runtime weakening to “pass tests faster.”
7. Every change batch must produce evidence + go/no-go decision artifact.

---

## 3) Best-Path Remediation Strategy

## Phase 0 (Week 0-1): Baseline Freeze & Safety Harness
- Lock pre-change evidence pack and add go/no-go gate execution discipline.
- Snapshot baseline artifacts and configs.
- Define scenario-level acceptance criteria before code edits.

**Exit criteria**
- Baseline evidence pack archived
- Go/no-go command sequence documented and rehearsed
- Ticket board activated with dependencies and gate checks

## Phase 1 (Week 1-3): Non-Invasive Decision Output Hardening
- Add standard notebook output contract:
  - Decision Summary
  - Confidence + Rationale
  - Recommended Action
- Introduce default PII masking for notebook outputs.
- Add reason-code style explainability blocks to sanctions/AML/fraud notebooks.

**Exit criteria**
- 100% P0/P1 notebooks use standardized decision block
- No deterministic or notebook runtime regressions
- No API/schema/index breaks

## Phase 2 (Week 3-7): Controlled Domain Logic Upgrades
- Sanctions: weighted multi-factor scoring + association-risk tiering.
- UBO: recursive effective ownership + control-rights logic.
- TBML: market benchmark + route anomaly checks.

**Exit criteria**
- New logic is additive and explainable
- Deterministic wrapper remains PASS
- OpenSearch/search compatibility remains PASS

## Phase 3 (Week 7-12): Missing High-Value Scenario Additions (Additive-First)
- Add APP mule-chain scenario.
- Add Account Takeover scenario.
- Add corporate invoice/vendor fraud scenario.

**Exit criteria**
- 3 new runnable scenarios/notebooks
- All baseline gates PASS
- New scenarios include case-evidence-friendly outputs

## Phase 4 (Week 12+): Decision Safety & Governance
- Introduce alert-quality governance KPIs.
- Add standardized case evidence export for regulator/compliance handoff.
- Introduce drift checks for alert behavior quality (not only runtime determinism).

**Exit criteria**
- Weekly quality dashboard in place
- Case-evidence export available for core AML/fraud notebooks
- No regression to baseline safety domains

---

## 4) Go/No-Go Control Policy

A change batch is **GO** only if all mandatory domains pass:

1. Determinism runtime/gates
2. Notebook runtime integrity
3. Data generation reproducibility
4. Integration/API contracts
5. OpenSearch compatibility

Any mandatory failure => **NO-GO + rollback** using baseline protection plan.

Reference: `docs/operations/baseline-protection-test-plan.md`

---

## 5) Risk-Based Sequencing Rationale

- Start with output explainability and governance (high business value, low runtime risk).
- Delay heavy domain logic changes until contract and validation harnesses are in place.
- Add missing scenarios as additive modules first to avoid destabilizing baseline notebooks.
- Keep deterministic-sensitive surfaces untouched unless absolutely necessary and explicitly controlled.

---

## 6) Success Metrics (Progress Tracking)

| Metric | Baseline | Target After Phase 2 | Target After Phase 4 |
|---|---:|---:|---:|
| Deterministic Pass Rate | 99%+ class | >=99% | >=99% |
| Notebook Runtime Pass Set | 19/19 | 19/19 | 19/19 |
| Fraud Realism Score | 68/100 | >=78/100 | >=85/100 |
| Decision Utility Score | 70/100 class | >=80/100 | >=88/100 |
| Evidence Export Coverage | Partial | 50% core scenarios | 100% core scenarios |
| SLA Breach Frequency (>20m) | Rare/controlled | No repeated breaches | No repeated breaches |

---

## 7) Related Artifacts

- `docs/operations/baseline-assessment-matrix-2026-03-27.md`
- `docs/operations/baseline-protection-test-plan.md`
- `docs/operations/fraud-realism-audit-2026-03-27.md`
- `docs/operations/notebook-business-audit-remediation-plan.md`
