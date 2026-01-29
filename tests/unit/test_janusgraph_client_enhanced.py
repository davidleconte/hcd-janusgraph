#!/usr/bin/env python3
"""
Enhanced Unit Tests for JanusGraph Client
Comprehensive test coverage for production-ready client

File: tests/unit/test_janusgraph_client_enhanced.py
Created: 2026-01-28
Author: Security Remediation Team
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.python.client.janusgraph_client import JanusGraphClient
from src.python.client.exceptions import (
    ConnectionError,
    QueryError,
    ValidationError,
    TimeoutError
)


class TestJanusGraphClientInitialization:
    """Test client initialization and validation"""

    def test_init_with_default_parameters(self):
        """Test client initialization with default parameters"""
        client = JanusGraphClient()
        assert client.host == "localhost"
        assert client.port == 18182
        assert client.traversal_source == "g"
        assert client.timeout == 30
        assert client.url == "ws://localhost:18182/gremlin"
        assert not client.is_connected()

    def test_init_with_custom_parameters(self):
        """Test client initialization with custom parameters"""
        client = JanusGraphClient(
            host="janusgraph.example.com",
            port=8182,
            traversal_source="graph",
            timeout=60
        )
        assert client.host == "janusgraph.example.com"
        assert client.port == 8182
        assert client.traversal_source == "graph"
        assert client.timeout == 60
        assert client.url == "ws://janusgraph.example.com:8182/gremlin"

    def test_init_with_empty_host(self):
        """Test client initialization with empty host raises ValidationError"""
        with pytest.raises(ValidationError, match="Host cannot be empty"):
            JanusGraphClient(host="")

    def test_init_with_invalid_port_too_low(self):
        """Test client initialization with port < 1 raises ValidationError"""
        with pytest.raises(ValidationError, match="Invalid port"):
            JanusGraphClient(port=0)

    def test_init_with_invalid_port_too_high(self):
        """Test client initialization with port > 65535 raises ValidationError"""
        with pytest.raises(ValidationError, match="Invalid port"):
            JanusGraphClient(port=99999)

    def test_init_with_negative_timeout(self):
        """Test client initialization with negative timeout raises ValidationError"""
        with pytest.raises(ValidationError, match="Invalid timeout"):
            JanusGraphClient(timeout=-1)

    def test_init_with_zero_timeout(self):
        """Test client initialization with zero timeout raises ValidationError"""
        with pytest.raises(ValidationError, match="Invalid timeout"):
            JanusGraphClient(timeout=0)


class TestJanusGraphClientConnection:
    """Test client connection management"""

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_connect_success(self, mock_client_class):
        """Test successful connection"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        jg_client = JanusGraphClient()
        jg_client.connect()

        assert jg_client.is_connected()
        mock_client_class.assert_called_once()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_connect_already_connected(self, mock_client_class):
        """Test connecting when already connected logs warning"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        jg_client = JanusGraphClient()
        jg_client.connect()
        
        # Connect again
        jg_client.connect()
        
        # Should only be called once
        assert mock_client_class.call_count == 1

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_connect_timeout(self, mock_client_class):
        """Test connection timeout raises TimeoutError"""
        mock_client_class.side_effect = TimeoutError("Connection timeout")

        jg_client = JanusGraphClient()
        
        with pytest.raises(TimeoutError, match="Connection to .* timed out"):
            jg_client.connect()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_connect_failure(self, mock_client_class):
        """Test connection failure raises ConnectionError"""
        mock_client_class.side_effect = Exception("Connection refused")

        jg_client = JanusGraphClient()
        
        with pytest.raises(ConnectionError, match="Failed to connect"):
            jg_client.connect()

    def test_is_connected_when_not_connected(self):
        """Test is_connected returns False when not connected"""
        jg_client = JanusGraphClient()
        assert not jg_client.is_connected()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_is_connected_when_connected(self, mock_client_class):
        """Test is_connected returns True when connected"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        jg_client = JanusGraphClient()
        jg_client.connect()
        
        assert jg_client.is_connected()


