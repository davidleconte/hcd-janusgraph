# Codex Single-Command Deterministic Fresh-Clone Implementation Plan

**Date:** 2026-02-17  
**Version:** 1.0  
**Status:** Proposed / Ready for Implementation  
**Owner:** Platform Engineering + Demo Reliability

## 1. Goal

Provide one command that a user can run from a fresh GitHub clone to:

1. Prepare Podman machine with required spec.
2. Prepare conda-forge Python environment.
3. Build and deploy all services.
4. Validate service health and runtime contracts.
5. Run all notebooks deterministically.
6. Emit final machine-readable and human-readable status.

Single command target:

```bash
bash scripts/onboarding/run_deterministic_fresh_clone.sh
```

## 2. Scope and Source Alignment

This plan implements and operationalizes:

1. `docs/implementation/audits/codex-podman-wxd-deployment-live-notebook-proof-remediation-log-2026-02-17.md` (R-01..R-18).
2. `docs/implementation/remediation/codex-full-deterministic-setup-and-run-motion-plan-2026-02-17.md` (WS-1..WS-5).
3. `docs/implementation/audits/codex-podman-wxd-fresh-machine-enforcement-matrix-2026-02-17.md` (enforcement mapping).

## 3. Command Contract

Command:

```bash
bash scripts/onboarding/run_deterministic_fresh_clone.sh
```

Optional flags:

```bash
--run-id <id>
--seed <int>                      # default 42
--podman-machine <name>           # default podman-wxd
--podman-cpus <int>               # default 4
--podman-memory-mb <int>          # default 8192
--podman-disk-gb <int>            # default 50
--strict-determinism              # default on
--no-reset                        # disables state reset (non-deterministic mode)
--skip-notebooks                  # diagnostics mode
--json                            # print final status JSON to stdout
```

Exit codes:

1. `0`: full PASS (all gates passed).
2. `10`: platform/tooling preflight failure.
3. `20`: Podman machine/connection failure.
4. `30`: build/deploy failure.
5. `40`: service health/contract failure.
6. `50`: notebook execution failure.
7. `60`: determinism fingerprint mismatch.

## 4. Required Outputs

For run id `<run-id>`, write:

1. `exports/<run-id>/status.json`
2. `exports/<run-id>/run_manifest.json`
3. `exports/<run-id>/notebook_run_report.tsv`
4. `exports/<run-id>/checksums.txt`
5. `exports/<run-id>/pipeline_summary.txt`
6. `exports/<run-id>/logs/*.log`

`status.json` minimum schema:

```json
{
  "run_id": "string",
  "commit_sha": "string",
  "seed": 42,
  "result": "PASS|FAIL",
  "failed_gate": "string|null",
  "started_at_utc": "ISO-8601",
  "ended_at_utc": "ISO-8601",
  "duration_seconds": 0,
  "services": {
    "vault": "healthy|unhealthy",
    "analytics_api": "healthy|unhealthy",
    "jupyter": "healthy|unhealthy",
    "hcd_server": "healthy|unhealthy",
    "janusgraph": "healthy|unhealthy"
  },
  "notebooks": {
    "total": 0,
    "pass": 0,
    "fail": 0
  },
  "determinism_gate": "pass|fail"
}
```

## 5. End-to-End Flow (Detailed)

### Phase 0: Tooling Preflight Gate

1. Verify commands: `podman`, `podman-compose`, `conda`, `uv`, `jq`.
2. Verify repo root and required files.
3. Fail fast with actionable message if missing.

Gate ID: `G0_PRECHECK`

### Phase 1: Podman Machine Spec and Connection Gate

1. Ensure machine exists (`podman-wxd` default), create if missing.
2. Enforce spec: `cpus=4`, `memory=8192MB`, `disk=50GB`.
3. Ensure machine running.
4. Resolve active connection and export `PODMAN_CONNECTION`.
5. Validate remote calls via `podman --remote ps`.

Gate ID: `G1_PODMAN`

### Phase 2: Conda-forge Environment Gate

1. Create/update `janusgraph-analysis` from project environment definition.
2. Enforce conda-forge resolver policy.
3. Install Python packages via `uv` in environment.
4. Verify deterministic vars (`JANUSGRAPH_PORT=18182`, SSL flags) are present.

Gate ID: `G2_ENV`

### Phase 3: Deterministic Reset Gate (WS-1)

1. If strict determinism: stop stack and remove project-scoped state volumes.
2. Clear prior transient outputs under `exports/<run-id>`.
3. Record reset action in manifest.

Gate ID: `G3_RESET`

### Phase 4: Build Gate

