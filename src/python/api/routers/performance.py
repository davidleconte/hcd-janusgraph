"""
Performance & Profiling Router
===============================

Exposes query profiling, cache stats, and benchmark endpoints.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from src.python.api.dependencies import get_settings, limiter, require_any_role
from src.python.performance.query_cache import CacheStrategy, QueryCache
from src.python.performance.query_profiler import QueryProfiler

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/performance",
    tags=["Performance"],
    dependencies=[Depends(require_any_role("admin", "developer"))],
)

_profiler: Optional[QueryProfiler] = None
_cache: Optional[QueryCache] = None


def get_profiler() -> QueryProfiler:
    global _profiler
    if _profiler is None:
        _profiler = QueryProfiler(slow_query_threshold_ms=1000.0)
    return _profiler


def get_cache() -> QueryCache:
    global _cache
    if _cache is None:
        _cache = QueryCache(max_size_mb=100, default_ttl_seconds=300, strategy=CacheStrategy.LRU)
    return _cache


class ProfileReportResponse(BaseModel):
    summary: Dict[str, Any]
    top_slow_queries: List[Dict[str, Any]]
    top_frequent_queries: List[Dict[str, Any]]
    optimization_recommendations: List[str]


class CacheStatsResponse(BaseModel):
    hits: int
    misses: int
    hit_rate: str
    miss_rate: str
    evictions: int
    invalidations: int
    entry_count: int
    total_size_mb: float
    max_size_mb: float


class CacheInvalidateRequest(BaseModel):
    resource: str = Field(..., description="Resource dependency key to invalidate")


class CacheInvalidateResponse(BaseModel):
    success: bool
    message: str


class ProfilerConfigRequest(BaseModel):
    slow_query_threshold_ms: Optional[float] = None
    expensive_query_threshold_scans: Optional[int] = None


class ProfilerConfigResponse(BaseModel):
    slow_query_threshold_ms: float
    expensive_query_threshold_scans: int
    total_profiled_queries: int
    unique_patterns: int


@router.get("/profiler/report", response_model=ProfileReportResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def get_profiler_report(request: Request):
    """Get comprehensive query profiling report."""
    profiler = get_profiler()
    report = profiler.generate_report()
    return ProfileReportResponse(**report)


@router.get("/profiler/slow-queries")
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def get_slow_queries(request: Request, limit: int = 10):
    """Get slowest query patterns by average execution time."""
    profiler = get_profiler()
    queries = profiler.get_slow_queries(limit=limit)
    return [
        {
            "query_pattern": q.query_pattern,
            "avg_time_ms": q.avg_time_ms,
            "p95_time_ms": q.p95_time_ms,
            "execution_count": q.execution_count,
            "slow_query_count": q.slow_query_count,
        }
        for q in queries
    ]


@router.get("/profiler/frequent-queries")
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def get_frequent_queries(request: Request, limit: int = 10):
    """Get most frequently executed query patterns."""
    profiler = get_profiler()
    queries = profiler.get_frequent_queries(limit=limit)
    return [
        {
            "query_pattern": q.query_pattern,
            "execution_count": q.execution_count,
            "avg_time_ms": q.avg_time_ms,
        }
        for q in queries
    ]


@router.get("/profiler/config", response_model=ProfilerConfigResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def get_profiler_config(request: Request):
    """Get current profiler configuration."""
    profiler = get_profiler()
    return ProfilerConfigResponse(
        slow_query_threshold_ms=profiler.slow_query_threshold_ms,
        expensive_query_threshold_scans=profiler.expensive_query_threshold_scans,
        total_profiled_queries=len(profiler.query_metrics),
        unique_patterns=len(profiler.query_statistics),
    )


@router.put("/profiler/config", response_model=ProfilerConfigResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def update_profiler_config(request: Request, body: ProfilerConfigRequest):
    """Update profiler thresholds at runtime."""
    profiler = get_profiler()
    if body.slow_query_threshold_ms is not None:
        profiler.slow_query_threshold_ms = body.slow_query_threshold_ms
    if body.expensive_query_threshold_scans is not None:
        profiler.expensive_query_threshold_scans = body.expensive_query_threshold_scans
    return ProfilerConfigResponse(
        slow_query_threshold_ms=profiler.slow_query_threshold_ms,
        expensive_query_threshold_scans=profiler.expensive_query_threshold_scans,
        total_profiled_queries=len(profiler.query_metrics),
        unique_patterns=len(profiler.query_statistics),
    )


@router.get("/cache/stats", response_model=CacheStatsResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def get_cache_stats(request: Request):
    """Get query cache statistics."""
    cache = get_cache()
    stats = cache.get_stats()
    return CacheStatsResponse(**stats)


@router.post("/cache/invalidate", response_model=CacheInvalidateResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def invalidate_cache(request: Request, body: CacheInvalidateRequest):
    """Invalidate cache entries by resource dependency."""
    cache = get_cache()
    cache.invalidate_by_dependency(body.resource)
    return CacheInvalidateResponse(
        success=True, message=f"Invalidated entries for resource: {body.resource}"
    )


@router.post("/cache/clear", response_model=CacheInvalidateResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def clear_cache(request: Request):
    """Clear all cache entries."""
    cache = get_cache()
    cache.clear()
    return CacheInvalidateResponse(success=True, message="Cache cleared")
