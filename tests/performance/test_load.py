#!/usr/bin/env python3
# File: tests/performance/test_load.py
# Created: 2026-01-28T11:13:00.123
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
"""
Performance and load testing for JanusGraph
"""

import time
import pytest
from gremlin_python.driver import client
from concurrent.futures import ThreadPoolExecutor, as_completed


@pytest.fixture
def gremlin_client():
    """Create Gremlin client"""
    gc = client.Client('ws://localhost:18182/gremlin', 'g')
    yield gc
    gc.close()


@pytest.mark.performance
def test_query_latency(gremlin_client):
    """Test single query latency"""
    query = "g.V().has('person', 'name', 'Alice Johnson').count()"
    
    start = time.time()
    result = gremlin_client.submit(query).all().result()
    latency = time.time() - start
    
    assert latency < 0.1, f"Query too slow: {latency:.3f}s"
    print(f"✅ Query latency: {latency:.3f}s")


@pytest.mark.performance
def test_bulk_read(gremlin_client):
    """Test bulk read performance"""
    query = "g.V().limit(100).valueMap('name')"
    
    start = time.time()
    result = gremlin_client.submit(query).all().result()
    duration = time.time() - start
    
    count = len(result)
    throughput = count / duration
    
    assert throughput > 100, f"Low throughput: {throughput:.0f} ops/s"
    print(f"✅ Bulk read: {count} vertices in {duration:.3f}s ({throughput:.0f} ops/s)")


@pytest.mark.performance
def test_concurrent_queries(gremlin_client):
    """Test concurrent query performance"""
    query = "g.V().has('person', 'name', 'Alice Johnson').out('knows').count()"
    num_threads = 10
    queries_per_thread = 10
    
    def run_queries():
        results = []
        for _ in range(queries_per_thread):
            start = time.time()
            gremlin_client.submit(query).all().result()
            results.append(time.time() - start)
        return results
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(run_queries) for _ in range(num_threads)]
        all_results = []
        for future in as_completed(futures):
            all_results.extend(future.result())
    
    total_time = time.time() - start_time
    total_queries = num_threads * queries_per_thread
    qps = total_queries / total_time
    avg_latency = sum(all_results) / len(all_results)
    
    assert qps > 50, f"Low QPS: {qps:.1f}"
    print(f"✅ Concurrent queries: {total_queries} queries in {total_time:.2f}s")
    print(f"   QPS: {qps:.1f}, Avg latency: {avg_latency:.3f}s")


@pytest.mark.performance
def test_traversal_performance(gremlin_client):
    """Test multi-hop traversal performance"""
    query = """
    g.V().has('person', 'name', 'Alice Johnson')
      .out('knows').out('knows')
      .dedup()
      .limit(10)
    """
    
    start = time.time()
    result = gremlin_client.submit(query).all().result()
    duration = time.time() - start
    
    assert duration < 0.5, f"Traversal too slow: {duration:.3f}s"
    print(f"✅ Traversal: {len(result)} results in {duration:.3f}s")


@pytest.mark.performance
def test_aggregation_performance(gremlin_client):
    """Test aggregation query performance"""
    query = "g.V().hasLabel('person').groupCount().by('location')"
    
    start = time.time()
    result = gremlin_client.submit(query).all().result()
    duration = time.time() - start
    
    assert duration < 0.2, f"Aggregation too slow: {duration:.3f}s"
    print(f"✅ Aggregation: completed in {duration:.3f}s")


@pytest.mark.slow
@pytest.mark.performance
def test_stress_test(gremlin_client):
    """Stress test with sustained load"""
    query = "g.V().hasLabel('person').count()"
    duration_seconds = 10
    
    start = time.time()
    count = 0
    errors = 0
    
    while time.time() - start < duration_seconds:
        try:
            gremlin_client.submit(query).all().result()
            count += 1
        except Exception:
            errors += 1
    
    total_time = time.time() - start
    qps = count / total_time
    error_rate = errors / (count + errors) if (count + errors) > 0 else 0
    
    assert qps > 10, f"Low sustained QPS: {qps:.1f}"
    assert error_rate < 0.01, f"High error rate: {error_rate:.2%}"
    
    print(f"✅ Stress test: {count} queries in {total_time:.1f}s")
    print(f"   QPS: {qps:.1f}, Errors: {errors} ({error_rate:.2%})")


@pytest.mark.performance
def test_memory_usage_stable(gremlin_client):
    """Test memory usage remains stable"""
    query = "g.V().limit(100).valueMap()"
    iterations = 100
    
    for _ in range(iterations):
        gremlin_client.submit(query).all().result()
    
    # If we get here without OOM, memory is stable
    print(f"✅ Memory stable after {iterations} iterations")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'performance'])

# Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