1. Build `localhost/hcd:1.2.3` from repo root.
2. Build or pull other required images in controlled order.
3. Record image IDs/digests.

Gate ID: `G4_BUILD`

### Phase 5: Deploy + Vault Gate

1. Deploy from `config/compose` with `COMPOSE_PROJECT_NAME=janusgraph-demo`.
2. Health wait loop for core containers.
3. If fresh Vault state: initialize/unseal and persist `.vault-keys` handling policy.
4. Validate Vault health (`initialized=true`, `sealed=false`).

Gate ID: `G5_DEPLOY_VAULT`

### Phase 6: Runtime Contract Gate (R-05..R-13)

1. Verify `analytics-api` starts and remains healthy.
2. Verify required runtime modules and permissions (incl. `/var/log/janusgraph`).
3. Verify required env injection (`OPENSEARCH_INITIAL_ADMIN_PASSWORD`).

Gate ID: `G6_RUNTIME_CONTRACT`

### Phase 7: Deterministic Seeding Gate

1. Seed deterministic demo graph with fixed seed.
2. Validate baseline assertions (counts + sentinel records).

Gate ID: `G7_SEED`

### Phase 8: Notebook Readiness + Execution Gate (R-14..R-18)

1. Validate active podman connection for notebook runner.
2. Validate exploratory mount/path (`/workspace/notebooks-exploratory`).
3. Validate notebook runtime dependencies (`pydantic`, `pydantic-settings`, `email-validator`).
4. Execute notebooks with:
   - `DEMO_SEED=<seed>`
   - `PYTHONHASHSEED=0`
   - `TZ=UTC`
   - fixed timeout budgets
5. Capture `notebook_run_report.tsv`.

Gate ID: `G8_NOTEBOOKS`

### Phase 9: Determinism Gate (WS-5)

1. Generate checksums of deterministic artifacts.
2. Compare against baseline for same commit + seed + mode.
3. Fail on mismatch.

Gate ID: `G9_DETERMINISM`

### Phase 10: Final Status Gate

1. Build final `status.json`.
2. Build `pipeline_summary.txt`.
3. Print concise final PASS/FAIL line with run id and failed gate when relevant.

Gate ID: `G10_STATUS`

## 6. Determinism Controls to Enforce

1. Default strict reset mode enabled.
2. No live package installation in containers during official run.
3. Image digest capture and dependency fingerprint capture.
4. Stable ordering requirements for notebook outputs and queries.
5. Stable runtime settings: `TZ=UTC`, `PYTHONHASHSEED=0`, fixed seed.

## 7. Failure and Retry Policy

1. Retry health probes with bounded backoff.
2. No silent fallback between podman connections.
3. No partial PASS; any failed gate sets overall FAIL.
4. Include remediation hint in `status.json` and summary for each gate failure.

## 8. File-by-File Implementation Plan

New files:

1. `scripts/onboarding/run_deterministic_fresh_clone.sh`
2. `scripts/testing/verify_deterministic_artifacts.sh`
3. `scripts/testing/collect_run_manifest.sh`
4. `scripts/testing/check_runtime_contracts.sh`

Modified files:

1. `scripts/testing/run_demo_pipeline_repeatable.sh` (strict deterministic mode defaults).
2. `scripts/testing/run_notebooks_live_repeatable.sh` (status + manifest integration).
3. `scripts/testing/seed_demo_graph.sh` (strict deterministic assertions).
4. `scripts/deployment/deploy_full_stack.sh` (single-command compatibility hooks).
5. `docs/guides/setup-guide.md` (single-command quickstart).
6. `docs/guides/deployment-guide.md` (command contract + outputs).
7. `docs/development/deployment-verification.md` (new gate IDs + acceptance).
8. `docs/operations/operations-runbook.md` (incident mapping to gates).

## 9. Acceptance Criteria

1. Fresh clone on supported host executes one command and completes end-to-end.
2. All required services healthy.
3. Notebook run report shows full pass set (current target 15/15).
4. `status.json` and manifest artifacts always generated.
5. Two consecutive strict runs on same commit + seed produce matching determinism fingerprints.

## 10. Rollout Plan

1. Implement scripts and gate wiring.
2. Run two consecutive local strict runs and compare artifacts.
3. Add CI deterministic workflow job.
4. Set CI gate to required for protected branch.

## 11. Non-Goals (for this implementation cycle)

1. Cross-platform package-manager bootstrapping beyond documented host prerequisites.
2. Re-architecture of notebooks beyond deterministic ordering and guards.
3. Production secrets governance redesign (demo-focused scope only).

