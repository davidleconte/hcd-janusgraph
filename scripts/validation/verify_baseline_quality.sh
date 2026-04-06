#!/usr/bin/env bash
#
# Verify Baseline Quality
# =======================
#
# Validates that a deterministic run is suitable for promotion to canonical baseline.
#
# Usage:
#   bash scripts/validation/verify_baseline_quality.sh <run-directory>
#
# Example:
#   bash scripts/validation/verify_baseline_quality.sh exports/demo-20260406T120000Z
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Usage
usage() {
    cat <<EOF
Usage: $(basename "$0") <run-directory>

Verify that a deterministic run is suitable for baseline promotion.

Arguments:
  run-directory    Path to run directory (e.g., exports/demo-20260406T120000Z)

Example:
  $(basename "$0") exports/demo-20260406T120000Z

Exit Codes:
  0 - All checks passed
  1 - One or more checks failed
EOF
}

# Check arguments
if [[ $# -ne 1 ]]; then
    usage
    exit 1
fi

RUN_DIR="$1"

# Validate run directory exists
if [[ ! -d "$RUN_DIR" ]]; then
    echo -e "${RED}❌ ERROR: Run directory not found: ${RUN_DIR}${NC}"
    exit 1
fi

echo "🔍 Verifying baseline quality for: ${RUN_DIR}"
echo ""

# Track failures
FAILURES=0

# Check 1: Notebook report exists
echo "📝 Checking notebook report..."
REPORT="${RUN_DIR}/notebook_run_report.tsv"
if [[ ! -f "$REPORT" ]]; then
    echo -e "${RED}❌ FAIL: Notebook report not found${NC}"
    ((FAILURES++))
else
    # Check all notebooks passed
    FAILED_NOTEBOOKS=$(awk -F'\t' '$2 != "PASS" && NR>1 {count++} END {print count+0}' "$REPORT")
    TOTAL_NOTEBOOKS=$(awk 'END {print NR-1}' "$REPORT")
    
    if [[ $FAILED_NOTEBOOKS -gt 0 ]]; then
        echo -e "${RED}❌ FAIL: ${FAILED_NOTEBOOKS}/${TOTAL_NOTEBOOKS} notebooks failed${NC}"
        echo ""
        echo "Failed notebooks:"
        awk -F'\t' '$2 != "PASS" && NR>1 {print "  - " $1 ": " $2}' "$REPORT"
        ((FAILURES++))
    else
        echo -e "${GREEN}✅ PASS: All ${TOTAL_NOTEBOOKS} notebooks passed${NC}"
    fi
fi
echo ""

# Check 2: Deterministic status
echo "🎯 Checking deterministic status..."
STATUS="${RUN_DIR}/deterministic-status.json"
if [[ ! -f "$STATUS" ]]; then
    echo -e "${RED}❌ FAIL: Status file not found${NC}"
    ((FAILURES++))
else
    EXIT_CODE=$(jq -r '.exit_code // 1' "$STATUS" 2>/dev/null || echo "1")
    
    if [[ "$EXIT_CODE" != "0" ]]; then
        echo -e "${RED}❌ FAIL: Pipeline exit code = ${EXIT_CODE}${NC}"
        echo ""
        echo "Status details:"
        jq '.' "$STATUS" 2>/dev/null || cat "$STATUS"
        ((FAILURES++))
    else
        RUN_TIMESTAMP=$(jq -r '.run_timestamp // "unknown"' "$STATUS" 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✅ PASS: Pipeline succeeded (exit_code=0)${NC}"
        echo "   Timestamp: ${RUN_TIMESTAMP}"
    fi
fi
echo ""

# Check 3: Checksums file
echo "🔐 Checking checksums file..."
CHECKSUMS="${RUN_DIR}/checksums.txt"
if [[ ! -f "$CHECKSUMS" ]]; then
    echo -e "${RED}❌ FAIL: Checksums file not found${NC}"
    ((FAILURES++))
else
    # Verify format
    LINE_COUNT=$(wc -l < "$CHECKSUMS")
    if [[ $LINE_COUNT -ne 5 ]]; then
        echo -e "${RED}❌ FAIL: Checksums has ${LINE_COUNT} lines, expected 5${NC}"
        ((FAILURES++))
    elif ! grep -qE '^[a-f0-9]{64}  [a-zA-Z0-9_.-]+$' "$CHECKSUMS"; then
        echo -e "${RED}❌ FAIL: Invalid checksum format${NC}"
        ((FAILURES++))
    else
        echo -e "${GREEN}✅ PASS: Checksums file valid (5 lines, correct format)${NC}"
    fi
fi
echo ""

# Check 4: Required artifacts
echo "📦 Checking required artifacts..."
REQUIRED_FILES=(
    "notebook_run_report.tsv"
    "deterministic-status.json"
    "checksums.txt"
    "image_digests.txt"
    "dependency_fingerprint.txt"
    "runtime_package_fingerprint.txt"
    "deterministic_manifest.json"
)

MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "${RUN_DIR}/${file}" ]]; then
        echo -e "${RED}  ❌ Missing: ${file}${NC}"
        ((MISSING_FILES++))
    fi
done

if [[ $MISSING_FILES -gt 0 ]]; then
    echo -e "${RED}❌ FAIL: ${MISSING_FILES} required files missing${NC}"
    ((FAILURES++))
else
    echo -e "${GREEN}✅ PASS: All required artifacts present${NC}"
fi
echo ""

# Check 5: No error cells in notebooks (warning only)
echo "🔬 Checking for error cells in notebooks..."
ERROR_CELLS=0
if command -v python3 &> /dev/null; then
    shopt -s nullglob
    for notebook in "${RUN_DIR}"/*.ipynb; do
        if [[ -f "$notebook" ]]; then
            ERRORS=$(python3 -c "
import json, sys
try:
    with open('$notebook') as f:
        nb = json.load(f)
    errors = sum(1 for cell in nb.get('cells', []) 
                 if cell.get('cell_type') == 'code' 
                 and any('error' in str(output).lower() 
                        for output in cell.get('outputs', [])))
    print(errors)
except:
    print(0)
" 2>/dev/null || echo 0)
            
            if [[ $ERRORS -gt 0 ]]; then
                echo -e "${YELLOW}  ⚠️  Warning: $(basename "$notebook") has ${ERRORS} error cells${NC}"
                ((ERROR_CELLS += ERRORS))
            fi
        fi
    done
    
    if [[ $ERROR_CELLS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  WARNING: Found ${ERROR_CELLS} error cells across notebooks${NC}"
        echo "   (This is a warning, not a failure)"
    else
        echo -e "${GREEN}✅ PASS: No error cells found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  SKIP: Python not available for error cell check${NC}"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $FAILURES -eq 0 ]]; then
    echo -e "${GREEN}✅ VERIFICATION PASSED${NC}"
    echo ""
    echo "This run is suitable for promotion to canonical baseline."
    echo ""
    echo "Next steps:"
    echo "  1. Copy checksums to canonical:"
    echo "     cp ${RUN_DIR}/checksums.txt exports/determinism-baselines/CANONICAL_42.checksums"
    echo ""
    echo "  2. Commit with override token:"
    echo "     git commit -m \"[determinism-override] Update baseline for <reason>\""
    echo ""
    exit 0
else
    echo -e "${RED}❌ VERIFICATION FAILED${NC}"
    echo ""
    echo "Found ${FAILURES} critical issues."
    echo "This run is NOT suitable for baseline promotion."
    echo ""
    echo "Fix the issues and run the deterministic pipeline again."
    exit 1
fi

# Made with Bob
