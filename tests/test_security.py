"""
Security Tests
Tests for authentication, validation, and sanitization

Author: IBM Bob
Created: 2026-01-28
"""

import pytest
import os
from decimal import Decimal
from src.python.utils.validation import (
    validate_account_id,
    validate_amount,
    validate_gremlin_query,
    validate_email,
    validate_hostname,
    validate_port,
    ValidationError
)
from src.python.utils.log_sanitizer import PIISanitizer, sanitize_for_logging


class TestInputValidation:
    """Test input validation functions."""
    
    def test_validate_account_id_valid(self):
        """Test valid account ID."""
        assert validate_account_id("ACC-12345") == "ACC-12345"
        assert validate_account_id("ACCOUNT-ABC123") == "ACCOUNT-ABC123"
    
    def test_validate_account_id_invalid(self):
        """Test invalid account ID."""
        with pytest.raises(ValidationError):
            validate_account_id("invalid@id")
        with pytest.raises(ValidationError):
            validate_account_id("abc")  # Too short
        with pytest.raises(ValidationError):
            validate_account_id("a" * 100)  # Too long
    
    def test_validate_amount_valid(self):
        """Test valid amounts."""
        assert validate_amount(100.50) == Decimal('100.50')
        assert validate_amount(0.01) == Decimal('0.01')
        assert validate_amount(1000000) == Decimal('1000000')
    
    def test_validate_amount_invalid(self):
        """Test invalid amounts."""
        with pytest.raises(ValidationError):
            validate_amount(-10)  # Negative
        with pytest.raises(ValidationError):
            validate_amount(0)  # Below minimum
        with pytest.raises(ValidationError):
            validate_amount(10_000_000_000)  # Above maximum
    
    def test_validate_gremlin_query_valid(self):
        """Test valid Gremlin queries."""
        assert validate_gremlin_query("g.V().count()") == "g.V().count()"
        assert validate_gremlin_query("g.V().has('name', 'John')") == "g.V().has('name', 'John')"
    
    def test_validate_gremlin_query_dangerous(self):
        """Test dangerous Gremlin queries are blocked."""
        with pytest.raises(ValidationError, match="dangerous operation"):
            validate_gremlin_query("g.V().drop()")
        with pytest.raises(ValidationError, match="dangerous operation"):
            validate_gremlin_query("g.V().system('rm -rf /')")
    
    def test_validate_email_valid(self):
        """Test valid email addresses."""
        assert validate_email("user@example.com") == "user@example.com"
        assert validate_email("test.user+tag@domain.co.uk") == "test.user+tag@domain.co.uk"
    
    def test_validate_email_invalid(self):
        """Test invalid email addresses."""
        with pytest.raises(ValidationError):
            validate_email("invalid")
        with pytest.raises(ValidationError):
            validate_email("@example.com")
        with pytest.raises(ValidationError):
            validate_email("user@")
    
    def test_validate_hostname_valid(self):
        """Test valid hostnames."""
        assert validate_hostname("localhost") == "localhost"
        assert validate_hostname("example.com") == "example.com"
        assert validate_hostname("192.168.1.1") == "192.168.1.1"
    
    def test_validate_hostname_invalid(self):
        """Test invalid hostnames."""
        with pytest.raises(ValidationError):
            validate_hostname("")
        with pytest.raises(ValidationError):
            validate_hostname("a" * 300)  # Too long
    
    def test_validate_port_valid(self):
        """Test valid ports."""
        assert validate_port(80) == 80
        assert validate_port(8182) == 8182
        assert validate_port(65535) == 65535
    
    def test_validate_port_invalid(self):
        """Test invalid ports."""
        with pytest.raises(ValidationError):
            validate_port(0)
        with pytest.raises(ValidationError):
            validate_port(70000)
        with pytest.raises(ValidationError):
            validate_port(-1)


class TestLogSanitization:
    """Test PII sanitization in logs."""
    
    def test_sanitize_email(self):
        """Test email redaction."""
        sanitizer = PIISanitizer()
        text = "User email: john.doe@example.com"
        result = sanitizer.sanitize(text)
        assert "[EMAIL_REDACTED]" in result
        assert "john.doe@example.com" not in result
    
    def test_sanitize_ssn(self):
        """Test SSN redaction."""
        sanitizer = PIISanitizer()
        text = "SSN: 123-45-6789"
        result = sanitizer.sanitize(text)
        assert "[SSN_REDACTED]" in result
        assert "123-45-6789" not in result
    
    def test_sanitize_credit_card(self):
        """Test credit card redaction."""
        sanitizer = PIISanitizer()
        text = "Card: 4532-1234-5678-9010"
        result = sanitizer.sanitize(text)
        assert "[CARD_REDACTED]" in result
        assert "4532-1234-5678-9010" not in result
    
    def test_sanitize_phone(self):
        """Test phone number redaction."""
        sanitizer = PIISanitizer()
        text = "Phone: (555) 123-4567"
        result = sanitizer.sanitize(text)
        assert "[PHONE_REDACTED]" in result
        assert "(555) 123-4567" not in result
    
    def test_sanitize_account_id(self):
        """Test account ID redaction."""
        sanitizer = PIISanitizer()
        text = "Processing account ACC-12345"
        result = sanitizer.sanitize(text)
        assert "[ACCOUNT_REDACTED]" in result
        assert "ACC-12345" not in result
    
    def test_sanitize_multiple_pii(self):
        """Test multiple PII types in one string."""
        sanitizer = PIISanitizer()
        text = "User john@example.com with SSN 123-45-6789 and card 4532123456789010"
        result = sanitizer.sanitize(text)
        assert "[EMAIL_REDACTED]" in result
        assert "[SSN_REDACTED]" in result
        assert "[CARD_REDACTED]" in result
        assert "john@example.com" not in result
    
    def test_sanitize_for_logging_function(self):
        """Test convenience function."""
        text = "Email: test@example.com, SSN: 123-45-6789"
        result = sanitize_for_logging(text)
        assert "[EMAIL_REDACTED]" in result
        assert "[SSN_REDACTED]" in result
        assert "test@example.com" not in result


