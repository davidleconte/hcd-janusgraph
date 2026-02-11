"""
Custom Exception Hierarchy for JanusGraph Infrastructure

This module provides a comprehensive exception hierarchy for the JanusGraph
banking compliance platform. All custom exceptions inherit from JanusGraphBaseException
and provide structured error information for better debugging and error handling.

Features:
    - Structured error information (code, message, details, timestamp)
    - Exception chaining support
    - API-friendly error serialization
    - Consistent error handling patterns

Created: 2026-02-11
Week 3 Day 15: Core Exception Refactoring
"""

from datetime import datetime
from typing import Any, Dict, Optional


class JanusGraphBaseException(Exception):
    """
    Base exception for all JanusGraph-related errors.

    All custom exceptions should inherit from this class to ensure
    consistent error handling and structured error information.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code (defaults to class name)
        details: Additional context as dictionary
        cause: Original exception if chained
        timestamp: When the error occurred (UTC)

    Example:
        >>> try:
        ...     raise JanusGraphBaseException(
        ...         "Operation failed",
        ...         error_code="OP_001",
        ...         details={"operation": "query", "retries": 3}
        ...     )
        ... except JanusGraphBaseException as e:
        ...     print(e.to_dict())
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code (defaults to class name)
            details: Additional context as dictionary
            cause: Original exception if chained
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for API responses.

        Returns:
            Dictionary with error information suitable for JSON serialization
        """
        result: Dict[str, Any] = {
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() + "Z",
        }

        if self.details:
            result["details"] = self.details

        if self.cause:
            result["cause"] = str(self.cause)

        return result

    def __str__(self) -> str:
        """String representation of the exception."""
        if self.details:
            return f"{self.error_code}: {self.message} (details: {self.details})"
        return f"{self.error_code}: {self.message}"


# ============================================================================
# Connection Errors
# ============================================================================


class ConnectionError(JanusGraphBaseException):
    """
    Base exception for connection-related errors.

    Use this for any errors related to establishing or maintaining
    connections to JanusGraph, Cassandra, or other backend services.
    """

    pass


class ConnectionFailedError(ConnectionError):
    """
    Failed to establish connection to backend service.

    Raised when initial connection attempt fails. This is typically
    a retryable error.

    Example:
        >>> raise ConnectionFailedError(
        ...     "Failed to connect to JanusGraph",
        ...     details={"host": "localhost", "port": 8182, "attempt": 3}
        ... )
    """

    pass


class ConnectionLostError(ConnectionError):
    """
    Connection to backend service was lost.

    Raised when an established connection is unexpectedly closed.
    This typically requires reconnection logic.

    Example:
        >>> raise ConnectionLostError(
        ...     "Connection to JanusGraph lost",
        ...     details={"duration": "5m", "queries_executed": 42}
        ... )
    """

    pass


class ConnectionTimeoutError(ConnectionError):
    """
    Connection attempt timed out.

    Raised when connection attempt exceeds timeout threshold.
    This is typically a retryable error.

    Example:
        >>> raise ConnectionTimeoutError(
        ...     "Connection timeout",
        ...     details={"timeout_seconds": 30, "host": "localhost"}
        ... )
    """

    pass


class ConnectionPoolExhaustedError(ConnectionError):
    """
    Connection pool has no available connections.

    Raised when all connections in the pool are in use and
    no new connections can be created.

    Example:
        >>> raise ConnectionPoolExhaustedError(
        ...     "Connection pool exhausted",
        ...     details={"pool_size": 10, "active": 10, "waiting": 5}
        ... )
    """

    pass


# ============================================================================
# Query Errors
# ============================================================================


class QueryError(JanusGraphBaseException):
    """
    Base exception for query-related errors.

    Use this for any errors related to query construction,
    validation, or execution.
    """

    pass


