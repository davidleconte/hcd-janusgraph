# Codex MCP Rollout Execution Plan

**Date:** 2026-02-18  
**Version:** 1.0  
**Status:** Active  
**Scope:** Add MCP governance and onboarding without changing deterministic runtime behavior

## Objective

Adopt MCP as a control and evidence layer on top of the existing deterministic script-based execution path.

Canonical execution remains:

```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json
```

## Phase plan

| Phase | Description | Owner | Effort | Acceptance criteria |
|---|---|---|---|---|
| 0 | Governance lock in `AGENTS.md` | Platform + Security | 0.5 day | MCP policy section merged; read-only default and determinism rules explicit |
| 1 | Server discovery + inventory | DevOps | 0.5 day | Discovery matrix filled with endpoint/auth/owner/status for each target server |
| 2 | Reference existing MCP servers (read-only) | DevOps | 1 day | Configured servers return status/evidence queries; no write capability enabled |
| 3 | Read-only validation | QA + Platform | 0.5 day | CI status, podman runtime state, docs source-of-truth, and observability queries succeed via MCP |
| 4 | Build missing MCP servers | DevOps + SRE + Security | 2-5 days | Missing servers delivered with least-privilege scopes and audit logging |
| 5 | Optional controlled writes | Platform + Security | 1-2 days | Write actions require explicit user request and are fully auditable |

## Mandatory constraints

1. MCP is additive; scripts remain authoritative for deterministic setup/proof.
2. Default MCP mode is read-only.
3. No seed/state/order changing action without explicit user request.
4. Redact credentials and secrets in all MCP outputs.

## Target server set

1. GitHub MCP
2. Docs/File MCP
3. Podman MCP
4. Observability MCP (Prometheus/Grafana/Loki)
5. Security Evidence MCP

## Execution checklist

1. Confirm `AGENTS.md` contains active MCP policy (done).
2. Complete discovery matrix with real endpoint/auth metadata.
3. Register existing servers with read-only scopes in runtime config.
4. Validate deterministic-safe read-only workflows.
5. Create missing servers only after discovery confirms gaps.
6. Re-run deterministic proof command and confirm no behavior drift.

## Deliverables

1. `AGENTS.md` MCP policy section (governance).
2. Discovery matrix artifact (current status and ownership).
3. Runtime registration records (outside repo, platform-managed).
4. Validation evidence summary for audit traceability.
