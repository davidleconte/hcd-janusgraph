#!/bin/bash
# Test AML Structuring Implementation
# Quick validation script

set -e

cd /Users/david.leconte/Documents/Work/Demos/hcd-tarball-janusgraph

echo "🧪 Testing AML Structuring Implementation"
echo "========================================"
echo ""

echo "1. Installing Python dependencies..."
pip install -q faker pandas tqdm

echo ""
echo "2. Generating synthetic data..."
python3 banking/data/aml/generate_structuring_data.py

echo ""
echo "3. Loading schema into JanusGraph..."
podman --remote --connection podman-wxd exec -i janusgraph-server ./bin/gremlin.sh < banking/schema/graph/aml_schema.groovy

echo ""
echo "4. Loading data into JanusGraph..."
python3 banking/data/aml/load_structuring_data.py

echo ""
echo "✅ Test complete!"
echo ""
echo "Validation:"
echo "  - Synthetic data generated"
echo "  - Schema loaded"
echo "  - Data loaded into graph"
echo "  - Relationships created"
echo ""
echo "Next: Run detection queries"

# Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
