# notebook-determinism-enforcer

## Purpose
Keep notebook determinism contracts enforced in strict mode.

## Trigger when
- Determinism sweep reports hard errors.
- Notebook proof regression appears.
- New notebook cells introduce non-deterministic patterns.

## Hard patterns
- `datetime.now()`
- `datetime.utcnow()`
- `date.today()`
- `time.time()`
- `uuid.uuid4()`
- `pandas.sample()` without `random_state`

## Workflow
1. Run sweep:
`bash scripts/testing/check_notebook_determinism_contracts.sh`
2. Replace hard patterns with deterministic constants/helpers.
3. Stabilize query outputs (`order()` before `limit()` where needed).
4. Re-run sweep until `errors: 0`.

## Outputs
- Clean determinism sweep
- Updated deterministic notebook cells

## Guardrails
- Do not weaken strict mode as a workaround.
- Keep demo semantics unchanged while fixing determinism.

