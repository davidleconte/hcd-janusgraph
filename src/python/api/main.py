"""
FastAPI Analytics Service
=========================

REST API for graph-based analytics including:
- UBO (Ultimate Beneficial Owner) discovery
- AML structuring detection
- Fraud pattern detection
- Graph visualization data

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from gremlin_python.driver import serializer
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import P, T

from src.python.config.settings import Settings, get_settings

# ---------------------------------------------------------------------------
# Structured Logging
# ---------------------------------------------------------------------------


def _configure_logging(settings: Settings) -> None:
    """Configure root logger; optionally emit JSON lines."""
    root = logging.getLogger()
    root.setLevel(settings.log_level)

    if root.handlers:
        root.handlers.clear()

    handler = logging.StreamHandler()

    if settings.log_json:
        from pythonjsonlogger import jsonlogger

        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )

    handler.setFormatter(formatter)
    root.addHandler(handler)


logger = logging.getLogger(__name__)


# ===========================================================================
# Pydantic Models
# ===========================================================================


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
    """Health check response"""
    status: str
    timestamp: str
    services: Dict[str, bool]


class LivenessResponse(BaseModel):
    """Liveness probe – confirms process is alive."""
    status: str = "ok"


class UBORequest(BaseModel):
    """Request for UBO discovery"""
    company_id: str = Field(..., description="Company ID to analyze")
    include_indirect: bool = Field(True, description="Include indirect ownership")
    max_depth: int = Field(10, description="Maximum ownership chain depth", ge=1, le=20)
    ownership_threshold: float = Field(
        25.0, description="Minimum ownership percentage", ge=0, le=100
    )


class UBOOwner(BaseModel):
    """Ultimate Beneficial Owner"""
    person_id: str
    name: str
    ownership_percentage: float
    ownership_type: str
    chain_length: int


class UBOResponse(BaseModel):
    """UBO discovery response"""
    target_entity_id: str
    target_entity_name: str
    ubos: List[UBOOwner]
    total_layers: int
    high_risk_indicators: List[str]
    risk_score: float
    query_time_ms: float


class StructuringAlertRequest(BaseModel):
    """Request for structuring detection"""
    account_id: Optional[str] = Field(None, description="Specific account to analyze")
    time_window_days: int = Field(7, description="Days to analyze", ge=1, le=90)
    threshold_amount: float = Field(10000.0, description="CTR threshold amount")
    min_transaction_count: int = Field(3, description="Minimum transactions to flag")
    offset: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(50, ge=1, le=500, description="Maximum items to return")


class StructuringAlert(BaseModel):
    """Structuring pattern alert"""
    account_id: str
    account_holder: str
    total_amount: float
    transaction_count: int
    time_window: str
    risk_score: float
    pattern_type: str


class StructuringResponse(BaseModel):
    """Structuring detection response"""
    alerts: List[StructuringAlert]
    total_alerts: int
    analysis_period: str
    query_time_ms: float


class NetworkNode(BaseModel):
    """Node in ownership network"""
    id: str
    label: str
    name: str
    type: str


class NetworkEdge(BaseModel):
    """Edge in ownership network"""
    source: str
    target: str
    label: str
    weight: Optional[float] = None


class NetworkResponse(BaseModel):
    """Ownership network for visualization"""
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    center_entity: str


class GraphStatsResponse(BaseModel):
    """Graph statistics"""
    vertex_count: int
    edge_count: int
    person_count: int
    company_count: int
    account_count: int
    transaction_count: int
    last_updated: str


# ===========================================================================
# Application Setup
# ===========================================================================

_connection: Optional[DriverRemoteConnection] = None
_traversal = None


def get_graph_connection(settings: Settings | None = None):
    """Get or create graph traversal connection with optional TLS."""
    global _connection, _traversal

    if _connection is None:
        if settings is None:
            settings = get_settings()
        try:
            _connection = DriverRemoteConnection(
                settings.janusgraph_ws_url,
                "g",
                message_serializer=serializer.GraphSONSerializersV3d0(),
            )
            _traversal = traversal().withRemote(_connection)
            ssl_status = "with TLS" if settings.janusgraph_use_ssl else "without TLS"
            logger.info(
                "Connected to JanusGraph at %s:%s (%s)",
                settings.janusgraph_host,
                settings.janusgraph_port,
                ssl_status,
            )
        except Exception as e:
            logger.error("Failed to connect to JanusGraph: %s", e)
            raise HTTPException(status_code=503, detail="Graph database unavailable")

    return _traversal


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

_security = HTTPBearer(auto_error=False)

PUBLIC_PATHS = {"/health", "/healthz", "/readyz", "/docs", "/redoc", "/openapi.json"}


async def verify_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> None:
    """Verify Bearer token on protected endpoints when AUTH_ENABLED=true."""
    settings = get_settings()
    if not settings.auth_enabled:
        return
    if request.url.path in PUBLIC_PATHS:
        return
    if credentials is None or credentials.credentials != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    _configure_logging(settings)

    from src.python.utils.tracing import TracingConfig, initialize_tracing
    tracing_config = TracingConfig(
        service_name="graph-analytics-api",
        enabled=settings.tracing_enabled,
    )
    tracing_mgr = initialize_tracing(tracing_config)

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        logger.debug("opentelemetry-instrumentation-fastapi not installed, skipping")

    logger.info("Starting Analytics API Service...")
    yield
    global _connection
    if _connection:
        _connection.close()
        logger.info("Closed JanusGraph connection")
    tracing_mgr.shutdown()


# ---------------------------------------------------------------------------
# Create FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Graph Analytics API",
    description="REST API for graph-based analytics including UBO discovery, AML detection, and fraud analysis",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    dependencies=[Depends(verify_auth)],
)

app.state.limiter = limiter

settings = get_settings()
_allow_credentials = settings.api_cors_origins != "*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================================================
# Global Error Handlers (#5)
# ===========================================================================


def _error_response(status_code: int, error: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=error,
            detail=detail,
            status_code=status_code,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ).model_dump(),
    )


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return _error_response(429, "rate_limit_exceeded", "Too many requests. Slow down.")


@app.exception_handler(HTTPException)
async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return _error_response(exc.status_code, "http_error", str(exc.detail))


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return _error_response(500, "internal_error", "An unexpected error occurred.")


# ===========================================================================
# Health / Probes (#4)
# ===========================================================================


@app.get("/healthz", response_model=LivenessResponse, tags=["Health"])
def liveness():
    """Liveness probe — returns 200 if the process is alive (no dependency check)."""
    return LivenessResponse()


@app.get("/readyz", response_model=HealthResponse, tags=["Health"])
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def readiness():
    """Readiness probe — checks backend connectivity."""
    services: Dict[str, bool] = {}

    try:
        g = get_graph_connection()
        g.V().limit(1).count().next()
        services["janusgraph"] = True
    except Exception as e:
        logger.error("JanusGraph health check failed: %s", e)
        services["janusgraph"] = False

    status = "healthy" if all(services.values()) else "degraded"
    return HealthResponse(
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services,
    )


@app.get("/stats", response_model=GraphStatsResponse, tags=["Health"])
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def graph_stats(request: Request):
    """Get graph statistics."""
    g = get_graph_connection()

    stats = {
        "vertex_count": g.V().count().next(),
        "edge_count": g.E().count().next(),
        "person_count": g.V().hasLabel("person").count().next(),
        "company_count": g.V().hasLabel("company").count().next(),
        "account_count": g.V().hasLabel("account").count().next(),
        "transaction_count": g.V().hasLabel("transaction").count().next(),
    }

    return GraphStatsResponse(
        **stats, last_updated=datetime.now(timezone.utc).isoformat()
    )


# ===========================================================================
# UBO Discovery Endpoints
# ===========================================================================


@app.post("/api/v1/ubo/discover", response_model=UBOResponse, tags=["UBO Discovery"])
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

    g = get_graph_connection()

    company = g.V().has("company_id", body.company_id).valueMap(True).toList()
    if not company:
        raise HTTPException(
            status_code=404, detail=f"Company not found: {body.company_id}"
        )

    company_info = _flatten_value_map(company[0])

    ubos: List[UBOOwner] = []
    high_risk_indicators: List[str] = []

    direct_owners = (
        g.V()
        .has("company_id", body.company_id)
        .inE("beneficial_owner")
        .project("person_id", "name", "ownership_percentage")
        .by(__.outV().values("person_id"))
        .by(__.outV().coalesce(__.values("full_name"), __.constant("Unknown")))
        .by(__.coalesce(__.values("ownership_percentage"), __.constant(0.0)))
        .toList()
    )

    for owner in direct_owners:
        if owner.get("ownership_percentage", 0) >= body.ownership_threshold:
            ubos.append(
                UBOOwner(
                    person_id=owner["person_id"],
                    name=owner["name"],
                    ownership_percentage=owner["ownership_percentage"],
                    ownership_type="direct",
                    chain_length=1,
                )
            )

    risk_score = 0.0
    if not ubos:
        risk_score += 20
        high_risk_indicators.append(
            "No beneficial owners identified above threshold"
        )

    query_time = (time.time() - start_time) * 1000

    return UBOResponse(
        target_entity_id=body.company_id,
        target_entity_name=company_info.get(
            "legal_name", company_info.get("company_name", "Unknown")
        ),
        ubos=ubos,
        total_layers=1 if ubos else 0,
        high_risk_indicators=high_risk_indicators,
        risk_score=min(risk_score, 100.0),
        query_time_ms=round(query_time, 2),
    )


@app.get(
    "/api/v1/ubo/network/{company_id}",
    response_model=NetworkResponse,
    tags=["UBO Discovery"],
)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def get_ownership_network(
    request: Request,
    company_id: str,
    depth: int = Query(3, ge=1, le=5, description="Traversal depth"),
):
    """Get ownership network around a company for visualization."""
    g = get_graph_connection()

    if not g.V().has("company_id", company_id).hasNext():
        raise HTTPException(
            status_code=404, detail=f"Company not found: {company_id}"
        )

    nodes: List[NetworkNode] = []
    edges: List[NetworkEdge] = []
    visited: set = set()

    company = g.V().has("company_id", company_id).valueMap(True).next()
    company_flat = _flatten_value_map(company)

    nodes.append(
        NetworkNode(
            id=company_id,
            label="company",
            name=company_flat.get(
                "legal_name", company_flat.get("company_name", "Unknown")
            ),
            type="company",
        )
    )
    visited.add(company_id)

    owners = (
        g.V()
        .has("company_id", company_id)
        .inE("beneficial_owner")
        .outV()
        .valueMap(True)
        .toList()
    )

    for owner in owners:
        owner_flat = _flatten_value_map(owner)
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
            edges.append(
                NetworkEdge(
                    source=person_id, target=company_id, label="beneficial_owner"
                )
            )

    return NetworkResponse(nodes=nodes, edges=edges, center_entity=company_id)


# ===========================================================================
# AML Structuring Detection Endpoints
# ===========================================================================


@app.post(
    "/api/v1/aml/structuring",
    response_model=StructuringResponse,
    tags=["AML Detection"],
)
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
                    (txn_count * 10)
                    + ((body.threshold_amount - avg_amount) / 100),
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

    total = len(alerts)
    page = alerts[body.offset : body.offset + body.limit]

    return StructuringResponse(
        alerts=page,
        total_alerts=total,
        analysis_period=f"{start_date.date()} to {end_date.date()}",
        query_time_ms=round(query_time, 2),
    )


# ===========================================================================
# Fraud Detection Endpoints
# ===========================================================================


@app.get("/api/v1/fraud/rings", tags=["Fraud Detection"])
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


# ===========================================================================
# Helper Functions
# ===========================================================================


def _flatten_value_map(value_map: Dict) -> Dict:
    """Flatten JanusGraph valueMap (lists to single values)."""
    flat: Dict = {}
    for key, value in value_map.items():
        if key == T.id:
            flat["id"] = value
        elif key == T.label:
            flat["label"] = value
        elif isinstance(value, list) and len(value) == 1:
            flat[key] = value[0]
        else:
            flat[key] = value
    return flat


# ===========================================================================
# Main Entry Point
# ===========================================================================

if __name__ == "__main__":
    import uvicorn

    _settings = get_settings()
    uvicorn.run(
        "main:app",
        host=_settings.api_host,
        port=_settings.api_port,
        reload=True,
        log_level=_settings.log_level.lower(),
    )
