"""
Text Embeddings Module for Semantic MNPI Detection
===================================================

Generates vector embeddings for Material Non-Public Information (MNPI) detection
using sentence-transformers. Enables semantic similarity search in OpenSearch.

Key Features:
- MNPI keyword embedding generation
- Communication text embedding
- Batch processing for efficiency
- Caching for performance

Author: Banking Compliance Platform Team
Date: 2026-04-07
Sprint: 1.4 - Vector Search Integration
"""

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generate vector embeddings for MNPI detection.
    
    Uses sentence-transformers for high-quality semantic embeddings.
    Supports batch processing and caching for performance.
    """
    
    # MNPI Keywords - Material Non-Public Information indicators
    MNPI_KEYWORDS = [
        # Financial Performance
        "earnings", "revenue", "profit", "loss", "quarterly results",
        "financial results", "guidance", "forecast", "outlook",
        
        # Corporate Actions
        "merger", "acquisition", "takeover", "buyout", "divestiture",
        "restructuring", "bankruptcy", "liquidation",
        
        # Strategic Information
        "product launch", "new product", "patent", "FDA approval",
        "clinical trial", "regulatory approval", "contract award",
        
        # Executive Actions
        "CEO resignation", "CFO departure", "board changes",
        "executive compensation", "insider selling", "insider buying",
        
        # Market Moving Events
        "dividend", "stock split", "share buyback", "capital raise",
        "debt offering", "credit rating", "analyst upgrade", "analyst downgrade",
        
        # Confidential Information
        "confidential", "non-public", "insider information", "material information",
        "not yet announced", "upcoming announcement", "embargo",
        
        # Trading Signals
        "buy recommendation", "sell recommendation", "price target",
        "trading opportunity", "market timing", "advance notice"
    ]
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        cache_size: int = 1000
    ):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Sentence-transformers model name
                       'all-MiniLM-L6-v2' - Fast, 384 dimensions (default)
                       'all-mpnet-base-v2' - High quality, 768 dimensions
            device: 'cpu' or 'cuda' for GPU acceleration
            cache_size: LRU cache size for embeddings
        """
        self.model_name = model_name
        self.device = device
        self.cache_size = cache_size
        
        logger.info(f"Loading sentence-transformers model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
        
        # Pre-compute MNPI keyword embeddings
        self._mnpi_embeddings = self._generate_mnpi_embeddings()
        
    def _generate_mnpi_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Pre-compute embeddings for all MNPI keywords.
        
        Returns:
            Dictionary mapping keywords to embeddings
        """
        logger.info(f"Generating embeddings for {len(self.MNPI_KEYWORDS)} MNPI keywords")
        
        embeddings = {}
        for keyword in self.MNPI_KEYWORDS:
            embedding = self.model.encode(keyword, convert_to_numpy=True)
            embeddings[keyword] = embedding
            
        logger.info("MNPI keyword embeddings generated")
        return embeddings
    
    @lru_cache(maxsize=1000)
    def encode_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text with caching.
        
        Args:
            text: Input text to encode
            
        Returns:
            Numpy array of embedding vector
        """
        if not text or not text.strip():
            return np.zeros(self.embedding_dim or 384)
            
        return self.model.encode(text.strip(), convert_to_numpy=True)
    
    def encode_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
            
        # Filter empty texts
        valid_texts = [text.strip() for text in texts if text and text.strip()]
        
        if not valid_texts:
            return [np.zeros(self.embedding_dim or 384) for _ in texts]
            
        logger.info(f"Encoding batch of {len(valid_texts)} texts")
        embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
        
        return embeddings.tolist()
    
    def calculate_mnpi_similarity(
        self,
        text: str,
        threshold: float = 0.7
    ) -> Tuple[float, List[Tuple[str, float]]]:
        """
        Calculate semantic similarity between text and MNPI keywords.
        
        Args:
            text: Text to analyze for MNPI content
            threshold: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            Tuple of (max_similarity, matching_keywords)
            matching_keywords: List of (keyword, similarity_score)
        """
        if not text or not text.strip():
            return 0.0, []
            
        text_embedding = self.encode_text(text)
        
        similarities = []
        max_similarity = 0.0
        
        for keyword, keyword_embedding in self._mnpi_embeddings.items():
            # Calculate cosine similarity
            similarity = np.dot(text_embedding, keyword_embedding) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(keyword_embedding)
            )
            
            if similarity >= threshold:
                similarities.append((keyword, float(similarity)))
                max_similarity = max(max_similarity, similarity)
        
        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return float(max_similarity), similarities
    
    def detect_mnpi_content(
        self,
        communications: List[Dict[str, str]],
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Detect MNPI content in communications using semantic similarity.
        
        Args:
            communications: List of communication records
                          Each record should have 'id', 'content', 'sender', 'timestamp'
            threshold: MNPI similarity threshold
            
        Returns:
            List of MNPI detection results
        """
        results = []
        
        for comm in communications:
            comm_id = comm.get('id', 'unknown')
            content = comm.get('content', '')
            sender = comm.get('sender', 'unknown')
            timestamp = comm.get('timestamp', '')
            
            max_similarity, matching_keywords = self.calculate_mnpi_similarity(
                content, threshold
            )
            
            if max_similarity > 0:
                result = {
                    'communication_id': comm_id,
                    'sender': sender,
                    'timestamp': timestamp,
                    'content_preview': content[:100] + '...' if len(content) > 100 else content,
                    'mnpi_similarity': max_similarity,
                    'matching_keywords': matching_keywords[:5],  # Top 5 matches
                    'risk_level': self._calculate_risk_level(max_similarity),
                    'requires_review': max_similarity >= 0.8
                }
                results.append(result)
        
        # Sort by similarity score (highest risk first)
        results.sort(key=lambda x: x['mnpi_similarity'], reverse=True)
        
        return results
    
    def _calculate_risk_level(self, similarity: float) -> str:
        """
        Calculate risk level based on MNPI similarity score.
        
        Args:
            similarity: Similarity score (0.0 to 1.0)
            
        Returns:
            Risk level string
        """
        if similarity >= 0.9:
            return "CRITICAL"
        elif similarity >= 0.8:
            return "HIGH"
        elif similarity >= 0.7:
            return "MEDIUM"
        else:
            return "LOW"
    
    def generate_communication_embedding(
        self,
        communication: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Generate embedding for a communication record.
        
        Args:
            communication: Communication record with 'content' field
            
        Returns:
            Dictionary with embedding and metadata
        """
        content = communication.get('content', '')
        
        # Generate embedding
        embedding = self.encode_text(content)
        
        # Calculate MNPI similarity
        mnpi_similarity, matching_keywords = self.calculate_mnpi_similarity(content)
        
        return {
            'communication_id': communication.get('id', 'unknown'),
            'embedding': embedding.tolist(),  # Convert to list for JSON serialization
            'embedding_dim': self.embedding_dim,
            'model_name': self.model_name,
            'mnpi_similarity': mnpi_similarity,
            'matching_keywords': matching_keywords,
            'content_length': len(content),
            'timestamp': communication.get('timestamp', ''),
            'sender': communication.get('sender', 'unknown')
        }
    
    def find_similar_communications(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[np.ndarray],
        top_k: int = 10,
        threshold: float = 0.6
    ) -> List[Tuple[int, float]]:
        """
        Find communications similar to a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (index, similarity_score) tuples
        """
        if not candidate_embeddings:
            return []
            
        similarities = []
        
        for i, candidate_embedding in enumerate(candidate_embeddings):
            similarity = np.dot(query_embedding, candidate_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(candidate_embedding)
            )
            
            if similarity >= threshold:
                similarities.append((i, float(similarity)))
        
        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dim,
            'device': self.device,
            'cache_size': self.cache_size,
            'mnpi_keywords_count': len(self.MNPI_KEYWORDS),
            'model_max_seq_length': getattr(self.model, 'max_seq_length', 'unknown')
        }


