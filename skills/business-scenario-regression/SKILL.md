# business-scenario-regression

## Purpose
Validate business-level banking outcomes, not only technical pass/fail.

## Trigger when
- A remediation may affect AML/Fraud/UBO outcomes.
- Need to confirm no business regression after infra/runtime changes.

## Core scenarios
- Sanctions screening workflow
- AML structuring detection workflow
- Fraud detection workflow
- UBO ownership discovery workflow

## Workflow
1. Run deterministic proof pipeline.
2. Review notebook outputs and API responses for scenario acceptance criteria.
3. Compare against expected baseline behavior.
4. Document deltas as:
- expected change
- regression risk
- blocker/non-blocker

## Outputs
- Business regression verdict by scenario
- Required follow-up actions

## Guardrails
- A technical pass is insufficient without scenario-level validation.

