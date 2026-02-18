#!/usr/bin/env python3
"""Tests for startup validation module."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.python.utils.startup_validation import (
    StartupValidationError,
    ValidationResult,
    _check_password_strength,
    _is_default_password,
    validate_passwords,
    validate_startup,
)


class TestDefaultPasswordDetection:
    def test_detects_changeit(self):
        assert _is_default_password("changeit") is True

    def test_detects_password(self):
        assert _is_default_password("password") is True

    def test_detects_placeholder(self):
        assert _is_default_password("YOUR_PASSWORD_HERE") is True

    def test_accepts_strong_password(self):
        assert _is_default_password("MyStr0ng!Pass#2024") is False


class TestPasswordStrength:
    def test_short_password(self):
        issues = _check_password_strength("short")
        assert any("12 characters" in i for i in issues)

    def test_missing_uppercase(self):
        issues = _check_password_strength("allowercase123!")
        assert any("uppercase" in i for i in issues)

    def test_strong_password(self):
        issues = _check_password_strength("StrongP@ss123!")
        assert len(issues) == 0


class TestValidatePasswords:
    @patch.dict(os.environ, {"JANUSGRAPH_PASSWORD": "changeit"}, clear=False)
    def test_rejects_default_password(self):
        result = ValidationResult()
        validate_passwords(result)
        assert result.has_errors

    @patch.dict(
        os.environ,
        {
            "JANUSGRAPH_PASSWORD": "MyStr0ng!Pass#2024",
            "OPENSEARCH_INITIAL_ADMIN_PASSWORD": "Str0ng!Pass#2024",
        },
        clear=False,
    )
    def test_accepts_strong_password(self):
        result = ValidationResult()
        validate_passwords(result, strict=False)
        assert not result.has_errors


class TestValidateStartup:
    @patch.dict(os.environ, {"OPENSEARCH_INITIAL_ADMIN_PASSWORD": "Str0ng!Pass#2024"}, clear=True)
    def test_no_env_vars_passes(self):
        result = validate_startup(strict=False)
        assert not result.has_errors

    @patch.dict(os.environ, {"JANUSGRAPH_PASSWORD": "changeit"}, clear=False)
    def test_default_password_raises(self):
        with pytest.raises(StartupValidationError):
            validate_startup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
