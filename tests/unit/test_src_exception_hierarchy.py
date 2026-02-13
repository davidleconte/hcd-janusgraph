"""
Unit Tests for Custom Exception Hierarchy

Tests cover:
- Base exception functionality
- Exception serialization
- Exception chaining
- Utility functions
- All exception types

Created: 2026-02-11
Week 3 Day 15: Core Exception Refactoring
"""

from datetime import datetime

import pytest

from src.python.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConfigurationLoadError,
    ConnectionError,
    ConnectionFailedError,
    ConnectionLostError,
    ConnectionPoolExhaustedError,
    ConnectionTimeoutError,
    DataError,
    DataIntegrityError,
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidConfigurationError,
    JanusGraphBaseException,
    MissingConfigurationError,
    QueryError,
    QueryExecutionError,
    QueryResultError,
    QueryTimeoutError,
    QueryValidationError,
    RateLimitExceededError,
    ResourceError,
    ResourceExhaustedError,
    SecurityError,
    SerializationError,
    TokenExpiredError,
    ValidationError,
    get_error_category,
    is_retryable_error,
)


# ============================================================================
# Base Exception Tests
# ============================================================================


class TestJanusGraphBaseException:
    """Tests for JanusGraphBaseException base class."""

    def test_create_basic_exception(self):
        """Test creating exception with just message."""
        exc = JanusGraphBaseException("Test error")

        assert exc.message == "Test error"
        assert exc.error_code == "JanusGraphBaseException"
        assert exc.details == {}
        assert exc.cause is None
        assert isinstance(exc.timestamp, datetime)

    def test_create_exception_with_error_code(self):
        """Test creating exception with custom error code."""
        exc = JanusGraphBaseException("Test error", error_code="TEST_001")

        assert exc.error_code == "TEST_001"

    def test_create_exception_with_details(self):
        """Test creating exception with details."""
        details = {"field": "entity_id", "value": "123"}
        exc = JanusGraphBaseException("Test error", details=details)

        assert exc.details == details

    def test_create_exception_with_cause(self):
        """Test creating exception with cause."""
        cause = ValueError("Original error")
        exc = JanusGraphBaseException("Test error", cause=cause)

        assert exc.cause == cause

    def test_exception_to_dict(self):
        """Test converting exception to dictionary."""
        exc = JanusGraphBaseException(
            "Test error", error_code="TEST_001", details={"key": "value"}
        )

        result = exc.to_dict()

        assert result["error_code"] == "TEST_001"
        assert result["message"] == "Test error"
        assert "timestamp" in result
        assert result["details"] == {"key": "value"}

    def test_exception_to_dict_with_cause(self):
        """Test converting exception with cause to dictionary."""
        cause = ValueError("Original error")
        exc = JanusGraphBaseException("Test error", cause=cause)

        result = exc.to_dict()

        assert "cause" in result
        assert "Original error" in result["cause"]

    def test_exception_str_representation(self):
        """Test string representation of exception."""
        exc = JanusGraphBaseException("Test error", error_code="TEST_001")

        assert "TEST_001" in str(exc)
        assert "Test error" in str(exc)

    def test_exception_str_with_details(self):
        """Test string representation with details."""
        exc = JanusGraphBaseException(
            "Test error", error_code="TEST_001", details={"key": "value"}
        )

        result = str(exc)

        assert "TEST_001" in result
        assert "Test error" in result
        assert "details" in result


# ============================================================================
# Connection Error Tests
# ============================================================================


class TestConnectionErrors:
    """Tests for connection-related exceptions."""

    def test_connection_failed_error(self):
        """Test ConnectionFailedError."""
        exc = ConnectionFailedError(
            "Failed to connect", details={"host": "localhost", "port": 8182}
        )

        assert isinstance(exc, ConnectionError)
        assert isinstance(exc, JanusGraphBaseException)
        assert exc.message == "Failed to connect"
        assert exc.details["host"] == "localhost"

    def test_connection_lost_error(self):
        """Test ConnectionLostError."""
        exc = ConnectionLostError("Connection lost", details={"duration": "5m"})

        assert isinstance(exc, ConnectionError)
        assert exc.message == "Connection lost"

    def test_connection_timeout_error(self):
        """Test ConnectionTimeoutError."""
        exc = ConnectionTimeoutError("Timeout", details={"timeout_seconds": 30})

        assert isinstance(exc, ConnectionError)
        assert exc.details["timeout_seconds"] == 30

    def test_connection_pool_exhausted_error(self):
        """Test ConnectionPoolExhaustedError."""
        exc = ConnectionPoolExhaustedError(
            "Pool exhausted", details={"pool_size": 10, "active": 10}
        )

        assert isinstance(exc, ConnectionError)
        assert exc.details["pool_size"] == 10


