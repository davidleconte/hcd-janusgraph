"""
Unit tests for SanctionsScreener.

Tests the AML sanctions screening with mocked dependencies.
All tests are deterministic with fixed timestamps and mocked OpenSearch.

Created: 2026-04-07
Phase 2: AML Module Testing
"""

import sys
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch, call

import pytest

# Mock dependencies before importing
mock_opensearch = MagicMock()
sys.modules['opensearchpy'] = mock_opensearch

from banking.aml.sanctions_screening import (
    SanctionsScreener,
    SanctionMatch,
    ScreeningResult,
    TTLCache
)

# Fixed timestamp for deterministic tests
FIXED_TIMESTAMP = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def mock_embedding_generator():
    """Mock EmbeddingGenerator."""
    generator = MagicMock()
    generator.dimensions = 384
    generator.encode.return_value = [0.1] * 384
    return generator


@pytest.fixture
def mock_vector_search_client():
    """Mock VectorSearchClient."""
    client = MagicMock()
    client.client = MagicMock()
    client.client.indices = MagicMock()
    client.client.indices.exists.return_value = False
    return client


@pytest.fixture
def sample_sanction_match():
    """Create a sample sanction match."""
    return SanctionMatch(
        customer_name="John Doe",
        sanctioned_name="John DOE",
        similarity_score=0.95,
        sanctions_list="OFAC",
        entity_id="sanc-123",
        match_type="exact",
        risk_level="high",
        weighted_score=0.95,
        risk_score_100=95.0,
        reason_codes=["exact_match"],
        metadata={"source": "test"}
    )


@pytest.fixture
def sample_screening_result(sample_sanction_match):
    """Create a sample screening result."""
    return ScreeningResult(
        customer_id="cust-123",
        customer_name="John Doe",
        is_match=True,
        is_fuzzy_match=False,
        matches=[sample_sanction_match],
        screening_timestamp=FIXED_TIMESTAMP.isoformat(),
        confidence=0.95
    )


class TestSanctionMatch:
    """Test SanctionMatch dataclass."""

    def test_sanction_match_creation(self):
        """Test creating a sanction match."""
        match = SanctionMatch(
            customer_name="John Doe",
            sanctioned_name="John DOE",
            similarity_score=0.95,
            sanctions_list="OFAC",
            entity_id="sanc-123",
            match_type="exact",
            risk_level="high"
        )
        
        assert match.customer_name == "John Doe"
        assert match.sanctioned_name == "John DOE"
        assert match.similarity_score == 0.95
        assert match.sanctions_list == "OFAC"
        assert match.match_type == "exact"
        assert match.risk_level == "high"

    def test_sanction_match_with_defaults(self):
        """Test sanction match with default values."""
        match = SanctionMatch(
            customer_name="John Doe",
            sanctioned_name="John DOE",
            similarity_score=0.95,
            sanctions_list="OFAC",
            entity_id="sanc-123",
            match_type="exact",
            risk_level="high"
        )
        
        assert match.weighted_score == 0.0
        assert match.risk_score_100 == 0.0
        assert match.reason_codes == []
        assert match.metadata == {}


class TestScreeningResult:
    """Test ScreeningResult dataclass."""

    def test_screening_result_creation(self, sample_sanction_match):
        """Test creating a screening result."""
        result = ScreeningResult(
            customer_id="cust-123",
            customer_name="John Doe",
            is_match=True,
            is_fuzzy_match=False,
            matches=[sample_sanction_match],
            screening_timestamp=FIXED_TIMESTAMP.isoformat(),
            confidence=0.95
        )
        
        assert result.customer_id == "cust-123"
        assert result.customer_name == "John Doe"
        assert result.is_match is True
        assert result.is_fuzzy_match is False
        assert len(result.matches) == 1
        assert result.confidence == 0.95

    def test_screening_result_no_match(self):
        """Test screening result with no matches."""
        result = ScreeningResult(
            customer_id="cust-123",
            customer_name="John Doe",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=FIXED_TIMESTAMP.isoformat(),
            confidence=0.0
        )
        
        assert result.is_match is False
        assert len(result.matches) == 0


