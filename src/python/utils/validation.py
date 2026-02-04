"""
Input Validation and Sanitization Utilities
Provides secure validation for all user inputs

Author: IBM Bob
Created: 2026-01-28
Updated: 2026-01-28 - Review fixes applied
Phase: Week 1 Remediation - Security Hardening
"""

import re
import os
import ipaddress
import logging
from typing import Any, Optional, Union, List
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Module-level constants for validation limits
MAX_STRING_LENGTH = 1000
MAX_QUERY_LENGTH = 10000
MAX_HOSTNAME_LENGTH = 253
MAX_EMAIL_LENGTH = 254
MAX_EMAIL_LOCAL_LENGTH = 64
MAX_BATCH_SIZE = 10000
MIN_BATCH_SIZE = 1
MAX_PORT = 65535
MIN_PORT = 1
PRIVILEGED_PORT_THRESHOLD = 1024
MAX_ACCOUNT_ID_LENGTH = 50
MIN_ACCOUNT_ID_LENGTH = 5
MIN_AMOUNT = 0.01
MAX_AMOUNT = 1_000_000_000.00
MAX_DECIMAL_PLACES = 2
MAX_CONNECTION_NAME_LENGTH = 64
MIN_PASSWORD_LENGTH = 12
MAX_FILE_PATH_LENGTH = 4096


class ValidationError(Exception):
    """
    Raised when input validation fails.
    
    This exception is raised when user input fails validation checks,
    such as invalid format, out of range values, or security violations.
    Use this instead of ValueError for validation-specific errors to
    distinguish validation failures from other value errors.
    """
    pass