# ============================================================================
# Query Error Tests
# ============================================================================


class TestQueryErrors:
    """Tests for query-related exceptions."""

    def test_query_validation_error(self):
        """Test QueryValidationError."""
        exc = QueryValidationError(
            "Invalid syntax", details={"query": "g.V().invalid()", "line": 1}
        )

        assert isinstance(exc, QueryError)
        assert isinstance(exc, JanusGraphBaseException)
        assert "Invalid syntax" in exc.message

    def test_query_execution_error(self):
        """Test QueryExecutionError."""
        exc = QueryExecutionError("Execution failed", details={"query": "g.V().count()"})

        assert isinstance(exc, QueryError)
        assert exc.details["query"] == "g.V().count()"

    def test_query_timeout_error(self):
        """Test QueryTimeoutError."""
        exc = QueryTimeoutError("Query timeout", details={"timeout_seconds": 30})

        assert isinstance(exc, QueryError)
        assert exc.details["timeout_seconds"] == 30

    def test_query_result_error(self):
        """Test QueryResultError."""
        exc = QueryResultError(
            "Failed to deserialize", details={"result_type": "vertex"}
        )

        assert isinstance(exc, QueryError)
        assert exc.details["result_type"] == "vertex"


# ============================================================================
# Data Error Tests
# ============================================================================


class TestDataErrors:
    """Tests for data-related exceptions."""

    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError(
            "Invalid entity_id",
            details={"field": "entity_id", "value": "", "constraint": "non-empty"},
        )

        assert isinstance(exc, DataError)
        assert isinstance(exc, JanusGraphBaseException)
        assert exc.details["field"] == "entity_id"

    def test_entity_not_found_error(self):
        """Test EntityNotFoundError."""
        exc = EntityNotFoundError(
            "Person not found", details={"entity_type": "person", "entity_id": "p-123"}
        )

        assert isinstance(exc, DataError)
        assert exc.details["entity_id"] == "p-123"

    def test_duplicate_entity_error(self):
        """Test DuplicateEntityError."""
        exc = DuplicateEntityError(
            "Person already exists",
            details={"entity_type": "person", "entity_id": "p-123"},
        )

        assert isinstance(exc, DataError)
        assert "already exists" in exc.message

    def test_data_integrity_error(self):
        """Test DataIntegrityError."""
        exc = DataIntegrityError(
            "Constraint violated", details={"entity": "account", "constraint": "owner_id"}
        )

        assert isinstance(exc, DataError)
        assert exc.details["constraint"] == "owner_id"

    def test_serialization_error(self):
        """Test SerializationError."""
        exc = SerializationError(
            "Serialization failed", details={"entity_type": "person", "format": "JSON"}
        )

        assert isinstance(exc, DataError)
        assert exc.details["format"] == "JSON"


# ============================================================================
# Configuration Error Tests
# ============================================================================


class TestConfigurationErrors:
    """Tests for configuration-related exceptions."""

    def test_invalid_configuration_error(self):
        """Test InvalidConfigurationError."""
        exc = InvalidConfigurationError(
            "Invalid port", details={"setting": "janusgraph.port", "value": -1}
        )

        assert isinstance(exc, ConfigurationError)
        assert isinstance(exc, JanusGraphBaseException)
        assert exc.details["value"] == -1

    def test_missing_configuration_error(self):
        """Test MissingConfigurationError."""
        exc = MissingConfigurationError(
            "Missing setting", details={"setting": "janusgraph.host"}
        )

        assert isinstance(exc, ConfigurationError)
        assert exc.details["setting"] == "janusgraph.host"

    def test_configuration_load_error(self):
        """Test ConfigurationLoadError."""
        exc = ConfigurationLoadError(
            "Failed to load config", details={"file": "config.yml", "error": "not found"}
        )

        assert isinstance(exc, ConfigurationError)
        assert exc.details["file"] == "config.yml"


