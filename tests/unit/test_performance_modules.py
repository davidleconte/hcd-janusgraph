"""Tests for src/python/performance/ modules (query_profiler, query_cache, benchmark)."""

import json
import os
import tempfile
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.python.performance.query_profiler import QueryProfiler, QueryMetrics, QueryStatistics
from src.python.performance.query_cache import (
    QueryCache,
    CacheStrategy,
    CacheEntry,
    CacheStats,
    CachedQueryExecutor,
    CacheWarmer,
)
from src.python.performance.benchmark import (
    PerformanceBenchmark,
    BenchmarkResult,
    LoadTester,
    LoadTestResult,
    QueryBenchmarkSuite,
)


class TestQueryMetrics:
    def test_defaults(self):
        m = QueryMetrics(
            query_id="q1",
            query_hash="h1",
            query_text="g.V()",
            execution_time_ms=10.0,
            result_count=5,
            traversal_steps=2,
        )
        assert m.is_slow is False
        assert m.is_expensive is False
        assert m.optimization_hints == []
        assert m.memory_used_mb == 0.0
        assert m.compilation_time_ms == 0.0

    def test_with_optional_fields(self):
        m = QueryMetrics(
            query_id="q1",
            query_hash="h1",
            query_text="g.V()",
            execution_time_ms=10.0,
            result_count=5,
            traversal_steps=2,
            user_id="user1",
            trace_id="trace1",
        )
        assert m.user_id == "user1"
        assert m.trace_id == "trace1"


class TestQueryStatistics:
    def test_defaults(self):
        s = QueryStatistics(query_hash="h1", query_pattern="g.V()")
        assert s.execution_count == 0
        assert s.min_time_ms == float("inf")
        assert s.max_time_ms == 0.0


