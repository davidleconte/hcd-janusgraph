"""
API Dependencies
================

Shared dependencies: graph connection, authentication, rate limiting.
"""

import logging
from typing import Dict, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from gremlin_python.driver import serializer
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.python.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

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
    if credentials is None or credentials.credentials != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


limiter = Limiter(key_func=get_remote_address)


def flatten_value_map(value_map: Dict) -> Dict:
    """Flatten JanusGraph valueMap (lists to single values).

    .. deprecated:: 1.4.0
        Use ``GraphRepository.flatten_value_map`` instead.
    """
    from src.python.repository.graph_repository import _flatten_value_map

    return _flatten_value_map(value_map)
