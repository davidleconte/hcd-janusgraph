#!/bin/bash
# HCD Health Check Script
# File: health_check.sh
# Purpose: Monitor HCD/Cassandra cluster health for JanusGraph
# Author: David LECONTE - IBM Worldwide
# Date: 2026-01-29

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
HCD_HOST="${HCD_HOST:-localhost}"
HCD_PORT="${HCD_PORT:-19042}"
CONTAINER_NAME="${CONTAINER_NAME:-janusgraph-demo_hcd-server_1}"
KEYSPACE="${KEYSPACE:-janusgraph}"

# Check if running in container or host
if [ -f /.dockerenv ]; then
    IN_CONTAINER=true
    NODETOOL="nodetool"
    CQLSH="cqlsh"
else
    IN_CONTAINER=false
    NODETOOL="podman exec $CONTAINER_NAME nodetool"
    CQLSH="podman exec -i $CONTAINER_NAME cqlsh"
fi

echo "========================================"
echo "HCD Health Check"
echo "========================================"
echo "Host: $HCD_HOST:$HCD_PORT"
echo "Keyspace: $KEYSPACE"
echo "Container: $CONTAINER_NAME"
echo ""

# Function to print status
print_status() {
    local status=$1
    local message=$2

    if [ "$status" == "ok" ]; then
        echo -e "${GREEN}✅${NC} $message"
    elif [ "$status" == "warning" ]; then
        echo -e "${YELLOW}⚠️${NC} $message"
    else
        echo -e "${RED}❌${NC} $message"
    fi
}

# Check 1: Container running (if not in container)
if [ "$IN_CONTAINER" = false ]; then
    echo "1. Checking container status..."
    if podman ps --filter "name=$CONTAINER_NAME" --filter "status=running" | grep -q "$CONTAINER_NAME"; then
        print_status "ok" "Container is running"
    else
        print_status "error" "Container is not running"
        echo "   Start with: podman start $CONTAINER_NAME"
        exit 1
    fi
fi

# Check 2: Nodetool status
echo ""
echo "2. Checking cluster status..."
if $NODETOOL status > /dev/null 2>&1; then
    print_status "ok" "Nodetool accessible"

    # Get status output
    STATUS_OUTPUT=$($NODETOOL status)

    # Check for UN (Up Normal) nodes
    UN_COUNT=$(echo "$STATUS_OUTPUT" | grep -c "^UN" || true)
    DN_COUNT=$(echo "$STATUS_OUTPUT" | grep -c "^DN" || true)

    echo "   Nodes UP: $UN_COUNT"
    if [ $DN_COUNT -gt 0 ]; then
        print_status "error" "Nodes DOWN: $DN_COUNT"
        echo "$STATUS_OUTPUT"
    else
        print_status "ok" "All nodes operational"
    fi
else
    print_status "error" "Cannot connect to nodetool"
    exit 1
fi

# Check 3: CQL connection
echo ""
echo "3. Checking CQL connectivity..."
if echo "DESCRIBE KEYSPACES;" | $CQLSH $HCD_HOST $HCD_PORT > /dev/null 2>&1; then
    print_status "ok" "CQL connection successful"
else
    print_status "error" "Cannot connect via CQL"
    exit 1
fi

# Check 4: Keyspace exists
echo ""
echo "4. Checking keyspace: $KEYSPACE..."
if echo "DESCRIBE KEYSPACE $KEYSPACE;" | $CQLSH $HCD_HOST $HCD_PORT > /dev/null 2>&1; then
    print_status "ok" "Keyspace exists"

    # Get replication info
    REPLICATION=$(echo "SELECT replication FROM system_schema.keyspaces WHERE keyspace_name='$KEYSPACE';" | $CQLSH $HCD_HOST $HCD_PORT -e "EXPAND ON" 2>/dev/null | grep -A5 "replication" | tail -1 || true)
    if [ -n "$REPLICATION" ]; then
        echo "   Replication: $REPLICATION"
    fi
else
    print_status "warning" "Keyspace does not exist (will be created by JanusGraph)"
fi

# Check 5: JanusGraph tables
echo ""
echo "5. Checking JanusGraph tables..."
TABLE_COUNT=$(echo "SELECT COUNT(*) FROM system_schema.tables WHERE keyspace_name='$KEYSPACE';" | $CQLSH $HCD_HOST $HCD_PORT 2>/dev/null | grep -oP '\d+' | head -1 || echo "0")