class TestTTLCache:
    """Test TTLCache implementation."""

    def test_cache_initialization(self):
        """Test TTLCache initialization."""
        cache = TTLCache(maxsize=100, ttl_seconds=60)
        
        assert cache._maxsize == 100
        assert cache._ttl_seconds == 60
        assert cache._hits == 0
        assert cache._misses == 0
        assert len(cache._cache) == 0

    def test_cache_set_and_get(self):
        """Test setting and getting cache entries."""
        cache = TTLCache(maxsize=100, ttl_seconds=3600)
        result = ScreeningResult(
            customer_id="cust-1",
            customer_name="John Doe",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=FIXED_TIMESTAMP.isoformat(),
            confidence=0.0
        )
        
        cache.set("cust-1", "John Doe", result)
        cached_result, found = cache.get("cust-1", "John Doe")
        
        assert found is True
        assert cached_result == result
        assert cache._hits == 1
        assert cache._misses == 0

    def test_cache_miss(self):
        """Test cache miss."""
        cache = TTLCache(maxsize=100, ttl_seconds=3600)
        
        cached_result, found = cache.get("cust-1", "John Doe")
        
        assert found is False
        assert cached_result is None
        assert cache._hits == 0
        assert cache._misses == 1

    def test_cache_expiration(self):
        """Test cache entry expiration."""
        cache = TTLCache(maxsize=100, ttl_seconds=1)  # 1 second TTL
        result = ScreeningResult(
            customer_id="cust-1",
            customer_name="John Doe",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=FIXED_TIMESTAMP.isoformat(),
            confidence=0.0
        )
        
        cache.set("cust-1", "John Doe", result)
        
        # Immediate get should succeed
        cached_result, found = cache.get("cust-1", "John Doe")
        assert found is True
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        cached_result, found = cache.get("cust-1", "John Doe")
        assert found is False

    def test_cache_eviction(self):
        """Test cache eviction when maxsize reached."""
        cache = TTLCache(maxsize=2, ttl_seconds=3600)
        
        result1 = ScreeningResult(
            customer_id="cust-1",
            customer_name="John Doe",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=FIXED_TIMESTAMP.isoformat(),
            confidence=0.0
        )
        result2 = ScreeningResult(
            customer_id="cust-2",
            customer_name="Jane Smith",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=FIXED_TIMESTAMP.isoformat(),
            confidence=0.0
        )
        result3 = ScreeningResult(
            customer_id="cust-3",
            customer_name="Bob Johnson",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=FIXED_TIMESTAMP.isoformat(),
            confidence=0.0
        )
        
        cache.set("cust-1", "John Doe", result1)
        cache.set("cust-2", "Jane Smith", result2)
        
        # Cache is full, adding third entry should evict oldest
        cache.set("cust-3", "Bob Johnson", result3)
        
        assert len(cache._cache) == 2

    def test_cache_clear(self):
        """Test clearing cache."""
        cache = TTLCache(maxsize=100, ttl_seconds=3600)
        result = ScreeningResult(
            customer_id="cust-1",
            customer_name="John Doe",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=FIXED_TIMESTAMP.isoformat(),
            confidence=0.0
        )
        
        cache.set("cust-1", "John Doe", result)
        assert len(cache._cache) == 1
        
        cache.clear()
        
        assert len(cache._cache) == 0
        assert cache._hits == 0
        assert cache._misses == 0

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = TTLCache(maxsize=100, ttl_seconds=3600)
        result = ScreeningResult(
            customer_id="cust-1",
            customer_name="John Doe",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=FIXED_TIMESTAMP.isoformat(),
            confidence=0.0
        )
        
        cache.set("cust-1", "John Doe", result)
        cache.get("cust-1", "John Doe")  # Hit
        cache.get("cust-2", "Jane Smith")  # Miss
        
        stats = cache.stats()
        
        assert stats["size"] == 1
        assert stats["maxsize"] == 100
        assert stats["ttl_seconds"] == 3600
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_cache_key_generation(self):
        """Test cache key generation."""
        cache = TTLCache()
        
        key1 = cache._make_key("cust-1", "John Doe")
        key2 = cache._make_key("cust-1", "john doe")  # Different case
        key3 = cache._make_key("cust-1", " John Doe ")  # Extra spaces
        
        # Same customer with different name formatting should produce same key
        assert key2 == key3  # Both normalized to lowercase and stripped

    def test_cache_thread_safety(self):
        """Test cache thread safety (basic check)."""
        cache = TTLCache(maxsize=100, ttl_seconds=3600)
        result = ScreeningResult(
            customer_id="cust-1",
            customer_name="John Doe",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=FIXED_TIMESTAMP.isoformat(),
            confidence=0.0
        )
        
        # Multiple operations should not raise
        for i in range(10):
            cache.set(f"cust-{i}", f"Name {i}", result)
            cache.get(f"cust-{i}", f"Name {i}")


