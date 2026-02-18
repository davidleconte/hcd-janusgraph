# Codex MCP Server Discovery Matrix

**Date:** 2026-02-18  
**Version:** 1.0  
**Status:** Active  
**Scope:** Inventory MCP servers required for deterministic-safe operations and evidence workflows

## Discovery baseline

Session discovery result on 2026-02-18:

- `list_mcp_resources` returned no configured resources.
- `list_mcp_resource_templates` returned no configured templates.

Interpretation: no MCP server is currently connected in this workspace session.

## Server inventory matrix

| Server | Required for project | Current status | Endpoint/registration | Auth method | Owner | Allowed mode | Next action |
|---|---|---|---|---|---|---|---|
| GitHub MCP | Yes | Not configured in current session | TBD | GitHub App or PAT (least privilege) | Platform | Read-only | Register server and validate CI/workflow status reads |
| Docs/File MCP | Yes | Not configured in current session | TBD | Local runtime credentials | Platform | Read-only | Register server and validate canonical docs reads |
| Podman MCP | Yes | Not configured in current session | TBD | Local socket/connection credentials | DevOps | Read-only | Register server and validate machine/container status queries |
| Observability MCP | Yes | Not configured in current session | TBD | Prometheus/Grafana/Loki scoped credentials | SRE | Read-only | Register server and validate metrics/log evidence queries |
| Security Evidence MCP | Yes | Not configured in current session | TBD | Scanner/Vault scoped credentials | Security | Read-only | Register server and validate vulnerability/secret evidence reads |

## Required metadata before activation

1. Server runtime location and owning team.
2. Authentication model and rotation policy.
3. Permission scope (read-only baseline).
4. Audit logging destination and retention.
5. Break-glass procedure for temporary write permissions.

## Acceptance criteria

1. Every required server has an owner and registration endpoint.
2. Read-only scope is enforced for all servers.
3. Determinism-sensitive write actions are disabled by default.
4. Evidence responses include source, timestamp, scope, and verdict.
