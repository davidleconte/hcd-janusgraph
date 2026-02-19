# Codex GitHub Issue Drafts (P0-P2)

- Date: 2026-02-18
- Target Repo: `davidleconte/hcd-janusgraph`
- Status: Drafts prepared because MCP issue creation is blocked by PAT scope (`Resource not accessible by personal access token`).

Use each section as the issue title/body in GitHub.

---

## CODEX-P0-001: Per-package coverage gates

### Body

## Objective
Add CI coverage thresholds for critical banking packages.

## Scope
- Enforce package-level coverage floors for `banking/streaming`, `banking/compliance`, `banking/aml`, `banking/fraud`.
- Fail PRs when a package drops below threshold.

## Acceptance Criteria
- CI blocks on package-level coverage regression.
- Thresholds documented in repo docs and workflow comments.

## Estimate
2 days

## Dependencies
None

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P0-002: No new untyped public functions

### Body

## Objective
Enforce type-safety gate for new public functions.

## Scope
- Add CI check to reject newly introduced untyped public functions.
- Keep existing backlog as gradual migration, but enforce no new debt.

## Acceptance Criteria
- PR with new untyped public function fails quality gate.
- Rule is documented in contributor guidance.

## Estimate
2 days

## Dependencies
None

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P0-003: Workflow major-version upgrades

### Body

## Objective
Remove CI workflow action major-version lag.

## Scope
- Upgrade lagging GitHub Actions versions in `.github/workflows/`.
- Verify compatibility with current pipeline behavior.

## Acceptance Criteria
- No outdated major action versions remain.
- Workflows continue to pass with updated actions.

## Estimate
1 day

## Dependencies
None

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P0-004: Docs authority normalization

### Body

## Objective
Eliminate conflicting metrics/status claims across docs.

## Scope
- Keep `docs/project-status.md` as single authoritative metrics source.
- Remove stale or duplicate numeric status from top-level/module READMEs.

## Acceptance Criteria
- No conflicting project status metrics in non-authoritative docs.
- Cross-links point to `docs/project-status.md`.

## Estimate
2 days

## Dependencies
None

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P0-005: Debt registry from TODO/FIXME/HACK

### Body

## Objective
Build a managed debt registry from markers in code/docs.

## Scope
- Inventory TODO/FIXME/HACK markers.
- Map each marker to owner, severity, ETA, and resolution path.

## Acceptance Criteria
- 100% markers mapped to issue/work item or removed.
- Debt register published and maintained.

## Estimate
1 day

## Dependencies
None

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P1-001: Refactor graph_consumer complexity hotspot

### Body

## Objective
Reduce complexity and improve testability in `banking/streaming/graph_consumer.py`.

## Scope
- Split event processing into typed handlers/services.
- Isolate retries/error mapping from business logic.

## Acceptance Criteria
- Complexity and function length reduced to target profile.
- Failure-path unit tests added.

## Estimate
4 days

## Dependencies
CODEX-P0-002

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P1-002: Refactor vector_consumer batch path

### Body

## Objective
Decompose `banking/streaming/vector_consumer.py` batch pipeline into explicit units.

## Scope
- Break batch processing into parse/validate/transform/write stages.
- Add typed interfaces and deterministic error behavior.

## Acceptance Criteria
- Reduced branching and improved unit testability.
- Higher failure-path coverage.

## Estimate
3 days

## Dependencies
CODEX-P1-001

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P1-003: Refactor insider-trading report pipeline

### Body

## Objective
Decompose insider-trading report generation for maintainability and correctness.

## Scope
- Refactor `banking/analytics/detect_insider_trading.py` report logic into composable stages.
- Improve type clarity and edge-case handling.

## Acceptance Criteria
- Complexity hotspot removed.
- Output remains behaviorally equivalent on deterministic fixtures.

## Estimate
4 days

## Dependencies
CODEX-P0-002

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P1-004: Refactor fraud notebook compatibility path

### Body

## Objective
Isolate notebook compatibility adapter logic from runtime core path.

## Scope
- Refactor `banking/fraud/notebook_compat.py`.
- Preserve notebook behavior while reducing production-path coupling.

## Acceptance Criteria
- Compatibility preserved.
- Core fraud pipeline is simpler and more testable.

## Estimate
3 days

## Dependencies
CODEX-P1-003

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P1-005: Refactor orchestrator export path

### Body

## Objective
Reduce complexity in export logic under `master_orchestrator`.

## Scope
- Split export behavior by format/strategy.
- Add deterministic I/O boundary tests.

## Acceptance Criteria
- Function-size and complexity tail reduced.
- Export contract unchanged.

## Estimate
3 days

## Dependencies
CODEX-P0-002

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P1-006: Logging and exception standardization

### Body

## Objective
Standardize structured logging and exception taxonomy across refactored hotspots.

## Scope
- Replace ad-hoc prints in critical runtime modules.
- Ensure consistent exception categories and context fields.

## Acceptance Criteria
- Queryable structured logs for key runtime flows.
- No ambiguous exception pathways in targeted modules.

## Estimate
3 days

## Dependencies
CODEX-P1-001, CODEX-P1-002, CODEX-P1-003, CODEX-P1-004, CODEX-P1-005

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P1-007: API contract regression suite

### Body

## Objective
Protect backward compatibility with API contract regression tests.

## Scope
- Add contract tests for key routes and response schemas.
- Validate compatibility expectations on PRs.

## Acceptance Criteria
- Breaking contract changes are gate-blocking.
- Compatibility baselines are documented.

## Estimate
4 days

## Dependencies
CODEX-P0-001

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P2-001: Performance SLO baseline and CI gate

### Body

## Objective
Establish measurable SLOs and enforce performance regression gates.

## Scope
- Define latency/throughput/error budgets for critical paths.
- Add CI checks that fail on significant regression.

## Acceptance Criteria
- Performance regressions fail CI according to agreed policy.
- Baselines documented and reviewed.

## Estimate
5 days

## Dependencies
CODEX-P1-001, CODEX-P1-002, CODEX-P1-003, CODEX-P1-004, CODEX-P1-005, CODEX-P1-006, CODEX-P1-007

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P2-002: API versioning and deprecation policy

### Body

## Objective
Formalize API lifecycle governance.

## Scope
- Publish versioning/deprecation policy.
- Add compatibility matrix and release checklist controls.

## Acceptance Criteria
- Policy published and referenced by release workflow.
- New deprecations require migration guidance and timeline.

## Estimate
3 days

## Dependencies
CODEX-P1-007

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P2-003: Security negative-path test expansion

### Body

## Objective
Expand abuse-case and negative-path security tests.

## Scope
- Add tests for unauthorized access, malformed payloads, replay, and bypass attempts.
- Increase coverage of auth/session/input validation failure modes.

## Acceptance Criteria
- New negative-path tests are enforced by CI.
- Security test evidence linked in status docs.

## Estimate
4 days

## Dependencies
CODEX-P0-001, CODEX-P0-002

## Source
`docs/codex-execution-task-board.md`

---

## CODEX-P2-004: Observability and runbook mapping

### Body

## Objective
Map major gate failures to alerts and deterministic runbooks.

## Scope
- Align `G0-G9` failure classes with alert rules and runbook actions.
- Ensure each class has owner and on-call triage path.

## Acceptance Criteria
- Each failure class has an actionable runbook and alert mapping.
- Triage path is validated in operational drills.

## Estimate
3 days

## Dependencies
CODEX-P1-006

## Source
`docs/codex-execution-task-board.md`

