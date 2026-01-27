#!/bin/bash
# File: scripts/maintenance/cleanup_logs.sh
# Created: 2026-01-28T10:32:16.678
# Author: David LECONTE, IBM WorldWide | Data & AI
#
# Cleanup old logs and temporary files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🧹 Cleaning up logs and temporary files..."

# Remove old container logs (older than 7 days)
echo "Cleaning container logs..."
find ~/.local/share/containers/storage/overlay-containers -name "*.log" -mtime +7 -delete 2>/dev/null || true

# Remove Python cache
echo "Cleaning Python cache..."
find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true

# Remove Jupyter checkpoints
echo "Cleaning Jupyter checkpoints..."
find "$PROJECT_ROOT/notebooks" -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true

# Remove old exports (older than 30 days)
echo "Cleaning old exports..."
find "$PROJECT_ROOT/data/exports" -type f -mtime +30 -delete 2>/dev/null || true

# Remove temporary test results
rm -f "$PROJECT_ROOT/tests/TEST_RESULTS.md" 2>/dev/null || true

echo "✅ Cleanup complete"

# Signature: David LECONTE, IBM WorldWide | Data & AI
