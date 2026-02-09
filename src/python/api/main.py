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
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver import serializer
from gremlin_python.process.anonymous_traversal import traversal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
JANUSGRAPH_HOST = os.getenv('JANUSGRAPH_HOST', 'localhost')
JANUSGRAPH_PORT = int(os.getenv('JANUSGRAPH_PORT', '18182'))


# ===========================================================================
# Pydantic Models
# ===========================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    services: Dict[str, bool]


class UBORequest(BaseModel):
    """Request for UBO discovery"""
    company_id: str = Field(..., description="Company ID to analyze")
    include_indirect: bool = Field(True, description="Include indirect ownership")
    max_depth: int = Field(10, description="Maximum ownership chain depth", ge=1, le=20)
    ownership_threshold: float = Field(25.0, description="Minimum ownership percentage", ge=0, le=100)


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

# Global connection pool
_connection = None
_traversal = None


# JanusGraph SSL configuration
JANUSGRAPH_USE_SSL = os.getenv('JANUSGRAPH_USE_SSL', 'false').lower() == 'true'
JANUSGRAPH_CA_CERTS = os.getenv('JANUSGRAPH_CA_CERTS', None)


def get_graph_connection():
    """Get or create graph traversal connection with optional TLS"""
    global _connection, _traversal
    
    if _connection is None:
        try:
            protocol = 'wss' if JANUSGRAPH_USE_SSL else 'ws'
            url = f'{protocol}://{JANUSGRAPH_HOST}:{JANUSGRAPH_PORT}/gremlin'
            
            _connection = DriverRemoteConnection(
                url,
                'g',
                message_serializer=serializer.GraphSONSerializersV3d0()
            )
            _traversal = traversal().withRemote(_connection)
            ssl_status = "with TLS" if JANUSGRAPH_USE_SSL else "without TLS"
            logger.info("Connected to JanusGraph at %s:%s (%s)", JANUSGRAPH_HOST, JANUSGRAPH_PORT, ssl_status)
        except Exception as e:
            logger.error("Failed to connect to JanusGraph: %s", e)
            raise HTTPException(status_code=503, detail="Graph database unavailable")
    
    return _traversal


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Analytics API Service...")
    yield
    # Cleanup
    global _connection
    if _connection:
        _connection.close()
        logger.info("Closed JanusGraph connection")


