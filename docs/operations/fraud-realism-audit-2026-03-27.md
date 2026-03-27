# Fraud Realism Audit (Retail + Corporate Banking, Graph + Realtime)

**Date:** 2026-03-27  
**POC:** Fraud Analytics Lead + Compliance + Platform Engineering  
**Status:** Active (Independent Critical Review)  
**Scope:** Full codebase, documentation set (including checkpoints), notebook scenarios, and reported outputs.

---

## TL;DR

The platform is **operationally strong** (deterministic execution, repeatability, infrastructure rigor) but **analytically not yet decision-grade** for production fraud/AML actioning without additional controls on explainability, calibration, false-positive governance, and case-evidence packaging.

- **Strength:** repeatable runtime and notebook execution reliability.
- **Gap:** several scenarios remain demo-oriented (illustrative) rather than investigator-grade (defensible decisions).
- **Verdict:** suitable for advanced POC / controlled pilot; not yet sufficient as a standalone production fraud control stack.

---

## 1) Evidence Reviewed

### Core status and checkpoint evidence
- `docs/project-status.md`
- `CHECKPOINT_20260312.md`
- `CHECKPOINT_20260326.md`
- `SUMMARY_20260326.md`
- `RELEASE_NOTE_20260326.md`
- `GRAPH_DENSITY_SUMMARY_20260326.md`

### Notebook and scenario docs
- `banking/notebooks/*.ipynb` (15 demos + exploratory scenarios)
- `docs/banking/guides/notebook-scenarios-business-technical-summary.md`
- `docs/operations/notebook-business-audit-remediation-plan.md`

### Operations/readiness docs
- `docs/operations/time-to-notebook-ready-sla.md`
- `docs/operations/determinism-acceptance-criteria-checklist.md`
- `docs/operations/deterministic-behavior-expected-outputs.md`
- `docs/operations/runbook-improvement-plan-30-60-90.md`
- `docs/index.md`
- `docs/document-catalog.md`

### Relevant implementation surfaces
- `banking/analytics/*`
- `banking/streaming/*`
- `src/python/repository/*`
- `src/python/api/*`
- deterministic/deployment scripts under `scripts/`

---

## 2) Scoring Rubric

- **Realism Score (1-5):** How close scenario logic is to real investigator conditions/data complexity.
- **Correctness Risk:** Low / Medium / High risk of misleading conclusions if used directly for actioning.
- **Decision Utility (1-5):** How directly the output supports a safe operational decision (escalate, hold, file SAR/STR, clear).
- **Evidence Quality:** Strength of explicit rationale, traceability, and reviewability.

---

## 3) Notebook-by-Notebook Fraud Realism Audit

