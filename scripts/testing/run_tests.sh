#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/.env" || source "$PROJECT_ROOT/.env.example"
# HCD + JanusGraph Automated Test Suite

set +e  # Continue on error
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables if .env exists
if [ -f ".env" ]; then
    source .env
fi

# Set defaults
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"

RESULTS="$SCRIPT_DIR/TEST_RESULTS.md"

echo "# HCD + JanusGraph Test Results" > "$RESULTS"
echo "" >> "$RESULTS"
echo "**Date**: $(date)" >> "$RESULTS"
echo "" >> "$RESULTS"
echo "---" >> "$RESULTS"
echo "" >> "$RESULTS"

PASS=0
FAIL=0

log_test() {
    echo ""
    echo "## $1"
    echo "" >> "$RESULTS"
    echo "## $1" >> "$RESULTS"
    echo "" >> "$RESULTS"
}

log_pass() {
    echo "✅ $1"
    echo "✅ **PASSED**: $1" >> "$RESULTS"
    echo "" >> "$RESULTS"
    ((PASS++))
}

log_fail() {
    echo "❌ $1"
    echo "❌ **FAILED**: $1" >> "$RESULTS"
    echo "" >> "$RESULTS"
    ((FAIL++))
}

echo "Starting tests..."

# Test 1: Container Status
log_test "Test 1: Container Status"
if podman --remote --connection $PODMAN_CONNECTION ps | grep -q "hcd-server"; then
    log_pass "HCD container running"
else
    log_fail "HCD container not running"
fi

if podman --remote --connection $PODMAN_CONNECTION ps | grep -q "janusgraph-server"; then
    log_pass "JanusGraph container running"
else
    log_fail "JanusGraph container not running"
fi

# Test 2: HCD Status
log_test "Test 2: HCD Database"
if podman --remote --connection $PODMAN_CONNECTION exec hcd-server /opt/hcd/bin/nodetool status 2>/dev/null | grep -q "UN"; then
    log_pass "HCD cluster healthy (UN status)"
else
    log_fail "HCD cluster unhealthy"
fi

if podman --remote --connection $PODMAN_CONNECTION exec hcd-server /opt/hcd/bin/cqlsh -e "DESCRIBE KEYSPACES;" 2>/dev/null | grep -q "janusgraph"; then
    log_pass "JanusGraph keyspace exists"
else
    log_fail "JanusGraph keyspace missing"
fi

# Test 3: Initialize Schema and Data
log_test "Test 3: Schema and Data Initialization"

# Copy scripts from new location (src/groovy/)
cd "$PROJECT_ROOT"
podman --remote --connection $PODMAN_CONNECTION cp src/groovy/init_schema_remote.groovy janusgraph-server:/tmp/ 2>&1
podman --remote --connection $PODMAN_CONNECTION cp src/groovy/load_data_remote.groovy janusgraph-server:/tmp/ 2>&1

# Check current vertex count
VCOUNT=$(podman --remote --connection $PODMAN_CONNECTION exec janusgraph-server ./bin/gremlin.sh 2>&1 << 'EOF' | grep "^==>" | tail -1 | sed 's/^==>//'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().count()
EOF
)

echo "Current vertices: $VCOUNT"
echo "Current vertices: $VCOUNT" >> "$RESULTS"
echo "" >> "$RESULTS"

if [ "$VCOUNT" = "0" ] || [ -z "$VCOUNT" ]; then
    echo "Initializing schema..."
    SCHEMA_OUT=$(podman --remote --connection $PODMAN_CONNECTION exec janusgraph-server ./bin/gremlin.sh -e /tmp/init_schema_remote.groovy 2>&1)
    
    
    if echo "$SCHEMA_OUT" | grep -q "Schema committed"; then
        log_pass "Schema initialized"
    else
        log_fail "Schema initialization failed"
        echo "Error: $SCHEMA_OUT" | tail -20 >> "$RESULTS"
    fi
    
    echo "Loading data..."
    DATA_OUT=$(podman --remote --connection $PODMAN_CONNECTION exec janusgraph-server ./bin/gremlin.sh -e /tmp/load_data_remote.groovy 2>&1)
    
    if echo "$DATA_OUT" | grep -q "Data loading complete"; then
        log_pass "Sample data loaded"
    else
        log_fail "Data loading failed"
        echo "Error: $DATA_OUT" | tail -20 >> "$RESULTS"
    fi
