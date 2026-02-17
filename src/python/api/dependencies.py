"""
API Dependencies
================

Shared dependencies: graph connection, authentication, rate limiting.
"""

import logging
from typing import Dict, List, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from gremlin_python.driver import serializer
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.python.config.settings import Settings, get_settings
from src.python.security.session_manager import SessionConfig, SessionError, SessionManager

logger = logging.getLogger(__name__)

_connection: Optional[DriverRemoteConnection] = None
_traversal = None
_session_manager: Optional[SessionManager] = None


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
            _traversal = traversal().with_remote(_connection)
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


def close_graph_connection() -> None:
    """Close the graph connection gracefully."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
        logger.info("Closed JanusGraph connection")


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
    if request.url.path.startswith("/api/v1/auth/"):
        return
    if credentials is None:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication token")

    if settings.api_key and credentials.credentials == settings.api_key:
        request.state.user_id = "api-key-user"
        request.state.user_roles = _normalize_roles(settings.auth_default_roles)
        request.state.mfa_verified = True
        request.state.auth_mode = "api_key"
        return

    try:
        payload = get_auth_session_manager().verify_access_token(credentials.credentials)
    except SessionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token payload")

    user_roles = _normalize_roles(payload.get("roles", []))
    request.state.user_id = user_id
    request.state.user_roles = user_roles
    request.state.mfa_verified = bool(payload.get("mfa_verified", False))
    request.state.auth_mode = "session"

    if _is_mfa_required(user_roles) and not request.state.mfa_verified:
        raise HTTPException(status_code=403, detail="MFA required for this role")


def _normalize_roles(raw_roles: str | List[str]) -> List[str]:
    """Normalize role input to a list of lowercase role names."""
    if isinstance(raw_roles, list):
        return [str(role).strip().lower() for role in raw_roles if str(role).strip()]
    if not raw_roles:
        return []
    return [role.strip().lower() for role in raw_roles.split(",") if role.strip()]


def _is_mfa_required(user_roles: List[str]) -> bool:
    """Return True when one of the user roles requires MFA."""
    settings = get_settings()
    required_roles = {role.strip().lower() for role in settings.mfa_required_roles.split(",") if role.strip()}
    return any(role in required_roles for role in user_roles)


def get_auth_session_manager() -> SessionManager:
    """Get or create the shared auth session manager."""
    global _session_manager
    if _session_manager is None:
        secret = get_settings().api_jwt_secret
        if not secret:
            raise RuntimeError(
                "api_jwt_secret must be configured when authentication or session features are used."
            )
        _session_manager = SessionManager(
            config=SessionConfig(
                secret_key=secret,
                access_token_ttl_minutes=get_settings().api_access_token_ttl_minutes,
                refresh_token_ttl_minutes=get_settings().api_refresh_token_ttl_minutes,
            )
        )
    return _session_manager


def clear_auth_session_manager() -> None:
    """Clear auth session manager singleton cache (mainly for tests)."""
    global _session_manager
    _session_manager = None


limiter = Limiter(key_func=get_remote_address)


def flatten_value_map(value_map: Dict) -> Dict:
    """Flatten JanusGraph valueMap (lists to single values).

    .. deprecated:: 1.4.0
        Use ``GraphRepository.flatten_value_map`` instead.
    """
    from src.python.repository.graph_repository import _flatten_value_map

    return _flatten_value_map(value_map)
