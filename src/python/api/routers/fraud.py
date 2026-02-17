"""
Fraud Detection Router
======================
"""

import logging

from fastapi import APIRouter, Query, Request

from src.python.api.dependencies import get_graph_connection, get_settings, limiter
from src.python.repository import GraphRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/fraud", tags=["Fraud Detection"])


@router.get("/rings")
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def detect_fraud_rings(
    request: Request,
    min_members: int = Query(3, ge=2, le=10, description="Minimum ring members"),
    include_accounts: bool = Query(True, description="Include account details"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Maximum items to return"),
):
    """
    Detect potential fraud rings based on shared addresses/phones and transaction patterns.
    """
    repo = GraphRepository(get_graph_connection())
    rings = repo.find_shared_addresses_with_accounts(
        min_members=min_members,
        include_accounts=include_accounts,
    )

    total = len(rings)
    page = rings[offset : offset + limit]

    return {"rings": page, "total_detected": total, "offset": offset, "limit": limit}
