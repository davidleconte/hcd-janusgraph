"""
Multi-Factor Authentication (MFA) Module

Provides TOTP-based multi-factor authentication for enhanced security.
Supports QR code generation, backup codes, and MFA enforcement policies.
"""

import pyotp
import qrcode
import secrets
import hashlib
import logging
from io import BytesIO
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

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
            self.require_mfa_for_roles = ['admin', 'developer']


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
                name=user_email,
                issuer_name=self.config.issuer
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()
            
            logger.info(f"TOTP setup completed for user: {user_id}")
            
            return secret, img_bytes
            
        except Exception as e:
            logger.error(f"Failed to setup TOTP for user {user_id}: {e}")
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
                logger.warning(f"MFA verification blocked - user locked out: {user_id}")
                return False
            
            # Verify token
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(token, valid_window=1)
            
            if is_valid:
                logger.info(f"TOTP verification successful for user: {user_id}")
                self._reset_failed_attempts(user_id)
            else:
                logger.warning(f"TOTP verification failed for user: {user_id}")
                self._record_failed_attempt(user_id)
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying TOTP: {e}")
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
        
        logger.info(f"Generated {count} backup codes")
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
        code = ''.join(
            format(b, '02x') for b in random_bytes
        )[:self.config.backup_code_length]
        
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
                'count': 0,
                'first_attempt': datetime.now(timezone.utc)
            }
        
        self.failed_attempts[user_id]['count'] += 1
        self.failed_attempts[user_id]['last_attempt'] = datetime.now(timezone.utc)
        
        if self.failed_attempts[user_id]['count'] >= self.config.max_attempts:
            logger.warning(f"User {user_id} locked out after {self.config.max_attempts} failed MFA attempts")
    
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
        
        if attempts['count'] < self.config.max_attempts:
            return False
        
        # Check if lockout period has expired
        lockout_end = attempts['last_attempt'] + timedelta(
            seconds=self.config.lockout_duration
        )
        
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
        lockout_end = attempts['last_attempt'] + timedelta(
            seconds=self.config.lockout_duration
        )
        
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
        return any(
            role in self.config.require_mfa_for_roles
            for role in user_roles
        )


class MFAEnrollment:
    """Manages MFA enrollment for users."""
    
    def __init__(self, mfa_manager: MFAManager):
        """
        Initialize MFA enrollment manager.
        
        Args:
            mfa_manager: MFA manager instance
        """
        self.mfa_manager = mfa_manager
    
    def enroll_user(self, user_id: str, user_email: str, method: MFAMethod = MFAMethod.TOTP) -> dict:
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
            hashed_codes = [
                self.mfa_manager.hash_backup_code(code)
                for code in backup_codes
            ]
            
            enrollment_data = {
                'user_id': user_id,
                'method': method.value,
                'secret': secret,
                'qr_code': qr_code,
                'backup_codes': backup_codes,
                'hashed_backup_codes': hashed_codes,
                'enrolled_at': datetime.now(timezone.utc).isoformat(),
                'status': 'pending_verification'
            }
            
            logger.info(f"User {user_id} enrolled in MFA (TOTP)")
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
        is_valid = self.mfa_manager.verify_totp(secret, token, user_id)
        
        if is_valid:
            logger.info(f"MFA enrollment verified for user: {user_id}")
        else:
            logger.warning(f"MFA enrollment verification failed for user: {user_id}")
        
        return is_valid
    
    def unenroll_user(self, user_id: str, reason: str = None):
        """
        Unenroll user from MFA.
        
        Args:
            user_id: User identifier
            reason: Optional reason for unenrollment
        """
        logger.info(f"User {user_id} unenrolled from MFA. Reason: {reason}")
        # Implementation would remove MFA data from storage


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
            logger.warning(f"MFA required but not verified for user: {user_id}")
            return False
        
        return True


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize MFA manager
    config = MFAConfig(
        issuer="JanusGraph Demo",
        require_mfa_for_roles=['admin', 'developer']
    )
    mfa_manager = MFAManager(config)
    
    # Enroll user
    enrollment = MFAEnrollment(mfa_manager)
    user_data = enrollment.enroll_user(
        user_id="user123",
        user_email="user@example.com"
    )
    
    print(f"Secret: {user_data['secret']}")
    print(f"Backup codes: {user_data['backup_codes']}")
    
    # Verify token (in real usage, user would provide this from authenticator app)
    totp = pyotp.TOTP(user_data['secret'])
    current_token = totp.now()
    
    is_valid = mfa_manager.verify_totp(
        user_data['secret'],
        current_token,
        "user123"
    )
    
    print(f"Token verification: {is_valid}")
    
    # Verify backup code
    backup_code = user_data['backup_codes'][0]
    is_backup_valid = mfa_manager.verify_backup_code(
        backup_code,
        user_data['hashed_backup_codes']
    )
    
    print(f"Backup code verification: {is_backup_valid}")

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
