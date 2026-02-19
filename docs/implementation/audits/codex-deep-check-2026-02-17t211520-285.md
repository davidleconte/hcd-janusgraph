# codex deep check report

**date:** 2026-02-17
**timestamp_utc:** 2026-02-17T211520.285
**status:** active

## Summary
- static script quality: pass (`bash -n`, `shellcheck`)
- determinism control flow: pass (`G9_DETERMINISM` maps to `exit_code=60` with consistent `status.json`)
- manifest/checksum pipeline: pass (`run_manifest.json`, `deterministic_manifest.json`, `image_digests.txt`, `dependency_fingerprint.txt`)
- live deployment: pass on active root connection (`podman-wxd-root`)
- notebook status: pass (`15/15` notebooks `PASS`, `0` fail)

## Key finding
- connection mismatch risk exists when forcing `PODMAN_CONNECTION=podman-wxd` while active containers run on `podman-wxd-root`.
- enforcement objective: resolve and use the active connection hosting the compose project containers.

## Evidence snapshot
- podman machine: `podman-wxd` running (12 CPU, 24GiB RAM, 254GiB disk)
- services: core `janusgraph-demo` containers up, most healthy
- latest notebook report: `exports/live-notebooks-final-20260217T170000Z/notebook_run_report.tsv`

## Next actions requested
1. implement active-connection enforcement in scripts/docs
2. commit and push
3. run fresh full deterministic end-to-end execution
