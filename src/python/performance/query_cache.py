"""
Query Cache Module

Provides intelligent caching for JanusGraph queries with TTL,
invalidation strategies, and cache warming capabilities.
"""

import time
import logging
import hashlib
import pickle
from typing import Any, Optional, Callable, Dict, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache invalidation strategies."""
    TTL = "ttl"  # Time-to-live
    LRU = "lru"  # Least recently used
    LFU = "lfu"  # Least frequently used
    WRITE_THROUGH = "write_through"  # Invalidate on write
    WRITE_BEHIND = "write_behind"  # Async write with delayed invalidation


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl_seconds is None:
            return False
        
        age = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return age > self.ttl_seconds
    
    def touch(self):
        """Update access metadata."""
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    invalidations: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 100.0 - self.hit_rate


class QueryCache:
    """Intelligent query result cache."""
    
    def __init__(
        self,
        max_size_mb: int = 100,
        default_ttl_seconds: int = 300,
        strategy: CacheStrategy = CacheStrategy.LRU,
        enable_compression: bool = False
    ):
        """
        Initialize query cache.
        
        Args:
            max_size_mb: Maximum cache size in megabytes
            default_ttl_seconds: Default TTL for cache entries
            strategy: Cache eviction strategy
            enable_compression: Enable value compression
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_seconds
        self.strategy = strategy
        self.enable_compression = enable_compression
        
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = CacheStats()
        
        # Dependency tracking for invalidation
        self.dependencies: Dict[str, Set[str]] = {}  # resource -> cache_keys
        
        logger.info(
            f"Query Cache initialized: {max_size_mb}MB, "
            f"TTL={default_ttl_seconds}s, strategy={strategy.value}"
        )
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            self.stats.misses += 1
            logger.debug("Cache miss: %s", key)
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if entry.is_expired():
            self._remove_entry(key)
            self.stats.misses += 1
            logger.debug("Cache miss (expired): %s", key)
            return None
        
        # Update access metadata
        entry.touch()
        self.stats.hits += 1
        logger.debug("Cache hit: %s", key)
        
        return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        dependencies: Optional[List[str]] = None
    ):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional TTL override
            dependencies: Optional list of resource dependencies
        """
        # Calculate size
        size_bytes = self._calculate_size(value)
        
        # Check if we need to evict
        while self._should_evict(size_bytes):
            self._evict_one()
        
        # Create entry
        entry = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl_seconds or self.default_ttl_seconds,
            size_bytes=size_bytes
        )
        
        # Store entry
        self.cache[key] = entry
        self.stats.entry_count = len(self.cache)
        self.stats.total_size_bytes += size_bytes
        
        # Track dependencies
        if dependencies:
            for dep in dependencies:
                if dep not in self.dependencies:
                    self.dependencies[dep] = set()
                self.dependencies[dep].add(key)
        
        logger.debug("Cache set: %s (%s bytes)", key, size_bytes)
    
    def delete(self, key: str):
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
        """
        if key in self.cache:
            self._remove_entry(key)
            self.stats.invalidations += 1
            logger.debug("Cache invalidated: %s", key)
    
    def invalidate_by_dependency(self, resource: str):
        """
        Invalidate all cache entries dependent on a resource.
        
        Args:
            resource: Resource identifier
        """
        if resource not in self.dependencies:
            return
        
        keys_to_invalidate = list(self.dependencies[resource])
        for key in keys_to_invalidate:
            self.delete(key)
        
        del self.dependencies[resource]
        logger.info("Invalidated %s entries for resource: %s", len(keys_to_invalidate), resource)
    
    def clear(self):
        """Clear all cache entries."""
        count = len(self.cache)
        self.cache.clear()
        self.dependencies.clear()
        self.stats.entry_count = 0
        self.stats.total_size_bytes = 0
        logger.info("Cache cleared: %s entries removed", count)
    
    def _should_evict(self, new_entry_size: int) -> bool:
        """
        Check if eviction is needed.
        
        Args:
            new_entry_size: Size of new entry in bytes
        
        Returns:
            True if eviction needed
        """
        return (self.stats.total_size_bytes + new_entry_size) > self.max_size_bytes
    
    def _evict_one(self):
        """Evict one entry based on strategy."""
        if not self.cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # Evict least recently used
            key_to_evict = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].last_accessed
            )
        elif self.strategy == CacheStrategy.LFU:
            # Evict least frequently used
            key_to_evict = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].access_count
            )
        else:
            # Default: evict oldest
            key_to_evict = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].created_at
            )
        
        self._remove_entry(key_to_evict)
        self.stats.evictions += 1
        logger.debug("Cache evicted: %s", key_to_evict)
    
    def _remove_entry(self, key: str):
        """
        Remove entry from cache.
        
        Args:
            key: Cache key
        """
        if key in self.cache:
            entry = self.cache[key]
            self.stats.total_size_bytes -= entry.size_bytes
            del self.cache[key]
            self.stats.entry_count = len(self.cache)
            
            # Remove from dependencies
            for dep_keys in self.dependencies.values():
                dep_keys.discard(key)
    
    def _calculate_size(self, value: Any) -> int:
        """
        Calculate size of value in bytes.
        
        Args:
            value: Value to measure
        
        Returns:
            Size in bytes
        """
        try:
            return len(pickle.dumps(value))
        except Exception:
            # Fallback estimation
            return 1024
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'hits': self.stats.hits,
            'misses': self.stats.misses,
            'hit_rate': f"{self.stats.hit_rate:.2f}%",
            'miss_rate': f"{self.stats.miss_rate:.2f}%",
            'evictions': self.stats.evictions,
            'invalidations': self.stats.invalidations,
            'entry_count': self.stats.entry_count,
            'total_size_mb': self.stats.total_size_bytes / 1024 / 1024,
            'max_size_mb': self.max_size_bytes / 1024 / 1024
        }


