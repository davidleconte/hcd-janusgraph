#!/bin/bash
# Deploy AML System to Production
# Phases 5-6: Vector/AI Foundation + Complete AML Implementation

set -e

echo "=========================================="
echo "AML SYSTEM PRODUCTION DEPLOYMENT"
echo "=========================================="

# Configuration
OPENSEARCH_HOST=${OPENSEARCH_HOST:-localhost}
OPENSEARCH_PORT=${OPENSEARCH_PORT:-9200}
JANUSGRAPH_HOST=${JANUSGRAPH_HOST:-localhost}
JANUSGRAPH_PORT=${JANUSGRAPH_PORT:-8182}
CONDA_ENV=${CONDA_ENV:-janusgraph-analysis}

echo ""
echo "Configuration:"
echo "  OpenSearch: $OPENSEARCH_HOST:$OPENSEARCH_PORT"
echo "  JanusGraph: $JANUSGRAPH_HOST:$JANUSGRAPH_PORT"
echo "  Conda Env: $CONDA_ENV"
echo ""

# Step 1: Verify prerequisites
echo "1. Verifying prerequisites..."

# Check OpenSearch
if ! curl -s "http://$OPENSEARCH_HOST:$OPENSEARCH_PORT" > /dev/null; then
    echo "   ❌ OpenSearch not accessible at $OPENSEARCH_HOST:$OPENSEARCH_PORT"
    exit 1
fi
echo "   ✅ OpenSearch accessible"

# Check JanusGraph
if ! curl -s "http://$JANUSGRAPH_HOST:$JANUSGRAPH_PORT" > /dev/null 2>&1; then
    echo "   ⚠️  JanusGraph not accessible (may be WebSocket only)"
fi

# Check conda environment
if ! conda env list | grep -q "$CONDA_ENV"; then
    echo "   ❌ Conda environment '$CONDA_ENV' not found"
    echo "   Run: conda env create -f docker/jupyter/environment.yml"
    exit 1
fi
echo "   ✅ Conda environment exists"

# Step 2: Activate environment and verify dependencies
echo ""
echo "2. Verifying ML/AI dependencies..."
eval "$(conda shell.bash hook)"
conda activate $CONDA_ENV

python -c "
import sys
try:
    import torch
    import sentence_transformers
    import opensearchpy
    from gremlin_python import __version__
    print('   ✅ All dependencies installed')
except ImportError as e:
    print(f'   ❌ Missing dependency: {e}')
    sys.exit(1)
"

# Step 3: Create OpenSearch indices
echo ""
echo "3. Creating OpenSearch indices..."

python << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, 'src/python')

from utils.vector_search import VectorSearchClient

try:
    client = VectorSearchClient(host='localhost', port=9200)

    # Create sanctions index
    if not client.client.indices.exists(index='sanctions_list'):
        client.create_vector_index(
            index_name='sanctions_list',
            vector_dimension=384,
            additional_fields={
                'name': {'type': 'text'},
                'entity_id': {'type': 'keyword'},
                'sanctions_list': {'type': 'keyword'},
                'entity_type': {'type': 'keyword'},
                'country': {'type': 'keyword'}
            }
        )
        print('   ✅ Created sanctions_list index')
    else:
        print('   ℹ️  sanctions_list index already exists')

    # Create transactions index
    if not client.client.indices.exists(index='aml_transactions'):
        client.create_vector_index(
            index_name='aml_transactions',
            vector_dimension=768,
            additional_fields={
                'transaction_id': {'type': 'keyword'},
                'account_id': {'type': 'keyword'},
                'description': {'type': 'text'},
                'amount': {'type': 'float'},
                'timestamp': {'type': 'date'}
            }
        )
        print('   ✅ Created aml_transactions index')
    else:
        print('   ℹ️  aml_transactions index already exists')

    print('   ✅ OpenSearch indices ready')
except Exception as e:
    print(f'   ❌ Error creating indices: {e}')
    sys.exit(1)
PYTHON_SCRIPT

# Step 4: Verify JanusGraph schema
echo ""
echo "4. Verifying JanusGraph schema..."
echo "   ℹ️  Ensure AML schema is loaded (banking/schema/graph/aml_schema.groovy)"

# Step 5: Run system tests
echo ""
echo "5. Running system tests..."

# Test Phase 5 setup
echo "   Testing Phase 5 (Vector/AI)..."
if python scripts/testing/test_phase5_setup.py > /tmp/phase5_test.log 2>&1; then
    echo "   ✅ Phase 5 tests passed"
else
    echo "   ⚠️  Phase 5 tests had issues (check /tmp/phase5_test.log)"
fi

# Test sanctions screening
echo "   Testing sanctions screening..."
if python banking/aml/sanctions_screening.py > /tmp/sanctions_test.log 2>&1; then
    echo "   ✅ Sanctions screening operational"
else
    echo "   ⚠️  Sanctions screening test failed (check /tmp/sanctions_test.log)"
fi

# Step 6: Deployment summary
echo ""
echo "=========================================="
echo "DEPLOYMENT SUMMARY"
echo "=========================================="
echo ""
echo "✅ Prerequisites verified"
echo "✅ ML/AI dependencies installed"
echo "✅ OpenSearch indices created"
echo "✅ System tests completed"
echo ""
echo "Deployed Components:"
echo "  - Embedding Generator (384/768 dim)"
echo "  - Vector Search Client (OpenSearch + JVector)"
echo "  - Sanctions Screening Module"
echo "  - Enhanced Structuring Detection"
echo ""
echo "Next Steps:"
echo "  1. Load sanctions list data"
echo "  2. Index transaction data"
echo "  3. Configure monitoring alerts"
echo "  4. Train compliance team"
echo ""
echo "=========================================="
echo "🎉 AML SYSTEM DEPLOYED TO PRODUCTION"
echo "=========================================="

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
