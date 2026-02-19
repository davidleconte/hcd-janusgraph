# Codex Implementation Plan (P0-P2)

- Date: 2026-02-18
- Horizon: 12 weeks
- Goal: Move quality posture from `C+` to at least `B+` while preserving deterministic deployment and runtime security constraints.

## Program Objectives

1. Raise typed function ratio from `65.9%` to `>=90%`.
2. Reduce long-function tail from `42` functions >80 lines to `<=10`.
3. Reduce critical complexity hotspots (>20) from `6` to `<=1`.
4. Enforce per-package coverage floors `>=75%` for critical banking domains.
5. Eliminate docs authority drift and stale metric duplication.
6. Remove CI workflow major-version lag.

## Team Model and Capacity

1. Backend engineers: `3`
2. QA/SDET: `1`
3. DevOps: `0.5`
4. Tech Writer: `0.5`
5. Estimated effort: `44-56 engineer-weeks`

## Phase Plan

## P0 (Weeks 1-2): Control Plane Hardening

### Scope

1. CI gate realignment:
   - Add per-package coverage thresholds for critical modules.
   - Fail on new untyped public functions.
2. Docs authority normalization:
   - Centralize numerical status metrics in `docs/project-status.md`.
   - Remove stale duplicate metrics from top-level docs.
3. CI workflow hygiene:
   - Upgrade lagging action major versions.
4. Debt triage:
   - Convert TODO/FIXME/HACK inventory into owned issues.

### Exit Criteria

1. CI blocks threshold regressions.
2. No conflicting metrics across authoritative docs.
3. Workflow major versions current.
4. Deterministic proof path remains green.

## P1 (Weeks 3-6): Code Risk Reduction

### Scope

1. Refactor complexity hotspots:
   - `banking/streaming/graph_consumer.py`
   - `banking/streaming/vector_consumer.py`
   - `banking/analytics/detect_insider_trading.py`
   - `banking/fraud/notebook_compat.py`
   - `banking/data_generators/orchestration/master_orchestrator.py`
2. Standardize structured logging and exception handling.
3. Expand edge/failure-path tests and API contract tests.

### Exit Criteria

1. Hotspot complexity and function-size targets met for refactored modules.
2. Critical package coverage floors met.
3. Contract tests cover backward compatibility scenarios.

## P2 (Weeks 7-12): Audit-Grade Maturity

### Scope

1. Performance governance:
   - Define SLO budgets and perf regression thresholds in CI.
2. API lifecycle governance:
   - Formal deprecation/versioning policy and compatibility matrix.
3. Security hardening:
   - Expand negative-path tests for auth/session/input validation.
4. Observability hardening:
   - Ensure gate-class failures map to actionable alerts and runbooks.

### Exit Criteria

1. Perf regressions are gate-blocking.
2. Versioning/deprecation policy is enforced in release workflows.
3. Security negative-path coverage is demonstrably expanded.
4. Deterministic and integration paths remain stable.

## Governance Cadence

1. Weekly architecture and risk review.
2. Twice-weekly KPI check against target table.
3. End-of-phase deterministic evidence run and status publication.

## KPI Table

| KPI | Baseline | Target |
|---|---:|---:|
| Typed functions | 65.9% | >=90% |
| Functions >80 lines | 42 | <=10 |
| Complexity >20 | 6 | <=1 |
| Critical package coverage floors | mixed | >=75% each |
| Debt markers | 143 | <=60 |
| Workflow action lag | present | none |

