#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/scripts/utils/podman_connection.sh"
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
PODMAN_CONNECTION="${PODMAN_CONNECTION:-}"
PODMAN_CONNECTION="$(resolve_podman_connection "${PODMAN_CONNECTION}")"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"

RESULTS="$SCRIPT_DIR/TEST_RESULTS.md"

echo "# HCD + JanusGraph Test Results" > "$RESULTS"
echo "" >> "$RESULTS"
echo "**Date**: $(date)" >> "$RESULTS"
echo "" >> "$RESULTS"
echo "---" >> "$RESULTS"
echo "" >> "$RESULTS"

PASS=0
FAIL=0

ansi_clean() {
    printf '%s\n' "$1" | sed -E $'s/\x1B\[[0-9;]*[[:alpha:]]//g'
}

run_gremlin() {
    local script="$1"
    podman --remote --connection "$PODMAN_CONNECTION" exec -i "$JANUSGRAPH_CONTAINER" ./bin/gremlin.sh 2>&1 <<EOF
:remote connect tinkerpop.server conf/remote.yaml
:remote console
$script
:quit
EOF
}

run_gremlin_query() {
    local script="$1"
    local output
    output="$(run_gremlin "$script")"
    ansi_clean "$output" | grep -E '^==>.*' | tail -n 1 | sed -E 's/^==>[[:space:]]*//'
}

query_person_count() {
    run_gremlin_query "g.V().hasLabel('person').count()"
}

run_gremlin_file() {
    local file_path="$1"
    local script
    if [ ! -f "$file_path" ]; then
        echo "File not found: $file_path"
        return 1
    fi
    script="$(tr '\n' ';' < "$file_path")"
    run_gremlin "$script"
}

resolve_container_name() {
    local service_name="$1"
    local candidate_with_prefix="${COMPOSE_PROJECT_NAME}_${service_name}_1"

    if podman --remote --connection "$PODMAN_CONNECTION" ps --format '{{.Names}}' | grep -q "^${candidate_with_prefix}$"; then
        echo "$candidate_with_prefix"
        return 0
    fi

    if podman --remote --connection "$PODMAN_CONNECTION" ps --format '{{.Names}}' | grep -q "^${service_name}$"; then
        echo "$service_name"
        return 0
    fi

    return 1
}

if ! HCD_CONTAINER="$(resolve_container_name "hcd-server")"; then
    HCD_CONTAINER="${COMPOSE_PROJECT_NAME}_hcd-server_1"
fi

if ! JANUSGRAPH_CONTAINER="$(resolve_container_name "janusgraph-server")"; then
    JANUSGRAPH_CONTAINER="${COMPOSE_PROJECT_NAME}_janusgraph-server_1"
fi

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
if podman --remote --connection $PODMAN_CONNECTION ps --format '{{.Names}}' | grep -q "^${HCD_CONTAINER}$"; then
    log_pass "HCD container running"
else
    log_fail "HCD container not running"
fi

if podman --remote --connection $PODMAN_CONNECTION ps --format '{{.Names}}' | grep -q "^${JANUSGRAPH_CONTAINER}$"; then
    log_pass "JanusGraph container running"
else
    log_fail "JanusGraph container not running"
fi

# Test 2: HCD Status
log_test "Test 2: HCD Database"
if podman --remote --connection $PODMAN_CONNECTION exec "$HCD_CONTAINER" /opt/hcd/bin/nodetool status 2>/dev/null | grep -q "UN"; then
    log_pass "HCD cluster healthy (UN status)"
else
    log_fail "HCD cluster unhealthy"
fi

if podman --remote --connection $PODMAN_CONNECTION exec "$HCD_CONTAINER" /opt/hcd/bin/cqlsh -e "DESCRIBE KEYSPACES;" 2>/dev/null | grep -q "janusgraph"; then
    log_pass "JanusGraph keyspace exists"
else
    log_fail "JanusGraph keyspace missing"
fi

# Test 3: Initialize Schema and Data
log_test "Test 3: Schema and Data Initialization"
GRAPH_INITIALIZED=0
RUN_BASELINE_CHECKS=0

# Copy scripts from new location (src/groovy/)
cd "$PROJECT_ROOT"
podman --remote --connection $PODMAN_CONNECTION cp src/groovy/init_schema_remote.groovy "$JANUSGRAPH_CONTAINER:/tmp/" 2>&1
podman --remote --connection $PODMAN_CONNECTION cp src/groovy/load_data_remote.groovy "$JANUSGRAPH_CONTAINER:/tmp/" 2>&1

