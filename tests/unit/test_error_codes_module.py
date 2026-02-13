"""Tests for src.python.utils.error_codes module."""
import pytest
from src.python.utils.error_codes import (
    ErrorCategory, ErrorCode, ERROR_CODES, AppException,
    ValidationError, NotFoundError, ConnectionError,
)


class TestErrorCategory:
    def test_values(self):
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.AUTHENTICATION.value == "auth"
        assert ErrorCategory.AUTHORIZATION.value == "authz"
        assert ErrorCategory.DATABASE.value == "db"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.CONFIGURATION.value == "config"
        assert ErrorCategory.INTERNAL.value == "internal"


class TestErrorCode:
    def test_creation(self):
        ec = ErrorCode("TEST_001", ErrorCategory.VALIDATION, "Test error", 400)
        assert ec.code == "TEST_001"
        assert ec.category == ErrorCategory.VALIDATION
        assert ec.http_status == 400

    def test_default_status(self):
        ec = ErrorCode("TEST_002", ErrorCategory.INTERNAL, "Internal error")
        assert ec.http_status == 500


class TestErrorCodeRegistry:
    def test_val_001_exists(self):
        assert "VAL_001" in ERROR_CODES
        assert ERROR_CODES["VAL_001"].http_status == 400

    def test_auth_001_exists(self):
        assert "AUTH_001" in ERROR_CODES
        assert ERROR_CODES["AUTH_001"].http_status == 401

    def test_db_001_exists(self):
        assert "DB_001" in ERROR_CODES
        assert ERROR_CODES["DB_001"].http_status == 503

    def test_all_codes_have_required_fields(self):
        for code, ec in ERROR_CODES.items():
            assert ec.code == code
            assert isinstance(ec.category, ErrorCategory)
            assert isinstance(ec.message, str)
            assert isinstance(ec.http_status, int)


class TestAppException:
    def test_known_error_code(self):
        e = AppException("VAL_001", "bad input")
        assert e.error.code == "VAL_001"
        assert e.details == "bad input"
        assert "VAL_001" in str(e)

    def test_unknown_error_code(self):
        e = AppException("UNKNOWN_999")
        assert e.error.code == "UNKNOWN_999"
        assert e.error.category == ErrorCategory.INTERNAL

    def test_to_dict(self):
        e = AppException("VAL_001", "bad", {"field": "name"})
        d = e.to_dict()
        assert d["error_code"] == "VAL_001"
        assert d["details"] == "bad"
        assert d["context"] == {"field": "name"}

    def test_without_details(self):
        e = AppException("DB_001")
        assert "DB_001" in str(e)


class TestValidationError:
    def test_creation(self):
        e = ValidationError("Invalid email")
        assert e.error.code == "VAL_001"
        assert e.details == "Invalid email"

    def test_with_field(self):
        e = ValidationError("Required", field="email")
        assert e.context == {"field": "email"}


class TestNotFoundError:
    def test_creation(self):
        e = NotFoundError("person", "p-123")
        assert e.error.code == "DB_003"
        assert "person" in e.details
        assert "p-123" in e.details
        assert e.context["entity_type"] == "person"
        assert e.context["entity_id"] == "p-123"


class TestConnectionError:
    def test_creation(self):
        e = ConnectionError("janusgraph", "timeout")
        assert e.error.code == "DB_001"
        assert e.context["service"] == "janusgraph"
