#!/bin/bash
# File: scripts/backup/backup_volumes.sh
# Created: 2026-01-28T10:32:15.123
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
#
# Backup HCD and JanusGraph volumes

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

BACKUP_DIR="${BACKUP_DIR:-/backups/janusgraph}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "📦 Starting backup at $TIMESTAMP"

# 1. Backup HCD data
echo "Backing up HCD..."
podman_exec hcd-server nodetool snapshot janusgraph
podman_cp hcd-server:/var/lib/cassandra/data "$BACKUP_DIR/hcd_$TIMESTAMP"

# 2. Backup JanusGraph data
echo "Backing up JanusGraph..."
podman_exec janusgraph-server tar -czf /tmp/jg_backup.tar.gz /var/lib/janusgraph 2>/dev/null || true
podman_cp janusgraph-server:/tmp/jg_backup.tar.gz "$BACKUP_DIR/janusgraph_$TIMESTAMP.tar.gz"

# 3. Export graph to GraphML
echo "Exporting graph..."
python3 "$SCRIPT_DIR/export_graph.py" --output "$BACKUP_DIR/graph_$TIMESTAMP.graphml" || echo "⚠️  Graph export failed (non-critical)"

# 4. Cleanup old backups
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

# 5. Upload to S3 (optional)
if [ -n "${AWS_S3_BACKUP_BUCKET:-}" ]; then
    echo "Uploading to S3..."
    aws s3 sync "$BACKUP_DIR" "s3://$AWS_S3_BACKUP_BUCKET/janusgraph/" \
        --storage-class STANDARD_IA
fi

echo "✅ Backup completed: $BACKUP_DIR"
echo "   HCD: hcd_$TIMESTAMP"
echo "   JanusGraph: janusgraph_$TIMESTAMP.tar.gz"
echo "   Graph: graph_$TIMESTAMP.graphml"

# Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
