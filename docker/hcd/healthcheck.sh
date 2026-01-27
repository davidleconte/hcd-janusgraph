#!/bin/bash
# File: docker/hcd/healthcheck.sh
# Created: 2026-01-28T10:33:30.345
# Author: David LECONTE, IBM WorldWide | Data & AI
#
# Health check for HCD container

set -e

# Check if nodetool works
if ! nodetool status | grep -q "UN"; then
    echo "❌ No UN (Up/Normal) nodes found"
    exit 1
fi

# Check if CQL is responsive
if ! cqlsh -e "SELECT now() FROM system.local" > /dev/null 2>&1; then
    echo "❌ CQL not responsive"
    exit 1
fi

echo "✅ HCD healthy"
exit 0

# Signature: David LECONTE, IBM WorldWide | Data & AI
