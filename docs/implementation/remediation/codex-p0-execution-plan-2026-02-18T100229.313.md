# Codex P0 Execution Plan (Determinism-Safe)

**Date:** 2026-02-18  
**Status:** Active  
**Scope:** P0 remediation only, preserving mandatory deterministic behavior

## Objective

Close the highest-risk audit gaps without destabilizing the canonical deterministic setup and proof flow.

## File-by-file plan

| File | Exact edit | Owner | Acceptance criteria | Status |
|---|---|---|---|---|
| `.github/workflows/container-scan.yml` | Replace Docker-only image build path with engine-aware build/export (`podman` if available, fallback `docker`) and scan OCI/Docker archive via Trivy `input`. | DevOps | Workflow succeeds on CI runner; Trivy still blocks on HIGH/CRITICAL; no Docker-only hard dependency. | Implemented |
| `README.md` | Promote canonical CI-equivalent deterministic command using `deterministic_setup_and_proof_wrapper.sh`; align Python install guidance to `uv`-first with pip emergency fallback. | Platform + Docs | README deterministic command matches CI workflow; setup instructions do not conflict with `AGENTS.md`. | Implemented |
| `docs/technical-specifications.md` | Add explicit non-authoritative warning and canonical references for runtime deployment/proof. | Architecture + Docs | Readers are redirected to canonical scripts and current status docs; reduced operator ambiguity. | Implemented |
| `docs/operations/operations-runbook.md` | Add legacy-warning banner and canonical deterministic execution references. | Operations + Docs | Runbook no longer appears as primary runtime authority for deterministic execution. | Implemented |
| `banking/notebooks/02_AML_Structuring_Detection_Demo.ipynb` | Replace `datetime.now()` with deterministic reference timestamp helper and stable ordering in sample query output cells. | Analytics Notebook Owner | No hard non-deterministic pattern from this notebook in sweep output. | Planned |
| `banking/notebooks/03_Fraud_Detection_Demo.ipynb` | Replace `datetime.now()` usage with deterministic timestamp source. | Fraud Notebook Owner | Sweep reports no hard errors from this notebook. | Planned |
| `banking/notebooks/04_Customer_360_View_Demo.ipynb` | Replace `datetime.utcnow()` and `uuid.uuid4()` with deterministic equivalents (seeded UUID utility + fixed time source). | API/Notebook Owner | Sweep reports no hard errors from this notebook. | Planned |
| `banking/notebooks/06_TBML_Detection_Demo.ipynb` | Replace `datetime.now()` with deterministic timestamp source. | AML/TBML Owner | Sweep reports no hard errors from this notebook. | Planned |
| `banking/notebooks/07_Insider_Trading_Detection_Demo.ipynb` | Replace `datetime.now()` with deterministic timestamp source. | Fraud/Market Abuse Owner | Sweep reports no hard errors from this notebook. | Planned |
| `banking/notebooks/08_UBO_Discovery_Demo.ipynb` | Replace `datetime.now()` with deterministic timestamp source; add stable ordering where needed. | UBO Owner | Sweep reports no hard errors from this notebook. | Planned |
| `banking/notebooks/11_Streaming_Pipeline_Demo.ipynb` | Replace `datetime.utcnow()` with deterministic timestamp source. | Streaming Owner | Sweep reports no hard errors from this notebook. | Planned |
| `notebooks-exploratory/03_advanced_queries.ipynb` | Replace `time.time()` use with deterministic seeded/scoped constant for examples. | Developer Experience Owner | Sweep reports no hard errors from this notebook. | Planned |
| `scripts/testing/check_notebook_determinism_contracts.sh` | After notebook cleanup, switch strict default from advisory to enforce (`NOTEBOOK_DETERMINISM_STRICT=1` default). | Platform | Script exits non-zero on hard patterns without additional flags. | Planned |
| `.github/workflows/quality-gates.yml` | Raise test-coverage gate from 60 to target 70 once baseline proves stable. | QA + DevOps | CI fails under target threshold; no false positives from test selection drift. | Planned |
| `pyproject.toml` | Raise `--cov-fail-under` from 60 to 70 in pytest default addopts, synchronized with CI. | QA + Maintainers | Local/CI thresholds match; deterministic proof flow remains unaffected. | Planned |
| `src/python/api/*.py`, `src/python/repository/graph_repository.py` | Replace broad `except Exception` blocks in critical request/repository boundaries with typed domain exceptions + explicit HTTP mapping. | Backend | No broad catches in critical API/repository paths; tests assert precise error mapping. | Planned |

## Validation plan for this P0 wave

1. Run canonical deterministic command:
`bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json`
2. Confirm status JSON contains `exit_code: 0`.
3. Preserve strict determinism enforcement switch as deferred until notebook hard-pattern cleanup is complete.

## Notes

- Strict notebook determinism is currently blocked by known hard-pattern findings in live and exploratory notebooks.
- Coverage gate increase is intentionally staged to avoid destabilizing the current deterministic proof path before baseline alignment.
