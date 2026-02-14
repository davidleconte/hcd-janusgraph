#!/bin/bash
# Clear Notebook Outputs
# Removes execution outputs from Jupyter notebooks to prevent hardcoded paths from being committed.
#
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
# Date: 2026-02-06

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check if jupyter is available
if ! command -v jupyter &> /dev/null; then
    echo "⚠️  jupyter not found. Install with: pip install jupyter"
    echo "   Or use: conda activate janusgraph-analysis"
    exit 1
fi

echo "🧹 Clearing notebook outputs..."
echo "   Project root: $PROJECT_ROOT"

# Counter for processed notebooks
count=0

# Process banking notebooks
for notebook in "$PROJECT_ROOT"/banking/notebooks/*.ipynb; do
    if [[ -f "$notebook" ]]; then
        echo "   Clearing: $(basename "$notebook")"
        jupyter nbconvert --clear-output --inplace "$notebook" 2>/dev/null || true
        ((count++))
    fi
done

# Process exploratory notebooks
for notebook in "$PROJECT_ROOT"/notebooks-exploratory/*.ipynb; do
    if [[ -f "$notebook" ]]; then
        echo "   Clearing: $(basename "$notebook")"
        jupyter nbconvert --clear-output --inplace "$notebook" 2>/dev/null || true
        ((count++))
    fi
done

echo ""
echo "✅ Cleared outputs from $count notebooks"
echo ""
echo "💡 Tip: Run this before committing to avoid hardcoded paths in outputs"
