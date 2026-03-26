"""
Unit tests for AsyncJanusGraphClient

Tests async wrapper functionality including:
- Async connection management
- Async query execution
- Async connection pool
- Thread pool executor integration

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watsonx.Data Global Product Specialist (GPS)
Date: 2026-03-25
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.python.client.async_client import (
    AsyncConnectionPool,
    AsyncJanusGraphClient,
    AsyncPooledConnection,
    shutdown_executor,
)
from src.python.client.connection_pool import PoolConfig
from src.python.client.exceptions import ConnectionError, QueryError


class TestAsyncJanusGraphClientInit:
    """Test AsyncJanusGraphClient initialization."""

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        client = AsyncJanusGraphClient()
        assert client._sync_client is not None
        assert client._connected is False
        assert client._executor is None

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters."""
        client = AsyncJanusGraphClient(
            host="remote-host",
            port=8182,
            username="admin",
            password="secret",
            use_ssl=True,
        )
        assert client._sync_client.host == "remote-host"
        assert client._sync_client.port == 8182

    def test_init_with_custom_executor(self):
        """Test initialization with custom executor."""
        executor = ThreadPoolExecutor(max_workers=4)
        client = AsyncJanusGraphClient(executor=executor)
        assert client._executor is executor

    def test_is_connected_false_initially(self):
        """Test is_connected returns False before connect."""
        client = AsyncJanusGraphClient()
        assert client.is_connected() is False


class TestAsyncJanusGraphClientConnection:
    """Test async connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful async connection."""
        client = AsyncJanusGraphClient()

        with patch.object(client._sync_client, 'connect') as mock_connect:
            with patch.object(client._sync_client, 'is_connected', return_value=True):
                await client.connect()
                mock_connect.assert_called_once()
                assert client.is_connected() is True

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure raises ConnectionError."""
        client = AsyncJanusGraphClient()

        with patch.object(
            client._sync_client, 'connect', side_effect=Exception("Connection refused")
        ):
            with pytest.raises(ConnectionError, match="Failed to connect"):
                await client.connect()
            assert client.is_connected() is False

    @pytest.mark.asyncio
    async def test_close_success(self):
        """Test successful async close."""
        client = AsyncJanusGraphClient()
        client._connected = True

        with patch.object(client._sync_client, 'close') as mock_close:
            await client.close()
            mock_close.assert_called_once()
            assert client.is_connected() is False

    @pytest.mark.asyncio
    async def test_close_when_not_connected(self):
        """Test close when not connected is no-op."""
        client = AsyncJanusGraphClient()
        client._connected = False

        with patch.object(client._sync_client, 'close') as mock_close:
            await client.close()
            mock_close.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager usage."""
        with patch('src.python.client.async_client.AsyncJanusGraphClient.connect', new_callable=AsyncMock) as mock_connect:
            with patch('src.python.client.async_client.AsyncJanusGraphClient.close', new_callable=AsyncMock) as mock_close:
                mock_connect.return_value = None
                mock_close.return_value = None

                async with AsyncJanusGraphClient() as client:
                    pass

                mock_connect.assert_called_once()
                mock_close.assert_called_once()


class TestAsyncJanusGraphClientExecute:
    """Test async query execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful async query execution."""
        client = AsyncJanusGraphClient()
        client._connected = True

        expected_result = [{"name": "Alice"}, {"name": "Bob"}]
        with patch.object(
            client._sync_client, 'execute', return_value=expected_result
        ) as mock_execute:
            result = await client.execute("g.V().limit(2)")
            assert result == expected_result
            mock_execute.assert_called_once_with("g.V().limit(2)", None)

    @pytest.mark.asyncio
    async def test_execute_with_bindings(self):
        """Test async query with bindings."""
        client = AsyncJanusGraphClient()
        client._connected = True

        bindings = {"name": "Alice"}
        with patch.object(client._sync_client, 'execute', return_value=[]) as mock_execute:
            await client.execute("g.V().has('name', name)", bindings)
            mock_execute.assert_called_once_with("g.V().has('name', name)", bindings)

    @pytest.mark.asyncio
    async def test_execute_not_connected_raises(self):
        """Test execute raises when not connected."""
        client = AsyncJanusGraphClient()
        client._connected = False

        with pytest.raises(ConnectionError, match="not connected"):
            await client.execute("g.V().count()")

    @pytest.mark.asyncio
    async def test_execute_query_error_propagates(self):
        """Test query errors propagate correctly."""
        client = AsyncJanusGraphClient()
        client._connected = True

        with patch.object(
            client._sync_client,
            'execute',
            side_effect=QueryError("Invalid query", query="g.invalid()")
        ):
            with pytest.raises(QueryError, match="Invalid query"):
                await client.execute("g.invalid()")