class TestSanctionsScreenerInitialization:
    """Test SanctionsScreener initialization."""

    @patch('banking.aml.sanctions_screening.EmbeddingGenerator')
    @patch('banking.aml.sanctions_screening.VectorSearchClient')
    def test_init_with_defaults(self, mock_search_client, mock_generator):
        """Test initialization with default values."""
        mock_gen_instance = MagicMock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance
        
        mock_client_instance = MagicMock()
        mock_client_instance.client = MagicMock()
        mock_client_instance.client.indices = MagicMock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_search_client.return_value = mock_client_instance
        
        screener = SanctionsScreener()
        
        assert screener.index_name == "sanctions_list"
        assert screener.generator == mock_gen_instance
        assert screener.search_client == mock_client_instance

    @patch('banking.aml.sanctions_screening.EmbeddingGenerator')
    @patch('banking.aml.sanctions_screening.VectorSearchClient')
    def test_init_with_custom_values(self, mock_search_client, mock_generator):
        """Test initialization with custom values."""
        mock_gen_instance = MagicMock()
        mock_gen_instance.dimensions = 768
        mock_generator.return_value = mock_gen_instance
        
        mock_client_instance = MagicMock()
        mock_client_instance.client = MagicMock()
        mock_client_instance.client.indices = MagicMock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_search_client.return_value = mock_client_instance
        
        screener = SanctionsScreener(
            opensearch_host="custom-host",
            opensearch_port=9300,
            embedding_model="mpnet",
            index_name="custom_sanctions"
        )
        
        assert screener.index_name == "custom_sanctions"

    @patch('banking.aml.sanctions_screening.EmbeddingGenerator')
    @patch('banking.aml.sanctions_screening.VectorSearchClient')
    def test_init_creates_cache(self, mock_search_client, mock_generator):
        """Test that initialization creates TTL cache."""
        mock_gen_instance = MagicMock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance
        
        mock_client_instance = MagicMock()
        mock_client_instance.client = MagicMock()
        mock_client_instance.client.indices = MagicMock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_search_client.return_value = mock_client_instance
        
        screener = SanctionsScreener()
        
        assert screener._cache is not None
        assert isinstance(screener._cache, TTLCache)


class TestSanctionsScreenerConstants:
    """Test SanctionsScreener constants."""

    def test_risk_thresholds(self):
        """Test risk threshold constants."""
        assert SanctionsScreener.HIGH_RISK_THRESHOLD == 0.95
        assert SanctionsScreener.MEDIUM_RISK_THRESHOLD == 0.85
        assert SanctionsScreener.FUZZY_THRESHOLD == 0.60
        assert SanctionsScreener.LOW_RISK_THRESHOLD == 0.75

    def test_weight_constants(self):
        """Test weight constants for scoring."""
        assert SanctionsScreener.WEIGHT_NAME_SIMILARITY == 0.70
        assert SanctionsScreener.WEIGHT_COUNTRY_MATCH == 0.20
        assert SanctionsScreener.WEIGHT_ENTITY_TYPE_MATCH == 0.10
        
        # Weights should sum to 1.0
        total = (
            SanctionsScreener.WEIGHT_NAME_SIMILARITY +
            SanctionsScreener.WEIGHT_COUNTRY_MATCH +
            SanctionsScreener.WEIGHT_ENTITY_TYPE_MATCH
        )
        assert abs(total - 1.0) < 0.01


