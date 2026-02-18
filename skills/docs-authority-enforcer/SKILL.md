# docs-authority-enforcer

## Purpose
Keep docs aligned with implemented runtime commands, services, and ports.

## Trigger when
- Deployment commands or service contracts changed.
- Audit finds stale `docker-compose` or outdated port/service naming in active docs.

## Workflow
1. Identify authoritative docs (README, QUICKSTART, AGENTS, active runbooks).
2. Cross-check against implemented scripts/workflows.
3. Update active docs to canonical commands.
4. Mark legacy docs as non-authoritative or archive them.
5. Re-scan for prohibited stale patterns in active docs.

## Outputs
- Documentation drift report
- Updated authoritative docs and archival notes

## Guardrails
- Do not rewrite historical audit artifacts as active runbooks.
- Preserve clear distinction between active and legacy documents.

