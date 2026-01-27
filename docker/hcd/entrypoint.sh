#!/bin/bash
# File: docker/hcd/entrypoint.sh
# Created: 2026-01-28T10:33:30.567
# Author: David LECONTE, IBM WorldWide | Data & AI
#
# Entrypoint with graceful shutdown handling

set -e

# Graceful shutdown handler
shutdown_handler() {
    echo "🛑 Received shutdown signal, draining connections..."
    nodetool drain || true
    echo "✅ Graceful shutdown complete"
    exit 0
}

# Trap SIGTERM
trap shutdown_handler SIGTERM

# Start HCD in background
exec /opt/hcd-1.2.3/bin/hcd -f &

# Wait for signals
wait $!

# Signature: David LECONTE, IBM WorldWide | Data & AI
