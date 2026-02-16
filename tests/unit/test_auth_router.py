"""Tests for src.python.api.routers.auth — MFA API endpoints."""
import os
import pytest

os.environ.setdefault("AUDIT_LOG_DIR", "/tmp/janusgraph-test-logs")

from unittest.mock import patch, MagicMock
from unittest.mock import patch as _patch, MagicMock as _MagicMock
with _patch("banking.compliance.audit_logger.AuditLogger.__init__", lambda self, *a, **kw: None):
    with _patch("banking.compliance.audit_logger.AuditLogger.log_event", _MagicMock()):
        import banking.compliance.audit_logger as _al
        _al._audit_logger = _MagicMock()

try:
    import pyotp
except ModuleNotFoundError:
    pyotp = None

from src.python.api import dependencies as api_dependencies
from src.python.config import settings as settings_module
from fastapi.testclient import TestClient

from src.python.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_mfa_singletons(tmp_path, monkeypatch):
    import src.python.api.routers.auth as auth_mod
    settings = settings_module.get_settings()
    original_user_roles = settings.api_user_roles
    original_required_roles = settings.mfa_required_roles

    monkeypatch.setenv("JANUSGRAPH_MFA_STORE_PATH", str(tmp_path / "mfa-store.json"))
    auth_mod._mfa_manager = None
    auth_mod._mfa_enrollment = None
    auth_mod._login_challenges.clear()
    api_dependencies.clear_auth_session_manager()
    settings.api_user_roles = original_user_roles
    settings.mfa_required_roles = original_required_roles

    yield

    auth_mod._mfa_manager = None
    auth_mod._mfa_enrollment = None
    auth_mod._login_challenges.clear()
    api_dependencies.clear_auth_session_manager()
    settings.api_user_roles = original_user_roles
    settings.mfa_required_roles = original_required_roles


def _require_pyotp() -> None:
    if pyotp is None:
        pytest.skip("pyotp is required to run MFA tests")


