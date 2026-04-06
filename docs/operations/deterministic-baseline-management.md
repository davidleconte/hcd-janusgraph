# Deterministic Baseline Management

**Version:** 1.0  
**Last Updated:** 2026-04-06  
**Owner:** Platform Engineering

---

## Table of Contents

1. [Overview](#overview)
2. [Baseline Types](#baseline-types)
3. [Baseline Verification Checklist](#baseline-verification-checklist)
4. [Update Process](#update-process)
5. [Multi-Seed Management](#multi-seed-management)
6. [Corruption Detection](#corruption-detection)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What is a Baseline?

A **baseline** is a set of SHA-256 checksums representing the expected output of a deterministic pipeline run. It serves as the reference for detecting drift and ensuring reproducibility.

### Why Baselines Matter

- **Reproducibility**: Ensures identical output across runs
- **Drift Detection**: Identifies unintended changes
- **Quality Gate**: Prevents broken code from merging
- **Audit Trail**: Documents intentional changes

### Baseline Location

```
exports/determinism-baselines/
├── CANONICAL_42.checksums      # Primary (seed 42)
├── CANONICAL_123.checksums     # Secondary (seed 123)
├── CANONICAL_999.checksums     # Stress test (seed 999)
└── README.md                   # Seed documentation
```

---

## Baseline Types

### 1. Canonical Baseline (Primary)

- **File:** `CANONICAL_42.checksums`
- **Seed:** 42
- **Purpose:** Primary reference for CI/CD
- **Update Frequency:** Only on intentional changes
- **Protection:** Requires `[determinism-override]` token + CI verification

### 2. Secondary Baseline

- **File:** `CANONICAL_123.checksums`
- **Seed:** 123
- **Purpose:** Validation and cross-checking
- **Update Frequency:** Synchronized with primary
- **Protection:** Same as primary

### 3. Stress Test Baseline

- **File:** `CANONICAL_999.checksums`
- **Seed:** 999
- **Purpose:** Large-scale testing (10x data)
- **Update Frequency:** Monthly or on major changes
- **Protection:** Same as primary

---

## Baseline Verification Checklist

Before promoting any run to canonical baseline:

### Automated Checks (CI)

✅ These are automatically verified by `.github/workflows/verify-baseline-update.yml`:

- [ ] All notebooks status = `PASS`
- [ ] Deterministic status `exit_code = 0`
- [ ] No error cells in notebooks
- [ ] Checksums file exists and is valid (5 lines, SHA-256 format)
- [ ] Runtime fingerprint stable
- [ ] Image digests recorded
- [ ] `[determinism-override]` token present in commit message

### Manual Checks (Human Review)

⚠️ These require human judgment:

- [ ] **Visual Inspection**: Notebook outputs look correct
- [ ] **Business Logic**: Results match expected behavior
- [ ] **No Warnings**: No unexpected warnings in logs
- [ ] **Performance**: Metrics within acceptable range
- [ ] **Change Reason**: Clear documentation of why baseline changed
- [ ] **Impact Analysis**: Understand what changed and why
- [ ] **Regression Check**: No unintended side effects

### Quality Gate Commands

Run these to verify quality before updating:

```bash
# 1. Verify notebook report quality
awk -F'\t' 'NR>1 {
  if ($2 != "PASS") failed++;
  if ($3 == "") no_output++;
  if ($4 ~ /error/i) errors++;
}
END {
  print "Failed:", failed;
  print "No output:", no_output;
  print "Errors:", errors;
  exit (failed + no_output + errors > 0 ? 1 : 0);
}' exports/demo-*/notebook_run_report.tsv

# 2. Verify deterministic status
jq -e '.exit_code == 0' exports/deterministic-status.json

# 3. Verify checksums format
grep -E '^[a-f0-9]{64}  [a-zA-Z0-9_.-]+$' exports/demo-*/checksums.txt | wc -l
# Should output: 5

# 4. Run automated verification
bash scripts/validation/verify_baseline_quality.sh exports/demo-<run-id>
```

---

## Update Process

### When to Update Canonical Baseline

Update the baseline when:

1. **Intentional Code Changes**
   - New features that change output
   - Bug fixes that alter behavior
   - Algorithm improvements

2. **Notebook Changes**
   - New notebooks added
   - Existing notebooks modified
   - Output format changes

3. **Infrastructure Changes**
   - Container image updates
   - Python package updates
   - Configuration changes

4. **Data Changes**
   - Seed data modifications
   - Schema changes
   - Generator updates

### Step-by-Step Update Process

#### Step 1: Run Deterministic Pipeline

```bash
# Run with default seed (42)
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json

# Or with specific seed
DEMO_SEED=123 bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

#### Step 2: Verify Output Quality

```bash
# Get run ID
RUN_ID=$(jq -r '.run_id' exports/deterministic-status.json)

# Run automated verification
bash scripts/validation/verify_baseline_quality.sh "exports/${RUN_ID}"

# Expected output: ✅ VERIFICATION PASSED
```

#### Step 3: Review Changes

```bash
# Compare current vs canonical
SEED=42  # or your seed
diff -u exports/determinism-baselines/CANONICAL_${SEED}.checksums \
        "exports/${RUN_ID}/checksums.txt"

# Review what changed and why
```

#### Step 4: Create Backup

```bash
# Backup current baseline
SEED=42
CANONICAL="exports/determinism-baselines/CANONICAL_${SEED}.checksums"
BACKUP="${CANONICAL}.backup-$(date +%Y%m%d-%H%M%S)"

cp "$CANONICAL" "$BACKUP"
echo "✅ Backup created: $BACKUP"
```

#### Step 5: Update Baseline

```bash
# Copy new checksums to canonical
cp "exports/${RUN_ID}/checksums.txt" \
   "exports/determinism-baselines/CANONICAL_${SEED}.checksums"
```

#### Step 6: Verify Integrity

```bash
# Verify baseline is not corrupted
bash scripts/validation/verify_baseline_integrity.sh ${SEED}

# Expected output: ✅ BASELINE INTEGRITY VERIFIED
```

#### Step 7: Commit with Override Token

```bash
git add exports/determinism-baselines/CANONICAL_${SEED}.checksums
git commit -m "[determinism-override] Update baseline for <reason>

Reason: <detailed explanation>
Changes: <what changed>
Verification: <how verified>
Run ID: ${RUN_ID}
Seed: ${SEED}
Backup: ${BACKUP}
"
```

#### Step 8: Create Pull Request

```bash
# Push to remote
git push origin HEAD

# Create PR (via GitHub UI or CLI)
gh pr create \
  --title "[Determinism] Update baseline - <reason>" \
  --body "See commit message for details. CI will verify automatically."
```

#### Step 9: Wait for CI Verification

The baseline verification CI (`.github/workflows/verify-baseline-update.yml`) will automatically:
- ✅ Verify run directory exists
- ✅ Check all notebooks passed
- ✅ Validate deterministic status
- ✅ Verify checksums match
- ✅ Check file format
- ✅ Post verification report as PR comment

#### Step 10: Manual Review & Merge

Reviewers must verify:
- Business logic changes are intentional
- No regressions introduced
- Documentation updated
- Reason is clear and justified

---

## Multi-Seed Management

### Supported Seeds

| Seed | Purpose | Data Scale | Update Frequency |
|------|---------|------------|------------------|
| **42** | Primary canonical | Standard (100 entities) | On changes |
| **123** | Secondary validation | Standard (100 entities) | With primary |
| **999** | Stress test | Large (1000 entities) | Monthly |

### Updating Non-Default Seeds

```bash
# Run with specific seed
DEMO_SEED=123 bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh

# Get run ID
RUN_ID=$(jq -r '.run_id' exports/deterministic-status.json)

# Verify quality
bash scripts/validation/verify_baseline_quality.sh "exports/${RUN_ID}"

# Update baseline for seed 123
cp "exports/${RUN_ID}/checksums.txt" \
   exports/determinism-baselines/CANONICAL_123.checksums

# Commit
git commit -m "[determinism-override] Update baseline for seed 123

Reason: <reason>
Seed: 123
Run ID: ${RUN_ID}
"
```

### Synchronizing Multiple Seeds

When updating primary baseline, also update secondary:

```bash
# Update seed 42 (primary)
DEMO_SEED=42 bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh
RUN_ID_42=$(jq -r '.run_id' exports/deterministic-status.json)
cp "exports/${RUN_ID_42}/checksums.txt" \
   exports/determinism-baselines/CANONICAL_42.checksums

# Update seed 123 (secondary)
DEMO_SEED=123 bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh
RUN_ID_123=$(jq -r '.run_id' exports/deterministic-status.json)
cp "exports/${RUN_ID_123}/checksums.txt" \
   exports/determinism-baselines/CANONICAL_123.checksums

# Commit both
git add exports/determinism-baselines/CANONICAL_*.checksums
git commit -m "[determinism-override] Update baselines for seeds 42 and 123

Reason: <reason>
Run IDs: ${RUN_ID_42}, ${RUN_ID_123}
"
```

---

## Corruption Detection

### Symptoms of Corruption

- Checksums file has wrong format
- Missing required files
- Checksums don't match actual files
- Invalid SHA-256 hashes
- Wrong line count

### Detection Script

```bash
# Run integrity check
bash scripts/validation/verify_baseline_integrity.sh 42

# Expected output: ✅ BASELINE INTEGRITY VERIFIED
```

### Manual Verification

```bash
SEED=42
BASELINE="exports/determinism-baselines/CANONICAL_${SEED}.checksums"

# Check 1: File exists
test -f "$BASELINE" && echo "✅ File exists" || echo "❌ File missing"

# Check 2: Line count (must be 5)
LINE_COUNT=$(wc -l < "$BASELINE")
[[ $LINE_COUNT -eq 5 ]] && echo "✅ Line count correct" || echo "❌ Wrong line count: $LINE_COUNT"

# Check 3: SHA-256 format
grep -qE '^[a-f0-9]{64}  [a-zA-Z0-9_.-]+$' "$BASELINE" && \
  echo "✅ Format valid" || echo "❌ Invalid format"

# Check 4: Required files
REQUIRED=(
  "notebook_run_report.tsv"
  "image_digests.txt"
  "dependency_fingerprint.txt"
  "runtime_package_fingerprint.txt"
  "deterministic_manifest.json"
)

for file in "${REQUIRED[@]}"; do
  grep -q "  ${file}$" "$BASELINE" && \
    echo "✅ $file" || echo "❌ Missing: $file"
done
```

### Recovery from Corruption

If baseline is corrupted:

```bash
# Option 1: Restore from backup
SEED=42
BACKUP=$(ls -t exports/determinism-baselines/CANONICAL_${SEED}.checksums.backup-* | head -1)
cp "$BACKUP" exports/determinism-baselines/CANONICAL_${SEED}.checksums
git add exports/determinism-baselines/CANONICAL_${SEED}.checksums
git commit -m "Restore baseline from backup: $(basename $BACKUP)"

# Option 2: Regenerate from valid run
# Run deterministic pipeline
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh
RUN_ID=$(jq -r '.run_id' exports/deterministic-status.json)

# Verify quality
bash scripts/validation/verify_baseline_quality.sh "exports/${RUN_ID}"

# Update baseline
cp "exports/${RUN_ID}/checksums.txt" \
   exports/determinism-baselines/CANONICAL_${SEED}.checksums
git add exports/determinism-baselines/CANONICAL_${SEED}.checksums
git commit -m "[determinism-override] Regenerate baseline after corruption

Reason: Baseline was corrupted, regenerated from run ${RUN_ID}
Run ID: ${RUN_ID}
Seed: ${SEED}
"
```

---

## Rollback Procedures

### Before Updating Baseline

Always test rollback procedure before updating:

```bash
# 1. Backup current baseline
cp exports/determinism-baselines/CANONICAL_42.checksums \
   exports/determinism-baselines/CANONICAL_42.checksums.backup-$(date +%Y%m%d-%H%M%S)

# 2. Test rollback procedure
BACKUP=$(ls -t exports/determinism-baselines/CANONICAL_42.checksums.backup-* | head -1)
cp "$BACKUP" exports/determinism-baselines/CANONICAL_42.checksums.test-rollback

# 3. Verify rollback works
bash scripts/testing/detect_determinism_drift.sh exports/demo-latest
# Should pass if using backup

# 4. Clean up test
rm exports/determinism-baselines/CANONICAL_42.checksums.test-rollback
```

### After Updating Baseline

If issues found after merge:

```bash
# Option 1: Revert the commit
git revert <commit-sha>
git push origin HEAD

# Option 2: Restore from backup
SEED=42
BACKUP=$(ls -t exports/determinism-baselines/CANONICAL_${SEED}.checksums.backup-* | head -1)
cp "$BACKUP" exports/determinism-baselines/CANONICAL_${SEED}.checksums
git add exports/determinism-baselines/CANONICAL_${SEED}.checksums
git commit -m "Rollback baseline update due to <reason>

Original commit: <commit-sha>
Reason: <detailed explanation>
Backup: $(basename $BACKUP)
"
git push origin HEAD
```

### Emergency Rollback

If baseline is causing critical issues:

```bash
# 1. Identify last known good baseline
git log --oneline exports/determinism-baselines/CANONICAL_42.checksums | head -5

# 2. Checkout specific version
git checkout <commit-sha> -- exports/determinism-baselines/CANONICAL_42.checksums

# 3. Commit emergency rollback
git commit -m "EMERGENCY: Rollback baseline to <commit-sha>

Reason: <critical issue description>
Impact: <what broke>
Action: Rolled back to last known good baseline
"

# 4. Push immediately
git push origin HEAD

# 5. Notify team
echo "⚠️ EMERGENCY BASELINE ROLLBACK - Check Slack/Email"
```

---

## Troubleshooting

### Issue: Baseline Update PR Fails CI

**Symptoms:**
- CI workflow fails with verification errors
- PR cannot be merged

**Diagnosis:**
```bash
# Check CI logs for specific failure
# Common failures:
# - Run directory not found
# - Notebooks failed
# - Deterministic status != 0
# - Checksums don't match
# - Missing [determinism-override] token
```

**Solution:**
```bash
# 1. Fix the underlying issue
# 2. Re-run deterministic pipeline
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh

# 3. Verify quality
RUN_ID=$(jq -r '.run_id' exports/deterministic-status.json)
bash scripts/validation/verify_baseline_quality.sh "exports/${RUN_ID}"

# 4. Update baseline again
cp "exports/${RUN_ID}/checksums.txt" \
   exports/determinism-baselines/CANONICAL_42.checksums

# 5. Amend commit or create new one
git add exports/determinism-baselines/CANONICAL_42.checksums
git commit --amend -m "[determinism-override] Update baseline for <reason>

Reason: <reason>
Run ID: ${RUN_ID}
Seed: 42
"
git push --force origin HEAD
```

### Issue: Drift Detected After Update

**Symptoms:**
- Deterministic pipeline fails with drift error
- Checksums don't match canonical baseline

**Diagnosis:**
```bash
# Check drift detection log
cat exports/demo-*/drift_detection.log

# Compare checksums
diff -u exports/determinism-baselines/CANONICAL_42.checksums \
        exports/demo-*/checksums.txt
```

**Solution:**
```bash
# If drift is expected (intentional change):
# 1. Update baseline following standard process

# If drift is unexpected (bug):
# 1. Investigate what changed
# 2. Fix the bug
# 3. Re-run pipeline
# 4. Verify no drift
```

### Issue: Baseline Corruption

**Symptoms:**
- Integrity check fails
- Invalid checksum format
- Missing required files

**Solution:**
```bash
# Restore from backup (see Recovery from Corruption section)
BACKUP=$(ls -t exports/determinism-baselines/CANONICAL_42.checksums.backup-* | head -1)
cp "$BACKUP" exports/determinism-baselines/CANONICAL_42.checksums
git add exports/determinism-baselines/CANONICAL_42.checksums
git commit -m "Restore baseline from backup: $(basename $BACKUP)"
```

---

## Related Documentation

- [AGENTS.md](../../AGENTS.md) - Agent rules and determinism contract
- [Operations Runbook](operations-runbook.md) - Day-to-day operations
- [Deterministic Pipeline](../../scripts/testing/run_demo_pipeline_repeatable.sh) - Pipeline implementation
- [Drift Detection](../../scripts/testing/detect_determinism_drift.sh) - Drift detection logic

---

**Last Updated:** 2026-04-06  
**Version:** 1.0  
**Maintainer:** Platform Engineering Team