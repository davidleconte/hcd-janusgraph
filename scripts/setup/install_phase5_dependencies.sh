#!/bin/bash
# Phase 5: Install ML/AI Dependencies
# OpenSearch 3.3.4+ with JVector Plugin
# NO FAISS - JVector handles all vector operations
# Uses conda environment (janusgraph-analysis) and uv package manager

set -e

echo "=========================================="
echo "Phase 5: ML/AI Dependencies Installation"
echo "=========================================="

# Check if conda environment exists
if ! conda env list | grep -q "janusgraph-analysis"; then
    echo "⚠️  Conda environment 'janusgraph-analysis' not found"
    echo "Creating environment from docker/jupyter/environment.yml..."
    conda env create -f docker/jupyter/environment.yml
fi

# Activate conda environment
echo "🔧 Activating conda environment: janusgraph-analysis"
eval "$(conda shell.bash hook)"
conda activate janusgraph-analysis

# Navigate to project root
cd "$(dirname "$0")/../.."

# Install deterministic locked dependencies
echo "📦 Installing deterministic dependencies with uv..."
uv lock --check
uv pip install -r requirements-dev.txt

echo "📥 Downloading NLP models..."
python -m spacy download en_core_web_sm --quiet || echo "⚠️  Skipping spaCy model (can download later)"

echo "📥 Downloading NLTK data..."
python -c "
import nltk
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
print('✅ NLTK data downloaded')
"

echo "📥 Downloading embedding models..."
python -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
print('✅ Models cached')
"

echo "✅ Verifying installations..."
python -c "
import torch, sentence_transformers, opensearchpy
print('✅ PyTorch:', torch.__version__)
print('✅ sentence-transformers:', sentence_transformers.__version__)
print('✅ opensearch-py:', opensearchpy.__version__)

try:
    import gremlinpython
    print('✅ gremlinpython:', gremlinpython.__version__)
except ImportError:
    print('⚠️  gremlinpython not found (will be installed from conda env)')

print('🎉 Phase 5 ML/AI stack ready!')
"

echo "=========================================="
echo "✅ Installation Complete"
echo "📝 Environment: janusgraph-analysis (conda-forge)"
echo "📝 Package manager: uv"
echo "=========================================="

# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
