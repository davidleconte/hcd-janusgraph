"""Comprehensive tests for src.python.security.mfa — targets 55% → 90%+."""
import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

os.environ.setdefault("AUDIT_LOG_DIR", "/tmp/janusgraph-test-logs")

from unittest.mock import patch as _patch, MagicMock as _MagicMock
with _patch("banking.compliance.audit_logger.AuditLogger.__init__", lambda self, *a, **kw: None):
    with _patch("banking.compliance.audit_logger.AuditLogger.log_event", _MagicMock()):
        import banking.compliance.audit_logger as _al
        _al._audit_logger = _MagicMock()

import pyotp


@pytest.fixture(autouse=True)
def mfa_store_path(monkeypatch, tmp_path):
    """Use a temporary MFA enrollment store for every test."""
    monkeypatch.setenv("JANUSGRAPH_MFA_STORE_PATH", str(tmp_path / "mfa_enrollments.json"))

from src.python.security.mfa import (
    MFAMethod,
    MFAConfig,
    MFAManager,
    MFAEnrollment,
    MFAMiddleware,
)


class TestMFAMethod:
    def test_values(self):
        assert MFAMethod.TOTP.value == "totp"
        assert MFAMethod.SMS.value == "sms"
        assert MFAMethod.EMAIL.value == "email"
        assert MFAMethod.BACKUP_CODE.value == "backup_code"


class TestMFAConfig:
    def test_defaults(self):
        c = MFAConfig()
        assert c.issuer == "JanusGraph"
        assert c.digits == 6
        assert c.interval == 30
        assert c.max_attempts == 3
        assert c.lockout_duration == 300
        assert "admin" in c.require_mfa_for_roles

    def test_custom(self):
        c = MFAConfig(issuer="Custom", max_attempts=5, require_mfa_for_roles=["superadmin"])
        assert c.issuer == "Custom"
        assert c.max_attempts == 5
        assert c.require_mfa_for_roles == ["superadmin"]


class TestMFAManager:
    def setup_method(self):
        self.mgr = MFAManager()

    def test_generate_secret(self):
        secret = self.mgr.generate_secret()
        assert len(secret) > 0
        pyotp.TOTP(secret)

    def test_setup_totp(self):
        secret, qr_bytes = self.mgr.setup_totp("u1", "u1@example.com")
        assert isinstance(secret, str)
        assert isinstance(qr_bytes, bytes)
        assert len(qr_bytes) > 100

    def test_verify_totp_valid(self):
        secret = self.mgr.generate_secret()
        totp = pyotp.TOTP(secret)
        token = totp.now()
        assert self.mgr.verify_totp(secret, token, user_id="u1")

    def test_verify_totp_invalid(self):
        secret = self.mgr.generate_secret()
        assert not self.mgr.verify_totp(secret, "000000", user_id="u1")

    def test_verify_totp_no_user_id(self):
        secret = self.mgr.generate_secret()
        totp = pyotp.TOTP(secret)
        assert self.mgr.verify_totp(secret, totp.now())

    def test_verify_totp_exception(self):
        assert not self.mgr.verify_totp("invalid-secret!!!", "123456", user_id="u1")

    def test_generate_backup_codes(self):
        codes = self.mgr.generate_backup_codes()
        assert len(codes) == 10
        assert all(len(c) == 8 for c in codes)
        assert all(c == c.upper() for c in codes)

    def test_generate_backup_codes_custom_count(self):
        codes = self.mgr.generate_backup_codes(count=5)
        assert len(codes) == 5

    def test_hash_backup_code(self):
        h = self.mgr.hash_backup_code("ABCD1234")
        assert isinstance(h, str)
        assert len(h) == 64

    def test_verify_backup_code_valid(self):
        code = "ABCD1234"
        hashed = [self.mgr.hash_backup_code(code)]
        assert self.mgr.verify_backup_code(code, hashed)

    def test_verify_backup_code_invalid(self):
        assert not self.mgr.verify_backup_code("WRONG", ["abc123"])

    def test_lockout_after_max_attempts(self):
        secret = self.mgr.generate_secret()
        for _ in range(3):
            self.mgr.verify_totp(secret, "000000", user_id="lockme")
        assert self.mgr._is_locked_out("lockme")
        assert not self.mgr.verify_totp(secret, "000000", user_id="lockme")

    def test_lockout_remaining(self):
        secret = self.mgr.generate_secret()
        for _ in range(3):
            self.mgr.verify_totp(secret, "000000", user_id="u1")
        remaining = self.mgr.get_lockout_remaining("u1")
        assert remaining is not None
        assert remaining > 0

    def test_lockout_remaining_not_locked(self):
        assert self.mgr.get_lockout_remaining("nobody") is None

    def test_lockout_expires(self):
        secret = self.mgr.generate_secret()
        for _ in range(3):
            self.mgr.verify_totp(secret, "000000", user_id="u1")
        self.mgr.failed_attempts["u1"]["last_attempt"] = datetime.now(timezone.utc) - timedelta(seconds=600)
        assert not self.mgr._is_locked_out("u1")

    def test_reset_failed_attempts(self):
        self.mgr.failed_attempts["u1"] = {"count": 5}
        self.mgr._reset_failed_attempts("u1")
        assert "u1" not in self.mgr.failed_attempts

    def test_reset_failed_attempts_none(self):
        self.mgr._reset_failed_attempts(None)

    def test_record_failed_attempt_none(self):
        self.mgr._record_failed_attempt(None)

    def test_is_mfa_required(self):
        assert self.mgr.is_mfa_required(["admin"])
        assert self.mgr.is_mfa_required(["developer"])
        assert not self.mgr.is_mfa_required(["viewer"])
        assert not self.mgr.is_mfa_required([])


class TestMFAEnrollment:
    def setup_method(self):
        self.mgr = MFAManager()
        self.enrollment = MFAEnrollment(self.mgr)

    def test_enroll_user_totp(self):
        data = self.enrollment.enroll_user("u1", "u1@example.com")
        assert data["user_id"] == "u1"
        assert data["method"] == "totp"
        assert "secret" in data
        assert "qr_code" in data
        assert len(data["backup_codes"]) == 10
        assert len(data["hashed_backup_codes"]) == 10
        assert data["status"] == "pending_verification"

    def test_enroll_user_unsupported_method(self):
        with pytest.raises(NotImplementedError):
            self.enrollment.enroll_user("u1", "u1@example.com", method=MFAMethod.SMS)

    def test_verify_enrollment_valid(self):
        secret = self.mgr.generate_secret()
        totp = pyotp.TOTP(secret)
        assert self.enrollment.verify_enrollment("u1", secret, totp.now())

    def test_verify_enrollment_invalid(self):
        secret = self.mgr.generate_secret()
        assert not self.enrollment.verify_enrollment("u1", secret, "000000")

    def test_unenroll_user(self):
        self.enrollment.unenroll_user("u1", reason="User request")


class TestMFAMiddleware:
    def setup_method(self):
        self.mgr = MFAManager()
        self.mw = MFAMiddleware(self.mgr)

    def test_mfa_not_required(self):
        assert self.mw.require_mfa("u1", ["viewer"], mfa_verified=False)

    def test_mfa_required_not_verified(self):
        assert not self.mw.require_mfa("u1", ["admin"], mfa_verified=False)

    def test_mfa_required_verified(self):
        assert self.mw.require_mfa("u1", ["admin"], mfa_verified=True)
