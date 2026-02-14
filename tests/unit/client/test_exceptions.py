"""
Unit Tests for JanusGraph Client Exceptions
============================================

Test suite for custom exception classes in exceptions.py

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Created: 2026-01-29
Phase: Week 3 - Test Coverage Implementation (Days 1-2)
"""

import pytest

from src.python.client.exceptions import (
    ConnectionError,
    JanusGraphError,
    QueryError,
    TimeoutError,
    ValidationError,
)


class TestJanusGraphError:
    """Test base exception class"""

    def test_base_exception_creation(self):
        """Test creating base exception"""
        error = JanusGraphError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_base_exception_inheritance(self):
        """Test all custom exceptions inherit from base"""
        assert issubclass(ConnectionError, JanusGraphError)
        assert issubclass(QueryError, JanusGraphError)
        assert issubclass(TimeoutError, JanusGraphError)
        assert issubclass(ValidationError, JanusGraphError)

    def test_base_exception_raise(self):
        """Test raising base exception"""
        with pytest.raises(JanusGraphError, match="Test message"):
            raise JanusGraphError("Test message")


class TestConnectionError:
    """Test ConnectionError exception"""

    def test_connection_error_creation(self):
        """Test creating ConnectionError"""
        error = ConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, JanusGraphError)

    def test_connection_error_raise(self):
        """Test raising ConnectionError"""
        with pytest.raises(ConnectionError, match="Failed to connect"):
            raise ConnectionError("Failed to connect")

    def test_connection_error_catch_as_base(self):
        """Test catching ConnectionError as base exception"""
        with pytest.raises(JanusGraphError):
            raise ConnectionError("Connection failed")


class TestQueryError:
    """Test QueryError exception"""

    def test_query_error_creation_with_message(self):
        """Test creating QueryError with message only"""
        error = QueryError("Query failed")
        assert str(error) == "Query failed"
        assert error.query is None
        assert isinstance(error, JanusGraphError)

    def test_query_error_creation_with_query(self):
        """Test creating QueryError with query"""
        query = "g.V().count()"
        error = QueryError("Query failed", query=query)
        assert str(error) == "Query failed"
        assert error.query == query

    def test_query_error_raise_with_query(self):
        """Test raising QueryError with query"""
        query = "g.V().invalid()"
        with pytest.raises(QueryError) as exc_info:
            raise QueryError("Syntax error", query=query)

        assert exc_info.value.query == query
        assert "Syntax error" in str(exc_info.value)

    def test_query_error_query_attribute_access(self):
        """Test accessing query attribute"""
        query = "g.V().has('name', 'Alice')"
        error = QueryError("Query failed", query=query)
        assert error.query == query

    def test_query_error_none_query(self):
        """Test QueryError with None query"""
        error = QueryError("Query failed", query=None)
        assert error.query is None

    def test_query_error_catch_as_base(self):
        """Test catching QueryError as base exception"""
        with pytest.raises(JanusGraphError):
            raise QueryError("Query failed", query="g.V()")


class TestTimeoutError:
    """Test TimeoutError exception"""

    def test_timeout_error_creation(self):
        """Test creating TimeoutError"""
        error = TimeoutError("Operation timed out")
        assert str(error) == "Operation timed out"
        assert isinstance(error, JanusGraphError)

    def test_timeout_error_raise(self):
        """Test raising TimeoutError"""
        with pytest.raises(TimeoutError, match="Connection timed out"):
            raise TimeoutError("Connection timed out")

    def test_timeout_error_catch_as_base(self):
        """Test catching TimeoutError as base exception"""
        with pytest.raises(JanusGraphError):
            raise TimeoutError("Timeout occurred")


class TestValidationError:
    """Test ValidationError exception"""

    def test_validation_error_creation(self):
        """Test creating ValidationError"""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"
        assert isinstance(error, JanusGraphError)

    def test_validation_error_raise(self):
        """Test raising ValidationError"""
        with pytest.raises(ValidationError, match="Invalid port"):
            raise ValidationError("Invalid port")

    def test_validation_error_catch_as_base(self):
        """Test catching ValidationError as base exception"""
        with pytest.raises(JanusGraphError):
            raise ValidationError("Validation failed")


class TestExceptionHierarchy:
    """Test exception hierarchy and catching"""

    def test_catch_all_with_base(self):
        """Test catching all custom exceptions with base class"""
        exceptions = [
            ConnectionError("Connection failed"),
            QueryError("Query failed"),
            TimeoutError("Timeout"),
            ValidationError("Invalid"),
        ]

        for exc in exceptions:
            with pytest.raises(JanusGraphError):
                raise exc

    def test_specific_exception_catching(self):
        """Test catching specific exceptions"""
        # ConnectionError
        with pytest.raises(ConnectionError):
            raise ConnectionError("Connection failed")

        # QueryError
        with pytest.raises(QueryError):
            raise QueryError("Query failed")

        # TimeoutError
        with pytest.raises(TimeoutError):
            raise TimeoutError("Timeout")

        # ValidationError
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid")

    def test_exception_not_caught_by_wrong_type(self):
        """Test exceptions are not caught by wrong exception type"""
        with pytest.raises(ConnectionError):
            try:
                raise ConnectionError("Connection failed")
            except QueryError:
                pytest.fail("Should not catch ConnectionError as QueryError")

    def test_multiple_exception_types_in_try_except(self):
        """Test handling multiple exception types in single try-except"""

        def raise_connection_error():
            raise ConnectionError("Connection failed")

        def raise_query_error():
            raise QueryError("Query failed")

        # Test catching multiple types
        for func in [raise_connection_error, raise_query_error]:
            with pytest.raises((ConnectionError, QueryError)):
                func()

    def test_exception_chaining(self):
        """Test exception chaining with 'from' clause"""
        original_error = ValueError("Original error")

        with pytest.raises(ValidationError) as exc_info:
            try:
                raise original_error
            except ValueError as e:
                raise ValidationError("Validation failed") from e

        assert exc_info.value.__cause__ == original_error
