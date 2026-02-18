"""
Unit Tests for Banking Domain Exception Hierarchy

Tests cover:
- Base exception functionality
- Data generation errors
- Streaming errors
- Analytics errors
- Compliance errors
- Utility functions

Created: 2026-02-11
Week 3 Day 16: Banking Exception Refactoring
"""

from datetime import datetime

import pytest

from banking.exceptions import (
    AnalyticsError,
    AuditLoggingError,
    BankingBaseException,
    ComplianceError,
    ComplianceViolationError,
    ConsumerError,
    DataGenerationError,
    DeadLetterQueueError,
    DetectionError,
    GeneratorConfigurationError,
    GeneratorExecutionError,
    InsufficientDataError,
    MessageSerializationError,
    PatternInjectionError,
    ProducerError,
    ReportGenerationError,
    StreamingConnectionError,
    StreamingError,
    ThresholdViolationError,
    get_banking_error_category,
    is_critical_banking_error,
    is_retryable_banking_error,
)

# ============================================================================
# Base Exception Tests
# ============================================================================


class TestBankingBaseException:
    """Tests for BankingBaseException base class."""

    def test_create_basic_exception(self):
        """Test creating exception with just message."""
        exc = BankingBaseException("Test error")

        assert exc.message == "Test error"
        assert exc.error_code == "BankingBaseException"
        assert exc.entity_id is None
        assert exc.entity_type is None
        assert exc.details == {}
        assert isinstance(exc.timestamp, datetime)

    def test_create_exception_with_entity_info(self):
        """Test creating exception with entity information."""
        exc = BankingBaseException("Test error", entity_id="p-123", entity_type="person")

        assert exc.entity_id == "p-123"
        assert exc.entity_type == "person"

    def test_create_exception_with_all_fields(self):
        """Test creating exception with all fields."""
        exc = BankingBaseException(
            "Test error",
            error_code="BANK_001",
            entity_id="p-123",
            entity_type="person",
            details={"key": "value"},
        )

        assert exc.error_code == "BANK_001"
        assert exc.entity_id == "p-123"
        assert exc.entity_type == "person"
        assert exc.details == {"key": "value"}

    def test_exception_to_dict(self):
        """Test converting exception to dictionary."""
        exc = BankingBaseException(
            "Test error",
            error_code="BANK_001",
            entity_id="p-123",
            entity_type="person",
            details={"key": "value"},
        )

        result = exc.to_dict()

        assert result["error_code"] == "BANK_001"
        assert result["message"] == "Test error"
        assert result["entity_id"] == "p-123"
        assert result["entity_type"] == "person"
        assert result["details"] == {"key": "value"}
        assert "timestamp" in result

    def test_exception_to_dict_minimal(self):
        """Test converting minimal exception to dictionary."""
        exc = BankingBaseException("Test error")

        result = exc.to_dict()

        assert result["error_code"] == "BankingBaseException"
        assert result["message"] == "Test error"
        assert "entity_id" not in result
        assert "entity_type" not in result
        assert "details" not in result

    def test_exception_str_representation(self):
        """Test string representation of exception."""
        exc = BankingBaseException(
            "Test error",
            error_code="BANK_001",
            entity_id="p-123",
            entity_type="person",
        )

        result = str(exc)

        assert "BANK_001" in result
        assert "Test error" in result
        assert "p-123" in result
        assert "person" in result


# ============================================================================
# Data Generation Error Tests
# ============================================================================


class TestDataGenerationErrors:
    """Tests for data generation exceptions."""

    def test_generator_configuration_error(self):
        """Test GeneratorConfigurationError."""
        exc = GeneratorConfigurationError(
            "Invalid seed", details={"seed": -1, "constraint": "non-negative"}
        )

        assert isinstance(exc, DataGenerationError)
        assert isinstance(exc, BankingBaseException)
        assert exc.message == "Invalid seed"
        assert exc.details["seed"] == -1

    def test_generator_execution_error(self):
        """Test GeneratorExecutionError."""
        exc = GeneratorExecutionError(
            "Generation failed",
            entity_type="person",
            details={"attempt": 3, "error": "constraint violation"},
        )

        assert isinstance(exc, DataGenerationError)
        assert exc.entity_type == "person"
        assert exc.details["attempt"] == 3

    def test_pattern_injection_error(self):
        """Test PatternInjectionError."""
        exc = PatternInjectionError(
            "Pattern injection failed",
            details={"pattern": "structuring", "required_entities": 10, "available": 5},
        )

        assert isinstance(exc, DataGenerationError)
        assert exc.details["pattern"] == "structuring"


# ============================================================================
# Streaming Error Tests
# ============================================================================


