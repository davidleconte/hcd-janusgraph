#!/usr/bin/env python3
"""
Structured Error Codes Module

Provides consistent error codes and exception classes for the application.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ErrorCategory(Enum):
    """Error categories for classification."""

    VALIDATION = "validation"
    AUTHENTICATION = "auth"
    AUTHORIZATION = "authz"
    DATABASE = "db"
    NETWORK = "network"
    CONFIGURATION = "config"
    INTERNAL = "internal"


@dataclass
class ErrorCode:
    """Structured error code definition."""

    code: str
    category: ErrorCategory
    message: str
    http_status: int = 500


# Error code registry
ERROR_CODES: Dict[str, ErrorCode] = {
    # Validation errors (1xxx)
    "VAL_001": ErrorCode("VAL_001", ErrorCategory.VALIDATION, "Invalid input parameter", 400),
    "VAL_002": ErrorCode("VAL_002", ErrorCategory.VALIDATION, "Required field missing", 400),
    "VAL_003": ErrorCode("VAL_003", ErrorCategory.VALIDATION, "Invalid date format", 400),
    "VAL_004": ErrorCode("VAL_004", ErrorCategory.VALIDATION, "Value out of range", 400),
    # Auth errors (2xxx)
    "AUTH_001": ErrorCode("AUTH_001", ErrorCategory.AUTHENTICATION, "Invalid credentials", 401),
    "AUTH_002": ErrorCode("AUTH_002", ErrorCategory.AUTHENTICATION, "Token expired", 401),
    "AUTH_003": ErrorCode("AUTH_003", ErrorCategory.AUTHORIZATION, "Insufficient permissions", 403),
    # Database errors (3xxx)
    "DB_001": ErrorCode("DB_001", ErrorCategory.DATABASE, "Connection failed", 503),
    "DB_002": ErrorCode("DB_002", ErrorCategory.DATABASE, "Query timeout", 504),
    "DB_003": ErrorCode("DB_003", ErrorCategory.DATABASE, "Entity not found", 404),
    "DB_004": ErrorCode("DB_004", ErrorCategory.DATABASE, "Duplicate entity", 409),
    # Config errors (4xxx)
    "CFG_001": ErrorCode("CFG_001", ErrorCategory.CONFIGURATION, "Missing configuration", 500),
    "CFG_002": ErrorCode("CFG_002", ErrorCategory.CONFIGURATION, "Invalid configuration", 500),
}


class AppException(Exception):
    """Base application exception with structured error code."""

    def __init__(
        self,
        error_code: str,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.error: ErrorCode = ERROR_CODES.get(error_code) or ErrorCode(
            error_code, ErrorCategory.INTERNAL, "Unknown error", 500
        )
        self.details = details
        self.context = context or {}
        super().__init__(
            f"[{self.error.code}] {self.error.message}: {details}"
            if details
            else f"[{self.error.code}] {self.error.message}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error.code,
            "category": self.error.category.value,
            "message": self.error.message,
            "details": self.details,
            "context": self.context,
        }


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, details: Optional[str] = None, field: Optional[str] = None) -> None:
        super().__init__("VAL_001", details, {"field": field} if field else None)


class NotFoundError(AppException):
    """Entity not found error."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            "DB_003",
            f"{entity_type} '{entity_id}' not found",
            {"entity_type": entity_type, "entity_id": entity_id},
        )


class ConnectionError(AppException):
    """Database connection error."""

    def __init__(self, service: str, details: Optional[str] = None) -> None:
        super().__init__("DB_001", details, {"service": service})
