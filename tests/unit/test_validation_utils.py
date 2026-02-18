"""Tests for src.python.utils.validation module."""

from decimal import Decimal

import pytest

from src.python.utils.validation import (
    MAX_ACCOUNT_ID_LENGTH,
    MAX_AMOUNT,
    MAX_QUERY_LENGTH,
    MAX_STRING_LENGTH,
    MIN_ACCOUNT_ID_LENGTH,
    MIN_AMOUNT,
    ValidationError,
    Validator,
)


class TestValidateAccountId:
    def test_valid_id(self):
        assert Validator.validate_account_id("ACC-12345") == "ACC-12345"

    def test_valid_with_underscore(self):
        assert Validator.validate_account_id("ACC_12345") == "ACC_12345"

    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            Validator.validate_account_id("")

    def test_none_raises(self):
        with pytest.raises(ValidationError):
            Validator.validate_account_id(None)

    def test_too_short(self):
        with pytest.raises(ValidationError):
            Validator.validate_account_id("AB")

    def test_too_long(self):
        with pytest.raises(ValidationError):
            Validator.validate_account_id("A" * 60)

    def test_lowercase_rejected(self):
        with pytest.raises(ValidationError):
            Validator.validate_account_id("acc-12345")

    def test_special_chars_rejected(self):
        with pytest.raises(ValidationError):
            Validator.validate_account_id("ACC@12345")


class TestValidateAmount:
    def test_valid_amount(self):
        result = Validator.validate_amount(100.50)
        assert result == Decimal("100.50")

    def test_integer_amount(self):
        result = Validator.validate_amount(100)
        assert result == Decimal("100.00")

    def test_decimal_amount(self):
        result = Validator.validate_amount(Decimal("99.99"))
        assert result == Decimal("99.99")

    def test_below_minimum(self):
        with pytest.raises(ValidationError, match="below minimum"):
            Validator.validate_amount(0.001)

    def test_above_maximum(self):
        with pytest.raises(ValidationError, match="exceeds maximum"):
            Validator.validate_amount(2_000_000_000)

    def test_too_many_decimals(self):
        with pytest.raises(ValidationError, match="decimal places"):
            Validator.validate_amount(10.123)

    def test_invalid_type(self):
        with pytest.raises(ValidationError, match="Invalid amount"):
            Validator.validate_amount("not_a_number")

    def test_custom_range(self):
        result = Validator.validate_amount(5.0, min_amount=1.0, max_amount=10.0)
        assert result == Decimal("5.00")


class TestSanitizeString:
    def test_normal_string(self):
        assert Validator.sanitize_string("hello world") == "hello world"

    def test_removes_control_chars(self):
        result = Validator.sanitize_string("hello\x00world")
        assert "\x00" not in result

    def test_truncates_long_string(self):
        result = Validator.sanitize_string("a" * 150, max_length=100)
        assert len(result) <= 100

    def test_rejects_extremely_long(self):
        with pytest.raises(ValidationError, match="too long"):
            Validator.sanitize_string("a" * 3000, max_length=100)

    def test_not_string_raises(self):
        with pytest.raises(ValidationError, match="Expected string"):
            Validator.sanitize_string(123)

    def test_allow_whitespace(self):
        result = Validator.sanitize_string("line1\nline2", allow_whitespace=True)
        assert "\n" in result

    def test_suspicious_sql_injection(self):
        result = Validator.sanitize_string("DROP TABLE users")
        assert isinstance(result, str)

    def test_suspicious_xss(self):
        result = Validator.sanitize_string("<script>alert(1)</script>")
        assert isinstance(result, str)

    def test_path_traversal(self):
        result = Validator.sanitize_string("../../etc/passwd")
        assert isinstance(result, str)