class TestAuthFlow:
    def test_login_without_mfa(self, client):
        settings = settings_module.get_settings()
        settings.api_user_roles = "user"

        resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "ignored"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["user_id"] == "admin"
        assert data["mfa_required"] is False
        assert data["roles"] == ["user"]
        assert data["access_token"] is not None
        assert data["refresh_token"] is not None
        assert data["session_id"] is not None
        assert data["token_type"] == "Bearer"

    def test_login_rejects_invalid_credentials(self, client):
        resp = client.post("/api/v1/auth/login", json={"username": "not-admin", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_with_mfa_challenge(self, client):
        _require_pyotp()
        settings = settings_module.get_settings()
        settings.api_user_roles = "admin"

        resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "ignored"})
        assert resp.status_code == 200
        challenge = resp.json()
        assert challenge["mfa_required"] is True
        assert "mfa_login_challenge" in challenge
        assert "mfa_secret" in challenge
        assert challenge["session_id"] is None

        token = pyotp.TOTP(challenge["mfa_secret"]).now()
        completed = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "ignored",
                "mfa_login_challenge": challenge["mfa_login_challenge"],
                "mfa_token": token,
            },
        )
        assert completed.status_code == 200
        data = completed.json()
        assert data["mfa_required"] is False
        assert data["access_token"] is not None
        assert data["refresh_token"] is not None
        assert data["session_id"] is not None

    def test_refresh_session(self, client):
        settings = settings_module.get_settings()
        settings.api_user_roles = "user"

        login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "ignored"})
        login_data = login_resp.json()
        resp = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": login_data["refresh_token"],
                "session_id": login_data["session_id"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["session_id"] == login_data["session_id"]
        assert data["access_token"] is not None
        assert data["refresh_token"] is not None
        assert data["refresh_token"] != login_data["refresh_token"]

    def test_refresh_session_invalid_token(self, client):
        settings = settings_module.get_settings()
        settings.api_user_roles = "user"

        login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "ignored"})
        login_data = login_resp.json()
        resp = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": "wrong-refresh-token-not-valid-format-at-least-thirty-two-chars",
                "session_id": login_data["session_id"],
            },
        )
        assert resp.status_code == 401

    def test_logout_with_session_id(self, client):
        settings = settings_module.get_settings()
        settings.api_user_roles = "user"

        login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "ignored"})
        session_id = login_resp.json()["session_id"]

        resp = client.post("/api/v1/auth/logout", json={"session_id": session_id})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_logout_with_bearer_authorization(self, client):
        settings = settings_module.get_settings()
        settings.api_user_roles = "user"

        login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "ignored"})
        login_data = login_resp.json()

        resp = client.post(
            "/api/v1/auth/logout",
            json={},
            headers={"Authorization": f"Bearer {login_data['access_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_logout_missing_session_or_token(self, client):
        resp = client.post("/api/v1/auth/logout", json={})
        assert resp.status_code == 400


class TestMFAEnroll:
    def test_enroll_totp(self, client):
        _require_pyotp()
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
        _require_pyotp()
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
        _require_pyotp()
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
        _require_pyotp()
        resp = client.post("/api/v1/auth/mfa/verify", json={
            "user_id": "u-1",
            "token": "123456",
        })
        assert resp.status_code == 400

    def test_verify_enrollment_activates_user(self, client):
        _require_pyotp()
        user_id = "admin"
        enroll_resp = client.post(
            "/api/v1/auth/mfa/enroll",
            json={
                "user_id": user_id,
                "email": "admin@example.com",
                "method": "totp",
            },
        )
        secret = enroll_resp.json()["secret"]
        token = pyotp.TOTP(secret).now()

        verify_resp = client.post(
            "/api/v1/auth/mfa/verify",
            json={
                "user_id": user_id,
                "token": token,
                "secret": secret,
            },
        )
        assert verify_resp.status_code == 200

        status_resp = client.get(f"/api/v1/auth/mfa/status/{user_id}")
        status = status_resp.json()
        assert status["is_enrolled"] is True
        assert status["status"] == "active"
        assert status["method"] == "totp"
        assert status["backup_codes_remaining"] == 10

    def test_verify_login_uses_enrolled_secret(self, client):
        _require_pyotp()
        user_id = "admin"
        enroll_resp = client.post(
            "/api/v1/auth/mfa/enroll",
            json={
                "user_id": user_id,
                "email": "admin@example.com",
                "method": "totp",
            },
        )
        secret = enroll_resp.json()["secret"]
        token = pyotp.TOTP(secret).now()

        verify_resp = client.post(
            "/api/v1/auth/mfa/verify",
            json={
                "user_id": user_id,
                "token": token,
                "secret": secret,
            },
        )
        assert verify_resp.status_code == 200

        settings = settings_module.get_settings()
        settings.api_user_roles = "admin"
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "ignored"},
        )
        challenge = login_resp.json()
        assert challenge["mfa_required"] is True
        assert challenge["mfa_secret"] == secret

    def test_verify_backup_code(self, client):
        _require_pyotp()
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
        _require_pyotp()
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
        _require_pyotp()
        resp = client.get("/api/v1/auth/mfa/status/u-new")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "u-new"
        assert data["is_locked_out"] is False
        assert data["is_enrolled"] is False

    def test_status_locked_out(self, client):
        _require_pyotp()
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
        _require_pyotp()
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

    def test_disable_removes_enrollment(self, client):
        _require_pyotp()
        user_id = "admin"
        enroll_resp = client.post(
            "/api/v1/auth/mfa/enroll",
            json={
                "user_id": user_id,
                "email": "admin2@example.com",
                "method": "totp",
            },
        )
        secret = enroll_resp.json()["secret"]
        token = pyotp.TOTP(secret).now()

        verify_resp = client.post(
            "/api/v1/auth/mfa/verify",
            json={
                "user_id": user_id,
                "token": token,
                "secret": secret,
            },
        )
        assert verify_resp.status_code == 200

        resp = client.post(
            "/api/v1/auth/mfa/disable",
            json={
                "user_id": user_id,
                "secret": secret,
                "token": pyotp.TOTP(secret).now(),
            },
        )
        assert resp.status_code == 200

        status_resp = client.get(f"/api/v1/auth/mfa/status/{user_id}")
        status = status_resp.json()
        assert status["is_enrolled"] is False

    def test_disable_invalid_token(self, client):
        _require_pyotp()
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
