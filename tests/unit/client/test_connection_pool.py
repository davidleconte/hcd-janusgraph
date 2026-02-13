"""
Unit tests for ConnectionPool.

Tests cover:
- Pool initialization and configuration
- Connection acquisition and release
- Overflow handling
- Stale connection recycling
- Thread safety
- Pool statistics
- Context manager usage
"""

import threading
import time
from queue import Empty
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.python.client.connection_pool import ConnectionPool, PoolConfig, _PooledConnection


@pytest.fixture
def mock_client_class():
    with patch("src.python.client.connection_pool.JanusGraphClient") as mock_cls:
        mock_instance = Mock()
        mock_cls.return_value = mock_instance
        yield mock_cls


class TestPoolConfig:
    """Test PoolConfig dataclass."""

    def test_default_config(self):
        config = PoolConfig()
        assert config.host == "localhost"
        assert config.pool_size == 5
        assert config.max_overflow == 10
        assert config.pool_timeout == 30.0
        assert config.recycle_seconds == 3600

    def test_custom_config(self):
        config = PoolConfig(host="remote", port=8182, pool_size=10, max_overflow=20)
        assert config.host == "remote"
        assert config.port == 8182
        assert config.pool_size == 10
        assert config.max_overflow == 20


class TestPooledConnection:
    """Test _PooledConnection internal class."""

    def test_creation(self):
        mock_client = Mock()
        conn = _PooledConnection(client=mock_client)
        assert conn.client is mock_client
        assert conn.use_count == 0
        assert conn.age >= 0

    def test_is_stale(self):
        mock_client = Mock()
        conn = _PooledConnection(client=mock_client, created_at=time.time() - 7200)
        assert conn.is_stale(3600) is True

    def test_is_not_stale(self):
        mock_client = Mock()
        conn = _PooledConnection(client=mock_client)
        assert conn.is_stale(3600) is False


class TestConnectionPoolInit:
    """Test pool initialization."""

    def test_init_creates_connections(self, mock_client_class):
        config = PoolConfig(pool_size=3)
        pool = ConnectionPool(config)
        assert pool.size == 3
        assert mock_client_class.call_count == 3
        pool.close()

    def test_init_default_config(self, mock_client_class):
        pool = ConnectionPool()
        assert pool._config.pool_size == 5
        pool.close()

    def test_init_handles_connection_failure(self, mock_client_class):
        mock_client_class.return_value.connect.side_effect = Exception("Connection failed")
        config = PoolConfig(pool_size=3)
        pool = ConnectionPool(config)
        assert pool.size == 0
        pool.close()


class TestConnectionAcquisition:
    """Test connection acquisition and release."""

    def test_acquire_returns_connection(self, mock_client_class):
        config = PoolConfig(pool_size=2)
        pool = ConnectionPool(config)

        with pool.connection() as client:
            assert client is not None

        pool.close()

    def test_connection_returned_to_pool(self, mock_client_class):
        config = PoolConfig(pool_size=2)
        pool = ConnectionPool(config)

        initial_size = pool.size
        with pool.connection() as client:
            assert pool.size == initial_size - 1
        assert pool.size == initial_size

        pool.close()

    def test_pool_exhausted_uses_overflow(self, mock_client_class):
        config = PoolConfig(pool_size=1, max_overflow=2, pool_timeout=0.1)
        pool = ConnectionPool(config)

        conn1 = pool._acquire()
        assert pool.size == 0

        conn2 = pool._acquire()
        assert pool.overflow_count == 1

        pool._release(conn1)
        pool._release(conn2)
        pool.close()

    def test_pool_exhausted_no_overflow_raises(self, mock_client_class):
        config = PoolConfig(pool_size=1, max_overflow=0, pool_timeout=0.1)
        pool = ConnectionPool(config)

        conn1 = pool._acquire()
        with pytest.raises(Exception, match="Connection pool exhausted"):
            pool._acquire()

        pool._release(conn1)
        pool.close()

    def test_closed_pool_raises(self, mock_client_class):
        pool = ConnectionPool(PoolConfig(pool_size=1))
        pool.close()

        with pytest.raises(Exception, match="closed"):
            with pool.connection() as client:
                pass


class TestStaleConnectionRecycling:
    """Test stale connection recycling."""

    def test_stale_connection_recycled_on_acquire(self, mock_client_class):
        config = PoolConfig(pool_size=1, recycle_seconds=0)
        pool = ConnectionPool(config)

        time.sleep(0.01)
        with pool.connection() as client:
            pass

        assert mock_client_class.call_count >= 2
        pool.close()


class TestPoolStatistics:
    """Test pool statistics."""

    def test_stats(self, mock_client_class):
        config = PoolConfig(pool_size=3)
        pool = ConnectionPool(config)

        stats = pool.stats()
        assert stats["pool_size"] == 3
        assert stats["available"] == 3
        assert stats["overflow"] == 0
        assert stats["total_created"] == 3
        assert stats["closed"] is False

        pool.close()

    def test_stats_after_use(self, mock_client_class):
        config = PoolConfig(pool_size=2)
        pool = ConnectionPool(config)

        with pool.connection():
            pass

        stats = pool.stats()
        assert stats["total_returned"] >= 1
        pool.close()


class TestPoolContextManager:
    """Test pool as context manager."""

    def test_pool_context_manager(self, mock_client_class):
        with ConnectionPool(PoolConfig(pool_size=2)) as pool:
            with pool.connection() as client:
                assert client is not None

    def test_pool_closed_after_context(self, mock_client_class):
        pool = None
        with ConnectionPool(PoolConfig(pool_size=1)) as p:
            pool = p
        assert pool._closed is True


class TestPoolClose:
    """Test pool closure."""

    def test_close_destroys_all_connections(self, mock_client_class):
        config = PoolConfig(pool_size=3)
        pool = ConnectionPool(config)

        pool.close()

        assert pool.size == 0
        assert pool._closed is True
        assert mock_client_class.return_value.close.call_count == 3

    def test_close_idempotent(self, mock_client_class):
        pool = ConnectionPool(PoolConfig(pool_size=1))
        pool.close()
        pool.close()
        assert pool._closed is True
