"""
Unit tests for Performance Router endpoints.

Tests profiler report, slow queries, cache stats, and configuration endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.python.api.routers.performance import (
    CacheInvalidateRequest,
    CacheStatsResponse,
    ProfilerConfigRequest,
    ProfilerConfigResponse,
    ProfileReportResponse,
    get_cache,
    get_profiler,
    router,
)


@pytest.fixture(autouse=True)
def reset_singletons():
    import src.python.api.routers.performance as perf_mod

    perf_mod._profiler = None
    perf_mod._cache = None
    yield
    perf_mod._profiler = None
    perf_mod._cache = None


@pytest.fixture
def client():
    from fastapi import FastAPI

    app = FastAPI()
    app.state.limiter = MagicMock()
    app.include_router(router)

    with patch("src.python.api.routers.performance.limiter") as mock_limiter:
        mock_limiter.limit.return_value = lambda f: f
        with TestClient(app) as c:
            yield c


class TestGetProfilerSingleton:
    def test_creates_profiler_on_first_call(self):
        profiler = get_profiler()
        assert profiler is not None
        assert profiler.slow_query_threshold_ms == 1000.0

    def test_returns_same_instance(self):
        p1 = get_profiler()
        p2 = get_profiler()
        assert p1 is p2


class TestGetCacheSingleton:
    def test_creates_cache_on_first_call(self):
        cache = get_cache()
        assert cache is not None

    def test_returns_same_instance(self):
        c1 = get_cache()
        c2 = get_cache()
        assert c1 is c2


class TestProfilerReportEndpoint:
    def test_get_profiler_report(self, client):
        resp = client.get("/api/v1/performance/profiler/report")
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "top_slow_queries" in data
        assert "optimization_recommendations" in data

    def test_get_slow_queries(self, client):
        resp = client.get("/api/v1/performance/profiler/slow-queries?limit=5")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_frequent_queries(self, client):
        resp = client.get("/api/v1/performance/profiler/frequent-queries?limit=5")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestProfilerConfigEndpoint:
    def test_get_config(self, client):
        resp = client.get("/api/v1/performance/profiler/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slow_query_threshold_ms"] == 1000.0

    def test_update_config(self, client):
        resp = client.put(
            "/api/v1/performance/profiler/config",
            json={"slow_query_threshold_ms": 500.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["slow_query_threshold_ms"] == 500.0

    def test_update_config_partial(self, client):
        resp = client.put(
            "/api/v1/performance/profiler/config",
            json={"expensive_query_threshold_scans": 5000},
        )
        assert resp.status_code == 200
        assert resp.json()["expensive_query_threshold_scans"] == 5000


class TestCacheEndpoints:
    def test_get_cache_stats(self, client):
        resp = client.get("/api/v1/performance/cache/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "hits" in data
        assert "misses" in data
        assert "hit_rate" in data

    def test_invalidate_cache(self, client):
        resp = client.post(
            "/api/v1/performance/cache/invalidate",
            json={"resource": "test-resource"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_clear_cache(self, client):
        resp = client.post("/api/v1/performance/cache/clear")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert "cleared" in resp.json()["message"].lower()


class TestResponseModels:
    def test_profile_report_response_model(self):
        model = ProfileReportResponse(
            summary={"total": 0},
            top_slow_queries=[],
            top_frequent_queries=[],
            optimization_recommendations=[],
        )
        assert model.summary == {"total": 0}

    def test_cache_stats_response_model(self):
        model = CacheStatsResponse(
            hits=10,
            misses=5,
            hit_rate="66.67%",
            miss_rate="33.33%",
            evictions=0,
            invalidations=0,
            entry_count=10,
            total_size_mb=1.0,
            max_size_mb=100.0,
        )
        assert model.hits == 10

    def test_profiler_config_request_defaults(self):
        model = ProfilerConfigRequest()
        assert model.slow_query_threshold_ms is None
        assert model.expensive_query_threshold_scans is None

    def test_cache_invalidate_request(self):
        model = CacheInvalidateRequest(resource="vertices")
        assert model.resource == "vertices"

    def test_profiler_config_response(self):
        model = ProfilerConfigResponse(
            slow_query_threshold_ms=1000.0,
            expensive_query_threshold_scans=10000,
            total_profiled_queries=0,
            unique_patterns=0,
        )
        assert model.slow_query_threshold_ms == 1000.0
