#!/usr/bin/env bash
# =============================================================================
# Determinism Drift Detection
# =============================================================================
# Compares current run checksums against canonical baseline.
# Exit 0 = no drift, Exit 1 = drift detected
#
# Usage:
#   ./detect_determinism_drift.sh <output-dir>
#   ./detect_determinism_drift.sh exports/demo-20260313T124824Z
# =============================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CANONICAL_BASELINE="${PROJECT_ROOT}/exports/determinism-baselines/CANONICAL_42.checksums"

OUT_DIR="${1:-}"
if [[ -z "${OUT_DIR}" ]]; then
    echo "Usage: detect_determinism_drift.sh <output-dir>"
    exit 1
fi

CHECKSUM_FILE="${OUT_DIR}/checksums.txt"

if [[ ! -f "${CHECKSUM_FILE}" ]]; then
    echo "❌ Checksum file not found: ${CHECKSUM_FILE}"
    exit 1
fi

if [[ ! -f "${CANONICAL_BASELINE}" ]]; then
    echo "❌ Canonical baseline not found: ${CANONICAL_BASELINE}"
    echo "   See exports/determinism-baselines/CANONICAL_BASELINE.md"
    exit 1
fi

echo "🔍 Checking for determinism drift..."
echo "   Current: ${CHECKSUM_FILE}"
echo "   Canonical: ${CANONICAL_BASELINE}"

if cmp -s "${CHECKSUM_FILE}" "${CANONICAL_BASELINE}"; then
    echo "✅ No drift detected - checksums match canonical baseline"
    exit 0
fi

echo ""
echo "❌ DETERMINISM DRIFT DETECTED!"
echo ""
echo "Diff:"
diff -u "${CANONICAL_BASELINE}" "${CHECKSUM_FILE}" || true
echo ""
echo "Possible causes:"
echo "  1. Non-deterministic code (timestamps, random seeds, etc.)"
echo "  2. Dependency version changes"
echo "  3. Container image updates"
echo "  4. Notebook output changes"
echo ""
echo "If this is intentional, update the canonical baseline with:"
echo "  cp ${CHECKSUM_FILE} ${CANONICAL_BASELINE}"
echo ""
echo "And commit with: [determinism-override] token"
exit 1