else
    log_pass "Graph already initialized ($VCOUNT vertices)"
fi

# Test 4: Query Tests
log_test "Test 4: JanusGraph Queries"

VCOUNT=$(podman --remote --connection $PODMAN_CONNECTION exec janusgraph-server ./bin/gremlin.sh 2>&1 << 'EOF' | grep "^==>" | tail -1 | sed 's/^==>//'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().count()
EOF
)

if [ "$VCOUNT" = "11" ]; then
    log_pass "Vertex count correct: $VCOUNT"
else
    log_fail "Unexpected vertex count: $VCOUNT (expected 11)"
fi

ECOUNT=$(podman --remote --connection $PODMAN_CONNECTION exec janusgraph-server ./bin/gremlin.sh 2>&1 << 'EOF' | grep "^==>" | tail -1 | sed 's/^==>//'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.E().count()
EOF
)

if [ "$ECOUNT" = "19" ]; then
    log_pass "Edge count correct: $ECOUNT"
else
    log_fail "Unexpected edge count: $ECOUNT (expected 19)"
fi

PEOPLE=$(podman --remote --connection $PODMAN_CONNECTION exec janusgraph-server ./bin/gremlin.sh 2>&1 << 'EOF' | grep "Alice"
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().hasLabel('person').values('name').toList()
EOF
)

if [ -n "$PEOPLE" ]; then
    log_pass "Person vertices found"
else
    log_fail "Person vertices not found"
fi

FRIENDS=$(podman --remote --connection $PODMAN_CONNECTION exec janusgraph-server ./bin/gremlin.sh 2>&1 << 'EOF' | grep "Bob"
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().has('person', 'name', 'Alice Johnson').out('knows').values('name').toList()
EOF
)

if [ -n "$FRIENDS" ]; then
    log_pass "Traversal queries working"
else
    log_fail "Traversal queries failed"
fi

# Test 5: Python Client
log_test "Test 5: Python Client"

if python3 -c "import gremlin_python" 2>/dev/null; then
    log_pass "gremlin_python installed"
else
    log_fail "gremlin_python not installed"
fi

if [ -f "$PROJECT_ROOT/tests/integration/test_janusgraph_client.py" ]; then
    if timeout 60 python3 "$PROJECT_ROOT/tests/integration/test_janusgraph_client.py" 2>&1 | grep -q "completed successfully"; then
        log_pass "Python client tests passed"
    else
        log_fail "Python client tests failed"
    fi
else
    log_fail "test_janusgraph_client.py not found"
fi

# Summary
echo "" >> "$RESULTS"
echo "---" >> "$RESULTS"
echo "" >> "$RESULTS"
echo "## Summary" >> "$RESULTS"
echo "" >> "$RESULTS"
echo "- **Passed**: $PASS" >> "$RESULTS"
echo "- **Failed**: $FAIL" >> "$RESULTS"
echo "- **Total**: $((PASS + FAIL))" >> "$RESULTS"
echo "" >> "$RESULTS"

if [ $FAIL -eq 0 ]; then
    echo "✅ ALL TESTS PASSED" >> "$RESULTS"
    echo ""
    echo "✅ ALL TESTS PASSED"
else
    echo "❌ $FAIL TEST(S) FAILED" >> "$RESULTS"
    echo ""
    echo "❌ $FAIL TEST(S) FAILED"
fi

echo ""
echo "Results saved to: $RESULTS"
