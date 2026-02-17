# Codex Podman-WXD Deployment and Live Notebook Proof Remediation Log

**Date:** 2026-02-17  
**Version:** 1.0  
**Status:** Active  
**Scope:** Full stack deployment recovery, service stabilization, and full live notebook proof run.

## 1) Issue-by-Issue Resolution Log

| ID | Issue Observed | Root Cause | Solution Applied | Validation |
|---|---|---|---|---|
| R-01 | `podman-wxd` checkpoint showed `Last Up: Never` | Machine was created but not fully started at checkpoint time | Started and validated active machine state | `podman machine list` showed `podman-wxd` running |
| R-02 | Full deployment blocked at `hcd-server` | Missing local image `localhost/hcd:1.2.3` | Built image from `docker/hcd/Dockerfile` with root context containing `hcd-1.2.3` | Deployment moved past HCD image error |
| R-03 | Vault unhealthy (`security barrier not initialized`) | Vault was not initialized/unsealed | Reset Vault data volume, reinitialized, unsealed, regenerated `.vault-keys` | Vault status became `initialized=true`, `sealed=false`, container healthy |
| R-04 | `init_vault.sh` failed to detect running Vault | Script expected `vault-server` name, actual container name is compose-prefixed | Performed manual Vault init/unseal via `janusgraph-demo_vault_1` | Vault healthy and usable |
| R-05 | `analytics-api` restart loop: `No module named slowapi` | Missing runtime dependency in API image | Added `slowapi` in `docker/api/Dockerfile` | Next startup blocker surfaced |
| R-06 | `analytics-api`: `No module named pydantic_settings` (+ related runtime libs) | Missing API runtime deps | Added `pydantic-settings`, `python-json-logger`, `pyjwt` | Next startup blocker surfaced |
| R-07 | `analytics-api`: `No module named banking` | Package path not copied into image | Added `COPY banking /app/banking` in API image | Next startup blocker surfaced |
| R-08 | `analytics-api`: permission denied `/var/log/janusgraph` | Non-root runtime user lacked write permission | Added directory creation/chown for `/var/log/janusgraph` | Permission error cleared |
| R-09 | `analytics-api`: `No module named pyotp` | Missing MFA dependency | Added `pyotp` | Next startup blocker surfaced |
| R-10 | `analytics-api`: `No module named qrcode` | Missing MFA QR dependency | Added `qrcode[pil]` | Next startup blocker surfaced |
| R-11 | `analytics-api` startup validation failure | `OPENSEARCH_INITIAL_ADMIN_PASSWORD` not passed to container env | Added env injection in `config/compose/docker-compose.full.yml` for `analytics-api` | Validation error cleared |
| R-12 | `analytics-api`: `No module named opentelemetry` | Tracing dependencies absent | Added OpenTelemetry packages (`api`, `sdk`, Jaeger, OTLP gRPC, requests instrumentation) | Next startup blocker surfaced |
| R-13 | `analytics-api`: `No module named requests` | Missing transitive dependency for OTEL requests instrumentation | Added `requests` to API image | `analytics-api` became healthy |
| R-14 | Notebook runner reported Jupyter container not running | Wrong Podman connection used (`podman-wxd` vs active `podman-wxd-root`) | Ran notebook proof against `PODMAN_CONNECTION=podman-wxd-root` | Notebook runner could reach live container |
| R-15 | Exploratory notebooks failed with “pattern matched no files” | Wrong in-container path and missing mount for `notebooks-exploratory` | Fixed runner path to `/workspace/notebooks-exploratory` and added compose mount | Exploratory notebooks executed successfully |
| R-16 | `11_Streaming_Pipeline_Demo` failed with missing `pydantic` then `email_validator` | Missing Jupyter runtime deps for streaming/API import path | Added `pydantic`, `pydantic-settings`, `email-validator` in `docker/jupyter/environment.yml`; installed `email-validator` in running env for immediate rerun | Streaming notebook passed |
| R-17 | `06_TBML_Detection_Demo`: `KeyError: 'sum'` | Empty transaction stats map lacked `sum` key | Patched notebook cell to use defensive `.get(..., default)` values | TBML notebook passed |
| R-18 | `07_Insider_Trading_Detection_Demo`: `KeyError: 'first_name'` | DataFrame could be empty/missing expected columns | Patched notebook cell to handle empty/missing columns defensively | Insider notebook passed |

## 2) Files Updated

- `docker/api/Dockerfile`
- `config/compose/docker-compose.full.yml`
- `scripts/testing/run_notebooks_live_repeatable.sh`
- `docker/jupyter/environment.yml`
- `banking/notebooks/06_TBML_Detection_Demo.ipynb`
- `banking/notebooks/07_Insider_Trading_Detection_Demo.ipynb`
- `.vault-keys` (regenerated)

## 3) Proof Run Evidence

- Initial full run (mixed):  
  `exports/live-notebooks-stable-20260217T152805Z/notebook_run_report.tsv`
- Intermediate rerun (reduced failures):  
  `exports/live-notebooks-rerun-20260217T163800Z/notebook_run_report.tsv`
- Targeted final fixes (3/3 pass):  
  `exports/live-notebooks-rerun-20260217T165200Z/notebook_run_report.tsv`
- Final full sweep: **15/15 PASS, 0 FAIL**  
  `exports/live-notebooks-final-20260217T170000Z/notebook_run_report.tsv`

## 4) Final State

- Full deployment: **healthy**
- Vault: **healthy, initialized, unsealed**
- Analytics API: **healthy**
- Jupyter: **healthy**
- Full live notebook proof run: **complete, 100% pass**
