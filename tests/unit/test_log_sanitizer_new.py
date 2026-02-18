"""Tests for src.python.utils.log_sanitizer module."""

import logging

import pytest

from src.python.utils.log_sanitizer import (
    AllowPIILogging,
    PIISanitizer,
    get_secure_logger,
    sanitize_for_logging,
    setup_secure_logging,
)


class TestPIISanitizer:
    def test_init(self):
        s = PIISanitizer()
        assert s is not None

    def test_init_with_ip_redaction(self):
        s = PIISanitizer(redact_ip=True)
        assert "ip_address" in s.patterns

    def test_init_without_ip_redaction(self):
        s = PIISanitizer(redact_ip=False)
        assert "ip_address" not in s.patterns

    def test_sanitize_email(self):
        s = PIISanitizer()
        result = s.sanitize("Email: user@example.com")
        assert "user@example.com" not in result
        assert "EMAIL_REDACTED" in result

    def test_sanitize_ssn(self):
        s = PIISanitizer()
        result = s.sanitize("SSN: 123-45-6789")
        assert "123-45-6789" not in result

    def test_sanitize_credit_card(self):
        s = PIISanitizer()
        result = s.sanitize("Card: 4111 1111 1111 1111")
        assert "4111" not in result

    def test_sanitize_account_id(self):
        s = PIISanitizer()
        result = s.sanitize("Account: ACC-12345")
        assert "ACC-12345" not in result

    def test_sanitize_ip(self):
        s = PIISanitizer(redact_ip=True)
        result = s.sanitize("IP: 192.168.1.1")
        assert "192.168.1.1" not in result

    def test_sanitize_no_pii(self):
        s = PIISanitizer()
        assert s.sanitize("hello world") == "hello world"

    def test_sanitize_empty(self):
        s = PIISanitizer()
        assert s.sanitize("") == ""

    def test_additional_patterns(self):
        s = PIISanitizer(additional_patterns={"custom": (r"SECRET-\w+", "[CUSTOM_REDACTED]")})
        result = s.sanitize("Key: SECRET-abc123")
        assert "SECRET-abc123" not in result

    def test_filter_record(self):
        s = PIISanitizer()
        record = logging.LogRecord("test", logging.INFO, "", 0, "Email: test@test.com", (), None)
        assert s.filter(record) is True
        assert "test@test.com" not in record.msg

    def test_filter_record_dict_args(self):
        s = PIISanitizer()
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        record.args = {"key": "user@example.com"}
        s.filter(record)
        assert "user@example.com" not in str(record.args)

    def test_filter_record_tuple_args(self):
        s = PIISanitizer()
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "msg %s", ("user@example.com",), None
        )
        s.filter(record)
        assert "user@example.com" not in str(record.args)


class TestSanitizeForLogging:
    def test_basic(self):
        result = sanitize_for_logging("Email: test@test.com")
        assert "test@test.com" not in result

    def test_with_ip(self):
        result = sanitize_for_logging("IP: 10.0.0.1", redact_ip=True)
        assert "10.0.0.1" not in result


class TestAllowPIILogging:
    def test_context_manager(self):
        with AllowPIILogging():
            pass


class TestSetupSecureLogging:
    def test_setup(self):
        import logging

        original_handlers = logging.root.handlers[:]
        original_level = logging.root.level
        try:
            setup_secure_logging(level="WARNING")
        finally:
            logging.root.handlers = original_handlers
            logging.root.level = original_level


class TestGetSecureLogger:
    def test_get_logger(self):
        logger = get_secure_logger("test_module")
        assert isinstance(logger, logging.Logger)
