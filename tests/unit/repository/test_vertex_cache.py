"""Tests for _VertexCache LRU implementation.

Tests verify O(1) performance characteristics and correct LRU behavior.
"""

import pytest
from src.python.repository.graph_repository import _VertexCache


class TestVertexCacheLRU:
    """Test LRU cache implementation with OrderedDict."""

    def test_cache_basic_operations(self):
        """Test basic get/set operations."""
        cache = _VertexCache(max_size=3)
        
        # Set and get
        cache.set(("personId", "p1"), {"name": "Alice"})
        result = cache.get(("personId", "p1"))
        assert result == {"name": "Alice"}
        
        # Cache miss
        result = cache.get(("personId", "p2"))
        assert result is None

    def test_lru_eviction(self):
        """Test that least recently used items are evicted."""
        cache = _VertexCache(max_size=3)
        
        # Fill cache
        cache.set(("personId", "p1"), {"name": "Alice"})
        cache.set(("personId", "p2"), {"name": "Bob"})
        cache.set(("personId", "p3"), {"name": "Charlie"})
        
        # Access p1 to make it recently used
        cache.get(("personId", "p1"))
        
        # Add p4, should evict p2 (least recently used)
        cache.set(("personId", "p4"), {"name": "David"})
        
        # Verify p2 was evicted
        assert cache.get(("personId", "p2")) is None
        # Verify others still exist
        assert cache.get(("personId", "p1")) is not None
        assert cache.get(("personId", "p3")) is not None
        assert cache.get(("personId", "p4")) is not None

    def test_update_moves_to_end(self):
        """Test that updating an existing entry moves it to end (most recent)."""
        cache = _VertexCache(max_size=3)
        
        # Fill cache
        cache.set(("personId", "p1"), {"name": "Alice"})
        cache.set(("personId", "p2"), {"name": "Bob"})
        cache.set(("personId", "p3"), {"name": "Charlie"})
        
        # Update p1 (should move to end)
        cache.set(("personId", "p1"), {"name": "Alice Updated"})
        
        # Add p4, should evict p2 (now least recently used)
        cache.set(("personId", "p4"), {"name": "David"})
        
        # Verify p2 was evicted, p1 still exists
        assert cache.get(("personId", "p2")) is None
        assert cache.get(("personId", "p1"))["name"] == "Alice Updated"

    def test_cache_stats(self):
        """Test cache statistics tracking."""
        cache = _VertexCache(max_size=3)
        
        # Initial stats
        stats = cache.stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["hit_ratio"] == 0.0
        
        # Add items
        cache.set(("personId", "p1"), {"name": "Alice"})
        cache.set(("personId", "p2"), {"name": "Bob"})
        
        # Hit
        cache.get(("personId", "p1"))
        # Miss
        cache.get(("personId", "p3"))
        
        stats = cache.stats()
        assert stats["size"] == 2
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_ratio"] == 0.5
        assert stats["total_requests"] == 2

    def test_cache_eviction_tracking(self):
        """Test that evictions are tracked correctly."""
        cache = _VertexCache(max_size=2)
        
        # Fill cache
        cache.set(("personId", "p1"), {"name": "Alice"})
        cache.set(("personId", "p2"), {"name": "Bob"})
        
        # Trigger eviction
        cache.set(("personId", "p3"), {"name": "Charlie"})
        
        stats = cache.stats()
        assert stats["evictions"] == 1
        assert stats["size"] == 2

    def test_invalidate(self):
        """Test cache invalidation."""
        cache = _VertexCache(max_size=3)
        
        cache.set(("personId", "p1"), {"name": "Alice"})
        cache.set(("personId", "p2"), {"name": "Bob"})
        
        # Invalidate existing
        result = cache.invalidate(("personId", "p1"))
        assert result is True
        assert cache.get(("personId", "p1")) is None
        
        # Invalidate non-existing
        result = cache.invalidate(("personId", "p3"))
        assert result is False

    def test_invalidate_pattern(self):
        """Test pattern-based invalidation."""
        cache = _VertexCache(max_size=5)
        
        cache.set(("personId", "p1"), {"name": "Alice"})
        cache.set(("personId", "p2"), {"name": "Bob"})
        cache.set(("companyId", "c1"), {"name": "Acme"})
        cache.set(("companyId", "c2"), {"name": "TechCorp"})
        
        # Invalidate all persons
        count = cache.invalidate_pattern("personId")
        assert count == 2
        
        # Verify persons removed, companies remain
        assert cache.get(("personId", "p1")) is None
        assert cache.get(("personId", "p2")) is None
        assert cache.get(("companyId", "c1")) is not None
        assert cache.get(("companyId", "c2")) is not None

    def test_clear(self):
        """Test cache clearing."""
        cache = _VertexCache(max_size=3)
        
        cache.set(("personId", "p1"), {"name": "Alice"})
        cache.set(("personId", "p2"), {"name": "Bob"})
        
        cache.clear()
        
        stats = cache.stats()
        assert stats["size"] == 0
        assert cache.get(("personId", "p1")) is None
        assert cache.get(("personId", "p2")) is None

    def test_warm_cache(self):
        """Test cache warming with pre-fetched entries."""
        cache = _VertexCache(max_size=5)
        
        entries = [
            (("personId", "p1"), {"name": "Alice"}),
            (("personId", "p2"), {"name": "Bob"}),
            (("personId", "p3"), {"name": "Charlie"}),
        ]
        
        added = cache.warm(entries)
        assert added == 3
        
        # Verify entries are in cache
        assert cache.get(("personId", "p1"))["name"] == "Alice"
        assert cache.get(("personId", "p2"))["name"] == "Bob"
        assert cache.get(("personId", "p3"))["name"] == "Charlie"
        
        stats = cache.stats()
        assert stats["size"] == 3

    def test_warm_cache_respects_max_size(self):
        """Test that warming respects max_size limit."""
        cache = _VertexCache(max_size=2)
        
        entries = [
            (("personId", "p1"), {"name": "Alice"}),
            (("personId", "p2"), {"name": "Bob"}),
            (("personId", "p3"), {"name": "Charlie"}),
        ]
        
        added = cache.warm(entries)
        assert added == 2  # Only 2 added due to max_size
        
        stats = cache.stats()
        assert stats["size"] == 2

    def test_warm_cache_skips_existing(self):
        """Test that warming skips existing entries."""
        cache = _VertexCache(max_size=5)
        
        # Pre-populate
        cache.set(("personId", "p1"), {"name": "Alice"})
        
        entries = [
            (("personId", "p1"), {"name": "Alice Updated"}),  # Should skip
            (("personId", "p2"), {"name": "Bob"}),
        ]
        
        added = cache.warm(entries)
        assert added == 1  # Only p2 added
        
        # Verify p1 not updated
        assert cache.get(("personId", "p1"))["name"] == "Alice"

    def test_thread_safety_basic(self):
        """Test basic thread safety with concurrent operations."""
        import threading
        
        cache = _VertexCache(max_size=100)
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(10):
                    key = (f"thread{thread_id}", f"item{i}")
                    cache.set(key, {"value": i})
                    result = cache.get(key)
                    assert result is not None
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        
        # Verify cache is consistent
        stats = cache.stats()
        assert stats["size"] <= 100


