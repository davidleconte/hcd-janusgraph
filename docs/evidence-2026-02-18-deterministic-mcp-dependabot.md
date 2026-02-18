# Evidence Snapshot: Deterministic Proof, MCP Validation, Dependabot Triage

Date: 2026-02-18
Scope: requested execution of steps `1,2,3` (evidence snapshot, commit/push, PR triage)

## 1) Deterministic proof evidence

Command evidence source:
- `exports/deterministic-status.json`
- `exports/demo-20260218T130558Z/pipeline_summary.txt`
- `exports/demo-20260218T130558Z/notebook_run_report.tsv`

Observed result:
- Run ID: `demo-20260218T130558Z`
- Wrapper exit code: `0`
- Project: `janusgraph-demo`
- Steps included: reset, preflight, isolation, deploy, runtime contracts, notebooks, data generators, determinism
- Notebook results: `15 PASS`, `0 FAIL`

Notes:
- `exports/deterministic-status.json` currently reports `timestamp_utc` as `2026-02-18T13:17:51.3NZ` (non-standard fractional formatting) but carries `exit_code: 0`.

## 2) MCP GitHub validation evidence

Validated MCP operations against `davidleconte/hcd-janusgraph`:
- `search_repositories` (repository discovery)
- `get_file_contents` (repository file read)
- `list_pull_requests` (open PR retrieval)
- `list_issues` / `search_issues` (issue/PR search)
- `get_pull_request`, `get_pull_request_files`, `get_pull_request_status` (triage data retrieval)

Outcome:
- MCP GitHub operations are functional with authenticated access.

## 3) Open Dependabot PR triage (MCP-sourced)

Snapshot scope includes all currently open Dependabot PRs found by MCP query `repo:davidleconte/hcd-janusgraph is:pr is:open author:app/dependabot`.

| PR | Title | Change Surface | CI Status | Priority | Recommendation |
|---|---|---|---|---|---|
| [#5](https://github.com/davidleconte/hcd-janusgraph/pull/5) | `github/codeql-action` `3 -> 4` | `.github/workflows/security*.yml` (`init/autobuild/analyze/upload-sarif`) | `pending` (`0` statuses) | `P0` | Validate security workflow compatibility first, then merge. |
| [#7](https://github.com/davidleconte/hcd-janusgraph/pull/7) | `actions/setup-python` `5 -> 6` | Multiple CI workflows | `pending` (`0` statuses) | `P0` | Confirm runner compatibility (Node 24-era actions), then merge with CI workflow batch. |
| [#12](https://github.com/davidleconte/hcd-janusgraph/pull/12) | `actions/checkout` `4 -> 6` | Multiple CI workflows | `pending` (`0` statuses) | `P0` | Merge with `#7` after runner/version precheck and green CI. |
| [#2](https://github.com/davidleconte/hcd-janusgraph/pull/2) | `codecov/codecov-action` `4 -> 5` | `.github/workflows/quality-gates.yml` | `pending` (`0` statuses) | `P1` | Validate Codecov v5 input behavior and tokenless/public upload mode, then merge. |
| [#17](https://github.com/davidleconte/hcd-janusgraph/pull/17) | `parso` `0.8.5 -> 0.8.6` | `requirements*.txt` | `pending` (`0` statuses) | `P1` | Low risk dependency bump; merge after standard tests. |
| [#24](https://github.com/davidleconte/hcd-janusgraph/pull/24) | `opentelemetry-exporter-otlp-proto-http` `1.15.0 -> 1.39.1` | `requirements-tracing.txt` | `pending` (`0` statuses) | `P2` | High version delta with upstream breaking changes in telemetry stack; run targeted tracing/integration checks before merge. |

## 4) Recommended execution sequence

1. `P0`: merge CI platform upgrades as a controlled batch (`#5`, `#7`, `#12`) after runner compatibility check and passing workflows.
2. `P1`: merge `#2` and `#17` after quality gates pass.
3. `P2`: process `#24` last with explicit telemetry regression checks.

## 5) Audit gaps identified

- All 6 Dependabot PRs currently show `pending` with no recorded status checks (`total_count: 0`), so there is no automated pass/fail signal in the PR metadata snapshot.
- Telemetry dependency jump in `#24` spans many releases and should not be auto-merged without runtime verification.
