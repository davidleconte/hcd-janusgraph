# Audit Reports

**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
**Last Updated:** 2026-02-17

## Overview

This directory contains current audit reports and analysis documents for the HCD + JanusGraph Banking Platform.

## Active Audits

- **[codex-podman-wxd-deployment-live-notebook-proof-executive-summary-2026-02-17.md](codex-podman-wxd-deployment-live-notebook-proof-executive-summary-2026-02-17.md)** - 1-page executive status for deployment recovery and notebook proof
- **[codex-podman-wxd-deployment-live-notebook-proof-remediation-log-2026-02-17.md](codex-podman-wxd-deployment-live-notebook-proof-remediation-log-2026-02-17.md)** - Full issue-by-issue remediation log with evidence
- **[comprehensive-project-audit-2026-02-16.md](comprehensive-project-audit-2026-02-16.md)** - Full project audit and detailed remediation plan
- **[comprehensive-project-audit-2026-01-30.md](comprehensive-project-audit-2026-01-30.md)** - Full project audit
- **[deployment-scripts-audit-2026-02-11.md](deployment-scripts-audit-2026-02-11.md)** - Deployment scripts audit
- **[workflow-pip-audit-2026-02-11.md](workflow-pip-audit-2026-02-11.md)** - Workflow pip audit

## 2026-02-17 Closure Snapshot (Codex Run)

- Full deployment recovered and healthy on `podman-wxd-root`.
- Vault initialized/unsealed and healthy.
- Analytics API healthy after dependency/startup contract remediation.
- Final full notebook sweep: **15/15 PASS**.
- Final evidence artifact: `exports/live-notebooks-final-20260217T170000Z/notebook_run_report.tsv`.

## Impact Map — Deterministic Demo Reliability

### High-Impact Risks

- **Streaming message ordering/replay stability** → causes non-repeatable notebook outcomes and inconsistent fraud/AML baselines.
- **API contract drift** → endpoint results can differ by caller expectations and test fixtures.
- **Authentication/session fallback values** → hidden weak security state and non-obvious runtime failures.
- **Notebook runtime state** → implicit random seeds and wall-clock dependent behavior in generators.

### Mitigations Implemented

1. **Deterministic event sequencing**
   - File: `banking/streaming/events.py`
   - Replaces non-deterministic `hash()` behavior with SHA-256-based `sequence_id`.

2. **Stricter auth/session guardrails**
   - Files: `src/python/api/dependencies.py`, `src/python/utils/startup_validation.py`, `src/python/security/session_manager.py`
   - Removes implicit secret fallback, requires explicit strong secret when auth/session paths are used.

3. **Router → repository contract fixes**
   - Files: `src/python/api/routers/aml.py`, `src/python/api/routers/fraud.py`, `src/python/api/routers/ubo.py`, `src/python/repository/graph_repository.py`
   - Ensures request parameters are applied to graph queries and response shape aligns with endpoint contracts.

4. **Repeatable live pipeline runner**
   - File: `scripts/testing/run_demo_pipeline_repeatable.sh`
   - One-command flow with preflight, health waits, service snapshots, notebook replay report, and summary artifact.

5. **Expanded deterministic pipeline docs**
   - File: `scripts/README.md`
   - Documents execution path, outputs, and hard-fail behavior.

### Non-Detailed Example (Leads to deterministic runs)

- Set `DEMO_PIPELINE_RUN_ID=demo-2026-02-16` and `DEMO_SEED=42`.
- Run one command: `PODMAN_CONNECTION=podman-wxd bash scripts/testing/run_demo_pipeline_repeatable.sh`.
- A fresh `exports/demo-2026-02-16` folder is produced with all step logs + `notebook_run_report.tsv`.
- Non-PASS notebook entries are treated as a hard failure for operator confidence.

## Archive

Historical and superseded audit documents have been archived to:
- **[Local archive/](archive/)** - Directory-specific historical audits
- **[Project archive](../../archive/2026-02/audits/)** - Project-wide obsolete audits

## Related Documentation

- [Remediation Tracking](../remediation/)
- [Codex Full Deterministic Setup and Run Motion Plan (2026-02-17)](../remediation/codex-full-deterministic-setup-and-run-motion-plan-2026-02-17.md)
- [Production Readiness](../production-readiness-audit-2026.md)
- [Historical Archive](../../archive/2026-02/)