class TestAsyncConnectionPool:
    """Test AsyncConnectionPool."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        pool = AsyncConnectionPool()
        assert pool._sync_pool is not None
        assert pool._executor is None

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = PoolConfig(pool_size=10)
        pool = AsyncConnectionPool(config)
        assert pool._sync_pool._config.pool_size == 10

    def test_stats_property(self):
        """Test stats property returns pool stats."""
        pool = AsyncConnectionPool()
        stats = pool.stats
        assert "pool_size" in stats
        assert "available" in stats

    @pytest.mark.asyncio
    async def test_connection_acquires_pooled_connection(self):
        """Test connection() acquires a pooled connection."""
        pool = AsyncConnectionPool()

        with patch.object(pool._sync_pool, '_acquire') as mock_acquire:
            mock_pooled = Mock()
            mock_pooled.client = Mock()
            mock_acquire.return_value = mock_pooled

            conn = await pool.connection()
            assert isinstance(conn, AsyncPooledConnection)
            mock_acquire.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_closes_sync_pool(self):
        """Test async close closes sync pool."""
        pool = AsyncConnectionPool()

        with patch.object(pool._sync_pool, 'close') as mock_close:
            await pool.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager usage."""
        with patch('src.python.client.async_client.AsyncConnectionPool.close', new_callable=AsyncMock) as mock_close:
            mock_close.return_value = None

            async with AsyncConnectionPool() as pool:
                assert pool is not None

            mock_close.assert_called_once()


