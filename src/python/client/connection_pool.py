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
        """Get the age of this connection in seconds since creation."""
        return time.time() - self.created_at

    def is_stale(self, recycle_seconds: int) -> bool:
        """Check if connection has exceeded the recycle threshold.
        
        Args:
            recycle_seconds: Maximum allowed age in seconds.
        
        Returns:
            True if connection should be recycled.
        """
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
        self._maintenance_stop = threading.Event()
        self._maintenance_thread: Optional[threading.Thread] = None

        self._initialize_pool()
        self._start_maintenance()
        logger.info(
            "ConnectionPool initialized: size=%d, max_overflow=%d, host=%s:%d",
            self._config.pool_size,
            self._config.max_overflow,
            self._config.host,
            self._config.port,
        )

    def _initialize_pool(self) -> None:
        """Pre-create connections to fill the pool to configured size."""
        for _ in range(self._config.pool_size):
            try:
                conn = self._create_connection()
                self._pool.put_nowait(conn)
            except Exception as e:
                logger.warning("Failed to pre-create connection: %s", e)

    def _start_maintenance(self) -> None:
        """Start background maintenance loop for proactive pool refill."""
        if self._config.health_check_interval <= 0:
            return

        self._maintenance_thread = threading.Thread(
            target=self._maintenance_loop,
            name=f"connection-pool-maintenance-{id(self)}",
            daemon=True,
        )
        self._maintenance_thread.start()

    def _maintenance_loop(self) -> None:
        """Continuously check pool health and refill if under target."""
        while not self._maintenance_stop.wait(self._config.health_check_interval):
            if self._closed:
                break
            self._check_pool_health()

    def _check_pool_health(self) -> None:
        """Refill available pooled connections up to configured pool_size."""
        if self._closed:
            return

        missing = self._config.pool_size - self._pool.qsize()
        if missing <= 0:
            return

        for _ in range(missing):
            if self._closed:
                break
            try:
                conn = self._create_connection()
                self._pool.put_nowait(conn)
            except Exception:
                logger.warning("Failed to refill connection during maintenance", exc_info=True)
                break

    def _create_connection(self) -> _PooledConnection:
        """Create and establish a new JanusGraph client connection.

        Returns:
            Wrapped connection with metadata for pool tracking.

        Raises:
            ConnectionError: If connection cannot be established.
        """
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
        """Safely close and remove a pooled connection.

        Args:
            conn: The pooled connection to destroy.
        """
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
        """Acquire a connection from the pool, creating overflow if needed.

        Returns:
            An available pooled connection.

        Raises:
            ConnectionError: If pool exhausted and max overflow reached.
        """
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
        """Return a connection to the pool after use.

        Args:
            conn: The connection to return to the pool.
        """
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
        self._maintenance_stop.set()
        if self._maintenance_thread and self._maintenance_thread.is_alive():
            self._maintenance_thread.join(timeout=self._config.health_check_interval + 1)

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
        """Current number of available connections in the pool."""
        return self._pool.qsize()

    @property
    def overflow_count(self) -> int:
        """Current number of overflow connections in use."""
        return self._overflow_count

    def stats(self) -> dict[str, Any]:
        """Return pool statistics for monitoring.

        Returns:
            Dictionary with pool_size, available, overflow, and usage counts.
        """
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
        """Enter context manager, returning the pool instance."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager, closing all connections."""
        self.close()