| Notebook | Business Question | Current Method | Realism (1-5) | Correctness Risk | Decision Utility (1-5) | Key Evidence Gap | Priority Fix |
|---|---|---|---:|---|---:|---|---|
| 01 Sanctions Screening | Onboard / reject / escalate? | Vector + graph proximity style matching | 4 | Medium | 4 | Limited multi-factor weighting transparency | Add weighted scoring (name/DOB/country/association) + reason codes |
| 02 AML Structuring | Smurfing likely enough for escalation? | Rule/window thresholds | 3 | Medium | 3 | Hardcoded thresholds; weak segmentation by profile | Dynamic baselines by customer/product/geo |
| 03 Fraud Detection | Freeze / monitor / release? | Graph neighborhood/rule signals | 3 | Medium | 3 | Limited attribution and drift handling | Add top signal attribution + behavior drift scoring |
| 04 Customer 360 | Is EDD/KYC scope sufficient? | Multi-hop entity context | 4 | Medium | 4 | PII handling and consistency risks in outputs | Enforce default PII masking + confidence labels |
| 05 Advanced Analytics OLAP | Where to allocate fraud ops effort? | Aggregate trend views | 2 | Medium | 2 | Mostly descriptive; weak decision thresholds | Add KPI deltas and intervention thresholds |
| 06 TBML Detection | Is trade flow suspicious enough to investigate? | Cycle/path detection | 2 | High | 2 | Missing market-price and route realism | Add price benchmark and route anomaly validation |
| 07 Insider Trading Detection | Is suspicious coordination present? | Trade/communication correlation | 2 | High | 2 | Limited event-context integration | Add external event timeline + temporal confidence |
| 08 UBO Discovery | Who ultimately controls entity? | Ownership traversal | 4 | Medium | 3 | Manual/implicit effective ownership logic | Add recursive effective control/ownership computation |
| 09 Community Detection | Which clusters are probable rings? | Community/graph clustering | 2 | Medium | 2 | Weak explanation of cluster risk semantics | Add cluster rationale map + ring typology labels |
| 10 Integrated Architecture | Is platform release-ready for fraud ops? | End-to-end architecture walkthrough | 3 | Low | 3 | Business gate outputs not always explicit | Add release/no-release decision card with gate criteria |
| 11 Streaming Pipeline | Is realtime fraud triage operational? | Event ingestion and stream flow | 3 | Medium | 3 | Lag thresholds and triage impact unclear | Add lag SLA impact matrix + breach actions |
| 12 API Integration | Are integrations safe for production flow? | API connectivity + examples | 3 | Medium | 3 | Contract validation depth not uniform | Add schema contract assertions and latency profile |
| 13 Time Travel Queries | Can we reconstruct historical state for audit? | Temporal query replay | 4 | Medium | 4 | Diff interpretation can be analyst-heavy | Add human-readable before/after evidence template |
| 14 Entity Resolution | Are entities duplicates or distinct? | Matching + linkage logic | 3 | Medium | 3 | Ambiguity and confidence calibration | Add confidence distribution + merge rationale card |
| 15 Graph Embeddings ML | Are features useful for fraud models? | Embeddings/ML exploration | 2 | Medium | 2 | Feature meaning to business not explicit | Add model utility KPIs and feature explainability |
| Ex-01 Quickstart | Can new analysts become productive quickly? | Guided setup flow | 4 | Low | 4 | Limited scenario handoff | Add next-scenario decision path |
| Ex-02 JanusGraph Guide | Can engineers implement fraud graph queries quickly? | Query cookbook style | 3 | Low | 3 | Recipe-to-use-case mapping sparse | Add business-use-case query packs |
| Ex-03 Advanced Query Patterns | Can investigators perform deep graph forensics? | Advanced traversals | 3 | Medium | 3 | Interpretation burden high | Add interpretation aids and risk pattern templates |
| Ex-04 AML Investigation Playbook | Is evidence package analyst-ready? | Playbook demonstration | 3 | Medium | 3 | Report standardization not complete | Add standardized findings export schema |

---

## 4) Coverage Matrix (Domain Spectrum)

| Domain Area | Status | Assessment |
|---|---|---|
| Retail transaction fraud | Partial | Coverage exists but attribution/calibration needs strengthening |
| Corporate fraud (vendor/invoice/procurement) | Missing/Weak | Not comprehensively represented as first-class scenarios |
| AML structuring/smurfing | Partial | Scenario present, threshold realism limited |
| TBML | Partial | Present but lacks external economic reference context |
| Sanctions screening | Partial-Strong | Good foundation; association and multi-factor scoring needs hardening |
| UBO/KYB transparency | Partial-Strong | Traversal good; control/rights realism needs formalized computation |
| Mule network detection (APP cash-out chains) | Missing | High-value scenario gap |
| Account takeover (ATO) | Missing | No comprehensive device/session behavioral scenario |
| Insider trading/market abuse | Partial | Concept covered; event-context robustness limited |
| Realtime alert triage | Partial-Strong | Pipeline exists; decision-grade triage thresholds underdeveloped |
| Case evidence packaging | Partial | Direction exists; standard regulator-facing output needs completion |
| False-positive governance | Missing/Weak | No consistent precision/review-loop framework across notebooks |

---

## 5) Challenges to Existing Documentation Claims

This section intentionally confronts optimistic viewpoints with evidence-based caution.

1. **“All notebooks pass” vs “decision-ready analytics”**
   - Checkpoints demonstrate execution reliability (`19/19 PASS`) but do not prove precision, recall, or operational safety.
   - Passing execution should not be interpreted as validated control effectiveness.

2. **Operational maturity vs model maturity**
   - Runbooks, deterministic controls, and SLA framing are strong.
   - However, multiple scenarios still require investigator-grade explainability and calibration before production claims are fully defensible.

