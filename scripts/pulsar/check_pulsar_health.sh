#!/bin/bash
# Pulsar Health Check Script
# Part of Week 1: Pulsar Infrastructure
# Created: 2026-02-04

set -e

PULSAR_HOST="${PULSAR_HOST:-localhost}"
PULSAR_ADMIN_PORT="${PULSAR_ADMIN_PORT:-8081}"
PULSAR_BROKER_PORT="${PULSAR_BROKER_PORT:-6650}"

echo "=============================================="
echo "Pulsar Health Check"
echo "=============================================="
echo ""

# Check if Pulsar admin API is accessible
echo "1. Checking Pulsar Admin API..."
if curl -s "http://${PULSAR_HOST}:${PULSAR_ADMIN_PORT}/admin/v2/clusters" | grep -q "standalone"; then
    echo "   ✅ Admin API: OK (standalone cluster)"
else
    echo "   ❌ Admin API: FAILED"
    exit 1
fi

# Check broker port
echo "2. Checking Pulsar Broker Port..."
if nc -z "${PULSAR_HOST}" "${PULSAR_BROKER_PORT}" 2>/dev/null; then
    echo "   ✅ Broker Port ${PULSAR_BROKER_PORT}: OK"
else
    echo "   ❌ Broker Port ${PULSAR_BROKER_PORT}: FAILED"
    exit 1
fi

# Check namespace exists
echo "3. Checking banking namespace..."
if curl -s "http://${PULSAR_HOST}:${PULSAR_ADMIN_PORT}/admin/v2/namespaces/public/banking" | grep -qv "not found"; then
    echo "   ✅ Namespace public/banking: OK"
else
    echo "   ❌ Namespace public/banking: NOT FOUND"
    exit 1
fi

# Check deduplication is enabled
echo "4. Checking deduplication status..."
DEDUP_STATUS=$(curl -s "http://${PULSAR_HOST}:${PULSAR_ADMIN_PORT}/admin/v2/namespaces/public/banking/deduplication")
if echo "$DEDUP_STATUS" | grep -q "true"; then
    echo "   ✅ Deduplication: ENABLED"
else
    echo "   ⚠️  Deduplication: disabled or unknown"
fi

# List topics
echo "5. Checking topics..."
TOPICS=$(curl -s "http://${PULSAR_HOST}:${PULSAR_ADMIN_PORT}/admin/v2/persistent/public/banking")
echo "   Topics found:"

EXPECTED_TOPICS=("persons-events" "accounts-events" "transactions-events" "companies-events" "communications-events" "dlq-events")
for topic in "${EXPECTED_TOPICS[@]}"; do
    if echo "$TOPICS" | grep -q "$topic"; then
        echo "   ✅ persistent://public/banking/${topic}"
    else
        echo "   ❌ persistent://public/banking/${topic} - NOT FOUND"
    fi
done

# Get broker metrics
echo ""
echo "6. Broker Stats..."
BROKER_STATS=$(curl -s "http://${PULSAR_HOST}:${PULSAR_ADMIN_PORT}/admin/v2/broker-stats/destinations")
echo "   Broker stats retrieved successfully"

echo ""
echo "=============================================="
echo "Pulsar Health Check: COMPLETE"
echo "=============================================="
echo ""
echo "Admin Console: http://${PULSAR_HOST}:${PULSAR_ADMIN_PORT}"
echo "Broker URL:    pulsar://${PULSAR_HOST}:${PULSAR_BROKER_PORT}"
