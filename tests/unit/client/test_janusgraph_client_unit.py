"""
Unit Tests for JanusGraph Client
=================================

Comprehensive test suite for janusgraph_client.py covering:
- Initialization and validation
- Connection management
- Query execution
- Error handling
- SSL/TLS configuration
- Context manager usage

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-29
Phase: Week 3 - Test Coverage Implementation (Days 1-2)
"""

import pytest
import logging
import ssl
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

from src.python.client.janusgraph_client import JanusGraphClient
from src.python.client.exceptions import (
    ConnectionError,
    QueryError,
    TimeoutError,
    ValidationError as ClientValidationError,
)
from src.python.utils.validation import ValidationError as UtilsValidationError


class TestJanusGraphClientInitialization:
    """Test client initialization and parameter validation"""

    def test_init_with_defaults(self, monkeypatch):
        """Test initialization with default parameters"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'test_user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'test_password')
        
        client = JanusGraphClient()
        
        assert client.host == 'localhost'
        assert client.port == 18182  # Project default is 18182 (podman mapped port)
        assert client.username == 'test_user'
        assert client.password == 'test_password'
        assert client.traversal_source == 'g'
        assert client.timeout == 30
        assert client.use_ssl is True
        assert client.verify_certs is True
        assert client.url == 'wss://localhost:18182/gremlin'

    def test_init_with_custom_parameters(self, monkeypatch):
        """Test initialization with custom parameters"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'env_user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'env_pass')
        
        client = JanusGraphClient(
            host='example.com',
            port=9999,
            username='custom_user',
            password='custom_pass',
            traversal_source='custom_g',
            timeout=60,
            use_ssl=False,
            verify_certs=False
        )
        
        assert client.host == 'example.com'
        assert client.port == 9999
        assert client.username == 'custom_user'
        assert client.password == 'custom_pass'
        assert client.traversal_source == 'custom_g'
        assert client.timeout == 60
        assert client.use_ssl is False
        assert client.url == 'ws://example.com:9999/gremlin'

    def test_init_ssl_url_format(self, monkeypatch):
        """Test URL format with SSL enabled"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        client = JanusGraphClient(host='secure.example.com', use_ssl=True)
        assert client.url == 'wss://secure.example.com:18182/gremlin'

    def test_init_no_ssl_url_format(self, monkeypatch):
        """Test URL format with SSL disabled"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        client = JanusGraphClient(host='insecure.example.com', use_ssl=False, verify_certs=False)
        assert client.url == 'ws://insecure.example.com:18182/gremlin'
    def test_init_missing_credentials(self, monkeypatch):
        """Test initialization fails without credentials"""
        monkeypatch.delenv('JANUSGRAPH_USERNAME', raising=False)
        monkeypatch.delenv('JANUSGRAPH_PASSWORD', raising=False)
        
        with pytest.raises(ClientValidationError, match="authentication required"):
            JanusGraphClient()

    def test_init_invalid_hostname(self, monkeypatch):
        """Test initialization with invalid hostname"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        with pytest.raises(UtilsValidationError):
            JanusGraphClient(host='')
            JanusGraphClient(port=-1)

    def test_init_invalid_port_too_high(self, monkeypatch):
        """Test initialization with port > 65535"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        with pytest.raises(UtilsValidationError, match="Port must be between"):
            JanusGraphClient(port=70000)

    def test_init_invalid_timeout_negative(self, monkeypatch):
        """Test initialization with negative timeout"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        with pytest.raises(ClientValidationError, match="Timeout must be positive"):
            JanusGraphClient(timeout=-5)

    def test_init_invalid_timeout_zero(self, monkeypatch):
        """Test initialization with zero timeout"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        with pytest.raises(ClientValidationError, match="Timeout must be positive"):
            JanusGraphClient(timeout=0)

    def test_init_invalid_timeout_type(self, monkeypatch):
        """Test initialization with non-numeric timeout"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        with pytest.raises(ClientValidationError, match="Timeout must be numeric"):
            JanusGraphClient(timeout="invalid")

    def test_init_high_timeout_warning(self, monkeypatch, caplog):
        """Test warning for very high timeout values"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        client = JanusGraphClient(timeout=500)
        assert "Timeout 500 seconds is very high" in caplog.text

    def test_init_invalid_ca_certs_file(self, monkeypatch):
        """Test initialization with non-existent CA certs file"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        with pytest.raises(UtilsValidationError, match="File does not exist"):
            JanusGraphClient(ca_certs='/nonexistent/ca.pem')
    def test_init_ssl_config_invalid(self, monkeypatch):
        """Test initialization with invalid SSL configuration"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        with pytest.raises(UtilsValidationError, match="File does not exist"):
            JanusGraphClient(ca_certs='/nonexistent/ca.pem')
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'env_username')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'env_password')
        
        client = JanusGraphClient()
        assert client.username == 'env_username'
        assert client.password == 'env_password'

    def test_init_credentials_override_env(self, monkeypatch):
        """Test explicit credentials override environment variables"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'env_username')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'env_password')
        
        client = JanusGraphClient(username='explicit_user', password='explicit_pass')
        assert client.username == 'explicit_user'
        assert client.password == 'explicit_pass'


class TestJanusGraphClientConnection:
    """Test connection management"""

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_connect_success(self, mock_client_class, monkeypatch):
        """Test successful connection"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        jg_client = JanusGraphClient()
        jg_client.connect()
        
        assert jg_client.is_connected()
        mock_client_class.assert_called_once()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_connect_already_connected(self, mock_client_class, monkeypatch, caplog):
        """Test connecting when already connected"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        jg_client = JanusGraphClient()
        jg_client.connect()
        jg_client.connect()  # Second connect
        
        assert "Client already connected" in caplog.text
        assert mock_client_class.call_count == 1  # Only called once

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_connect_failure(self, mock_client_class, monkeypatch):
        """Test connection failure"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_client_class.side_effect = Exception("Connection refused")
        
        jg_client = JanusGraphClient()
        with pytest.raises(ConnectionError, match="Failed to connect"):
            jg_client.connect()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_connect_timeout(self, mock_client_class, monkeypatch):
        """Test connection timeout"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_client_class.side_effect = TimeoutError("Connection timed out")
        
        jg_client = JanusGraphClient()
        with pytest.raises(TimeoutError, match="timed out"):
            jg_client.connect()

    @patch('src.python.client.janusgraph_client.client.Client')
    @patch('src.python.client.janusgraph_client.ssl.create_default_context')
    def test_connect_with_ssl(self, mock_ssl_context, mock_client_class, monkeypatch):
        """Test connection with SSL enabled"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_context = Mock()
        mock_ssl_context.return_value = mock_context
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        jg_client = JanusGraphClient(use_ssl=True)
        jg_client.connect()
        
        mock_ssl_context.assert_called_once()
        assert jg_client.is_connected()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_connect_without_ssl(self, mock_client_class, monkeypatch):
        """Test connection without SSL"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        jg_client = JanusGraphClient(use_ssl=False, verify_certs=False)
        jg_client.connect()
        
        assert jg_client.url.startswith('ws://')
        assert jg_client.is_connected()

    def test_is_connected_false_initially(self, monkeypatch):
        """Test is_connected returns False before connection"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
    def test_close_connection(self, mock_client_class, monkeypatch, caplog):
        assert not jg_client.is_connected()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_close_connection(self, mock_client_class, monkeypatch, caplog):
        """Test closing connection"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        jg_client = JanusGraphClient()
        jg_client.connect()
        jg_client.close()
        
        mock_client_instance.close.assert_called_once()
        assert not jg_client.is_connected()

    def test_close_not_connected(self, monkeypatch, caplog):
        """Test closing when not connected"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        caplog.set_level(logging.DEBUG)
        jg_client = JanusGraphClient()
        jg_client.close()
        
        assert "already closed or never connected" in caplog.text
        
        assert "already closed or never connected" in caplog.text

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_close_error_handling(self, mock_client_class, monkeypatch):
        """Test error handling during close"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_client_instance = Mock()
        mock_client_instance.close.side_effect = Exception("Close failed")
        mock_client_class.return_value = mock_client_instance
        
        jg_client = JanusGraphClient()
        jg_client.connect()
        
        with pytest.raises(Exception, match="Close failed"):
            jg_client.close()
        
        # Client should still be set to None even on error
        assert not jg_client.is_connected()


class TestJanusGraphClientQueryExecution:
    """Test query execution"""

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_execute_simple_query(self, mock_client_class, monkeypatch):
        """Test executing a simple query"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [42]
        mock_client_instance = Mock()
        mock_client_instance.submit.return_value = mock_result
        mock_client_class.return_value = mock_client_instance
        
        jg_client = JanusGraphClient()
        jg_client.connect()
        result = jg_client.execute("g.V().count()")
        
        assert result == [42]
        mock_client_instance.submit.assert_called_once_with("g.V().count()")

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_execute_query_with_bindings(self, mock_client_class, monkeypatch):
        """Test executing query with parameter bindings"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [{'name': 'Alice'}]
        mock_client_instance = Mock()
        mock_client_instance.submit.return_value = mock_result
        mock_client_class.return_value = mock_client_instance
        
        jg_client = JanusGraphClient()
        jg_client.connect()
        bindings = {'name': 'Alice'}
        result = jg_client.execute("g.V().has('name', name)", bindings=bindings)
        
        assert result == [{'name': 'Alice'}]
        mock_client_instance.submit.assert_called_once_with(
            "g.V().has('name', name)",
            bindings
        )

    def test_execute_not_connected(self, monkeypatch):
        """Test executing query without connection"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        jg_client = JanusGraphClient()
        
        with pytest.raises(ConnectionError, match="Client not connected"):
            jg_client.execute("g.V().count()")
    @patch('src.python.client.janusgraph_client.client.Client')
    def test_execute_invalid_query(self, mock_client_class, monkeypatch):
        """Test executing invalid query"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        jg_client = JanusGraphClient()
        jg_client.connect()
        
        with pytest.raises(UtilsValidationError):
            jg_client.execute("")  # Empty query
    @patch('src.python.client.janusgraph_client.client.Client')
    def test_execute_query_error(self, mock_client_class, monkeypatch):
        """Test query execution error"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        from gremlin_python.driver.protocol import GremlinServerError
        
        mock_client_instance = Mock()
        mock_client_instance.submit.side_effect = GremlinServerError({'code': 500, 'message': 'Syntax error', 'attributes': {}})
        mock_client_class.return_value = mock_client_instance
        
        jg_client = JanusGraphClient()
        jg_client.connect()
        
        with pytest.raises(QueryError, match="Gremlin query error"):
            jg_client.execute("g.V().invalid()")
        mock_client_instance.submit.side_effect = TimeoutError("Query timed out")
        mock_client_class.return_value = mock_client_instance
        
        jg_client = JanusGraphClient()
        jg_client.connect()
        
        with pytest.raises(TimeoutError, match="Query execution timed out"):
            jg_client.execute("g.V().count()")

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_execute_unexpected_error(self, mock_client_class, monkeypatch):
        """Test unexpected error during query execution"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_client_instance = Mock()
        mock_client_instance.submit.side_effect = RuntimeError("Unexpected error")
        mock_client_class.return_value = mock_client_instance
        
        jg_client = JanusGraphClient()
        jg_client.connect()
        
        with pytest.raises(QueryError, match="Query execution failed"):
            jg_client.execute("g.V().count()")


class TestJanusGraphClientContextManager:
    """Test context manager functionality"""

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_context_manager_success(self, mock_client_class, monkeypatch):
        """Test using client as context manager"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_result = Mock()
        mock_result.all.return_value.result.return_value = [10]
        mock_client_instance = Mock()
        mock_client_instance.submit.return_value = mock_result
        mock_client_class.return_value = mock_client_instance
        
        with JanusGraphClient() as client:
            assert client.is_connected()
            result = client.execute("g.V().count()")
            assert result == [10]
        
        # Connection should be closed after context
        assert not client.is_connected()
        mock_client_instance.close.assert_called_once()

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_context_manager_with_exception(self, mock_client_class, monkeypatch):
        """Test context manager closes connection even on exception"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        try:
            with JanusGraphClient() as client:
                assert client.is_connected()
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Connection should still be closed
        mock_client_instance.close.assert_called_once()


class TestJanusGraphClientRepresentation:
    """Test string representation"""

    def test_repr_disconnected(self, monkeypatch):
        """Test __repr__ when disconnected"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        client = JanusGraphClient()
        repr_str = repr(client)
        
        assert 'JanusGraphClient' in repr_str
        assert 'wss://localhost:18182/gremlin' in repr_str
        assert 'ssl=True' in repr_str
        assert 'disconnected' in repr_str

    @patch('src.python.client.janusgraph_client.client.Client')
    def test_repr_connected(self, mock_client_class, monkeypatch):
        """Test __repr__ when connected"""
        monkeypatch.setenv('JANUSGRAPH_USERNAME', 'user')
        monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'pass')
        
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        client = JanusGraphClient()
        client.connect()
        repr_str = repr(client)
        
        assert 'JanusGraphClient' in repr_str
        assert 'connected' in repr_str


