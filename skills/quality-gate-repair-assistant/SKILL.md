# quality-gate-repair-assistant

## Purpose
Run CI-equivalent quality gates locally and repair failures in the correct order.

## Trigger when
- CI quality-gates fail.
- Local repo is drifted from formatting/lint/type/coverage expectations.

## Workflow
1. Run gate sequence:
- coverage/test gate
- docstring coverage
- mypy
- ruff
- black
- isort
2. Classify failures:
- environment/dependency
- configuration mismatch
- code defects
- style/formatting
3. Fix in this order:
- env/config blockers
- formatter/import ordering
- lint defects
- type defects
- test/coverage defects

## Outputs
- Gate-by-gate pass/fail report
- Minimal repair patch set

## Guardrails
- Keep deterministic runtime behavior intact.
- Do not lower gates as first response.

