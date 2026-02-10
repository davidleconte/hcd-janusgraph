"""
API Pydantic Models
===================

Request/response schemas for the Graph Analytics API.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all error handlers."""

    error: str
    detail: str
    status_code: int
    timestamp: str


class PaginationParams(BaseModel):
    """Reusable pagination parameters."""

    offset: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(50, ge=1, le=500, description="Maximum items to return")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str
    services: Dict[str, bool]


class LivenessResponse(BaseModel):
    """Liveness probe – confirms process is alive."""

    status: str = "ok"


class UBORequest(BaseModel):
    """Request for UBO discovery."""

    company_id: str = Field(..., description="Company ID to analyze")
    include_indirect: bool = Field(True, description="Include indirect ownership")
    max_depth: int = Field(10, description="Maximum ownership chain depth", ge=1, le=20)
    ownership_threshold: float = Field(
        25.0, description="Minimum ownership percentage", ge=0, le=100
    )


class UBOOwner(BaseModel):
    """Ultimate Beneficial Owner."""

    person_id: str
    name: str
    ownership_percentage: float
    ownership_type: str
    chain_length: int


class UBOResponse(BaseModel):
    """UBO discovery response."""

    target_entity_id: str
    target_entity_name: str
    ubos: List[UBOOwner]
    total_layers: int
    high_risk_indicators: List[str]
    risk_score: float
    query_time_ms: float


class StructuringAlertRequest(BaseModel):
    """Request for structuring detection."""

    account_id: Optional[str] = Field(None, description="Specific account to analyze")
    time_window_days: int = Field(7, description="Days to analyze", ge=1, le=90)
    threshold_amount: float = Field(10000.0, description="CTR threshold amount")
    min_transaction_count: int = Field(3, description="Minimum transactions to flag")
    offset: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(50, ge=1, le=500, description="Maximum items to return")


class StructuringAlert(BaseModel):
    """Structuring pattern alert."""

    account_id: str
    account_holder: str
    total_amount: float
    transaction_count: int
    time_window: str
    risk_score: float
    pattern_type: str


class StructuringResponse(BaseModel):
    """Structuring detection response."""

    alerts: List[StructuringAlert]
    total_alerts: int
    analysis_period: str
    query_time_ms: float


class NetworkNode(BaseModel):
    """Node in ownership network."""

    id: str
    label: str
    name: str
    type: str


class NetworkEdge(BaseModel):
    """Edge in ownership network."""

    source: str
    target: str
    label: str
    weight: Optional[float] = None


class NetworkResponse(BaseModel):
    """Ownership network for visualization."""

    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    center_entity: str


class GraphStatsResponse(BaseModel):
    """Graph statistics."""

    vertex_count: int
    edge_count: int
    person_count: int
    company_count: int
    account_count: int
    transaction_count: int
    last_updated: str
