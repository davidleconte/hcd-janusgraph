"""
Multi-Factor Authentication (MFA) Module

Provides TOTP-based multi-factor authentication for enhanced security.
Supports QR code generation, backup codes, and MFA enforcement policies.
"""

import json
import hashlib
import logging
import os
import tempfile
import threading
from pathlib import Path
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import pyotp
import qrcode

logger = logging.getLogger(__name__)


class MFAMethod(Enum):
    """MFA authentication methods."""

    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODE = "backup_code"


@dataclass
class MFAConfig:
    """MFA configuration."""

    issuer: str = "JanusGraph"
    algorithm: str = "SHA1"
    digits: int = 6
    interval: int = 30
    backup_codes_count: int = 10
    backup_code_length: int = 8
    max_attempts: int = 3
    lockout_duration: int = 300  # seconds
    require_mfa_for_roles: List[str] = None

    def __post_init__(self):
        if self.require_mfa_for_roles is None:
            self.require_mfa_for_roles = ["admin", "developer"]


class MFAManager:
    """Manages multi-factor authentication operations."""

    def __init__(self, config: MFAConfig = None):
        """
        Initialize MFA manager.

        Args:
            config: MFA configuration
        """
        self.config = config or MFAConfig()
        self.failed_attempts = {}  # Track failed attempts
        logger.info("MFA Manager initialized")

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret.

        Returns:
            Base32-encoded secret
        """
        secret = pyotp.random_base32()
        logger.debug("Generated new TOTP secret")
        return secret

    def setup_totp(self, user_id: str, user_email: str) -> Tuple[str, bytes]:
        """
        Setup TOTP for a user.

        Args:
            user_id: User identifier
            user_email: User email address

        Returns:
            Tuple of (secret, qr_code_image)
        """
        try:
            # Generate secret
            secret = self.generate_secret()

            # Create TOTP URI
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=user_email, issuer_name=self.config.issuer
            )

            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to bytes
            img_buffer = BytesIO()
            img.save(img_buffer, format="PNG")
            img_bytes = img_buffer.getvalue()

            logger.info("TOTP setup completed for user: %s", user_id)

            return secret, img_bytes

        except Exception as e:
            logger.error("Failed to setup TOTP for user %s: %s", user_id, e)
            raise

    def verify_totp(self, secret: str, token: str, user_id: str = None) -> bool:
        """
        Verify a TOTP token.

        Args:
            secret: User's TOTP secret
            token: Token to verify
            user_id: Optional user ID for logging

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Check if user is locked out
            if user_id and self._is_locked_out(user_id):
                logger.warning("MFA verification blocked - user locked out: %s", user_id)
                return False

            # Verify token
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(token, valid_window=1)

            if is_valid:
                logger.info("TOTP verification successful for user: %s", user_id)
                self._reset_failed_attempts(user_id)
            else:
                logger.warning("TOTP verification failed for user: %s", user_id)
                self._record_failed_attempt(user_id)

            return is_valid

        except Exception as e:
            logger.error("Error verifying TOTP: %s", e)
            return False

    def generate_backup_codes(self, count: int = None) -> List[str]:
        """
        Generate backup codes for account recovery.

        Args:
            count: Number of codes to generate

        Returns:
            List of backup codes
        """
        count = count or self.config.backup_codes_count
        codes = []

        for _ in range(count):
            code = self._generate_backup_code()
            codes.append(code)

        logger.info("Generated %d backup codes", count)
        return codes

    def _generate_backup_code(self) -> str:
        """
        Generate a single backup code.

        Returns:
            Backup code string
        """
        # Generate random bytes
        random_bytes = secrets.token_bytes(self.config.backup_code_length)

        # Convert to alphanumeric string
        code = "".join(format(b, "02x") for b in random_bytes)[: self.config.backup_code_length]

        return code.upper()

    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for storage.

        Args:
            code: Backup code to hash

        Returns:
            Hashed code
        """
        return hashlib.sha256(code.encode()).hexdigest()

    def verify_backup_code(self, code: str, hashed_codes: List[str]) -> bool:
        """
        Verify a backup code against stored hashes.

        Args:
            code: Code to verify
            hashed_codes: List of hashed backup codes

        Returns:
            True if code is valid, False otherwise
        """
        code_hash = self.hash_backup_code(code)

        if code_hash in hashed_codes:
            logger.info("Backup code verification successful")
            return True
        else:
            logger.warning("Backup code verification failed")
            return False

    def _record_failed_attempt(self, user_id: str):
        """
        Record a failed MFA attempt.

        Args:
            user_id: User identifier
        """
        if not user_id:
            return

        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = {
                "count": 0,
                "first_attempt": datetime.now(timezone.utc),
            }

        self.failed_attempts[user_id]["count"] += 1
        self.failed_attempts[user_id]["last_attempt"] = datetime.now(timezone.utc)

        if self.failed_attempts[user_id]["count"] >= self.config.max_attempts:
            logger.warning(
                "User %s locked out after %d failed MFA attempts", user_id, self.config.max_attempts
            )

    def _reset_failed_attempts(self, user_id: str):
        """
        Reset failed attempt counter.

        Args:
            user_id: User identifier
        """
        if user_id and user_id in self.failed_attempts:
            del self.failed_attempts[user_id]

    def _is_locked_out(self, user_id: str) -> bool:
        """
        Check if user is locked out due to failed attempts.

        Args:
            user_id: User identifier

        Returns:
            True if locked out, False otherwise
        """
        if user_id not in self.failed_attempts:
            return False

        attempts = self.failed_attempts[user_id]

        if attempts["count"] < self.config.max_attempts:
            return False

        # Check if lockout period has expired
        lockout_end = attempts["last_attempt"] + timedelta(seconds=self.config.lockout_duration)

        if datetime.now(timezone.utc) > lockout_end:
            # Lockout expired, reset
            self._reset_failed_attempts(user_id)
            return False

        return True

    def get_lockout_remaining(self, user_id: str) -> Optional[int]:
        """
        Get remaining lockout time in seconds.

        Args:
            user_id: User identifier

        Returns:
            Remaining seconds or None if not locked out
        """
        if not self._is_locked_out(user_id):
            return None

        attempts = self.failed_attempts[user_id]
        lockout_end = attempts["last_attempt"] + timedelta(seconds=self.config.lockout_duration)

        remaining = (lockout_end - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(remaining))

    def is_mfa_required(self, user_roles: List[str]) -> bool:
        """
        Check if MFA is required for given roles.

        Args:
            user_roles: List of user roles

        Returns:
            True if MFA is required, False otherwise
        """
        return any(role in self.config.require_mfa_for_roles for role in user_roles)


class MFAEnrollment:
    """Manages MFA enrollment for users."""

    def __init__(self, mfa_manager: MFAManager, storage_path: str = None):
        """
        Initialize MFA enrollment manager.

        Args:
            mfa_manager: MFA manager instance
            storage_path: Optional path for storing enrollment records.
        """
        self.mfa_manager = mfa_manager
        self._lock = threading.Lock()
        self._storage_path = Path(
            storage_path
            or os.getenv(
                "JANUSGRAPH_MFA_STORE_PATH",
                str(Path(tempfile.gettempdir()) / "janusgraph_mfa_enrollment.json"),
            )
        )
        self._enrollments = self._load_enrollments()

    def get_user_enrollment(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Return stored enrollment data for a user, if any."""
        with self._lock:
            record = self._enrollments.get(user_id)
        if not record:
            return None
        return {**record}

    def is_user_enrolled(self, user_id: str) -> bool:
        """Return True if the user has an active enrollment."""
        data = self.get_user_enrollment(user_id)
        return bool(data and data.get("status") == "active")

    def enroll_user(
        self, user_id: str, user_email: str, method: MFAMethod = MFAMethod.TOTP
    ) -> dict:
        """
        Enroll user in MFA.

        Args:
            user_id: User identifier
            user_email: User email
            method: MFA method to enroll

        Returns:
            Enrollment data including secret and QR code
        """
        if method == MFAMethod.TOTP:
            secret, qr_code = self.mfa_manager.setup_totp(user_id, user_email)
            backup_codes = self.mfa_manager.generate_backup_codes()

            # Hash backup codes for storage
            hashed_codes = [self.mfa_manager.hash_backup_code(code) for code in backup_codes]

            now = datetime.now(timezone.utc).isoformat()
            enrollment_data = {
                "user_id": user_id,
                "method": method.value,
                "secret": secret,
                "qr_code": qr_code,
                "backup_codes": backup_codes,
                "hashed_backup_codes": hashed_codes,
                "enrolled_at": now,
                "updated_at": now,
                "status": "pending_verification",
            }

            self._save_user_enrollment(user_id, enrollment_data)

            logger.info("User %s enrolled in MFA (TOTP)", user_id)
            return enrollment_data

        else:
            raise NotImplementedError(f"MFA method {method} not implemented")

    def verify_enrollment(self, user_id: str, secret: str, token: str) -> bool:
        """
        Verify MFA enrollment with initial token.

        Args:
            user_id: User identifier
            secret: User's TOTP secret
            token: Verification token

        Returns:
            True if enrollment verified, False otherwise
        """
        enrolled_data = self.get_user_enrollment(user_id)
        expected_secret = enrolled_data.get("secret") if enrolled_data else secret
        hashed_backup_codes = []
        if enrolled_data:
            hashed_backup_codes = enrolled_data.get("hashed_backup_codes", [])
            if enrolled_data.get("status") == "active":
                hashed_backup_codes = []

        is_valid = self.mfa_manager.verify_totp(expected_secret, token, user_id)

        if not is_valid and hashed_backup_codes:
            is_valid = self.mfa_manager.verify_backup_code(token, hashed_backup_codes)
            if is_valid and expected_secret:
                self.consume_backup_code(user_id, token)

        if is_valid and enrolled_data:
            enrolled_data["status"] = "active"
            enrolled_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save_user_enrollment(user_id, enrolled_data)
            logger.info("MFA enrollment verified for user: %s", user_id)
        elif is_valid:
            logger.info(
                "MFA enrollment verification passed for untracked user: %s",
                user_id,
            )
        else:
            logger.warning("MFA enrollment verification failed for user: %s", user_id)

        return is_valid

    def unenroll_user(self, user_id: str, reason: str = None):
        """
        Unenroll user from MFA.

        Args:
            user_id: User identifier
            reason: Optional reason for unenrollment
        """
        self._remove_user_enrollment(user_id)
        logger.info("User %s unenrolled from MFA. Reason: %s", user_id, reason)

    def consume_backup_code(self, user_id: str, token: str) -> bool:
        """
        Consume a backup code if it is valid and tracked for the user.

        Args:
            user_id: User identifier
            token: Backup code to consume

        Returns:
            True when the code was consumed
        """
        if not user_id or not token:
            return False

        record = self.get_user_enrollment(user_id)
        if not record:
            return False

        stored_codes = record.get("hashed_backup_codes", [])
        return self._consume_backup_code(user_id, token, stored_codes)

    def _load_enrollments(self) -> Dict[str, Dict[str, Any]]:
        """Load persisted enrollment records from storage."""
        if not self._storage_path.exists():
            return {}

        try:
            with self._storage_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return {
                    user_id: enrollment
                    for user_id, enrollment in data.items()
                    if isinstance(user_id, str) and isinstance(enrollment, dict)
                }
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load MFA enrollments from %s: %s", self._storage_path, exc)
        return {}

    def _save_user_enrollment(self, user_id: str, data: Dict[str, Any]) -> None:
        """Persist a user enrollment record."""
        if not user_id:
            return
        with self._lock:
            self._enrollments[user_id] = {k: v for k, v in data.items() if k != "qr_code"}
            self._persist_enrollments()

    def _remove_user_enrollment(self, user_id: str) -> None:
        """Remove a user enrollment record."""
        with self._lock:
            if self._enrollments.pop(user_id, None) is not None:
                self._persist_enrollments()

    def _persist_enrollments(self) -> None:
        """Write enrollment records to disk."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._storage_path.with_suffix(".tmp")
        payload = {
            user_id: {
                k: v
                for k, v in record.items()
                if k != "qr_code" and k != "backup_codes"
            }
            for user_id, record in self._enrollments.items()
        }
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        tmp_path.replace(self._storage_path)

    def _consume_backup_code(
        self, user_id: str, token: str, hashed_backup_codes: List[str]
    ) -> bool:
        """
        Remove a consumed backup code from the stored list.
        """
        if not user_id or not token:
            return False
        code_hash = self.mfa_manager.hash_backup_code(token)
        if code_hash not in hashed_backup_codes:
            return False
        try:
            with self._lock:
                record = self._enrollments.get(user_id)
                if not record:
                    return False
                record_codes = record.get("hashed_backup_codes", [])
                if code_hash in record_codes:
                    record_codes.remove(code_hash)
                    record["hashed_backup_codes"] = record_codes
                    record["updated_at"] = datetime.now(timezone.utc).isoformat()
                    self._persist_enrollments()
                    return True
            return False
        except (OSError, ValueError, TypeError) as exc:
            logger.warning("Failed consuming backup code for user %s: %s", user_id, exc)
        return False



class MFAMiddleware:
    """Middleware for enforcing MFA requirements."""

    def __init__(self, mfa_manager: MFAManager):
        """
        Initialize MFA middleware.

        Args:
            mfa_manager: MFA manager instance
        """
        self.mfa_manager = mfa_manager

    def require_mfa(self, user_id: str, user_roles: List[str], mfa_verified: bool) -> bool:
        """
        Check if MFA is required and verified.

        Args:
            user_id: User identifier
            user_roles: User roles
            mfa_verified: Whether MFA has been verified in current session

        Returns:
            True if MFA requirements are met, False otherwise
        """
        # Check if MFA is required for user's roles
        if not self.mfa_manager.is_mfa_required(user_roles):
            return True

        # MFA is required - check if verified
        if not mfa_verified:
            logger.warning("MFA required but not verified for user: %s", user_id)
            return False

        return True
