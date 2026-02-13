"""MFA TOTP verification test — validates real authenticator app compatibility."""

import os
from unittest.mock import patch

import pyotp
import pytest

os.environ.setdefault("JANUSGRAPH_HOST", "localhost")
os.environ.setdefault("JANUSGRAPH_PORT", "8182")

with patch("banking.compliance.audit_logger.AuditLogger.__init__", return_value=None):
    from src.python.security.mfa import MFAManager, MFAEnrollment, MFAMethod


class TestMFAEndToEnd:
    """Tests MFA enrollment and verification with real TOTP codes."""

    def test_totp_enrollment_and_verification(self):
        """Simulate full MFA flow: enroll → generate code → verify."""
        mgr = MFAManager()
        enrollment = MFAEnrollment(mgr)

        data = enrollment.enroll_user("test-user", "test@example.com", method=MFAMethod.TOTP)

        assert data["user_id"] == "test-user"
        assert data["method"] == "totp"
        assert data["secret"]
        assert len(data["backup_codes"]) > 0
        assert data["status"] == "pending_verification"

        secret = data["secret"]
        totp = pyotp.TOTP(secret)
        current_code = totp.now()

        is_valid = mgr.verify_totp(secret, current_code, user_id="test-user")
        assert is_valid is True

    def test_totp_wrong_code_rejected(self):
        """Wrong TOTP code should be rejected."""
        mgr = MFAManager()
        enrollment = MFAEnrollment(mgr)
        data = enrollment.enroll_user("test-user-2", "test2@example.com", method=MFAMethod.TOTP)
        secret = data["secret"]

        is_valid = mgr.verify_totp(secret, "000000", user_id="test-user-2")
        assert is_valid is False

    def test_backup_code_verification(self):
        """Backup codes should work for single-use verification."""
        mgr = MFAManager()
        enrollment = MFAEnrollment(mgr)
        data = enrollment.enroll_user("test-user-3", "test3@example.com", method=MFAMethod.TOTP)

        backup_codes = data["backup_codes"]
        assert len(backup_codes) > 0

        hashed = [mgr.hash_backup_code(code) for code in backup_codes]
        is_valid = mgr.verify_backup_code(backup_codes[0], hashed)
        assert is_valid is True

    def test_lockout_after_failed_attempts(self):
        """Account should lock after too many failed attempts."""
        from src.python.security.mfa import MFAConfig

        config = MFAConfig(max_attempts=3, lockout_duration=60)
        mgr = MFAManager(config=config)
        enrollment = MFAEnrollment(mgr)
        data = enrollment.enroll_user("lockout-user", "lock@example.com", method=MFAMethod.TOTP)
        secret = data["secret"]

        for _ in range(3):
            mgr.verify_totp(secret, "000000", user_id="lockout-user")

        lockout = mgr.get_lockout_remaining("lockout-user")
        assert lockout is not None
        assert lockout > 0

    def test_totp_provisioning_uri(self):
        """Verify TOTP secret generates valid provisioning URI for QR codes."""
        mgr = MFAManager()
        enrollment = MFAEnrollment(mgr)
        data = enrollment.enroll_user("qr-user", "qr@example.com", method=MFAMethod.TOTP)

        secret = data["secret"]
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name="qr@example.com", issuer_name="JanusGraph Analytics")

        assert uri.startswith("otpauth://totp/")
        assert "example.com" in uri
        assert "JanusGraph" in uri