class CachedQueryExecutor:
    """Executes queries with caching."""
    
    def __init__(self, cache: QueryCache):
        """
        Initialize cached query executor.
        
        Args:
            cache: Query cache instance
        """
        self.cache = cache
    
    def execute(
        self,
        query: str,
        execution_func: Callable,
        *args,
        cache_key: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        dependencies: Optional[List[str]] = None,
        force_refresh: bool = False,
        **kwargs
    ) -> Any:
        """
        Execute query with caching.
        
        Args:
            query: Query string
            execution_func: Function to execute query
            *args: Arguments for execution function
            cache_key: Optional custom cache key
            ttl_seconds: Optional TTL override
            dependencies: Optional resource dependencies
            force_refresh: Force cache refresh
            **kwargs: Keyword arguments for execution function
        
        Returns:
            Query result
        """
        # Generate cache key
        if cache_key is None:
            cache_key = self._generate_cache_key(query, args, kwargs)
        
        # Check cache (unless force refresh)
        if not force_refresh:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug("Returning cached result for: %s", cache_key)
                return cached_result
        
        # Execute query
        logger.debug("Executing query: %s", cache_key)
        result = execution_func(*args, **kwargs)
        
        # Cache result
        self.cache.set(
            cache_key,
            result,
            ttl_seconds=ttl_seconds,
            dependencies=dependencies
        )
        
        return result
    
    def _generate_cache_key(self, query: str, args: tuple, kwargs: dict) -> str:
        """
        Generate cache key from query and parameters.
        
        Args:
            query: Query string
            args: Positional arguments
            kwargs: Keyword arguments
        
        Returns:
            Cache key
        """
        # Create key from query and parameters
        key_parts = [query]
        
        if args:
            key_parts.append(str(args))
        
        if kwargs:
            # Sort kwargs for consistent keys
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(str(sorted_kwargs))
        
        key_string = '|'.join(key_parts)
        
        # Hash for consistent length
        return hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()


class CacheWarmer:
    """Warms cache with frequently used queries."""
    
    def __init__(self, cache: QueryCache, executor: CachedQueryExecutor):
        """
        Initialize cache warmer.
        
        Args:
            cache: Query cache instance
            executor: Cached query executor
        """
        self.cache = cache
        self.executor = executor
        self.warm_queries: List[Dict[str, Any]] = []
    
    def register_query(
        self,
        query: str,
        execution_func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        ttl_seconds: Optional[int] = None
    ):
        """
        Register query for cache warming.
        
        Args:
            query: Query string
            execution_func: Function to execute query
            args: Query arguments
            kwargs: Query keyword arguments
            ttl_seconds: Optional TTL
        """
        self.warm_queries.append({
            'query': query,
            'execution_func': execution_func,
            'args': args,
            'kwargs': kwargs or {},
            'ttl_seconds': ttl_seconds
        })
        logger.info("Registered query for warming: %s...", query[:50])
    
    def warm_cache(self):
        """Execute all registered queries to warm cache."""
        logger.info("Warming cache with %s queries...", len(self.warm_queries))
        
        for query_config in self.warm_queries:
            try:
                self.executor.execute(
                    query_config['query'],
                    query_config['execution_func'],
                    *query_config['args'],
                    ttl_seconds=query_config['ttl_seconds'],
                    force_refresh=True,
                    **query_config['kwargs']
                )
                logger.debug("Warmed: %s...", query_config['query'][:50])
            except Exception as e:
                logger.error("Failed to warm query: %s", e)
        
        logger.info("Cache warming complete")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize cache
    cache = QueryCache(
        max_size_mb=50,
        default_ttl_seconds=300,
        strategy=CacheStrategy.LRU
    )
    
    # Initialize executor
    executor = CachedQueryExecutor(cache)
    
    # Example query function
    def execute_query(query):
        time.sleep(0.1)  # Simulate query execution
        return [{'id': i, 'name': f'user{i}'} for i in range(10)]
    
    # Execute queries with caching
    query = "g.V().has('type', 'user').limit(10)"
    
    # First execution (cache miss)
    start = time.time()
    result1 = executor.execute(query, execute_query, query)
    time1 = time.time() - start
    print(f"First execution: {time1:.3f}s")
    
    # Second execution (cache hit)
    start = time.time()
    result2 = executor.execute(query, execute_query, query)
    time2 = time.time() - start
    print(f"Second execution: {time2:.3f}s (cached)")
    
    # Print stats
    stats = cache.get_stats()
    print(f"\nCache Stats:")
    print(json.dumps(stats, indent=2))
    
    # Cache warming example
    warmer = CacheWarmer(cache, executor)
    warmer.register_query(
        "g.V().has('type', 'product').limit(100)",
        execute_query,
        args=("g.V().has('type', 'product').limit(100)",)
    )
    warmer.warm_cache()

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
