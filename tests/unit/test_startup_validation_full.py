"""Comprehensive tests for src.python.utils.startup_validation — targets 67% → 90%+."""
import os
import sys
from unittest.mock import patch

import pytest

from src.python.utils.startup_validation import (
    StartupValidationError,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    _check_password_strength,
    _is_default_password,
    print_validation_report,
    validate_passwords,
    validate_production_mode,
    validate_startup,
)


class TestValidationSeverity:
    def test_values(self):
        assert ValidationSeverity.ERROR.value == "error"
        assert ValidationSeverity.WARNING.value == "warning"
        assert ValidationSeverity.INFO.value == "info"


class TestValidationIssue:
    def test_fields(self):
        i = ValidationIssue("msg", ValidationSeverity.ERROR, variable="X", recommendation="fix")
        assert i.message == "msg"
        assert i.severity == ValidationSeverity.ERROR
        assert i.variable == "X"
        assert i.recommendation == "fix"

    def test_defaults(self):
        i = ValidationIssue("msg", ValidationSeverity.WARNING)
        assert i.variable is None
        assert i.recommendation is None


class TestValidationResult:
    def test_has_errors_false(self):
        r = ValidationResult()
        assert not r.has_errors

    def test_has_errors_true(self):
        r = ValidationResult()
        r.add_error("bad")
        assert r.has_errors

    def test_add_warning(self):
        r = ValidationResult()
        r.add_warning("warn", variable="V", recommendation="fix")
        assert len(r.issues) == 1
        assert r.issues[0].severity == ValidationSeverity.WARNING
        assert not r.has_errors

    def test_add_error(self):
        r = ValidationResult()
        r.add_error("err", variable="V", recommendation="fix")
        assert r.issues[0].severity == ValidationSeverity.ERROR


class TestStartupValidationError:
    def test_message(self):
        r = ValidationResult()
        r.add_error("e1")
        r.add_error("e2")
        err = StartupValidationError(r)
        assert "2 error(s)" in str(err)
        assert err.result is r


class TestIsDefaultPassword:
    @pytest.mark.parametrize("pwd", [
        "changeit", "password", "admin", "secret", "123456", "1234567890",
        "YOUR_PASSWORD_HERE", "CHANGEME", "CHANGE_ME", "PLACEHOLDER",
        "DefaultDev0nly!2026",
    ])
    def test_detects_defaults(self, pwd):
        assert _is_default_password(pwd)

    @pytest.mark.parametrize("pwd", [
        "MyStr0ng!Pass#2026", "xK9$mNpQ2wLz", "not-a-default",
    ])
    def test_allows_strong(self, pwd):
        assert not _is_default_password(pwd)

    def test_case_insensitive(self):
        assert _is_default_password("CHANGEIT")
        assert _is_default_password("Password")


class TestCheckPasswordStrength:
    def test_strong_password(self):
        assert _check_password_strength("MyStr0ng!Pass") == []

    def test_short(self):
        issues = _check_password_strength("Ab1")
        assert any("12 characters" in i for i in issues)

    def test_no_uppercase(self):
        issues = _check_password_strength("alllowercase1234")
        assert any("uppercase" in i for i in issues)

    def test_no_lowercase(self):
        issues = _check_password_strength("ALLUPPERCASE1234")
        assert any("lowercase" in i for i in issues)

    def test_no_numbers(self):
        issues = _check_password_strength("NoNumbersHere!!")
        assert any("numbers" in i for i in issues)


class TestValidatePasswords:
    def test_no_env_vars(self):
        env = {"OPENSEARCH_INITIAL_ADMIN_PASSWORD": "StrongP@ss1234"}
        with patch.dict(os.environ, env, clear=True):
            r = ValidationResult()
            validate_passwords(r, strict=False)
            assert not r.has_errors

    def test_missing_opensearch_password(self):
        with patch.dict(os.environ, {}, clear=True):
            r = ValidationResult()
            validate_passwords(r)
            assert r.has_errors
            assert any("OPENSEARCH_INITIAL_ADMIN_PASSWORD" in i.message or
                       (i.variable and "OPENSEARCH" in i.variable) for i in r.issues)

    def test_default_password_detected(self):
        env = {
            "OPENSEARCH_INITIAL_ADMIN_PASSWORD": "StrongP@ss1234",
            "JANUSGRAPH_PASSWORD": "changeit",
        }
        with patch.dict(os.environ, env, clear=True):
            r = ValidationResult()
            validate_passwords(r)
            assert r.has_errors

    def test_weak_password_warning_strict(self):
        env = {
            "OPENSEARCH_INITIAL_ADMIN_PASSWORD": "StrongP@ss1234",
            "JANUSGRAPH_PASSWORD": "short",
        }
        with patch.dict(os.environ, env, clear=True):
            r = ValidationResult()
            validate_passwords(r, strict=True)
            warnings = [i for i in r.issues if i.severity == ValidationSeverity.WARNING]
            assert len(warnings) > 0

    def test_no_warnings_non_strict(self):
        env = {
            "OPENSEARCH_INITIAL_ADMIN_PASSWORD": "StrongP@ss1234",
            "JANUSGRAPH_PASSWORD": "short",
        }
        with patch.dict(os.environ, env, clear=True):
            r = ValidationResult()
            validate_passwords(r, strict=False)
            warnings = [i for i in r.issues if i.severity == ValidationSeverity.WARNING]
            assert len(warnings) == 0


class TestValidateProductionMode:
    def test_non_production(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "dev"}, clear=True):
            r = ValidationResult()
            validate_production_mode(r)
            assert not r.has_errors

    def test_production_no_ssl(self):
        env = {"ENVIRONMENT": "production", "JANUSGRAPH_USE_SSL": "false"}
        with patch.dict(os.environ, env, clear=True):
            r = ValidationResult()
            validate_production_mode(r)
            assert r.has_errors

    def test_production_debug_on(self):
        env = {"ENVIRONMENT": "prod", "JANUSGRAPH_USE_SSL": "true", "DEBUG": "true"}
        with patch.dict(os.environ, env, clear=True):
            r = ValidationResult()
            validate_production_mode(r)
            assert r.has_errors

    def test_production_ok(self):
        env = {"ENVIRONMENT": "production", "JANUSGRAPH_USE_SSL": "true", "DEBUG": "false"}
        with patch.dict(os.environ, env, clear=True):
            r = ValidationResult()
            validate_production_mode(r)
            assert not r.has_errors


class TestValidateStartup:
    def test_passes_clean(self):
        env = {"OPENSEARCH_INITIAL_ADMIN_PASSWORD": "StrongP@ss1234"}
        with patch.dict(os.environ, env, clear=True):
            result = validate_startup(strict=False)
            assert not result.has_errors

    def test_raises_on_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(StartupValidationError):
                validate_startup(strict=False)

    def test_exit_on_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                validate_startup(strict=False, exit_on_error=True)


class TestPrintValidationReport:
    def test_no_issues(self, capsys):
        r = ValidationResult()
        print_validation_report(r)
        out = capsys.readouterr().out
        assert "All validations passed" in out

    def test_errors_and_warnings(self, capsys):
        r = ValidationResult()
        r.add_error("bad thing", variable="VAR")
        r.add_warning("meh", variable="VAR2")
        print_validation_report(r)
        out = capsys.readouterr().out
        assert "ERRORS" in out
        assert "WARNINGS" in out
