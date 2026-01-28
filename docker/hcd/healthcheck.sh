#!/bin/bash
# File: docker/hcd/healthcheck.sh
# Created: 2026-01-28T10:33:30.345
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
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

# Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
