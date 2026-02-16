"""
Authentication & MFA Router
===========================

Provides authentication session endpoints and MFA enrollment/verification flows.
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from src.python.api.dependencies import get_auth_session_manager, get_settings, limiter
from src.python.api.models import (
    LoginRequest,
    LoginResponse,
    MFADisableRequest,
    MFADisableResponse,
    MFAEnrollRequest,
    MFAEnrollResponse,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    MFAStatusResponse,
    MFAVerifyRequest,
    MFAVerifyResponse,
)
from src.python.security.mfa import MFAEnrollment, MFAManager, MFAMethod
from src.python.security.session_manager import SessionError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

_mfa_manager: Optional[MFAManager] = None
_mfa_enrollment: Optional[MFAEnrollment] = None
_login_challenges: Dict[str, Dict[str, Any]] = {}
_challenge_ttl_seconds = 300


def _split_roles(raw_roles: str) -> list[str]:
    """Split and normalize a comma-separated role list."""
    return [role.strip().lower() for role in raw_roles.split(",") if role.strip()]


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


def _create_login_challenge(
    user_id: str,
    roles: list[str],
    *,
    secret: Optional[str] = None,
    hashed_backup_codes: Optional[list[str]] = None,
) -> tuple[str, str, list[str]]:
    """Create a login MFA challenge and return (challenge_id, secret, hashed_codes)."""
    mgr = get_mfa_manager()
    challenge_secret = secret or mgr.generate_secret()
    backup_codes: list[str] = []
    challenge_hashed_backup_codes = hashed_backup_codes
    if challenge_hashed_backup_codes is None:
        backup_codes = mgr.generate_backup_codes()
        challenge_hashed_backup_codes = [
            mgr.hash_backup_code(code) for code in backup_codes
        ]
    challenge_id = secrets.token_urlsafe(24)
    _login_challenges[challenge_id] = {
        "user_id": user_id,
        "secret": challenge_secret,
        "roles": roles,
        "hashed_backup_codes": challenge_hashed_backup_codes,
        "issued_at": datetime.now(timezone.utc),
    }
    return challenge_id, challenge_secret, backup_codes


def _get_login_challenge(challenge_id: str) -> Optional[Dict[str, Any]]:
    """Get a valid login challenge and drop expired ones."""
    challenge = _login_challenges.get(challenge_id)
    if not challenge:
        return None
    age_seconds = (datetime.now(timezone.utc) - challenge["issued_at"]).total_seconds()
    if age_seconds > _challenge_ttl_seconds:
        _login_challenges.pop(challenge_id, None)
        return None
    return challenge


def _issue_session(
    request: Request, user_id: str, roles: list[str], mfa_verified: bool
) -> dict:
    """Create and return a session record."""
    manager = get_auth_session_manager()
    return manager.create_session(
        user_id,
        roles=roles,
        mfa_verified=mfa_verified,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def login(request: Request, body: LoginRequest):
    """
    Authenticate with credentials and optionally complete MFA.

    If MFA is required for the user role, this returns a challenge unless a valid
    `mfa_login_challenge` and `mfa_token` are provided.
    """
    settings = get_settings()
    if body.username != settings.api_user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if settings.api_user_password and body.password != settings.api_user_password:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    roles = _split_roles(settings.api_user_roles)
    mfa_manager = get_mfa_manager()
    mfa_required = mfa_manager.is_mfa_required(roles)

    if not mfa_required:
        session = _issue_session(request, body.username, roles, mfa_verified=True)
        return LoginResponse(
            success=True,
            user_id=body.username,
            mfa_required=False,
            roles=roles,
            access_token=session["access_token"],
            refresh_token=session["refresh_token"],
            token_type=session["token_type"],
            expires_in=session["expires_in"],
            message="Login successful",
            session_id=session["session_id"],
        )

    if body.mfa_login_challenge:
        challenge = _get_login_challenge(body.mfa_login_challenge)
        if not challenge or challenge["user_id"] != body.username:
            raise HTTPException(
                HTTP_401_UNAUTHORIZED,
                "Invalid or expired MFA challenge",
            )
        if not body.mfa_token:
            raise HTTPException(HTTP_400_BAD_REQUEST, "MFA token is required for challenge completion")

        is_valid = mfa_manager.verify_totp(challenge["secret"], body.mfa_token, user_id=body.username)
        used_backup_code = False
        if not is_valid:
            is_valid = mfa_manager.verify_backup_code(
                body.mfa_token,
                challenge.get("hashed_backup_codes", []),
            )
            used_backup_code = is_valid
        if not is_valid:
            lockout = mfa_manager.get_lockout_remaining(body.username)
            if lockout:
                raise HTTPException(
                    HTTP_400_BAD_REQUEST,
                    f"Account locked. Try again in {lockout} seconds.",
                )
            raise HTTPException(HTTP_401_UNAUTHORIZED, "Invalid MFA token")

        if used_backup_code:
            get_mfa_enrollment().consume_backup_code(body.username, body.mfa_token)

        _login_challenges.pop(body.mfa_login_challenge, None)
        session = _issue_session(request, body.username, roles, mfa_verified=True)
        return LoginResponse(
            success=True,
            user_id=body.username,
            mfa_required=False,
            roles=roles,
            access_token=session["access_token"],
            refresh_token=session["refresh_token"],
            token_type=session["token_type"],
            expires_in=session["expires_in"],
            message="Login successful",
            session_id=session["session_id"],
        )

    enrollment = get_mfa_enrollment().get_user_enrollment(body.username)
    stored_secret = None
    stored_hashed_backup_codes = None
    if enrollment:
        stored_secret = enrollment.get("secret")
        stored_hashed_backup_codes = enrollment.get("hashed_backup_codes")
    challenge_id, secret, _ = _create_login_challenge(
        body.username,
        roles,
        secret=stored_secret,
        hashed_backup_codes=stored_hashed_backup_codes,
    )
    return LoginResponse(
        success=True,
        user_id=body.username,
        mfa_required=True,
        mfa_secret=secret,
        mfa_login_challenge=challenge_id,
        roles=roles,
        message="MFA required. Provide mfa_token with mfa_login_challenge.",
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def refresh_token(request: Request, body: RefreshTokenRequest):
    """Refresh an access token using a refresh token and session id."""
    _ = request
    manager = get_auth_session_manager()
    try:
        refreshed = manager.refresh_session(body.refresh_token, body.session_id)
    except SessionError as exc:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(exc))

    return RefreshTokenResponse(
        success=True,
        access_token=refreshed["access_token"],
        refresh_token=refreshed["refresh_token"],
        token_type=refreshed["token_type"],
        expires_in=refreshed["expires_in"],
        session_id=refreshed["session_id"],
        message="Access token refreshed",
    )


@router.post("/logout", response_model=LogoutResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def logout(
    request: Request,
    body: LogoutRequest,
    authorization: str = Header(default=None),
):
    """Revoke the current session or a specific session id."""
    manager = get_auth_session_manager()
    session_id = body.session_id
    if not session_id and authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(
                HTTP_400_BAD_REQUEST,
                "Authorization must use Bearer token",
            )
        try:
            payload = manager.verify_access_token(token)
        except SessionError as exc:
            raise HTTPException(HTTP_401_UNAUTHORIZED, str(exc))
        session_id = payload.get("sid")

    if not session_id:
        raise HTTPException(HTTP_400_BAD_REQUEST, "session_id or valid Authorization is required")

    if manager.revoke_session(session_id):
        return LogoutResponse(success=True, message="Session revoked")

    return LogoutResponse(success=False, message="Session not found or already revoked")


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

    if body.mfa_login_challenge:
        challenge = _get_login_challenge(body.mfa_login_challenge)
        if not challenge or challenge["user_id"] != body.user_id:
            raise HTTPException(
                HTTP_401_UNAUTHORIZED,
                "Invalid or expired MFA challenge",
            )
        if not body.token:
            raise HTTPException(HTTP_400_BAD_REQUEST, "MFA token is required")

        is_valid = mgr.verify_totp(challenge["secret"], body.token, user_id=body.user_id)
        used_backup_code = False
        if not is_valid and challenge.get("hashed_backup_codes"):
            is_valid = mgr.verify_backup_code(body.token, challenge["hashed_backup_codes"])
            used_backup_code = is_valid
        if is_valid and used_backup_code:
            get_mfa_enrollment().consume_backup_code(body.user_id, body.token)
        if is_valid:
            _login_challenges.pop(body.mfa_login_challenge, None)
            session = _issue_session(request, body.user_id, _split_roles(get_settings().api_user_roles), mfa_verified=True)
            return MFAVerifyResponse(
                success=True,
                message="MFA verification successful",
                user_id=body.user_id,
                access_token=session["access_token"],
                refresh_token=session["refresh_token"],
                token_type=session["token_type"],
                expires_in=session["expires_in"],
                session_id=session["session_id"],
            )
        lockout = mgr.get_lockout_remaining(body.user_id)
        if lockout:
            raise HTTPException(
                HTTP_400_BAD_REQUEST,
                f"Account locked. Try again in {lockout} seconds.",
            )
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Invalid MFA token")

    if not body.secret:
        raise HTTPException(HTTP_400_BAD_REQUEST, "Secret is required for verification")

    enrollment = get_mfa_enrollment()
    is_valid = enrollment.verify_enrollment(body.user_id, body.secret, body.token)

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
    enrollment = get_mfa_enrollment().get_user_enrollment(user_id)

    return MFAStatusResponse(
        user_id=user_id,
        is_locked_out=lockout is not None,
        lockout_remaining_seconds=lockout,
        is_enrolled=bool(enrollment and enrollment.get("status") == "active"),
        status=enrollment.get("status") if enrollment else None,
        method=enrollment.get("method") if enrollment else None,
        enrolled_at=enrollment.get("enrolled_at") if enrollment else None,
        backup_codes_remaining=len(enrollment.get("hashed_backup_codes", []))
        if enrollment
        else 0,
    )


@router.post("/mfa/disable", response_model=MFADisableResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
def disable_mfa(request: Request, body: MFADisableRequest):
    """
    Disable MFA for a user.

    Requires a valid TOTP token or backup code for confirmation.
    """
    mgr = get_mfa_manager()

    enrollment = get_mfa_enrollment().get_user_enrollment(body.user_id)
    secret = enrollment.get("secret") if enrollment else body.secret
    is_valid = mgr.verify_totp(secret, body.token, user_id=body.user_id)
    used_backup_code = False

    if not is_valid:
        hashed_backup_codes = []
        if enrollment:
            hashed_backup_codes = enrollment.get("hashed_backup_codes", [])
        if hashed_backup_codes:
            is_valid = mgr.verify_backup_code(body.token, hashed_backup_codes)
            used_backup_code = is_valid
    if used_backup_code and enrollment:
        get_mfa_enrollment().consume_backup_code(body.user_id, body.token)

    if not is_valid:
        raise HTTPException(401, "Invalid MFA token — cannot disable MFA")

    enrollment = get_mfa_enrollment()
    enrollment.unenroll_user(body.user_id, reason=body.reason or "User request")

    return MFADisableResponse(
        success=True,
        user_id=body.user_id,
        message="MFA disabled successfully",
    )
