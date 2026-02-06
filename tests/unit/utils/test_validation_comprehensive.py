"""
Comprehensive Unit Tests for Validation Module
===============================================

Complete test suite for src/python/utils/validation.py covering:
- Validator class methods
- Standalone validation functions
- Edge cases and error handling
- Security validation

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-29
Phase: Week 3 Days 3-4 - Utils Module Testing
"""

import pytest
from decimal import Decimal, InvalidOperation
from datetime import datetime, date, timedelta
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.python.utils.validation import (
    Validator,
    ValidationError,
    validate_hostname,
    validate_port,
    validate_gremlin_query,
    validate_file_path,
)


class TestValidatorAccountID:
    """Test account ID validation"""

    @pytest.mark.parametrize("account_id,should_pass", [
        ("ACC-12345", True),
        ("USER_001", True),
        ("A1B2C3D4E5", True),
        ("12345-ABCDE", True),
        ("VALID_ID-123", True),
        ("", False),  # Empty
        ("abc", False),  # Too short (< 5)
        ("a" * 51, False),  # Too long (> 50)
        ("invalid@id", False),  # Invalid char
        ("lower-case", False),  # Lowercase not allowed
        ("spaces here", False),  # Spaces not allowed
    ])
    def test_validate_account_id(self, account_id, should_pass):
        """Test account ID validation with various inputs"""
        if should_pass:
            result = Validator.validate_account_id(account_id)
            assert result == account_id
        else:
            with pytest.raises(ValidationError):
                Validator.validate_account_id(account_id)

    def test_validate_account_id_none(self):
        """Test account ID validation with None"""
        with pytest.raises(ValidationError, match="must be a non-empty string"):
            Validator.validate_account_id(None)

    def test_validate_account_id_not_string(self):
        """Test account ID validation with non-string"""
        with pytest.raises(ValidationError):
            Validator.validate_account_id(12345)


class TestValidatorAmount:
    """Test amount validation"""

    def test_validate_amount_valid_float(self):
        """Test amount validation with valid float"""
        result = Validator.validate_amount(100.50)
        assert result == Decimal('100.50')
        assert isinstance(result, Decimal)

    def test_validate_amount_valid_int(self):
        """Test amount validation with valid integer"""
        result = Validator.validate_amount(100)
        assert result == Decimal('100.00')

    def test_validate_amount_valid_decimal(self):
        """Test amount validation with Decimal"""
        result = Validator.validate_amount(Decimal('99.99'))
        assert result == Decimal('99.99')

    def test_validate_amount_valid_string(self):
        """Test amount validation with string"""
        result = Validator.validate_amount('50.25')
        assert result == Decimal('50.25')

    def test_validate_amount_below_minimum(self):
        """Test amount below minimum"""
        with pytest.raises(ValidationError, match="below minimum"):
            Validator.validate_amount(0.001, min_amount=0.01)

    def test_validate_amount_above_maximum(self):
        """Test amount above maximum"""
        with pytest.raises(ValidationError, match="exceeds maximum"):
            Validator.validate_amount(2000000000, max_amount=1000000000)

    def test_validate_amount_too_many_decimals(self):
        """Test amount with too many decimal places"""
        with pytest.raises(ValidationError, match="too many decimal places"):
            Validator.validate_amount(Decimal('10.123'))

    def test_validate_amount_invalid_format(self):
        """Test amount with invalid format"""
        with pytest.raises(ValidationError, match="Invalid amount format"):
            Validator.validate_amount("invalid")

    def test_validate_amount_none(self):
        """Test amount validation with None"""
        with pytest.raises(ValidationError):
            Validator.validate_amount(None)

    def test_validate_amount_quantization(self):
        """Test amount is quantized to 2 decimal places"""
        result = Validator.validate_amount(10.1)
        assert result == Decimal('10.10')


