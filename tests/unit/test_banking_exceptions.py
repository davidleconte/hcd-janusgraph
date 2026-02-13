"""Tests for banking.exceptions module."""
import pytest
from datetime import datetime, timezone

from banking.exceptions import (
    BankingBaseException,
    DataGenerationError,
    GeneratorConfigurationError,
    GeneratorExecutionError,
    PatternInjectionError,
    StreamingError,
    ProducerError,
    ConsumerError,
    MessageSerializationError,
    DeadLetterQueueError,
    StreamingConnectionError,
    AnalyticsError,
    DetectionError,
    InsufficientDataError,
    ThresholdViolationError,
    ComplianceError,
    AuditLoggingError,
    ComplianceViolationError,
    ReportGenerationError,
    is_retryable_banking_error,
    get_banking_error_category,
    is_critical_banking_error,
)


class TestBankingBaseException:
    def test_basic_creation(self):
        e = BankingBaseException("test error")
        assert str(e).startswith("BankingBaseException: test error")
        assert e.message == "test error"
        assert e.error_code == "BankingBaseException"
        assert e.entity_id is None
        assert e.entity_type is None
        assert e.details == {}
        assert isinstance(e.timestamp, datetime)

    def test_full_creation(self):
        e = BankingBaseException(
            "op failed",
            error_code="BANK_001",
            entity_id="p-123",
            entity_type="person",
            details={"op": "create"},
        )
        assert e.error_code == "BANK_001"
        assert e.entity_id == "p-123"
        assert e.entity_type == "person"
        assert e.details == {"op": "create"}

    def test_to_dict(self):
        e = BankingBaseException("err", error_code="E1", entity_id="a-1", entity_type="account", details={"k": "v"})
        d = e.to_dict()
        assert d["error_code"] == "E1"
        assert d["message"] == "err"
        assert d["entity_id"] == "a-1"
        assert d["entity_type"] == "account"
        assert d["details"] == {"k": "v"}
        assert "timestamp" in d

    def test_to_dict_minimal(self):
        e = BankingBaseException("err")
        d = e.to_dict()
        assert "entity_id" not in d
        assert "entity_type" not in d
        assert "details" not in d

    def test_str_with_all_fields(self):
        e = BankingBaseException("msg", entity_id="x", entity_type="t", details={"a": 1})
        s = str(e)
        assert "entity_id=x" in s
        assert "entity_type=t" in s
        assert "details=" in s

    def test_is_exception(self):
        e = BankingBaseException("test")
        assert isinstance(e, Exception)


class TestExceptionHierarchy:
    def test_data_generation_hierarchy(self):
        assert issubclass(DataGenerationError, BankingBaseException)
        assert issubclass(GeneratorConfigurationError, DataGenerationError)
        assert issubclass(GeneratorExecutionError, DataGenerationError)
        assert issubclass(PatternInjectionError, DataGenerationError)

    def test_streaming_hierarchy(self):
        assert issubclass(StreamingError, BankingBaseException)
        assert issubclass(ProducerError, StreamingError)
        assert issubclass(ConsumerError, StreamingError)
        assert issubclass(MessageSerializationError, StreamingError)
        assert issubclass(DeadLetterQueueError, StreamingError)
        assert issubclass(StreamingConnectionError, StreamingError)

    def test_analytics_hierarchy(self):
        assert issubclass(AnalyticsError, BankingBaseException)
        assert issubclass(DetectionError, AnalyticsError)
        assert issubclass(InsufficientDataError, AnalyticsError)
        assert issubclass(ThresholdViolationError, AnalyticsError)

    def test_compliance_hierarchy(self):
        assert issubclass(ComplianceError, BankingBaseException)
        assert issubclass(AuditLoggingError, ComplianceError)
        assert issubclass(ComplianceViolationError, ComplianceError)
        assert issubclass(ReportGenerationError, ComplianceError)

    def test_catch_by_base(self):
        with pytest.raises(BankingBaseException):
            raise ProducerError("fail")

    def test_catch_by_category(self):
        with pytest.raises(StreamingError):
            raise DeadLetterQueueError("fail")


class TestIsRetryable:
    def test_retryable_errors(self):
        assert is_retryable_banking_error(GeneratorExecutionError("e"))
        assert is_retryable_banking_error(ProducerError("e"))
        assert is_retryable_banking_error(ConsumerError("e"))
        assert is_retryable_banking_error(StreamingConnectionError("e"))
        assert is_retryable_banking_error(DetectionError("e"))
        assert is_retryable_banking_error(ReportGenerationError("e"))

    def test_non_retryable_errors(self):
        assert not is_retryable_banking_error(GeneratorConfigurationError("e"))
        assert not is_retryable_banking_error(PatternInjectionError("e"))
        assert not is_retryable_banking_error(MessageSerializationError("e"))
        assert not is_retryable_banking_error(AuditLoggingError("e"))
        assert not is_retryable_banking_error(ComplianceViolationError("e"))
        assert not is_retryable_banking_error(ValueError("e"))


class TestGetCategory:
    def test_data_generation(self):
        assert get_banking_error_category(DataGenerationError("e")) == "data_generation"
        assert get_banking_error_category(GeneratorConfigurationError("e")) == "data_generation"

    def test_streaming(self):
        assert get_banking_error_category(StreamingError("e")) == "streaming"
        assert get_banking_error_category(ProducerError("e")) == "streaming"

    def test_analytics(self):
        assert get_banking_error_category(AnalyticsError("e")) == "analytics"
        assert get_banking_error_category(DetectionError("e")) == "analytics"

    def test_compliance(self):
        assert get_banking_error_category(ComplianceError("e")) == "compliance"
        assert get_banking_error_category(AuditLoggingError("e")) == "compliance"

    def test_unknown(self):
        assert get_banking_error_category(ValueError("e")) == "unknown"


class TestIsCritical:
    def test_critical_errors(self):
        assert is_critical_banking_error(AuditLoggingError("e"))
        assert is_critical_banking_error(DeadLetterQueueError("e"))
        assert is_critical_banking_error(ComplianceViolationError("e"))

    def test_non_critical_errors(self):
        assert not is_critical_banking_error(ProducerError("e"))
        assert not is_critical_banking_error(DetectionError("e"))
        assert not is_critical_banking_error(ValueError("e"))