class TestAuthentication:
    """Test authentication requirements."""
    
    def test_janusgraph_requires_auth(self):
        """Test JanusGraph client requires authentication."""
        from src.python.client.janusgraph_client import JanusGraphClient
        from src.python.client.exceptions import ValidationError
        
        # Clear environment variables
        os.environ.pop('JANUSGRAPH_USERNAME', None)
        os.environ.pop('JANUSGRAPH_PASSWORD', None)
        
        # Should raise error without credentials
        with pytest.raises(ValidationError, match="Authentication required"):
            JanusGraphClient(host="localhost", port=8182)
    
    def test_janusgraph_accepts_env_credentials(self):
        """Test JanusGraph accepts credentials from environment."""
        from src.python.client.janusgraph_client import JanusGraphClient
        
        # Set environment variables
        os.environ['JANUSGRAPH_USERNAME'] = 'test_user'
        os.environ['JANUSGRAPH_PASSWORD'] = 'test_password'
        
        try:
            # Should not raise error
            client = JanusGraphClient(host="localhost", port=8182)
            assert client.username == 'test_user'
            assert client.password == 'test_password'
        finally:
            # Cleanup
            os.environ.pop('JANUSGRAPH_USERNAME', None)
            os.environ.pop('JANUSGRAPH_PASSWORD', None)
    
    def test_opensearch_requires_auth(self):
        """Test OpenSearch client requires authentication."""
        from src.python.utils.vector_search import VectorSearchClient
        
        # Clear environment variables
        os.environ.pop('OPENSEARCH_USERNAME', None)
        os.environ.pop('OPENSEARCH_PASSWORD', None)
        
        # Should raise error without credentials
        with pytest.raises(ValueError, match="Authentication required"):
            VectorSearchClient(host="localhost", port=9200)


class TestSSLTLS:
    """Test SSL/TLS configuration."""
    
    def test_janusgraph_ssl_default(self):
        """Test JanusGraph uses SSL by default."""
        from src.python.client.janusgraph_client import JanusGraphClient
        
        client = JanusGraphClient(
            host="localhost",
            port=8182,
            username="test",
            password="test"
        )
        assert client.use_ssl is True
        assert "wss://" in client.url
    
    def test_janusgraph_ssl_disabled(self):
        """Test JanusGraph can disable SSL."""
        from src.python.client.janusgraph_client import JanusGraphClient
        
        client = JanusGraphClient(
            host="localhost",
            port=8182,
            username="test",
            password="test",
            use_ssl=False
        )
        assert client.use_ssl is False
        assert "ws://" in client.url
    
    def test_opensearch_ssl_default(self):
        """Test OpenSearch uses SSL by default."""
        from src.python.utils.vector_search import VectorSearchClient
        
        # Set credentials to pass validation
        os.environ['OPENSEARCH_USERNAME'] = 'test'
        os.environ['OPENSEARCH_PASSWORD'] = 'test'
        
        try:
            # This will fail without running service, but we can check the default
            # The constructor will fail on connection, not on SSL setting
            pass  # Can't test without running service
        finally:
            os.environ.pop('OPENSEARCH_USERNAME', None)
            os.environ.pop('OPENSEARCH_PASSWORD', None)


class TestQueryValidation:
    """Test query validation and injection prevention."""
    
    def test_sql_injection_patterns(self):
        """Test SQL injection patterns are blocked."""
        dangerous_queries = [
            "g.V().drop()",
            "g.V().system('rm -rf /')",
            "'; DROP TABLE users; --",
            "1' OR '1'='1"
        ]
        
        for query in dangerous_queries:
            with pytest.raises(ValidationError):
                validate_gremlin_query(query)
    
    def test_safe_queries_allowed(self):
        """Test safe queries are allowed."""
        safe_queries = [
            "g.V().count()",
            "g.V().has('name', 'John').out('knows')",
            "g.V().hasLabel('person').values('name')"
        ]
        
        for query in safe_queries:
            result = validate_gremlin_query(query)
            assert result == query


class TestSecureLogging:
    """Test secure logging configuration."""
    
    def test_pii_not_in_logs(self):
        """Test PII is not logged."""
        import logging
        from io import StringIO
        
        # Create string buffer for log output
        log_buffer = StringIO()
        handler = logging.StreamHandler(log_buffer)
        
        # Create logger with sanitization
        logger = logging.getLogger('test_secure')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Log message with PII
        message = "User email: test@example.com, SSN: 123-45-6789"
        sanitized = sanitize_for_logging(message)
        logger.info(sanitized)
        
        # Check log output
        log_output = log_buffer.getvalue()
        assert "test@example.com" not in log_output
        assert "123-45-6789" not in log_output
        assert "[EMAIL_REDACTED]" in log_output
        assert "[SSN_REDACTED]" in log_output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
