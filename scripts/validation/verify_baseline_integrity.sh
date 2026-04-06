#!/usr/bin/env bash
#
# Verify Baseline Integrity
# =========================
#
# Checks that a canonical baseline file is not corrupted.
#
# Usage:
#   bash scripts/validation/verify_baseline_integrity.sh [seed]
#
# Example:
#   bash scripts/validation/verify_baseline_integrity.sh 42
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

SEED="${1:-42}"
BASELINE="${PROJECT_ROOT}/exports/determinism-baselines/CANONICAL_${SEED}.checksums"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "🔍 Verifying baseline integrity: CANONICAL_${SEED}.checksums"
echo ""

FAILURES=0

# Check 1: File exists
if [[ ! -f "$BASELINE" ]]; then
    echo -e "${RED}❌ FAIL: Baseline file not found: ${BASELINE}${NC}"
    exit 1
fi
echo -e "${GREEN}✅ File exists${NC}"

# Check 2: Line count (must be exactly 5)
LINE_COUNT=$(wc -l < "$BASELINE")
if [[ $LINE_COUNT -ne 5 ]]; then
    echo -e "${RED}❌ FAIL: Baseline has ${LINE_COUNT} lines, expected 5${NC}"
    ((FAILURES++))
else
    echo -e "${GREEN}✅ Line count correct (5 lines)${NC}"
fi

# Check 3: SHA-256 format
if ! grep -qE '^[a-f0-9]{64}  [a-zA-Z0-9_.-]+$' "$BASELINE"; then
    echo -e "${RED}❌ FAIL: Invalid checksum format${NC}"
    echo ""
    echo "Expected format: <64-hex-chars>  <filename>"
    echo "Actual content:"
    cat "$BASELINE"
    ((FAILURES++))
else
    echo -e "${GREEN}✅ Checksum format valid${NC}"
fi

# Check 4: Required files
REQUIRED_FILES=(
    "notebook_run_report.tsv"
    "image_digests.txt"
    "dependency_fingerprint.txt"
    "runtime_package_fingerprint.txt"
    "deterministic_manifest.json"
)

echo ""
echo "Checking required files..."
MISSING=0
while IFS= read -r line; do
    FILENAME=$(echo "$line" | awk '{print $2}')
    if [[ ! " ${REQUIRED_FILES[@]} " =~ " ${FILENAME} " ]]; then
        echo -e "${RED}  ❌ Unexpected file: ${FILENAME}${NC}"
        ((MISSING++))
    else
        echo -e "${GREEN}  ✅ ${FILENAME}${NC}"
    fi
done < "$BASELINE"

for required in "${REQUIRED_FILES[@]}"; do
    if ! grep -q "  ${required}$" "$BASELINE"; then
        echo -e "${RED}  ❌ Missing: ${required}${NC}"
        ((MISSING++))
    fi
done

if [[ $MISSING -gt 0 ]]; then
    ((FAILURES++))
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $FAILURES -eq 0 ]]; then
    echo -e "${GREEN}✅ BASELINE INTEGRITY VERIFIED${NC}"
    exit 0
else
    echo -e "${RED}❌ BASELINE INTEGRITY CHECK FAILED${NC}"
    echo ""
    echo "The baseline file is corrupted or invalid."
    echo "Restore from backup or regenerate from a valid run."
    exit 1
fi

# Made with Bob
