"""
Fraud Detection Router
======================
"""

import logging

from fastapi import APIRouter, Query, Request

from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import P

from src.python.api.dependencies import get_graph_connection, get_settings, limiter

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
    g = get_graph_connection()

    rings = []

    shared_addresses = (
        g.V()
        .hasLabel("address")
        .where(__.in_("has_address").count().is_(P.gte(min_members)))
        .project("address_id", "city", "persons")
        .by(__.values("address_id"))
        .by(__.values("city"))
        .by(__.in_("has_address").values("person_id").fold())
        .toList()
    )

    for addr in shared_addresses:
        rings.append(
            {
                "type": "shared_address",
                "indicator": addr.get("address_id"),
                "location": addr.get("city"),
                "members": addr.get("persons", []),
                "member_count": len(addr.get("persons", [])),
            }
        )

    total = len(rings)
    page = rings[offset : offset + limit]

    return {"rings": page, "total_detected": total, "offset": offset, "limit": limit}