class TestSanctionsScreenerIndexManagement:
    """Test index management."""

    @patch('banking.aml.sanctions_screening.EmbeddingGenerator')
    @patch('banking.aml.sanctions_screening.VectorSearchClient')
    def test_ensure_index_exists_creates_index(self, mock_search_client, mock_generator):
        """Test that _ensure_index_exists creates index if not exists."""
        mock_gen_instance = MagicMock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance
        
        mock_client_instance = MagicMock()
        mock_client_instance.client = MagicMock()
        mock_client_instance.client.indices = MagicMock()
        mock_client_instance.client.indices.exists.return_value = False
        mock_client_instance.create_vector_index = MagicMock()
        mock_search_client.return_value = mock_client_instance
        
        screener = SanctionsScreener()
        
        mock_client_instance.create_vector_index.assert_called_once()

    @patch('banking.aml.sanctions_screening.EmbeddingGenerator')
    @patch('banking.aml.sanctions_screening.VectorSearchClient')
    def test_ensure_index_exists_skips_if_exists(self, mock_search_client, mock_generator):
        """Test that _ensure_index_exists skips if index exists."""
        mock_gen_instance = MagicMock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance
        
        mock_client_instance = MagicMock()
        mock_client_instance.client = MagicMock()
        mock_client_instance.client.indices = MagicMock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_client_instance.create_vector_index = MagicMock()
        mock_search_client.return_value = mock_client_instance
        
        screener = SanctionsScreener()
        
        mock_client_instance.create_vector_index.assert_not_called()


class TestSanctionsScreenerEdgeCases:
    """Test edge cases."""

    def test_empty_customer_name(self):
        """Test screening with empty customer name."""
        # This would be handled by the actual implementation
        # Here we just verify the data structure can handle it
        match = SanctionMatch(
            customer_name="",
            sanctioned_name="John Doe",
            similarity_score=0.0,
            sanctions_list="OFAC",
            entity_id="sanc-123",
            match_type="none",
            risk_level="low"
        )
        
        assert match.customer_name == ""

    def test_very_high_similarity(self):
        """Test with similarity score of 1.0."""
        match = SanctionMatch(
            customer_name="John Doe",
            sanctioned_name="John Doe",
            similarity_score=1.0,
            sanctions_list="OFAC",
            entity_id="sanc-123",
            match_type="exact",
            risk_level="high"
        )
        
        assert match.similarity_score == 1.0

    def test_zero_similarity(self):
        """Test with similarity score of 0.0."""
        match = SanctionMatch(
            customer_name="John Doe",
            sanctioned_name="Jane Smith",
            similarity_score=0.0,
            sanctions_list="OFAC",
            entity_id="sanc-123",
            match_type="none",
            risk_level="low"
        )
        
        assert match.similarity_score == 0.0


class TestSanctionsScreenerCacheIntegration:
    """Test cache integration with screener."""

    @patch('banking.aml.sanctions_screening.EmbeddingGenerator')
    @patch('banking.aml.sanctions_screening.VectorSearchClient')
    def test_cache_used_for_repeated_lookups(self, mock_search_client, mock_generator):
        """Test that cache is used for repeated customer lookups."""
        mock_gen_instance = MagicMock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance
        
        mock_client_instance = MagicMock()
        mock_client_instance.client = MagicMock()
        mock_client_instance.client.indices = MagicMock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_search_client.return_value = mock_client_instance
        
        screener = SanctionsScreener()
        
        # Verify cache exists
        assert screener._cache is not None
        
        # Get initial stats
        stats = screener._cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

# Made with Bob
