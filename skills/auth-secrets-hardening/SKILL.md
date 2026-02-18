# auth-secrets-hardening

## Purpose
Ensure auth/session behavior is secure and testable under strict secret requirements.

## Trigger when
- Tests fail with `api_jwt_secret must be configured`.
- Startup/auth endpoints fail due missing secret material.
- Session manager behavior is inconsistent across environments.

## Workflow
1. Confirm secret requirements in:
- `src/python/security/session_manager.py`
- `src/python/api/dependencies.py`
- `src/python/utils/startup_validation.py`
2. For tests, set deterministic test secret values in test runtime.
3. Validate startup path behavior in prod-like vs test/dev modes.
4. Re-run targeted auth/session test subsets.

## Outputs
- Reproducible auth test setup
- Explicit secret contract documented and enforced

## Guardrails
- No weak fallback secrets.
- No bypass of production-like validation in runtime code.