class TestVertexCachePerformance:
    """Test performance characteristics of OrderedDict-based cache."""

    def test_get_is_constant_time(self):
        """Verify get() is O(1) regardless of cache size."""
        import time
        
        # Small cache
        small_cache = _VertexCache(max_size=100)
        for i in range(100):
            small_cache.set(("id", f"item{i}"), {"value": i})
        
        start = time.perf_counter()
        for _ in range(1000):
            small_cache.get(("id", "item50"))
        small_time = time.perf_counter() - start
        
        # Large cache
        large_cache = _VertexCache(max_size=10000)
        for i in range(10000):
            large_cache.set(("id", f"item{i}"), {"value": i})
        
        start = time.perf_counter()
        for _ in range(1000):
            large_cache.get(("id", "item5000"))
        large_time = time.perf_counter() - start
        
        # Large cache should not be significantly slower (allow 2x variance)
        assert large_time < small_time * 2, \
            f"Large cache get() too slow: {large_time:.6f}s vs {small_time:.6f}s"

    def test_set_is_constant_time(self):
        """Verify set() with eviction is O(1)."""
        import time
        
        cache = _VertexCache(max_size=1000)
        
        # Fill cache
        for i in range(1000):
            cache.set(("id", f"item{i}"), {"value": i})
        
        # Measure eviction time (should be O(1))
        start = time.perf_counter()
        for i in range(1000, 2000):
            cache.set(("id", f"item{i}"), {"value": i})
        elapsed = time.perf_counter() - start
        
        # Should complete quickly (< 0.1s for 1000 evictions)
        assert elapsed < 0.1, f"Eviction too slow: {elapsed:.6f}s"

# Made with Bob
