# ADR-011: LRU-Based Query Caching Strategy

**Status**: Accepted
**Date**: 2026-01-25
**Deciders**: Performance Team, Development Team
**Technical Story**: Performance Optimization P3-002

## Context

Performance profiling revealed that many Gremlin queries were being executed repeatedly with identical parameters, causing unnecessary load on JanusGraph and HCD. Query execution times ranged from 100ms to 2000ms, with some queries being executed hundreds of times per minute. We needed an intelligent caching strategy to:

- Reduce database load
- Improve response times
- Minimize memory usage
- Handle cache invalidation effectively
- Support different caching strategies for different query types

### Problem Statement

How do we implement an effective query caching system that significantly improves performance while maintaining data consistency and managing memory efficiently?

### Constraints

- Maximum cache size: 100MB (configurable)
- Must support TTL-based expiration
- Should handle cache invalidation on writes
- Must work with existing Python client
- Cannot cache sensitive data
- Must be thread-safe

### Assumptions

- Read-heavy workload (80% reads, 20% writes)
- Query results are relatively stable
- Memory is available for caching
- Cache hit rate target: 70-90%
- Acceptable staleness: 5 minutes for most queries

## Decision Drivers

- **Performance**: Significant reduction in query execution time
- **Memory Efficiency**: Optimal use of available memory
- **Simplicity**: Easy to implement and maintain
- **Flexibility**: Support multiple eviction strategies
- **Consistency**: Proper cache invalidation on updates
- **Observability**: Metrics for cache performance

## Considered Options

### Option 1: No Caching (Status Quo)

**Pros:**

- Simple - no additional complexity
- Always fresh data
- No memory overhead

**Cons:**

- Poor performance for repeated queries
- High database load
- Slow response times
- Wasted resources

### Option 2: Simple TTL-Based Cache

**Pros:**

- Simple to implement
- Predictable behavior
- Automatic expiration

**Cons:**

- No memory management
- May cache rarely-used data
- Fixed expiration regardless of usage
- No eviction strategy

### Option 3: LRU (Least Recently Used) Cache

**Pros:**

- Efficient memory usage
- Keeps frequently accessed data
- Automatic eviction of old data
- Well-understood algorithm
- Good for read-heavy workloads

**Cons:**

- Doesn't consider access frequency
- May evict data that's accessed regularly but not recently
- Requires tracking access times

### Option 4: LFU (Least Frequently Used) Cache

**Pros:**

- Keeps most frequently accessed data
- Good for stable access patterns
- Considers long-term usage

**Cons:**

- Slow to adapt to changing patterns
- Requires tracking access counts
- May keep old popular data too long
- More complex implementation

### Option 5: Hybrid LRU + TTL Cache

**Pros:**

- Combines benefits of both strategies
- Memory-efficient with automatic expiration
- Flexible and adaptable
- Handles both temporal and spatial locality

**Cons:**

- More complex implementation
- Requires tuning multiple parameters
- Higher overhead

## Decision

**We will implement a hybrid LRU + TTL caching strategy with the following features:**

1. **Primary Strategy**: LRU for memory management
2. **TTL**: Configurable time-to-live (default: 5 minutes)
3. **Size Limit**: Maximum cache size (default: 100MB)
4. **Dependency Tracking**: Invalidate related queries on writes
5. **Cache Warming**: Pre-populate cache with common queries
6. **Metrics**: Track hit rate, miss rate, evictions

### Architecture

```python
QueryCache
├── LRU Eviction (memory management)
├── TTL Expiration (data freshness)
├── Dependency Tracking (consistency)
├── Cache Warming (performance)
└── Metrics Collection (observability)
```

### Rationale

The hybrid LRU + TTL approach provides:

- **Performance**: 70-90% cache hit rate expected
- **Memory Efficiency**: LRU ensures optimal memory usage
- **Data Freshness**: TTL prevents stale data
- **Consistency**: Dependency tracking for write invalidation
- **Flexibility**: Configurable for different workloads
- **Observability**: Built-in metrics for monitoring

## Consequences

### Positive

- **70% Faster Queries**: Cached queries return in <10ms vs 100-2000ms
- **Reduced Database Load**: 70-90% reduction in database queries
- **Better Scalability**: Can handle more concurrent users
- **Improved User Experience**: Faster response times
- **Lower Infrastructure Costs**: Reduced database resource usage
- **Predictable Performance**: Consistent response times for cached queries

### Negative

- **Memory Usage**: 100MB additional memory per instance
- **Complexity**: Additional code to maintain
- **Stale Data Risk**: Cached data may be up to TTL old
- **Cache Warming Overhead**: Initial cache population takes time
- **Invalidation Complexity**: Must track dependencies correctly

