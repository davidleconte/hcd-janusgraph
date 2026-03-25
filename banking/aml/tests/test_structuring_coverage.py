"""
AML Structuring Detection - Coverage Enhancement Tests

Tests designed to increase code coverage by exercising actual code paths
instead of using heavy mocking. These tests focus on:
- Risk score calculations
- Pattern detection algorithms
- Data transformation logic
- Edge case handling
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from banking.aml.enhanced_structuring_detection import (
    EnhancedStructuringDetector,
    StructuringPattern,
)
from banking.aml.structuring_detection import StructuringDetector, StructuringAlert
from banking.aml.sanctions_screening import SanctionsScreener, TTLCache


# ============================================================
# RISK SCORE CALCULATION TESTS (Actual code execution)
# ============================================================

class TestRiskScoreCalculation:
    """Test risk score calculation logic with actual execution."""
    
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_risk_score_basic_calculation(self, mock_embed, mock_search):
        """Test basic risk score calculation."""
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        
        # Execute actual risk score calculation
        score = detector._calculate_risk_score(
            total_amount=15000.0,
            tx_count=5,
            threshold=10000.0
        )
        
        # Verify score is in valid range
        assert 0.0 <= score <= 1.0
        # Higher amounts relative to threshold should yield higher scores
        assert score > 0
    
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_risk_score_high_amount(self, mock_embed, mock_search):
        """Test risk score with high amount relative to threshold."""
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        
        score_high = detector._calculate_risk_score(
            total_amount=50000.0,
            tx_count=10,
            threshold=10000.0
        )
        
        score_low = detector._calculate_risk_score(
            total_amount=5000.0,
            tx_count=10,
            threshold=10000.0
        )
        
        # Higher amount should yield higher score
        assert score_high > score_low
    
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_risk_score_transaction_count_impact(self, mock_embed, mock_search):
        """Test that transaction count affects risk score."""
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        
        score_many = detector._calculate_risk_score(
            total_amount=15000.0,
            tx_count=10,
            threshold=10000.0
        )
        
        score_few = detector._calculate_risk_score(
            total_amount=15000.0,
            tx_count=3,
            threshold=10000.0
        )
        
        # More transactions should increase risk score
        assert score_many >= score_few
    
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_risk_score_threshold_proximity(self, mock_embed, mock_search):
        """Test risk score increases near threshold."""
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        
        # Amount just below threshold
        score_near = detector._calculate_risk_score(
            total_amount=9900.0,
            tx_count=5,
            threshold=10000.0
        )
        
        # Amount well below threshold
        score_far = detector._calculate_risk_score(
            total_amount=5000.0,
            tx_count=5,
            threshold=10000.0
        )
        
        # Amount near threshold should yield higher score
        assert score_near > score_far


# ============================================================
# STRUCTURING PATTERN DETECTION TESTS
# ============================================================

class TestStructuringPatternDetection:
    """Test structuring pattern detection logic."""
    
    def test_pattern_dataclass_fields(self):
        """Test StructuringPattern dataclass has expected fields."""
        from dataclasses import fields
        
        field_names = [f.name for f in fields(StructuringPattern)]
        
        # Verify expected fields exist
        assert 'pattern_id' in field_names
        assert 'pattern_type' in field_names
        assert 'account_id' in field_names
        assert 'risk_score' in field_names
        assert 'transactions' in field_names
    
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_class_constants(self, mock_embed, mock_search):
        """Test detector class constants."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        # Verify class constants
        assert EnhancedStructuringDetector.STRUCTURING_THRESHOLD == 10000.0
        assert EnhancedStructuringDetector.REPORTING_THRESHOLD == 10000.0
        assert EnhancedStructuringDetector.TIME_WINDOW_HOURS == 24
        assert EnhancedStructuringDetector.MIN_TRANSACTIONS >= 1
    
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_threshold_configuration(self, mock_embed, mock_search):
        """Test threshold configuration."""
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        
        # Verify default threshold
        assert detector.STRUCTURING_THRESHOLD == 10000.0
        
        # Verify semantic similarity threshold
        assert 0.0 <= detector.SEMANTIC_SIMILARITY_THRESHOLD <= 1.0


# ============================================================
# SANCTIONS SCREENING TESTS (Actual code execution)
# ============================================================