class TestJanusGraphClientQueryExecution:
    """Test query execution"""

    def test_execute_without_connection(self):
        """Test executing query without connection raises ConnectionError"""
        jg_client = JanusGraphClient()
        
        with pytest.raises(ConnectionError, match="Client not connected"):
            jg_client.execute("g.V().count()")

    def test_execute_with_empty_query(self):
        """Test executing empty query raises ValidationError"""
        jg_client = JanusGraphClient()
        
        with pytest.raises(ValidationError, match="Query cannot be empty"):
            jg_client.execute("")

    def test_execute_with_whitespace_query(self):
        """Test executing whitespace-only query raises ValidationError"""
        jg_client = JanusGraphClient()
        
        with pytest.raises(ValidationError, match="Query cannot be empty"):
            jg_client.execute("   ")

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_execute_success(self, mock_client_class):
        """Test successful query execution"""
        mock_result = Mock()
        mock_result.all().result.return_value = [42]
        
        mock_client_instance = Mock()
        mock_client_instance.submit.return_value = mock_result
        mock_client_class.return_value = mock_client_instance

        jg_client = JanusGraphClient()
        jg_client.connect()
        result = jg_client.execute("g.V().count()")

        assert result == [42]
        mock_client_instance.submit.assert_called_once_with("g.V().count()")

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_execute_with_bindings(self, mock_client_class):
        """Test query execution with parameter bindings"""
        mock_result = Mock()
        mock_result.all().result.return_value = [{"name": "Alice"}]
        
        mock_client_instance = Mock()
        mock_client_instance.submit.return_value = mock_result
        mock_client_class.return_value = mock_client_instance

        jg_client = JanusGraphClient()
        jg_client.connect()
        
        bindings = {"name": "Alice"}
        result = jg_client.execute("g.V().has('name', name)", bindings=bindings)

        assert result == [{"name": "Alice"}]
        mock_client_instance.submit.assert_called_once_with(
            "g.V().has('name', name)",
            bindings
        )

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_execute_gremlin_server_error(self, mock_client_class):
        """Test query execution with Gremlin server error raises QueryError"""
        from gremlin_python.driver.protocol import GremlinServerError
        
        mock_client_instance = Mock()
        mock_client_instance.submit.side_effect = GremlinServerError("Syntax error")
        mock_client_class.return_value = mock_client_instance

        jg_client = JanusGraphClient()
        jg_client.connect()

        with pytest.raises(QueryError, match="Gremlin query error"):
            jg_client.execute("g.V().invalid()")

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_execute_timeout(self, mock_client_class):
        """Test query execution timeout raises TimeoutError"""
        mock_client_instance = Mock()
        mock_client_instance.submit.side_effect = TimeoutError("Query timeout")
        mock_client_class.return_value = mock_client_instance

        jg_client = JanusGraphClient()
        jg_client.connect()

        with pytest.raises(TimeoutError, match="Query execution timed out"):
            jg_client.execute("g.V().count()")

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_execute_unexpected_error(self, mock_client_class):
        """Test query execution with unexpected error raises QueryError"""
        mock_client_instance = Mock()
        mock_client_instance.submit.side_effect = RuntimeError("Unexpected error")
        mock_client_class.return_value = mock_client_instance

        jg_client = JanusGraphClient()
        jg_client.connect()

        with pytest.raises(QueryError, match="Query execution failed"):
            jg_client.execute("g.V().count()")


class TestJanusGraphClientConnectionManagement:
    """Test connection lifecycle management"""

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_close_when_connected(self, mock_client_class):
        """Test closing connection when connected"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        jg_client = JanusGraphClient()
        jg_client.connect()
        jg_client.close()

        mock_client_instance.close.assert_called_once()
        assert not jg_client.is_connected()

    def test_close_when_not_connected(self):
        """Test closing connection when not connected (should not raise)"""
        jg_client = JanusGraphClient()
        jg_client.close()  # Should not raise
        assert not jg_client.is_connected()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_close_multiple_times(self, mock_client_class):
        """Test closing connection multiple times (idempotent)"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        jg_client = JanusGraphClient()
        jg_client.connect()
        jg_client.close()
        jg_client.close()  # Should not raise

        # Close should only be called once
        mock_client_instance.close.assert_called_once()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_close_with_error(self, mock_client_class):
        """Test closing connection when close() raises error"""
        mock_client_instance = Mock()
        mock_client_instance.close.side_effect = Exception("Close error")
        mock_client_class.return_value = mock_client_instance

        jg_client = JanusGraphClient()
        jg_client.connect()

        with pytest.raises(Exception, match="Close error"):
            jg_client.close()
        
        # Client should still be marked as closed
        assert not jg_client.is_connected()


