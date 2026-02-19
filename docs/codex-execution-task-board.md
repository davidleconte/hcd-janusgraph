# Codex Execution Task Board

- Date: 2026-02-18
- Source: Consolidated from comprehensive audit and P0-P2 plan
- Tracking model: one ticket = one acceptance-verifiable outcome

## P0 Tickets (Weeks 1-2)

### CODEX-P0-001: Per-package coverage gates
- Owner: QA/SDET + Backend
- Estimate: 2 days
- Dependencies: none
- Deliverable: CI thresholds for critical packages (`streaming`, `compliance`, `aml`, `fraud`)
- Acceptance:
  - CI fails when package coverage drops below thresholds.

### CODEX-P0-002: No new untyped public functions
- Owner: Backend
- Estimate: 2 days
- Dependencies: none
- Deliverable: Type gate policy integrated into CI.
- Acceptance:
  - PR introducing new untyped public function fails quality gate.

### CODEX-P0-003: Workflow major-version upgrades
- Owner: DevOps
- Estimate: 1 day
- Dependencies: none
- Deliverable: Update lagging workflow actions.
- Acceptance:
  - No major-version lag in `.github/workflows/`.

### CODEX-P0-004: Docs authority normalization
- Owner: Tech Writer + Backend
- Estimate: 2 days
- Dependencies: none
- Deliverable: Remove stale metrics outside `docs/project-status.md`.
- Acceptance:
  - Root and module docs reference status authority without conflicting numbers.

### CODEX-P0-005: Debt registry from TODO/FIXME/HACK
- Owner: Engineering Manager + Backend
- Estimate: 1 day
- Dependencies: none
- Deliverable: Prioritized debt register with owner and due date.
- Acceptance:
  - 100% of open markers mapped to tracked items or removed.

## P1 Tickets (Weeks 3-6)

### CODEX-P1-001: Refactor `graph_consumer` complexity hotspot
- Owner: Backend
- Estimate: 4 days
- Dependencies: CODEX-P0-002
- Deliverable: Split processing into typed handlers/services.
- Acceptance:
  - Complexity and function length reduced to target profile.

### CODEX-P1-002: Refactor `vector_consumer` batch path
- Owner: Backend
- Estimate: 3 days
- Dependencies: CODEX-P1-001
- Deliverable: Smaller testable units with explicit interfaces.
- Acceptance:
  - Reduced branching and higher unit test coverage on failure paths.

### CODEX-P1-003: Refactor insider-trading report pipeline
- Owner: Backend
- Estimate: 4 days
- Dependencies: CODEX-P0-002
- Deliverable: Decompose report generation into composable typed stages.
- Acceptance:
  - Complexity hotspot removed, deterministic output unchanged.

### CODEX-P1-004: Refactor fraud notebook compatibility path
- Owner: Backend
- Estimate: 3 days
- Dependencies: CODEX-P1-003
- Deliverable: Isolate compatibility adapters from core runtime logic.
- Acceptance:
  - Compatibility preserved and production path simplified.

### CODEX-P1-005: Refactor orchestrator export path
- Owner: Backend
- Estimate: 3 days
- Dependencies: CODEX-P0-002
- Deliverable: Split export logic by format/strategy.
- Acceptance:
  - Function length and complexity tail reduced.

### CODEX-P1-006: Logging and exception standardization
- Owner: Backend + SRE
- Estimate: 3 days
- Dependencies: CODEX-P1-001..005
- Deliverable: Structured logging and consistent exception taxonomy in refactored modules.
- Acceptance:
  - No ad-hoc prints in critical runtime modules; log fields are queryable.

### CODEX-P1-007: API contract regression suite
- Owner: QA/SDET + Backend
- Estimate: 4 days
- Dependencies: CODEX-P0-001
- Deliverable: Backward-compat tests for key API contracts.
- Acceptance:
  - Breaking API changes are gate-blocking.

## P2 Tickets (Weeks 7-12)

### CODEX-P2-001: Performance SLO baseline and CI gate
- Owner: SRE + QA/SDET
- Estimate: 5 days
- Dependencies: CODEX-P1-001..007
- Deliverable: Latency/throughput/error budgets with regression thresholds in CI.
- Acceptance:
  - CI fails on statistically significant perf regressions.

### CODEX-P2-002: API versioning and deprecation policy
- Owner: Backend Lead + Architect
- Estimate: 3 days
- Dependencies: CODEX-P1-007
- Deliverable: Published lifecycle policy with compatibility matrix.
- Acceptance:
  - Release checklist requires policy compliance.

### CODEX-P2-003: Security negative-path test expansion
- Owner: Security Engineer + QA/SDET
- Estimate: 4 days
- Dependencies: CODEX-P0-001, CODEX-P0-002
- Deliverable: Expanded abuse-case tests (auth/session/input validation).
- Acceptance:
  - New tests cover unauthorized, malformed, replay, and policy-bypass scenarios.

### CODEX-P2-004: Observability and runbook mapping
- Owner: SRE
- Estimate: 3 days
- Dependencies: CODEX-P1-006
- Deliverable: Alert/runbook mapping for major gate failures (`G0-G9`).
- Acceptance:
  - Every failure class has documented alert and deterministic triage steps.

## Program-Level Milestones

1. Milestone M1 (end of week 2): P0 complete, control plane stabilized.
2. Milestone M2 (end of week 6): P1 complete, hotspot risk materially reduced.
3. Milestone M3 (end of week 12): P2 complete, audit-grade maturity baseline achieved.

## Reporting Cadence

1. Weekly risk review: open blockers, quality metrics trend, decision log.
2. Bi-weekly KPI publication to authoritative status doc.
3. End-of-phase deterministic proof run and evidence attachment.