### Neutral

- **Configuration Required**: Need to tune TTL and size limits
- **Monitoring Needed**: Must track cache metrics
- **Testing Complexity**: Need to test cache behavior

## Implementation

### Required Changes

1. **Cache Module** (`src/python/performance/query_cache.py`):

   ```python
   class QueryCache:
       - LRU eviction logic
       - TTL expiration checking
       - Thread-safe operations
       - Metrics collection
   ```

2. **Cached Executor** (`src/python/performance/query_cache.py`):

   ```python
   class CachedQueryExecutor:
       - Cache key generation
       - Query execution with caching
       - Result serialization
   ```

3. **Cache Warmer** (`src/python/performance/query_cache.py`):

   ```python
   class CacheWarmer:
       - Pre-populate common queries
       - Scheduled cache refresh
   ```

4. **Dependency Tracking**:
   - Track which queries depend on which resources
   - Invalidate dependent queries on writes
   - Support wildcard invalidation

5. **Configuration**:

   ```yaml
   cache:
     max_size_mb: 100
     default_ttl_seconds: 300
     strategy: lru
     enable_compression: false
   ```

6. **Metrics**:
   - Cache hit rate
   - Cache miss rate
   - Eviction count
   - Memory usage
   - Average query time (cached vs uncached)

### Migration Path

**Phase 1: Development (Week 1)**

1. Implement core caching logic
2. Add unit tests
3. Benchmark performance improvements
4. Document usage

**Phase 2: Staging (Week 2)**

1. Deploy with conservative settings (50MB, 10min TTL)
2. Monitor cache metrics
3. Tune parameters based on workload
4. Validate invalidation logic

**Phase 3: Production (Week 3)**

1. Deploy with optimized settings
2. Enable cache warming for common queries
3. Monitor performance improvements
4. Create dashboards and alerts

**Phase 4: Optimization (Week 4)**

1. Analyze cache patterns
2. Optimize cache key generation
3. Fine-tune TTL per query type
4. Implement advanced features (compression, etc.)

### Rollback Strategy

If caching causes issues:

1. Disable caching via environment variable
2. Clear all cache entries
3. Monitor for data consistency issues
4. Analyze root cause
5. Fix and re-enable with conservative settings

## Compliance

- [x] Security review completed (no sensitive data cached)
- [x] Performance impact assessed (70% improvement expected)
- [x] Memory usage validated (100MB acceptable)
- [x] Documentation updated
- [x] Team trained on cache usage

## References

- [LRU Cache Algorithm](https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU))
- [Python functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.lru_cache)
- [Redis Caching Best Practices](https://redis.io/docs/manual/patterns/caching/)
- [Cache Invalidation Strategies](https://martinfowler.com/bliki/TwoHardThings.html)

## Notes

### Cache Key Generation

Cache keys are generated using:

```python
hash(query_string + str(parameters))
```

This ensures:

- Identical queries with same parameters share cache entries
- Different parameters create different cache entries
- Consistent key generation across instances

### Cache Invalidation Strategies

1. **TTL-Based**: Automatic expiration after configured time
2. **Write-Through**: Invalidate on write operations
3. **Dependency-Based**: Invalidate related queries
4. **Manual**: Explicit cache clearing via API

### Monitoring Metrics

Track these key metrics:

- **Hit Rate**: Target 70-90%
- **Miss Rate**: Should decrease over time
- **Eviction Rate**: Should be low (<10%)
- **Memory Usage**: Should stay under limit
- **Average Response Time**: Should improve 70%

### Query Types and Caching

| Query Type | Cache? | TTL | Reason |
|------------|--------|-----|--------|
| Read-only queries | Yes | 5 min | Safe to cache |
| Aggregations | Yes | 10 min | Expensive, stable |
| User-specific | Yes | 2 min | Personalized but cacheable |
| Write operations | No | N/A | Must be fresh |
| Real-time data | No | N/A | Requires freshness |

### Best Practices

1. **Cache Warming**: Pre-populate cache on startup
2. **Monitoring**: Track cache metrics continuously
3. **TTL Tuning**: Adjust based on data volatility
4. **Size Limits**: Set based on available memory
5. **Invalidation**: Be aggressive with write invalidation
6. **Testing**: Test cache behavior thoroughly
7. **Documentation**: Document what's cached and why

### Future Enhancements

- **Distributed Caching**: Redis for multi-instance caching
- **Intelligent TTL**: Adaptive TTL based on query patterns
- **Compression**: Compress large result sets
- **Tiered Caching**: Memory + disk caching
- **ML-Based Eviction**: Predict query access patterns
- **Cache Preloading**: Predictive cache warming
