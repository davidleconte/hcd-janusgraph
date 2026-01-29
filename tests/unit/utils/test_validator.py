"""
Unit Tests for Validator Class
===============================

Tests for the Validator utility class covering all validation methods.

Author: IBM Bob
Date: 2026-01-29
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.python.utils.validation import Validator


class TestValidatorEmail:
    """Test email validation"""
    
    @pytest.mark.parametrize("email,expected", [
        ("valid@example.com", True),
        ("user.name@example.co.uk", True),
        ("user+tag@example.com", True),
        ("invalid@", False),
        ("@example.com", False),
        ("no-at-sign.com", False),
        ("", False),
        ("spaces in@example.com", False),
    ])
    def test_validate_email(self, email, expected):
        """Test email validation with various inputs"""
        assert Validator.validate_email(email) == expected
    
    def test_validate_email_none(self):
        """Test email validation with None"""
        assert Validator.validate_email(None) == False


class TestValidatorPhone:
    """Test phone number validation"""
    
    @pytest.mark.parametrize("phone,expected", [
        ("+1-555-0100", True),
        ("+44-20-1234-5678", True),
        ("555-0100", True),
        ("invalid", False),
        ("", False),
        ("123", False),
    ])
    def test_validate_phone(self, phone, expected):
        """Test phone validation with various inputs"""
        assert Validator.validate_phone(phone) == expected


class TestValidatorIBAN:
    """Test IBAN validation"""
    
    @pytest.mark.parametrize("iban,expected", [
        ("GB82WEST12345698765432", True),
        ("DE89370400440532013000", True),
        ("FR1420041010050500013M02606", True),
        ("INVALID", False),
        ("", False),
        ("GB82WEST", False),  # Too short
    ])
    def test_validate_iban(self, iban, expected):
        """Test IBAN validation"""
        assert Validator.validate_iban(iban) == expected


class TestValidatorSWIFT:
    """Test SWIFT/BIC validation"""
    
    @pytest.mark.parametrize("swift,expected", [
        ("DEUTDEFF", True),
        ("DEUTDEFFXXX", True),
        ("BNPAFRPP", True),
        ("INVALID", False),
        ("", False),
        ("ABC", False),  # Too short
    ])
    def test_validate_swift(self, swift, expected):
        """Test SWIFT/BIC validation"""
        assert Validator.validate_swift(swift) == expected


class TestValidatorAmount:
    """Test amount validation"""
    
    def test_validate_amount_valid(self):
        """Test valid amount"""
        result = Validator.validate_amount(Decimal("100.00"))
        assert result == Decimal("100.00")
        result = Validator.validate_amount(Decimal("0.01"))
        assert result == Decimal("0.01")
    
    def test_validate_amount_negative(self):
        """Test negative amount"""
        from src.python.utils.validation import ValidationError
        with pytest.raises(ValidationError):
            Validator.validate_amount(Decimal("-100.00"))
    
    def test_validate_amount_zero(self):
        """Test zero amount"""
        from src.python.utils.validation import ValidationError
        with pytest.raises(ValidationError):
            Validator.validate_amount(Decimal("0.00"))
    
    def test_validate_amount_with_min_max(self):
        """Test amount with min/max constraints"""
        from src.python.utils.validation import ValidationError
        result = Validator.validate_amount(
            Decimal("100.00"),
            min_amount=Decimal("50.00"),
            max_amount=Decimal("200.00")
        )
        assert result == Decimal("100.00")
        
        with pytest.raises(ValidationError):
            Validator.validate_amount(
                Decimal("10.00"),
                min_amount=50.00
            )


class TestValidatorDate:
    """Test date validation"""
    
    def test_validate_date_valid(self):
        """Test valid date"""
        assert Validator.validate_date("2024-01-01") == True
        assert Validator.validate_date("2024-12-31") == True
    
    def test_validate_date_invalid_format(self):
        """Test invalid date format"""
        assert Validator.validate_date("01/01/2024") == False
        assert Validator.validate_date("invalid") == False
    
    def test_validate_date_future(self):
        """Test future date validation"""
        future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        # Note: validate_date doesn't have allow_future parameter in current implementation
        # This test documents expected behavior for future enhancement
        assert Validator.validate_date(future_date) == True


class TestValidatorSanitization:
    """Test string sanitization"""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization"""
        assert Validator.sanitize_string("Hello World") == "Hello World"
        assert Validator.sanitize_string("  spaces  ") == "spaces"
    
    def test_sanitize_string_sql_injection(self):
        """Test SQL injection prevention"""
        malicious = "'; DROP TABLE users; --"
        sanitized = Validator.sanitize_string(malicious)
        assert "DROP" not in sanitized
        assert "--" not in sanitized
    
    def test_sanitize_string_xss(self):
        """Test XSS prevention"""
        malicious = "<script>alert('XSS')</script>"
        sanitized = Validator.sanitize_string(malicious)
        assert "<script>" not in sanitized
        assert "alert" not in sanitized
    
    def test_sanitize_string_max_length(self):
        """Test max length enforcement"""
        long_string = "a" * 1000
        sanitized = Validator.sanitize_string(long_string, max_length=100)
        assert len(sanitized) <= 100