class QueryValidationError(QueryError):
    """
    Query validation failed.

    Raised when a query fails validation checks before execution.
    This is typically not retryable.

    Example:
        >>> raise QueryValidationError(
        ...     "Invalid Gremlin syntax",
        ...     details={"query": "g.V().invalid()", "line": 1, "column": 10}
        ... )
    """

    pass


class QueryExecutionError(QueryError):
    """
    Query execution failed.

    Raised when a valid query fails during execution.
    May be retryable depending on the cause.

    Example:
        >>> raise QueryExecutionError(
        ...     "Query execution failed",
        ...     details={"query": "g.V().count()", "error": "timeout"}
        ... )
    """

    pass


class QueryTimeoutError(QueryError):
    """
    Query execution timed out.

    Raised when query execution exceeds timeout threshold.
    This is typically retryable with a longer timeout.

    Example:
        >>> raise QueryTimeoutError(
        ...     "Query timeout",
        ...     details={"query": "g.V().count()", "timeout_seconds": 30}
        ... )
    """

    pass


class QueryResultError(QueryError):
    """
    Error processing query results.

    Raised when query executes successfully but results
    cannot be processed or deserialized.

    Example:
        >>> raise QueryResultError(
        ...     "Failed to deserialize query results",
        ...     details={"result_type": "vertex", "error": "invalid JSON"}
        ... )
    """

    pass


# ============================================================================
# Data Errors
# ============================================================================


class DataError(JanusGraphBaseException):
    """
    Base exception for data-related errors.

    Use this for any errors related to data validation,
    entity operations, or data integrity.
    """

    pass


class ValidationError(DataError):
    """
    Data validation failed.

    Raised when data fails validation checks.
    This is typically not retryable without fixing the data.

    Example:
        >>> raise ValidationError(
        ...     "Invalid entity_id",
        ...     details={"field": "entity_id", "value": "", "constraint": "non-empty"}
        ... )
    """

    pass


class EntityNotFoundError(DataError):
    """
    Entity not found in graph.

    Raised when attempting to access an entity that doesn't exist.
    This is typically not retryable.

    Example:
        >>> raise EntityNotFoundError(
        ...     "Person not found",
        ...     details={"entity_type": "person", "entity_id": "p-123"}
        ... )
    """

    pass


class DuplicateEntityError(DataError):
    """
    Entity already exists.

    Raised when attempting to create an entity that already exists.
    This is typically not retryable.

    Example:
        >>> raise DuplicateEntityError(
        ...     "Person already exists",
        ...     details={"entity_type": "person", "entity_id": "p-123"}
        ... )
    """

    pass


class DataIntegrityError(DataError):
    """
    Data integrity constraint violated.

    Raised when an operation would violate data integrity constraints.
    This is typically not retryable without fixing the data.

    Example:
        >>> raise DataIntegrityError(
        ...     "Foreign key constraint violated",
        ...     details={"entity": "account", "constraint": "owner_id"}
        ... )
    """

    pass


class SerializationError(DataError):
    """
    Data serialization/deserialization failed.

    Raised when data cannot be serialized or deserialized.
    This is typically not retryable.

    Example:
        >>> raise SerializationError(
        ...     "Failed to serialize entity",
        ...     details={"entity_type": "person", "format": "JSON"}
        ... )
    """

    pass


# ============================================================================
# Configuration Errors
# ============================================================================


class ConfigurationError(JanusGraphBaseException):
    """
    Base exception for configuration errors.

    Use this for any errors related to system configuration,
    settings, or initialization.
    """

    pass


class InvalidConfigurationError(ConfigurationError):
    """
    Configuration is invalid.

    Raised when configuration values are invalid or inconsistent.
    This is typically not retryable without fixing the configuration.

    Example:
        >>> raise InvalidConfigurationError(
        ...     "Invalid port number",
        ...     details={"setting": "janusgraph.port", "value": -1}
        ... )
    """

    pass


class MissingConfigurationError(ConfigurationError):
    """
    Required configuration is missing.

    Raised when required configuration values are not provided.
    This is typically not retryable without providing the configuration.

    Example:
        >>> raise MissingConfigurationError(
        ...     "Missing required setting",
        ...     details={"setting": "janusgraph.host"}
        ... )
    """

    pass