3. **Business-readiness narratives**
   - Business case docs are useful for sponsorship framing.
   - Production-readiness language should clearly separate **platform readiness** from **fraud-control readiness**.

---

## 6) Missing High-Value Scenarios (Top 10)

1. APP fraud mule-chain lifecycle (placement -> layering -> cash-out).
2. Account takeover (device/IP behavior + session risk + beneficiary novelty).
3. Corporate invoice/vendor fraud (collusion graph + duplicate invoice patterns).
4. Trade misinvoicing with external benchmark prices.
5. Sanctions evasion by association (1-2 hop controlled entities).
6. Beneficial-control abuse with nominee directors / control-rights asymmetry.
7. Cross-border corridor laundering anomalies with jurisdiction risk overlays.
8. Crypto off-ramp laundering path enrichment in mixed rails.
9. Alert disposition feedback loop (closed-case outcomes retraining risk logic).
10. Human-in-the-loop queue optimization (investigator bandwidth vs risk).

---

## 7) 30/60/90 Remediation Roadmap (Decision-Grade Focus)

## 0-30 days (Foundation hardening)
- Standardize notebook output contract:
  - executive decision block
  - confidence/rationale block
  - recommended action block
- Apply PII masking defaults across identity outputs.
- Add minimum false-positive review diagnostics for sanctions, AML, fraud notebooks.

**Acceptance criteria**
- 100% P0/P1 notebooks include decision + rationale + action blocks.
- 100% notebook identity outputs masked by default.
- At least 3 key notebooks report confidence and review diagnostics.

## 31-60 days (Domain realism upgrades)
- UBO: recursive effective ownership + control-rights logic.
- Sanctions: multi-factor weighted scoring and association-risk tiering.
- TBML: price benchmark + route anomaly checks.
- Entity resolution: confidence calibration and ambiguity classes.

**Acceptance criteria**
- UBO notebook produces deterministic >25% effective-control list.
- Sanctions notebook outputs standardized reason codes and weighted score.
- TBML notebook includes explicit economic anomaly indicator.

## 61-90 days (Operational decision safety)
- Add top missing scenarios (APP mule + ATO + corporate invoice fraud).
- Implement case evidence export templates for compliance handoff.
- Add alert quality governance metrics (precision proxy, investigation conversion).

**Acceptance criteria**
- At least 3 missing high-value scenarios implemented as runnable notebooks.
- Case evidence export format available for major AML/fraud notebooks.
- Weekly quality dashboard for alert utility metrics in place.

---

## 8) Production Risk Register (Top 12)

| # | Risk | Impact | Likelihood | Current Control | Residual |
|---:|---|---|---|---|---|
| 1 | Demo-grade outputs treated as production decisions | High | Medium | Checkpoints + docs | High |
| 2 | False-positive burden overwhelms investigators | High | Medium | Partial heuristics | High |
| 3 | Insufficient explainability for regulator challenge | High | Medium | Partial rationale | High |
| 4 | TBML conclusions without economic benchmarks | High | Medium | Graph cycle logic | High |
| 5 | UBO control interpretation ambiguity | High | Medium | Traversal logic | Medium-High |
| 6 | Incomplete sanctions association logic | High | Medium | Name/vector matching | Medium-High |
| 7 | Missing ATO/mule scenarios causes blind spots | High | Medium | None comprehensive | High |
| 8 | Case-evidence format inconsistency | Medium-High | Medium | Partial playbooks | Medium-High |
| 9 | Model confidence not calibrated for decisions | High | Medium | Limited scoring | High |
| 10 | Over-reliance on synthetic behavior patterns | Medium-High | High | Deterministic seed | Medium-High |
| 11 | Realtime triage actions unclear during lag/stress | Medium-High | Medium | SLA docs | Medium |
| 12 | Narrative optimism exceeds analytical maturity | Medium-High | Medium | Multiple docs | Medium-High |

---

## 9) Final Verdict

The repository demonstrates **excellent engineering discipline** and a strong graph/realtime foundation.  
For fraud and AML operations, it should currently be treated as:

- **Production-capable platform backbone**
- **Partially productionized analytics layer**

To cross into full decision-grade readiness, the priority is not more infrastructure—but stronger domain realism, explainability, calibration, and standardized case evidence outputs across high-risk scenarios.