# ============================================================================
# Security Error Tests
# ============================================================================


class TestSecurityErrors:
    """Tests for security-related exceptions."""

    def test_authentication_error(self):
        """Test AuthenticationError."""
        exc = AuthenticationError(
            "Invalid credentials", details={"username": "user@example.com"}
        )

        assert isinstance(exc, SecurityError)
        assert isinstance(exc, JanusGraphBaseException)
        assert exc.details["username"] == "user@example.com"

    def test_authorization_error(self):
        """Test AuthorizationError."""
        exc = AuthorizationError(
            "Insufficient permissions",
            details={"user": "user@example.com", "required_role": "admin"},
        )

        assert isinstance(exc, SecurityError)
        assert exc.details["required_role"] == "admin"

    def test_token_expired_error(self):
        """Test TokenExpiredError."""
        exc = TokenExpiredError(
            "Token expired",
            details={"token_type": "JWT", "expired_at": "2026-02-11T12:00:00Z"},
        )

        assert isinstance(exc, SecurityError)
        assert exc.details["token_type"] == "JWT"


# ============================================================================
# Resource Error Tests
# ============================================================================


class TestResourceErrors:
    """Tests for resource-related exceptions."""

    def test_resource_exhausted_error(self):
        """Test ResourceExhaustedError."""
        exc = ResourceExhaustedError(
            "Memory limit exceeded",
            details={"resource": "memory", "limit": "8GB", "used": "8.2GB"},
        )

        assert isinstance(exc, ResourceError)
        assert isinstance(exc, JanusGraphBaseException)
        assert exc.details["resource"] == "memory"

    def test_rate_limit_exceeded_error(self):
        """Test RateLimitExceededError."""
        exc = RateLimitExceededError(
            "Rate limit exceeded", details={"limit": 100, "window": "1m", "retry_after": 30}
        )

        assert isinstance(exc, ResourceError)
        assert exc.details["limit"] == 100


# ============================================================================
# Exception Chaining Tests
# ============================================================================


class TestExceptionChaining:
    """Tests for exception chaining functionality."""

    def test_chain_with_from_keyword(self):
        """Test exception chaining with 'from' keyword."""
        original = ValueError("Original error")

        try:
            try:
                raise original
            except ValueError as e:
                raise QueryExecutionError("Query failed") from e
        except QueryExecutionError as exc:
            assert exc.__cause__ == original
            assert "Original error" in str(exc.__cause__)

    def test_chain_with_cause_parameter(self):
        """Test exception chaining with cause parameter."""
        original = ValueError("Original error")
        exc = QueryExecutionError("Query failed", cause=original)

        assert exc.cause == original
        result = exc.to_dict()
        assert "cause" in result

    def test_nested_exception_chain(self):
        """Test nested exception chaining."""
        error1 = ValueError("Level 1")
        error2 = QueryExecutionError("Level 2", cause=error1)
        error3 = ConnectionLostError("Level 3", cause=error2)

        assert error3.cause == error2
        assert error2.cause == error1