class TestValidatorSSN:
    """Test SSN validation"""
    
    @pytest.mark.parametrize("ssn,expected", [
        ("123-45-6789", True),
        ("123456789", True),
        ("000-00-0000", False),  # Invalid SSN
        ("123-45-678", False),  # Too short
        ("invalid", False),
    ])
    def test_validate_ssn(self, ssn, expected):
        """Test SSN validation"""
        assert Validator.validate_ssn(ssn) == expected


class TestValidatorCurrency:
    """Test currency code validation"""
    
    @pytest.mark.parametrize("currency,expected", [
        ("USD", True),
        ("EUR", True),
        ("GBP", True),
        ("JPY", True),
        ("INVALID", False),
        ("US", False),  # Too short
        ("", False),
    ])
    def test_validate_currency(self, currency, expected):
        """Test currency code validation"""
        assert Validator.validate_currency(currency) == expected


class TestValidatorAccountNumber:
    """Test account number validation"""
    
    def test_validate_account_number_valid(self):
        """Test valid account numbers"""
        assert Validator.validate_account_number("1234567890") == True
        assert Validator.validate_account_number("0000000001") == True
    
    def test_validate_account_number_invalid(self):
        """Test invalid account numbers"""
        assert Validator.validate_account_number("") == False
        assert Validator.validate_account_number("123") == False  # Too short
        assert Validator.validate_account_number("abc123") == False  # Non-numeric


class TestValidatorIntegration:
    """Integration tests for Validator"""
    
    def test_validate_transaction_data(self):
        """Test validation of complete transaction data"""
        transaction = {
            'from_account': '1234567890',
            'to_account': '0987654321',
            'amount': Decimal('1000.00'),
            'currency': 'USD',
            'date': '2024-01-01'
        }
        
        assert Validator.validate_account_number(transaction['from_account']) == True
        assert Validator.validate_account_number(transaction['to_account']) == True
        result = Validator.validate_amount(transaction['amount'])
        assert result == Decimal('1000.00')
        assert Validator.validate_currency(transaction['currency']) == True
        assert Validator.validate_date(transaction['date']) == True
    
    def test_validate_person_data(self):
        """Test validation of complete person data"""
        person = {
            'email': 'john.doe@example.com',
            'phone': '+1-555-0100',
            'ssn': '123-45-6789'
        }
        
        assert Validator.validate_email(person['email']) == True
        assert Validator.validate_phone(person['phone']) == True
        assert Validator.validate_ssn(person['ssn']) == True


# Run tests with: pytest tests/unit/utils/test_validator.py -v