# Singleton instance for global use
_embedding_generator: Optional[EmbeddingGenerator] = None


def get_embedding_generator(
    model_name: str = "all-MiniLM-L6-v2",
    device: str = "cpu"
) -> EmbeddingGenerator:
    """
    Get singleton embedding generator instance.
    
    Args:
        model_name: Sentence-transformers model name
        device: 'cpu' or 'cuda'
        
    Returns:
        EmbeddingGenerator instance
    """
    global _embedding_generator
    
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator(
            model_name=model_name,
            device=device
        )
    
    return _embedding_generator


# Convenience functions
def encode_text(text: str) -> np.ndarray:
    """Encode single text using default generator."""
    generator = get_embedding_generator()
    return generator.encode_text(text)


def detect_mnpi_in_text(text: str, threshold: float = 0.7) -> Tuple[float, List[Tuple[str, float]]]:
    """Detect MNPI content in text using default generator."""
    generator = get_embedding_generator()
    return generator.calculate_mnpi_similarity(text, threshold)


def batch_encode_communications(communications: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Batch encode communications using default generator."""
    generator = get_embedding_generator()
    return [generator.generate_communication_embedding(comm) for comm in communications]


if __name__ == "__main__":
    # Example usage
    generator = EmbeddingGenerator()
    
    # Test MNPI detection
    test_texts = [
        "The quarterly earnings will be announced next week",
        "We should buy more shares before the merger announcement",
        "The weather is nice today",
        "FDA approval expected for our new drug next month",
        "Regular business meeting scheduled for tomorrow"
    ]
    
    print("MNPI Detection Results:")
    print("=" * 50)
    
    for text in test_texts:
        similarity, keywords = generator.calculate_mnpi_similarity(text)
        print(f"Text: {text}")
        print(f"MNPI Similarity: {similarity:.3f}")
        print(f"Matching Keywords: {keywords[:3]}")  # Top 3
        print("-" * 30)

# Made with Bob
