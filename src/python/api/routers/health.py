"""
Health & Readiness Probes
=========================
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from src.python.api.dependencies import get_graph_connection, get_settings, limiter
from src.python.api.models import GraphStatsResponse, HealthResponse, LivenessResponse
from src.python.repository import GraphRepository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/healthz", response_model=LivenessResponse)
def liveness():
    """Liveness probe — returns 200 if the process is alive (no dependency check)."""
    return LivenessResponse()


@router.get("/readyz", response_model=HealthResponse)
@router.get("/health", response_model=HealthResponse)
def readiness():
    """Readiness probe — checks backend connectivity."""
    services = {}
    try:
        repo = GraphRepository(get_graph_connection())
        services["janusgraph"] = repo.health_check()
    except Exception as e:
        logger.error("JanusGraph health check failed: %s", e)
        services["janusgraph"] = False

    status = "healthy" if all(services.values()) else "degraded"
    return HealthResponse(
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services,
    )


@router.get("/stats", response_model=GraphStatsResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def graph_stats(request: Request):
    """Get graph statistics."""
    repo = GraphRepository(get_graph_connection())
    stats = repo.graph_stats()
    return GraphStatsResponse(**stats, last_updated=datetime.now(timezone.utc).isoformat())
