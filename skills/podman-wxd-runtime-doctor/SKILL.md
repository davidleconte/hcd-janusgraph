# podman-wxd-runtime-doctor

## Purpose
Diagnose Podman machine/runtime health for this project before deployment or testing.

## Trigger when
- Podman connection fails.
- Services fail to start or health checks fail.
- Runtime status is inconsistent across commands.

## Workflow
1. Validate machine + connection:
`podman machine list`
`podman system connection list`
2. Validate remote service visibility:
`podman --remote ps`
3. Validate compose project isolation:
`COMPOSE_PROJECT_NAME=janusgraph-demo`
4. Validate service snapshot for expected containers.
5. If degraded, identify whether failure is:
- machine/connection
- compose/deploy
- service-specific (Vault, JanusGraph, Pulsar, Jupyter)

## Outputs
- Runtime diagnosis report
- Exact failing layer and next repair command set

## Guardrails
- Never use Docker commands as primary path.
- Preserve project isolation labels and naming.