class Validator:
    """
    Centralized validation class providing static methods for input validation.
    
    This class provides a consistent API for all validation operations,
    making it easier to use and test validation logic.
    """
    
    @staticmethod
    def validate_account_id(account_id: str) -> str:
        """
        Validate and sanitize account ID.
        
        Args:
            account_id: Account ID to validate
        
        Returns:
            Validated account ID
        
        Raises:
            ValidationError: If account ID is invalid
        
        Example:
            >>> Validator.validate_account_id("ACC-12345")
            'ACC-12345'
        """
        if not account_id or not isinstance(account_id, str):
            raise ValidationError("Account ID must be a non-empty string")
        
        # Allow alphanumeric, hyphens, underscores
        if not re.match(
            f'^[A-Z0-9\\-_]{{{MIN_ACCOUNT_ID_LENGTH},{MAX_ACCOUNT_ID_LENGTH}}}$',
            account_id
        ):
            raise ValidationError(
                f"Invalid account ID format: {account_id}. "
                f"Must be {MIN_ACCOUNT_ID_LENGTH}-{MAX_ACCOUNT_ID_LENGTH} characters, "
                "uppercase alphanumeric with hyphens/underscores"
            )
        
        return account_id
    
    @staticmethod
    def validate_amount(
        amount: Union[float, Decimal, int],
        min_amount: float = MIN_AMOUNT,
        max_amount: float = MAX_AMOUNT
    ) -> Decimal:
        """
        Validate transaction amount with proper Decimal handling.
        
        Args:
            amount: Amount to validate
            min_amount: Minimum allowed amount
            max_amount: Maximum allowed amount
        
        Returns:
            Validated amount as Decimal
        
        Raises:
            ValidationError: If amount is invalid
        """
        try:
            # Convert to string first to avoid float precision issues
            amount_decimal = Decimal(str(amount))
        except (ValueError, TypeError, InvalidOperation) as e:
            raise ValidationError(f"Invalid amount format: {amount}") from e
        
        # Normalize to remove trailing zeros and check precision
        amount_decimal = amount_decimal.normalize()
        
        if amount_decimal < Decimal(str(min_amount)):
            raise ValidationError(
                f"Amount ${amount_decimal} is below minimum ${min_amount}"
            )
        
        if amount_decimal > Decimal(str(max_amount)):
            raise ValidationError(
                f"Amount ${amount_decimal} exceeds maximum ${max_amount}"
            )
        
        # Check for reasonable precision (max 2 decimal places for currency)
        exponent = amount_decimal.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -MAX_DECIMAL_PLACES:
            raise ValidationError(
                f"Amount has too many decimal places: {amount_decimal}. "
                f"Maximum {MAX_DECIMAL_PLACES} decimal places allowed"
            )
        
        # Quantize to 2 decimal places to handle floating point edge cases
        return amount_decimal.quantize(Decimal('0.01'))
    
    @staticmethod
    def sanitize_string(
        value: str,
        max_length: int = MAX_STRING_LENGTH,
        allow_whitespace: bool = False,
        allow_chars: str = ''
    ) -> str:
        """
        Sanitize string input by removing control characters and limiting length.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            allow_whitespace: Whether to allow newlines and tabs
            allow_chars: Additional characters to allow (e.g., '@' for emails)
        
        Returns:
            Sanitized string
        
        Raises:
            ValidationError: If value is not a string or exceeds max length before sanitization
        """
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value).__name__}")
        
        # Check for suspicious patterns before sanitization (security monitoring)
        suspicious_patterns = [
            (r'(?i)(DROP|DELETE|INSERT|UPDATE|ALTER)\s+(TABLE|DATABASE)', 'SQL injection attempt'),
            (r'<script[^>]*>.*?</script>', 'XSS script tag'),
            (r'javascript:', 'JavaScript protocol'),
            (r'on\w+\s*=', 'Event handler injection'),
            (r'\.\./|\.\.\\', 'Path traversal attempt')
        ]
        
        for pattern, threat_type in suspicious_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(
                    f"Suspicious input detected and will be sanitized - {threat_type}: "
                    f"{value[:100]}{'...' if len(value) > 100 else ''}"
                )
                break
        
        # Check length before sanitization to prevent DoS
        if len(value) > max_length * 2:
            raise ValidationError(
                f"String too long: {len(value)} characters "
                f"(maximum {max_length} after sanitization)"
            )
        
        # Use regex for better performance on large strings
        if allow_whitespace:
            # Keep printable chars, newlines, tabs, and allowed chars
            pattern = f'[^\\x20-\\x7E\\n\\t{re.escape(allow_chars)}]'
        else:
            # Keep only printable chars and allowed chars
            pattern = f'[^\\x20-\\x7E{re.escape(allow_chars)}]'
        
        sanitized = re.sub(pattern, '', value)
        
        # Warn and truncate if exceeds max length
        if len(sanitized) > max_length:
            logger.warning(
                f"String truncated from {len(sanitized)} to {max_length} characters"
            )
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
        
        Returns:
            Validated email address (lowercase)
        
        Raises:
            ValidationError: If email format is invalid
        """
        if not email or not isinstance(email, str):
            raise ValidationError("Email must be a non-empty string")
        
        # Basic email regex (RFC 5322 simplified)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            raise ValidationError(f"Invalid email format: {email}")
        
        # Additional checks
        if len(email) > MAX_EMAIL_LENGTH:
            raise ValidationError(
                f"Email address too long (max {MAX_EMAIL_LENGTH} characters)"
            )
        
        local, domain = email.rsplit('@', 1)
        if len(local) > MAX_EMAIL_LOCAL_LENGTH:
            raise ValidationError(
                f"Email local part too long (max {MAX_EMAIL_LOCAL_LENGTH} characters)"
            )
        
        return email.lower()
    
    @staticmethod
    def validate_date(
        date_value: Union[str, date, datetime],
        min_date: Optional[date] = None,
        max_date: Optional[date] = None
    ) -> date:
        """
        Validate date value.
        
        Args:
            date_value: Date to validate (string, date, or datetime)
            min_date: Minimum allowed date
            max_date: Maximum allowed date
        
        Returns:
            Validated date object
        
        Raises:
            ValidationError: If date is invalid
        """
        # Convert to date object
        if isinstance(date_value, datetime):
            date_obj = date_value.date()
        elif isinstance(date_value, date):
            date_obj = date_value
        elif isinstance(date_value, str):
            try:
                # Try ISO format first
                date_obj = datetime.fromisoformat(date_value).date()
            except ValueError:
                try:
                    # Try common formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            date_obj = datetime.strptime(date_value, fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
                        raise ValueError("No valid format found")
                except ValueError as e:
                    raise ValidationError(f"Invalid date format: {date_value}") from e
        else:
            raise ValidationError(f"Invalid date type: {type(date_value).__name__}")
        
        # Check bounds
        if min_date and date_obj < min_date:
            raise ValidationError(f"Date {date_obj} is before minimum {min_date}")
        
        if max_date and date_obj > max_date:
            raise ValidationError(f"Date {date_obj} is after maximum {max_date}")
        
        return date_obj
    
    @staticmethod
    def validate_gremlin_query(query: str, max_length: int = MAX_QUERY_LENGTH) -> str:
        """
        Validate Gremlin query for safety.
        
        Args:
            query: Gremlin query string
            max_length: Maximum query length
        
        Returns:
            Validated query
        
        Raises:
            ValidationError: If query contains dangerous operations
        """
        if not query or not isinstance(query, str):
            raise ValidationError("Query must be a non-empty string")
        
        query = query.strip()
        if not query:
             raise ValidationError("Query must be a non-empty string")
        
        if len(query) > max_length:
            raise ValidationError(
                f"Query exceeds maximum length of {max_length} characters"
            )
        
        # Enhanced dangerous operation detection
        dangerous_patterns = [
            (r'\bdrop\s*\(', 'drop'),
            (r'\bsystem\s*\(', 'system'),
            (r'\beval\s*\(', 'eval'),
            (r'\bscript\s*\(', 'script'),
            (r'\binject\s*\(', 'inject'),
            (r'__', 'double underscore (internal methods)'),
            (r';.*drop\s+table', 'SQL injection attempt'),
            (r'\bor\s+1\s*=\s*1', 'SQL injection pattern'),
            (r'\bunion\s+select', 'SQL injection pattern'),
            (r'<script', 'XSS attempt'),
            (r'javascript:', 'JavaScript injection'),
            (r'\.\./', 'path traversal'),
        ]
        
        query_lower = query.lower()
        for pattern, description in dangerous_patterns:
            if re.search(pattern, query_lower):
                raise ValidationError(
                    f"Query contains dangerous operation: {description}. "
                    "This operation is not allowed for security reasons."
                )
        
        return query
    
    @staticmethod
    def sanitize_query(query: str, max_length: int = MAX_QUERY_LENGTH) -> str:
        """
        Sanitize query by removing comments and validating.
        
        Args:
            query: Query string to sanitize
            max_length: Maximum query length
        
        Returns:
            Sanitized query
        
        Raises:
            ValidationError: If query is invalid
        """
        # Remove single-line comments
        query = re.sub(r'//.*$', '', query, flags=re.MULTILINE)
        # Remove multi-line comments
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Validate after sanitization
        return Validator.validate_gremlin_query(query.strip(), max_length)
    
    @staticmethod
    def validate_port(
        port: Union[int, str],
        allow_privileged: bool = False
    ) -> int:
        """
        Validate network port number.
        
        Args:
            port: Port number to validate
            allow_privileged: Whether to allow privileged ports (1-1023)
        
        Returns:
            Validated port number
        
        Raises:
            ValidationError: If port is invalid
        """
        try:
            port_int = int(port)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid port format: {port}") from e
        
        if not (MIN_PORT <= port_int <= MAX_PORT):
            raise ValidationError(
                f"Port must be between {MIN_PORT} and {MAX_PORT}, got {port_int}"
            )
        
        # Check for privileged ports
        if not allow_privileged and port_int < PRIVILEGED_PORT_THRESHOLD:
            raise ValidationError(
                f"Port {port_int} is privileged (< {PRIVILEGED_PORT_THRESHOLD}). "
                "Requires root/admin access on Unix systems. "
                "Use allow_privileged=True to override."
            )
        
        return port_int
    
    @staticmethod
    def validate_hostname(hostname: str, allow_empty: bool = False) -> str:
        """
        Validate hostname or IP address with proper IPv6 support.
        
        Args:
            hostname: Hostname to validate
            allow_empty: Whether to allow empty hostname
        
        Returns:
            Validated hostname
        
        Raises:
            ValidationError: If hostname is invalid
        """
        if not hostname:
            if allow_empty:
                return ''
            raise ValidationError("Hostname must be a non-empty string")
        
        if not isinstance(hostname, str):
            raise ValidationError("Hostname must be a string")
        
        hostname = hostname.strip().lower()
        
        # Check length
        if len(hostname) > MAX_HOSTNAME_LENGTH:
            raise ValidationError(
                f"Hostname too long (max {MAX_HOSTNAME_LENGTH} characters)"
            )
        
        # Allow localhost
        if hostname == 'localhost':
            return hostname
        
        # Try to parse as IP address (handles both IPv4 and IPv6)
        try:
            ipaddress.ip_address(hostname)
            return hostname
        except ValueError:
            pass
        
        # Validate as hostname
        hostname_pattern = r'^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)*$'
        if re.match(hostname_pattern, hostname):
            return hostname
        
        raise ValidationError(f"Invalid hostname format: {hostname}")
    
    @staticmethod
    def validate_batch_size(
        batch_size: Union[int, str],
        min_size: int = MIN_BATCH_SIZE,
        max_size: int = MAX_BATCH_SIZE
    ) -> int:
        """
        Validate batch size parameter.
        
        Args:
            batch_size: Batch size to validate
            min_size: Minimum allowed batch size
            max_size: Maximum allowed batch size
        
        Returns:
            Validated batch size
        
        Raises:
            ValidationError: If batch size is invalid
        """
        try:
            size = int(batch_size)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid batch size format: {batch_size}") from e
        
        if size < min_size:
            raise ValidationError(f"Batch size must be at least {min_size}, got {size}")
        
        if size > max_size:
            raise ValidationError(f"Batch size cannot exceed {max_size}, got {size}")
        
        return size
    
    @staticmethod
    def validate_numeric(
        value: Union[int, float, str],
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None
    ) -> Union[int, float]:
        """
        Validate numeric value.
        
        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        
        Returns:
            Validated numeric value
        
        Raises:
            ValidationError: If value is invalid
        """
        try:
            if isinstance(value, str):
                # Try int first, then float
                try:
                    num_value = int(value)
                except ValueError:
                    num_value = float(value)
            else:
                num_value = value
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid numeric format: {value}") from e
        
        if min_value is not None and num_value < min_value:
            raise ValidationError(
                f"Value {num_value} is below minimum {min_value}"
            )
        
        if max_value is not None and num_value > max_value:
            raise ValidationError(
                f"Value {num_value} exceeds maximum {max_value}"
            )
        
        return num_value
    
    @staticmethod
    def validate_boolean(value: Any) -> bool:
        """
        Validate and convert boolean value.
        
        Args:
            value: Value to validate
        
        Returns:
            Boolean value
        
        Raises:
            ValidationError: If value cannot be converted to boolean
        """
        if isinstance(value, bool):
            return value
        
        if isinstance(value, (int, float)):
            if value in (0, 1):
                return bool(value)
            raise ValidationError(f"Numeric value must be 0 or 1, got {value}")
        
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ('true', 'yes', 'on', '1'):
                return True
            if value_lower in ('false', 'no', 'off', '0'):
                return False
        
        raise ValidationError(f"Cannot convert {value} to boolean")
    
    @staticmethod
    def validate_url(
        url: str,
        allowed_schemes: Optional[List[str]] = None
    ) -> str:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            allowed_schemes: List of allowed schemes (default: ['http', 'https', 'ws', 'wss'])
        
        Returns:
            Validated URL
        
        Raises:
            ValidationError: If URL is invalid
        """
        if not url or not isinstance(url, str):
            raise ValidationError("URL must be a non-empty string")
        
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https', 'ws', 'wss']
        
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValidationError(f"Invalid URL format: {url}") from e
        
        if not parsed.scheme:
            raise ValidationError(f"URL missing scheme: {url}")
        
        if parsed.scheme not in allowed_schemes:
            raise ValidationError(
                f"URL scheme '{parsed.scheme}' not allowed. "
                f"Allowed schemes: {', '.join(allowed_schemes)}"
            )
        
        if not parsed.netloc:
            raise ValidationError(f"URL missing network location: {url}")
        
        return url
    
    @staticmethod
    def validate_file_path(
        path: str,
        must_exist: bool = True,
        allow_absolute: bool = True
    ) -> str:
        """
        Validate file path.
        
        Args:
            path: File path to validate
            must_exist: Whether file must exist
            allow_absolute: Whether to allow absolute paths
        
        Returns:
            Validated file path
        
        Raises:
            ValidationError: If path is invalid
        """
        if not path or not isinstance(path, str):
            raise ValidationError("File path must be a non-empty string")
        
        if len(path) > MAX_FILE_PATH_LENGTH:
            raise ValidationError(
                f"File path too long (max {MAX_FILE_PATH_LENGTH} characters)"
            )
        
        # Check for path traversal
        if '..' in path:
            raise ValidationError(
                f"Path traversal detected in: {path}. "
                "Relative paths with '..' are not allowed for security."
            )
        
        path_obj = Path(path)
        
        # Check if absolute path is allowed
        if not allow_absolute and path_obj.is_absolute():
            raise ValidationError(f"Absolute paths not allowed: {path}")
        
        # Check if file exists
        if must_exist and not path_obj.exists():
            raise ValidationError(f"File does not exist: {path}")
        
        return str(path_obj)
    
    @staticmethod
    def validate_connection_name(name: str) -> str:
        """
        Validate connection name.
        
        Args:
            name: Connection name to validate
        
        Returns:
            Validated connection name
        
        Raises:
            ValidationError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValidationError("Connection name must be a non-empty string")
        
        if len(name) > MAX_CONNECTION_NAME_LENGTH:
            raise ValidationError(
                f"Connection name too long (max {MAX_CONNECTION_NAME_LENGTH} characters)"
            )
        
        # Allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValidationError(
                f"Invalid connection name: {name}. "
                "Only alphanumeric characters, hyphens, and underscores allowed."
            )
        
        return name
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
        
        Returns:
            True if password is strong enough
        
        Raises:
            ValidationError: If password is too weak
        """
        if not password or not isinstance(password, str):
            raise ValidationError("Password must be a non-empty string")
        
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password too short (minimum {MIN_PASSWORD_LENGTH} characters)"
            )
        
        # Check for required character types
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        if not has_upper:
            raise ValidationError("Password must contain at least one uppercase letter")
        if not has_lower:
            raise ValidationError("Password must contain at least one lowercase letter")
        if not has_digit:
            raise ValidationError("Password must contain at least one digit")
        if not has_special:
            raise ValidationError("Password must contain at least one special character")
        
        return True
    
    @staticmethod
    def validate_env_var_name(name: str) -> str:
        """
        Validate environment variable name.
        
        Args:
            name: Environment variable name to validate
        
        Returns:
            Validated name
        
        Raises:
            ValidationError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValidationError("Environment variable name must be a non-empty string")
        
        # Must be uppercase, start with letter or underscore, contain only alphanumeric and underscore
        if not re.match(r'^[A-Z_][A-Z0-9_]*$', name):
            raise ValidationError(
                f"Invalid environment variable name: {name}. "
                "Must be uppercase, start with letter or underscore, "
                "and contain only alphanumeric characters and underscores."
            )
        
        return name
    
    @staticmethod
    @staticmethod
    def validate_phone(phone: str) -> str:
        """
        Validate phone number.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Validated phone number
            
        Raises:
            ValidationError: If phone is invalid
        """
        if not phone or not isinstance(phone, str):
            raise ValidationError("Phone must be a non-empty string")
        # Basic regex: optional +, allowed chars digits, space, dash. Min length 7.
        if not re.match(r'^\+?[\d\s-]{7,20}$', phone):
            raise ValidationError(f"Invalid phone format: {phone}")
        return phone.strip()

    @staticmethod
    def validate_iban(iban: str) -> str:
        """
        Validate IBAN.
        
        Args:
            iban: IBAN to validate
            
        Returns:
            Validated IBAN
            
        Raises:
            ValidationError: If IBAN is invalid
        """
        if not iban or not isinstance(iban, str):
            raise ValidationError("IBAN must be a non-empty string")
        # Basic structure: 2 letters, 2 digits, alphanumeric. Min length 15.
        if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$', iban):
            raise ValidationError(f"Invalid IBAN format: {iban}")
        return iban

    @staticmethod
    def validate_swift(swift: str) -> str:
        """
        Validate SWIFT/BIC code.
        
        Args:
            swift: Code to validate
            
        Returns:
            Validated SWIFT code
            
        Raises:
            ValidationError: If SWIFT code is invalid
        """
        if not swift or not isinstance(swift, str):
            raise ValidationError("SWIFT code must be a non-empty string")
        if not re.match(r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$', swift):
            raise ValidationError(f"Invalid SWIFT code format: {swift}")
        return swift

    @staticmethod
    def validate_ssn(ssn: str) -> str:
        """
        Validate SSN.
        
        Args:
            ssn: SSN to validate
            
        Returns:
            Validated SSN
            
        Raises:
            ValidationError: If SSN is invalid
        """
        if not ssn or not isinstance(ssn, str):
            raise ValidationError("SSN must be a non-empty string")
        
        clean_ssn = ssn.replace('-', '')
        if not re.match(r'^\d{9}$', clean_ssn):
            raise ValidationError(f"Invalid SSN format: {ssn}")
        
        # Check for invalid groups (000)
        if clean_ssn.startswith('000') or clean_ssn[3:5] == '00' or clean_ssn[5:] == '0000':
            raise ValidationError(f"Invalid SSN value: {ssn}")
            
        return ssn

    @staticmethod
    def validate_currency(currency: str) -> str:
        """
        Validate currency code.
        
        Args:
            currency: Currency code to validate
            
        Returns:
            Validated currency code
            
        Raises:
            ValidationError: If currency is invalid
        """
        if not currency or not isinstance(currency, str):
            raise ValidationError("Currency must be a non-empty string")
        if not re.match(r'^[A-Z]{3}$', currency):
            raise ValidationError(f"Invalid currency code: {currency}")
        return currency

    @staticmethod
    def validate_account_number(account_number: str) -> str:
        """
        Validate account number.
        
        Args:
            account_number: Account number to validate
            
        Returns:
            Validated account number
            
        Raises:
            ValidationError: If account number is invalid
        """
        if not account_number or not isinstance(account_number, str):
            raise ValidationError("Account number must be a non-empty string")
        # Numeric, 5-20 digits
        if not re.match(r'^\d{5,20}$', account_number):
            raise ValidationError(f"Invalid account number format: {account_number}")
        return account_number


# Backward compatibility: expose functions at module level
validate_account_id = Validator.validate_account_id
validate_amount = Validator.validate_amount
sanitize_string = Validator.sanitize_string
validate_email = Validator.validate_email
validate_date = Validator.validate_date
validate_gremlin_query = Validator.validate_gremlin_query
sanitize_query = Validator.sanitize_query
validate_port = Validator.validate_port
validate_hostname = Validator.validate_hostname
validate_batch_size = Validator.validate_batch_size
validate_numeric = Validator.validate_numeric
validate_boolean = Validator.validate_boolean
validate_url = Validator.validate_url
validate_file_path = Validator.validate_file_path
validate_connection_name = Validator.validate_connection_name
validate_password_strength = Validator.validate_password_strength
validate_env_var_name = Validator.validate_env_var_name
validate_phone = Validator.validate_phone
validate_iban = Validator.validate_iban
validate_swift = Validator.validate_swift
validate_ssn = Validator.validate_ssn
validate_currency = Validator.validate_currency
validate_account_number = Validator.validate_account_number


__all__ = [
    'ValidationError',
    'Validator',
    'validate_account_id',
    'validate_amount',
    'sanitize_string',
    'validate_email',
    'validate_date',
    'validate_gremlin_query',
    'sanitize_query',
    'validate_port',
    'validate_hostname',
    'validate_batch_size',
    'validate_numeric',
    'validate_boolean',
    'validate_url',
    'validate_file_path',
    'validate_connection_name',
    'validate_password_strength',
    'validate_env_var_name',
    'validate_phone',
    'validate_iban',
    'validate_swift',
    'validate_ssn',
    'validate_currency',
    'validate_account_number',
]
