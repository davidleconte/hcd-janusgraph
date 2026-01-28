#!/bin/bash
# File: scripts/backup/restore_volumes.sh
# Created: 2026-01-28T10:32:15.345
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
#
# Restore HCD and JanusGraph volumes from backup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/.env" || source "$PROJECT_ROOT/.env.example"

BACKUP_PATH="$1"

if [ -z "$BACKUP_PATH" ] || [ ! -d "$BACKUP_PATH" ]; then
    echo "❌ Usage: $0 <backup_path>"
    echo "   Example: $0 /backups/janusgraph/hcd_20260128_103000"
    exit 1
fi

echo "⚠️  WARNING: This will OVERWRITE current data!"
echo "   Backup path: $BACKUP_PATH"
read -p "Type 'yes' to continue: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Stop services
echo "🛑 Stopping services..."
bash "$PROJECT_ROOT/scripts/deployment/stop_full_stack.sh"

# Restore HCD data
echo "📦 Restoring HCD data..."
${PODMAN_CONNECTION} cp "$BACKUP_PATH/hcd" hcd-server:/var/lib/cassandra/data

# Restore JanusGraph data
if [ -f "$BACKUP_PATH/janusgraph.tar.gz" ]; then
    echo "📦 Restoring JanusGraph data..."
    ${PODMAN_CONNECTION} cp "$BACKUP_PATH/janusgraph.tar.gz" janusgraph-server:/tmp/
    ${PODMAN_CONNECTION} exec janusgraph-server tar -xzf /tmp/janusgraph.tar.gz -C /
fi

# Start services
echo "🚀 Starting services..."
bash "$PROJECT_ROOT/scripts/deployment/deploy_full_stack.sh"

# Verify
echo "⏳ Waiting for startup (60s)..."
sleep 60

echo "🧪 Running smoke tests..."
bash "$PROJECT_ROOT/scripts/testing/run_tests.sh" || echo "⚠️  Some tests failed"

echo "✅ Restore completed"
echo ""
echo "Next steps:"
echo "  1. Verify data integrity"
echo "  2. Check application logs"
echo "  3. Run full test suite"

# Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