class TestValidatorSanitizeString:
    """Test string sanitization"""

    def test_sanitize_string_basic(self):
        """Test basic string sanitization"""
        result = Validator.sanitize_string("  Hello World  ")
        assert result == "Hello World"

    def test_sanitize_string_control_chars(self):
        """Test removal of control characters"""
        result = Validator.sanitize_string("Hello\x00World\x01")
        assert result == "HelloWorld"

    def test_sanitize_string_max_length(self):
        """Test string truncation at max length"""
        long_string = "a" * 150  # Must be < 2*max_length to avoid DoS error
        result = Validator.sanitize_string(long_string, max_length=100)
        assert len(result) == 100

    def test_sanitize_string_too_long_before_sanitization(self):
        """Test string that's too long before sanitization"""
        very_long = "a" * 3000
        with pytest.raises(ValidationError, match="String too long"):
            Validator.sanitize_string(very_long, max_length=100)

    def test_sanitize_string_with_whitespace(self):
        """Test sanitization allowing whitespace"""
        result = Validator.sanitize_string("Line1\nLine2\tTab", allow_whitespace=True)
        assert "Line1" in result
        assert "Line2" in result

    def test_sanitize_string_with_allowed_chars(self):
        """Test sanitization with allowed characters"""
        result = Validator.sanitize_string("user@example.com", allow_chars='@.')
        assert result == "user@example.com"

    def test_sanitize_string_not_string(self):
        """Test sanitization with non-string input"""
        with pytest.raises(ValidationError, match="Expected string"):
            Validator.sanitize_string(12345)


class TestValidatorEmail:
    """Test email validation"""

    @pytest.mark.parametrize("email,expected", [
        ("valid@example.com", "valid@example.com"),
        ("user.name@example.co.uk", "user.name@example.co.uk"),
        ("user+tag@example.com", "user+tag@example.com"),
        ("test_user@sub.domain.com", "test_user@sub.domain.com"),
        ("123@example.com", "123@example.com"),
    ])
    def test_validate_email_valid(self, email, expected):
        """Test email validation with valid emails"""
        result = Validator.validate_email(email)
        assert result == expected.lower()

    @pytest.mark.parametrize("email", [
        "invalid@",
        "@example.com",
        "no-at-sign.com",
        "",
        "spaces in@example.com",
        "missing.domain@",
        "@",
        "user@",
        "user@@example.com",
    ])
    def test_validate_email_invalid(self, email):
        """Test email validation with invalid emails"""
        with pytest.raises(ValidationError):
            Validator.validate_email(email)

    def test_validate_email_too_long(self):
        """Test email that's too long"""
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValidationError, match="too long"):
            Validator.validate_email(long_email)

    def test_validate_email_local_too_long(self):
        """Test email with local part too long"""
        long_local = "a" * 70 + "@example.com"
        with pytest.raises(ValidationError, match="local part too long"):
            Validator.validate_email(long_local)

    def test_validate_email_none(self):
        """Test email validation with None"""
        with pytest.raises(ValidationError, match="must be a non-empty string"):
            Validator.validate_email(None)

    def test_validate_email_lowercase_conversion(self):
        """Test email is converted to lowercase"""
        result = Validator.validate_email("USER@EXAMPLE.COM")
        assert result == "user@example.com"


