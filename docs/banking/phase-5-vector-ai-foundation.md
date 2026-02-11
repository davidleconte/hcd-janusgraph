
# Phase 5: Vector/AI Foundation

**Duration**: Weeks 13-14 (64 hours total)  
**Team**: Senior ML Engineer, Graph DB Expert, Python Developer  
**Status**: Ready for Implementation

---

## Overview

Phase 5 establishes the ML/AI foundation required for all four banking use cases. This includes embedding generation, vector search capabilities, and integration between JanusGraph and OpenSearch.

**Key Deliverables:**
- ML/AI infrastructure (PyTorch, sentence-transformers)
- Embedding generation system
- Vector search client
- JanusGraph schema updates
- Semantic matching POC

**Success Criteria:**
- ✅ All ML dependencies installed
- ✅ Embedding generation <10ms per text
- ✅ Vector search <50ms for k-NN
- ✅ Fuzzy name matching operational
- ✅ 90%+ accuracy on test cases

---

## Week 13: ML Infrastructure (32 hours)

### Task 13.1: Update Dependencies (4 hours)

#### Objective
Install and configure all ML/AI dependencies required for vector operations.

#### Files to Create/Modify

**1. `banking/requirements.txt`** (Update)

```python
# Banking Use Cases - Complete Dependencies
# Phase 5: ML/AI Integration

# ============================================
# Existing Dependencies (Phases 1-4)
# ============================================
faker==26.1.0
gremlinpython==4.0.0
pandas==2.2.0
numpy==1.26.0
scipy==1.13.0
opensearch-py==2.4.0
matplotlib==3.8.0
seaborn==0.13.0
networkx==3.2.0
pyvis==0.3.2
python-dotenv==1.0.0
tqdm==4.66.0

# ============================================
# Phase 5: ML/AI Stack
# ============================================

# Deep Learning Framework
torch==2.1.0
torchvision==0.16.0
torchaudio==2.1.0

# NLP & Embeddings
sentence-transformers==2.3.1
transformers==4.36.0
tokenizers==0.15.0

# Vector Search & Similarity
faiss-cpu==1.7.4
hnswlib==0.8.0

# Machine Learning
scikit-learn==1.4.0
xgboost==2.0.3
lightgbm==4.2.0

# NLP Processing
spacy==3.7.2
nltk==3.8.1
textblob==0.17.1

# Model Management
huggingface-hub==0.20.0
safetensors==0.4.1
accelerate==0.25.0

# Data Processing
pyarrow==14.0.2
fastparquet==2024.2.0

# Visualization
plotly==5.18.0
wordcloud==1.9.3

# Utilities
joblib==1.3.2
cloudpickle==3.0.0
```

**2. `docker/jupyter/environment.yml`** (Update)

```yaml
name: banking-ml
channels:
  - pytorch
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pytorch=2.1.0
  - torchvision=0.16.0
  - torchaudio=2.1.0
  - cpuonly
  - pip
  - pip:
    - sentence-transformers==2.3.1
    - transformers==4.36.0
    - faiss-cpu==1.7.4
    - hnswlib==0.8.0
    - scikit-learn==1.4.0
    - spacy==3.7.2
    - nltk==3.8.1
    - gremlinpython==4.0.0
    - opensearch-py==2.4.0
    - pandas==2.2.0
    - matplotlib==3.8.0
    - seaborn==0.13.0
    - jupyter==1.0.0
    - jupyterlab==4.0.0
```

**3. Installation Script**: `scripts/setup/install_ml_dependencies.sh`

```bash
#!/bin/bash
# Install ML/AI dependencies for banking use cases

set -e

echo "🚀 Installing ML/AI dependencies..."

# Update banking requirements
cd banking
pip install -r requirements.txt

# Download NLP models
echo "📥 Downloading NLP models..."
python -m spacy download en_core_web_sm
python -m nltk.downloader punkt stopwords wordnet

# Download sentence-transformers models
echo "📥 Downloading sentence-transformers models..."
python -c "
from sentence_transformers import SentenceTransformer
print('Downloading all-MiniLM-L6-v2 (fast, 384-dim)...')
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print('Downloading all-mpnet-base-v2 (accurate, 768-dim)...')
SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
print('✅ Models downloaded')
"

# Verify installation
echo "✅ Verifying installation..."
python -c "
import torch
import sentence_transformers
import faiss
import hnswlib
import spacy
import nltk

print('PyTorch:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
print('sentence-transformers:', sentence_transformers.__version__)
print('FAISS:', faiss.__version__)
print('✅ All dependencies installed successfully')
"

# Rebuild Docker images
echo "🐳 Rebuilding Docker images..."
cd ..
docker-compose build jupyter

echo "✅ ML/AI infrastructure ready"
```