class ConfigurationLoadError(ConfigurationError):
    """
    Failed to load configuration.

    Raised when configuration cannot be loaded from file or environment.
    This may be retryable if the issue is transient.

    Example:
        >>> raise ConfigurationLoadError(
        ...     "Failed to load config file",
        ...     details={"file": "config.yml", "error": "file not found"}
        ... )
    """

    pass


# ============================================================================
# Authentication & Authorization Errors
# ============================================================================


class SecurityError(JanusGraphBaseException):
    """
    Base exception for security-related errors.

    Use this for any errors related to authentication,
    authorization, or security violations.
    """

    pass


class AuthenticationError(SecurityError):
    """
    Authentication failed.

    Raised when user authentication fails.
    This is typically not retryable without correct credentials.

    Example:
        >>> raise AuthenticationError(
        ...     "Invalid credentials",
        ...     details={"username": "user@example.com"}
        ... )
    """

    pass


class AuthorizationError(SecurityError):
    """
    Authorization failed.

    Raised when user lacks required permissions.
    This is typically not retryable without granting permissions.

    Example:
        >>> raise AuthorizationError(
        ...     "Insufficient permissions",
        ...     details={"user": "user@example.com", "required_role": "admin"}
        ... )
    """

    pass


class TokenExpiredError(SecurityError):
    """
    Authentication token expired.

    Raised when authentication token has expired.
    This is retryable with token refresh.

    Example:
        >>> raise TokenExpiredError(
        ...     "Token expired",
        ...     details={"token_type": "JWT", "expired_at": "2026-02-11T12:00:00Z"}
        ... )
    """

    pass


# ============================================================================
# Resource Errors
# ============================================================================


class ResourceError(JanusGraphBaseException):
    """
    Base exception for resource-related errors.

    Use this for any errors related to system resources,
    limits, or capacity.
    """

    pass


class ResourceExhaustedError(ResourceError):
    """
    System resource exhausted.

    Raised when system resource (memory, disk, etc.) is exhausted.
    This may be retryable after resource cleanup.

    Example:
        >>> raise ResourceExhaustedError(
        ...     "Memory limit exceeded",
        ...     details={"resource": "memory", "limit": "8GB", "used": "8.2GB"}
        ... )
    """

    pass


class RateLimitExceededError(ResourceError):
    """
    Rate limit exceeded.

    Raised when request rate exceeds configured limits.
    This is retryable after waiting.

    Example:
        >>> raise RateLimitExceededError(
        ...     "Rate limit exceeded",
        ...     details={"limit": 100, "window": "1m", "retry_after": 30}
        ... )
    """

    pass


# ============================================================================
# Utility Functions
# ============================================================================


def is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is retryable.

    Args:
        error: Exception to check

    Returns:
        True if error is retryable, False otherwise

    Example:
        >>> error = ConnectionTimeoutError("Timeout")
        >>> is_retryable_error(error)
        True
    """
    retryable_types = (
        ConnectionFailedError,
        ConnectionTimeoutError,
        ConnectionLostError,
        QueryTimeoutError,
        TokenExpiredError,
        RateLimitExceededError,
    )
    return isinstance(error, retryable_types)


def get_error_category(error: Exception) -> str:
    """
    Get the category of an error.

    Args:
        error: Exception to categorize

    Returns:
        Error category as string

    Example:
        >>> error = QueryValidationError("Invalid query")
        >>> get_error_category(error)
        'query'
    """
    if isinstance(error, ConnectionError):
        return "connection"
    elif isinstance(error, QueryError):
        return "query"
    elif isinstance(error, DataError):
        return "data"
    elif isinstance(error, ConfigurationError):
        return "configuration"
    elif isinstance(error, SecurityError):
        return "security"
    elif isinstance(error, ResourceError):
        return "resource"
    else:
        return "unknown"

# Made with Bob