class TestValidatorDate:
    """Test date validation"""

    def test_validate_date_datetime_object(self):
        """Test date validation with datetime object"""
        dt = datetime(2024, 1, 15, 10, 30)
        result = Validator.validate_date(dt)
        assert result == date(2024, 1, 15)
        assert isinstance(result, date)

    def test_validate_date_date_object(self):
        """Test date validation with date object"""
        d = date(2024, 1, 15)
        result = Validator.validate_date(d)
        assert result == d

    def test_validate_date_iso_string(self):
        """Test date validation with ISO format string"""
        result = Validator.validate_date("2024-01-15")
        assert result == date(2024, 1, 15)

    @pytest.mark.parametrize("date_str,expected", [
        ("2024-01-15", date(2024, 1, 15)),
        ("01/15/2024", date(2024, 1, 15)),
        ("15/01/2024", date(2024, 1, 15)),
    ])
    def test_validate_date_various_formats(self, date_str, expected):
        """Test date validation with various string formats"""
        result = Validator.validate_date(date_str)
        assert result == expected

    def test_validate_date_invalid_format(self):
        """Test date validation with invalid format"""
        with pytest.raises(ValidationError, match="Invalid date format"):
            Validator.validate_date("invalid-date")

    def test_validate_date_invalid_type(self):
        """Test date validation with invalid type"""
        with pytest.raises(ValidationError, match="Invalid date type"):
            Validator.validate_date(12345)

    def test_validate_date_with_min_date(self):
        """Test date validation with minimum date"""
        min_date = date(2024, 1, 1)
        result = Validator.validate_date("2024-01-15", min_date=min_date)
        assert result == date(2024, 1, 15)

    def test_validate_date_before_min(self):
        """Test date before minimum"""
        min_date = date(2024, 1, 1)
        with pytest.raises(ValidationError, match="before minimum"):
            Validator.validate_date("2023-12-31", min_date=min_date)

    def test_validate_date_with_max_date(self):
        """Test date validation with maximum date"""
        max_date = date(2024, 12, 31)
        result = Validator.validate_date("2024-06-15", max_date=max_date)
        assert result == date(2024, 6, 15)

    def test_validate_date_after_max(self):
        """Test date after maximum"""
        max_date = date(2024, 12, 31)
        with pytest.raises(ValidationError, match="after maximum"):
            Validator.validate_date("2025-01-01", max_date=max_date)


class TestValidatorGremlinQuery:
    """Test Gremlin query validation"""

    def test_validate_gremlin_query_valid(self):
        """Test valid Gremlin query"""
        query = "g.V().count()"
        result = Validator.validate_gremlin_query(query)
        assert result == query

    def test_validate_gremlin_query_empty(self):
        """Test empty query"""
        with pytest.raises(ValidationError, match="must be a non-empty string"):
            Validator.validate_gremlin_query("")

    def test_validate_gremlin_query_none(self):
        """Test None query"""
        with pytest.raises(ValidationError, match="must be a non-empty string"):
            Validator.validate_gremlin_query(None)

    def test_validate_gremlin_query_too_long(self):
        """Test query exceeding max length"""
        long_query = "g.V()" * 5000
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            Validator.validate_gremlin_query(long_query)

    @pytest.mark.parametrize("dangerous_query,pattern", [
        ("g.V().drop()", "drop"),
        ("system('rm -rf /')", "system"),
        ("eval('malicious code')", "eval"),
        ("script('bad')", "script"),
        ("inject('sql')", "inject"),
        ("g.V().__class__", "double underscore"),
        ("'; DROP TABLE users--", "SQL injection"),
        ("1=1 OR 1=1", "SQL injection pattern"),
        ("UNION SELECT * FROM", "SQL injection pattern"),
        ("<script>alert('xss')</script>", "XSS attempt"),
        ("javascript:alert(1)", "JavaScript injection"),
        ("../../etc/passwd", "path traversal"),
    ])
    def test_validate_gremlin_query_dangerous(self, dangerous_query, pattern):
        """Test detection of dangerous operations"""
        with pytest.raises(ValidationError, match="dangerous operation"):
            Validator.validate_gremlin_query(dangerous_query)

    def test_validate_gremlin_query_whitespace_trimmed(self):
        """Test query whitespace is trimmed"""
        query = "  g.V().count()  "
        result = Validator.validate_gremlin_query(query)
        assert result == "g.V().count()"


class TestValidatorSanitizeQuery:
    """Test query sanitization"""

    def test_sanitize_query_removes_single_line_comments(self):
        """Test removal of single-line comments"""
        query = "g.V().count() // This is a comment"
        result = Validator.sanitize_query(query)
        assert "//" not in result
        assert "g.V().count()" in result

    def test_sanitize_query_removes_multi_line_comments(self):
        """Test removal of multi-line comments"""
        query = "g.V() /* comment */ .count()"
        result = Validator.sanitize_query(query)
        assert "/*" not in result
        assert "*/" not in result

    def test_sanitize_query_validates_after_sanitization(self):
        """Test query is validated after sanitization"""
        query = "g.V().drop() // dangerous"
        with pytest.raises(ValidationError, match="dangerous operation"):
            Validator.sanitize_query(query)


