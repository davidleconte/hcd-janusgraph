"""
API Pydantic Models
===================

Request/response schemas for the Graph Analytics API.
Enhanced with comprehensive validation for security.
"""

from typing import Annotated, Dict, List, Optional

from pydantic import BaseModel, Field, StringConstraints, field_validator

from src.python.utils.validation import ValidationError, Validator


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
    """Request for UBO discovery with validation."""

    company_id: Annotated[
        str, StringConstraints(min_length=5, max_length=50, pattern=r"^[A-Z0-9\-_]+$")
    ] = Field(..., description="Company ID to analyze (alphanumeric, hyphens, underscores only)")
    include_indirect: bool = Field(True, description="Include indirect ownership")
    max_depth: int = Field(10, description="Maximum ownership chain depth", ge=1, le=20)
    ownership_threshold: float = Field(
        25.0, description="Minimum ownership percentage", ge=0, le=100
    )

    @field_validator("company_id")
    @classmethod
    def validate_company_id(cls, v: str) -> str:
        """Validate company ID format and sanitize."""
        try:
            # Use existing Validator class for comprehensive validation
            return Validator.validate_account_id(v)
        except ValidationError as e:
            raise ValueError(f"Invalid company_id: {e}")


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
    """Request for structuring detection with validation."""

    account_id: Optional[
        Annotated[str, StringConstraints(min_length=5, max_length=50, pattern=r"^[A-Z0-9\-_]+$")]
    ] = Field(
        None, description="Specific account to analyze (alphanumeric, hyphens, underscores only)"
    )
    time_window_days: int = Field(7, description="Days to analyze", ge=1, le=90)
    threshold_amount: float = Field(
        10000.0, description="CTR threshold amount", ge=0.01, le=1_000_000_000.00
    )
    min_transaction_count: int = Field(3, description="Minimum transactions to flag", ge=1, le=1000)
    offset: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(50, ge=1, le=500, description="Maximum items to return")

    @field_validator("account_id")
    @classmethod
    def validate_account_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate account ID if provided."""
        if v is None:
            return v
        try:
            return Validator.validate_account_id(v)
        except ValidationError as e:
            raise ValueError(f"Invalid account_id: {e}")

    @field_validator("threshold_amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """Validate amount using Decimal for precision."""
        try:
            return float(Validator.validate_amount(v))
        except ValidationError as e:
            raise ValueError(f"Invalid threshold_amount: {e}")


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


class MFAEnrollRequest(BaseModel):
    """Request to enroll in MFA."""

    user_id: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    method: str = Field("totp", description="MFA method: totp, sms, or email")


class MFAEnrollResponse(BaseModel):
    """Response from MFA enrollment."""

    user_id: str
    method: str
    secret: str
    backup_codes: List[str]
    status: str
    enrolled_at: str


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA token."""

    user_id: str = Field(..., min_length=1)
    token: str = Field(..., min_length=6, max_length=8)
    secret: Optional[str] = None
    hashed_backup_codes: Optional[List[str]] = None
    mfa_login_challenge: Optional[str] = None


class MFAVerifyResponse(BaseModel):
    """Response from MFA verification."""

    success: bool
    message: str
    user_id: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None
    session_id: Optional[str] = None


class MFAStatusResponse(BaseModel):
    """MFA status for a user."""

    user_id: str
    is_locked_out: bool = False
    lockout_remaining_seconds: Optional[int] = None
    is_enrolled: bool = False
    status: Optional[str] = None
    method: Optional[str] = None
    enrolled_at: Optional[str] = None
    backup_codes_remaining: Optional[int] = None


class MFADisableRequest(BaseModel):
    """Request to disable MFA."""

    user_id: str = Field(..., min_length=1)
    secret: str = Field(..., min_length=1)
    token: str = Field(..., min_length=6, max_length=8)
    reason: Optional[str] = None


class MFADisableResponse(BaseModel):
    """Response from MFA disable."""

    success: bool
    user_id: str
    message: str


class LoginRequest(BaseModel):
    """Request to authenticate via API credentials."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=255)
    mfa_secret: Optional[str] = Field(
        None,
        description="Deprecated and ignored. Challenge flow no longer accepts raw secrets.",
    )
    mfa_token: Optional[str] = Field(None, description="TOTP or backup code")
    mfa_login_challenge: Optional[str] = None


class LoginResponse(BaseModel):
    """Response from login endpoint."""

    success: bool
    user_id: str
    mfa_required: bool = False
    mfa_secret: Optional[str] = None
    mfa_login_challenge: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None
    message: str
    session_id: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Request to refresh an access token."""

    refresh_token: str = Field(..., min_length=32)
    session_id: str = Field(..., min_length=1)


class RefreshTokenResponse(BaseModel):
    """Response to refresh request."""

    success: bool
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    session_id: str
    message: str


class LogoutRequest(BaseModel):
    """Request to revoke one or all active sessions."""

    session_id: Optional[str] = Field(None, min_length=1)


class LogoutResponse(BaseModel):
    """Response from logout endpoint."""

    success: bool
    message: str
