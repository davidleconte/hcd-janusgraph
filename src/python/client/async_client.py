"""
Async Wrapper for JanusGraph Client
====================================

Provides an async interface for the synchronous JanusGraph client by running
operations in a thread pool executor. This prevents blocking the event loop
in async FastAPI endpoints.

Features:
- Thread pool execution for non-blocking operations
- OpenTelemetry distributed tracing integration
- Prometheus metrics for queries and pool utilization

Usage:
    from src.python.client.async_client import AsyncJanusGraphClient

    async with AsyncJanusGraphClient(host="localhost", port=18182) as client:
        result = await client.execute("g.V().count()")

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watsonx.Data Global Product Specialist (GPS)
Date: 2026-03-25
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

from .connection_pool import ConnectionPool, PoolConfig
from .exceptions import ConnectionError, QueryError
from .janusgraph_client import JanusGraphClient
from ..utils.tracing import Status, StatusCode, get_tracer

logger = logging.getLogger(__name__)

# Tracer for distributed tracing
_tracer = get_tracer()

# Prometheus metrics (lazy initialization)
_metrics_initialized = False
_client_metrics = {}

# Global thread pool for async operations
# Sized for 12-CPU machines as per AGENTS.md requirements
_default_executor: Optional[ThreadPoolExecutor] = None


def _init_client_metrics():
    """Initialize Prometheus metrics for async client."""
    global _metrics_initialized, _client_metrics

    if _metrics_initialized:
        return

    try:
        from prometheus_client import Counter, Histogram, Gauge, REGISTRY

        def _safe_create(metric_class, name, desc, labels=None, **kwargs):
            """Create metric or return existing one from registry."""
            # Check if metric already exists
            check_names = [name, f"{name}_total", f"{name}_created"]
            for check_name in check_names:
                if check_name in REGISTRY._names_to_collectors:
                    return REGISTRY._names_to_collectors[check_name]
            try:
                if labels:
                    return metric_class(name, desc, labels, **kwargs)
                return metric_class(name, desc, **kwargs)
            except ValueError:
                # Race condition - get existing
                for check_name in check_names:
                    if check_name in REGISTRY._names_to_collectors:
                        return REGISTRY._names_to_collectors[check_name]
                return None

        # Async query metrics
        _client_metrics["async_queries_total"] = _safe_create(
            Counter,
            "janusgraph_async_queries_total",
            "Total async queries executed",
            ["status"],
        )
        _client_metrics["async_query_duration_seconds"] = _safe_create(
            Histogram,
            "janusgraph_async_query_duration_seconds",
            "Async query duration in seconds",
            ["operation"],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )

        # Pool metrics
        _client_metrics["pool_active_connections"] = _safe_create(
            Gauge,
            "janusgraph_pool_active_connections",
            "Number of active connections in pool",
            [],
        )
        _client_metrics["pool_idle_connections"] = _safe_create(
            Gauge,
            "janusgraph_pool_idle_connections",
            "Number of idle connections in pool",
            [],
        )
        _client_metrics["pool_wait_duration_seconds"] = _safe_create(
            Histogram,
            "janusgraph_pool_wait_duration_seconds",
            "Time spent waiting for pool connection",
            [],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
        )
        _client_metrics["pool_size"] = _safe_create(
            Gauge,
            "janusgraph_pool_size",
            "Total pool size",
            [],
        )

        _metrics_initialized = True
        logger.info("Async client Prometheus metrics initialized")
    except ImportError:
        logger.debug("prometheus_client not available, metrics disabled")
    except Exception as e:
        logger.warning("Failed to initialize metrics: %s", e)


def _get_executor() -> ThreadPoolExecutor:
    """Get or create the global thread pool executor."""
    global _default_executor
    if _default_executor is None:
        _default_executor = ThreadPoolExecutor(
            max_workers=12,  # Match AGENTS.md deterministic setup
            thread_name_prefix="janusgraph-async-",
        )
    _init_client_metrics()
    return _default_executor


class AsyncJanusGraphClient:
    """
    Async wrapper for JanusGraphClient that runs blocking operations in a thread pool.

    This allows using the synchronous Gremlin driver in async FastAPI endpoints
    without blocking the event loop.

    Example:
        async with AsyncJanusGraphClient() as client:
            count = await client.execute("g.V().count()")
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 18182,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = True,
        verify_certs: bool = True,
        ca_certs: Optional[str] = None,
        executor: Optional[ThreadPoolExecutor] = None,
    ) -> None:
        """
        Initialize async JanusGraph client.

        Args:
            host: JanusGraph server hostname
            port: Gremlin WebSocket port
            username: Authentication username
            password: Authentication password
            use_ssl: Use SSL/TLS (wss://)
            verify_certs: Verify SSL certificates
            ca_certs: Path to CA certificate bundle
            executor: Custom thread pool executor (uses global if None)
        """
        self._sync_client = JanusGraphClient(
            host=host,
            port=port,
            username=username,
            password=password,
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            ca_certs=ca_certs,
        )
        self._executor = executor
        self._connected = False

    async def connect(self) -> None:
        """Establish connection to JanusGraph in a background thread."""
        with _tracer.start_as_current_span("async_janusgraph.connect") as span:
            span.set_attribute("db.system", "janusgraph")
            span.set_attribute("db.url", self._sync_client.url)
            
            loop = asyncio.get_running_loop()
            executor = self._executor or _get_executor()

            try:
                start_time = time.time()
                await loop.run_in_executor(executor, self._sync_client.connect)
                self._connected = True
                
                duration = time.time() - start_time
                span.set_attribute("db.connection_duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.OK))
                
                logger.info("AsyncJanusGraphClient connected to %s", self._sync_client.url)
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error("Failed to connect async client: %s", e)
                raise ConnectionError(f"Failed to connect: {e}") from e

    async def execute(
        self, query: str, bindings: Optional[dict[str, Any]] = None
    ) -> list[Any]:
        """
        Execute a Gremlin query asynchronously.

        Args:
            query: Gremlin query string
            bindings: Optional query parameter bindings

        Returns:
            List of query results

        Raises:
            QueryError: If query execution fails
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Client not connected. Call connect() first.")

        with _tracer.start_as_current_span("async_janusgraph.execute") as span:
            span.set_attribute("db.system", "janusgraph")
            span.set_attribute("db.operation", "query")
            # Truncate query in span for security (first 100 chars)
            span.set_attribute("db.statement", query[:100])
            if bindings:
                span.set_attribute("db.bindings_count", len(bindings))

            loop = asyncio.get_running_loop()
            executor = self._executor or _get_executor()

            try:
                start_time = time.time()
                result = await loop.run_in_executor(
                    executor, self._sync_client.execute, query, bindings
                )
                duration = time.time() - start_time

                # Record metrics
                if "async_queries_total" in _client_metrics and _client_metrics["async_queries_total"]:
                    _client_metrics["async_queries_total"].labels(status="success").inc()
                if "async_query_duration_seconds" in _client_metrics and _client_metrics["async_query_duration_seconds"]:
                    _client_metrics["async_query_duration_seconds"].labels(operation="execute").observe(duration)

                span.set_attribute("db.duration_ms", duration * 1000)
                span.set_attribute("db.result_count", len(result))
                span.set_status(Status(StatusCode.OK))

                logger.debug("Async query returned %d results in %.3fs", len(result), duration)
                return result
            except Exception as e:
                # Record failure metric
                if "async_queries_total" in _client_metrics and _client_metrics["async_queries_total"]:
                    _client_metrics["async_queries_total"].labels(status="error").inc()

                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error("Async query failed: %s", e)
                raise

    async def close(self) -> None:
        """Close the connection asynchronously."""
        if not self._connected:
            return

        with _tracer.start_as_current_span("async_janusgraph.close") as span:
            span.set_attribute("db.system", "janusgraph")
            span.set_attribute("db.url", self._sync_client.url)

            loop = asyncio.get_running_loop()
            executor = self._executor or _get_executor()

            try:
                await loop.run_in_executor(executor, self._sync_client.close)
                self._connected = False
                span.set_status(Status(StatusCode.OK))
                logger.info("AsyncJanusGraphClient connection closed")
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error("Error closing async client: %s", e)
                self._connected = False
                raise

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected and self._sync_client.is_connected()

    async def __aenter__(self) -> "AsyncJanusGraphClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def __repr__(self) -> str:
        """String representation."""
        status = "connected" if self._connected else "disconnected"
        return f"AsyncJanusGraphClient(url={self._sync_client.url}, status={status})"


class AsyncConnectionPool:
    """
    Async wrapper for the connection pool.

    Provides async access to pooled connections, running blocking operations
    in a thread pool to avoid blocking the event loop.

    Example:
        pool = AsyncConnectionPool(PoolConfig(pool_size=5))
        async with pool.connection() as client:
            result = await client.execute("g.V().count()")
        await pool.close()
    """

    def __init__(
        self,
        config: Optional[PoolConfig] = None,
        executor: Optional[ThreadPoolExecutor] = None,
    ) -> None:
        """
        Initialize async connection pool.

        Args:
            config: Pool configuration
            executor: Custom thread pool executor
        """
        self._sync_pool = ConnectionPool(config)
        self._executor = executor
        self._update_pool_metrics()

    def _update_pool_metrics(self) -> None:
        """Update Prometheus pool gauges with current stats."""
        if not _metrics_initialized:
            return

        try:
            stats = self._sync_pool.stats()
            if _client_metrics.get("pool_active_connections"):
                _client_metrics["pool_active_connections"].set(stats.get("active", 0))
            if _client_metrics.get("pool_idle_connections"):
                _client_metrics["pool_idle_connections"].set(stats.get("idle", 0))
            if _client_metrics.get("pool_size"):
                _client_metrics["pool_size"].set(stats.get("total", 0))
        except Exception as e:
            logger.debug("Failed to update pool metrics: %s", e)

    @property
    def stats(self) -> dict[str, Any]:
        """Get pool statistics."""
        return self._sync_pool.stats()

    async def connection(self) -> "AsyncPooledConnection":
        """
        Get an async wrapper for a pooled connection.

        Returns:
            AsyncPooledConnection wrapper for the pooled client
        """
        with _tracer.start_as_current_span("async_pool.acquire") as span:
            span.set_attribute("pool.type", "async")

            # The sync pool's connection() is a context manager
            # We need to acquire synchronously first
            loop = asyncio.get_running_loop()
            executor = self._executor or _get_executor()

            try:
                start_time = time.time()
                # Acquire connection in thread pool
                pooled_conn = await loop.run_in_executor(
                    executor, self._sync_pool._acquire
                )
                wait_duration = time.time() - start_time

                # Record wait time metric
                if _client_metrics.get("pool_wait_duration_seconds"):
                    _client_metrics["pool_wait_duration_seconds"].observe(wait_duration)

                # Update pool metrics after acquisition
                self._update_pool_metrics()

                span.set_attribute("pool.wait_ms", wait_duration * 1000)
                span.set_status(Status(StatusCode.OK))

                return AsyncPooledConnection(self, pooled_conn, executor)
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    async def _release(self, conn: Any) -> None:
        """Release a connection back to the pool."""
        with _tracer.start_as_current_span("async_pool.release"):
            loop = asyncio.get_running_loop()
            executor = self._executor or _get_executor()
            await loop.run_in_executor(executor, self._sync_pool._release, conn)
            # Update pool metrics after release
            self._update_pool_metrics()

    async def close(self) -> None:
        """Close all connections in the pool."""
        with _tracer.start_as_current_span("async_pool.close") as span:
            loop = asyncio.get_running_loop()
            executor = self._executor or _get_executor()
            await loop.run_in_executor(executor, self._sync_pool.close)
            span.set_status(Status(StatusCode.OK))

    async def __aenter__(self) -> "AsyncConnectionPool":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()


class AsyncPooledConnection:
    """
    Async wrapper for a pooled connection that releases back to pool on close.
    """

    def __init__(
        self,
        pool: AsyncConnectionPool,
        pooled_conn: Any,
        executor: Optional[ThreadPoolExecutor] = None,
    ) -> None:
        self._pool = pool
        self._pooled_conn = pooled_conn
        self._executor = executor
        self._client = pooled_conn.client

    async def execute(
        self, query: str, bindings: Optional[dict[str, Any]] = None
    ) -> list[Any]:
        """
        Execute a Gremlin query asynchronously.

        Args:
            query: Gremlin query string
            bindings: Optional query parameter bindings

        Returns:
            List of query results
        """
        with _tracer.start_as_current_span("async_pooled_connection.execute") as span:
            span.set_attribute("db.system", "janusgraph")
            span.set_attribute("db.operation", "pooled_query")
            span.set_attribute("db.statement", query[:100])  # Truncate for security

            loop = asyncio.get_running_loop()
            executor = self._executor or _get_executor()

            try:
                start_time = time.time()
                result = await loop.run_in_executor(
                    executor, self._client.execute, query, bindings
                )
                duration = time.time() - start_time

                # Record metrics
                if _client_metrics.get("async_queries_total"):
                    _client_metrics["async_queries_total"].labels(status="success").inc()
                if _client_metrics.get("async_query_duration_seconds"):
                    _client_metrics["async_query_duration_seconds"].labels(operation="pooled_execute").observe(duration)

                span.set_attribute("db.duration_ms", duration * 1000)
                span.set_attribute("db.result_count", len(result))
                span.set_status(Status(StatusCode.OK))

                return result
            except Exception as e:
                if _client_metrics.get("async_queries_total"):
                    _client_metrics["async_queries_total"].labels(status="error").inc()
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    async def close(self) -> None:
        """Release the connection back to the pool."""
        await self._pool._release(self._pooled_conn)

    async def __aenter__(self) -> "AsyncPooledConnection":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()


def shutdown_executor() -> None:
    """Shutdown the global thread pool executor."""
    global _default_executor
    if _default_executor is not None:
        _default_executor.shutdown(wait=True)
        _default_executor = None
        logger.info("AsyncJanusGraph thread pool executor shutdown")