class TestQueryProfiler:
    def test_init(self):
        p = QueryProfiler(slow_query_threshold_ms=500.0, expensive_query_threshold_scans=5000)
        assert p.slow_query_threshold_ms == 500.0
        assert p.expensive_query_threshold_scans == 5000

    def test_profile_query_basic(self):
        p = QueryProfiler()
        result, metrics = p.profile_query("g.V().count()", lambda: [1, 2, 3])
        assert result == [1, 2, 3]
        assert metrics.result_count == 3
        assert metrics.execution_time_ms > 0
        assert len(p.query_metrics) == 1

    def test_profile_query_non_list_result(self):
        p = QueryProfiler()
        result, metrics = p.profile_query("g.V().count()", lambda: 42)
        assert result == 42
        assert metrics.result_count == 1

    def test_profile_query_with_args(self):
        p = QueryProfiler()
        func = MagicMock(return_value=[1])
        result, metrics = p.profile_query("q", func, "a", "b", user_id="u1", trace_id="t1")
        func.assert_called_once_with("a", "b")
        assert metrics.user_id == "u1"
        assert metrics.trace_id == "t1"

    def test_profile_query_exception(self):
        p = QueryProfiler()
        with pytest.raises(ValueError, match="boom"):
            p.profile_query("q", lambda: (_ for _ in ()).throw(ValueError("boom")))

    def test_slow_query_detection(self):
        p = QueryProfiler(slow_query_threshold_ms=1.0)
        _, metrics = p.profile_query("g.V()", lambda: time.sleep(0.01) or [])
        assert metrics.is_slow is True
        assert any("Slow query" in h for h in metrics.optimization_hints)

    def test_expensive_query_detection(self):
        p = QueryProfiler(expensive_query_threshold_scans=0)
        _, metrics = p.profile_query("g.V()", lambda: [])
        metrics.vertices_scanned = 100
        metrics.edges_scanned = 100
        p._analyze_performance(metrics)
        assert metrics.is_expensive is True

    def test_index_miss_hint(self):
        p = QueryProfiler()
        m = QueryMetrics(
            query_id="q1", query_hash="h1", query_text="g.V()",
            execution_time_ms=1.0, result_count=0, traversal_steps=1,
            index_hits=0, index_misses=5,
        )
        p._analyze_performance(m)
        assert any("index" in h.lower() for h in m.optimization_hints)

    def test_large_result_hint(self):
        p = QueryProfiler()
        m = QueryMetrics(
            query_id="q1", query_hash="h1", query_text="g.V()",
            execution_time_ms=1.0, result_count=2000, traversal_steps=1,
        )
        p._analyze_performance(m)
        assert any("Large result" in h for h in m.optimization_hints)

    def test_complex_traversal_hint(self):
        p = QueryProfiler()
        m = QueryMetrics(
            query_id="q1", query_hash="h1", query_text="g.V()",
            execution_time_ms=1.0, result_count=0, traversal_steps=15,
        )
        p._analyze_performance(m)
        assert any("Complex traversal" in h for h in m.optimization_hints)

    def test_hash_query_deterministic(self):
        p = QueryProfiler()
        h1 = p._hash_query("g.V().count()")
        h2 = p._hash_query("g.V().count()")
        h3 = p._hash_query("  g.V().count()  ")
        assert h1 == h2
        assert h1 == h3

    def test_count_traversal_steps(self):
        p = QueryProfiler()
        assert p._count_traversal_steps("g.V().has('name','x').out()") >= 1

    def test_extract_pattern(self):
        p = QueryProfiler()
        pattern = p._extract_pattern("g.V().has('name', 'John').limit(10)")
        assert "John" not in pattern
        assert "?" in pattern

    def test_statistics_update_with_multiple_queries(self):
        p = QueryProfiler()
        for i in range(5):
            p.profile_query("g.V().count()", lambda: [1])
        qhash = list(p.query_statistics.keys())[0]
        stats = p.query_statistics[qhash]
        assert stats.execution_count == 5
        assert stats.median_time_ms > 0

    def test_get_slow_queries(self):
        p = QueryProfiler(slow_query_threshold_ms=0.001)
        p.profile_query("slow", lambda: time.sleep(0.01) or [])
        p.profile_query("fast", lambda: [])
        slow = p.get_slow_queries(limit=1)
        assert len(slow) == 1

    def test_get_frequent_queries(self):
        p = QueryProfiler()
        for _ in range(3):
            p.profile_query("freq", lambda: [])
        p.profile_query("rare", lambda: [])
        freq = p.get_frequent_queries(limit=1)
        assert freq[0].execution_count == 3

    def test_get_expensive_queries(self):
        p = QueryProfiler()
        p.profile_query("q1", lambda: [])
        result = p.get_expensive_queries(limit=5)
        assert len(result) >= 1

    def test_generate_report_empty(self):
        p = QueryProfiler()
        report = p.generate_report()
        assert report["summary"]["total_queries"] == 0

    def test_generate_report_with_data(self):
        p = QueryProfiler()
        for i in range(3):
            p.profile_query(f"g.V().has('id', '{i}')", lambda: [1])
        report = p.generate_report()
        assert report["summary"]["total_queries"] == 3
        assert "top_slow_queries" in report
        assert "optimization_recommendations" in report

    def test_generate_recommendations_slow(self):
        p = QueryProfiler(slow_query_threshold_ms=0.001)
        p.profile_query("q", lambda: time.sleep(0.01) or [])
        recs = p._generate_recommendations()
        assert any("slow" in r.lower() for r in recs)

    def test_export_metrics(self):
        p = QueryProfiler()
        p.profile_query("g.V()", lambda: [1])
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            p.export_metrics(path)
            with open(path) as f:
                data = json.load(f)
            assert "metrics" in data
            assert "statistics" in data
        finally:
            os.unlink(path)

    def test_get_memory_usage_no_psutil(self):
        p = QueryProfiler()
        with patch.dict("sys.modules", {"psutil": None}):
            result = p._get_memory_usage()
            assert isinstance(result, float)


