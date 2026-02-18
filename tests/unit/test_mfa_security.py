"""Tests for src.python.security.mfa module (unblocked by pyotp install)."""

import os
import sys
from unittest.mock import MagicMock, patch

# Patch AuditLogger before any import triggers it
with patch("banking.compliance.audit_logger.AuditLogger.__init__", lambda self, **kw: None):
    with patch("banking.compliance.audit_logger.AuditLogger.log_event", MagicMock()):
        import banking.compliance.audit_logger as _al

        _al._audit_logger = MagicMock()

import pyotp
import pytest

from src.python.security.mfa import MFAConfig, MFAManager, MFAMethod


class TestMFAConfig:
    def test_defaults(self):
        config = MFAConfig()
        assert config.issuer == "JanusGraph"
        assert config.algorithm == "SHA1"
        assert config.digits == 6
        assert config.interval == 30
        assert config.backup_codes_count == 10
        assert config.backup_code_length == 8
        assert config.max_attempts == 3
        assert config.lockout_duration == 300
        assert "admin" in config.require_mfa_for_roles
        assert "developer" in config.require_mfa_for_roles

    def test_custom_config(self):
        config = MFAConfig(issuer="TestApp", digits=8, interval=60, max_attempts=5)
        assert config.issuer == "TestApp"
        assert config.digits == 8
        assert config.interval == 60
        assert config.max_attempts == 5

    def test_custom_roles(self):
        config = MFAConfig(require_mfa_for_roles=["superadmin"])
        assert config.require_mfa_for_roles == ["superadmin"]


class TestMFAMethod:
    def test_totp(self):
        assert MFAMethod.TOTP.value == "totp"

    def test_sms(self):
        assert MFAMethod.SMS.value == "sms"

    def test_email(self):
        assert MFAMethod.EMAIL.value == "email"

    def test_backup_code(self):
        assert MFAMethod.BACKUP_CODE.value == "backup_code"


class TestMFAManager:
    def test_init_default(self):
        mgr = MFAManager()
        assert mgr.config.issuer == "JanusGraph"
        assert mgr.failed_attempts == {}

    def test_init_custom_config(self):
        config = MFAConfig(issuer="Test", digits=8)
        mgr = MFAManager(config=config)
        assert mgr.config.issuer == "Test"
        assert mgr.config.digits == 8

    def test_generate_secret(self):
        mgr = MFAManager()
        secret = mgr.generate_secret()
        assert isinstance(secret, str)
        assert len(secret) >= 16

    def test_generate_secret_uniqueness(self):
        mgr = MFAManager()
        secrets = {mgr.generate_secret() for _ in range(10)}
        assert len(secrets) == 10

    def test_setup_totp(self):
        mgr = MFAManager()
        secret, qr_image = mgr.setup_totp("user1", "user1@test.com")
        assert isinstance(secret, str)
        assert isinstance(qr_image, bytes)
        assert len(qr_image) > 100

    def test_verify_totp_valid(self):
        mgr = MFAManager()
        secret = mgr.generate_secret()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        result = mgr.verify_totp(secret, code)
        assert result is True

    def test_verify_totp_invalid_code(self):
        mgr = MFAManager()
        secret = mgr.generate_secret()
        result = mgr.verify_totp(secret, "000000")
        assert result is False

    def test_verify_totp_wrong_secret(self):
        mgr = MFAManager()
        secret1 = mgr.generate_secret()
        secret2 = mgr.generate_secret()
        totp = pyotp.TOTP(secret1)
        code = totp.now()
        result = mgr.verify_totp(secret2, code)
        assert result is False

    def test_generate_backup_codes(self):
        mgr = MFAManager()
        codes = mgr.generate_backup_codes()
        assert len(codes) == mgr.config.backup_codes_count
        assert all(isinstance(c, str) for c in codes)
        assert all(len(c) == mgr.config.backup_code_length for c in codes)

    def test_generate_backup_codes_unique(self):
        mgr = MFAManager()
        codes = mgr.generate_backup_codes()
        assert len(set(codes)) == len(codes)

    def test_generate_backup_codes_custom_count(self):
        config = MFAConfig(backup_codes_count=5)
        mgr = MFAManager(config=config)
        codes = mgr.generate_backup_codes()
        assert len(codes) == 5
