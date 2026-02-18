"""
Connection Pool for JanusGraph
===============================

Thread-safe connection pool that manages multiple JanusGraph client connections.
Provides connection reuse, health checking, and automatic reconnection.

Usage:
    from src.python.client.connection_pool import ConnectionPool, PoolConfig

    pool = ConnectionPool(PoolConfig(host="localhost", port=18182, pool_size=5))
    with pool.connection() as client:
        result = client.execute("g.V().count()")
    pool.close()
"""

import logging
import os
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from queue import Empty, Queue
from typing import Any, Generator, Optional

from .exceptions import ConnectionError
from .janusgraph_client import JanusGraphClient

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Connection pool configuration."""

    host: str = "localhost"
    port: int = int(os.getenv("JANUSGRAPH_PORT", "18182"))
    username: Optional[str] = None
    password: Optional[str] = None
    use_ssl: bool = os.getenv("JANUSGRAPH_USE_SSL", "false").lower() == "true"
    verify_certs: bool = True
    ca_certs: Optional[str] = None
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: float = 30.0
    recycle_seconds: int = 3600
    health_check_interval: int = 30
    retry_on_failure: bool = True


@dataclass
class _PooledConnection:
    """Internal wrapper tracking connection metadata."""

    client: JanusGraphClient
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    use_count: int = 0

    @property
    def age(self) -> float:
        return time.time() - self.created_at

    def is_stale(self, recycle_seconds: int) -> bool:
        return self.age > recycle_seconds


class ConnectionPool:
    """
    Thread-safe connection pool for JanusGraph.

    Manages a pool of pre-established connections for reuse across threads.
    Supports overflow connections, health checks, and automatic recycling.

    Example:
        pool = ConnectionPool(PoolConfig(pool_size=5))
        with pool.connection() as client:
            result = client.execute("g.V().count()")
        pool.close()
    """

    def __init__(self, config: Optional[PoolConfig] = None) -> None:
        self._config = config or PoolConfig()
        self._pool: Queue[_PooledConnection] = Queue(maxsize=self._config.pool_size)
        self._overflow_count = 0
        self._lock = threading.RLock()
        self._closed = False
        self._total_created = 0
        self._total_returned = 0

        self._initialize_pool()
        logger.info(
            "ConnectionPool initialized: size=%d, max_overflow=%d, host=%s:%d",
            self._config.pool_size,
            self._config.max_overflow,
            self._config.host,
            self._config.port,
        )

    def _initialize_pool(self) -> None:
        for _ in range(self._config.pool_size):
            try:
                conn = self._create_connection()
                self._pool.put_nowait(conn)
            except Exception as e:
                logger.warning("Failed to pre-create connection: %s", e)

    def _create_connection(self) -> _PooledConnection:
        client = JanusGraphClient(
            host=self._config.host,
            port=self._config.port,
            username=self._config.username,
            password=self._config.password,
            use_ssl=self._config.use_ssl,
            verify_certs=self._config.verify_certs,
            ca_certs=self._config.ca_certs,
        )
        client.connect()
        with self._lock:
            self._total_created += 1
        return _PooledConnection(client=client)

    def _destroy_connection(self, conn: _PooledConnection) -> None:
        try:
            conn.client.close()
        except Exception as e:
            logger.debug("Error closing pooled connection: %s", e)

    @contextmanager
    def connection(self) -> Generator[JanusGraphClient, None, None]:
        """
        Get a connection from the pool.

        Yields a JanusGraphClient that is automatically returned to the pool.

        Raises:
            ConnectionError: If no connection available within timeout.
        """
        if self._closed:
            raise ConnectionError("Connection pool is closed")

        conn = self._acquire()
        try:
            yield conn.client
        finally:
            self._release(conn)

    def _acquire(self) -> _PooledConnection:
        try:
            conn = self._pool.get(timeout=self._config.pool_timeout)
            if conn.is_stale(self._config.recycle_seconds):
                self._destroy_connection(conn)
                conn = self._create_connection()
            conn.last_used = time.time()
            conn.use_count += 1
            return conn
        except Empty:
            pass

        with self._lock:
            if self._overflow_count < self._config.max_overflow:
                self._overflow_count += 1
                try:
                    return self._create_connection()
                except Exception:
                    self._overflow_count -= 1
                    raise

        raise ConnectionError(
            f"Connection pool exhausted (size={self._config.pool_size}, "
            f"overflow={self._overflow_count}/{self._config.max_overflow})"
        )

    def _release(self, conn: _PooledConnection) -> None:
        with self._lock:
            self._total_returned += 1

        if self._closed:
            self._destroy_connection(conn)
            return

        if conn.is_stale(self._config.recycle_seconds):
            self._destroy_connection(conn)
            try:
                conn = self._create_connection()
            except Exception:
                logger.warning("Failed to recreate stale connection during release", exc_info=True)
                return

        try:
            self._pool.put_nowait(conn)
        except Exception:
            with self._lock:
                self._overflow_count = max(0, self._overflow_count - 1)
            self._destroy_connection(conn)

    def close(self) -> None:
        """Close all connections and shut down the pool."""
        self._closed = True
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                self._destroy_connection(conn)
            except Empty:
                break
        logger.info(
            "ConnectionPool closed: created=%d, returned=%d",
            self._total_created,
            self._total_returned,
        )

    @property
    def size(self) -> int:
        return self._pool.qsize()

    @property
    def overflow_count(self) -> int:
        return self._overflow_count

    def stats(self) -> dict[str, Any]:
        return {
            "pool_size": self._config.pool_size,
            "available": self._pool.qsize(),
            "overflow": self._overflow_count,
            "max_overflow": self._config.max_overflow,
            "total_created": self._total_created,
            "total_returned": self._total_returned,
            "closed": self._closed,
        }

    def __enter__(self) -> "ConnectionPool":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
