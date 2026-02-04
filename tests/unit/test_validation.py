"""
File: test_validation.py
Created: 2026-01-28
Purpose: Unit tests for validation utilities
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/python'))

from utils.validation import Validator, ValidationError


class TestHostnameValidation:
    """Test hostname validation"""
    
    def test_valid_hostname(self):
        """Test valid hostnames"""
        assert Validator.validate_hostname('localhost')
        assert Validator.validate_hostname('example.com')
        assert Validator.validate_hostname('sub.example.com')
        assert Validator.validate_hostname('my-server-01')
    
    def test_valid_ipv4(self):
        """Test valid IPv4 addresses"""
        assert Validator.validate_hostname('127.0.0.1')
        assert Validator.validate_hostname('192.168.1.1')
        assert Validator.validate_hostname('10.0.0.1')
    
    def test_valid_ipv6(self):
        """Test valid IPv6 addresses"""
        assert Validator.validate_hostname('::1')
        assert Validator.validate_hostname('2001:db8::1')
    
    def test_invalid_hostname(self):
        """Test invalid hostnames"""
        with pytest.raises(ValidationError):
            Validator.validate_hostname('invalid..hostname')
        
        with pytest.raises(ValidationError):
            Validator.validate_hostname('-invalid')
        
        with pytest.raises(ValidationError):
            Validator.validate_hostname('invalid_hostname')
    
    def test_empty_hostname(self):
        """Test empty hostname"""
        with pytest.raises(ValidationError):
            Validator.validate_hostname('')
        
        # Should pass with allow_empty=True
        # Implementation returns empty string, which is falsy, so we compare equality
        assert Validator.validate_hostname('', allow_empty=True) == ''
    def test_hostname_too_long(self):
        """Test hostname exceeding max length"""
        long_hostname = 'a' * 254
        with pytest.raises(ValidationError):
            Validator.validate_hostname(long_hostname)


class TestPortValidation:
    """Test port validation"""
    
    def test_valid_ports(self):
        """Test valid port numbers"""
        assert Validator.validate_port(80, allow_privileged=True)
        assert Validator.validate_port(443, allow_privileged=True)
        assert Validator.validate_port(8080)
        assert Validator.validate_port(65535)
        assert Validator.validate_port('8080')  # String port
    
    def test_invalid_ports(self):
        """Test invalid port numbers"""
        with pytest.raises(ValidationError):
            Validator.validate_port(0)
        
        with pytest.raises(ValidationError):
            Validator.validate_port(65536)
        
        with pytest.raises(ValidationError):
            Validator.validate_port(-1)
        
        with pytest.raises(ValidationError):
            Validator.validate_port('invalid')
    
    def test_privileged_ports(self):
        """Test privileged port handling"""
        # Should raise without allow_privileged
        with pytest.raises(ValidationError):
            Validator.validate_port(80, allow_privileged=False)
        
        # Should pass with allow_privileged
        assert Validator.validate_port(80, allow_privileged=True)


class TestConnectionNameValidation:
    """Test connection name validation"""
    
    def test_valid_names(self):
        """Test valid connection names"""
        assert Validator.validate_connection_name('my-connection')
        assert Validator.validate_connection_name('connection_01')
        assert Validator.validate_connection_name('MyConnection123')
    
    def test_invalid_names(self):
        """Test invalid connection names"""
        with pytest.raises(ValidationError):
            Validator.validate_connection_name('invalid name')  # Space
        
        with pytest.raises(ValidationError):
            Validator.validate_connection_name('invalid@name')  # Special char
        
        with pytest.raises(ValidationError):
            Validator.validate_connection_name('')  # Empty
    
    def test_name_too_long(self):
        """Test connection name exceeding max length"""
        long_name = 'a' * 65
        with pytest.raises(ValidationError):
            Validator.validate_connection_name(long_name)


class TestPasswordValidation:
    """Test password strength validation"""
    
    def test_strong_passwords(self):
        """Test strong passwords"""
        assert Validator.validate_password_strength('MyP@ssw0rd123!')
        assert Validator.validate_password_strength('Str0ng!P@ssword')
        assert Validator.validate_password_strength('C0mpl3x#Pass')
    
    def test_weak_passwords(self):
        """Test weak passwords"""
        # Too short
        with pytest.raises(ValidationError):
            Validator.validate_password_strength('Short1!')
        
        # No uppercase
        with pytest.raises(ValidationError):
            Validator.validate_password_strength('mypassword123!')
        
        # No lowercase
        with pytest.raises(ValidationError):
            Validator.validate_password_strength('MYPASSWORD123!')
        
        # No digit
        with pytest.raises(ValidationError):
            Validator.validate_password_strength('MyPassword!')
        
        # No special character
        with pytest.raises(ValidationError):
            Validator.validate_password_strength('MyPassword123')


class TestURLValidation:
    """Test URL validation"""
    
    def test_valid_urls(self):
        """Test valid URLs"""
        assert Validator.validate_url('http://example.com')
        assert Validator.validate_url('https://example.com:8080')
        assert Validator.validate_url('https://sub.example.com/path')
        assert Validator.validate_url('wss://localhost:8182/gremlin')
    
    def test_invalid_urls(self):
        """Test invalid URLs"""
        with pytest.raises(ValidationError):
            Validator.validate_url('not-a-url')
        
        with pytest.raises(ValidationError):
            Validator.validate_url('ftp://example.com')  # Not in allowed schemes
        
        with pytest.raises(ValidationError):
            Validator.validate_url('')  # Empty
    
    def test_custom_schemes(self):
        """Test custom URL schemes"""
        # Should fail with default schemes
        with pytest.raises(ValidationError):
            Validator.validate_url('ftp://example.com')
        
        # Should pass with custom schemes
        assert Validator.validate_url('ftp://example.com', allowed_schemes=['ftp'])


class TestEmailValidation:
    """Test email validation"""
    
    def test_valid_emails(self):
        """Test valid email addresses"""
        assert Validator.validate_email('user@example.com')
        assert Validator.validate_email('john.doe@company.co.uk')
        assert Validator.validate_email('admin+test@example.org')
    
    def test_invalid_emails(self):
        """Test invalid email addresses"""
        with pytest.raises(ValidationError):
            Validator.validate_email('invalid')
        
        with pytest.raises(ValidationError):
            Validator.validate_email('invalid@')
        
        with pytest.raises(ValidationError):
            Validator.validate_email('@example.com')
        
        with pytest.raises(ValidationError):
            Validator.validate_email('')


class TestStringSanitization:
    """Test string sanitization"""
    def test_sanitize_basic(self):
        """Test basic string sanitization"""
        # Default behavior preserves printable characters including spaces
        assert Validator.sanitize_string('hello world') == 'hello world'
        assert Validator.sanitize_string('test@#$%123') == 'test@#$%123'
        assert Validator.sanitize_string('my-file_name.txt') == 'my-file_name.txt'
    
    def test_sanitize_with_allowed_chars(self):
        """Test sanitization with allowed characters"""
        # Standard range includes ! so it is preserved by default
        result = Validator.sanitize_string('hello world!', allow_chars=' ')
        assert result == 'hello world!'
        
        result = Validator.sanitize_string('test@example.com', allow_chars='@')
        assert result == 'test@example.com'
        assert result == 'test@example.com'


class TestQuerySanitization:
    """Test query sanitization"""
    
    def test_safe_queries(self):
        """Test safe queries"""
        query = "g.V().has('name', 'John').out('knows')"
        assert Validator.sanitize_query(query) == query
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection"""
        with pytest.raises(ValidationError):
            Validator.sanitize_query("g.V(); DROP TABLE users;")
        
        with pytest.raises(ValidationError):
            Validator.sanitize_query("g.V() OR 1=1")
        
        with pytest.raises(ValidationError):
            Validator.sanitize_query("g.V() UNION SELECT * FROM users")
    
    def test_xss_detection(self):
        """Test XSS pattern detection"""
        with pytest.raises(ValidationError):
            Validator.sanitize_query("<script>alert('xss')</script>")
        
        with pytest.raises(ValidationError):
            Validator.sanitize_query("javascript:alert('xss')")
    
    def test_comment_removal(self):
        """Test comment removal"""
        query = "g.V() // This is a comment"
        sanitized = Validator.sanitize_query(query)
        assert '//' not in sanitized