class TestStreamingErrors:
    """Tests for streaming exceptions."""

    def test_producer_error(self):
        """Test ProducerError."""
        exc = ProducerError(
            "Send failed",
            entity_id="p-123",
            entity_type="person",
            details={"topic": "persons-events", "attempt": 3},
        )

        assert isinstance(exc, StreamingError)
        assert isinstance(exc, BankingBaseException)
        assert exc.entity_id == "p-123"
        assert exc.details["topic"] == "persons-events"

    def test_consumer_error(self):
        """Test ConsumerError."""
        exc = ConsumerError(
            "Processing failed",
            entity_id="p-123",
            details={"topic": "persons-events", "offset": 12345},
        )

        assert isinstance(exc, StreamingError)
        assert exc.details["offset"] == 12345

    def test_message_serialization_error(self):
        """Test MessageSerializationError."""
        exc = MessageSerializationError(
            "Serialization failed",
            entity_id="p-123",
            entity_type="person",
            details={"format": "JSON", "error": "invalid character"},
        )

        assert isinstance(exc, StreamingError)
        assert exc.details["format"] == "JSON"

    def test_dead_letter_queue_error(self):
        """Test DeadLetterQueueError."""
        exc = DeadLetterQueueError(
            "DLQ send failed",
            entity_id="p-123",
            details={"original_topic": "persons-events", "retry_count": 5},
        )

        assert isinstance(exc, StreamingError)
        assert exc.details["retry_count"] == 5

    def test_streaming_connection_error(self):
        """Test StreamingConnectionError."""
        exc = StreamingConnectionError(
            "Connection failed",
            details={"broker_url": "pulsar://localhost:6650", "timeout": 30},
        )

        assert isinstance(exc, StreamingError)
        assert exc.details["broker_url"] == "pulsar://localhost:6650"


# ============================================================================
# Analytics Error Tests
# ============================================================================


class TestAnalyticsErrors:
    """Tests for analytics exceptions."""

    def test_detection_error(self):
        """Test DetectionError."""
        exc = DetectionError(
            "Detection failed",
            entity_id="p-123",
            entity_type="person",
            details={"algorithm": "structuring", "error": "insufficient data"},
        )

        assert isinstance(exc, AnalyticsError)
        assert isinstance(exc, BankingBaseException)
        assert exc.details["algorithm"] == "structuring"

    def test_insufficient_data_error(self):
        """Test InsufficientDataError."""
        exc = InsufficientDataError(
            "Insufficient transactions",
            entity_id="p-123",
            entity_type="person",
            details={"required": 10, "available": 3},
        )

        assert isinstance(exc, AnalyticsError)
        assert exc.details["required"] == 10

    def test_threshold_violation_error(self):
        """Test ThresholdViolationError."""
        exc = ThresholdViolationError(
            "Threshold exceeded",
            entity_id="p-123",
            entity_type="person",
            details={"risk_score": 0.95, "threshold": 0.8, "rule": "structuring"},
        )

        assert isinstance(exc, AnalyticsError)
        assert exc.details["risk_score"] == 0.95


# ============================================================================
# Compliance Error Tests
# ============================================================================


class TestComplianceErrors:
    """Tests for compliance exceptions."""

    def test_audit_logging_error(self):
        """Test AuditLoggingError."""
        exc = AuditLoggingError(
            "Audit log failed",
            entity_id="p-123",
            details={"event_type": "data_access", "user": "analyst@example.com"},
        )

        assert isinstance(exc, ComplianceError)
        assert isinstance(exc, BankingBaseException)
        assert exc.details["event_type"] == "data_access"

    def test_compliance_violation_error(self):
        """Test ComplianceViolationError."""
        exc = ComplianceViolationError(
            "GDPR violation",
            entity_id="p-123",
            entity_type="person",
            details={"regulation": "GDPR", "article": "17", "retention_days": 400},
        )

        assert isinstance(exc, ComplianceError)
        assert exc.details["regulation"] == "GDPR"

    def test_report_generation_error(self):
        """Test ReportGenerationError."""
        exc = ReportGenerationError(
            "Report generation failed",
            details={"report_type": "SAR", "period": "2026-01", "error": "missing data"},
        )

        assert isinstance(exc, ComplianceError)
        assert exc.details["report_type"] == "SAR"