class TestCacheEntry:
    def test_not_expired_no_ttl(self):
        e = CacheEntry(key="k", value="v")
        assert e.is_expired() is False

    def test_not_expired_within_ttl(self):
        e = CacheEntry(key="k", value="v", ttl_seconds=3600)
        e.created_at = datetime.now(timezone.utc)
        assert e.is_expired() is False

    def test_expired(self):
        e = CacheEntry(key="k", value="v", ttl_seconds=1)
        e.created_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        assert e.is_expired() is True

    def test_touch(self):
        e = CacheEntry(key="k", value="v")
        old_count = e.access_count
        e.touch()
        assert e.access_count == old_count + 1


class TestCacheStats:
    def test_hit_rate_zero(self):
        s = CacheStats()
        assert s.hit_rate == 0.0
        assert s.miss_rate == 100.0

    def test_hit_rate(self):
        s = CacheStats(hits=3, misses=1)
        assert s.hit_rate == 75.0
        assert s.miss_rate == 25.0


class TestQueryCache:
    def test_get_miss(self):
        c = QueryCache()
        assert c.get("nonexistent") is None
        assert c.stats.misses == 1

    def test_set_and_get(self):
        c = QueryCache()
        c.set("k1", {"data": 1})
        result = c.get("k1")
        assert result == {"data": 1}
        assert c.stats.hits == 1

    def test_expired_entry(self):
        c = QueryCache(default_ttl_seconds=1)
        c.set("k1", "v1")
        c.cache["k1"].created_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        assert c.get("k1") is None
        assert c.stats.misses == 1

    def test_delete(self):
        c = QueryCache()
        c.set("k1", "v1")
        c.delete("k1")
        assert c.get("k1") is None
        assert c.stats.invalidations == 1

    def test_delete_nonexistent(self):
        c = QueryCache()
        c.delete("nope")
        assert c.stats.invalidations == 0

    def test_clear(self):
        c = QueryCache()
        c.set("k1", "v1")
        c.set("k2", "v2")
        c.clear()
        assert c.stats.entry_count == 0
        assert len(c.cache) == 0

    def test_dependency_invalidation(self):
        c = QueryCache()
        c.set("k1", "v1", dependencies=["resource_a"])
        c.set("k2", "v2", dependencies=["resource_a"])
        c.set("k3", "v3", dependencies=["resource_b"])
        c.invalidate_by_dependency("resource_a")
        assert c.get("k1") is None
        assert c.get("k2") is None
        assert c.get("k3") == "v3"

    def test_invalidate_nonexistent_dependency(self):
        c = QueryCache()
        c.invalidate_by_dependency("nonexistent")

    def test_lru_eviction(self):
        c = QueryCache(max_size_mb=0, strategy=CacheStrategy.LRU)
        c.max_size_bytes = 30
        c.set("k1", "a")
        c.get("k1")
        c.set("k2", "b")
        assert c.stats.evictions >= 1

    def test_lfu_eviction(self):
        c = QueryCache(max_size_mb=0, strategy=CacheStrategy.LFU)
        c.max_size_bytes = 30
        c.set("k1", "a")
        for _ in range(5):
            c.get("k1")
        c.set("k2", "b")
        assert c.stats.evictions >= 1

    def test_ttl_eviction(self):
        c = QueryCache(max_size_mb=1, strategy=CacheStrategy.TTL)
        c.set("k1", "a")
        c.set("k2", "b")
        assert c.stats.entry_count == 2

    def test_evict_empty_cache(self):
        c = QueryCache()
        c._evict_one()

    def test_get_stats(self):
        c = QueryCache(max_size_mb=50, default_ttl_seconds=300)
        c.set("k1", "v1")
        c.get("k1")
        c.get("miss")
        stats = c.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["entry_count"] == 1
        assert "hit_rate" in stats

    def test_calculate_size_fallback(self):
        c = QueryCache()
        obj = MagicMock()
        obj.__reduce__ = MagicMock(side_effect=Exception("unpicklable"))
        size = c._calculate_size(obj)
        assert size == 1024


