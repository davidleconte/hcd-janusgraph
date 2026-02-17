"""
UBO (Ultimate Beneficial Owner) Discovery Router
=================================================
"""

import logging
import time
from typing import List

from fastapi import APIRouter, HTTPException, Query, Request

from src.python.api.dependencies import get_graph_connection, get_settings, limiter
from src.python.api.models import (
    NetworkEdge,
    NetworkNode,
    NetworkResponse,
    UBOOwner,
    UBORequest,
    UBOResponse,
)
from src.python.repository import GraphRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ubo", tags=["UBO Discovery"])


@router.post("/discover", response_model=UBOResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def discover_ubo(request: Request, body: UBORequest):
    """
    Discover Ultimate Beneficial Owners for a company.

    Traverses ownership chains through direct ownership and holding companies
    to identify individuals with significant control (default: 25%+ ownership).

    Regulatory references:
    - EU 5AMLD: 25% ownership threshold
    - FATF Recommendations
    - FinCEN CDD Rule
    """
    start_time = time.time()

    repo = GraphRepository(get_graph_connection())

    company_info = repo.get_company(body.company_id)
    if not company_info:
        raise HTTPException(status_code=404, detail=f"Company not found: {body.company_id}")

    ubos: List[UBOOwner] = []
    high_risk_indicators: List[str] = []

    ubos_payload, total_layers = repo.find_ubo_owners(
        body.company_id,
        ownership_threshold=body.ownership_threshold,
        include_indirect=body.include_indirect,
        max_depth=body.max_depth,
    )

    for owner in ubos_payload:
        ubos.append(
            UBOOwner(
                person_id=owner["person_id"],
                name=owner["name"],
                ownership_percentage=owner["ownership_percentage"],
                ownership_type=owner.get("ownership_type", "direct"),
                chain_length=owner.get("chain_length", 1),
            )
        )

    risk_score = 0.0
    if not ubos:
        risk_score += 20
        high_risk_indicators.append("No beneficial owners identified above threshold")

    query_time = (time.time() - start_time) * 1000

    return UBOResponse(
        target_entity_id=body.company_id,
        target_entity_name=company_info.get(
            "legal_name", company_info.get("company_name", "Unknown")
        ),
        ubos=ubos,
        total_layers=total_layers,
        high_risk_indicators=high_risk_indicators,
        risk_score=min(risk_score, 100.0),
        query_time_ms=round(query_time, 2),
    )


@router.get("/network/{company_id}", response_model=NetworkResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def get_ownership_network(
    request: Request,
    company_id: str,
    depth: int = Query(3, ge=1, le=5, description="Traversal depth"),
):
    """Get ownership network around a company for visualization."""
    repo = GraphRepository(get_graph_connection())

    company_info = repo.get_company(company_id)
    if not company_info:
        raise HTTPException(status_code=404, detail=f"Company not found: {company_id}")

    nodes: List[NetworkNode] = []
    edges: List[NetworkEdge] = []
    visited: set = set()

    nodes.append(
        NetworkNode(
            id=company_id,
            label="company",
            name=company_info.get("legal_name", company_info.get("company_name", "Unknown")),
            type="company",
        )
    )
    visited.add(company_id)

    owners = repo.get_owner_vertices(company_id)

    for owner_flat in owners:
        person_id = owner_flat.get("person_id")
        if person_id and person_id not in visited:
            visited.add(person_id)
            nodes.append(
                NetworkNode(
                    id=person_id,
                    label="person",
                    name=owner_flat.get(
                        "full_name",
                        f"{owner_flat.get('first_name', '')} {owner_flat.get('last_name', '')}",
                    ),
                    type="person",
                )
            )
            edges.append(NetworkEdge(source=person_id, target=company_id, label="beneficial_owner"))

    return NetworkResponse(nodes=nodes, edges=edges, center_entity=company_id)
