# Canonical Determinism Baseline

**Created:** 2026-03-13
**Commit:** 8afd7e8d4c61ccc0ce8ac3023f81e33fa596a6e4
**Seed:** 42

This is the authoritative baseline for deterministic runs. All pipeline runs
MUST match these checksums to pass the determinism gate.

## Checksums

```
d64c8c42ed9c1d19fd5adf11e872cfa63f5eb74d5237507074fe4776b38b9c47  notebook_run_report.tsv
93f7cb66f4da18fbaa7d69de9512da0e0cbbbf1aeab833dde78c63e3c6b63829  image_digests.txt
b175f6d08c6ec43ac117d7deb9735331a0389b2ff11518e140ebbfa9f7c8e88b  dependency_fingerprint.txt
b410ef94eb6c80932462685e39ff651598c60453f7e3200a24ba006a5aa8e567  runtime_package_fingerprint.txt
9f5b4bc3e06bf76af80e004b599002818ff5cc7800c38cc714ea9d0a90a93369  deterministic_manifest.json
```

## Validation

Run the determinism verification with strict mode:

```bash
DEMO_REQUIRE_EXISTING_BASELINE=1 \
DEMO_BASELINE_DIR=exports/determinism-baselines \
bash scripts/testing/verify_deterministic_artifacts.sh exports/demo-YYYYMMDDTHHMMSSZ
```

## Drift Policy

If checksums drift:
1. **DO NOT** update this baseline without explicit approval
2. Investigate root cause (non-deterministic code, dependency changes, seed issues)
3. Document the reason for any baseline update
4. Use `[determinism-override]` commit token for intentional changes