class TestValidatorPort:
    """Test port validation"""

    def test_validate_port_valid(self):
        """Test valid port number"""
        result = Validator.validate_port(8080)
        assert result == 8080

    def test_validate_port_string(self):
        """Test port as string"""
        result = Validator.validate_port("8080")
        assert result == 8080

    def test_validate_port_privileged_allowed(self):
        """Test privileged port with allow_privileged=True"""
        result = Validator.validate_port(80, allow_privileged=True)
        assert result == 80

    def test_validate_port_privileged_not_allowed(self):
        """Test privileged port without allow_privileged"""
        with pytest.raises(ValidationError, match="privileged"):
            Validator.validate_port(80, allow_privileged=False)

    def test_validate_port_below_minimum(self):
        """Test port below minimum (0)"""
        with pytest.raises(ValidationError, match="must be between"):
            Validator.validate_port(0)

    def test_validate_port_above_maximum(self):
        """Test port above maximum (65535)"""
        with pytest.raises(ValidationError, match="must be between"):
            Validator.validate_port(70000)

    def test_validate_port_invalid_format(self):
        """Test port with invalid format"""
        with pytest.raises(ValidationError, match="Invalid port format"):
            Validator.validate_port("invalid")

    def test_validate_port_negative(self):
        """Test negative port"""
        with pytest.raises(ValidationError, match="must be between"):
            Validator.validate_port(-1)


class TestStandaloneValidateHostname:
    """Test standalone hostname validation function"""

    @pytest.mark.parametrize("hostname", [
        "localhost",
        "example.com",
        "sub.domain.example.com",
        "192.168.1.1",
        "my-server",
        "server123",
    ])
    def test_validate_hostname_valid(self, hostname):
        """Test valid hostnames"""
        result = validate_hostname(hostname)
        assert result == hostname

    @pytest.mark.parametrize("hostname", [
        "",
        " ",
        "a" * 254,  # Too long
        "invalid..domain",
        "-invalid",
        "invalid-",
        "invalid_domain",  # Underscore not allowed
    ])
    def test_validate_hostname_invalid(self, hostname):
        """Test invalid hostnames"""
        with pytest.raises(ValidationError):
            validate_hostname(hostname)

    def test_validate_hostname_none(self):
        """Test hostname validation with None"""
        with pytest.raises(ValidationError):
            validate_hostname(None)


class TestStandaloneValidatePort:
    """Test standalone port validation function"""

    def test_validate_port_function(self):
        """Test standalone validate_port function"""
        result = validate_port(8080, allow_privileged=True)
        assert result == 8080


class TestStandaloneValidateGremlinQuery:
    """Test standalone Gremlin query validation function"""

    def test_validate_gremlin_query_function(self):
        """Test standalone validate_gremlin_query function"""
        result = validate_gremlin_query("g.V().count()")
        assert result == "g.V().count()"


class TestStandaloneValidateFilePath:
    """Test standalone file path validation function"""

    def test_validate_file_path_valid(self, tmp_path):
        """Test valid file path"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        result = validate_file_path(str(test_file), must_exist=True)
        assert result == str(test_file)

    def test_validate_file_path_not_exists(self):
        """Test file path that doesn't exist"""
        with pytest.raises(ValidationError, match="does not exist"):
            validate_file_path("/nonexistent/file.txt", must_exist=True)

    def test_validate_file_path_not_exists_allowed(self):
        """Test file path that doesn't exist but is allowed"""
        result = validate_file_path("/some/new/file.txt", must_exist=False)
        assert result == "/some/new/file.txt"

    def test_validate_file_path_too_long(self):
        """Test file path that's too long"""
        long_path = "/" + "a" * 5000
        with pytest.raises(ValidationError, match="too long"):
            validate_file_path(long_path)

    def test_validate_file_path_empty(self):
        """Test empty file path"""
        with pytest.raises(ValidationError, match="must be a non-empty string"):
            validate_file_path("")


class TestValidationErrorException:
    """Test ValidationError exception"""

    def test_validation_error_creation(self):
        """Test creating ValidationError"""
        error = ValidationError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_validation_error_raise(self):
        """Test raising ValidationError"""
        with pytest.raises(ValidationError, match="Test message"):
            raise ValidationError("Test message")


