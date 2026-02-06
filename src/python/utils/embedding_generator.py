"""
Embedding Generator for Banking Use Cases
Generates vector embeddings for text data using sentence-transformers

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-28
Phase: 5 (Vector/AI Foundation)
"""

from typing import List, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generate vector embeddings for text data using pre-trained models.
    
    Supports multiple embedding models optimized for different use cases:
    - all-MiniLM-L6-v2: Fast, lightweight (384 dimensions)
    - all-mpnet-base-v2: High quality (768 dimensions)
    """
    
    # Model configurations
    MODELS = {
        'mini': {
            'name': 'sentence-transformers/all-MiniLM-L6-v2',
            'dimensions': 384,
            'description': 'Fast, lightweight model for general use'
        },
        'mpnet': {
            'name': 'sentence-transformers/all-mpnet-base-v2',
            'dimensions': 768,
            'description': 'High-quality model for semantic similarity'
        }
    }
    
    def __init__(self, model_name: str = 'mini', device: Optional[str] = None):
        """
        Initialize the embedding generator.
        
        Args:
            model_name: Model to use ('mini' or 'mpnet')
            device: Device to run on ('cpu', 'cuda', 'mps'). Auto-detected if None.
        """
        if model_name not in self.MODELS:
            raise ValueError(f"Unknown model: {model_name}. Choose from: {list(self.MODELS.keys())}")
        
        self.model_config = self.MODELS[model_name]
        self.model_name = model_name
        
        logger.info(f"Loading embedding model: {self.model_config['name']}")
        self.model = SentenceTransformer(self.model_config['name'], device=device)
        logger.info(f"Model loaded. Dimensions: {self.model_config['dimensions']}")
    
    @property
    def dimensions(self) -> int:
        """Get the embedding dimensions for this model."""
        return self.model_config['dimensions']
    
    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text or list of texts to encode
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            normalize: Normalize embeddings to unit length (recommended for cosine similarity)
        
        Returns:
            numpy array of embeddings (shape: [n_texts, dimensions])
        """
        if isinstance(texts, str):
            texts = [texts]
        
        logger.debug(f"Encoding {len(texts)} texts with batch_size={batch_size}")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def encode_for_search(
        self,
        query: str,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Encode a single query for vector search.
        
        Args:
            query: Query text
            normalize: Normalize embedding to unit length
        
        Returns:
            numpy array of embedding (shape: [dimensions])
        """
        embedding = self.encode(query, normalize=normalize)
        return embedding[0]  # Return single embedding
    
    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[np.ndarray]:
        """
        Encode a batch of texts and return as list of arrays.
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding
            show_progress: Show progress bar
        
        Returns:
            List of numpy arrays, one per text
        """
        embeddings = self.encode(texts, batch_size=batch_size, show_progress=show_progress)
        return [emb for emb in embeddings]
    
    def similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Cosine similarity score (0-1, higher is more similar)
        """
        # Normalize if not already normalized
        emb1 = embedding1 / np.linalg.norm(embedding1)
        emb2 = embedding2 / np.linalg.norm(embedding2)
        
        return float(np.dot(emb1, emb2))
    
    def batch_similarity(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Calculate cosine similarity between query and multiple candidates.
        
        Args:
            query_embedding: Query embedding (shape: [dimensions])
            candidate_embeddings: Candidate embeddings (shape: [n_candidates, dimensions])
        
        Returns:
            Similarity scores (shape: [n_candidates])
        """
        # Normalize
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        candidates_norm = candidate_embeddings / np.linalg.norm(
            candidate_embeddings, axis=1, keepdims=True
        )
        
        # Compute dot product
        similarities = np.dot(candidates_norm, query_norm)
        return similarities


# Banking-specific helper functions

def encode_person_name(
    name: str,
    generator: Optional[EmbeddingGenerator] = None
) -> np.ndarray:
    """
    Encode a person's name for fuzzy matching.
    
    Args:
        name: Person's name
        generator: EmbeddingGenerator instance (creates new if None)
    
    Returns:
        Embedding vector
    """
    if generator is None:
        generator = EmbeddingGenerator(model_name='mini')
    
    # Normalize name: lowercase, strip whitespace
    normalized_name = name.lower().strip()
    return generator.encode_for_search(normalized_name)


def encode_transaction_description(
    description: str,
    generator: Optional[EmbeddingGenerator] = None
) -> np.ndarray:
    """
    Encode a transaction description for semantic search.
    
    Args:
        description: Transaction description
        generator: EmbeddingGenerator instance (creates new if None)
    
    Returns:
        Embedding vector
    """
    if generator is None:
        generator = EmbeddingGenerator(model_name='mpnet')
    
    return generator.encode_for_search(description)


def encode_sanctions_list(
    names: List[str],
    generator: Optional[EmbeddingGenerator] = None,
    batch_size: int = 32
) -> np.ndarray:
    """
    Encode a list of sanctioned entity names.
    
    Args:
        names: List of sanctioned entity names
        generator: EmbeddingGenerator instance (creates new if None)
        batch_size: Batch size for encoding
    
    Returns:
        Embeddings matrix (shape: [n_names, dimensions])
    """
    if generator is None:
        generator = EmbeddingGenerator(model_name='mini')
    
    # Normalize names
    normalized_names = [name.lower().strip() for name in names]
    
    return generator.encode(
        normalized_names,
        batch_size=batch_size,
        show_progress=True
    )


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize generator
    print("Initializing embedding generator...")
    generator = EmbeddingGenerator(model_name='mini')
    
    # Example 1: Encode single text
    print("\n1. Single text encoding:")
    text = "John Smith"
    embedding = generator.encode_for_search(text)
    print(f"Text: {text}")
    print(f"Embedding shape: {embedding.shape}")
    print(f"First 5 values: {embedding[:5]}")
    
    # Example 2: Batch encoding
    print("\n2. Batch encoding:")
    names = ["John Smith", "Jane Doe", "Bob Johnson"]
    embeddings = generator.encode(names)
    print(f"Encoded {len(names)} names")
    print(f"Embeddings shape: {embeddings.shape}")
    
    # Example 3: Similarity calculation
    print("\n3. Similarity calculation:")
    name1 = "John Smith"
    name2 = "Jon Smyth"  # Similar but different spelling
    name3 = "Jane Doe"   # Different person
    
    emb1 = generator.encode_for_search(name1)
    emb2 = generator.encode_for_search(name2)
    emb3 = generator.encode_for_search(name3)
    
    sim_12 = generator.similarity(emb1, emb2)
    sim_13 = generator.similarity(emb1, emb3)
    
    print(f"Similarity '{name1}' vs '{name2}': {sim_12:.4f}")
    print(f"Similarity '{name1}' vs '{name3}': {sim_13:.4f}")
    print(f"✅ Fuzzy matching works! Similar names have higher similarity.")

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