class TestCachedQueryExecutor:
    def test_cache_miss_then_hit(self):
        cache = QueryCache()
        executor = CachedQueryExecutor(cache)
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
            return [1, 2, 3]

        r1 = executor.execute("q1", func)
        r2 = executor.execute("q1", func)
        assert r1 == [1, 2, 3]
        assert r2 == [1, 2, 3]
        assert call_count == 1

    def test_force_refresh(self):
        cache = QueryCache()
        executor = CachedQueryExecutor(cache)
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
            return call_count

        executor.execute("q1", func)
        r2 = executor.execute("q1", func, force_refresh=True)
        assert r2 == 2
        assert call_count == 2

    def test_custom_cache_key(self):
        cache = QueryCache()
        executor = CachedQueryExecutor(cache)
        executor.execute("q1", lambda: "a", cache_key="custom")
        assert cache.get("custom") == "a"

    def test_with_dependencies(self):
        cache = QueryCache()
        executor = CachedQueryExecutor(cache)
        executor.execute("q1", lambda: "a", dependencies=["res1"])
        cache.invalidate_by_dependency("res1")
        assert cache.get(executor._generate_cache_key("q1", (), {})) is None

    def test_generate_cache_key_with_args(self):
        executor = CachedQueryExecutor(QueryCache())
        k1 = executor._generate_cache_key("q", ("a",), {"b": 1})
        k2 = executor._generate_cache_key("q", ("a",), {"b": 1})
        k3 = executor._generate_cache_key("q", ("a",), {"b": 2})
        assert k1 == k2
        assert k1 != k3


