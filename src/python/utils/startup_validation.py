#!/usr/bin/env python3
"""
Startup Validation Module

Validates critical configuration before application startup.
Rejects default/placeholder passwords and insecure configurations.

Usage:
    from src.python.utils.startup_validation import validate_startup
    validate_startup()  # Raises StartupValidationError if invalid
"""

import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""
    message: str
    severity: ValidationSeverity
    variable: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of startup validation."""
    issues: List[ValidationIssue] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        return any(i.severity == ValidationSeverity.ERROR for i in self.issues)
    
    def add_error(self, message: str, variable: str = None, recommendation: str = None):
        self.issues.append(ValidationIssue(message, ValidationSeverity.ERROR, variable, recommendation))
    
    def add_warning(self, message: str, variable: str = None, recommendation: str = None):
        self.issues.append(ValidationIssue(message, ValidationSeverity.WARNING, variable, recommendation))


class StartupValidationError(Exception):
    """Raised when startup validation fails."""
    def __init__(self, result: ValidationResult):
        self.result = result
        errors = [i for i in result.issues if i.severity == ValidationSeverity.ERROR]
        message = f"Startup validation failed with {len(errors)} error(s)"
        super().__init__(message)


DEFAULT_PASSWORD_PATTERNS = [
    r"^changeit$", r"^password$", r"^admin$", r"^secret$",
    r"^123456", r"YOUR_.*_HERE", r"CHANGE_?ME", r"PLACEHOLDER",
]

PASSWORD_VARIABLES = [
    "JANUSGRAPH_PASSWORD", "HCD_KEYSTORE_PASSWORD",
    "OPENSEARCH_ADMIN_PASSWORD", "GRAFANA_ADMIN_PASSWORD",
    "VAULT_TOKEN", "DB_PASSWORD",
]


def _is_default_password(value: str) -> bool:
    """Check if value matches a default/placeholder pattern."""
    for pattern in DEFAULT_PASSWORD_PATTERNS:
        if re.match(pattern, value, re.IGNORECASE):
            return True
    return False


def _check_password_strength(password: str) -> List[str]:
    """Check password strength, return list of issues."""
    issues = []
    if len(password) < 12:
        issues.append("Password must be at least 12 characters")
    if not re.search(r"[A-Z]", password):
        issues.append("Password should contain uppercase letters")
    if not re.search(r"[a-z]", password):
        issues.append("Password should contain lowercase letters")
    if not re.search(r"\d", password):
        issues.append("Password should contain numbers")
    return issues


def validate_passwords(result: ValidationResult, strict: bool = True) -> None:
    """Validate password environment variables."""
    for var in PASSWORD_VARIABLES:
        value = os.getenv(var)
        if not value:
            continue
        if _is_default_password(value):
            result.add_error(
                "Default/placeholder password detected",
                variable=var,
                recommendation=f"Set a strong password: export {var}='your-secure-password'"
            )
            continue
        if strict:
            for issue in _check_password_strength(value):
                result.add_warning(issue, variable=var)


def validate_production_mode(result: ValidationResult) -> None:
    """Additional checks for production mode."""
    is_production = os.getenv("ENVIRONMENT", "").lower() in ["production", "prod"]
    if not is_production:
        return
    ssl_enabled = os.getenv("JANUSGRAPH_USE_SSL", "false").lower() == "true"
    if not ssl_enabled:
        result.add_error("SSL/TLS must be enabled in production", "JANUSGRAPH_USE_SSL")
    if os.getenv("DEBUG", "false").lower() == "true":
        result.add_error("Debug mode must be disabled in production", "DEBUG")


def validate_startup(strict: bool = False, exit_on_error: bool = False) -> ValidationResult:
    """Run all startup validations."""
    result = ValidationResult()
    validate_passwords(result, strict=strict)
    validate_production_mode(result)
    
    if result.has_errors:
        if exit_on_error:
            print_validation_report(result)
            sys.exit(1)
        raise StartupValidationError(result)
    return result


def print_validation_report(result: ValidationResult) -> None:
    """Print a formatted validation report."""
    print("\n" + "=" * 50)
    print("STARTUP VALIDATION REPORT")
    print("=" * 50)
    
    errors = [i for i in result.issues if i.severity == ValidationSeverity.ERROR]
    warnings = [i for i in result.issues if i.severity == ValidationSeverity.WARNING]
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for issue in errors:
            print(f"   {issue.message} ({issue.variable})")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for issue in warnings:
            print(f"   {issue.message} ({issue.variable})")
    
    if not errors and not warnings:
        print("\n✅ All validations passed!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        result = validate_startup(strict=True)
        print_validation_report(result)
    except StartupValidationError as e:
        print_validation_report(e.result)
        sys.exit(1)
