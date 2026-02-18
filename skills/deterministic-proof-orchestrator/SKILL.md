# deterministic-proof-orchestrator

## Purpose
Run and troubleshoot the canonical deterministic setup + notebook proof pathway.

## Trigger when
- User asks to verify full deterministic deployment.
- CI/local deterministic proof fails.
- Need pass/fail gate classification (`G0` to `G9`).

## Preconditions
- `conda activate janusgraph-analysis`
- Podman machine reachable
- Run from repository root

## Workflow
1. Run canonical wrapper:
`bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json`
2. Read status:
`exports/deterministic-status.json`
3. If non-zero, inspect:
`exports/<RUN_ID>/failed_gate.txt` and corresponding step log.
4. Confirm notebook report:
`exports/<RUN_ID>/notebook_run_report.tsv`
5. Confirm determinism gate:
`exports/<RUN_ID>/determinism.log` and baseline behavior.

## Outputs
- Deterministic status JSON
- Gate diagnosis
- Actionable remediation path per failed gate

## Guardrails
- Do not replace canonical command with ad-hoc scripts for final verdict.
- Keep `COMPOSE_PROJECT_NAME` stable (`janusgraph-demo`) unless explicitly changed.