class TestCacheWarmer:
    def test_warm_cache(self):
        cache = QueryCache()
        executor = CachedQueryExecutor(cache)
        warmer = CacheWarmer(cache, executor)
        warmer.register_query("q1", lambda: "result1", args=())
        warmer.warm_cache()
        assert cache.stats.entry_count == 1

    def test_warm_cache_error_handling(self):
        cache = QueryCache()
        executor = CachedQueryExecutor(cache)
        warmer = CacheWarmer(cache, executor)
        warmer.register_query("q_bad", lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        warmer.warm_cache()

    def test_register_with_kwargs(self):
        cache = QueryCache()
        executor = CachedQueryExecutor(cache)
        warmer = CacheWarmer(cache, executor)
        warmer.register_query("q1", lambda x=1: x, kwargs={"x": 42}, ttl_seconds=60)
        assert len(warmer.warm_queries) == 1
        assert warmer.warm_queries[0]["ttl_seconds"] == 60


class TestBenchmarkResult:
    def test_to_dict(self):
        r = BenchmarkResult(
            name="test", iterations=100, total_time_seconds=1.0,
            min_time_ms=5.0, max_time_ms=50.0, avg_time_ms=10.0,
            median_time_ms=9.0, p95_time_ms=20.0, p99_time_ms=40.0,
            std_dev_ms=3.0, throughput_qps=100.0,
            success_count=100, error_count=0,
        )
        d = r.to_dict()
        assert d["name"] == "test"
        assert d["success_rate"] == "100.00%"
        assert "timestamp" in d


class TestPerformanceBenchmark:
    def test_run_benchmark(self):
        b = PerformanceBenchmark()
        result = b.run_benchmark("test", lambda: None, iterations=10, warmup_iterations=2)
        assert result.success_count == 10
        assert result.error_count == 0
        assert result.avg_time_ms >= 0

    def test_run_benchmark_with_errors(self):
        b = PerformanceBenchmark()
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise RuntimeError("fail")

        result = b.run_benchmark("flaky", flaky, iterations=10, warmup_iterations=0)
        assert result.error_count > 0

    def test_run_benchmark_all_errors(self):
        b = PerformanceBenchmark()

        def always_fail():
            raise RuntimeError("always")

        result = b.run_benchmark("fail", always_fail, iterations=5, warmup_iterations=0)
        assert result.error_count == 5
        assert result.avg_time_ms == 0

    def test_compare_no_regression(self):
        b = PerformanceBenchmark()
        baseline = BenchmarkResult(
            name="t", iterations=100, total_time_seconds=1.0,
            min_time_ms=5, max_time_ms=15, avg_time_ms=10.0,
            median_time_ms=10.0, p95_time_ms=14.0, p99_time_ms=15.0,
            std_dev_ms=2.0, throughput_qps=100.0,
            success_count=100, error_count=0,
        )
        current = BenchmarkResult(
            name="t", iterations=100, total_time_seconds=1.0,
            min_time_ms=5, max_time_ms=15, avg_time_ms=10.5,
            median_time_ms=10.0, p95_time_ms=14.5, p99_time_ms=15.0,
            std_dev_ms=2.0, throughput_qps=98.0,
            success_count=100, error_count=0,
        )
        comp = b.compare_benchmarks(baseline, current)
        assert comp["is_regression"] is False

    def test_compare_regression_detected(self):
        b = PerformanceBenchmark()
        baseline = BenchmarkResult(
            name="t", iterations=100, total_time_seconds=1.0,
            min_time_ms=5, max_time_ms=15, avg_time_ms=10.0,
            median_time_ms=10.0, p95_time_ms=14.0, p99_time_ms=15.0,
            std_dev_ms=2.0, throughput_qps=100.0,
            success_count=100, error_count=0,
        )
        current = BenchmarkResult(
            name="t", iterations=100, total_time_seconds=1.0,
            min_time_ms=5, max_time_ms=50, avg_time_ms=25.0,
            median_time_ms=20.0, p95_time_ms=40.0, p99_time_ms=50.0,
            std_dev_ms=10.0, throughput_qps=40.0,
            success_count=100, error_count=0,
        )
        comp = b.compare_benchmarks(baseline, current)
        assert comp["is_regression"] is True

    def test_export_results(self):
        b = PerformanceBenchmark()
        b.run_benchmark("test", lambda: None, iterations=5, warmup_iterations=0)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            b.export_results(path)
            with open(path) as f:
                data = json.load(f)
            assert data["summary"]["total_benchmarks"] == 1
        finally:
            os.unlink(path)

    def test_export_empty(self):
        b = PerformanceBenchmark()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            b.export_results(path)
            with open(path) as f:
                data = json.load(f)
            assert data["summary"]["avg_throughput_qps"] == 0
        finally:
            os.unlink(path)


class TestLoadTester:
    def test_init(self):
        lt = LoadTester(max_workers=5)
        assert lt.max_workers == 5

    @pytest.mark.timeout(5)
    def test_run_load_test(self):
        lt = LoadTester(max_workers=2)
        result = lt.run_load_test("test", lambda: None, concurrent_users=1, duration_seconds=0.1)
        assert isinstance(result, LoadTestResult)
        assert result.total_requests > 0


class TestQueryBenchmarkSuite:
    def test_register_and_run(self):
        suite = QueryBenchmarkSuite()
        suite.register_query("fast", lambda: None)
        results = suite.run_all_benchmarks(iterations=3)
        assert len(results) == 1

    def test_generate_report_empty(self):
        suite = QueryBenchmarkSuite()
        report = suite.generate_report()
        assert "error" in report

    def test_generate_report_with_data(self):
        suite = QueryBenchmarkSuite()
        suite.register_query("q1", lambda: None)
        suite.run_all_benchmarks(iterations=3)
        report = suite.generate_report()
        assert report["summary"]["total_queries"] == 1
        assert "benchmarks" in report

    def test_run_load_tests_short(self):
        suite = QueryBenchmarkSuite()
        suite.register_query("q1", lambda: None)
        results = suite.run_load_tests(concurrent_users=[1], duration_seconds=0.1)
        assert len(results) == 1
