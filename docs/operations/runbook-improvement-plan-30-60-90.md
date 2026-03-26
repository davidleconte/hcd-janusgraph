# Runbook Improvement Plan (30-60-90 Days)

**Date:** 2026-03-26  
**Created (UTC):** 2026-03-26T19:32:58Z  
**Created (Local):** 2026-03-26 20:32:58 CET  
**POC:** Platform Engineering + Domain Engineering + Security/Compliance  
**Status:** Active (Execution Plan)  
**TL;DR:** In 90 days, evolve runbooks from infrastructure-strong to business-outcome-strong by adding functional gates, SLA-driven incident handling, automated compliance evidence packaging, and explicit ownership/KPI governance.

---

## 1) Business Objective

Improve operational runbooks to reduce:
- Incident cost (faster recovery and clearer escalation)
- Release risk (technical PASS must also mean business PASS)
- Compliance burden (evidence bundles generated automatically)
- Onboarding time (first successful notebook journey under 2 hours)

---

## 2) Scope and Success Criteria

### In Scope
- Operations runbooks under `docs/operations/`
- Deterministic workflow guidance and gate interpretation
- Incident/escalation runbooks tied to SLA outcomes
- Compliance evidence generation and packaging process
- Ownership model and KPI/SLI instrumentation

### Out of Scope (for this 90-day window)
- Major platform re-architecture
- Full business-model redesign of notebooks
- New infrastructure stack replacement

### 90-Day Success Criteria
1. Infra + business functional gates both enforced for release readiness.
2. Time-to-notebook-ready SLA tracked weekly (p50/p95) with incident triggers.
3. Compliance evidence bundle generation reduced to one command.
4. New contributor onboarding path documented and validated under 2 hours.

---

## 3) Priority Themes (Impact vs Effort)

1. **Functional confidence gates (high impact)**  
   Add business validation gates beyond infra determinism.
2. **SLA-operated runbooks (high impact)**  
   Convert timing thresholds into action branches with escalation.
3. **Evidence automation (high impact)**  
   Produce regulator-ready artifact bundles per run.
4. **Ownership + accountability (medium/high impact)**  
   Assign team ownership per gate/runbook/KPI.
5. **Onboarding simplification (medium impact)**  
   Reduce operational friction for non-platform stakeholders.

---

## 4) 30-60-90 Day Plan

## Day 0-30 (Quick Wins / Stabilization)

### Deliverables
1. **Runbook metadata standardization**
   - Add required headers to top runbooks:
     - business service impacted
     - severity model
     - owner / backup owner
     - RTO/RPO/SLA links
2. **SLA branch activation**
   - Align runbooks to:
     - PASS: `<= 17m`
     - WARNING: `17m–20m`
     - BREACH: `>20m`
   - Include “first 3 diagnostics” command list for each branch.
3. **Known reliability fixes in runbook flow**
   - Document and remediate deterministic wrapper exit-code anomaly.
   - Add explicit notebook connectivity/security alignment checks.
4. **Escalation matrix**
   - Add P0/P1/P2 escalation contacts and handoff criteria.
5. **Morning operational checklist integration**
   - Include time-to-notebook-ready SLA check and drift signal review.

### KPIs for Day 30
- 100% of critical runbooks include owner + escalation + business impact metadata.
- 100% of daily checks include SLA status.
- Wrapper reliability issue tracked and either fixed or formally mitigated with workaround.

---

## Day 31-60 (Business-Functional Reliability)

### Deliverables
1. **Functional gates (G10+) added to release criteria**
   - G10: AML scenario sanity checks
   - G11: Fraud-ring scenario integrity checks
   - G12: UBO path/output consistency checks
2. **Runbook decision trees**
   - Add fault trees for:
     - Infra pass / business fail
     - Business pass / timing breach
     - drift fail / no code change
3. **Compliance evidence bundling v1**
   - One-command generation of:
     - deterministic status
     - notebook report
     - graph metrics snapshot
     - audit evidence pointers
     - manifest/checksum file
4. **Post-incident template**
   - Standardized PIR format with root cause, blast radius, and action tracking.

### KPIs for Day 60
- At least 3 functional business gates operational and documented.
- 80% of incidents have completed PIR artifacts within SLA.
- Evidence bundle generation time < 30 minutes from run completion.

---

## Day 61-90 (Scale, Governance, and Audit Readiness)

### Deliverables
1. **KPI dashboard operationalization**
   - Weekly trend reporting for reliability and business gates.
2. **Ownership and governance model formalization**
   - Gate ownership matrix approved and published.
3. **Onboarding runbook (“first success in <2h”)**
   - Role-based path for analysts/data scientists/platform engineers.
4. **Quarterly runbook review cadence**
   - Scheduled review + drift checks between docs and runtime scripts.
5. **Compliance evidence bundle v2**
   - Auditor-facing index, traceability mapping, and retention guidance.

### KPIs for Day 90
- Deterministic + functional pass rate target met for releases.
- p95 notebook-ready time within SLA or with documented exception process.
- New-hire/role onboarding first-success path validated in under 2 hours.
- Audit evidence retrieval process fully documented and rehearsal-complete.

---

## 5) KPI / SLI Set (Recommended)

| Metric | Type | Target | Owner |
|---|---|---|---|
| Deterministic pass rate | SLI | >= 99% | Platform Engineering |
| Time-to-notebook-ready | SLA | <= 17m target; breach >20m | DevOps/SRE |
| Functional gate pass rate (G10+) | SLI | >= 95% | Domain Engineering |
| Compliance evidence lead time | KPI | <= 30 min | Security/Compliance |
| Incident MTTR (deterministic pipeline) | KPI | -30% from current baseline | Platform Engineering |
| Onboarding first-success time | KPI | < 2 hours | Platform + DevRel |

---

## 6) Ownership Model

- **Platform Engineering:** G0-G6, deploy/runtime reliability, deterministic infra controls
- **Domain Engineering (Banking):** G7-G8 + G10-G12 functional quality signals
- **Security/Compliance:** evidence controls, audit traceability, policy mapping
- **SRE/DevOps:** SLA monitoring, alert routing, incident command discipline
- **QA:** regression verification across infra + business gates

---

## 7) Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Infra pass but business logic regresses | High | Enforce G10+ functional gates pre-release |
| SLA drift hidden by warm-cache behavior | Medium | Track cold/warm runs separately in reports |
| Compliance evidence remains manual | High | Automate evidence bundle command and manifesting |
| Ownership ambiguity during incidents | High | Publish and enforce escalation/ownership matrix |
| Runbook/doc drift from scripts | Medium | Monthly docs-authority checks + review cadence |

---

## 8) Execution Governance

- **Cadence:** weekly progress review, monthly governance checkpoint
- **Reporting:** one-page executive status + technical appendix
- **Acceptance gate:** no release sign-off without infra + business + compliance evidence readiness

---

## 9) Immediate Next Actions (This Week)

1. Add metadata headers and escalation matrix to top 5 operational runbooks.
2. Wire SLA branch logic into daily/morning checklist.
3. Define exact pass/fail assertions for G10/G11/G12.
4. Draft `generate_compliance_evidence_bundle.sh` contract and artifact schema.
5. Schedule first 30-day review meeting with all owners.