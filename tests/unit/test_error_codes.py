#!/usr/bin/env python3
"""Tests for error codes module."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.python.utils.error_codes import (
    ERROR_CODES,
    AppException,
    ConnectionError,
    ErrorCategory,
    ErrorCode,
    NotFoundError,
    ValidationError,
)


class TestErrorCode:
    def test_error_code_attributes(self):
        code = ErrorCode("TEST_001", ErrorCategory.VALIDATION, "Test message", 400)
        assert code.code == "TEST_001"
        assert code.category == ErrorCategory.VALIDATION
        assert code.message == "Test message"
        assert code.http_status == 400

    def test_default_http_status(self):
        code = ErrorCode("TEST_002", ErrorCategory.INTERNAL, "Internal error")
        assert code.http_status == 500


class TestErrorCodesRegistry:
    def test_validation_errors_exist(self):
        assert "VAL_001" in ERROR_CODES
        assert "VAL_002" in ERROR_CODES
        assert ERROR_CODES["VAL_001"].http_status == 400

    def test_auth_errors_exist(self):
        assert "AUTH_001" in ERROR_CODES
        assert "AUTH_003" in ERROR_CODES
        assert ERROR_CODES["AUTH_001"].http_status == 401
        assert ERROR_CODES["AUTH_003"].http_status == 403

    def test_database_errors_exist(self):
        assert "DB_001" in ERROR_CODES
        assert "DB_003" in ERROR_CODES
        assert ERROR_CODES["DB_003"].http_status == 404


class TestAppException:
    def test_known_error_code(self):
        exc = AppException("VAL_001", "Invalid email format")
        assert exc.error.code == "VAL_001"
        assert "Invalid email format" in str(exc)

    def test_unknown_error_code(self):
        exc = AppException("UNKNOWN_999", "Something went wrong")
        assert exc.error.code == "UNKNOWN_999"
        assert exc.error.http_status == 500

    def test_to_dict(self):
        exc = AppException("DB_003", "User not found", {"user_id": "123"})
        result = exc.to_dict()
        assert result["error_code"] == "DB_003"
        assert result["details"] == "User not found"
        assert result["context"]["user_id"] == "123"


class TestSpecificExceptions:
    def test_validation_error(self):
        exc = ValidationError("Email required", field="email")
        assert exc.error.code == "VAL_001"
        assert exc.context["field"] == "email"

    def test_not_found_error(self):
        exc = NotFoundError("User", "user-123")
        assert exc.error.code == "DB_003"
        assert "User 'user-123' not found" in str(exc)

    def test_connection_error(self):
        exc = ConnectionError("JanusGraph", "Connection refused")
        assert exc.error.code == "DB_001"
        assert exc.context["service"] == "JanusGraph"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
