"""
OpenSearch Vector Search Integration
Provides k-NN vector search capabilities using OpenSearch 3.3.4+ with JVector plugin

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-28
Updated: 2026-01-28 - Security Hardening
Phase: 5 (Vector/AI Foundation)
"""

from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from opensearchpy import OpenSearch, helpers
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class VectorSearchClient:
    """
    OpenSearch client for vector similarity search.
    
    Uses OpenSearch 3.3.4+ with JVector plugin for k-NN search.
    No external FAISS required - JVector handles all vector operations.
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 9200,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = False,
        verify_certs: bool = False,
        ca_certs: Optional[str] = None
    ):
        """
        Initialize OpenSearch client with optional security.
        
        Args:
            host: OpenSearch host
            port: OpenSearch port
            username: Authentication username (optional for local dev)
            password: Authentication password (optional for local dev)
            use_ssl: Use SSL/TLS - default False for local development
            verify_certs: Verify SSL certificates - default False
            ca_certs: Path to CA certificate bundle
        
        Note:
            For production, set OPENSEARCH_USERNAME and OPENSEARCH_PASSWORD
            environment variables or pass credentials to constructor.
        """
        # Get credentials from environment if not provided
        if not username:
            username = os.getenv('OPENSEARCH_USERNAME')
        if not password:
            password = os.getenv('OPENSEARCH_PASSWORD')
        
        # Configure authentication only if credentials provided
        auth = None
        if username and password:
            auth = (username, password)
            logger.info("Using authenticated OpenSearch connection")
        else:
            logger.warning("No authentication configured - using unauthenticated connection (development mode)")
        
        # Configure SSL options
        ssl_options = {}
        if use_ssl and ca_certs:
            ssl_options['ca_certs'] = ca_certs
        
        client_kwargs = {
            'hosts': [{'host': host, 'port': port}],
            'use_ssl': use_ssl,
            'verify_certs': verify_certs,
            'ssl_show_warn': False,
        }
        
        if auth:
            client_kwargs['http_auth'] = auth
        
        client_kwargs.update(ssl_options)
        
        self.client = OpenSearch(**client_kwargs)
        
        logger.info(f"Connected to OpenSearch at {host}:{port} (SSL: {use_ssl})")
        
        # Verify connection
        info = self.client.info()
        logger.info(f"OpenSearch version: {info['version']['number']}")
    
    def create_vector_index(
        self,
        index_name: str,
        vector_dimension: int,
        vector_field: str = 'embedding',
        additional_fields: Optional[Dict[str, Dict]] = None,
        engine: str = 'lucene',
        space_type: str = 'cosinesimil',
        ef_construction: int = 512,
        m: int = 16
    ) -> bool:
        """
        Create an index with k-NN vector search enabled.
        
        Args:
            index_name: Name of the index
            vector_dimension: Dimension of embedding vectors
            vector_field: Name of the vector field
            additional_fields: Additional field mappings
            engine: Vector engine ('lucene' for JVector, 'nmslib', 'faiss')
            space_type: Distance metric ('cosinesimil', 'l2', 'l1', 'linf')
            ef_construction: HNSW ef_construction parameter (higher = better recall, slower indexing)
            m: HNSW M parameter (higher = better recall, more memory)
        
        Returns:
            True if index created successfully
        """
        if self.client.indices.exists(index=index_name):
            logger.warning(f"Index {index_name} already exists")
            return False
        
        # Build index settings and mappings
        index_body = {
            'settings': {
                'index': {
                    'knn': True,  # Enable k-NN
                    'knn.algo_param.ef_search': 512  # Search-time parameter
                }
            },
            'mappings': {
                'properties': {
                    vector_field: {
                        'type': 'knn_vector',
                        'dimension': vector_dimension,
                        'method': {
                            'name': 'hnsw',
                            'space_type': space_type,
                            'engine': engine,
                            'parameters': {
                                'ef_construction': ef_construction,
                                'm': m
                            }
                        }
                    }
                }
            }
        }
        
        # Add additional fields
        if additional_fields:
            index_body['mappings']['properties'].update(additional_fields)
        
        # Create index
        self.client.indices.create(index=index_name, body=index_body)
        logger.info(f"Created vector index: {index_name} (dim={vector_dimension}, engine={engine})")
        
        return True
    
    def index_document(
        self,
        index_name: str,
        doc_id: str,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
        vector_field: str = 'embedding'
    ) -> bool:
        """
        Index a single document with its embedding.
        
        Args:
            index_name: Index name
            doc_id: Document ID
            embedding: Embedding vector
            metadata: Additional metadata fields
            vector_field: Name of the vector field
        
        Returns:
            True if indexed successfully
        """
        doc = {
            vector_field: embedding.tolist(),
            'indexed_at': datetime.utcnow().isoformat()
        }
        
        if metadata:
            doc.update(metadata)
        
        response = self.client.index(
            index=index_name,
            id=doc_id,
            body=doc,
            refresh=True
        )
        
        return response['result'] in ['created', 'updated']
    
    def bulk_index_documents(
        self,
        index_name: str,
        documents: List[Dict[str, Any]],
        vector_field: str = 'embedding',
        id_field: str = 'id'
    ) -> Tuple[int, List[Dict]]:
        """
        Bulk index multiple documents.
        
        Args:
            index_name: Index name
            documents: List of documents, each with 'id', 'embedding', and optional metadata
            vector_field: Name of the vector field
            id_field: Name of the ID field
        
        Returns:
            Tuple of (success_count, errors)
        """
        actions = []
        for doc in documents:
            if id_field not in doc or vector_field not in doc:
                logger.warning(f"Skipping document missing required fields: {doc}")
                continue
            
            embedding = doc[vector_field]
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            action = {
                '_index': index_name,
                '_id': doc[id_field],
                '_source': {
                    vector_field: embedding,
                    'indexed_at': datetime.utcnow().isoformat()
                }
            }
            
            # Add metadata
            for key, value in doc.items():
                if key not in [id_field, vector_field]:
                    action['_source'][key] = value
            
            actions.append(action)
        
        success, errors = helpers.bulk(self.client, actions, refresh=True)
        logger.info(f"Bulk indexed {success} documents to {index_name}")
        
        return success, errors
    
    def search(
        self,
        index_name: str,
        query_embedding: np.ndarray,
        k: int = 10,
        vector_field: str = 'embedding',
        filters: Optional[Dict] = None,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform k-NN vector similarity search.
        
        Args:
            index_name: Index name
            query_embedding: Query embedding vector
            k: Number of results to return
            vector_field: Name of the vector field
            filters: Optional filters to apply
            min_score: Minimum similarity score threshold
        
        Returns:
            List of search results with scores
        """
        query_vector = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding
        
        # Build k-NN query for OpenSearch 3.x
        # Use the newer knn query format
        search_body = {
            'size': k,
            'query': {
                'knn': {
                    vector_field: {
                        'vector': query_vector,
                        'k': k
                    }
                }
            }
        }
        
        # Add filters if provided
        if filters:
            search_body['query'] = {
                'bool': {
                    'must': [
                        {'knn': {vector_field: {'vector': query_vector, 'k': k}}}
                    ],
                    'filter': filters
                }
            }
        
        # Execute search
        response = self.client.search(
            index=index_name,
            body=search_body
        )
        
        # Parse results
        results = []
        for hit in response['hits']['hits']:
            result = {
                'id': hit['_id'],
                'score': hit['_score'],
                'source': hit['_source']
            }
            
            # Apply min_score filter
            if min_score is None or result['score'] >= min_score:
                results.append(result)
        
        logger.debug(f"Found {len(results)} results for k-NN search")
        return results
    
    def delete_index(self, index_name: str) -> bool:
        """
        Delete an index.
        
        Args:
            index_name: Index name
        
        Returns:
            True if deleted successfully
        """
        if not self.client.indices.exists(index=index_name):
            logger.warning(f"Index {index_name} does not exist")
            return False
        
        self.client.indices.delete(index=index_name)
        logger.info(f"Deleted index: {index_name}")
        return True
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """
        Get statistics for an index.
        
        Args:
            index_name: Index name
        
        Returns:
            Index statistics
        """
        stats = self.client.indices.stats(index=index_name)
        return stats['indices'][index_name]