# Create FastAPI app
app = FastAPI(
    title="Graph Analytics API",
    description="REST API for graph-based analytics including UBO discovery, AML detection, and fraud analysis",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - use env-driven allowlist for security
_cors_origins = os.getenv("API_CORS_ORIGINS", "*")
_cors_origins_list = ["*"] if _cors_origins == "*" else [o.strip() for o in _cors_origins.split(",")]
_allow_credentials = _cors_origins != "*"  # Only allow credentials with explicit origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_list,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================================================
# Health Check Endpoints
# ===========================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Check service health and connectivity to backend services.
    Note: Using sync endpoint to avoid event loop conflicts with gremlin-python.
    """
    services = {}
    
    # Check JanusGraph
    try:
        g = get_graph_connection()
        count = g.V().limit(1).count().next()
        services['janusgraph'] = True
    except Exception as e:
        logger.error("JanusGraph health check failed: %s", e)
        services['janusgraph'] = False
    
    status = "healthy" if all(services.values()) else "degraded"
    
    return HealthResponse(
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services
    )


@app.get("/stats", response_model=GraphStatsResponse, tags=["Health"])
def graph_stats():
    """
    Get graph statistics.
    Note: Using sync endpoint to avoid event loop conflicts with gremlin-python.
    """
    try:
        g = get_graph_connection()
        
        stats = {
            'vertex_count': g.V().count().next(),
            'edge_count': g.E().count().next(),
            'person_count': g.V().hasLabel('person').count().next(),
            'company_count': g.V().hasLabel('company').count().next(),
            'account_count': g.V().hasLabel('account').count().next(),
            'transaction_count': g.V().hasLabel('transaction').count().next(),
        }
        
        return GraphStatsResponse(
            **stats,
            last_updated=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error("Error getting graph stats: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================================================
# UBO Discovery Endpoints
# ===========================================================================

@app.post("/api/v1/ubo/discover", response_model=UBOResponse, tags=["UBO Discovery"])
def discover_ubo(request: UBORequest):
    """
    Discover Ultimate Beneficial Owners for a company.
    
    Traverses ownership chains through direct ownership and holding companies
    to identify individuals with significant control (default: 25%+ ownership).
    
    Regulatory references:
    - EU 5AMLD: 25% ownership threshold
    - FATF Recommendations
    - FinCEN CDD Rule
    """
    import time
    start_time = time.time()
    
    try:
        g = get_graph_connection()
        
        # Check if company exists
        company = g.V().has('company_id', request.company_id).valueMap(True).toList()
        if not company:
            raise HTTPException(status_code=404, detail=f"Company not found: {request.company_id}")
        
        company_info = _flatten_value_map(company[0])
        
        # Find direct beneficial owners
        ubos = []
        high_risk_indicators = []
        
        direct_owners = g.V().has('company_id', request.company_id) \
            .inE('beneficial_owner') \
            .project('person_id', 'name', 'ownership_percentage') \
            .by(__.outV().values('person_id')) \
            .by(__.outV().coalesce(__.values('full_name'), __.constant('Unknown'))) \
            .by(__.coalesce(__.values('ownership_percentage'), __.constant(0.0))) \
            .toList()
        
        for owner in direct_owners:
            if owner.get('ownership_percentage', 0) >= request.ownership_threshold:
                ubos.append(UBOOwner(
                    person_id=owner['person_id'],
                    name=owner['name'],
                    ownership_percentage=owner['ownership_percentage'],
                    ownership_type='direct',
                    chain_length=1
                ))
        
        # Calculate risk score
        risk_score = 0.0
        if not ubos:
            risk_score += 20  # No identified UBOs
            high_risk_indicators.append("No beneficial owners identified above threshold")
        
        query_time = (time.time() - start_time) * 1000
        
        return UBOResponse(
            target_entity_id=request.company_id,
            target_entity_name=company_info.get('legal_name', company_info.get('company_name', 'Unknown')),
            ubos=ubos,
            total_layers=1 if ubos else 0,
            high_risk_indicators=high_risk_indicators,
            risk_score=min(risk_score, 100.0),
            query_time_ms=round(query_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("UBO discovery error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/ubo/network/{company_id}", response_model=NetworkResponse, tags=["UBO Discovery"])
def get_ownership_network(
    company_id: str,
    depth: int = Query(3, ge=1, le=5, description="Traversal depth")
):
    """
    Get ownership network around a company for visualization.
    
    Returns nodes and edges suitable for rendering in a graph visualization tool.
    """
    try:
        g = get_graph_connection()
        
        # Check if company exists
        if not g.V().has('company_id', company_id).hasNext():
            raise HTTPException(status_code=404, detail=f"Company not found: {company_id}")
        
        nodes = []
        edges = []
        visited = set()
        
        # Get company and its owners
        company = g.V().has('company_id', company_id).valueMap(True).next()
        company_flat = _flatten_value_map(company)
        
        nodes.append(NetworkNode(
            id=company_id,
            label='company',
            name=company_flat.get('legal_name', company_flat.get('company_name', 'Unknown')),
            type='company'
        ))
        visited.add(company_id)
        
        # Get beneficial owners
        owners = g.V().has('company_id', company_id) \
            .inE('beneficial_owner').outV() \
            .valueMap(True).toList()
        
        for owner in owners:
            owner_flat = _flatten_value_map(owner)
            person_id = owner_flat.get('person_id')
            if person_id and person_id not in visited:
                visited.add(person_id)
                nodes.append(NetworkNode(
                    id=person_id,
                    label='person',
                    name=owner_flat.get('full_name', f"{owner_flat.get('first_name', '')} {owner_flat.get('last_name', '')}"),
                    type='person'
                ))
                edges.append(NetworkEdge(
                    source=person_id,
                    target=company_id,
                    label='beneficial_owner'
                ))
        
        return NetworkResponse(
            nodes=nodes,
            edges=edges,
            center_entity=company_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Network query error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================================================
# AML Structuring Detection Endpoints
# ===========================================================================

@app.post("/api/v1/aml/structuring", response_model=StructuringResponse, tags=["AML Detection"])
def detect_structuring(request: StructuringAlertRequest):
    """
    Detect potential structuring (smurfing) patterns.
    
    Identifies accounts with multiple transactions just below reporting thresholds
    that may indicate attempts to evade Currency Transaction Reports (CTRs).
    
    Pattern indicators:
    - Multiple deposits just under $10,000 threshold
    - Transactions within short time windows
    - Round number amounts
    """
    import time
    start_time = time.time()
    
    try:
        g = get_graph_connection()
        
        # Time window calculation
        from datetime import timedelta
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=request.time_window_days)
        
        alerts = []
        
        # Query for structuring patterns
        # Find accounts with multiple transactions just below threshold
        threshold_low = request.threshold_amount * 0.8  # 80% of threshold
        
        query_result = g.V().hasLabel('account') \
            .project('account_id', 'holder', 'txn_count', 'total') \
            .by(__.values('account_id')) \
            .by(__.in_('owns_account').coalesce(
                __.values('full_name'),
                __.values('company_name'),
                __.constant('Unknown')
            )) \
            .by(__.outE('from_account').count()) \
            .by(__.outE('from_account').inV().values('amount').sum()) \
            .toList()
        
        for result in query_result:
            txn_count = result.get('txn_count', 0)
            total = result.get('total', 0) or 0
            
            # Flag if multiple transactions averaging near threshold
            if txn_count >= request.min_transaction_count:
                avg_amount = total / txn_count if txn_count > 0 else 0
                if threshold_low <= avg_amount < request.threshold_amount:
                    risk_score = min(100, (txn_count * 10) + ((request.threshold_amount - avg_amount) / 100))
                    
                    alerts.append(StructuringAlert(
                        account_id=result['account_id'],
                        account_holder=result['holder'],
                        total_amount=float(total),
                        transaction_count=txn_count,
                        time_window=f"{request.time_window_days} days",
                        risk_score=round(risk_score, 2),
                        pattern_type="potential_structuring"
                    ))
        
        query_time = (time.time() - start_time) * 1000
        
        return StructuringResponse(
            alerts=alerts[:100],  # Limit results
            total_alerts=len(alerts),
            analysis_period=f"{start_date.date()} to {end_date.date()}",
            query_time_ms=round(query_time, 2)
        )
        
    except Exception as e:
        logger.error("Structuring detection error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================================================
# Fraud Detection Endpoints
# ===========================================================================

@app.get("/api/v1/fraud/rings", tags=["Fraud Detection"])
def detect_fraud_rings(
    min_members: int = Query(3, ge=2, le=10, description="Minimum ring members"),
    include_accounts: bool = Query(True, description="Include account details")
):
    """
    Detect potential fraud rings based on shared addresses/phones and transaction patterns.
    
    A fraud ring typically consists of multiple entities that:
    - Share physical addresses
    - Share phone numbers
    - Have circular transaction patterns
    """
    try:
        g = get_graph_connection()
        
        rings = []
        
        # Find persons sharing addresses
        shared_addresses = g.V().hasLabel('address') \
            .where(__.in_('has_address').count().is_(P.gte(min_members))) \
            .project('address_id', 'city', 'persons') \
            .by(__.values('address_id')) \
            .by(__.values('city')) \
            .by(__.in_('has_address').values('person_id').fold()) \
            .toList()
        
        for addr in shared_addresses:
            rings.append({
                'type': 'shared_address',
                'indicator': addr.get('address_id'),
                'location': addr.get('city'),
                'members': addr.get('persons', []),
                'member_count': len(addr.get('persons', []))
            })
        
        return {
            'rings': rings[:50],
            'total_detected': len(rings)
        }
        
    except Exception as e:
        logger.error("Fraud ring detection error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================================================
# Helper Functions
# ===========================================================================

def _flatten_value_map(value_map: Dict) -> Dict:
    """Flatten JanusGraph valueMap (lists to single values)"""
    from gremlin_python.process.traversal import T
    
    flat = {}
    for key, value in value_map.items():
        if key == T.id:
            flat['id'] = value
        elif key == T.label:
            flat['label'] = value
        elif isinstance(value, list) and len(value) == 1:
            flat[key] = value[0]
        else:
            flat[key] = value
    return flat


# Import __ for Gremlin traversals
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import P


# ===========================================================================
# Main Entry Point
# ===========================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv('API_PORT', '8001'))
    host = os.getenv('API_HOST', '0.0.0.0')
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
