"""Tests for log_sanitizer PII protection."""

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
    def test_redacts_email(self):
        s = PIISanitizer()
        assert s.sanitize("contact john@example.com now") == "contact [EMAIL_REDACTED] now"

    def test_redacts_ssn(self):
        s = PIISanitizer()
        assert "[SSN_REDACTED]" in s.sanitize("SSN: 123-45-6789")

    def test_redacts_credit_card(self):
        s = PIISanitizer()
        assert "[CARD_REDACTED]" in s.sanitize("Card: 4111 1111 1111 1111")

    def test_redacts_phone(self):
        s = PIISanitizer()
        assert "[PHONE_REDACTED]" in s.sanitize("Call 555-123-4567")

    def test_redacts_account_id(self):
        s = PIISanitizer()
        assert "[ACCOUNT_REDACTED]" in s.sanitize("Account ACC-99887")

    def test_ip_not_redacted_by_default(self):
        s = PIISanitizer()
        assert "192.168.1.1" in s.sanitize("IP: 192.168.1.1")

    def test_ip_redacted_when_enabled(self):
        s = PIISanitizer(redact_ip=True)
        assert "[IP_REDACTED]" in s.sanitize("IP: 192.168.1.1")

    def test_empty_string(self):
        s = PIISanitizer()
        assert s.sanitize("") == ""

    def test_additional_patterns(self):
        s = PIISanitizer(additional_patterns={"custom": (r"SECRET-\d+", "[CUSTOM_REDACTED]")})
        assert "[CUSTOM_REDACTED]" in s.sanitize("Token SECRET-42")

    def test_filter_sanitizes_message(self):
        s = PIISanitizer()
        record = logging.LogRecord("test", logging.INFO, "", 0, "email: a@b.com", None, None)
        s.filter(record)
        assert "[EMAIL_REDACTED]" in record.msg

    def test_filter_sanitizes_tuple_args(self):
        s = PIISanitizer()
        record = logging.LogRecord("test", logging.INFO, "", 0, "info %s", ("a@b.com",), None)
        s.filter(record)
        assert "[EMAIL_REDACTED]" in record.args[0]

    def test_filter_sanitizes_dict_args(self):
        s = PIISanitizer()
        record = logging.LogRecord("test", logging.INFO, "", 0, "info", None, None)
        record.args = {"email": "a@b.com"}
        s.filter(record)
        assert "[EMAIL_REDACTED]" in record.args["email"]

    def test_filter_preserves_numeric_tuple_args(self):
        s = PIISanitizer()
        record = logging.LogRecord("test", logging.INFO, "", 0, "status %d", (200,), None)
        s.filter(record)
        assert record.args[0] == 200

    def test_filter_returns_true(self):
        s = PIISanitizer()
        record = logging.LogRecord("test", logging.INFO, "", 0, "safe", None, None)
        assert s.filter(record) is True


class TestHelperFunctions:
    def test_sanitize_for_logging(self):
        result = sanitize_for_logging("email john@test.com here")
        assert "[EMAIL_REDACTED]" in result

    def test_sanitize_for_logging_with_ip(self):
        result = sanitize_for_logging("host 10.0.0.1", redact_ip=True)
        assert "[IP_REDACTED]" in result

    def test_setup_secure_logging(self):
        old_handlers = logging.root.handlers[:]
        old_level = logging.root.level
        try:
            setup_secure_logging(level="WARNING")
            assert logging.root.level == logging.WARNING
        finally:
            logging.root.handlers = old_handlers
            logging.root.level = old_level

    def test_get_secure_logger(self):
        lgr = get_secure_logger("test_module")
        assert isinstance(lgr, logging.Logger)


class TestAllowPIILogging:
    def test_context_removes_and_restores_filters(self):
        handler = logging.StreamHandler()
        pii_filter = PIISanitizer()
        handler.addFilter(pii_filter)
        root = logging.getLogger()
        root.addHandler(handler)

        with AllowPIILogging():
            assert not any(isinstance(f, PIISanitizer) for f in handler.filters)

        assert any(isinstance(f, PIISanitizer) for f in handler.filters)
        root.removeHandler(handler)
