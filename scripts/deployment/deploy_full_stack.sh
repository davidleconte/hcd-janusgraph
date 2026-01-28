#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/.env" || source "$PROJECT_ROOT/.env.example"
# Deploy Full HCD + JanusGraph Visualization Stack
# Platform: macOS M3 Pro (Sequoia 26.2)
# Podman machine: configurable via .env

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables if .env exists
if [ -f ".env" ]; then
    source .env
fi

# Set defaults
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"
PODMAN_PLATFORM="${PODMAN_PLATFORM:-linux/arm64}"
HCD_CQL_PORT="${HCD_CQL_PORT:-19042}"
JANUSGRAPH_GREMLIN_PORT="${JANUSGRAPH_GREMLIN_PORT:-18182}"
JANUSGRAPH_MGMT_PORT="${JANUSGRAPH_MGMT_PORT:-18184}"
JUPYTER_PORT="${JUPYTER_PORT:-8888}"
VISUALIZER_PORT="${VISUALIZER_PORT:-3000}"
GRAPHEXP_PORT="${GRAPHEXP_PORT:-8080}"
PROMETHEUS_PORT="${PROMETHEUS_PORT:-9090}"
GRAFANA_PORT="${GRAFANA_PORT:-3001}"
NETWORK_NAME="${NETWORK_NAME:-hcd-janusgraph-network}"

echo "=========================================="
echo "HCD + JanusGraph Full Stack Deployment"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Podman Connection: $PODMAN_CONNECTION"
echo "  Platform: $PODMAN_PLATFORM"
echo ""

# Check podman-wxd is running
echo "1. Checking podman machine..."
if ! podman --remote --connection $PODMAN_CONNECTION ps >/dev/null 2>&1; then
    echo "❌ Podman machine '$PODMAN_CONNECTION' not accessible"
    echo "   Start it with: podman machine start $PODMAN_CONNECTION"
    exit 1
fi
echo "✅ Podman machine accessible"
echo ""

# Create exports directory
echo "2. Creating directories..."
mkdir -p exports notebooks
echo "✅ Directories created"
echo ""

# Build visualization images
echo "3. Building container images..."
echo "   This may take 10-15 minutes on first run..."

# Build Jupyter
echo "   Building Jupyter Lab (conda-forge)..."
podman --remote --connection $PODMAN_CONNECTION build \
    --platform $PODMAN_PLATFORM \
    -f docker/jupyter/Dockerfile \
    -t localhost/jupyter-janusgraph:latest \
    .

# Build JanusGraph Visualizer
echo "   Building JanusGraph Visualizer..."
podman --remote --connection $PODMAN_CONNECTION build \
    --platform $PODMAN_PLATFORM \
    -f docker/visualizer/Dockerfile \
    -t localhost/janusgraph-visualizer:latest \
    .

# Build Graphexp
echo "   Building Graphexp..."
podman --remote --connection $PODMAN_CONNECTION build \
    --platform $PODMAN_PLATFORM \
    -f docker/graphexp/Dockerfile \
    -t localhost/graphexp:latest \
    .

# Build cqlsh client
echo "   Building cqlsh client..."
podman --remote --connection $PODMAN_CONNECTION build \
    --platform $PODMAN_PLATFORM \
    -f docker/cqlsh/Dockerfile \
    -t localhost/cqlsh-client:latest \
    .

echo "✅ All images built"
echo ""

# Check if core containers are running
echo "4. Checking core containers (HCD + JanusGraph)..."
if ! podman --remote --connection $PODMAN_CONNECTION ps | grep -q "hcd-server"; then
    echo "⚠️  HCD container not running. Starting core stack..."
    # Start HCD first (already built)
    podman --remote --connection $PODMAN_CONNECTION run -d \
        --name hcd-server \
        --hostname hcd-server \
        --network $NETWORK_NAME \
        -p $HCD_CQL_PORT:9042 \
        -p 17000-17001:7000-7001 \
        -p 17199:7199 \
        -p 19160:9160 \
        localhost/hcd:1.2.3
    
    echo "   Waiting for HCD to be ready (60s)..."
    sleep 60
fi

if ! podman --remote --connection $PODMAN_CONNECTION ps | grep -q "janusgraph-server"; then
    echo "   Starting JanusGraph..."
    podman --remote --connection $PODMAN_CONNECTION run -d \
        --name janusgraph-server \
        --hostname janusgraph-server \
        --network $NETWORK_NAME \
        -p $JANUSGRAPH_GREMLIN_PORT:8182 \
        -p $JANUSGRAPH_MGMT_PORT:8184 \
        -e janusgraph.storage.backend=cql \
        -e janusgraph.storage.hostname=hcd-server \
        -e janusgraph.storage.port=9042 \
        -e janusgraph.storage.cql.keyspace=janusgraph \
        -e janusgraph.storage.cql.local-datacenter=datacenter1 \
        -e janusgraph.storage.cql.replication-factor=1 \
        -e janusgraph.storage.cql.replication-strategy-class=SimpleStrategy \
        -e index.search.backend=lucene \
        -e index.search.directory=/var/lib/janusgraph/index \
        -e gremlinserver.graphs.graph=/opt/janusgraph/conf/janusgraph-cql-server.properties \
        -e gremlinserver.graphManager=org.janusgraph.graphdb.management.JanusGraphManager \
        docker.io/janusgraph/janusgraph:latest
    
    echo "   Waiting for JanusGraph to be ready (30s)..."
    sleep 30