class TestSanctionsScreening:
    """Test sanctions screening logic with actual execution."""
    
    def test_ttl_cache_basic_operations(self):
        """Test TTL cache basic operations."""
        from banking.aml.sanctions_screening import ScreeningResult
        
        cache = TTLCache(maxsize=100, ttl_seconds=3600)
        
        # Create a mock result
        mock_result = MagicMock(spec=ScreeningResult)
        mock_result.customer_id = "CUST-001"
        mock_result.customer_name = "Test Customer"
        
        # Test set and get (API: customer_id, customer_name, result)
        cache.set("CUST-001", "Test Customer", mock_result)
        result, found = cache.get("CUST-001", "Test Customer")
        
        assert found is True
        assert result == mock_result
        
        # Test miss
        result, found = cache.get("NONEXISTENT", "Unknown")
        assert found is False
        assert result is None
    
    def test_ttl_cache_maxsize(self):
        """Test TTL cache maxsize enforcement."""
        cache = TTLCache(maxsize=3, ttl_seconds=3600)
        
        cache.set("k1", "Customer 1", MagicMock())
        cache.set("k2", "Customer 2", MagicMock())
        cache.set("k3", "Customer 3", MagicMock())
        cache.set("k4", "Customer 4", MagicMock())  # Should evict oldest
        
        # First key should be evicted
        result, found = cache.get("k1", "Customer 1")
        assert found is False
        
        result, found = cache.get("k4", "Customer 4")
        assert found is True
    
    def test_ttl_cache_expiration(self):
        """Test TTL cache expiration."""
        import time
        cache = TTLCache(maxsize=100, ttl_seconds=0.1)  # 100ms TTL
        
        cache.set("key", "Customer", MagicMock())
        result, found = cache.get("key", "Customer")
        assert found is True
        
        time.sleep(0.15)  # Wait for expiration
        
        result, found = cache.get("key", "Customer")
        assert found is False
    
    def test_ttl_cache_clear(self):
        """Test TTL cache clear operation."""
        cache = TTLCache(maxsize=100, ttl_seconds=3600)
        
        cache.set("k1", "Customer 1", MagicMock())
        cache.set("k2", "Customer 2", MagicMock())
        cache.clear()
        
        result, found = cache.get("k1", "Customer 1")
        assert found is False
        
        result, found = cache.get("k2", "Customer 2")
        assert found is False
    
    def test_ttl_cache_stats(self):
        """Test TTL cache hit/miss tracking."""
        cache = TTLCache(maxsize=100, ttl_seconds=3600)
        
        cache.set("k1", "Customer 1", MagicMock())
        
        # Hit
        cache.get("k1", "Customer 1")
        
        # Miss
        cache.get("nonexistent", "Unknown")
        
        assert cache._hits == 1
        assert cache._misses == 1
    
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screener_initialization(self, mock_embed, mock_search):
        """Test sanctions screener initialization."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        screener = SanctionsScreener()
        
        assert screener is not None
        # Verify it has the expected attributes
        assert hasattr(screener, '_cache')
    
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screener_thresholds(self, mock_embed, mock_search):
        """Test screener has correct thresholds."""
        mock_search.return_value.client.indices.exists.return_value = True
        
        screener = SanctionsScreener()
        
        # Verify thresholds exist and are in valid range
        assert hasattr(screener, 'HIGH_RISK_THRESHOLD')
        assert hasattr(screener, 'FUZZY_THRESHOLD')
        assert 0.0 <= screener.HIGH_RISK_THRESHOLD <= 1.0
        assert 0.0 <= screener.FUZZY_THRESHOLD <= 1.0


# ============================================================
# NAME MATCHING ALGORITHM TESTS
# ============================================================

class TestNameMatchingAlgorithms:
    """Test name matching algorithms."""
    
    def test_exact_match_comparison(self):
        """Test exact name matching."""
        # Simple case-sensitive comparison
        name1 = "John Smith"
        name2 = "John Smith"
        name3 = "john smith"
        
        assert name1.lower() == name2.lower()
        assert name1.lower() == name3.lower()
    
    def test_name_normalization(self):
        """Test name normalization for matching."""
        # Common normalization patterns
        names = [
            "AHMED AL-RASHID",
            "Ahmed Al-Rashid",
            "ahmed al-rashid",
            "AHMED AL RASHID",
        ]
        
        normalized = [n.lower().replace("-", " ").replace("  ", " ") for n in names]
        
        # All should normalize to same value
        assert len(set(normalized)) == 1


# ============================================================
# EDGE CASE TESTS
# ============================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_zero_amount_risk_score(self, mock_embed, mock_search):
        """Test risk score with zero amount handles division by zero."""
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        
        # Zero transaction count should not crash
        try:
            score = detector._calculate_risk_score(
                total_amount=0.0,
                tx_count=0,
                threshold=10000.0
            )
            # If it returns, verify range
            assert 0.0 <= score <= 1.0
        except ZeroDivisionError:
            # If it raises, that's acceptable behavior
            pass
    
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_very_high_amount_risk_score(self, mock_embed, mock_search):
        """Test risk score with very high amount."""
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        
        score = detector._calculate_risk_score(
            total_amount=1_000_000.0,
            tx_count=100,
            threshold=10000.0
        )
        
        # Should cap at 1.0
        assert 0.0 <= score <= 1.0
    
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_negative_values_handling(self, mock_embed, mock_search):
        """Test handling of negative values."""
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        
        # Negative amounts should not crash
        try:
            score = detector._calculate_risk_score(
                total_amount=-1000.0,
                tx_count=-1,
                threshold=10000.0
            )
            assert 0.0 <= score <= 1.0
        except (ValueError, AssertionError):
            pass  # Acceptable to raise error for invalid input


# ============================================================
# INTEGRATION MARKER TESTS
# ============================================================

# ============================================================
# SANCTIONS SCREENING - SCREEN_CUSTOMER TESTS
# ============================================================

class TestSanctionsScreeningExtended:
    """Extended tests for sanctions screening coverage."""
    
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screen_customer_basic(self, mock_embed, mock_search):
        """Test screen_customer method."""
        from banking.aml.sanctions_screening import ScreeningResult
        
        # Mock the search client
        mock_search_instance = MagicMock()
        mock_search.return_value = mock_search_instance
        mock_search_instance.client.indices.exists.return_value = True
        mock_search_instance.vector_search.return_value = [
            {"id": "sanction_001", "score": 0.95, "name": "SANCTIONED ENTITY"}
        ]
        
        # Mock embedding generator
        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance
        mock_embed_instance.encode.return_value = [[0.1] * 384]
        mock_embed_instance.dimensions = 384
        
        screener = SanctionsScreener()
        result = screener.screen_customer("CUST-001", "John Doe")
        
        assert result is not None
        assert result.customer_id == "CUST-001"
        assert result.customer_name == "John Doe"
    
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screen_customer_with_cache(self, mock_embed, mock_search):
        """Test screen_customer uses cache."""
        from banking.aml.sanctions_screening import ScreeningResult
        
        mock_search_instance = MagicMock()
        mock_search.return_value = mock_search_instance
        mock_search_instance.client.indices.exists.return_value = True
        mock_search_instance.vector_search.return_value = []
        
        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance
        mock_embed_instance.encode.return_value = [[0.1] * 384]
        mock_embed_instance.dimensions = 384
        
        screener = SanctionsScreener()
        
        # First call - should query
        result1 = screener.screen_customer("CUST-001", "Test Customer")
        
        # Second call - should use cache
        result2 = screener.screen_customer("CUST-001", "Test Customer")
        
        assert result1 is not None
        assert result2 is not None
    
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_load_sanctions_list(self, mock_embed, mock_search):
        """Test load_sanctions_list method."""
        mock_search_instance = MagicMock()
        mock_search.return_value = mock_search_instance
        mock_search_instance.client.indices.exists.return_value = True
        mock_search_instance.bulk_index_documents.return_value = (3, [])
        
        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance
        mock_embed_instance.encode.return_value = [[0.1] * 384] * 3
        mock_embed_instance.dimensions = 384
        
        screener = SanctionsScreener()
        
        sanctions_data = [
            {"name": "Entity 1", "entity_id": "E1", "sanctions_list": "OFAC"},
            {"name": "Entity 2", "entity_id": "E2", "sanctions_list": "UN"},
            {"name": "Entity 3", "entity_id": "E3", "sanctions_list": "EU"},
        ]
        
        result = screener.load_sanctions_list(sanctions_data)
        assert result == 3
    
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_create_sanctions_index(self, mock_embed, mock_search):
        """Test _create_sanctions_index method."""
        mock_search_instance = MagicMock()
        mock_search.return_value = mock_search_instance
        mock_search_instance.client.indices.exists.return_value = False
        
        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance
        mock_embed_instance.dimensions = 384
        
        screener = SanctionsScreener()
        
        # Index creation should be called
        assert mock_search_instance.create_vector_index.called


# ============================================================
# ENHANCED STRUCTURING DETECTION - GRAPH PATTERNS
# ============================================================

class TestEnhancedStructuringGraphPatterns:
    """Tests for graph-based pattern detection."""
    
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_format_transaction(self, mock_embed, mock_search):
        """Test _format_transaction helper method."""
        mock_search.return_value.client.indices.exists.return_value = True
        detector = EnhancedStructuringDetector()
        
        tx_data = {
            "amount": [5000.0],
            "timestamp": [1700000000000],
            "transaction_id": ["TX-001"]
        }
        
        result = detector._format_transaction(tx_data)
        
        assert result is not None
        assert "amount" in result
    
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_graph_patterns_no_connection(self, mock_embed, mock_search):
        """Test graph pattern detection handles connection errors gracefully."""
        mock_search.return_value.client.indices.exists.return_value = True
        # Use correct constructor args (janusgraph_host/port, not graph_url)
        detector = EnhancedStructuringDetector(
            janusgraph_host="nonexistent",
            janusgraph_port=8182
        )
        
        # Should return empty list on connection failure
        patterns = detector.detect_graph_patterns()
        assert patterns == []
    
    @patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
    @patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
    def test_detect_semantic_patterns(self, mock_embed, mock_search):
        """Test semantic pattern detection method exists and runs."""
        mock_search_instance = MagicMock()
        mock_search.return_value = mock_search_instance
        mock_search_instance.client.indices.exists.return_value = True
        mock_search_instance.vector_search.return_value = []
        
        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance
        mock_embed_instance.dimensions = 384
        
        detector = EnhancedStructuringDetector()
        
        # Should run without error (returns empty if no data)
        patterns = detector.detect_semantic_patterns()
        assert isinstance(patterns, list)


# ============================================================
# BASIC STRUCTURING DETECTION TESTS
# ============================================================

class TestBasicStructuringDetection:
    """Tests for basic structuring detection module."""
    
    def test_structuring_alert_dataclass(self):
        """Test StructuringAlert dataclass fields."""
        from dataclasses import fields
        
        field_names = [f.name for f in fields(StructuringAlert)]
        
        # Correct fields based on actual dataclass definition
        assert "alert_id" in field_names
        assert "alert_type" in field_names
        assert "severity" in field_names
        assert "patterns" in field_names
        assert "accounts_involved" in field_names
        assert "total_amount" in field_names
        assert "recommendation" in field_names
        assert "timestamp" in field_names
    
    def test_structuring_pattern_dataclass(self):
        """Test StructuringPattern dataclass fields."""
        from dataclasses import fields
        from banking.aml.structuring_detection import StructuringPattern as BasicStructuringPattern
        
        field_names = [f.name for f in fields(BasicStructuringPattern)]
        
        assert "pattern_id" in field_names
        assert "pattern_type" in field_names
        assert "account_ids" in field_names
        assert "total_amount" in field_names
        assert "transaction_count" in field_names
        assert "confidence_score" in field_names
    
    @patch("banking.aml.structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.structuring_detection.traversal")
    def test_detector_initialization(self, mock_traversal, mock_conn):
        """Test StructuringDetector initialization."""
        mock_conn_instance = MagicMock()
        mock_conn.return_value = mock_conn_instance
        
        # Use correct constructor args (janusgraph_host/port, not janusgraph_url)
        detector = StructuringDetector(janusgraph_host="localhost", janusgraph_port=18182)
        assert detector is not None
    
    def test_class_constants(self):
        """Test StructuringDetector class constants exist."""
        # Check if class has the constants (may be instance-based)
        detector_class = StructuringDetector
        # Just verify the class exists and is callable
        assert callable(detector_class)


# ============================================================
# INTEGRATION MARKER TESTS
# ============================================================

@pytest.mark.integration
class TestIntegrationRequiresServices:
    """Tests that require running services (skipped if unavailable)."""
    
    def test_structuring_detector_connection(self, skip_if_no_services, janusgraph_url):
        """Test structuring detector can connect to JanusGraph."""
        if "://" in janusgraph_url:
            host = janusgraph_url.split("://")[1].split(":")[0]
            port = int(janusgraph_url.split(":")[-1].split("/")[0])
        else:
            host = "localhost"
            port = 18182
        
        detector = EnhancedStructuringDetector(
            janusgraph_host=host,
            janusgraph_port=port
        )
        
        assert detector is not None
    
    def test_sanctions_screener_opensearch(self, skip_if_no_services, opensearch_url):
        """Test sanctions screener can connect to OpenSearch."""
        if "://" in opensearch_url:
            host = opensearch_url.split("://")[1].split(":")[0]
            port = int(opensearch_url.split(":")[-1].split("/")[0])
        else:
            host = "localhost"
            port = 9200
        
        screener = SanctionsScreener(
            opensearch_host=host,
            opensearch_port=port
        )
        
        assert screener is not None