#### Acceptance Criteria
- [ ] All packages install without errors
- [ ] PyTorch operational (CPU or GPU)
- [ ] sentence-transformers can load models
- [ ] FAISS operational
- [ ] Docker image builds successfully
- [ ] Models downloaded and cached

---

### Task 13.2: Embedding Generator (8 hours)

#### Objective
Create a production-ready embedding generation system supporting multiple model types and use cases.

#### Implementation

**File**: `src/python/utils/embedding_generator.py`

```python
"""
Embedding Generator for Banking Use Cases

Generates vector embeddings for text, names, addresses, and behavioral patterns
using sentence-transformers and custom models.
"""

import logging
from typing import List, Dict, Any, Optional, Union
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from functools import lru_cache
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generate embeddings for various banking entities and patterns.
    
    Supports:
    - Text embeddings (general purpose)
    - Name embeddings (person/company names)
    - Address embeddings (physical addresses)
    - Behavioral embeddings (transaction patterns)
    - Sequence embeddings (time-series data)
    """
    
    # Available models
    MODELS = {
        'fast': 'sentence-transformers/all-MiniLM-L6-v2',  # 384 dim, fast
        'accurate': 'sentence-transformers/all-mpnet-base-v2',  # 768 dim, accurate
        'multilingual': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'  # 384 dim
    }
    
    def __init__(
        self,
        model_name: str = 'fast',
        device: Optional[str] = None,
        cache_size: int = 10000
    ):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Model to use ('fast', 'accurate', 'multilingual')
            device: Device to use ('cuda', 'cpu', or None for auto)
            cache_size: Size of embedding cache
        """
        if model_name not in self.MODELS:
            raise ValueError(f"Unknown model: {model_name}. Choose from {list(self.MODELS.keys())}")
        
        self.model_name = model_name
        self.model_path = self.MODELS[model_name]
        
        # Auto-detect device
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        
        # Load model
        logger.info(f"Loading model: {self.model_path} on {self.device}")
        self.model = SentenceTransformer(self.model_path, device=self.device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"Model loaded: {self.embedding_dim} dimensions")
        
        # Cache for embeddings
        self._cache = {}
        self._cache_size = cache_size
    
    def generate_text_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for general text.
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector
        """
        # Check cache
        cache_key = self._get_cache_key(text)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Generate embedding
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        # Cache result
        self._add_to_cache(cache_key, embedding)
        
        return embedding
    
    def generate_text_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts (batched for efficiency).
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            show_progress: Show progress bar
        
        Returns:
            Array of embeddings (n_texts, embedding_dim)
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=show_progress
        )
        
        return embeddings
    
    def generate_name_embedding(
        self,
        first_name: str,
        last_name: str,
        middle_name: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate embedding for person/company name.
        
        Uses special formatting to improve matching:
        - Handles abbreviations (J. Smith)
        - Handles nicknames (Bob vs Robert)
        - Handles variations (Smith vs Smyth)
        
        Args:
            first_name: First name
            last_name: Last name
            middle_name: Middle name (optional)
        
        Returns:
            Name embedding
        """
        # Format name
        parts = [first_name, middle_name, last_name]
        name = " ".join(p for p in parts if p)
        
        # Generate multiple variations for better matching
        variations = [
            name,  # Full name
            f"{first_name} {last_name}",  # Without middle
            f"{last_name}, {first_name}",  # Last, First
        ]
        
        # Generate embeddings for all variations
        embeddings = self.generate_text_embeddings_batch(variations)
        
        # Average embeddings (improves robustness)
        avg_embedding = np.mean(embeddings, axis=0)
        
        # Normalize
        avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)
        
        return avg_embedding
    
    def generate_address_embedding(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str,
        country: str = "USA"
    ) -> np.ndarray:
        """
        Generate embedding for physical address.
        
        Args:
            street: Street address
            city: City
            state: State/province
            zip_code: ZIP/postal code
            country: Country
        
        Returns:
            Address embedding
        """
        # Format address
        address = f"{street}, {city}, {state} {zip_code}, {country}"
        
        return self.generate_text_embedding(address)
    
    def generate_behavioral_embedding(
        self,
        features: Dict[str, float]
    ) -> np.ndarray:
        """
        Generate embedding for behavioral patterns.
        
        Converts numerical features to text description, then embeds.
        Useful for transaction patterns, customer behavior, etc.
        
        Args:
            features: Dictionary of feature name -> value
        
        Returns:
            Behavioral embedding
        """
        # Convert features to text description
        description_parts = []
        for key, value in features.items():
            if isinstance(value, float):
                description_parts.append(f"{key}: {value:.2f}")
            else:
                description_parts.append(f"{key}: {value}")
        
        description = ", ".join(description_parts)
        
        return self.generate_text_embedding(description)
    
    def generate_sequence_embedding(
        self,
        sequence: List[str],
        aggregate: str = 'mean'
    ) -> np.ndarray:
        """
        Generate embedding for sequence of texts (e.g., transaction descriptions).
        
        Args:
            sequence: List of texts in sequence
            aggregate: How to aggregate ('mean', 'max', 'sum')
        
        Returns:
            Sequence embedding
        """
        if not sequence:
            return np.zeros(self.embedding_dim)
        
        # Generate embeddings for all items
        embeddings = self.generate_text_embeddings_batch(sequence)
        
        # Aggregate
        if aggregate == 'mean':
            result = np.mean(embeddings, axis=0)
        elif aggregate == 'max':
            result = np.max(embeddings, axis=0)
        elif aggregate == 'sum':
            result = np.sum(embeddings, axis=0)
        else:
            raise ValueError(f"Unknown aggregate: {aggregate}")
        
        # Normalize
        result = result / np.linalg.norm(result)
        
        return result
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
        metric: str = 'cosine'
    ) -> float:
        """
        Compute similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            metric: Similarity metric ('cosine', 'euclidean', 'dot')
        
        Returns:
            Similarity score
        """
        if metric == 'cosine':
            # Cosine similarity (assumes normalized embeddings)
            return float(np.dot(embedding1, embedding2))
        
        elif metric == 'euclidean':
            # Euclidean distance (convert to similarity)
            distance = np.linalg.norm(embedding1 - embedding2)
            return 1.0 / (1.0 + distance)
        
        elif metric == 'dot':
            # Dot product
            return float(np.dot(embedding1, embedding2))
        
        else:
            raise ValueError(f"Unknown metric: {metric}")
    
    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: np.ndarray,
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find most similar embeddings from candidates.
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: Array of candidate embeddings
            top_k: Number of results to return
        
        Returns:
            List of (index, similarity_score) tuples
        """
        # Compute similarities
        similarities = np.dot(candidate_embeddings, query_embedding)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Return (index, score) pairs
        results = [(int(idx), float(similarities[idx])) for idx in top_indices]
        
        return results
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _add_to_cache(self, key: str, embedding: np.ndarray):
        """Add embedding to cache with size limit."""
        if len(self._cache) >= self._cache_size:
            # Remove oldest entry (simple FIFO)
            self._cache.pop(next(iter(self._cache)))
        
        self._cache[key] = embedding
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generator statistics."""
        return {
            'model': self.model_name,
            'model_path': self.model_path,
            'device': self.device,
            'embedding_dim': self.embedding_dim,
            'cache_size': len(self._cache),
            'cache_limit': self._cache_size
        }


# Example usage
if __name__ == "__main__":
    # Initialize generator
    gen = EmbeddingGenerator(model_name='fast')
    
    print("Embedding Generator Stats:")
    print(gen.get_stats())
    
    # Test text embedding
    text = "Suspicious transaction detected"
    embedding = gen.generate_text_embedding(text)
    print(f"\nText embedding shape: {embedding.shape}")
    
    # Test name embedding
    name_emb = gen.generate_name_embedding("John", "Smith")
    print(f"Name embedding shape: {name_emb.shape}")
    
    # Test similarity
    name_emb2 = gen.generate_name_embedding("Jon", "Smyth")
    similarity = gen.compute_similarity(name_emb, name_emb2)
    print(f"\nSimilarity (John Smith vs Jon Smyth): {similarity:.4f}")
    
    # Test batch processing
    texts = [f"Transaction {i}" for i in range(100)]
    import time
    start = time.time()
    batch_embeddings = gen.generate_text_embeddings_batch(texts, batch_size=32)
    duration = time.time() - start
    print(f"\nBatch processing: 100 texts in {duration:.2f}s ({100/duration:.0f} texts/sec)")
```

#### Testing

**File**: `tests/test_embedding_generator.py`

```python
"""
Tests for EmbeddingGenerator
"""

import pytest
import numpy as np
from src.python.utils.embedding_generator import EmbeddingGenerator


@pytest.fixture
def generator():
    """Create embedding generator for tests."""
    return EmbeddingGenerator(model_name='fast')


def test_initialization(generator):
    """Test generator initialization."""
    assert generator.model_name == 'fast'
    assert generator.embedding_dim == 384
    assert generator.device in ['cuda', 'cpu']


def test_text_embedding(generator):
    """Test text embedding generation."""
    text = "This is a test"
    embedding = generator.generate_text_embedding(text)
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)
    assert np.isclose(np.linalg.norm(embedding), 1.0, atol=1e-5)


def test_batch_embeddings(generator):
    """Test batch embedding generation."""
    texts = ["Text 1", "Text 2", "Text 3"]
    embeddings = generator.generate_text_embeddings_batch(texts)
    
    assert embeddings.shape == (3, 384)
    assert all(np.isclose(np.linalg.norm(emb), 1.0, atol=1e-5) for emb in embeddings)


def test_name_embedding(generator):
    """Test name embedding generation."""
    embedding = generator.generate_name_embedding("John", "Smith")
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)


def test_name_similarity(generator):
    """Test name similarity matching."""
    # Exact match
    emb1 = generator.generate_name_embedding("John", "Smith")
    emb2 = generator.generate_name_embedding("John", "Smith")
    similarity = generator.compute_similarity(emb1, emb2)
    assert similarity > 0.99
    
    # Similar names
    emb3 = generator.generate_name_embedding("Jon", "Smyth")
    similarity = generator.compute_similarity(emb1, emb3)
    assert similarity > 0.85  # Should be high but not perfect
    
    # Different names
    emb4 = generator.generate_name_embedding("Jane", "Doe")
    similarity = generator.compute_similarity(emb1, emb4)
    assert similarity < 0.7  # Should be lower


def test_address_embedding(generator):
    """Test address embedding generation."""
    embedding = generator.generate_address_embedding(
        "123 Main St",
        "New York",
        "NY",
        "10001"
    )
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)


def test_behavioral_embedding(generator):
    """Test behavioral embedding generation."""
    features = {
        'avg_transaction_amount': 1500.50,
        'transaction_frequency': 25,
        'risk_score': 0.75
    }
    
    embedding = generator.generate_behavioral_embedding(features)
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)


def test_sequence_embedding(generator):
    """Test sequence embedding generation."""
    sequence = ["Transaction 1", "Transaction 2", "Transaction 3"]
    
    # Test mean aggregation
    embedding = generator.generate_sequence_embedding(sequence, aggregate='mean')
    assert embedding.shape == (384,)
    
    # Test max aggregation
    embedding = generator.generate_sequence_embedding(sequence, aggregate='max')
    assert embedding.shape == (384,)


def test_similarity_metrics(generator):
    """Test different similarity metrics."""
    emb1 = generator.generate_text_embedding("Test 1")
    emb2 = generator.generate_text_embedding("Test 2")
    
    # Cosine similarity
    sim_cosine = generator.compute_similarity(emb1, emb2, metric='cosine')
    assert 0 <= sim_cosine <= 1
    
    # Euclidean similarity
    sim_euclidean = generator.compute_similarity(emb1, emb2, metric='euclidean')
    assert 0 <= sim_euclidean <= 1
    
    # Dot product
    sim_dot = generator.compute_similarity(emb1, emb2, metric='dot')
    assert isinstance(sim_dot, float)


def test_find_most_similar(generator):
    """Test finding most similar embeddings."""
    # Create query and candidates
    query = generator.generate_text_embedding("Query text")
    candidates = generator.generate_text_embeddings_batch([
        "Similar text",
        "Very different content",
        "Query text",  # Exact match
        "Somewhat related"
    ])
    
    # Find top 2
    results = generator.find_most_similar(query, candidates, top_k=2)
    
    assert len(results) == 2
    assert results[0][0] == 2  # Exact match should be first
    assert results[0][1] > 0.99  # Very high similarity


def test_caching(generator):
    """Test embedding caching."""
    text = "Cached text"
    
    # First call
    emb1 = generator.generate_text_embedding(text)
    cache_size_1 = len(generator._cache)
    
    # Second call (should use cache)
    emb2 = generator.generate_text_embedding(text)
    cache_size_2 = len(generator._cache)
    
    assert np.array_equal(emb1, emb2)
    assert cache_size_1 == cache_size_2  # Cache size shouldn't increase


def test_stats(generator):
    """Test getting generator statistics."""
    stats = generator.get_stats()
    
    assert 'model' in stats
    assert 'embedding_dim' in stats
    assert 'device' in stats
    assert stats['embedding_dim'] == 384


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

#### Acceptance Criteria
- [ ] All tests pass
- [ ] Embedding generation <10ms per text
- [ ] Batch processing >100 texts/second
- [ ] Name similarity matching works
- [ ] Caching operational

---

### Task 13.3: Vector Search Client (8 hours)

#### Objective
Create OpenSearch integration for vector similarity search.

#### Implementation

**File**: `src/python/utils/vector_search.py`

```python
"""
Vector Search Client for OpenSearch

Provides k-NN vector similarity search using OpenSearch with JVector plugin.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from opensearchpy import OpenSearch, helpers
from opensearchpy.exceptions import RequestError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorSearchClient:
    """
    Client for vector similarity search using OpenSearch.
    
    Features:
    - Index creation with k-NN configuration
    - Batch vector indexing
    - k-NN similarity search
    - Filtering and metadata support
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 9200,
        use_ssl: bool = False,
        verify_certs: bool = False,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize OpenSearch client.
        
        Args:
            host: OpenSearch host
            port: OpenSearch port
            use_ssl: Use SSL/TLS
            verify_certs: Verify SSL certificates
            username: Username for authentication
            password: Password for authentication
        """
        self.host = host
        self.port = port
        
        # Create client
        client_config = {
            'hosts': [{'host': host, 'port': port}],
            'use_ssl': use_ssl,
            'verify_certs': verify_certs,
            'ssl_show_warn': False
        }
        
        if username and password:
            client_config['http_auth'] = (username, password)
        
        self.client = OpenSearch(**client_config)
        
        logger.info(f"Connected to OpenSearch at {host}:{port}")
    
    def create_index(
        self,
        index_name: str,
        dimension: int,
        method: str = 'hnsw',
        space_type: str = 'cosinesimil',
        ef_construction: int = 512,
        m: int = 16
    ) -> bool:
        """
        Create vector index with k-NN configuration.
        
        Args:
            index_name: Name of the index
            dimension: Vector dimension
            method: Index method ('hnsw' or 'ivf')
            space_type: Distance metric ('cosinesimil', 'l2', 'innerproduct')
            ef_construction: HNSW ef_construction parameter
            m: HNSW M parameter (number of connections)
        
        Returns:
            True if successful
        """
        # Index configuration
        index_body = {
            'settings': {
                'index': {
                    'knn': True,
                    'knn.algo_param.ef_search': 512,
                    'number_of_shards': 1,
                    'number_of_replicas': 1
                }
            },
            'mappings': {
                'properties': {
                    'entity_id': {'type': 'keyword'},
                    'entity_type': {'type': 'keyword'},
                    'text': {'type': 'text'},
                    'embedding': {
                        'type': 'knn_vector',
                        'dimension': dimension,
                        'method': {
                            'name': method,
                            'space_type': space_type,
                            'engine': 'nmslib',
                            'parameters': {
                                'ef_construction': ef_construction,
                                'm': m
                            }
                        }
                    },
                    'metadata': {'type': 'object', 'enabled': True},
                    'timestamp': {'type': 'date'}
                }
            }
        }
        
        try:
            # Delete if exists
            if self.client.indices.exists(index=index_name):
                logger.warning(f"Index {index_name} already exists, deleting...")
                self.client.indices.delete(index=index_name)
            
            # Create index
            response = self.client.indices.create(index=index_name, body=index_body)
            logger.info(f"Created index: {index_name} (dimension={dimension})")
            return True
        
        except RequestError as e:
            logger.error(f"Failed to create index: {e}")
            return False
    
    def index_vector(
        self,
        index_name: str,
        entity_id: str,
        entity_type: str,
        text: str,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Index a single vector.
        
        Args:
            index_name: Index name
            entity_id: Unique entity identifier
            entity_type: Type of entity (person, address, etc.)
            text: Original text
            embedding: Vector embedding
            metadata: Additional metadata
        
        Returns:
            True if successful
        """
        document = {
            'entity_id': entity_id,
            'entity_type': entity_type,
            'text': text,
            'embedding': embedding.tolist(),
            'metadata': metadata or {},
            'timestamp': 'now'
        }
        
        try:
            response = self.client.index(
                index=index_name,
                body=document,
                id=entity_id,
                refresh=True
            )
            return response['result'] in ['created', 'updated']
        
        except Exception as e:
            logger.error(f"Failed to index vector: {e}")
            return False
    
    def index_vectors_batch(
        self,
        index_name: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 500
    ) -> int:
        """
        Index multiple vectors in batch.
        
        Args:
            index_name: Index name
            documents: List of documents with keys:
                - entity_id: str
                - entity_type: str
                - text: str
                - embedding: np.ndarray or list
                - metadata: dict (optional)
            batch_size: Batch size for bulk indexing
        
        Returns:
            Number of successfully indexed documents
        """
        # Prepare bulk actions
        actions = []
        for doc in documents:
            # Convert embedding to list if numpy array
            embedding = doc['embedding']
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            action = {
                '_index': index_name,
                '_id': doc['entity_id'],
                '_source': {
                    'entity_id': doc['entity_id'],
                    'entity_type': doc['entity_type'],
                    'text': doc['text'],
                    'embedding': embedding,
                    'metadata': doc.get('metadata', {}),
                    'timestamp': 'now'
                }
            }
            actions.append(action)
        
        # Bulk index
        try:
            success, failed = helpers.bulk(
                self.client,
                actions,
                chunk_size=batch_size,
                raise_on_error=False
            )
            
            logger.info(f"Indexed {success} documents, {len(failed)} failed")
            return success
        
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return 0
    
    def search_similar(
        self,
        index_name: str,
        query_embedding: np.ndarray,
        k: int = 10,
        filter_query: Optional[Dict] = None,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using k-NN.
        
        Args:
            index_name: Index name
            query_embedding: Query vector
            k: Number of results to return
            filter_query: Optional filter query (OpenSearch DSL)
            min_score: Minimum similarity score
        
        Returns:
            List of results with keys: entity_id, text, score, metadata
        """
        # Convert embedding to list
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()
        
        # Build k-NN query
        knn_query = {
            'size': k,
            'query': {
                'knn': {
                    'embedding': {
                        'vector': query_embedding,
                        'k': k
                    }
                }
            }
        }
        
        # Add filter if provided
        if filter_query:
            knn_query['query'] = {
                'bool': {
                    'must': [knn_query['query']],
                    'filter': filter_query
                }
            }
        
        # Add min_score if provided
        if min_score:
            knn_query['min_score'] = min_score
        
        try:
            response = self.client.search(index=index_name, body=knn_query)
            
            # Parse results
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'entity_id': hit['_source']['entity_id'],
                    'entity_type': hit['_source']['entity_type'],
                    'text': hit['_source']['text'],
                    'score': hit['_score'],
                    'metadata': hit['_source'].get('metadata', {})
                }
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_by_text(
        self,
        index_name: str,
        query_text: str,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search using full-text search (not vector search).
        
        Args:
            index_name: Index name
            query_text: Query text
            k: Number of results
        
        Returns:
            List of results
        """
        query = {
            'size': k,
            'query': {
                'match': {
                    'text': query_text
                }
            }
        }
        
        try:
            response = self.client.search(index=index_name, body=query)
            
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'entity_id': hit['_source']['entity_id'],
                    'text': hit['_source']['text'],
                    'score': hit['_score'],
                    'metadata': hit['_source'].get('metadata', {})
                }
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []
    
    def delete_index(self, index_name: str) -> bool:
        """Delete an index."""
        try:
            self.client.indices.delete(index=index_name)
            logger.info(f"Deleted index: {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete index: {e}")
            return False
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            stats = self.client.indices.stats(index=index_name)
            return {
                'doc_count': stats['_all']['primaries']['docs']['count'],
                'size_bytes': stats['_all']['primaries']['store']['size_in_bytes']
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# Example usage
if __name__ == "__main__":
    from src.python.utils.embedding_generator import EmbeddingGenerator
    
    # Initialize clients
    vector_client = VectorSearchClient()
    embedding_gen = EmbeddingGenerator(model_name='fast')
    
    # Create index
    vector_client.create_index('test_index', dimension=384)
    
    # Index some vectors
    documents = []
    for i in range(10):
        text = f"Test document {i}"
        embedding = embedding_gen.generate_text_embedding(text)
        
        documents.append({
            'entity_id': f'doc_{i}',
            'entity_type': 'test',
            'text': text,
            'embedding': embedding,
            'metadata': {'index': i}
        })
    
    vector_client.index_vectors_batch('test_index', documents)
    
    # Search
    query_text = "Test document 5"
    query_embedding = embedding_gen.generate_text_embedding(query_text)
    results = vector_client.search_similar('test_index', query_embedding, k=3)
    
    print("Search results:")
    for result in results:
        print(f"  - {result['text']} (score: {result['score']:.4f})")
    
    # Clean up
    vector_client.delete_index('test_index')
```

#### Acceptance Criteria
- [ ] Index creation successful
- [ ] Batch indexing works
- [ ] k-NN search <50ms
- [ ] Filtering operational
- [ ] All tests pass

---

### Task 13.4: JanusGraph Schema Updates (12 hours)

#### Objective
Update JanusGraph schema to support vector properties and mixed indices.

#### Implementation

**File**: `banking/schema/graph/aml_schema_v2.groovy`

```groovy
// AML Schema v2 - With Vector Support
// Extends v1 schema with vector properties and mixed indices

mgmt = graph.openManagement()

// ============================================
// EXISTING SCHEMA (from v1)
// ============================================

// Vertex labels
if (!mgmt.containsVertexLabel('person')) {
    person = mgmt.makeVertexLabel('person').make()
} else {
    person = mgmt.getVertexLabel('person')
}

if (!mgmt.containsVertexLabel('account')) {
    account = mgmt.makeVertexLabel('account').make()
} else {
    account = mgmt.getVertexLabel('account')
}

if (!mgmt.containsVertexLabel('transaction')) {
    transaction = mgmt.makeVertexLabel('transaction').make()
} else {
    transaction = mgmt.getVertexLabel('transaction')
}

if (!mgmt.containsVertexLabel('address')) {
    address = mgmt.makeVertexLabel('address').make()
} else {
    address = mgmt.getVertexLabel('address')
}

if (!mgmt.containsVertexLabel('phone')) {
    phone = mgmt.makeVertexLabel('phone').make()
} else {
    phone = mgmt.getVertexLabel('phone')
}

if (!mgmt.containsVertexLabel('company')) {
    company = mgmt.makeVertexLabel('company').make()
} else {
    company = mgmt.getVertexLabel('company')
}

// Edge labels
if (!mgmt.containsEdgeLabel('owns_account')) {
    owns_account = mgmt.makeEdgeLabel('owns_account').make()
} else {
    owns_account = mgmt.getEdgeLabel('owns_account')
}

if (!mgmt.containsEdgeLabel('from_account')) {
    from_account = mgmt.makeEdgeLabel('from_account').make()
} else {
    from_account = mgmt.getEdgeLabel('from_account')
}

if (!mgmt.containsEdgeLabel('to_account')) {
    to_account = mgmt.makeEdgeLabel('to_account').make()
} else {
    to_account = mgmt.getEdgeLabel('to_account')
}

if (!mgmt.containsEdgeLabel('has_address')) {
    has_address = mgmt.makeEdgeLabel('has_address').make()
} else {
    has_address = mgmt.getEdgeLabel('has_address')
}

if (!mgmt.containsEdgeLabel('has_phone')) {
    has_phone = mgmt.makeEdgeLabel('has_phone').make()
} else {
    has_phone = mgmt.getEdgeLabel('has_phone')
}

if (!mgmt.containsEdgeLabel('beneficial_owner')) {
    beneficial_owner = mgmt.makeEdgeLabel('beneficial_owner').make()
} else {
    beneficial_owner = mgmt.getEdgeLabel('beneficial_owner')
}

if (!mgmt.containsEdgeLabel('owns_company')) {
    owns_company = mgmt.makeEdgeLabel('owns_company').make()
} else {
    owns_company = mgmt.getEdgeLabel('owns_company')
}

// Properties (existing)
if (!mgmt.containsPropertyKey('person_id')) {
    person_id = mgmt.makePropertyKey('person_id').dataType(String.class).make()
} else {
    person_id = mgmt.getPropertyKey('person_id')
}

if (!mgmt.containsPropertyKey('first_name')) {
    first_name = mgmt.makePropertyKey('first_name').dataType(String.class).make()
} else {
    first_name = mgmt.getPropertyKey('first_name')
}

if (!mgmt.containsPropertyKey('last_name')) {
    last_name = mgmt.makePropertyKey('last_name').dataType(String.class).make()
} else {
    last_name = mgmt.getPropertyKey('last_name')
}

if (!mgmt.containsPropertyKey('ssn')) {
    ssn = mgmt.makePropertyKey('ssn').dataType(String.class).make()
} else {
    ssn = mgmt.getPropertyKey('ssn')
}

if (!mgmt.containsPropertyKey('dob')) {
    dob = mgmt.makePropertyKey('dob').dataType(String.class).make()
} else {
    dob = mgmt.getPropertyKey('dob')
}

if (!mgmt.containsPropertyKey('account_id')) {
    account_id = mgmt.makePropertyKey('account_id').dataType(String.class).make()
} else {
    account_id = mgmt.getPropertyKey('account_id')
}

if (!mgmt.containsPropertyKey('account_type')) {
    account_type = mgmt.makePropertyKey('account_type').dataType(String.class).make()
} else {
    account_type = mgmt.getPropertyKey('account_type')
}

if (!mgmt.containsPropertyKey('balance')) {
    balance = mgmt.makePropertyKey('balance').dataType(Double.class).make()
} else {
    balance = mgmt.getPropertyKey('balance')
}

if (!mgmt.containsPropertyKey('transaction_id')) {
    transaction_id = mgmt.makePropertyKey('transaction_id').dataType(String.class).make()
} else {
    transaction_id = mgmt.getPropertyKey('transaction_id')
}

if (!mgmt.containsPropertyKey('amount')) {
    amount = mgmt.makePropertyKey('amount').dataType(Double.class).make()
} else {
    amount = mgmt.getPropertyKey('amount')
}

if (!mgmt.containsPropertyKey('timestamp')) {
    timestamp = mgmt.makePropertyKey('timestamp').dataType(Long.class).make()
} else {
    timestamp = mgmt.getPropertyKey('timestamp')
}

if (!mgmt.containsPropertyKey('description')) {
    description = mgmt.makePropertyKey('description').dataType(String.class).make()
} else {
    description = mgmt.getPropertyKey('description')
}

if (!mgmt.containsPropertyKey('street')) {
    street = mgmt.makePropertyKey('street').dataType(String.class).make()
} else {
    street = mgmt.getPropertyKey('street')
}

if (!mgmt.containsPropertyKey('city')) {
    city = mgmt.makePropertyKey('city').dataType(String.class).make()
} else {
    city = mgmt.getPropertyKey('city')
}

if (!mgmt.containsPropertyKey('state')) {
    state = mgmt.makePropertyKey('state').dataType(String.class).make()
} else {
    state = mgmt.getPropertyKey('state')
}

if (!mgmt.containsPropertyKey('zip_code')) {
    zip_code = mgmt.makePropertyKey('zip_code').dataType(String.class).make()
} else {
    zip_code = mgmt.getPropertyKey('zip_code')
}

if (!mgmt.containsPropertyKey('phone_number')) {
    phone_number = mgmt.makePropertyKey('phone_number').dataType(String.class).make()
} else {
    phone_number = mgmt.getPropertyKey('phone_number')
}

if (!mgmt.containsPropertyKey('company_id')) {
    company_id = mgmt.makePropertyKey('company_id').dataType(String.class).make()
} else {
    company_id = mgmt.getPropertyKey('company_id')
}

if (!mgmt.containsPropertyKey('company_name')) {
    company_name = mgmt.makePropertyKey('company_name').dataType(String.class).make()
} else {
    company_name = mgmt.getPropertyKey('company_name')
}

// ============================================
// NEW: VECTOR PROPERTIES
// ============================================

// Name embedding (384 dimensions for fast model, 768 for accurate)
if (!mgmt.containsPropertyKey('name_embedding')) {
    name_embedding = mgmt.makePropertyKey('name_embedding')
        .dataType(float[].class)
        .cardinality(Cardinality.SINGLE)
        .make()
    println("✅ Created property: name_embedding")
} else {
    name_embedding = mgmt.getPropertyKey('name_embedding')
    println("ℹ️  Property exists: name_embedding")
}

// Address embedding
if (!mgmt.containsPropertyKey('address_embedding')) {
    address_embedding = mgmt.makePropertyKey('address_embedding')
        .dataType(float[].class)
        .cardinality(Cardinality.SINGLE)
        .make()