fi

echo "✅ Core stack running"
echo ""

# Start visualization containers
echo "5. Starting visualization containers..."

# Jupyter Lab
if ! podman --remote --connection $PODMAN_CONNECTION ps | grep -q "jupyter-lab"; then
    echo "   Starting Jupyter Lab..."
    podman --remote --connection $PODMAN_CONNECTION run -d \
        --name jupyter-lab \
        --hostname jupyter-lab \
        --network $NETWORK_NAME \
        -p $JUPYTER_PORT:8888 \
        -v "$PWD/notebooks:/workspace/notebooks:Z" \
        -v "$PWD/exports:/workspace/exports:Z" \
        -e GREMLIN_URL=ws://janusgraph-server:8182/gremlin \
        -e HCD_HOST=hcd-server \
        -e HCD_PORT=9042 \
        localhost/jupyter-janusgraph:latest
fi

# JanusGraph Visualizer
if ! podman --remote --connection $PODMAN_CONNECTION ps | grep -q "janusgraph-visualizer"; then
    echo "   Starting JanusGraph Visualizer..."
    podman --remote --connection $PODMAN_CONNECTION run -d \
        --name janusgraph-visualizer \
        --hostname janusgraph-visualizer \
        --network $NETWORK_NAME \
        -p $VISUALIZER_PORT:3000 \
        -e GREMLIN_URL=ws://janusgraph-server:8182/gremlin \
        localhost/janusgraph-visualizer:latest
fi

# Graphexp
if ! podman --remote --connection $PODMAN_CONNECTION ps | grep -q "graphexp"; then
    echo "   Starting Graphexp..."
    podman --remote --connection $PODMAN_CONNECTION run -d \
        --name graphexp \
        --hostname graphexp \
        --network $NETWORK_NAME \
        -p $GRAPHEXP_PORT:8080 \
        localhost/graphexp:latest
fi

# cqlsh client (kept running for exec access)
if ! podman --remote --connection $PODMAN_CONNECTION ps | grep -q "cqlsh-client"; then
    echo "   Starting cqlsh client..."
    podman --remote --connection $PODMAN_CONNECTION run -d \
        --name cqlsh-client \
        --hostname cqlsh-client \
        --network $NETWORK_NAME \
        -e CQLSH_HOST=hcd-server \
        -e CQLSH_PORT=9042 \
        localhost/cqlsh-client:latest \
        tail -f /dev/null
fi

echo "✅ Visualization containers started"
echo ""

# Start monitoring containers
echo "6. Starting monitoring containers..."

# Prometheus
if ! podman --remote --connection $PODMAN_CONNECTION ps | grep -q "prometheus"; then
    echo "   Starting Prometheus..."
    podman --remote --connection $PODMAN_CONNECTION run -d \
        --name prometheus \
        --hostname prometheus \
        --network $NETWORK_NAME \
        -p $PROMETHEUS_PORT:9090 \
        -v "$PWD/prometheus.yml:/etc/prometheus/prometheus.yml:ro,Z" \
        docker.io/prom/prometheus:latest \
        --config.file=/etc/prometheus/prometheus.yml \
        --storage.tsdb.path=/prometheus
fi

# Grafana
if ! podman --remote --connection $PODMAN_CONNECTION ps | grep -q "grafana"; then
    echo "   Starting Grafana..."
    podman --remote --connection $PODMAN_CONNECTION run -d \
        --name grafana \
        --hostname grafana \
        --network $NETWORK_NAME \
        -p $GRAFANA_PORT:3000 \
        -e GF_SECURITY_ADMIN_USER=admin \
        -e GF_SECURITY_ADMIN_PASSWORD=admin \
        -e GF_USERS_ALLOW_SIGN_UP=false \
        docker.io/grafana/grafana:latest
fi

echo "✅ Monitoring containers started"
echo ""

# Wait for services to be ready
echo "7. Waiting for services to be ready..."
sleep 10
echo "✅ Services ready"
echo ""

# Display access information
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "📊 WEB INTERFACES:"
echo "   Jupyter Lab:          http://localhost:$JUPYTER_PORT"
echo "   JanusGraph Visualizer: http://localhost:$VISUALIZER_PORT"
echo "   Graphexp:             http://localhost:$GRAPHEXP_PORT"
echo "   Grafana:              http://localhost:$GRAFANA_PORT (admin/admin)"
echo "   Prometheus:           http://localhost:$PROMETHEUS_PORT"
echo ""
echo "🔌 API ENDPOINTS:"
echo "   JanusGraph Gremlin:   ws://localhost:$JANUSGRAPH_GREMLIN_PORT/gremlin"
echo "   HCD CQL:              localhost:$HCD_CQL_PORT"
echo "   HCD JMX:              localhost:17199"
echo ""
echo "💻 CLI ACCESS:"
echo "   Gremlin Console:"
echo "     podman --remote --connection $PODMAN_CONNECTION exec -it janusgraph-server ./bin/gremlin.sh"
echo ""
echo "   CQL Shell:"
echo "     podman --remote --connection $PODMAN_CONNECTION exec -it cqlsh-client cqlsh"
echo ""
echo "📁 SHARED DIRECTORIES:"
echo "   Notebooks: $PWD/notebooks"
echo "   Exports:   $PWD/exports"
echo ""
echo "📖 See FULL_STACK_ACCESS.md for detailed documentation"
echo ""
echo "To stop all services:"
echo "   ./stop_full_stack.sh"
echo ""
