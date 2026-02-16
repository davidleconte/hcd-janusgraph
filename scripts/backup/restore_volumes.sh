#!/bin/bash
# File: scripts/backup/restore_volumes.sh
# Created: 2026-01-28T10:32:15.345
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
#
# Restore HCD and JanusGraph volumes from backup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/scripts/utils/podman_connection.sh"
source "$PROJECT_ROOT/.env" || source "$PROJECT_ROOT/.env.example"
PODMAN_CONNECTION="${PODMAN_CONNECTION:-}"
PODMAN_CONNECTION="$(resolve_podman_connection "${PODMAN_CONNECTION}")"

podman_exec() {
    podman --remote --connection "$PODMAN_CONNECTION" exec "$@"
}

podman_cp() {
    podman --remote --connection "$PODMAN_CONNECTION" cp "$@"
}

BACKUP_DIR="${1:-}"

if [ -z "$BACKUP_DIR" ]; then
    echo "❌ Usage: $0 <backup_directory> <timestamp>"
    echo "   Example: $0 /backups/janusgraph 20260128_103000"
    echo ""
    echo "Available backups:"
    ls -lh /backups/janusgraph/ 2>/dev/null | grep -E "hcd_|janusgraph_" || echo "  No backups found"
    exit 1
fi

TIMESTAMP="${2:-}"
if [ -z "$TIMESTAMP" ]; then
    echo "❌ Timestamp required"
    echo "   Example: $0 /backups/janusgraph 20260128_103000"
    exit 1
fi

HCD_BACKUP="$BACKUP_DIR/hcd_$TIMESTAMP"
JG_BACKUP="$BACKUP_DIR/janusgraph_$TIMESTAMP.tar.gz"

if [ ! -d "$HCD_BACKUP" ]; then
    echo "❌ HCD backup not found: $HCD_BACKUP"
    exit 1
fi

if [ ! -f "$JG_BACKUP" ]; then
    echo "❌ JanusGraph backup not found: $JG_BACKUP"
    exit 1
fi

echo "⚠️  WARNING: This will OVERWRITE current data!"
echo "   HCD backup: $HCD_BACKUP"
echo "   JanusGraph backup: $JG_BACKUP"
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
podman_cp "$HCD_BACKUP" hcd-server:/var/lib/cassandra/data

# Restore JanusGraph data
echo "📦 Restoring JanusGraph data..."
podman_cp "$JG_BACKUP" janusgraph-server:/tmp/janusgraph_restore.tar.gz
podman_exec janusgraph-server tar -xzf /tmp/janusgraph_restore.tar.gz -C /
podman_exec janusgraph-server rm /tmp/janusgraph_restore.tar.gz

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