# Check current vertex count
VCOUNT="$(run_gremlin_query "g.V().count()")"

echo "Current vertices: $VCOUNT"
echo "Current vertices: $VCOUNT" >> "$RESULTS"
echo "" >> "$RESULTS"

if [ "$VCOUNT" = "0" ] || [ -z "$VCOUNT" ]; then
    echo "Initializing schema..."
    SCHEMA_OUT="$(run_gremlin_file "$PROJECT_ROOT/src/groovy/init_schema_remote.groovy")"

    if echo "$SCHEMA_OUT" | grep -q "Schema committed successfully!"; then
        log_pass "Schema initialized"
        GRAPH_INITIALIZED=1
        RUN_BASELINE_CHECKS=1
    else
        log_fail "Schema initialization failed"
        echo "Error: $(ansi_clean "$SCHEMA_OUT")" | tail -20 >> "$RESULTS"
    fi

    echo "Loading data..."
    DATA_OUT="$(run_gremlin_file "$PROJECT_ROOT/src/groovy/load_data_remote.groovy")"

    if echo "$DATA_OUT" | grep -q "Data loading complete"; then
        log_pass "Sample data loaded"
        GRAPH_INITIALIZED=1
        RUN_BASELINE_CHECKS=1
    else
        log_fail "Data loading failed"
        echo "Error: $(ansi_clean "$DATA_OUT")" | tail -20 >> "$RESULTS"
    fi
else
    log_pass "Graph already initialized ($VCOUNT vertices)"
    SAMPLE_COUNT="$(query_person_count)"
    if [ -z "$SAMPLE_COUNT" ] || [ "$SAMPLE_COUNT" -eq 0 ]; then
        echo "Loading sample data for validation coverage..."
        DATA_OUT="$(run_gremlin_file "$PROJECT_ROOT/src/groovy/load_data_remote.groovy")"

        if echo "$DATA_OUT" | grep -q "Data loading complete"; then
            log_pass "Validation sample data loaded"
        else
            log_fail "Validation sample data not loaded"
            echo "Error: $(ansi_clean "$DATA_OUT")" | tail -20 >> "$RESULTS"
        fi
    else
        log_pass "Validation sample data already present"
    fi
fi

# Test 4: Query Tests
log_test "Test 4: JanusGraph Queries"

VCOUNT="$(run_gremlin_query "g.V().count()")"
ECOUNT="$(run_gremlin_query "g.E().count()")"

if [ "$RUN_BASELINE_CHECKS" = "1" ]; then
    if [ "$VCOUNT" = "11" ]; then
        log_pass "Vertex count correct: $VCOUNT"
    else
        log_fail "Unexpected vertex count: $VCOUNT (expected 11)"
    fi
else
    if [[ "$VCOUNT" =~ ^[0-9]+$ ]] && [ "$VCOUNT" -gt 0 ]; then
        log_pass "Vertex data present: $VCOUNT"
    else
        log_fail "No vertices found: $VCOUNT"
    fi
fi

if [ "$RUN_BASELINE_CHECKS" = "1" ]; then
    if [ "$ECOUNT" = "19" ]; then
        log_pass "Edge count correct: $ECOUNT"
    else
        log_fail "Unexpected edge count: $ECOUNT (expected 19)"
    fi
else
    if [[ "$ECOUNT" =~ ^[0-9]+$ ]] && [ "$ECOUNT" -gt 0 ]; then
        log_pass "Edge data present: $ECOUNT"
    else
        log_fail "No edges found: $ECOUNT"
    fi
fi

PEOPLE="$(query_person_count)"

if [ -n "$PEOPLE" ] && [ "$PEOPLE" -gt 0 ]; then
    log_pass "Person vertices found"
else
    log_fail "Person vertices not found"
fi

FRIENDS="$(run_gremlin_query "g.V().hasLabel('person').outE().limit(1).count()")"

if [ -n "$FRIENDS" ] && [ "$FRIENDS" -gt 0 ]; then
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
    PY_CLIENT_TEST_LOG="$SCRIPT_DIR/test_janusgraph_client.log"
    if timeout 120 pytest --no-cov "$PROJECT_ROOT/tests/integration/test_janusgraph_client.py" > "$PY_CLIENT_TEST_LOG" 2>&1; then
        log_pass "Python client tests passed"
    else
        log_fail "Python client tests failed"
        echo "Python client test output:" >> "$RESULTS"
        tail -20 "$PY_CLIENT_TEST_LOG" >> "$RESULTS"
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
