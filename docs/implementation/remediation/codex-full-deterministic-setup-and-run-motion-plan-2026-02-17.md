# Codex Full Deterministic Setup and Run Motion Plan

**Date:** 2026-02-17  
**Version:** 1.0  
**Status:** Proposed / Ready for Implementation  
**Owner:** Platform Engineering + Demo Reliability

## 1. Objective

Achieve an **entirely deterministic demo run posture** for deployment + notebook proof, so that the same code and inputs produce the same outputs on every run.

Target guarantee:

- Given the same:
  - Git commit SHA
  - `DEMO_SEED`
  - run configuration
  - podman machine spec
- and a clean deterministic reset,
- the pipeline must produce reproducible notebook status/results and stable evidence artifacts.

## 2. Current Gaps to Close

1. Stateful data/volumes are reused across runs.
2. Vault init/secrets are random and not controlled by deterministic run orchestration.
3. Runtime hotfix risk (packages installed live instead of only baked image state).
4. Mutable image tags (`latest`) can drift.
5. Some live query/dataframe flows can vary by order/timing.

## 3. Implementation Workstreams

## WS-1: Deterministic Environment Reset + Reseed

### Changes

- Add deterministic reset mode before each proof run:
  - Stop stack
  - Remove project-scoped volumes used by demo state
  - Recreate stack cleanly
- Add explicit deterministic seed phase:
  - Fixed seed inputs for graph/data generation
  - Deterministic baseline assertions (entity counts + required sentinel records)

### Proposed script updates

- `scripts/testing/run_demo_pipeline_repeatable.sh`
  - Add `DEMO_RESET_STATE=1` (default on for deterministic mode)
  - Add `DEMO_DETERMINISTIC_MODE=1` guard
- `scripts/testing/seed_demo_graph.sh`
  - Keep deterministic checks strict and fail-fast

### Acceptance

- Two consecutive runs with reset enabled produce identical PASS/FAIL matrix and deterministic summary metrics.

## WS-2: Immutable Runtime (No Live Hotfix Drift)

### Changes

- Enforce image-baked dependencies only for proof runs.
- Disallow ad-hoc `pip install` in live containers for “official deterministic” runs.
- Add pre-run validation to confirm required modules exist in image runtime.

### Proposed checks

- Add runtime module check script (pre-notebook):
  - verify `pydantic`, `pydantic-settings`, `email-validator`, notebook-critical modules.
- Fail proof run if runtime package state diverges from expected lock fingerprint.

### Acceptance

- Proof run passes with freshly built containers and no runtime package mutation.

## WS-3: Pin Images and Dependencies

### Changes

- Replace mutable `latest` references in deterministic path with pinned tags/digests.
- Record image digests used for each run in a manifest artifact.
- Lock Python dependencies used in container builds and record lock fingerprint.

### Proposed artifacts

- `exports/<run-id>/image_digests.txt`
- `exports/<run-id>/dependency_fingerprint.txt`
- `exports/<run-id>/run_manifest.json` (commit, seed, connection, image digests, lock hash)

### Acceptance

- Deterministic run fails if image digest or dependency fingerprint differs from expected baseline.

## WS-4: Deterministic Query/Output Ordering

### Changes

- Enforce explicit ordering in notebook queries and dataframe outputs:
  - Gremlin traversals: use explicit `order().by(...)`
  - pandas outputs: `sort_values(...)` + stable column ordering
- Normalize runtime locale/time settings:
  - `TZ=UTC`
  - stable locale env in notebook execution context

### Acceptance

- Notebook outputs are stable in row ordering and summary values for repeated runs.

## WS-5: Determinism Gate and Reproducibility Evidence

### Changes

- Add post-run determinism gate:
  - compute checksums for key outputs (`notebook_run_report.tsv`, summary, manifest)
  - compare against a stored baseline for same commit/seed/mode
- Emit machine-readable pass/fail reason on mismatch.

### Proposed script

- `scripts/testing/verify_deterministic_artifacts.sh`

### Acceptance

- Pipeline exits non-zero if deterministic fingerprints differ from baseline.

## 4. Deterministic Run Motion (Operational Sequence)

1. `preflight_check --strict`
2. validate podman connection + machine resource spec
3. hard reset stack state (`DEMO_RESET_STATE=1`)
4. build/recreate required images (pinned tags/digests)
5. deploy full stack
6. wait for all required services healthy
7. deterministic seed + baseline graph assertions
8. execute notebooks with fixed:
   - `DEMO_SEED`
   - `PYTHONHASHSEED=0`
   - fixed timeout policy
9. generate manifest + checksums + reports
10. compare deterministic fingerprints with baseline
11. emit final summary (`PASS` only if all checks + determinism gate pass)

## 5. CI/CD Integration Plan

- Add a dedicated deterministic workflow job:
  - runs on controlled runner profile
  - executes deterministic mode end-to-end
  - publishes artifacts and manifest
  - blocks merge on deterministic gate failure

## 6. Definition of Done

The setup is considered fully deterministic when all conditions are true:

- Final proof run is 100% passing.
- Same commit + seed + deterministic mode yields identical evidence fingerprints across repeated runs.
- No runtime dependency mutation is required.
- Image and dependency provenance are pinned and captured.
- Determinism gate is enforced both locally and in CI.

## 7. Initial Implementation Backlog (Concrete)

1. Add deterministic reset flags + implementation in `run_demo_pipeline_repeatable.sh`.
2. Add deterministic manifest/checksum generation and comparison script.
3. Pin image references used by deterministic path and record digests.
4. Add runtime package fingerprint check in notebook pipeline.
5. Sweep notebooks for explicit ordering and stable dataframe output ordering.
6. Add CI deterministic workflow and hard gate.