# Banking-specific helper functions

def create_person_name_index(
    client: VectorSearchClient,
    index_name: str = 'banking_person_names',
    vector_dimension: int = 384
) -> bool:
    """
    Create an index for person name fuzzy matching.
    
    Args:
        client: VectorSearchClient instance
        index_name: Index name
        vector_dimension: Embedding dimension (384 for mini, 768 for mpnet)
    
    Returns:
        True if created successfully
    """
    additional_fields = {
        'name': {'type': 'text'},
        'person_id': {'type': 'keyword'},
        'source': {'type': 'keyword'}  # e.g., 'customer', 'sanctions_list'
    }
    
    return client.create_vector_index(
        index_name=index_name,
        vector_dimension=vector_dimension,
        additional_fields=additional_fields
    )


def create_transaction_description_index(
    client: VectorSearchClient,
    index_name: str = 'banking_transaction_descriptions',
    vector_dimension: int = 768
) -> bool:
    """
    Create an index for transaction description semantic search.
    
    Args:
        client: VectorSearchClient instance
        index_name: Index name
        vector_dimension: Embedding dimension (768 for mpnet recommended)
    
    Returns:
        True if created successfully
    """
    additional_fields = {
        'description': {'type': 'text'},
        'transaction_id': {'type': 'keyword'},
        'amount': {'type': 'float'},
        'timestamp': {'type': 'date'}
    }
    
    return client.create_vector_index(
        index_name=index_name,
        vector_dimension=vector_dimension,
        additional_fields=additional_fields
    )


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize client
    print("Connecting to OpenSearch...")
    client = VectorSearchClient(host='localhost', port=9200)
    
    # Create test index
    print("\nCreating test index...")
    index_name = 'test_vectors'
    client.create_vector_index(
        index_name=index_name,
        vector_dimension=384,
        additional_fields={'text': {'type': 'text'}}
    )
    
    # Index test documents
    print("\nIndexing test documents...")
    test_docs = [
        {
            'id': '1',
            'embedding': np.random.rand(384),
            'text': 'John Smith'
        },
        {
            'id': '2',
            'embedding': np.random.rand(384),
            'text': 'Jane Doe'
        }
    ]
    
    success, errors = client.bulk_index_documents(index_name, test_docs)
    print(f"Indexed {success} documents")
    
    # Search
    print("\nSearching...")
    query_vector = np.random.rand(384)
    results = client.search(index_name, query_vector, k=2)
    
    print(f"Found {len(results)} results:")
    for result in results:
        print(f"  - ID: {result['id']}, Score: {result['score']:.4f}, Text: {result['source']['text']}")
    
    # Cleanup
    print("\nCleaning up...")
    client.delete_index(index_name)
    print("✅ Test complete!")

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