# ============================================================================
# Utility Function Tests
# ============================================================================


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_is_retryable_banking_error_for_retryable(self):
        """Test is_retryable_banking_error for retryable errors."""
        retryable_errors = [
            GeneratorExecutionError("Failed"),
            ProducerError("Send failed"),
            ConsumerError("Processing failed"),
            StreamingConnectionError("Connection failed"),
            DetectionError("Detection failed"),
            ReportGenerationError("Report failed"),
        ]

        for error in retryable_errors:
            assert is_retryable_banking_error(error), f"{type(error).__name__} should be retryable"

    def test_is_retryable_banking_error_for_non_retryable(self):
        """Test is_retryable_banking_error for non-retryable errors."""
        non_retryable_errors = [
            GeneratorConfigurationError("Invalid config"),
            PatternInjectionError("Pattern failed"),
            MessageSerializationError("Serialization failed"),
            InsufficientDataError("Not enough data"),
            AuditLoggingError("Audit failed"),
        ]

        for error in non_retryable_errors:
            assert not is_retryable_banking_error(
                error
            ), f"{type(error).__name__} should not be retryable"

    def test_get_banking_error_category_data_generation(self):
        """Test get_banking_error_category for data generation errors."""
        errors = [
            GeneratorConfigurationError("Invalid"),
            GeneratorExecutionError("Failed"),
            PatternInjectionError("Pattern failed"),
        ]

        for error in errors:
            assert get_banking_error_category(error) == "data_generation"

    def test_get_banking_error_category_streaming(self):
        """Test get_banking_error_category for streaming errors."""
        errors = [
            ProducerError("Send failed"),
            ConsumerError("Processing failed"),
            MessageSerializationError("Serialization failed"),
            DeadLetterQueueError("DLQ failed"),
            StreamingConnectionError("Connection failed"),
        ]

        for error in errors:
            assert get_banking_error_category(error) == "streaming"

    def test_get_banking_error_category_analytics(self):
        """Test get_banking_error_category for analytics errors."""
        errors = [
            DetectionError("Detection failed"),
            InsufficientDataError("Not enough data"),
            ThresholdViolationError("Threshold exceeded"),
        ]

        for error in errors:
            assert get_banking_error_category(error) == "analytics"

    def test_get_banking_error_category_compliance(self):
        """Test get_banking_error_category for compliance errors."""
        errors = [
            AuditLoggingError("Audit failed"),
            ComplianceViolationError("Violation detected"),
            ReportGenerationError("Report failed"),
        ]

        for error in errors:
            assert get_banking_error_category(error) == "compliance"

    def test_get_banking_error_category_unknown(self):
        """Test get_banking_error_category for unknown errors."""
        error = ValueError("Standard error")

        assert get_banking_error_category(error) == "unknown"

    def test_is_critical_banking_error_for_critical(self):
        """Test is_critical_banking_error for critical errors."""
        critical_errors = [
            AuditLoggingError("Audit failed"),
            DeadLetterQueueError("DLQ failed"),
            ComplianceViolationError("Violation detected"),
        ]

        for error in critical_errors:
            assert is_critical_banking_error(error), f"{type(error).__name__} should be critical"

    def test_is_critical_banking_error_for_non_critical(self):
        """Test is_critical_banking_error for non-critical errors."""
        non_critical_errors = [
            ProducerError("Send failed"),
            DetectionError("Detection failed"),
            GeneratorExecutionError("Generation failed"),
        ]

        for error in non_critical_errors:
            assert not is_critical_banking_error(
                error
            ), f"{type(error).__name__} should not be critical"


# ============================================================================
# Integration Tests
# ============================================================================


class TestBankingExceptionIntegration:
    """Integration tests for banking exception usage patterns."""

    def test_streaming_error_handling_pattern(self):
        """Test typical streaming error handling pattern."""

        def send_to_pulsar():
            raise ConnectionError("Pulsar unavailable")

        with pytest.raises(ProducerError) as exc_info:
            try:
                send_to_pulsar()
            except ConnectionError as e:
                raise ProducerError(
                    "Failed to send message",
                    entity_id="p-123",
                    entity_type="person",
                    details={"topic": "persons-events"},
                ) from e

        exc = exc_info.value
        assert exc.entity_id == "p-123"
        assert exc.details["topic"] == "persons-events"

    def test_analytics_error_with_entity_tracking(self):
        """Test analytics error with entity tracking."""
        exc = DetectionError(
            "Structuring detection failed",
            entity_id="p-123",
            entity_type="person",
            details={
                "algorithm": "structuring",
                "transactions_analyzed": 50,
                "error": "insufficient pattern data",
            },
        )

        # Verify entity tracking
        assert exc.entity_id == "p-123"
        assert exc.entity_type == "person"

        # Verify API serialization
        result = exc.to_dict()
        assert result["entity_id"] == "p-123"
        assert result["entity_type"] == "person"

    def test_compliance_error_for_audit(self):
        """Test compliance error for audit logging."""
        exc = AuditLoggingError(
            "Failed to write audit log",
            entity_id="p-123",
            details={
                "event_type": "data_access",
                "user": "analyst@example.com",
                "timestamp": "2026-02-11T12:00:00Z",
            },
        )

        # Verify critical error detection
        assert is_critical_banking_error(exc)

        # Verify error categorization
        assert get_banking_error_category(exc) == "compliance"

    def test_retry_logic_with_banking_errors(self):
        """Test retry logic with banking errors."""
        retryable = ProducerError("Temporary failure")
        non_retryable = MessageSerializationError("Invalid format")

        # Verify retry logic can distinguish
        assert is_retryable_banking_error(retryable)
        assert not is_retryable_banking_error(non_retryable)

    def test_error_monitoring_pattern(self):
        """Test error monitoring and categorization."""
        errors = [
            ProducerError("Send failed"),
            DetectionError("Detection failed"),
            AuditLoggingError("Audit failed"),
            GeneratorExecutionError("Generation failed"),
        ]

        categories = [get_banking_error_category(e) for e in errors]
        critical_flags = [is_critical_banking_error(e) for e in errors]

        assert categories == ["streaming", "analytics", "compliance", "data_generation"]
        assert critical_flags == [False, False, True, False]


# Made with Bob
