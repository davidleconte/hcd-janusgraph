"""
Authentication & MFA Router
============================

Provides MFA enrollment, verification, and status endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from src.python.api.dependencies import get_settings, limiter
from src.python.api.models import (
    MFADisableRequest,
    MFADisableResponse,
    MFAEnrollRequest,
    MFAEnrollResponse,
    MFAStatusResponse,
    MFAVerifyRequest,
    MFAVerifyResponse,
)
from src.python.security.mfa import MFAEnrollment, MFAManager, MFAMethod

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

_mfa_manager: Optional[MFAManager] = None
_mfa_enrollment: Optional[MFAEnrollment] = None


def get_mfa_manager() -> MFAManager:
    global _mfa_manager
    if _mfa_manager is None:
        _mfa_manager = MFAManager()
    return _mfa_manager


def get_mfa_enrollment() -> MFAEnrollment:
    global _mfa_enrollment
    if _mfa_enrollment is None:
        _mfa_enrollment = MFAEnrollment(get_mfa_manager())
    return _mfa_enrollment


@router.post("/mfa/enroll", response_model=MFAEnrollResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def enroll_mfa(request: Request, body: MFAEnrollRequest):
    """
    Start MFA enrollment for a user.

    Returns TOTP secret and QR code for authenticator app setup.
    User must verify with a valid token to complete enrollment.
    """
    enrollment = get_mfa_enrollment()

    try:
        method = MFAMethod(body.method)
    except ValueError:
        raise HTTPException(400, f"Unsupported MFA method: {body.method}")

    try:
        data = enrollment.enroll_user(body.user_id, body.email, method=method)
    except NotImplementedError:
        raise HTTPException(400, f"MFA method '{body.method}' not yet implemented")

    return MFAEnrollResponse(
        user_id=data["user_id"],
        method=data["method"],
        secret=data["secret"],
        backup_codes=data["backup_codes"],
        status=data["status"],
        enrolled_at=data["enrolled_at"],
    )


@router.post("/mfa/verify", response_model=MFAVerifyResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def verify_mfa(request: Request, body: MFAVerifyRequest):
    """
    Verify MFA token (for enrollment confirmation or login).

    Accepts either a TOTP token or a backup code.
    """
    mgr = get_mfa_manager()

    if not body.secret:
        raise HTTPException(400, "Secret is required for verification")

    is_valid = mgr.verify_totp(body.secret, body.token, user_id=body.user_id)

    if not is_valid and body.hashed_backup_codes:
        is_valid = mgr.verify_backup_code(body.token, body.hashed_backup_codes)

    if is_valid:
        return MFAVerifyResponse(
            success=True,
            message="MFA verification successful",
            user_id=body.user_id,
        )

    lockout_remaining = mgr.get_lockout_remaining(body.user_id)
    if lockout_remaining:
        raise HTTPException(
            429,
            f"Account locked. Try again in {lockout_remaining} seconds.",
        )

    raise HTTPException(401, "Invalid MFA token")


@router.get("/mfa/status/{user_id}", response_model=MFAStatusResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def get_mfa_status(request: Request, user_id: str):
    """Get MFA enrollment status for a user."""
    mgr = get_mfa_manager()
    lockout = mgr.get_lockout_remaining(user_id)

    return MFAStatusResponse(
        user_id=user_id,
        is_locked_out=lockout is not None,
        lockout_remaining_seconds=lockout,
    )


@router.post("/mfa/disable", response_model=MFADisableResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def disable_mfa(request: Request, body: MFADisableRequest):
    """
    Disable MFA for a user.

    Requires a valid TOTP token or backup code for confirmation.
    """
    mgr = get_mfa_manager()

    is_valid = mgr.verify_totp(body.secret, body.token, user_id=body.user_id)

    if not is_valid:
        raise HTTPException(401, "Invalid MFA token — cannot disable MFA")

    enrollment = get_mfa_enrollment()
    enrollment.unenroll_user(body.user_id, reason=body.reason or "User request")

    return MFADisableResponse(
        success=True,
        user_id=body.user_id,
        message="MFA disabled successfully",
    )
