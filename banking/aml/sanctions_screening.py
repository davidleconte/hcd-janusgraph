"""
AML Sanctions Screening Module
Fuzzy name matching using vector embeddings for sanctions list screening

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-28
Phase: 6 (Complete AML Implementation)
"""

import sys
import os
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/python'))

from utils.embedding_generator import EmbeddingGenerator, encode_person_name
from utils.vector_search import VectorSearchClient

logger = logging.getLogger(__name__)


@dataclass
class SanctionMatch:
    """Represents a potential sanctions match."""
    customer_name: str
    sanctioned_name: str
    similarity_score: float
    sanctions_list: str
    entity_id: str
    match_type: str  # 'exact', 'fuzzy', 'phonetic'
    risk_level: str  # 'high', 'medium', 'low'
    metadata: Dict[str, Any]


@dataclass
class ScreeningResult:
    """Result of sanctions screening."""
    customer_id: str
    customer_name: str
    is_match: bool
    matches: List[SanctionMatch]
    screening_timestamp: str
    confidence: float


class SanctionsScreener:
    """
    Sanctions screening with fuzzy name matching.
    
    Uses vector embeddings to detect name variations, typos,
    transliterations, and phonetic similarities.
    """
    
    # Risk thresholds
    HIGH_RISK_THRESHOLD = 0.95  # Very similar names
    MEDIUM_RISK_THRESHOLD = 0.85  # Moderately similar
    LOW_RISK_THRESHOLD = 0.75  # Possibly similar
    
    def __init__(
        self,
        opensearch_host: str = 'localhost',
        opensearch_port: int = 9200,
        embedding_model: str = 'mini',
        index_name: str = 'sanctions_list'
    ):
        """
        Initialize sanctions screener.
        
        Args:
            opensearch_host: OpenSearch host
            opensearch_port: OpenSearch port
            embedding_model: Embedding model ('mini' or 'mpnet')
            index_name: OpenSearch index name for sanctions
        """
        self.index_name = index_name
        
        # Initialize embedding generator
        logger.info("Initializing embedding generator: %s", embedding_model)
        self.generator = EmbeddingGenerator(model_name=embedding_model)
        
        # Initialize vector search client
        logger.info("Connecting to OpenSearch: %s:%s", opensearch_host, opensearch_port)
        self.search_client = VectorSearchClient(
            host=opensearch_host,
            port=opensearch_port
        )
        
        # Create index if not exists
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Create sanctions index if it doesn't exist."""
        if not self.search_client.client.indices.exists(index=self.index_name):
            logger.info("Creating sanctions index: %s", self.index_name)
            
            additional_fields = {
                'name': {'type': 'text'},
                'entity_id': {'type': 'keyword'},
                'sanctions_list': {'type': 'keyword'},  # OFAC, UN, EU, etc.
                'entity_type': {'type': 'keyword'},  # person, company, vessel
                'country': {'type': 'keyword'},
                'aliases': {'type': 'text'},
                'date_added': {'type': 'date'},
                'metadata': {'type': 'object', 'enabled': False}
            }
            
            self.search_client.create_vector_index(
                index_name=self.index_name,
                vector_dimension=self.generator.dimensions,
                additional_fields=additional_fields
            )
    
    def load_sanctions_list(
        self,
        sanctions_data: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        Load sanctions list into vector index.
        
        Args:
            sanctions_data: List of sanctioned entities
                Each dict should have: name, entity_id, sanctions_list, etc.
            batch_size: Batch size for indexing
        
        Returns:
            Number of entities indexed
        """
        logger.info("Loading %s sanctioned entities...", len(sanctions_data))
        
        # Generate embeddings
        names = [entity['name'] for entity in sanctions_data]
        embeddings = self.generator.encode(names, batch_size=batch_size, show_progress=True)
        
        # Prepare documents for indexing
        documents = []
        for i, entity in enumerate(sanctions_data):
            doc = {
                'id': entity.get('entity_id', f"sanction_{i}"),
                'embedding': embeddings[i],
                'name': entity['name'],
                'entity_id': entity.get('entity_id', f"sanction_{i}"),
                'sanctions_list': entity.get('sanctions_list', 'UNKNOWN'),
                'entity_type': entity.get('entity_type', 'person'),
                'country': entity.get('country', ''),
                'aliases': entity.get('aliases', ''),
                'date_added': entity.get('date_added', datetime.now(timezone.utc).isoformat()),
                'metadata': entity.get('metadata', {})
            }
            documents.append(doc)
        
        # Bulk index
        success, errors = self.search_client.bulk_index_documents(
            index_name=self.index_name,
            documents=documents
        )
        
        logger.info("Indexed %s sanctioned entities", success)
        if errors:
            logger.warning("Encountered %s errors during indexing", len(errors))
        
        return success
    
    def screen_customer(
        self,
        customer_id: str,
        customer_name: str,
        k: int = 10,
        min_score: float = None
    ) -> ScreeningResult:
        """
        Screen a customer against sanctions list.
        
        Args:
            customer_id: Customer ID
            customer_name: Customer name to screen
            k: Number of top matches to retrieve
            min_score: Minimum similarity score (default: LOW_RISK_THRESHOLD)
        
        Returns:
            ScreeningResult with matches
        """
        if min_score is None:
            min_score = self.LOW_RISK_THRESHOLD
        
        logger.info("Screening customer: %s (ID: %s)", customer_name, customer_id)
        
        # Generate embedding for customer name
        customer_embedding = encode_person_name(customer_name, self.generator)
        
        # Search for similar names
        results = self.search_client.search(
            index_name=self.index_name,
            query_embedding=customer_embedding,
            k=k,
            min_score=min_score
        )
        
        # Process matches
        matches = []
        for result in results:
            score = result['score']
            source = result['source']
            
            # Determine risk level
            if score >= self.HIGH_RISK_THRESHOLD:
                risk_level = 'high'
                match_type = 'exact' if score > 0.98 else 'fuzzy'
            elif score >= self.MEDIUM_RISK_THRESHOLD:
                risk_level = 'medium'
                match_type = 'fuzzy'
            else:
                risk_level = 'low'
                match_type = 'phonetic'
            
            match = SanctionMatch(
                customer_name=customer_name,
                sanctioned_name=source['name'],
                similarity_score=score,
                sanctions_list=source.get('list_type', 'UNKNOWN'),
                entity_id=source.get('id', 'UNKNOWN'),
                match_type=match_type,
                risk_level=risk_level,
                metadata={
                    'entity_type': source.get('entity_type', ''),
                    'country': source.get('country', ''),
                    'aliases': source.get('aliases', ''),
                    'date_added': source.get('added_date', '')
                }
            )
            matches.append(match)
        
        # Determine if there's a match
        is_match = len(matches) > 0 and matches[0].similarity_score >= self.MEDIUM_RISK_THRESHOLD
        confidence = matches[0].similarity_score if matches else 0.0
        
        result = ScreeningResult(
            customer_id=customer_id,
            customer_name=customer_name,
            is_match=is_match,
            matches=matches,
            screening_timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=confidence
        )
        
        if is_match:
            logger.warning(
                f"⚠️  SANCTIONS MATCH: {customer_name} -> {matches[0].sanctioned_name} "
                f"(score: {matches[0].similarity_score:.4f}, risk: {matches[0].risk_level})"
            )
        else:
            logger.info("✅ No sanctions match for: %s", customer_name)
        
        return result
    
    def batch_screen_customers(
        self,
        customers: List[Dict[str, str]],
        k: int = 10,
        min_score: float = None
    ) -> Dict[str, Any]:
        """
        Screen multiple customers in batch.
        
        Args:
            customers: List of dicts with 'customer_id'/'customer_name' OR 'id'/'name'
            k: Number of top matches per customer
            min_score: Minimum similarity score
        
        Returns:
            Dict with 'total_screened', 'matches_found', 'processing_time_seconds', 'results'
        """
        import time
        start_time = time.time()
        
        logger.info("Batch screening %s customers...", len(customers))
        
        results = []
        for customer in customers:
            # Support both key formats: customer_id/customer_name and id/name
            cust_id = customer.get('customer_id') or customer.get('id', 'UNKNOWN')
            cust_name = customer.get('customer_name') or customer.get('name', '')
            
            result = self.screen_customer(
                customer_id=cust_id,
                customer_name=cust_name,
                k=k,
                min_score=min_score
            )
            results.append(result)
        
        processing_time = time.time() - start_time
        
        # Summary
        matches = [r for r in results if r.is_match]
        logger.info("Batch screening complete: %s/%s matches found", len(matches), len(customers))
        
        return {
            'total_screened': len(customers),
            'matches_found': len(matches),
            'processing_time_seconds': processing_time,
            'results': results
        }
    def get_statistics(self) -> Dict[str, Any]:
        """Get sanctions list statistics."""
        stats = self.search_client.get_index_stats(self.index_name)
        
        return {
            'total_entities': stats['total']['docs']['count'],
            'index_size_bytes': stats['total']['store']['size_in_bytes'],
            'index_name': self.index_name,
            'embedding_dimensions': self.generator.dimensions
        }


# Example usage and testing