class TestJanusGraphClientContextManager:
    """Test context manager functionality"""

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_context_manager_success(self, mock_client_class):
        """Test using client as context manager"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        with JanusGraphClient() as client:
            assert client.is_connected()
        
        # Connection should be closed after exiting context
        mock_client_instance.close.assert_called_once()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_context_manager_with_exception(self, mock_client_class):
        """Test context manager closes connection even when exception occurs"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        with pytest.raises(RuntimeError):
            with JanusGraphClient() as client:
                assert client.is_connected()
                raise RuntimeError("Test error")
        
        # Connection should still be closed
        mock_client_instance.close.assert_called_once()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_context_manager_query_execution(self, mock_client_class):
        """Test executing queries within context manager"""
        mock_result = Mock()
        mock_result.all().result.return_value = [10]
        
        mock_client_instance = Mock()
        mock_client_instance.submit.return_value = mock_result
        mock_client_class.return_value = mock_client_instance

        with JanusGraphClient() as client:
            result = client.execute("g.V().count()")
            assert result == [10]


class TestJanusGraphClientRepresentation:
    """Test string representation"""

    def test_repr_when_not_connected(self):
        """Test __repr__ when not connected"""
        jg_client = JanusGraphClient(host="test.example.com", port=8182)
        repr_str = repr(jg_client)
        
        assert "JanusGraphClient" in repr_str
        assert "ws://test.example.com:8182/gremlin" in repr_str
        assert "disconnected" in repr_str

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_repr_when_connected(self, mock_client_class):
        """Test __repr__ when connected"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        jg_client = JanusGraphClient(host="test.example.com", port=8182)
        jg_client.connect()
        repr_str = repr(jg_client)
        
        assert "JanusGraphClient" in repr_str
        assert "ws://test.example.com:8182/gremlin" in repr_str
        assert "connected" in repr_str


# Integration-style tests (mocked but more realistic scenarios)
class TestJanusGraphClientIntegration:
    """Integration-style tests with realistic scenarios"""

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_full_workflow(self, mock_client_class):
        """Test complete workflow: connect, query, close"""
        mock_result = Mock()
        mock_result.all().result.return_value = [5]
        
        mock_client_instance = Mock()
        mock_client_instance.submit.return_value = mock_result
        mock_client_class.return_value = mock_client_instance

        # Create client
        client = JanusGraphClient(host="localhost", port=8182)
        assert not client.is_connected()

        # Connect
        client.connect()
        assert client.is_connected()

        # Execute query
        result = client.execute("g.V().hasLabel('person').count()")
        assert result == [5]

        # Close
        client.close()
        assert not client.is_connected()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_multiple_queries(self, mock_client_class):
        """Test executing multiple queries in sequence"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        # Setup different results for different queries
        mock_result1 = Mock()
        mock_result1.all().result.return_value = [10]
        mock_result2 = Mock()
        mock_result2.all().result.return_value = [20]
        mock_result3 = Mock()
        mock_result3.all().result.return_value = [{"name": "Alice"}]

        mock_client_instance.submit.side_effect = [mock_result1, mock_result2, mock_result3]

        with JanusGraphClient() as client:
            result1 = client.execute("g.V().count()")
            result2 = client.execute("g.E().count()")
            result3 = client.execute("g.V().has('name', 'Alice').valueMap()")

            assert result1 == [10]
            assert result2 == [20]
            assert result3 == [{"name": "Alice"}]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.python.client", "--cov-report=term-missing"])