class TestNumericValidation:
    """Test numeric validation"""
    
    def test_valid_numbers(self):
        """Test valid numeric values"""
        assert Validator.validate_numeric(42)
        assert Validator.validate_numeric(3.14)
        assert Validator.validate_numeric('123')
        assert Validator.validate_numeric('-10')
    
    def test_invalid_numbers(self):
        """Test invalid numeric values"""
        with pytest.raises(ValidationError):
            Validator.validate_numeric('not-a-number')
        
        with pytest.raises(ValidationError):
            Validator.validate_numeric('12.34.56')
    
    def test_numeric_range(self):
        """Test numeric range validation"""
        assert Validator.validate_numeric(50, min_value=0, max_value=100)
        
        with pytest.raises(ValidationError):
            Validator.validate_numeric(-10, min_value=0)
        
        with pytest.raises(ValidationError):
            Validator.validate_numeric(150, max_value=100)



class TestFilePathValidation:
    """Test file path validation"""
    
    def test_path_traversal_detection(self):
        """Test path traversal detection"""
        with pytest.raises(ValidationError):
            Validator.validate_file_path('../etc/passwd', must_exist=False)
        
        with pytest.raises(ValidationError):
            Validator.validate_file_path('../../secret', must_exist=False)
    
    def test_empty_path(self):
        """Test empty path"""
        with pytest.raises(ValidationError):
            Validator.validate_file_path('', must_exist=False)


class TestEnvVarValidation:
    """Test environment variable name validation"""
    
    def test_valid_env_vars(self):
        """Test valid environment variable names"""
        assert Validator.validate_env_var_name('MY_VAR')
        assert Validator.validate_env_var_name('DATABASE_URL')
        assert Validator.validate_env_var_name('_PRIVATE_VAR')
    
    def test_invalid_env_vars(self):
        """Test invalid environment variable names"""
        with pytest.raises(ValidationError):
            Validator.validate_env_var_name('my-var')  # Lowercase
        
        with pytest.raises(ValidationError):
            Validator.validate_env_var_name('123VAR')  # Starts with digit
        
        with pytest.raises(ValidationError):
            Validator.validate_env_var_name('MY VAR')  # Space
        
        with pytest.raises(ValidationError):
            Validator.validate_env_var_name('')  # Empty


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

