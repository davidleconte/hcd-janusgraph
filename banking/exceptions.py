"""
Custom Exception Hierarchy for Banking Domain

This module provides domain-specific exceptions for the banking compliance
platform. All exceptions inherit from BankingBaseException and provide
structured error information for banking operations.

Features:
    - Domain-specific error types (data generation, streaming, analytics, compliance)
    - Entity-level error tracking (entity_id, entity_type)
    - Structured error information for debugging
    - API-friendly error serialization

Created: 2026-02-11
Week 3 Day 16: Banking Exception Refactoring
"""

from datetime import datetime
from typing import Any, Dict, Optional


class BankingBaseException(Exception):
    """
    Base exception for all banking domain errors.

    All banking-specific exceptions should inherit from this class to ensure
    consistent error handling and structured error information.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code (defaults to class name)
        entity_id: ID of the entity involved in the error
        entity_type: Type of entity (person, account, transaction, etc.)
        details: Additional context as dictionary
        timestamp: When the error occurred (UTC)

    Example:
        >>> raise BankingBaseException(
        ...     "Operation failed",
        ...     error_code="BANK_001",
        ...     entity_id="p-123",
        ...     entity_type="person",
        ...     details={"operation": "create"}
        ... )
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code (defaults to class name)
            entity_id: ID of the entity involved
            entity_type: Type of entity
            details: Additional context as dictionary
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.details = details or {}
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

        if self.entity_id:
            result["entity_id"] = self.entity_id

        if self.entity_type:
            result["entity_type"] = self.entity_type

        if self.details:
            result["details"] = self.details

        return result

    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [f"{self.error_code}: {self.message}"]

        if self.entity_id:
            parts.append(f"entity_id={self.entity_id}")

        if self.entity_type:
            parts.append(f"entity_type={self.entity_type}")

        if self.details:
            parts.append(f"details={self.details}")

        return " | ".join(parts)


# ============================================================================
# Data Generation Errors
# ============================================================================


class DataGenerationError(BankingBaseException):
    """
    Base exception for data generation errors.

    Use this for any errors related to synthetic data generation,
    including configuration, execution, and validation errors.
    """

    pass


class GeneratorConfigurationError(DataGenerationError):
    """
    Generator configuration is invalid.

    Raised when generator configuration values are invalid or inconsistent.
    This is typically not retryable without fixing the configuration.

    Example:
        >>> raise GeneratorConfigurationError(
        ...     "Invalid seed value",
        ...     details={"seed": -1, "constraint": "must be non-negative"}
        ... )
    """

    pass


class GeneratorExecutionError(DataGenerationError):
    """
    Generator execution failed.

    Raised when data generation fails during execution.
    May be retryable depending on the cause.

    Example:
        >>> raise GeneratorExecutionError(
        ...     "Failed to generate person",
        ...     entity_type="person",
        ...     details={"attempt": 3, "error": "constraint violation"}
        ... )
    """

    pass


class PatternInjectionError(DataGenerationError):
    """
    Pattern injection failed.

    Raised when fraud/AML pattern injection fails.
    This is typically not retryable without fixing the pattern configuration.

    Example:
        >>> raise PatternInjectionError(
        ...     "Failed to inject structuring pattern",
        ...     details={"pattern": "structuring", "required_entities": 10, "available": 5}
        ... )
    """

    pass


# ============================================================================
# Streaming Errors
# ============================================================================


class StreamingError(BankingBaseException):
    """
    Base exception for streaming errors.

    Use this for any errors related to Pulsar streaming,
    including producer, consumer, and message processing errors.
    """

    pass


class ProducerError(StreamingError):
    """
    Producer operation failed.

    Raised when Pulsar producer operations fail.
    May be retryable depending on the cause.

    Example:
        >>> raise ProducerError(
        ...     "Failed to send message",
        ...     entity_id="p-123",
        ...     entity_type="person",
        ...     details={"topic": "persons-events", "attempt": 3}
        ... )
    """

    pass


class ConsumerError(StreamingError):
    """
    Consumer operation failed.

    Raised when Pulsar consumer operations fail.
    May be retryable depending on the cause.

    Example:
        >>> raise ConsumerError(
        ...     "Failed to process message",
        ...     entity_id="p-123",
        ...     details={"topic": "persons-events", "offset": 12345}
        ... )
    """

    pass


class MessageSerializationError(StreamingError):
    """
    Message serialization/deserialization failed.

    Raised when message cannot be serialized or deserialized.
    This is typically not retryable without fixing the message format.

    Example:
        >>> raise MessageSerializationError(
        ...     "Failed to serialize event",
        ...     entity_id="p-123",
        ...     entity_type="person",
        ...     details={"format": "JSON", "error": "invalid character"}
        ... )
    """

    pass


class DeadLetterQueueError(StreamingError):
    """
    Dead letter queue operation failed.

    Raised when DLQ operations fail (send to DLQ, retry from DLQ, etc.).
    This is typically a critical error requiring investigation.

    Example:
        >>> raise DeadLetterQueueError(
        ...     "Failed to send message to DLQ",
        ...     entity_id="p-123",
        ...     details={"original_topic": "persons-events", "retry_count": 5}
        ... )
    """

    pass


class StreamingConnectionError(StreamingError):
    """
    Streaming connection failed.

    Raised when connection to Pulsar broker fails.
    This is typically retryable.

    Example:
        >>> raise StreamingConnectionError(
        ...     "Failed to connect to Pulsar",
        ...     details={"broker_url": "pulsar://localhost:6650", "timeout": 30}
        ... )
    """

    pass


# ============================================================================
# Analytics Errors
# ============================================================================


class AnalyticsError(BankingBaseException):
    """
    Base exception for analytics errors.

    Use this for any errors related to analytics operations,
    including detection algorithms, data analysis, and reporting.
    """

    pass


class DetectionError(AnalyticsError):
    """
    Detection algorithm failed.

    Raised when fraud/AML detection algorithms fail.
    May be retryable depending on the cause.

    Example:
        >>> raise DetectionError(
        ...     "Structuring detection failed",
        ...     entity_id="p-123",
        ...     entity_type="person",
        ...     details={"algorithm": "structuring", "error": "insufficient data"}
        ... )
    """

    pass


class InsufficientDataError(AnalyticsError):
    """
    Insufficient data for analysis.

    Raised when there is not enough data to perform analysis.
    This is typically not retryable without more data.

    Example:
        >>> raise InsufficientDataError(
        ...     "Insufficient transactions for analysis",
        ...     entity_id="p-123",
        ...     entity_type="person",
        ...     details={"required": 10, "available": 3}
        ... )
    """

    pass


class ThresholdViolationError(AnalyticsError):
    """
    Risk threshold violated.

    Raised when risk score exceeds configured thresholds.
    This is not an error per se, but a detection result.

    Example:
        >>> raise ThresholdViolationError(
        ...     "Risk score exceeds threshold",
        ...     entity_id="p-123",
        ...     entity_type="person",
        ...     details={"risk_score": 0.95, "threshold": 0.8, "rule": "structuring"}
        ... )
    """

    pass


# ============================================================================
# Compliance Errors
# ============================================================================


class ComplianceError(BankingBaseException):
    """
    Base exception for compliance errors.

    Use this for any errors related to compliance operations,
    including audit logging, reporting, and regulatory requirements.
    """

    pass


class AuditLoggingError(ComplianceError):
    """
    Audit logging failed.

    Raised when audit log operations fail.
    This is typically a critical error requiring immediate attention.

    Example:
        >>> raise AuditLoggingError(
        ...     "Failed to write audit log",
        ...     entity_id="p-123",
        ...     details={"event_type": "data_access", "user": "analyst@example.com"}
        ... )
    """

    pass


class ComplianceViolationError(ComplianceError):
    """
    Compliance violation detected.

    Raised when a compliance violation is detected.
    This is not an error per se, but a compliance alert.

    Example:
        >>> raise ComplianceViolationError(
        ...     "GDPR violation: data retention exceeded",
        ...     entity_id="p-123",
        ...     entity_type="person",
        ...     details={"regulation": "GDPR", "article": "17", "retention_days": 400}
        ... )
    """

    pass


class ReportGenerationError(ComplianceError):
    """
    Compliance report generation failed.

    Raised when compliance report generation fails.
    May be retryable depending on the cause.

    Example:
        >>> raise ReportGenerationError(
        ...     "Failed to generate SAR report",
        ...     details={"report_type": "SAR", "period": "2026-01", "error": "missing data"}
        ... )
    """

    pass


# ============================================================================
# Utility Functions
# ============================================================================


def is_retryable_banking_error(error: Exception) -> bool:
    """
    Check if a banking error is retryable.

    Args:
        error: Exception to check

    Returns:
        True if error is retryable, False otherwise

    Example:
        >>> error = ProducerError("Send failed")
        >>> is_retryable_banking_error(error)
        True
    """
    retryable_types = (
        GeneratorExecutionError,
        ProducerError,
        ConsumerError,
        StreamingConnectionError,
        DetectionError,
        ReportGenerationError,
    )
    return isinstance(error, retryable_types)


def get_banking_error_category(error: Exception) -> str:
    """
    Get the category of a banking error.

    Args:
        error: Exception to categorize

    Returns:
        Error category as string

    Example:
        >>> error = ProducerError("Send failed")
        >>> get_banking_error_category(error)
        'streaming'
    """
    if isinstance(error, DataGenerationError):
        return "data_generation"
    elif isinstance(error, StreamingError):
        return "streaming"
    elif isinstance(error, AnalyticsError):
        return "analytics"
    elif isinstance(error, ComplianceError):
        return "compliance"
    else:
        return "unknown"


def is_critical_banking_error(error: Exception) -> bool:
    """
    Check if a banking error is critical and requires immediate attention.

    Args:
        error: Exception to check

    Returns:
        True if error is critical, False otherwise

    Example:
        >>> error = AuditLoggingError("Audit failed")
        >>> is_critical_banking_error(error)
        True
    """
    critical_types = (
        AuditLoggingError,
        DeadLetterQueueError,
        ComplianceViolationError,
    )
    return isinstance(error, critical_types)

# Made with Bob
