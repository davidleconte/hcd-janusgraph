"""
100% coverage tests for sanctions_screening.py.

Covers:
- Cache expiration (lines 107-115)
- Cache eviction when at capacity (lines 124-125)
- Cache clear method (lines 131-134)
- Branch coverage for min_score default (line 305-306)
- Branch coverage for cache usage with customer context (lines 309-314)
- Error handling branches (lines 507-508)
"""

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from banking.aml.sanctions_screening import (
    TTLCache,
    ScreeningResult,
    SanctionMatch,
    SanctionsScreener,
)


class TestScreeningCacheExpiration:
    """Test cache TTL expiration."""

    def test_cache_expiration_removes_stale_entries(self):
        """Test that expired cache entries are removed and counted as misses."""
        cache = TTLCache(maxsize=10, ttl_seconds=1)
        
        # Create a screening result
        result = ScreeningResult(
            customer_id="c-1",
            customer_name="John Doe",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=1.0
        )
        
        # Cache the result
        cache.set("c-1", "John Doe", result)
        
        # Verify it's cached
        cached_result, found = cache.get("c-1", "John Doe")
        assert found is True
        assert cached_result == result
        assert cache._hits == 1
        assert cache._misses == 0
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Try to get expired entry
        cached_result, found = cache.get("c-1", "John Doe")
        assert found is False
        assert cached_result is None
        assert cache._hits == 1
        assert cache._misses == 1


class TestScreeningCacheEviction:
    """Test cache eviction when at capacity."""

    def test_cache_evicts_oldest_entry_when_full(self):
        """Test that oldest entry is evicted when cache reaches maxsize."""
        cache = TTLCache(maxsize=2, ttl_seconds=3600)
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create screening results
        result1 = ScreeningResult(
            customer_id="c-1",
            customer_name="John Doe",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=timestamp,
            confidence=1.0
        )
        result2 = ScreeningResult(
            customer_id="c-2",
            customer_name="Jane Smith",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=timestamp,
            confidence=1.0
        )
        result3 = ScreeningResult(
            customer_id="c-3",
            customer_name="Bob Johnson",
            is_match=False,
            is_fuzzy_match=False,
            matches=[],
            screening_timestamp=timestamp,
            confidence=1.0
        )
        
        # Fill cache to capacity
        cache.set("c-1", "John Doe", result1)
        time.sleep(0.01)  # Ensure different timestamps
        cache.set("c-2", "Jane Smith", result2)
        
        # Verify both are cached
        _, found1 = cache.get("c-1", "John Doe")
        _, found2 = cache.get("c-2", "Jane Smith")
        assert found1 is True
        assert found2 is True
        
        # Add third entry (should evict oldest)
        time.sleep(0.01)
        cache.set("c-3", "Bob Johnson", result3)
        
        # Verify oldest (c-1) was evicted
        _, found1 = cache.get("c-1", "John Doe")
        _, found2 = cache.get("c-2", "Jane Smith")
        _, found3 = cache.get("c-3", "Bob Johnson")
        assert found1 is False  # Evicted
        assert found2 is True   # Still cached
        assert found3 is True   # Newly added


class TestScreeningCacheClear:
    """Test cache clear functionality."""

    def test_cache_clear_removes_all_entries_and_resets_stats(self):
        """Test that clear() removes all entries and resets statistics."""
        cache = TTLCache(maxsize=10, ttl_seconds=3600)
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Add multiple entries
        for i in range(5):
            result = ScreeningResult(
                customer_id=f"c-{i}",
                customer_name=f"Customer {i}",
                is_match=False,
                is_fuzzy_match=False,
                matches=[],
                screening_timestamp=timestamp,
                confidence=1.0
            )
            cache.set(f"c-{i}", f"Customer {i}", result)
        
        # Generate some hits and misses
        cache.get("c-1", "Customer 1")  # Hit
        cache.get("c-2", "Customer 2")  # Hit
        cache.get("c-99", "Unknown")    # Miss
        
        # Verify stats before clear
        stats = cache.stats()
        assert stats["size"] == 5
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        
        # Clear cache
        cache.clear()
        
        # Verify all entries removed and stats reset
        stats = cache.stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0
        
        # Verify entries are gone
        _, found = cache.get("c-1", "Customer 1")
        assert found is False


class TestSanctionsScreenerMinScoreDefault:
    """Test min_score default parameter handling."""

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screen_customer_uses_default_min_score_when_none(self, mock_embed, mock_search):
        """Test that min_score defaults to LOW_RISK_THRESHOLD when None."""
        mock_search.return_value.client.indices.exists.return_value = True
        mock_search.return_value.search.return_value = []
        
        screener = SanctionsScreener()
        
        # Call without min_score parameter (should use default)
        result = screener.screen_customer(
            customer_id="c-1",
            customer_name="John Doe"
            # min_score not provided, should default to LOW_RISK_THRESHOLD
        )
        
        # Verify result (no matches expected with empty search results)
        assert result.is_match is False
        assert len(result.matches) == 0