if [ "$TABLE_COUNT" -gt 0 ]; then
    print_status "ok" "Found $TABLE_COUNT tables in $KEYSPACE"

    # Check for critical JanusGraph tables
    CRITICAL_TABLES=("edgestore" "graphindex" "janusgraph_ids" "system_properties")
    for table in "${CRITICAL_TABLES[@]}"; do
        if echo "DESCRIBE TABLE $KEYSPACE.$table;" | $CQLSH $HCD_HOST $HCD_PORT > /dev/null 2>&1; then
            echo "   ✓ $table"
        else
            echo "   ✗ $table (missing)"
        fi
    done
else
    print_status "warning" "No tables found (JanusGraph not initialized)"
fi

# Check 6: Disk usage
echo ""
echo "6. Checking disk usage..."
DISK_OUTPUT=$($NODETOOL tablestats $KEYSPACE 2>/dev/null || echo "")

if [ -n "$DISK_OUTPUT" ]; then
    # Extract total space used
    TOTAL_SPACE=$(echo "$DISK_OUTPUT" | grep "Total disk space used:" | awk '{print $5" "$6}')
    if [ -n "$TOTAL_SPACE" ]; then
        print_status "ok" "Disk usage: $TOTAL_SPACE"
    fi

    # Extract total SSTable count
    SSTABLE_COUNT=$(echo "$DISK_OUTPUT" | grep "Total number of SSTables:" | awk '{print $5}')
    if [ -n "$SSTABLE_COUNT" ]; then
        echo "   SSTables: $SSTABLE_COUNT"
    fi
else
    print_status "warning" "Cannot retrieve disk statistics"
fi

# Check 7: Compaction status
echo ""
echo "7. Checking compaction status..."
COMPACTION_OUTPUT=$($NODETOOL compactionstats 2>/dev/null || echo "")

if [ -n "$COMPACTION_OUTPUT" ]; then
    PENDING=$(echo "$COMPACTION_OUTPUT" | grep "pending tasks:" | awk '{print $3}')
    if [ -n "$PENDING" ]; then
        if [ "$PENDING" -eq 0 ]; then
            print_status "ok" "No pending compactions"
        else
            print_status "warning" "Pending compactions: $PENDING"
        fi
    fi
else
    print_status "warning" "Cannot retrieve compaction stats"
fi

# Check 8: Gossip info
echo ""
echo "8. Checking gossip protocol..."
if $NODETOOL gossipinfo > /dev/null 2>&1; then
    print_status "ok" "Gossip protocol active"
else
    print_status "warning" "Gossip protocol issues detected"
fi

# Check 9: Memory usage
echo ""
echo "9. Checking memory usage..."
INFO_OUTPUT=$($NODETOOL info 2>/dev/null || echo "")

if [ -n "$INFO_OUTPUT" ]; then
    HEAP_USED=$(echo "$INFO_OUTPUT" | grep "Heap Memory (MB)" | awk '{print $5}')
    HEAP_MAX=$(echo "$INFO_OUTPUT" | grep "Heap Memory (MB)" | awk '{print $7}')

    if [ -n "$HEAP_USED" ] && [ -n "$HEAP_MAX" ]; then
        HEAP_PCT=$(awk "BEGIN {printf \"%.1f\", ($HEAP_USED/$HEAP_MAX)*100}")
        echo "   Heap: ${HEAP_USED}MB / ${HEAP_MAX}MB (${HEAP_PCT}%)"

        if (( $(echo "$HEAP_PCT > 90" | bc -l) )); then
            print_status "error" "High memory usage (>90%)"
        elif (( $(echo "$HEAP_PCT > 75" | bc -l) )); then
            print_status "warning" "Elevated memory usage (>75%)"
        else
            print_status "ok" "Memory usage normal"
        fi
    fi
fi

# Summary
echo ""
echo "========================================"
echo "Health Check Complete"
echo "========================================"
echo ""

# Exit code
# 0 = all checks passed
# 1 = critical errors
# 2 = warnings only

if grep -q "❌" <<< "$OUTPUT"; then
    echo "Status: CRITICAL - Immediate action required"
    exit 1
elif grep -q "⚠️" <<< "$OUTPUT"; then
    echo "Status: WARNING - Review recommended"
    exit 2
else
    echo "Status: HEALTHY - All systems operational"
    exit 0
fi
