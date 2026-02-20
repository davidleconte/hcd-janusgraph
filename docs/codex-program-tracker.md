# Codex Program Tracker

- Date Created: 2026-02-18
- Program Window: 12 weeks
- Source Documents:
  - `docs/codex-audit-report-2026-02-18.md`
  - `docs/codex-implementation-plan-p0-p2.md`
  - `docs/codex-execution-task-board.md`

## Program Status

- Overall Status: `Not Started`
- Current Phase: `P0`
- Blockers:
  - GitHub issue creation via MCP blocked by token scope: `Resource not accessible by personal access token`

## KPI Progress

| KPI | Baseline | Target | Current | Status |
|---|---:|---:|---:|---|
| Typed functions | 65.9% | >=90% | 65.9% | Not Started |
| Functions >80 lines | 42 | <=10 | 42 | Not Started |
| Complexity >20 | 6 | <=1 | 6 | Not Started |
| Critical package coverage floors | mixed | >=75% each | mixed | Not Started |
| Debt markers | 143 | <=60 | 143 | Not Started |
| Workflow action lag | present | none | present | Not Started |

## Milestones

| Milestone | Target Date | Definition of Done | Status |
|---|---|---|---|
| M1 (P0 complete) | 2026-03-04 | CI gate hardening, docs authority normalized, workflow lag removed | Not Started |
| M2 (P1 complete) | 2026-04-01 | Hotspot refactors delivered with tests and logging standardization | Not Started |
| M3 (P2 complete) | 2026-05-13 | API/perf/security governance and regression controls in place | Not Started |

## Ticket Ledger

| Ticket ID | Title | Priority | Owner | Estimate | Status |
|---|---|---|---|---|---|
| CODEX-P0-001 | Per-package coverage gates | P0 | QA/SDET + Backend | 2d | Planned |
| CODEX-P0-002 | No new untyped public functions | P0 | Backend | 2d | Planned |
| CODEX-P0-003 | Workflow major-version upgrades | P0 | DevOps | 1d | Planned |
| CODEX-P0-004 | Docs authority normalization | P0 | Tech Writer + Backend | 2d | Planned |
| CODEX-P0-005 | Debt registry from TODO/FIXME/HACK | P0 | EM + Backend | 1d | Planned |
| CODEX-P1-001 | Refactor `graph_consumer` hotspot | P1 | Backend | 4d | Planned |
| CODEX-P1-002 | Refactor `vector_consumer` batch path | P1 | Backend | 3d | Planned |
| CODEX-P1-003 | Refactor insider-trading report pipeline | P1 | Backend | 4d | Planned |
| CODEX-P1-004 | Refactor fraud notebook compatibility path | P1 | Backend | 3d | Planned |
| CODEX-P1-005 | Refactor orchestrator export path | P1 | Backend | 3d | Planned |
| CODEX-P1-006 | Logging and exception standardization | P1 | Backend + SRE | 3d | Planned |
| CODEX-P1-007 | API contract regression suite | P1 | QA/SDET + Backend | 4d | Planned |
| CODEX-P2-001 | Performance SLO baseline and CI gate | P2 | SRE + QA/SDET | 5d | Planned |
| CODEX-P2-002 | API versioning and deprecation policy | P2 | Backend Lead + Architect | 3d | Planned |
| CODEX-P2-003 | Security negative-path test expansion | P2 | Security + QA/SDET | 4d | Planned |
| CODEX-P2-004 | Observability and runbook mapping | P2 | SRE | 3d | Completed (2026-02-20) |

## Weekly Update Template

### Week of YYYY-MM-DD

- Overall: `On Track | At Risk | Off Track`
- Completed:
  - [ ] Ticket ID - title
- In Progress:
  - [ ] Ticket ID - title
- Blocked:
  - [ ] Ticket ID - blocker and owner
- KPI Deltas:
  - Typed functions:
  - Coverage floors:
  - Complexity hotspots:
  - Debt markers:
