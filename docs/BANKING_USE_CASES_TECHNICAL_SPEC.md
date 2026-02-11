
# Banking Use Cases: Detailed Technical Specification Plan

**Project**: IBM HCD + JanusGraph + OpenSearch (JVector) Banking Use Cases  
**Version**: 1.0  
**Date**: 2026-01-28  
**Author**: IBM Bob (Senior Technical Leader)  
**Status**: DRAFT - Pending Approval

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Phase 5: Vector/AI Foundation](#phase-5-vectorai-foundation-weeks-13-14)
4. [Phase 6: Complete AML Use Case](#phase-6-complete-aml-use-case-week-15)
5. [Phase 7: Fraud Rings & Customer 360](#phase-7-fraud-rings--customer-360-week-16)
6. [Phase 8: Trade Surveillance & Integration](#phase-8-trade-surveillance--integration-week-17)
7. [Phase 9: Testing & Optimization](#phase-9-testing--optimization-week-18)
8. [Data Models](#data-models)
9. [API Specifications](#api-specifications)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Plan](#deployment-plan)
12. [Appendices](#appendices)

---

## Executive Summary

### Objective

Implement four mission-critical banking use cases leveraging the hybrid Graph + Vector + AI architecture:
1. Anti-Money Laundering (AML) Network Detection
2. Fraud Rings and Insider Fraud Detection
3. 360° Customer Insights and Personalization
4. Trade Surveillance and Compliance

### Scope

- **Duration**: 6 weeks (Weeks 13-18)
- **Effort**: 240 hours
- **Team**: 1 lead engineer + optional ML engineer
- **Deliverables**: 4 complete use cases, vector/AI integration, unified demo, production deployment

### Technology Stack

**Core Components:**
- JanusGraph 1.0.0 (Graph Database)
- HCD 1.2.3 / Cassandra (Storage Backend)
- OpenSearch 2.11+ with JVector plugin (Vector Search)
- Python 3.8-3.11 (Client & ML)

**New ML/AI Components:**
- sentence-transformers 2.3.1 (Text embeddings)
- PyTorch 2.1.0 (Deep learning framework)
- Transformers 4.36.0 (NLP models)
- FAISS 1.7.4 (Vector similarity search)
- scikit-learn 1.4.0 (ML utilities)

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Banking    │  │   Jupyter    │  │  Streamlit   │          │
│  │   Use Cases  │  │  Notebooks   │  │  Dashboard   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      ML/AI Processing Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Embedding   │  │   Vector     │  │  Semantic    │          │
│  │  Generator   │  │   Search     │  │   Matching   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Data Integration Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  JanusGraph  │←→│  OpenSearch  │←→│    Redis     │          │
│  │   (Graph)    │  │   (Vector)   │  │   (Cache)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Storage Layer                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              HCD/Cassandra Cluster                       │   │
│  │  - Graph data (vertices, edges, properties)              │   │
│  │  - Vector indices (embeddings)                           │   │
│  │  - Time-series data (transactions, events)               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
┌─────────────┐
│   Raw Data  │ (Transactions, Communications, etc.)
└──────┬──────┘
       ↓
┌──────────────────────────────────────────────────────┐
│              Data Ingestion Pipeline                  │
│  1. Validation & Sanitization                        │
│  2. Entity Extraction                                │
│  3. Relationship Mapping                             │
└──────┬───────────────────────────────────────────────┘
       ↓
┌──────────────────┐         ┌──────────────────┐
│  Graph Storage   │         │  Text Extraction │
│  (JanusGraph)    │         │  (for embedding) │
└──────┬───────────┘         └────────┬─────────┘
       │                              ↓
       │                     ┌──────────────────┐
       │                     │  ML Model        │
       │                     │  (Transformers)  │
       │                     └────────┬─────────┘
       │                              ↓
       │                     ┌──────────────────┐
       │                     │  Vector Index    │
       │                     │  (OpenSearch)    │
       │                     └────────┬─────────┘
       ↓                              ↓
┌──────────────────────────────────────────────────────┐
│              Query Processing Layer                   │
│  - Gremlin Traversals (Graph)                        │
│  - k-NN Search (Vector)                              │
│  - Hybrid Queries (Graph + Vector)                   │
└──────┬───────────────────────────────────────────────┘
       ↓
┌──────────────────┐
│  Results/Alerts  │
└──────────────────┘
```

---

## Phase 5: Vector/AI Foundation (Weeks 13-14)

### Week 13: ML Infrastructure Setup

#### 13.1 Update Dependencies (4 hours)

**Objective**: Install all required ML/AI libraries

**Files to Modify:**
1. `banking/requirements.txt`
2. `docker/jupyter/environment.yml`
3. `requirements.txt` (root)

**Detailed Changes:**

```python
# banking/requirements.txt - ADD THESE LINES

# ============================================
# ML/AI Dependencies (Phase 5)
# ============================================

# Core ML Framework
torch==2.1.0                    # PyTorch deep learning
torchvision==0.16.0            # Computer vision utilities

# NLP & Embeddings
sentence-transformers==2.3.1    # Text embedding models
transformers==4.36.0            # Hugging Face transformers
tokenizers==0.15.0             # Fast tokenization

# Vector Search
faiss-cpu==1.7.4               # Facebook AI Similarity Search
hnswlib==0.8.0                 # Hierarchical NSW for k-NN

# ML Utilities
scikit-learn==1.4.0            # Machine learning algorithms
scipy==1.11.4                  # Scientific computing
joblib==1.3.2                  # Model serialization

# NLP Processing
spacy==3.7.2                   # Advanced NLP
nltk==3.8.1                    # Natural language toolkit

# Model Management
huggingface-hub==0.20.0        # Model repository access
safetensors==0.4.1             # Safe tensor serialization

# Performance
accelerate==0.25.0             # Distributed training
```

**Docker Configuration:**

```yaml
# docker/jupyter/environment.yml - ADD TO dependencies

dependencies:
  # ... existing dependencies ...
  
  # ML/AI Stack
  - pytorch=2.1.0
  - torchvision=0.16.0
  - sentence-transformers=2.3.1
  - transformers=4.36.0
  - faiss-cpu=1.7.4
  - scikit-learn=1.4.0
  - spacy=3.7.2
  
  # Pip dependencies
  - pip:
    - hnswlib==0.8.0
    - accelerate==0.25.0
```

**Build Commands:**

```bash
# Rebuild Docker images
docker-compose build jupyter

# Update local environment
pip install -r banking/requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Verify installation
python -c "import torch; import sentence_transformers; print('ML stack ready')"
```

**Acceptance Criteria:**
- ✅ All packages install without errors
- ✅ PyTorch can detect CPU (or GPU if available)
- ✅ sentence-transformers can load a model
- ✅ Docker image builds successfully

---

#### 13.2 Create Embedding Utilities (8 hours)

**Objective**: Build reusable utilities for generating embeddings

**File**: `src/python/utils/embedding_generator.py`

**Complete Implementation:**

```python
"""
Embedding Generation Utilities

Provides functions to generate vector embeddings for text, behavioral patterns,
and other data types used in banking use cases.

Author: IBM Bob
Date: 2026-01-28
"""

import logging
from typing import List, Dict, Any, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from functools import lru_cache

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generate embeddings for various data types.
    
    Supports:
    - Text embeddings (names, addresses, communications)
    - Behavioral embeddings (transaction patterns)
    - Multi-modal embeddings (combining text + numerical features)
    """
    
    # Model configurations
    MODELS = {
        'fast': 'all-MiniLM-L6-v2',      # 384 dims, fast
        'accurate': 'all-mpnet-base-v2',  # 768 dims, accurate
        'multilingual': 'paraphrase-multilingual-MiniLM-L12-v2'  # 384 dims
    }
    
    def __init__(
        self,
        model_name: str = 'fast',
        device: Optional[str] = None,
        cache_size: int = 1000
    ):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Model to use ('fast', 'accurate', 'multilingual')
            device: Device to use ('cpu', 'cuda', or None for auto)
            cache_size: Number of embeddings to cache
        """
        self.model_name = model_name
        self.model_id = self.MODELS.get(model_name, model_name)
        
        # Auto-detect device
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        
        # Load model
        logger.info(f"Loading embedding model: {self.model_id} on {device}")
        self.model = SentenceTransformer(self.model_id, device=device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"Model loaded: {self.embedding_dim} dimensions")
        
        # Cache for repeated embeddings
        self._cache = {}
        self._cache_size = cache_size
    
    def generate_text_embedding(
        self,
        text: str,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Input text
            normalize: Whether to L2-normalize the embedding
        
        Returns:
            Embedding vector (numpy array)
        """
        # Check cache
        cache_key = f"text:{text}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Generate embedding
        embedding = self.model.encode(
            text,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )
        
        # Cache result
        if len(self._cache) < self._cache_size:
            self._cache[cache_key] = embedding
        
        return embedding
    
    def generate_text_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts (batched for efficiency).
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            normalize: Whether to L2-normalize embeddings
            show_progress: Show progress bar
        
        Returns:
            Array of embeddings (shape: [n_texts, embedding_dim])
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress
        )
        
        return embeddings
    
    def generate_name_embedding(
        self,
        first_name: str,
        last_name: str,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embedding for a person's name.
        
        Args:
            first_name: First name
            last_name: Last name
            normalize: Whether to normalize
        
        Returns:
            Name embedding
        """
        # Combine names with space
        full_name = f"{first_name} {last_name}".strip()
        return self.generate_text_embedding(full_name, normalize)
    
    def generate_address_embedding(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embedding for an address.
        
        Args:
            street: Street address
            city: City
            state: State
            zip_code: ZIP code
            normalize: Whether to normalize
        
        Returns:
            Address embedding
        """
        # Combine address components
        address = f"{street}, {city}, {state} {zip_code}"
        return self.generate_text_embedding(address, normalize)
    
    def generate_behavioral_embedding(
        self,
        features: Dict[str, float],
        feature_order: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        Generate embedding from behavioral features.
        
        Args:
            features: Dictionary of feature name -> value
            feature_order: Optional fixed order for features
        
        Returns:
            Behavioral embedding
        """
        # Convert features to ordered array
        if feature_order is None:
            feature_order = sorted(features.keys())
        
        feature_vector = np.array([
            features.get(key, 0.0) for key in feature_order
        ])
        
        # Normalize
        norm = np.linalg.norm(feature_vector)
        if norm > 0:
            feature_vector = feature_vector / norm
        
        return feature_vector
    
    def generate_transaction_sequence_embedding(
        self,
        transactions: List[Dict[str, Any]],
        max_length: int = 50
    ) -> np.ndarray:
        """
        Generate embedding for a sequence of transactions.
        
        Args:
            transactions: List of transaction dictionaries
            max_length: Maximum sequence length
        
        Returns:
            Sequence embedding
        """
        # Extract features from each transaction
        features = []
        for txn in transactions[:max_length]:
            # Create feature vector: [amount, hour, day_of_week, ...]
            feature = [
                txn.get('amount', 0.0),
                txn.get('hour', 0) / 24.0,  # Normalize to [0, 1]
                txn.get('day_of_week', 0) / 7.0,
                1.0 if txn.get('type') == 'deposit' else 0.0,
                1.0 if txn.get('type') == 'withdrawal' else 0.0,
            ]
            features.append(feature)
        
        # Pad if needed
        while len(features) < max_length:
            features.append([0.0] * len(features[0]))
        
        # Flatten to 1D vector
        embedding = np.array(features).flatten()
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
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
            # Cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0
        
        elif metric == 'euclidean':
            # Euclidean distance (inverted to similarity)
            distance = np.linalg.norm(embedding1 - embedding2)
            return 1.0 / (1.0 + distance)
        
        elif metric == 'dot':
            # Dot product
            return np.dot(embedding1, embedding2)
        
        else:
            raise ValueError(f"Unknown metric: {metric}")
    
    def find_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: np.ndarray,
        top_k: int = 10,
        metric: str = 'cosine'
    ) -> List[tuple]:
        """
        Find most similar embeddings to query.
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: Array of candidate embeddings
            top_k: Number of results to return
            metric: Similarity metric
        
        Returns:
            List of (index, similarity_score) tuples
        """
        # Compute similarities
        similarities = []
        for i, candidate in enumerate(candidate_embeddings):
            sim = self.compute_similarity(query_embedding, candidate, metric)
            similarities.append((i, sim))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def clear_cache(self):
        """Clear embedding cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            'model_name': self.model_name,
            'model_id': self.model_id,
            'embedding_dim': self.embedding_dim,
            'device': self.device,
            'cache_size': len(self._cache)
        }


# Singleton instance for easy access
_default_generator: Optional[EmbeddingGenerator] = None


def get_embedding_generator(
    model_name: str = 'fast',
    force_reload: bool = False
) -> EmbeddingGenerator:
    """
    Get or create the default embedding generator.
    
    Args:
        model_name: Model to use
        force_reload: Force reload of model
    
    Returns:
        EmbeddingGenerator instance
    """
    global _default_generator
    
    if _default_generator is None or force_reload:
        _default_generator = EmbeddingGenerator(model_name=model_name)
    
    return _default_generator


# Convenience functions
def embed_text(text: str) -> np.ndarray:
    """Generate embedding for text (convenience function)."""
    generator = get_embedding_generator()
    return generator.generate_text_embedding(text)


def embed_texts(texts: List[str]) -> np.ndarray:
    """Generate embeddings for multiple texts (convenience function)."""
    generator = get_embedding_generator()
    return generator.generate_text_embeddings_batch(texts)


def embed_name(first_name: str, last_name: str) -> np.ndarray:
    """Generate embedding for name (convenience function)."""
    generator = get_embedding_generator()
    return generator.generate_name_embedding(first_name, last_name)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize generator
    generator = EmbeddingGenerator(model_name='fast')
    
    # Test text embedding
    text = "John Smith"
    embedding = generator.generate_text_embedding(text)
    print(f"Text: {text}")
    print(f"Embedding shape: {embedding.shape}")
    print(f"Embedding (first 5): {embedding[:5]}")
    
    # Test batch embedding
    texts = ["John Smith", "Jon Smyth", "Jane Doe"]
    embeddings = generator.generate_text_embeddings_batch(texts)
    print(f"\nBatch embeddings shape: {embeddings.shape}")
    
    # Test similarity
    sim = generator.compute_similarity(embeddings[0], embeddings[1])
    print(f"\nSimilarity between '{texts[0]}' and '{texts[1]}': {sim:.4f}")
    
    # Test name embedding
    name_emb = generator.generate_name_embedding("John", "Smith")
    print(f"\nName embedding shape: {name_emb.shape}")
    
    # Model info
    info = generator.get_model_info()
    print(f"\nModel info: {info}")

# Made with IBM Bob
```

**Testing Script**: `tests/test_embedding_generator.py`

```python
"""
Tests for embedding generator.
"""

import pytest
import numpy as np
from src.python.utils.embedding_generator import (
    EmbeddingGenerator,
    embed_text,
    embed_texts,
    embed_name
)


def test_embedding_generator_init():
    """Test generator initialization."""
    generator = EmbeddingGenerator(model_name='fast')
    assert generator.embedding_dim == 384
    assert generator.device in ['cpu', 'cuda']


def test_text_embedding():
    """Test single text embedding."""
    generator = EmbeddingGenerator(model_name='fast')
    embedding = generator.generate_text_embedding("test text")
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)
    assert np.abs(np.linalg.norm(embedding) - 1.0) < 0.01  # Normalized


def test_batch_embedding():
    """Test batch text embedding."""
    generator = EmbeddingGenerator(model_name='fast')
    texts = ["text 1", "text 2", "text 3"]
    embeddings = generator.generate_text_embeddings_batch(texts)
    
    assert embeddings.shape == (3, 384)


def test_name_embedding():
    """Test name embedding."""
    generator = EmbeddingGenerator(model_name='fast')
    embedding = generator.generate_name_embedding("John", "Smith")
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)


def test_similarity():
    """Test similarity computation."""
    generator = EmbeddingGenerator(model_name='fast')
    
    emb1 = generator.generate_text_embedding("John Smith")
    emb2 = generator.generate_text_embedding("Jon Smyth")
    emb3 = generator.generate_text_embedding("Jane Doe")
    
    sim_similar = generator.compute_similarity(emb1, emb2)
    sim_different = generator.compute_similarity(emb1, emb3)
    
    # Similar names should have higher similarity
    assert sim_similar > sim_different
    assert 0 <= sim_similar <= 1
    assert 0 <= sim_different <= 1


def test_convenience_functions():
    """Test convenience functions."""
    embedding = embed_text("test")
    assert isinstance(embedding, np.ndarray)
    
    embeddings = embed_texts(["test1", "test2"])
    assert embeddings.shape[0] == 2
    
    name_emb = embed_name("John", "Smith")
    assert isinstance(name_emb, np.ndarray)


def test_cache():
    """Test embedding cache."""
    generator = EmbeddingGenerator(model_name='fast', cache_size=10)
    
    # Generate same embedding twice
    text = "cached text"
    emb1 = generator.generate_text_embedding(text)
    emb2 = generator.generate_text_embedding(text)
    
    # Should be identical (from cache)
    assert np.array_equal(emb1, emb2)
    
    # Clear cache
    generator.clear_cache()
    assert len(generator._cache) == 0
```

**Acceptance Criteria:**
- ✅ Can generate embeddings for text
- ✅ Can generate embeddings in batches
- ✅ Can compute similarity between embeddings
- ✅ All tests pass
- ✅ Documentation complete

---

#### 13.3 OpenSearch JVector Integration (12 hours)

**Objective**: Configure OpenSearch with JVector plugin for vector search

**Step 1: Enable JVector Plugin**

```bash
# Install JVector plugin in OpenSearch
docker exec opensearch /usr/share/opensearch/bin/opensearch-plugin install \
  https://github.com/opensearch-project/k-NN/releases/download/2.11.0.0/opensearch-knn-2.11.0.0.zip

# Restart OpenSearch
docker-compose restart opensearch
```

**Step 2: Create Vector Index Template**

File: `config/opensearch/vector_index_template.json`

```json
{
  "index_patterns": ["banking-vectors-*"],
  "template": {
    "settings": {
      "index": {
        "knn": true,
        "knn.algo_param.ef_search": 100,
        "number_of_shards": 3,
        "number_of_replicas": 1
      }
    },
    "mappings": {
      "properties": {
        "entity_id": {
          "type": "keyword"
        },
        "entity_type": {
          "type": "keyword"
        },
        "text": {
          "type": "text"
        },
        "embedding": {
          "type": "knn_vector",
          "dimension": 384,
          "method": {
            "name": "hnsw",
            "space_type": "cosinesimil",
            "engine": "nmslib",
            "parameters": {
              "ef_construction": 128,
              "m": 24
            }
          }
        },
        "metadata": {
          "type": "object",
          "enabled": true
        },
        "timestamp": {
          "type": "date"
        }
      }
    }
  }
}
```

**Step 3: Python Integration**

File: `src/python/utils/vector_search.py`

```python
"""
Vector Search Integration with OpenSearch JVector

Provides functions to index and search vector embeddings in OpenSearch.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from opensearchpy import OpenSearch, helpers
from datetime import datetime

logger = logging.getLogger(__name__)


class VectorSearchClient:
    """Client for vector search operations in OpenSearch."""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 9200,
        index_prefix: str = 'banking-vectors'
    ):
        """
        Initialize vector search client.
        
        Args:
            host: OpenSearch host
            port: OpenSearch port
            index_prefix: Prefix for vector indices
        """
        self.client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_compress=True,
            use_ssl=False,  # Set to True in production
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False
        )
        self.index_prefix = index_prefix
        logger.info(f"Vector search client initialized: {host}:{port}")
    
    def create_index(self, index_name: str, dimension: int = 384):
        """
        Create a vector index.
        
        Args:
            index_name: Name of index
            dimension: Embedding dimension
        """
        full_index_name = f"{self.index_prefix}-{index_name}"
        
        if self.client.indices.exists(index=full_index_name):
            logger.info(f"Index already exists: {full_index_name}")
            return
        
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100,
                    "number_of_shards": 3,
                    "number_of_replicas": 1
                }
            },
            "mappings": {
                "properties": {
                    "entity_id": {"type": "keyword"},
                    "entity_type": {"type": "keyword"},
                    "text": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": dimension,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 24
                            }
                        }
                    },
                    "metadata": {"type": "object", "enabled": True},
                    "timestamp": {"type": "date"}
                }
            }
        }
        
        self.client.indices.create(index=full_index_name, body=index_body)
        logger.info(f"Created vector index: {full_index_name}")
    
    def index_vector(
        self,
        index_name: str,
        entity_id: str,
        entity_type: str,
        text: str,
        embedding: np.ndarray,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Index a single vector.
        
        Args:
            index_name: Index name
            entity_id: Entity identifier
            entity_type: Type of entity
            text: Original text
            embedding: Vector embedding
            metadata: Additional metadata
        
        Returns:
            Document ID
        """
        full_index_name = f"{self.index_prefix}-{index_name}"
        
        document = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "text": text,
            "embedding": embedding.tolist(),
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        response = self.client.index(
            index=full_index_name,
            body=document,
            id=entity_id
        )
        
        return response['_id']
    
    def index_vectors_batch(
        self,
        index_name: str,
        documents: List[Dict[str, Any]]
    ) -> int:
        """
        Index multiple vectors in batch.
        
        Args:
            index_name: Index name
            documents: List of documents to index
        
        Returns:
            Number of documents indexed
        """
        full_index_name = f"{self.index_prefix}-{index_name}"
        
        actions = []
        for doc in documents:
            action = {
                "_index": full_index_name,
                "_id": doc['entity_id'],
                "_source": {
                    "entity_id": doc['entity_id'],
                    "entity_type": doc['entity_type'],
                    "text": doc['text'],
                    "embedding": doc['embedding'].tolist() if isinstance(doc['embedding'], np.ndarray) else doc['embedding'],
                    "metadata": doc.get('metadata', {}),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            actions.append(action)
        
        success, failed = helpers.bulk(self.client, actions)
        logger.info(f"Indexed {success} documents, {failed} failed")
        
        return success
    
    def search_similar(
        self,
        index_name: str,
        query_embedding: np.ndarray,
        k: int = 10,
        filter_query: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            index_name: Index name
            query_embedding: Query vector
            k: Number of results
            filter_query: Optional filter query
        
        Returns:
            List of similar documents with scores
        """
        full_index_name = f"{self.index_prefix}-{index_name}"
        
        query = {
            "size": k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding.tolist(),
                        "k": k
                    }
                }
            }
        }
        
        # Add filter if provided
        if filter_query:
            query["query"] = {
                "bool": {
                    "must": [query["query"]],
                    "filter": filter_query
                }
            }
        
        response = self.client.search(index=full_index_name, body=query)
        
        results = []
        for hit in response['hits']['hits']:
            results.append({
                'entity_id': hit['_source']['entity_id'],
                'entity_type': hit['_source']['entity_type'],
                'text': hit['_source']['text'],
                'score': hit['_score'],
                'metadata': hit['_source'].get('metadata', {})
            })
        
        return results
    
    def delete_index(self, index_name: str):
        """Delete a vector index."""
        full_index_name = f"{self.index_prefix}-{index_name}"
        if self.client.indices.exists(index=full_index_name):
            self.client.indices.delete(index=full_index_name)
            logger.info(f"Deleted index: {full_index_name}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from embedding_generator import EmbeddingGenerator
    
    # Initialize clients
    vector_client = VectorSearchClient()
    embedding_gen = EmbeddingGenerator(model_name='fast')
    
    # Create index
    vector_client.create_index('test', dimension=384)
    
    # Index some vectors
    texts = [
        "John Smith",
        "Jon Smyth",
        "Jane Doe",
        "Bob Johnson"
    ]
    
    embeddings = embedding_gen.generate_text_embeddings_batch(texts)
    
    documents = []
    for i, (text, embedding) in enumerate(zip(texts, embeddings)):
        documents.append({
            'entity_id': f'person_{i}',
            'entity_type': 'person',
            'text': text,
            'embedding': embedding
        })
    
    vector_client.index_vectors_batch('test', documents)
    
    # Search for similar
    query_text = "John Smyth"
    query_embedding = embedding_gen.generate_text_embedding(query_text)
    
    results = vector_client.search_similar('test', query_embedding, k=3)
    
    print(f"\nQuery: {query_text}")
    print("Similar entities:")
    for result in results:
        print(f"  - {result['text']} (score: {result['score']:.4f})")

# Made with IBM Bob
```

**Acceptance Criteria:**
- ✅ JVector plugin installed
- ✅ Vector indices created
- ✅ Can index vectors
- ✅ Can search for similar vectors
- ✅ Performance acceptable (<100ms for k-NN)

---

#### 13.4 JanusGraph Mixed Index Configuration (8 hours)

**Objective**: Enable full-text and vector search in JanusGraph

**File**: `banking/schema/graph/aml_schema_v2.groovy`

```groovy
// AML Banking Schema v2 - With Vector Support
// Enables mixed indices for text and vector search

mgmt = graph.openManagement()

// ... (existing vertex labels and properties) ...

// ============================================
// VECTOR PROPERTIES (NEW)
// ============================================

// Name embedding (384 dimensions for fast model)
name_embedding = mgmt.makePropertyKey('name_embedding')
    .dataType(float[].class)
    .cardinality(Cardinality.SINGLE)
    .make()

// Address embedding
address_embedding = mgmt.makePropertyKey('address_embedding')
    .dataType(float[].class)
    .cardinality(Cardinality.SINGLE)
    .make()

// Communication text embedding (for trade surveillance)
communication_embedding = mgmt.makePropertyKey('communication_embedding')
    .dataType(float[].class)
    .cardinality(Cardinality.SINGLE)
    .make()

// ============================================
// MIXED INDICES (ENABLED)
// ============================================

// Text search on person names
mgmt.buildIndex('personByName', Vertex.class)
    .addKey(first_name, Mapping.STRING.asParameter())
    .addKey(last_name, Mapping.STRING.asParameter())
    .indexOnly(person)
    .buildMixedIndex("search")

// Text search on addresses
mgmt.buildIndex('addressByText', Vertex.class)
    .addKey(street, Mapping.TEXT.asParameter())
    .addKey(city, Mapping.STRING.asParameter())
    .indexOnly(address)
    .buildMixedIndex("search")

// Vector search on name embeddings
// Note: Vector search is handled by OpenSearch separately
// These properties are stored in JanusGraph but queried via OpenSearch

mgmt.commit()

println("✅ AML Schema v2 created with vector support")
```

**Integration Script**: `banking/scripts/sync_vectors_to_opensearch.py`

```python
"""
Sync vector embeddings from JanusGraph to OpenSearch.

This script reads entities from JanusGraph, generates embeddings,
and indexes them in OpenSearch for vector search.
"""

import logging
from gremlin_python.driver import client
from src.python.utils.embedding_generator import EmbeddingGenerator
from src.python.utils.vector_search import VectorSearchClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sync_person_embeddings():
    """Sync person name embeddings to OpenSearch."""
    
    # Initialize clients
    gremlin_client = client.Client(
        'ws://localhost:18182/gremlin',
        'g'
    )
    embedding_gen = EmbeddingGenerator(model_name='fast')
    vector_client = VectorSearchClient()
    
    # Create index
    vector_client.create_index('persons', dimension=384)
    
    # Fetch all persons from JanusGraph
    query = "g.V().hasLabel('person').valueMap(true)"
    result_set = gremlin_client.submit(query)
    persons = result_set.all().result()
    
    logger.info(f"Found {len(persons)} persons to sync")
    
    # Generate embeddings and index
    documents = []
    for person in persons:
        person_id = str(person['id'])
        first_name = person.get('first_name', [''])[0]
        last_name = person.get('last_name', [''])[0]
        
        # Generate embedding
        embedding = embedding_gen.generate_name_embedding(first_name, last_name)
        
        documents.append({
            'entity_id': person_id,
            'entity_type': 'person',
            'text': f"{first_name} {last_name}",
            'embedding': embedding,
            'metadata': {
                'first_name': first_name,
                'last_name': last_name
            }
        })
        
        # Batch index every 100 documents
        if len(documents) >= 100:
            vector_client.index_vectors_batch('persons', documents)
            documents = []
    
    # Index remaining
    if documents:
        vector_client.index_vectors_batch('persons', documents)
    
    logger.info("Person embeddings synced successfully")
    
    gremlin_client.close()


if __name__ == "__main__":
    sync_person_embeddings()
```

**Acceptance Criteria:**
- ✅ Mixed indices configured
- ✅ Vector properties added to schema
- ✅ Sync script works
- ✅ Can query both graph and vectors

---

### Week 14: Vector Search Proof of Concept

#### 14.1 AML Semantic Matching (12 hours)

**Objective**: Implement fuzzy name matching for AML

**Notebook**: `banking/notebooks/02_AML_Semantic_Matching.ipynb`

```python
# Cell 1: Setup
import sys
sys.path.append('../..')

from gremlin_python.driver import client
from src.python.utils.embedding_generator import EmbeddingGenerator
from src.python.utils.vector_search import VectorSearchClient
import pandas as pd
import numpy as np

# Initialize clients
gremlin_client = client.Client('ws://localhost:18182/gremlin', 'g')
embedding_gen = EmbeddingGenerator(model_name='fast')
vector_client = VectorSearchClient()

print("✅ Clients initialized")

# Cell 2: Load Sample Data
# Fetch persons from graph
query = "g.V().hasLabel('person').limit(100).valueMap(true)"
result_set = gremlin_client.submit(query)
persons = result_set.all().result()

df = pd.DataFrame([
    {
        'id': p['id'],
        'first_name': p.get('first_name', [''])[0],
        'last_name': p.get('last_name', [''])[0],
        'full_name': f"{p.get('first_name', [''])[0]} {p.get('last_name', [''])[0]}"
    }
    for p in persons
])

print(f"Loaded {len(df)} persons")
df.head()

# Cell 3: Generate and Index Embeddings
documents = []
for _, row in df.iterrows():
    embedding = embedding_gen.generate_name_embedding(
        row['first_name'],
        row['last_name']
    )
    
    documents.append({
        'entity_id': str(row['id']),
        'entity_type': 'person',
        'text': row['full_name'],
        'embedding': embedding,
        'metadata': {
            'first_name': row['first_name'],
            'last_name': row['last_name']
        }
    })

# Create index and load vectors
vector_client.create_index('persons', dimension=384)
vector_client.index_vectors_batch('persons', documents)

print(f"✅ Indexed {len(documents)} person embeddings")

# Cell 4: Fuzzy Name Matching Demo
# Test case: Find matches for misspelled/variant names
test_names = [
    ("John", "Smith"),      # Exact match
    ("Jon", "Smyth"),       # Misspelling
    ("J.", "Smith"),        # Abbreviated
    ("John", "Smythe"),     # Variant spelling
]

for first, last in test_names:
    print(f"\n🔍 Searching for: {first} {last}")
    
    # Generate query embedding
    query_embedding = embedding_gen.generate_name_embedding(first, last)
    
    # Search for similar
    results = vector_client.search_similar('persons', query_embedding, k=5)
    
    print("Top matches:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['text']} (similarity: {result['score']:.4f})")

# Cell 5: Sanctions List Screening
# Simulate sanctions list
sanctions_list = [
    "Vladimir Putin",
    "Kim Jong Un",
    "Bashar al-Assad"
]

# Index sanctions
sanctions_docs = []
for i, name in enumerate(sanctions_list):
    parts = name.split()
    first_name = parts[0]
    last_name = " ".join(parts[1:])
    
    embedding = embedding_gen.generate_name_embedding(first_name, last_name)
    
    sanctions_docs.append({
        'entity_id': f'sanction_{i}',
        'entity_type': 'sanctioned_person',
        'text': name,
        'embedding': embedding,
        'metadata': {'list': 'OFAC'}
    })

vector_client.create_index('sanctions', dimension=384)
vector_client.index_vectors_batch('sanctions', sanctions_docs)

print("✅ Sanctions list indexed")

# Cell 6: Screen Customers Against Sanctions
# Check if any customers are similar to sanctioned entities
threshold = 0.85  # High similarity threshold