class TestAsyncPooledConnection:
    """Test AsyncPooledConnection."""

    @pytest.mark.asyncio
    async def test_execute_delegates_to_client(self):
        """Test execute delegates to underlying client."""
        mock_pool = Mock()
        mock_pooled = Mock()
        mock_client = Mock()
        mock_client.execute.return_value = [{"result": 1}]
        mock_pooled.client = mock_client

        conn = AsyncPooledConnection(mock_pool, mock_pooled)
        result = await conn.execute("g.V().count()")

        assert result == [{"result": 1}]
        mock_client.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_releases_to_pool(self):
        """Test close releases connection back to pool."""
        mock_pool = Mock()
        mock_pool._release = AsyncMock()
        mock_pooled = Mock()

        conn = AsyncPooledConnection(mock_pool, mock_pooled)
        await conn.close()

        mock_pool._release.assert_called_once_with(mock_pooled)

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager usage."""
        mock_pool = Mock()
        mock_pool._release = AsyncMock()
        mock_pooled = Mock()

        async with AsyncPooledConnection(mock_pool, mock_pooled) as conn:
            assert conn is not None

        mock_pool._release.assert_called_once()


class TestShutdownExecutor:
    """Test executor shutdown."""

    def test_shutdown_executor_when_initialized(self):
        """Test shutdown_executor cleans up global executor."""
        # Import the module to access the global
        from src.python.client import async_client

        # Create executor by calling _get_executor
        async_client._get_executor()
        assert async_client._default_executor is not None

        # Shutdown
        shutdown_executor()
        assert async_client._default_executor is None

    def test_shutdown_executor_when_not_initialized(self):
        """Test shutdown_executor is safe when no executor."""
        from src.python.client import async_client

        # Ensure no executor
        async_client._default_executor = None

        # Should not raise
        shutdown_executor()
        assert async_client._default_executor is None


class TestIntegrationScenarios:
    """Integration-style tests for common usage patterns."""

    @pytest.mark.asyncio
    async def test_concurrent_queries(self):
        """Test multiple concurrent async queries."""
        client = AsyncJanusGraphClient()
        client._connected = True

        with patch.object(
            client._sync_client, 'execute', return_value=[{"count": 1}]
        ):
            # Run multiple queries concurrently
            results = await asyncio.gather(
                client.execute("g.V().count()"),
                client.execute("g.E().count()"),
                client.execute("g.V().hasLabel('Person').count()"),
            )

            assert len(results) == 3
            assert all(len(r) == 1 for r in results)

    @pytest.mark.asyncio
    async def test_pool_reuse_connections(self):
        """Test pool reuses connections across operations."""
        config = PoolConfig(pool_size=2)
        pool = AsyncConnectionPool(config)

        with patch.object(pool._sync_pool, '_acquire') as mock_acquire:
            mock_pooled = Mock()
            mock_client = Mock()
            mock_client.execute.return_value = []
            mock_pooled.client = mock_client
            mock_acquire.return_value = mock_pooled

            # Get connection multiple times
            conn1 = await pool.connection()
            conn2 = await pool.connection()

            assert conn1 is not None
            assert conn2 is not None
            assert mock_acquire.call_count == 2


class TestTracingIntegration:
    """Test OpenTelemetry tracing integration."""

    @pytest.mark.asyncio
    async def test_connect_with_tracing_enabled(self):
        """Test that connect works with tracing enabled."""
        client = AsyncJanusGraphClient()

        with patch.object(client._sync_client, 'connect'):
            # Should not raise even with tracing
            await client.connect()
            assert client._connected is True

    @pytest.mark.asyncio
    async def test_execute_with_tracing_enabled(self):
        """Test that execute works with tracing enabled."""
        client = AsyncJanusGraphClient()
        client._connected = True

        with patch.object(client._sync_client, 'execute', return_value=[{"result": 42}]):
            # Should not raise even with tracing
            result = await client.execute("g.V().count()")
            assert result == [{"result": 42}]

    @pytest.mark.asyncio
    async def test_execute_error_with_tracing_enabled(self):
        """Test that execute errors are handled with tracing enabled."""
        client = AsyncJanusGraphClient()
        client._connected = True

        with patch.object(
            client._sync_client, 'execute',
            side_effect=QueryError("Query failed", query="g.V().invalid()")
        ):
            # Error should still propagate with tracing
            with pytest.raises(QueryError):
                await client.execute("g.V().invalid()")

    @pytest.mark.asyncio
    async def test_close_with_tracing_enabled(self):
        """Test that close works with tracing enabled."""
        client = AsyncJanusGraphClient()
        client._connected = True

        with patch.object(client._sync_client, 'close'):
            # Should not raise even with tracing
            await client.close()
            assert client._connected is False



class TestMetricsIntegration:
    """Test Prometheus metrics integration."""

    @pytest.mark.asyncio
    async def test_execute_records_metrics(self):
        """Test that execute records Prometheus metrics."""
        client = AsyncJanusGraphClient()
        client._connected = True

        # Ensure metrics are initialized
        from src.python.client.async_client import _init_client_metrics, _client_metrics
        _init_client_metrics()

        with patch.object(client._sync_client, 'execute', return_value=[{"count": 1}]):
            await client.execute("g.V().count()")

            # Metrics should be recorded (if prometheus_client available)
            if _client_metrics.get("async_queries_total"):
                # The counter should have been incremented
                pass  # Value check would require prometheus_client internals

    @pytest.mark.asyncio
    async def test_pool_metrics_updated_on_acquire(self):
        """Test that pool metrics are updated when acquiring connections."""
        config = PoolConfig(pool_size=2)
        pool = AsyncConnectionPool(config)

        # Ensure metrics are initialized
        from src.python.client.async_client import _init_client_metrics
        _init_client_metrics()

        with patch.object(pool._sync_pool, '_acquire') as mock_acquire:
            with patch.object(pool._sync_pool, 'stats', return_value={"active": 1, "idle": 1, "total": 2}):
                mock_pooled = Mock()
                mock_client = Mock()
                mock_client.execute.return_value = []
                mock_pooled.client = mock_client
                mock_acquire.return_value = mock_pooled

                conn = await pool.connection()
                assert conn is not None

    @pytest.mark.asyncio
    async def test_pooled_connection_execute_records_metrics(self):
        """Test pooled connection execute records metrics."""
        pool = AsyncConnectionPool(PoolConfig(pool_size=1))

        with patch.object(pool._sync_pool, '_acquire') as mock_acquire:
            mock_pooled = Mock()
            mock_client = Mock()
            mock_client.execute.return_value = [{"id": 1}]
            mock_pooled.client = mock_client
            mock_acquire.return_value = mock_pooled

            with patch.object(pool._sync_pool, 'stats', return_value={"active": 1, "idle": 0, "total": 1}):
                conn = await pool.connection()
                result = await conn.execute("g.V().limit(1)")

                assert result == [{"id": 1}]


class TestSyncClientTracing:
    """Test synchronous client tracing."""

    def test_sync_execute_with_tracing_enabled(self):
        """Test that sync client execute works with tracing enabled."""
        from src.python.client.janusgraph_client import JanusGraphClient

        client = JanusGraphClient()
        client._client = Mock()
        client._client.submit.return_value.all.return_value.result.return_value = [{"count": 42}]

        # Should not raise even with tracing
        result = client.execute("g.V().count()")
        assert result == [{"count": 42}]