# ============================================================================
# Utility Function Tests
# ============================================================================


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_is_retryable_error_for_retryable_errors(self):
        """Test is_retryable_error returns True for retryable errors."""
        retryable_errors = [
            ConnectionFailedError("Failed"),
            ConnectionTimeoutError("Timeout"),
            ConnectionLostError("Lost"),
            QueryTimeoutError("Timeout"),
            TokenExpiredError("Expired"),
            RateLimitExceededError("Rate limit"),
        ]

        for error in retryable_errors:
            assert is_retryable_error(error), f"{type(error).__name__} should be retryable"

    def test_is_retryable_error_for_non_retryable_errors(self):
        """Test is_retryable_error returns False for non-retryable errors."""
        non_retryable_errors = [
            QueryValidationError("Invalid"),
            ValidationError("Invalid"),
            EntityNotFoundError("Not found"),
            AuthenticationError("Auth failed"),
            InvalidConfigurationError("Invalid config"),
        ]

        for error in non_retryable_errors:
            assert not is_retryable_error(
                error
            ), f"{type(error).__name__} should not be retryable"

    def test_get_error_category_connection(self):
        """Test get_error_category for connection errors."""
        errors = [
            ConnectionFailedError("Failed"),
            ConnectionTimeoutError("Timeout"),
            ConnectionLostError("Lost"),
        ]

        for error in errors:
            assert get_error_category(error) == "connection"

    def test_get_error_category_query(self):
        """Test get_error_category for query errors."""
        errors = [
            QueryValidationError("Invalid"),
            QueryExecutionError("Failed"),
            QueryTimeoutError("Timeout"),
        ]

        for error in errors:
            assert get_error_category(error) == "query"

    def test_get_error_category_data(self):
        """Test get_error_category for data errors."""
        errors = [
            ValidationError("Invalid"),
            EntityNotFoundError("Not found"),
            DuplicateEntityError("Duplicate"),
        ]

        for error in errors:
            assert get_error_category(error) == "data"

    def test_get_error_category_configuration(self):
        """Test get_error_category for configuration errors."""
        errors = [
            InvalidConfigurationError("Invalid"),
            MissingConfigurationError("Missing"),
            ConfigurationLoadError("Load failed"),
        ]

        for error in errors:
            assert get_error_category(error) == "configuration"

    def test_get_error_category_security(self):
        """Test get_error_category for security errors."""
        errors = [
            AuthenticationError("Auth failed"),
            AuthorizationError("Not authorized"),
            TokenExpiredError("Expired"),
        ]

        for error in errors:
            assert get_error_category(error) == "security"

    def test_get_error_category_resource(self):
        """Test get_error_category for resource errors."""
        errors = [
            ResourceExhaustedError("Exhausted"),
            RateLimitExceededError("Rate limit"),
        ]

        for error in errors:
            assert get_error_category(error) == "resource"

    def test_get_error_category_unknown(self):
        """Test get_error_category for unknown errors."""
        error = ValueError("Standard error")

        assert get_error_category(error) == "unknown"


# ============================================================================
# Integration Tests
# ============================================================================


class TestExceptionIntegration:
    """Integration tests for exception usage patterns."""

    def test_typical_error_handling_pattern(self):
        """Test typical error handling pattern."""

        def risky_operation():
            raise ValueError("Something went wrong")

        with pytest.raises(QueryExecutionError) as exc_info:
            try:
                risky_operation()
            except ValueError as e:
                raise QueryExecutionError(
                    "Query failed", details={"query": "g.V().count()"}
                ) from e

        exc = exc_info.value
        assert exc.message == "Query failed"
        assert exc.details["query"] == "g.V().count()"
        assert isinstance(exc.__cause__, ValueError)

    def test_error_serialization_for_api(self):
        """Test error serialization for API responses."""
        exc = ValidationError(
            "Invalid entity_id",
            error_code="VAL_001",
            details={"field": "entity_id", "value": "", "constraint": "non-empty"},
        )

        result = exc.to_dict()

        # Verify API-friendly structure
        assert "error_code" in result
        assert "message" in result
        assert "timestamp" in result
        assert "details" in result
        assert result["error_code"] == "VAL_001"

    def test_error_logging_pattern(self):
        """Test error logging pattern."""
        exc = QueryExecutionError(
            "Query failed",
            error_code="QUERY_001",
            details={"query": "g.V().count()", "timeout": 30},
        )

        # Verify exception has all info needed for logging
        assert exc.message
        assert exc.error_code
        assert exc.details
        assert exc.timestamp

    def test_retry_logic_pattern(self):
        """Test retry logic pattern."""
        retryable = ConnectionTimeoutError("Timeout")
        non_retryable = ValidationError("Invalid")

        # Verify retry logic can distinguish
        assert is_retryable_error(retryable)
        assert not is_retryable_error(non_retryable)

    def test_error_categorization_pattern(self):
        """Test error categorization for monitoring."""
        errors = [
            ConnectionFailedError("Failed"),
            QueryValidationError("Invalid"),
            ValidationError("Invalid data"),
            AuthenticationError("Auth failed"),
        ]

        categories = [get_error_category(e) for e in errors]

        assert categories == ["connection", "query", "data", "security"]

# Made with Bob