class TestSanctionsScreenerCacheWithContext:
    """Test cache behavior with customer context parameters."""

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screen_customer_bypasses_cache_with_country_context(self, mock_embed, mock_search):
        """Test that cache is bypassed when customer_country is provided."""
        mock_search.return_value.client.indices.exists.return_value = True
        mock_search.return_value.search.return_value = []
        
        screener = SanctionsScreener()
        
        # First call with country context (should not cache)
        result1 = screener.screen_customer(
            customer_id="c-1",
            customer_name="John Doe",
            customer_country="US"
        )
        
        # Second call with same customer but different country (should not use cache)
        result2 = screener.screen_customer(
            customer_id="c-1",
            customer_name="John Doe",
            customer_country="RU"
        )
        
        # Verify both calls went through (not cached)
        assert result1.is_match is False
        assert result2.is_match is False
        
        # Verify cache stats show no hits (because cache was bypassed)
        stats = screener._cache.stats()
        assert stats["hits"] == 0

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screen_customer_bypasses_cache_with_entity_type_context(self, mock_embed, mock_search):
        """Test that cache is bypassed when customer_entity_type is provided."""
        mock_search.return_value.client.indices.exists.return_value = True
        mock_search.return_value.search.return_value = []
        
        screener = SanctionsScreener()
        
        # Call with entity type context (should not cache)
        result = screener.screen_customer(
            customer_id="c-1",
            customer_name="John Doe",
            customer_entity_type="individual"
        )
        
        # Verify cache was bypassed
        assert result.is_match is False
        stats = screener._cache.stats()
        assert stats["hits"] == 0

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screen_customer_uses_cache_without_context(self, mock_embed, mock_search):
        """Test that cache is used when no customer context is provided."""
        mock_search.return_value.client.indices.exists.return_value = True
        mock_search.return_value.search.return_value = []
        
        screener = SanctionsScreener()
        
        # First call (cache miss)
        result1 = screener.screen_customer(
            customer_id="c-1",
            customer_name="John Doe"
        )
        
        # Second call (should be cache hit)
        result2 = screener.screen_customer(
            customer_id="c-1",
            customer_name="John Doe"
        )
        
        # Verify cache was used
        assert result1.is_match is False
        assert result2.is_match is False
        stats = screener._cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1


class TestSanctionsScreenerErrorHandling:
    """Test error handling in sanctions screening."""

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_load_sanctions_list_handles_embedding_errors(self, mock_embed, mock_search):
        """Test that load_sanctions_list handles embedding generation errors gracefully."""
        mock_search.return_value.client.indices.exists.return_value = True
        # Mock bulk_index_documents to return success count and empty errors list
        mock_search.return_value.bulk_index_documents.return_value = (2, [])
        
        # Mock embedding generator to raise exception for one entry
        def mock_encode(name, generator):
            if "ERROR" in name:
                raise ValueError("Embedding generation failed")
            return [0.1] * 384
        
        with patch("banking.aml.sanctions_screening.encode_person_name", side_effect=mock_encode):
            screener = SanctionsScreener()
            
            sanctions_list = [
                {"name": "Valid Name", "list_name": "OFAC", "entity_type": "individual"},
                {"name": "ERROR Name", "list_name": "OFAC", "entity_type": "individual"},
                {"name": "Another Valid", "list_name": "UN", "entity_type": "entity"},
            ]
            
            # Should handle error and continue with other entries
            loaded_count = screener.load_sanctions_list(sanctions_list)
            
            # Verify only valid entries were loaded (2 out of 3)
            assert loaded_count == 2


class TestSanctionsScreenerClearCache:
    """Test clear_cache functionality."""

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_clear_cache_method(self, mock_embed, mock_search):
        """Test that clear_cache() clears the internal cache."""
        mock_search.return_value.client.indices.exists.return_value = True
        mock_search.return_value.search.return_value = []
        
        screener = SanctionsScreener()
        
        # Add some entries to cache
        screener.screen_customer("c-1", "John Doe")
        screener.screen_customer("c-2", "Jane Smith")
        
        # Verify cache has entries
        stats_before = screener._cache.stats()
        assert stats_before["size"] > 0
        
        # Clear cache
        screener.clear_cache()
        
        # Verify cache is empty
        stats_after = screener._cache.stats()
        assert stats_after["size"] == 0
        assert stats_after["hits"] == 0
        assert stats_after["misses"] == 0

# Made with Bob
