"""Tests for session management — JWT tokens, concurrent limits, revocation."""

import time

import pytest

import importlib.util
import sys
from pathlib import Path

_STRONG_TEST_SECRET = "unit-test-secret-key-for-session-manager-strong-32chars"

# Load module directly to avoid src.python.security.__init__ triggering audit logger
_spec = importlib.util.spec_from_file_location(
    "session_manager",
    Path(__file__).resolve().parents[2] / "src" / "python" / "security" / "session_manager.py",
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["session_manager"] = _mod
_spec.loader.exec_module(_mod)
SessionConfig = _mod.SessionConfig
SessionError = _mod.SessionError
SessionManager = _mod.SessionManager


@pytest.fixture
def mgr():
    config = SessionConfig(
        secret_key=_STRONG_TEST_SECRET,
        access_token_ttl_minutes=1,
        refresh_token_ttl_minutes=60,
        max_concurrent_sessions=3,
    )
    return SessionManager(config)


class TestCreateSession:
    def test_returns_tokens(self, mgr):
        result = mgr.create_session("user1", roles=["admin"])
        assert "access_token" in result
        assert "refresh_token" in result
        assert "session_id" in result
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 60

    def test_multiple_sessions(self, mgr):
        r1 = mgr.create_session("user1")
        r2 = mgr.create_session("user1")
        assert r1["session_id"] != r2["session_id"]

    def test_stores_metadata(self, mgr):
        mgr.create_session("user1", ip_address="1.2.3.4", user_agent="TestBot")
        sessions = mgr.get_active_sessions("user1")
        assert len(sessions) == 1
        assert sessions[0]["ip_address"] == "1.2.3.4"
        assert sessions[0]["user_agent"] == "TestBot"


class TestConcurrentSessionLimits:
    def test_evicts_oldest_when_limit_exceeded(self, mgr):
        sessions = []
        for i in range(4):
            s = mgr.create_session("user1")
            sessions.append(s)

        active = mgr.get_active_sessions("user1")
        assert len(active) == 3

        first_id = sessions[0]["session_id"]
        active_ids = {s["session_id"] for s in active}
        assert first_id not in active_ids

    def test_respects_limit(self, mgr):
        for _ in range(3):
            mgr.create_session("user1")
        assert len(mgr.get_active_sessions("user1")) == 3


class TestVerifyAccessToken:
    def test_valid_token(self, mgr):
        result = mgr.create_session("user1", roles=["admin"])
        payload = mgr.verify_access_token(result["access_token"])
        assert payload["sub"] == "user1"
        assert payload["roles"] == ["admin"]
        assert payload["sid"] == result["session_id"]

    def test_invalid_token(self, mgr):
        with pytest.raises(SessionError, match="Invalid access token"):
            mgr.verify_access_token("not.a.valid.token")

    def test_revoked_session_token(self, mgr):
        result = mgr.create_session("user1")
        mgr.revoke_session(result["session_id"])
        with pytest.raises(SessionError, match="Session no longer valid"):
            mgr.verify_access_token(result["access_token"])


class TestRefreshSession:
    def test_refresh_returns_new_tokens(self, mgr):
        original = mgr.create_session("user1")
        refreshed = mgr.refresh_session(
            original["refresh_token"], original["session_id"]
        )
        assert refreshed["session_id"] == original["session_id"]
        assert "access_token" in refreshed
        assert refreshed["refresh_token"] != original["refresh_token"]

    def test_refresh_rotates_refresh_token(self, mgr):
        original = mgr.create_session("user1")
        refreshed = mgr.refresh_session(
            original["refresh_token"], original["session_id"]
        )
        assert refreshed["refresh_token"] != original["refresh_token"]

        with pytest.raises(SessionError, match="Invalid refresh token"):
            mgr.refresh_session(original["refresh_token"], original["session_id"])

    def test_refresh_without_rotation(self):
        config = SessionConfig(
            secret_key=_STRONG_TEST_SECRET,
            rotate_refresh_on_use=False,
        )
        mgr = SessionManager(config)
        original = mgr.create_session("user1")
        refreshed = mgr.refresh_session(
            original["refresh_token"], original["session_id"]
        )
        assert refreshed["refresh_token"] == original["refresh_token"]

    def test_refresh_invalid_session(self, mgr):
        with pytest.raises(SessionError, match="Session not found"):
            mgr.refresh_session("token", "nonexistent")

    def test_refresh_revoked_session(self, mgr):
        result = mgr.create_session("user1")
        mgr.revoke_session(result["session_id"])
        with pytest.raises(SessionError, match="revoked"):
            mgr.refresh_session(result["refresh_token"], result["session_id"])

    def test_refresh_wrong_token_revokes_session(self, mgr):
        result = mgr.create_session("user1")
        with pytest.raises(SessionError, match="Invalid refresh token"):
            mgr.refresh_session("wrong-token", result["session_id"])
        with pytest.raises(SessionError, match="revoked"):
            mgr.refresh_session(result["refresh_token"], result["session_id"])


class TestRevokeSession:
    def test_revoke_existing(self, mgr):
        result = mgr.create_session("user1")
        assert mgr.revoke_session(result["session_id"]) is True
        assert len(mgr.get_active_sessions("user1")) == 0

    def test_revoke_nonexistent(self, mgr):
        assert mgr.revoke_session("nonexistent") is False


class TestRevokeAllUserSessions:
    def test_revokes_all(self, mgr):
        for _ in range(3):
            mgr.create_session("user1")
        mgr.create_session("user2")

        count = mgr.revoke_all_user_sessions("user1")
        assert count == 3
        assert len(mgr.get_active_sessions("user1")) == 0
        assert len(mgr.get_active_sessions("user2")) == 1


class TestGetActiveSessions:
    def test_excludes_revoked(self, mgr):
        r1 = mgr.create_session("user1")
        mgr.create_session("user1")
        mgr.revoke_session(r1["session_id"])
        assert len(mgr.get_active_sessions("user1")) == 1

    def test_empty_for_unknown_user(self, mgr):
        assert mgr.get_active_sessions("nobody") == []


class TestCleanupExpired:
    def test_cleanup_revoked(self, mgr):
        r = mgr.create_session("user1")
        mgr.revoke_session(r["session_id"])
        removed = mgr.cleanup_expired()
        assert removed == 1
        assert mgr.get_active_sessions("user1") == []


class TestExpiredTokens:
    def test_expired_access_token(self):
        config = SessionConfig(
            secret_key=_STRONG_TEST_SECRET,
            access_token_ttl_minutes=0,
        )
        mgr = SessionManager(config)
        result = mgr.create_session("user1")
        time.sleep(1)
        with pytest.raises(SessionError, match="expired"):
            mgr.verify_access_token(result["access_token"])


class TestSessionSecretValidation:
    def test_rejects_short_secret(self):
        with pytest.raises(ValueError, match="Session secret key is too weak"):
            SessionManager(SessionConfig(secret_key="short-key"))

    def test_accepts_long_high_entropy_secret(self):
        secret = "0123456789abcdef" * 4
        mgr = SessionManager(SessionConfig(secret_key=secret))
        assert mgr.config.secret_key == secret
