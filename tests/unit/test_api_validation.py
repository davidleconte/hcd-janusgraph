"""
Unit Tests for API Input Validation
====================================

Tests Pydantic field validators for security vulnerabilities:
- SQL injection prevention
- XSS prevention
- Path traversal prevention
- Format validation
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.python.api.models import StructuringAlertRequest, UBORequest


class TestUBORequestValidation:
    """Test UBORequest input validation."""

    def test_valid_company_id(self):
        """Valid company IDs should pass validation."""
        valid_ids = [
            "COMP-12345",
            "ABC123",
            "TEST_COMPANY_001",
            "A1B2C3",
        ]
        for company_id in valid_ids:
            request = UBORequest(company_id=company_id)
            assert request.company_id == company_id

    def test_company_id_too_short(self):
        """Company IDs shorter than 5 characters should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UBORequest(company_id="ABC")
        assert "company_id" in str(exc_info.value)

    def test_company_id_too_long(self):
        """Company IDs longer than 50 characters should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UBORequest(company_id="A" * 51)
        assert "company_id" in str(exc_info.value)

    def test_company_id_sql_injection_attempt(self):
        """SQL injection attempts should be rejected."""
        malicious_ids = [
            "'; DROP TABLE companies; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
        ]
        for malicious_id in malicious_ids:
            with pytest.raises(ValidationError):
                UBORequest(company_id=malicious_id)

    def test_company_id_xss_attempt(self):
        """XSS attempts should be rejected."""
        malicious_ids = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "';alert(String.fromCharCode(88,83,83))//",
        ]
        for malicious_id in malicious_ids:
            with pytest.raises(ValidationError):
                UBORequest(company_id=malicious_id)

    def test_company_id_path_traversal_attempt(self):
        """Path traversal attempts should be rejected."""
        malicious_ids = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//....//etc/passwd",
        ]
        for malicious_id in malicious_ids:
            with pytest.raises(ValidationError):
                UBORequest(company_id=malicious_id)

    def test_company_id_special_characters(self):
        """Special characters (except hyphen/underscore) should be rejected."""
        invalid_ids = [
            "comp@ny",
            "comp#any",
            "comp$any",
            "comp%any",
            "comp&any",
            "comp*any",
        ]
        for invalid_id in invalid_ids:
            with pytest.raises(ValidationError):
                UBORequest(company_id=invalid_id)

    def test_max_depth_boundaries(self):
        """Max depth should be between 1 and 20."""
        # Valid boundaries
        UBORequest(company_id="COMP-123", max_depth=1)
        UBORequest(company_id="COMP-123", max_depth=20)

        # Invalid boundaries
        with pytest.raises(ValidationError):
            UBORequest(company_id="COMP-123", max_depth=0)
        with pytest.raises(ValidationError):
            UBORequest(company_id="COMP-123", max_depth=21)

    def test_ownership_threshold_boundaries(self):
        """Ownership threshold should be between 0 and 100."""
        # Valid boundaries
        UBORequest(company_id="COMP-123", ownership_threshold=0.0)
        UBORequest(company_id="COMP-123", ownership_threshold=100.0)

        # Invalid boundaries
        with pytest.raises(ValidationError):
            UBORequest(company_id="COMP-123", ownership_threshold=-0.1)
        with pytest.raises(ValidationError):
            UBORequest(company_id="COMP-123", ownership_threshold=100.1)


class TestStructuringAlertRequestValidation:
    """Test StructuringAlertRequest input validation."""

    def test_valid_account_id(self):
        """Valid account IDs should pass validation."""
        valid_ids = [
            "ACC-12345",
            "ACCOUNT123",
            "TEST_ACCOUNT_001",
        ]
        for account_id in valid_ids:
            request = StructuringAlertRequest(account_id=account_id)
            assert request.account_id == account_id

    def test_account_id_optional(self):
        """Account ID should be optional."""
        request = StructuringAlertRequest()
        assert request.account_id is None

    def test_account_id_sql_injection_attempt(self):
        """SQL injection attempts should be rejected."""
        malicious_ids = [
            "'; DELETE FROM accounts; --",
            "1' OR '1'='1",
            "admin'--",
        ]
        for malicious_id in malicious_ids:
            with pytest.raises(ValidationError):
                StructuringAlertRequest(account_id=malicious_id)

    def test_threshold_amount_validation(self):
        """Threshold amount should be validated for precision and range."""
        # Valid amounts
        StructuringAlertRequest(threshold_amount=0.01)
        StructuringAlertRequest(threshold_amount=10000.00)
        StructuringAlertRequest(threshold_amount=999999999.99)

        # Invalid amounts
        with pytest.raises(ValidationError):
            StructuringAlertRequest(threshold_amount=0.0)  # Too small
        with pytest.raises(ValidationError):
            StructuringAlertRequest(threshold_amount=-100.0)  # Negative
        with pytest.raises(ValidationError):
            StructuringAlertRequest(threshold_amount=1_000_000_001.0)  # Too large

    def test_threshold_amount_decimal_precision(self):
        """Threshold amount should handle decimal precision correctly."""
        request = StructuringAlertRequest(threshold_amount=10000.50)
        assert request.threshold_amount == 10000.50

    def test_time_window_boundaries(self):
        """Time window should be between 1 and 90 days."""
        # Valid boundaries
        StructuringAlertRequest(time_window_days=1)
        StructuringAlertRequest(time_window_days=90)

        # Invalid boundaries
        with pytest.raises(ValidationError):
            StructuringAlertRequest(time_window_days=0)
        with pytest.raises(ValidationError):
            StructuringAlertRequest(time_window_days=91)

    def test_min_transaction_count_boundaries(self):
        """Min transaction count should be between 1 and 1000."""
        # Valid boundaries
        StructuringAlertRequest(min_transaction_count=1)
        StructuringAlertRequest(min_transaction_count=1000)

        # Invalid boundaries
        with pytest.raises(ValidationError):
            StructuringAlertRequest(min_transaction_count=0)
        with pytest.raises(ValidationError):
            StructuringAlertRequest(min_transaction_count=1001)

    def test_pagination_boundaries(self):
        """Pagination parameters should be validated."""
        # Valid pagination
        StructuringAlertRequest(offset=0, limit=1)
        StructuringAlertRequest(offset=100, limit=500)

        # Invalid pagination
        with pytest.raises(ValidationError):
            StructuringAlertRequest(offset=-1)  # Negative offset
        with pytest.raises(ValidationError):
            StructuringAlertRequest(limit=0)  # Zero limit
        with pytest.raises(ValidationError):
            StructuringAlertRequest(limit=501)  # Limit too high


class TestValidationErrorMessages:
    """Test that validation errors provide clear messages."""

    def test_company_id_error_message_clarity(self):
        """Validation errors should provide clear, actionable messages."""
        with pytest.raises(ValidationError) as exc_info:
            UBORequest(company_id="<script>")
        error_msg = str(exc_info.value)
        assert "company_id" in error_msg.lower()

    def test_threshold_amount_error_message(self):
        """Amount validation errors should be clear."""
        with pytest.raises(ValidationError) as exc_info:
            StructuringAlertRequest(threshold_amount=-100.0)
        error_msg = str(exc_info.value)
        assert "threshold_amount" in error_msg.lower()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_in_company_id(self):
        """Unicode characters should be rejected."""
        with pytest.raises(ValidationError):
            UBORequest(company_id="COMP-™®©")

    def test_null_bytes_in_input(self):
        """Null bytes should be rejected."""
        with pytest.raises(ValidationError):
            UBORequest(company_id="COMP\x00123")

    def test_whitespace_handling(self):
        """Leading/trailing whitespace should be handled."""
        # Whitespace in middle is rejected by pattern
        with pytest.raises(ValidationError):
            UBORequest(company_id="COMP 123")

    def test_case_sensitivity(self):
        """IDs should preserve case (uppercase only per pattern)."""
        request = UBORequest(company_id="COMP-123")
        assert request.company_id == "COMP-123"


# Made with Bob
