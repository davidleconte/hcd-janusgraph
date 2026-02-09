"""
Log Sanitization for PII Protection
Filters and sanitizes personally identifiable information from logs

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-28
Phase: Week 1 Remediation - Security Hardening
"""

import logging
import re
from typing import Dict, Optional, Pattern, Tuple


class PIISanitizer(logging.Filter):
    """
    Logging filter to sanitize PII from log messages.

    Automatically redacts:
    - Email addresses
    - Social Security Numbers (SSN)
    - Credit card numbers
    - Phone numbers
    - Account IDs
    - Customer names (when in specific patterns)
    - IP addresses (optional)

    Example:
        >>> handler = logging.StreamHandler()
        >>> handler.addFilter(PIISanitizer())
        >>> logging.basicConfig(handlers=[handler])
    """

    # Patterns to redact (pattern, replacement)
    PATTERNS: Dict[str, Tuple[Pattern, str]] = {
        "email": (
            re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "[EMAIL_REDACTED]",
        ),
        "ssn": (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
        "credit_card": (
            re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
            "[CARD_REDACTED]",
        ),
        "phone": (
            re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
            "[PHONE_REDACTED]",
        ),
        "account_id": (re.compile(r"\bACC-\d+\b"), "[ACCOUNT_REDACTED]"),
        "customer_name": (
            re.compile(r"(?:customer|user|person)[\s:]+([A-Z][a-z]+\s+[A-Z][a-z]+)", re.IGNORECASE),
            r"\1 [NAME_REDACTED]",
        ),
        "ip_address": (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP_REDACTED]"),
    }

    def __init__(
        self,
        redact_ip: bool = False,
        additional_patterns: Optional[Dict[str, Tuple[str, str]]] = None,
    ):
        """
        Initialize PII sanitizer.

        Args:
            redact_ip: Whether to redact IP addresses (default: False)
            additional_patterns: Additional patterns to redact
                Format: {'name': (regex_pattern, replacement)}
        """
        super().__init__()
        self.redact_ip = redact_ip

        # Compile patterns
        self.patterns = self.PATTERNS.copy()

        # Remove IP pattern if not redacting
        if not redact_ip:
            self.patterns.pop("ip_address", None)

        # Add additional patterns
        if additional_patterns:
            for name, (pattern, replacement) in additional_patterns.items():
                self.patterns[name] = (re.compile(pattern), replacement)

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record by sanitizing PII.

        Args:
            record: Log record to filter

        Returns:
            True (always allows record through after sanitization)
        """
        # Sanitize message
        record.msg = self.sanitize(str(record.msg))

        # Sanitize args
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.sanitize(str(v)) for k, v in record.args.items()}
            else:
                record.args = tuple(self.sanitize(str(arg)) for arg in record.args)

        return True

    def sanitize(self, text: str) -> str:
        """
        Remove PII from text.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text with PII redacted

        Example:
            >>> sanitizer = PIISanitizer()
            >>> sanitizer.sanitize("Email: user@example.com")
            'Email: [EMAIL_REDACTED]'
        """
        if not text:
            return text

        sanitized = text
        for pattern, replacement in self.patterns.values():
            sanitized = pattern.sub(replacement, sanitized)

        return sanitized


def setup_secure_logging(
    level: str = "INFO",
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    redact_ip: bool = False,
    additional_patterns: Optional[Dict[str, Tuple[str, str]]] = None,
) -> None:
    """
    Configure logging with PII sanitization.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Log format string
        redact_ip: Whether to redact IP addresses
        additional_patterns: Additional patterns to redact

    Example:
        >>> setup_secure_logging(level='INFO')
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Customer email: user@example.com")
        # Logs: "Customer email: [EMAIL_REDACTED]"
    """
    # Create handler with PII filter
    handler = logging.StreamHandler()
    handler.addFilter(PIISanitizer(redact_ip=redact_ip, additional_patterns=additional_patterns))
    handler.setFormatter(logging.Formatter(format_string))

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=[handler],
        force=True,  # Override existing configuration
    )


def get_secure_logger(name: str, redact_ip: bool = False) -> logging.Logger:
    """
    Get a logger with PII sanitization.

    Args:
        name: Logger name
        redact_ip: Whether to redact IP addresses

    Returns:
        Logger instance with PII sanitization

    Example:
        >>> logger = get_secure_logger(__name__)
        >>> logger.info("Processing account ACC-12345")
        # Logs: "Processing account [ACCOUNT_REDACTED]"
    """
    logger = logging.getLogger(name)

    # Add PII filter to all handlers
    for handler in logger.handlers:
        if not any(isinstance(f, PIISanitizer) for f in handler.filters):
            handler.addFilter(PIISanitizer(redact_ip=redact_ip))

    return logger


# Utility function for manual sanitization
def sanitize_for_logging(text: str, redact_ip: bool = False) -> str:
    """
    Manually sanitize text before logging.

    Args:
        text: Text to sanitize
        redact_ip: Whether to redact IP addresses

    Returns:
        Sanitized text

    Example:
        >>> sanitize_for_logging("User john.doe@example.com logged in")
        'User [EMAIL_REDACTED] logged in'
    """
    sanitizer = PIISanitizer(redact_ip=redact_ip)
    return sanitizer.sanitize(text)


# Context manager for temporary PII logging (development only)
class AllowPIILogging:
    """
    Context manager to temporarily disable PII sanitization.

    WARNING: Only use in development/debugging. Never in production!

    Example:
        >>> with AllowPIILogging():
        ...     logger.debug("Debug info with PII")
    """

    def __init__(self):
        self.original_filters = {}

    def __enter__(self):
        """Remove PII filters from all handlers."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            self.original_filters[handler] = handler.filters.copy()
            handler.filters = [f for f in handler.filters if not isinstance(f, PIISanitizer)]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore PII filters."""
        for handler, filters in self.original_filters.items():
            handler.filters = filters


__all__ = [
    "PIISanitizer",
    "setup_secure_logging",
    "get_secure_logger",
    "sanitize_for_logging",
    "AllowPIILogging",
]
