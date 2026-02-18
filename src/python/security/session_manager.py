"""
Session Management
===================

JWT-based session management with:
- Access + refresh token pairs
- Concurrent session limits per user
- Token refresh / rotation
- Session revocation
"""

import hashlib
import logging
import math
import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import jwt

logger = logging.getLogger(__name__)

_DEFAULT_SECRET = ""
_MIN_SECRET_LENGTH = 32
_MIN_SECRET_ENTROPY_BITS = 128.0


_KNOWN_WEAK_SECRETS = {
    "changeit",
    "password",
    "changeme",
    "default_secret",
    "secret",
}


def _is_weak_secret(secret: str) -> bool:
    if len(secret) < _MIN_SECRET_LENGTH:
        return True
    normalized = secret.strip()
    if not normalized:
        return True

    lowered = normalized.lower()
    return (
        lowered in _KNOWN_WEAK_SECRETS
        or len(set(lowered)) == 1
        or (math.log2(len(set(lowered)) or 1) * len(lowered)) < _MIN_SECRET_ENTROPY_BITS
    )


@dataclass
class SessionConfig:
    secret_key: str = _DEFAULT_SECRET
    algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_minutes: int = 1440  # 24 hours
    max_concurrent_sessions: int = 5
    rotate_refresh_on_use: bool = True
    issuer: str = "graph-analytics-api"


@dataclass
class Session:
    session_id: str
    user_id: str
    refresh_token_hash: str
    created_at: datetime
    last_active: datetime
    expires_at: datetime
    roles: List[str] = field(default_factory=list)
    mfa_verified: bool = False
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    revoked: bool = False


class SessionManager:
    """In-memory session store. Swap with Redis for production clustering."""

    def __init__(self, config: SessionConfig | None = None):
        self.config = config or SessionConfig()
        if not self.config.secret_key:
            raise ValueError("Session secret key must be configured and non-empty.")
        if _is_weak_secret(self.config.secret_key):
            raise ValueError("Session secret key is too weak. Use a strong secret (>=32 chars).")
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, List[str]] = {}
        self._lock = threading.Lock()

    def create_session(
        self,
        user_id: str,
        roles: List[str] | None = None,
        mfa_verified: bool = False,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        with self._lock:
            self._enforce_concurrent_limit(user_id)

            session_id = secrets.token_urlsafe(32)
            now = datetime.now(timezone.utc)

            access_token = self._issue_access_token(
                user_id,
                session_id,
                roles or [],
                mfa_verified=mfa_verified,
            )
            refresh_token = secrets.token_urlsafe(48)
            refresh_hash = self._hash(refresh_token)

            session = Session(
                session_id=session_id,
                user_id=user_id,
                refresh_token_hash=refresh_hash,
                created_at=now,
                last_active=now,
                expires_at=now + timedelta(minutes=self.config.refresh_token_ttl_minutes),
                roles=roles or [],
                mfa_verified=mfa_verified,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self._sessions[session_id] = session
            self._user_sessions.setdefault(user_id, []).append(session_id)

            logger.info("Session created: user=%s session=%s", user_id, session_id)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "session_id": session_id,
                "token_type": "Bearer",
                "expires_in": self.config.access_token_ttl_minutes * 60,
            }

    def refresh_session(self, refresh_token: str, session_id: str) -> dict:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionError("Session not found")
            if session.revoked:
                raise SessionError("Session has been revoked")

            now = datetime.now(timezone.utc)
            if now > session.expires_at:
                self._remove_session(session_id)
                raise SessionError("Refresh token expired")

            if self._hash(refresh_token) != session.refresh_token_hash:
                session.revoked = True
                logger.warning(
                    "Refresh token mismatch — possible theft, revoking session %s",
                    session_id,
                )
                raise SessionError("Invalid refresh token — session revoked")

            access_token = self._issue_access_token(
                session.user_id,
                session_id,
                session.roles,
                mfa_verified=session.mfa_verified,
            )

            new_refresh_token = refresh_token
            if self.config.rotate_refresh_on_use:
                new_refresh_token = secrets.token_urlsafe(48)
                session.refresh_token_hash = self._hash(new_refresh_token)

            session.last_active = now
            session.expires_at = now + timedelta(minutes=self.config.refresh_token_ttl_minutes)

            logger.info("Session refreshed: session=%s", session_id)

            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "session_id": session_id,
                "token_type": "Bearer",
                "expires_in": self.config.access_token_ttl_minutes * 60,
            }

    def verify_access_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
            )
        except jwt.ExpiredSignatureError:
            raise SessionError("Access token expired")
        except jwt.InvalidTokenError as exc:
            raise SessionError(f"Invalid access token: {exc}")

        session_id = payload.get("sid")
        if session_id:
            session = self._sessions.get(session_id)
            if session is None or session.revoked:
                raise SessionError("Session no longer valid")

        return payload

    def revoke_session(self, session_id: str) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            session.revoked = True
            logger.info("Session revoked: %s", session_id)
            return True

    def revoke_all_user_sessions(self, user_id: str) -> int:
        with self._lock:
            ids = self._user_sessions.get(user_id, [])
            count = 0
            for sid in ids:
                s = self._sessions.get(sid)
                if s and not s.revoked:
                    s.revoked = True
                    count += 1
            logger.info("Revoked %d sessions for user %s", count, user_id)
            return count

    def get_active_sessions(self, user_id: str) -> List[dict]:
        now = datetime.now(timezone.utc)
        result = []
        for sid in self._user_sessions.get(user_id, []):
            s = self._sessions.get(sid)
            if s and not s.revoked and now < s.expires_at:
                result.append(
                    {
                        "session_id": s.session_id,
                        "created_at": s.created_at.isoformat(),
                        "last_active": s.last_active.isoformat(),
                        "ip_address": s.ip_address,
                        "user_agent": s.user_agent,
                    }
                )
        return result

    def cleanup_expired(self) -> int:
        with self._lock:
            now = datetime.now(timezone.utc)
            expired = [sid for sid, s in self._sessions.items() if s.revoked or now > s.expires_at]
            for sid in expired:
                self._remove_session(sid)
            return len(expired)

    def _enforce_concurrent_limit(self, user_id: str) -> None:
        now = datetime.now(timezone.utc)
        active_ids = [
            sid
            for sid in self._user_sessions.get(user_id, [])
            if sid in self._sessions
            and not self._sessions[sid].revoked
            and now < self._sessions[sid].expires_at
        ]

        while len(active_ids) >= self.config.max_concurrent_sessions:
            oldest = min(active_ids, key=lambda s: self._sessions[s].created_at)
            self._sessions[oldest].revoked = True
            active_ids.remove(oldest)
            logger.info(
                "Evicted oldest session %s for user %s (concurrent limit)",
                oldest,
                user_id,
            )

    def _remove_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session:
            user_ids = self._user_sessions.get(session.user_id, [])
            if session_id in user_ids:
                user_ids.remove(session_id)

    def _issue_access_token(
        self,
        user_id: str,
        session_id: str,
        roles: List[str],
        *,
        mfa_verified: bool = False,
    ) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "sid": session_id,
            "roles": roles,
            "mfa_verified": mfa_verified,
            "iss": self.config.issuer,
            "iat": now,
            "exp": now + timedelta(minutes=self.config.access_token_ttl_minutes),
        }
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()


class SessionError(Exception):
    pass
