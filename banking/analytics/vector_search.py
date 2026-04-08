"""
OpenSearch Vector Search Module for MNPI Detection
===================================================

Implements k-NN (k-Nearest Neighbors) vector search in OpenSearch for
semantic similarity detection of Material Non-Public Information (MNPI).

Key Features:
- OpenSearch k-NN index management
- Semantic similarity search
- MNPI detection via vector similarity
- Integration with JanusGraph for graph-vector hybrid queries

Author: Banking Compliance Platform Team
Date: 2026-04-07
Sprint: 1.4 - Vector Search Integration
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from opensearchpy import OpenSearch, helpers

from banking.analytics.embeddings import EmbeddingGenerator, get_embedding_generator

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class VectorSearchClient:
    """
    OpenSearch k-NN vector search client for MNPI detection.
    
    Manages vector indices, performs semantic similarity searches,
    and integrates with JanusGraph for hybrid graph-vector queries.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9200,
        use_ssl: bool = False,
        verify_certs: bool = False,
        username: Optional[str] = None,
        password: Optional[str] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None
    ):
        """
        Initialize OpenSearch vector search client.
        
        Args:
            host: OpenSearch host
            port: OpenSearch port
            use_ssl: Enable SSL/TLS
            verify_certs: Verify SSL certificates
            username: Authentication username
            password: Authentication password
            embedding_generator: Custom embedding generator (optional)
        """
        self.host = host
        self.port = port
        
        # Initialize OpenSearch client
        client_config = {
            'hosts': [{'host': host, 'port': port}],
            'use_ssl': use_ssl,
            'verify_certs': verify_certs,
            'ssl_show_warn': False
        }
        
        if username and password:
            client_config['http_auth'] = (username, password)
        
        self.client = OpenSearch(**client_config)
        
        # Initialize embedding generator
        self.embedding_generator = embedding_generator or get_embedding_generator()
        self.embedding_dim = self.embedding_generator.embedding_dim
        
        logger.info(f"VectorSearchClient initialized: {host}:{port}")
        logger.info(f"Embedding dimension: {self.embedding_dim}")
    
    def create_communication_index(
        self,
        index_name: str = "communications-vector",
        force_recreate: bool = False
    ) -> bool:
        """
        Create OpenSearch index for communication vectors with k-NN enabled.
        
        Args:
            index_name: Name of the index to create
            force_recreate: Delete existing index if it exists
            
        Returns:
            True if index created successfully
        """
        if self.client.indices.exists(index=index_name):
            if force_recreate:
                logger.info(f"Deleting existing index: {index_name}")
                self.client.indices.delete(index=index_name)
            else:
                logger.info(f"Index already exists: {index_name}")
                return True
        
        # Index mapping with k-NN vector field
        index_body = {
            "settings": {
                "index": {
                    "knn": True,  # Enable k-NN
                    "knn.algo_param.ef_search": 100,  # Search quality parameter
                    "number_of_shards": 3,
                    "number_of_replicas": 2
                }
            },
            "mappings": {
                "properties": {
                    "communication_id": {"type": "keyword"},
                    "sender_id": {"type": "keyword"},
                    "receiver_id": {"type": "keyword"},
                    "content": {"type": "text"},
                    "content_vector": {
                        "type": "knn_vector",
                        "dimension": self.embedding_dim,
                        "method": {
                            "name": "hnsw",  # Hierarchical Navigable Small World
                            "space_type": "cosinesimil",  # Cosine similarity
                            "engine": "nmslib",  # Fast k-NN library
                            "parameters": {
                                "ef_construction": 128,
                                "m": 16
                            }
                        }
                    },
                    "mnpi_similarity": {"type": "float"},
                    "matching_keywords": {"type": "keyword"},
                    "risk_level": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "indexed_at": {"type": "date"}
                }
            }
        }
        
        logger.info(f"Creating index: {index_name}")
        self.client.indices.create(index=index_name, body=index_body)
        logger.info(f"Index created successfully: {index_name}")
        
        return True
    
    def index_communication(
        self,
        communication: Dict[str, Any],
        index_name: str = "communications-vector"
    ) -> bool:
        """
        Index a single communication with its vector embedding.
        
        Args:
            communication: Communication record with 'id', 'content', 'sender', etc.
            index_name: Target index name
            
        Returns:
            True if indexed successfully
        """
        # Generate embedding
        embedding_data = self.embedding_generator.generate_communication_embedding(communication)
        
        # Prepare document
        doc = {
            "communication_id": communication.get('id', 'unknown'),
            "sender_id": communication.get('sender', 'unknown'),
            "receiver_id": communication.get('receiver', 'unknown'),
            "content": communication.get('content', ''),
            "content_vector": embedding_data['embedding'],
            "mnpi_similarity": embedding_data['mnpi_similarity'],
            "matching_keywords": [kw[0] for kw in embedding_data['matching_keywords'][:10]],
            "risk_level": self._calculate_risk_level(embedding_data['mnpi_similarity']),
            "timestamp": communication.get('timestamp', datetime.utcnow().isoformat()),
            "indexed_at": datetime.utcnow().isoformat()
        }
        
        # Index document
        response = self.client.index(
            index=index_name,
            id=doc['communication_id'],
            body=doc
        )
        
        # Refresh index to make document searchable immediately
        self.client.indices.refresh(index=index_name)
        
        return response['result'] in ['created', 'updated']
    
    def bulk_index_communications(
        self,
        communications: List[Dict[str, Any]],
        index_name: str = "communications-vector",
        batch_size: int = 100
    ) -> Tuple[int, int]:
        """
        Bulk index multiple communications efficiently.
        
        Args:
            communications: List of communication records
            index_name: Target index name
            batch_size: Number of documents per batch
            
        Returns:
            Tuple of (success_count, error_count)
        """
        logger.info(f"Bulk indexing {len(communications)} communications")
        
        actions = []
        for comm in communications:
            # Generate embedding
            embedding_data = self.embedding_generator.generate_communication_embedding(comm)
            
            # Prepare action
            action = {
                "_index": index_name,
                "_id": comm.get('id', 'unknown'),
                "_source": {
                    "communication_id": comm.get('id', 'unknown'),
                    "sender_id": comm.get('sender', 'unknown'),
                    "receiver_id": comm.get('receiver', 'unknown'),
                    "content": comm.get('content', ''),
                    "content_vector": embedding_data['embedding'],
                    "mnpi_similarity": embedding_data['mnpi_similarity'],
                    "matching_keywords": [kw[0] for kw in embedding_data['matching_keywords'][:10]],
                    "risk_level": self._calculate_risk_level(embedding_data['mnpi_similarity']),
                    "timestamp": comm.get('timestamp', datetime.utcnow().isoformat()),
                    "indexed_at": datetime.utcnow().isoformat()
                }
            }
            actions.append(action)
        
        # Bulk index
        success, errors = helpers.bulk(
            self.client,
            actions,
            chunk_size=batch_size,
            raise_on_error=False
        )
        
        logger.info(f"Bulk indexing complete: {success} success, {len(errors)} errors")
        return success, len(errors)
    
    def search_similar_communications(
        self,
        query_text: str,
        index_name: str = "communications-vector",
        k: int = 10,
        min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for communications semantically similar to query text.
        
        Args:
            query_text: Query text to search for
            index_name: Index to search
            k: Number of results to return
            min_score: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of similar communications with scores
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.encode_text(query_text)
        
        # k-NN search query
        search_body = {
            "size": k,
            "query": {
                "knn": {
                    "content_vector": {
                        "vector": query_embedding.tolist(),
                        "k": k
                    }
                }
            },
            "_source": [
                "communication_id", "sender_id", "receiver_id",
                "content", "mnpi_similarity", "matching_keywords",
                "risk_level", "timestamp"
            ]
        }
        
        response = self.client.search(index=index_name, body=search_body)
        
        # Process results
        results = []
        for hit in response['hits']['hits']:
            score = hit['_score']
            
            # Filter by minimum score
            if score >= min_score:
                result = hit['_source']
                result['similarity_score'] = score
                results.append(result)
        
        logger.info(f"Found {len(results)} similar communications (min_score={min_score})")
        return results
    
    def detect_mnpi_sharing_network(
        self,
        insider_id: str,
        index_name: str = "communications-vector",
        mnpi_threshold: float = 0.8,
        similarity_threshold: float = 0.7,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Detect potential MNPI sharing network using vector similarity.
        
        Finds communications from an insider that:
        1. Have high MNPI similarity (contain material information)
        2. Are semantically similar to each other (coordinated messaging)
        
        Args:
            insider_id: Person ID of the insider
            index_name: Index to search
            mnpi_threshold: Minimum MNPI similarity score
            similarity_threshold: Minimum semantic similarity between communications
            max_results: Maximum number of results
            
        Returns:
            Dictionary with detection results
        """
        logger.info(f"Detecting MNPI sharing network for insider: {insider_id}")
        
        # Step 1: Find all communications from insider with high MNPI content
        search_body = {
            "size": max_results,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"sender_id": insider_id}},
                        {"range": {"mnpi_similarity": {"gte": mnpi_threshold}}}
                    ]
                }
            },
            "sort": [
                {"mnpi_similarity": {"order": "desc"}},
                {"timestamp": {"order": "desc"}}
            ]
        }
        
        response = self.client.search(index=index_name, body=search_body)
        
        mnpi_communications = []
        for hit in response['hits']['hits']:
            comm = hit['_source']
            comm['doc_id'] = hit['_id']
            mnpi_communications.append(comm)
        
        if not mnpi_communications:
            return {
                "insider_id": insider_id,
                "mnpi_communications_count": 0,
                "similar_clusters": [],
                "risk_score": 0.0,
                "alert_level": "NONE"
            }
        
        # Step 2: Find semantically similar communications (clustering)
        clusters = self._cluster_similar_communications(
            mnpi_communications,
            similarity_threshold
        )
        
        # Step 3: Calculate risk score
        risk_score = self._calculate_network_risk_score(
            mnpi_communications,
            clusters
        )
        
        return {
            "insider_id": insider_id,
            "mnpi_communications_count": len(mnpi_communications),
            "similar_clusters": clusters,
            "risk_score": risk_score,
            "alert_level": self._calculate_alert_level(risk_score),
            "top_mnpi_keywords": self._extract_top_keywords(mnpi_communications),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _cluster_similar_communications(
        self,
        communications: List[Dict[str, Any]],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Cluster communications by semantic similarity.
        
        Args:
            communications: List of communications
            threshold: Similarity threshold for clustering
            
        Returns:
            List of clusters
        """
        if len(communications) < 2:
            return []
        
        # Extract embeddings
        embeddings = []
        for comm in communications:
            embedding = self.embedding_generator.encode_text(comm['content'])
            embeddings.append(embedding)
        
        # Simple clustering: find pairs with high similarity
        clusters = []
        processed = set()
        
        for i, comm1 in enumerate(communications):
            if i in processed:
                continue
                
            cluster = {
                "cluster_id": f"cluster_{len(clusters)}",
                "communications": [comm1['communication_id']],
                "avg_mnpi_similarity": comm1['mnpi_similarity'],
                "receivers": [comm1.get('receiver_id', 'unknown')]
            }
            
            for j, comm2 in enumerate(communications[i+1:], start=i+1):
                if j in processed:
                    continue
                
                # Calculate similarity
                similarity = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                )
                
                if similarity >= threshold:
                    cluster['communications'].append(comm2['communication_id'])
                    cluster['receivers'].append(comm2.get('receiver_id', 'unknown'))
                    processed.add(j)
            
            if len(cluster['communications']) > 1:
                clusters.append(cluster)
                processed.add(i)
        
        return clusters
    
    def _calculate_network_risk_score(
        self,
        communications: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]]
    ) -> float:
        """Calculate risk score for MNPI sharing network."""
        if not communications:
            return 0.0
        
        # Factors:
        # 1. Number of MNPI communications
        # 2. Average MNPI similarity
        # 3. Number of clusters (coordinated messaging)
        # 4. Number of unique receivers
        
        comm_count_score = min(len(communications) / 10.0, 1.0)  # Max at 10 comms
        
        avg_mnpi = sum(c['mnpi_similarity'] for c in communications) / len(communications)
        mnpi_score = avg_mnpi
        
        cluster_score = min(len(clusters) / 5.0, 1.0)  # Max at 5 clusters
        
        unique_receivers = len(set(c.get('receiver_id', '') for c in communications))
        receiver_score = min(unique_receivers / 10.0, 1.0)  # Max at 10 receivers
        
        # Weighted average
        risk_score = (
            comm_count_score * 0.2 +
            mnpi_score * 0.4 +
            cluster_score * 0.2 +
            receiver_score * 0.2
        )
        
        return round(risk_score, 3)
    
    def _calculate_alert_level(self, risk_score: float) -> str:
        """Calculate alert level from risk score."""
        if risk_score >= 0.9:
            return "CRITICAL"
        elif risk_score >= 0.7:
            return "HIGH"
        elif risk_score >= 0.5:
            return "MEDIUM"
        elif risk_score >= 0.3:
            return "LOW"
        else:
            return "INFO"
    
    def _calculate_risk_level(self, mnpi_similarity: float) -> str:
        """Calculate risk level from MNPI similarity."""
        if mnpi_similarity >= 0.9:
            return "CRITICAL"
        elif mnpi_similarity >= 0.8:
            return "HIGH"
        elif mnpi_similarity >= 0.7:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _extract_top_keywords(
        self,
        communications: List[Dict[str, Any]],
        top_n: int = 10
    ) -> List[Tuple[str, int]]:
        """Extract top MNPI keywords from communications."""
        keyword_counts: Dict[str, int] = {}
        
        for comm in communications:
            for keyword in comm.get('matching_keywords', []):
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Sort by count
        sorted_keywords = sorted(
            keyword_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_keywords[:top_n]
    
    def get_index_stats(self, index_name: str = "communications-vector") -> Dict[str, Any]:
        """Get statistics for the vector index."""
        if not self.client.indices.exists(index=index_name):
            return {"error": "Index does not exist"}
        
        stats = self.client.indices.stats(index=index_name)
        count = self.client.count(index=index_name)
        
        return {
            "index_name": index_name,
            "document_count": count['count'],
            "size_in_bytes": stats['_all']['total']['store']['size_in_bytes'],
            "embedding_dimension": self.embedding_dim,
            "model_name": self.embedding_generator.model_name
        }


# Singleton instance
_vector_search_client: Optional[VectorSearchClient] = None


def get_vector_search_client(
    host: str = "localhost",
    port: int = 9200,
    use_ssl: bool = False
) -> VectorSearchClient:
    """Get singleton vector search client instance."""
    global _vector_search_client
    
    if _vector_search_client is None:
        _vector_search_client = VectorSearchClient(
            host=host,
            port=port,
            use_ssl=use_ssl
        )
    
    return _vector_search_client


if __name__ == "__main__":
    # Example usage
    client = VectorSearchClient()
    
    # Create index
    client.create_communication_index(force_recreate=True)
    
    # Example communications
    test_comms = [
        {
            "id": "comm-001",
            "sender": "insider-123",
            "receiver": "trader-456",
            "content": "The quarterly earnings will exceed expectations by 20%",
            "timestamp": "2026-04-07T10:00:00Z"
        },
        {
            "id": "comm-002",
            "sender": "insider-123",
            "receiver": "trader-789",
            "content": "Our Q1 results are much better than forecasted",
            "timestamp": "2026-04-07T10:05:00Z"
        }
    ]
    
    # Index communications
    for comm in test_comms:
        client.index_communication(comm)
    
    # Detect MNPI sharing network
    results = client.detect_mnpi_sharing_network("insider-123")
    print("MNPI Sharing Network Detection:")
    print(f"Risk Score: {results['risk_score']}")
    print(f"Alert Level: {results['alert_level']}")
    print(f"MNPI Communications: {results['mnpi_communications_count']}")

# Made with Bob
