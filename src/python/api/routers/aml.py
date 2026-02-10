"""
AML Structuring Detection Router
=================================
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Request

from gremlin_python.process.graph_traversal import __

from src.python.api.dependencies import get_graph_connection, get_settings, limiter
from src.python.api.models import StructuringAlert, StructuringAlertRequest, StructuringResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/aml", tags=["AML Detection"])


@router.post("/structuring", response_model=StructuringResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def detect_structuring(request: Request, body: StructuringAlertRequest):
    """
    Detect potential structuring (smurfing) patterns.

    Identifies accounts with multiple transactions just below reporting thresholds
    that may indicate attempts to evade Currency Transaction Reports (CTRs).
    """
    start_time = time.time()

    g = get_graph_connection()

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=body.time_window_days)

    alerts: List[StructuringAlert] = []

    threshold_low = body.threshold_amount * 0.8

    query_result = (
        g.V()
        .hasLabel("account")
        .project("account_id", "holder", "txn_count", "total")
        .by(__.values("account_id"))
        .by(
            __.in_("owns_account").coalesce(
                __.values("full_name"),
                __.values("company_name"),
                __.constant("Unknown"),
            )
        )
        .by(__.outE("from_account").count())
        .by(__.outE("from_account").inV().values("amount").sum())
        .toList()
    )

    for result in query_result:
        txn_count = result.get("txn_count", 0)
        total = result.get("total", 0) or 0

        if txn_count >= body.min_transaction_count:
            avg_amount = total / txn_count if txn_count > 0 else 0
            if threshold_low <= avg_amount < body.threshold_amount:
                risk_score = min(
                    100,
                    (txn_count * 10) + ((body.threshold_amount - avg_amount) / 100),
                )
                alerts.append(
                    StructuringAlert(
                        account_id=result["account_id"],
                        account_holder=result["holder"],
                        total_amount=float(total),
                        transaction_count=txn_count,
                        time_window=f"{body.time_window_days} days",
                        risk_score=round(risk_score, 2),
                        pattern_type="potential_structuring",
                    )
                )

    query_time = (time.time() - start_time) * 1000

    total_alerts = len(alerts)
    page = alerts[body.offset : body.offset + body.limit]

    return StructuringResponse(
        alerts=page,
        total_alerts=total_alerts,
        analysis_period=f"{start_date.date()} to {end_date.date()}",
        query_time_ms=round(query_time, 2),
    )
