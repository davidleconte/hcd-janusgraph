"""
JanusGraph client module.

Exports:
    - JanusGraphClient: Main synchronous client class
    - AsyncJanusGraphClient: Async wrapper for FastAPI endpoints
    - AsyncConnectionPool: Async connection pool
    - All custom exceptions

File: __init__.py
Created: 2026-01-28
Updated: 2026-03-25 - Added async client support
Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watsonx.Data Global Product Specialist (GPS)
"""

from .async_client import AsyncConnectionPool, AsyncJanusGraphClient, shutdown_executor
from .connection_pool import ConnectionPool, PoolConfig
from .exceptions import ConnectionError, JanusGraphError, QueryError, TimeoutError, ValidationError
from .janusgraph_client import JanusGraphClient

__all__ = [
    # Sync client
    "JanusGraphClient",
    "ConnectionPool",
    "PoolConfig",
    # Async client
    "AsyncJanusGraphClient",
    "AsyncConnectionPool",
    "shutdown_executor",
    # Exceptions
    "JanusGraphError",
    "ConnectionError",
    "QueryError",
    "TimeoutError",
    "ValidationError",
]
