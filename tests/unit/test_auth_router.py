"""Tests for src.python.api.routers.auth — MFA API endpoints."""
import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("AUDIT_LOG_DIR", "/tmp/janusgraph-test-logs")

from unittest.mock import patch as _patch, MagicMock as _MagicMock
with _patch("banking.compliance.audit_logger.AuditLogger.__init__", lambda self, *a, **kw: None):
    with _patch("banking.compliance.audit_logger.AuditLogger.log_event", _MagicMock()):
        import banking.compliance.audit_logger as _al
        _al._audit_logger = _MagicMock()

import pyotp
from fastapi.testclient import TestClient

from src.python.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_mfa_singletons():
    import src.python.api.routers.auth as auth_mod
    auth_mod._mfa_manager = None
    auth_mod._mfa_enrollment = None
    yield
    auth_mod._mfa_manager = None
    auth_mod._mfa_enrollment = None


class TestMFAEnroll:
    def test_enroll_totp(self, client):
        resp = client.post("/api/v1/auth/mfa/enroll", json={
            "user_id": "u-1",
            "email": "user@example.com",
            "method": "totp",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "u-1"
        assert data["method"] == "totp"
        assert len(data["secret"]) > 0
        assert len(data["backup_codes"]) == 10
        assert data["status"] == "pending_verification"

    def test_enroll_unsupported_method(self, client):
        resp = client.post("/api/v1/auth/mfa/enroll", json={
            "user_id": "u-1",
            "email": "user@example.com",
            "method": "sms",
        })
        assert resp.status_code == 400

    def test_enroll_invalid_method(self, client):
        resp = client.post("/api/v1/auth/mfa/enroll", json={
            "user_id": "u-1",
            "email": "user@example.com",
            "method": "carrier_pigeon",
        })
        assert resp.status_code == 400


class TestMFAVerify:
    def test_verify_valid_token(self, client):
        enroll_resp = client.post("/api/v1/auth/mfa/enroll", json={
            "user_id": "u-1",
            "email": "user@example.com",
            "method": "totp",
        })
        secret = enroll_resp.json()["secret"]
        token = pyotp.TOTP(secret).now()

        resp = client.post("/api/v1/auth/mfa/verify", json={
            "user_id": "u-1",
            "token": token,
            "secret": secret,
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_verify_invalid_token(self, client):
        enroll_resp = client.post("/api/v1/auth/mfa/enroll", json={
            "user_id": "u-2",
            "email": "user2@example.com",
            "method": "totp",
        })
        secret = enroll_resp.json()["secret"]

        resp = client.post("/api/v1/auth/mfa/verify", json={
            "user_id": "u-2",
            "token": "000000",
            "secret": secret,
        })
        assert resp.status_code == 401

    def test_verify_no_secret(self, client):
        resp = client.post("/api/v1/auth/mfa/verify", json={
            "user_id": "u-1",
            "token": "123456",
        })
        assert resp.status_code == 400

    def test_verify_backup_code(self, client):
        enroll_resp = client.post("/api/v1/auth/mfa/enroll", json={
            "user_id": "u-3",
            "email": "user3@example.com",
            "method": "totp",
        })
        data = enroll_resp.json()
        secret = data["secret"]
        import hashlib
        backup = data["backup_codes"][0]
        hashed = hashlib.sha256(backup.encode()).hexdigest()

        resp = client.post("/api/v1/auth/mfa/verify", json={
            "user_id": "u-3",
            "token": backup,
            "secret": secret,
            "hashed_backup_codes": [hashed],
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_verify_lockout(self, client):
        enroll_resp = client.post("/api/v1/auth/mfa/enroll", json={
            "user_id": "u-lock",
            "email": "lock@example.com",
            "method": "totp",
        })
        secret = enroll_resp.json()["secret"]

        for _ in range(3):
            client.post("/api/v1/auth/mfa/verify", json={
                "user_id": "u-lock",
                "token": "000000",
                "secret": secret,
            })

        resp = client.post("/api/v1/auth/mfa/verify", json={
            "user_id": "u-lock",
            "token": "000000",
            "secret": secret,
        })
        assert resp.status_code == 429


class TestMFAStatus:
    def test_status_no_lockout(self, client):
        resp = client.get("/api/v1/auth/mfa/status/u-new")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "u-new"
        assert data["is_locked_out"] is False

    def test_status_locked_out(self, client):
        enroll_resp = client.post("/api/v1/auth/mfa/enroll", json={
            "user_id": "u-status-lock",
            "email": "sl@example.com",
            "method": "totp",
        })
        secret = enroll_resp.json()["secret"]
        for _ in range(3):
            client.post("/api/v1/auth/mfa/verify", json={
                "user_id": "u-status-lock",
                "token": "000000",
                "secret": secret,
            })

        resp = client.get("/api/v1/auth/mfa/status/u-status-lock")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_locked_out"] is True
        assert data["lockout_remaining_seconds"] > 0


class TestMFADisable:
    def test_disable_success(self, client):
        enroll_resp = client.post("/api/v1/auth/mfa/enroll", json={
            "user_id": "u-dis",
            "email": "dis@example.com",
            "method": "totp",
        })
        secret = enroll_resp.json()["secret"]
        token = pyotp.TOTP(secret).now()

        resp = client.post("/api/v1/auth/mfa/disable", json={
            "user_id": "u-dis",
            "secret": secret,
            "token": token,
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_disable_invalid_token(self, client):
        enroll_resp = client.post("/api/v1/auth/mfa/enroll", json={
            "user_id": "u-dis2",
            "email": "dis2@example.com",
            "method": "totp",
        })
        secret = enroll_resp.json()["secret"]

        resp = client.post("/api/v1/auth/mfa/disable", json={
            "user_id": "u-dis2",
            "secret": secret,
            "token": "000000",
        })
        assert resp.status_code == 401
