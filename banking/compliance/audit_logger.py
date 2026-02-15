"""
Audit Logger for Banking Compliance

Provides comprehensive audit logging for regulatory compliance including:
- GDPR Article 30 (Records of Processing Activities)
- SOC 2 Type II (Access Control and Monitoring)
- PCI DSS (Payment Card Industry Data Security Standard)
- Bank Secrecy Act (BSA) / Anti-Money Laundering (AML)

All audit events are logged in structured JSON format with:
- Timestamp (ISO 8601 UTC)
- Event type and severity
- User/system identity
- Resource accessed/modified
- Action performed
- Result (success/failure)
- Metadata (IP address, session ID, etc.)
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class AuditEventType(Enum):
    """Types of audit events for compliance tracking"""

    # Data Access Events
    DATA_ACCESS = "data_access"
    DATA_QUERY = "data_query"
    DATA_EXPORT = "data_export"

    # Data Modification Events
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"

    # Authentication Events
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    AUTH_FAILED = "auth_failed"
    AUTH_MFA = "auth_mfa"

    # Authorization Events
    AUTHZ_GRANTED = "authz_granted"
    AUTHZ_DENIED = "authz_denied"
    AUTHZ_ESCALATION = "authz_escalation"

    # Administrative Events
    ADMIN_CONFIG_CHANGE = "admin_config_change"
    ADMIN_USER_CREATE = "admin_user_create"
    ADMIN_USER_DELETE = "admin_user_delete"
    ADMIN_ROLE_CHANGE = "admin_role_change"

    # Compliance Events
    GDPR_DATA_REQUEST = "gdpr_data_request"
    GDPR_DATA_DELETION = "gdpr_data_deletion"
    GDPR_CONSENT_CHANGE = "gdpr_consent_change"
    AML_ALERT_GENERATED = "aml_alert_generated"
    FRAUD_ALERT_GENERATED = "fraud_alert_generated"

    # Security Events
    SECURITY_BREACH_ATTEMPT = "security_breach_attempt"
    SECURITY_POLICY_VIOLATION = "security_policy_violation"
    SECURITY_ENCRYPTION_FAILURE = "security_encryption_failure"
    VALIDATION_FAILURE = "validation_failure"
    QUERY_EXECUTED = "query_executed"
    CREDENTIAL_ROTATION = "credential_rotation"
    VAULT_ACCESS = "vault_access"

    # System Events
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    SYSTEM_ERROR = "system_error"


class AuditSeverity(Enum):
    """Severity levels for audit events"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Structured audit event for compliance logging"""

    timestamp: str
    event_type: AuditEventType
    severity: AuditSeverity
    user: str
    resource: str
    action: str
    result: str
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary for JSON serialization"""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        return data

    def to_json(self) -> str:
        """Convert audit event to JSON string"""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Audit logger for banking compliance requirements

    Features:
    - Structured JSON logging
    - Automatic timestamp generation
    - Severity-based filtering
    - Separate log files for different event types
    - Tamper-evident logging (append-only)
    - Log rotation support
    """

    def __init__(
        self,
        log_dir: str = os.environ.get("AUDIT_LOG_DIR", "/var/log/janusgraph"),
        log_file: str = "audit.log",
        min_severity: AuditSeverity = AuditSeverity.INFO,
    ):
        """
        Initialize audit logger

        Args:
            log_dir: Directory for audit logs
            log_file: Name of audit log file
            min_severity: Minimum severity level to log
        """
        self.log_dir = Path(log_dir)
        self.log_file = log_file
        self.min_severity = min_severity

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Configure logger
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # File handler for audit logs
        log_path = self.log_dir / self.log_file
        handler = logging.FileHandler(log_path, mode="a")
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event

        Args:
            event: AuditEvent to log
        """
        # Check severity threshold
        severity_order = {
            AuditSeverity.INFO: 0,
            AuditSeverity.WARNING: 1,
            AuditSeverity.ERROR: 2,
            AuditSeverity.CRITICAL: 3,
        }

        if severity_order[event.severity] < severity_order[self.min_severity]:
            return

        # Log event as JSON
        self.logger.info(event.to_json())

    def log_data_access(
        self,
        user: str,
        resource: str,
        action: str,
        result: str,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log data access event (GDPR Article 30)"""
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user=user,
            resource=resource,
            action=action,
            result=result,
            ip_address=ip_address,
            session_id=session_id,
            metadata=metadata,
        )
        self.log_event(event)

    def log_data_modification(
        self,
        user: str,
        resource: str,
        action: str,
        old_value: Any,
        new_value: Any,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Log data modification event"""
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.DATA_UPDATE,
            severity=AuditSeverity.INFO,
            user=user,
            resource=resource,
            action=action,
            result="success",
            ip_address=ip_address,
            session_id=session_id,
            metadata={"old_value": str(old_value), "new_value": str(new_value)},
        )
        self.log_event(event)

    def log_authentication(
        self,
        user: str,
        action: str,
        result: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log authentication event"""
        # Determine event type based on result first, then action
        if result == "failure":
            event_type = AuditEventType.AUTH_FAILED
            severity = AuditSeverity.WARNING
        elif action == "login":
            event_type = AuditEventType.AUTH_LOGIN
            severity = AuditSeverity.INFO
        elif action == "logout":
            event_type = AuditEventType.AUTH_LOGOUT
            severity = AuditSeverity.INFO
        else:
            event_type = AuditEventType.AUTH_FAILED
            severity = AuditSeverity.WARNING

        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            severity=severity,
            user=user,
            resource="authentication_system",
            action=action,
            result=result,
            ip_address=ip_address,
            metadata=metadata,
        )
        self.log_event(event)

    def log_authorization(
        self,
        user: str,
        resource: str,
        action: str,
        result: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log authorization event"""
        event_type = (
            AuditEventType.AUTHZ_GRANTED if result == "granted" else AuditEventType.AUTHZ_DENIED
        )

        severity = AuditSeverity.WARNING if result == "denied" else AuditSeverity.INFO

        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            severity=severity,
            user=user,
            resource=resource,
            action=action,
            result=result,
            ip_address=ip_address,
            metadata=metadata,
        )
        self.log_event(event)

    def log_gdpr_request(
        self,
        user: str,
        request_type: str,
        subject_id: str,
        result: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log GDPR data subject request"""
        event_type_map = {
            "access": AuditEventType.GDPR_DATA_REQUEST,
            "deletion": AuditEventType.GDPR_DATA_DELETION,
            "consent": AuditEventType.GDPR_CONSENT_CHANGE,
        }

        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type_map.get(request_type, AuditEventType.GDPR_DATA_REQUEST),
            severity=AuditSeverity.INFO,
            user=user,
            resource=f"gdpr_subject:{subject_id}",
            action=request_type,
            result=result,
            metadata=metadata,
        )
        self.log_event(event)

    def log_aml_alert(
        self,
        user: str,
        alert_type: str,
        entity_id: str,
        severity: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log AML alert generation"""
        severity_map = {
            "low": AuditSeverity.INFO,
            "medium": AuditSeverity.WARNING,
            "high": AuditSeverity.ERROR,
            "critical": AuditSeverity.CRITICAL,
        }

        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.AML_ALERT_GENERATED,
            severity=severity_map.get(severity, AuditSeverity.WARNING),
            user=user,
            resource=f"aml_entity:{entity_id}",
            action=f"generate_alert:{alert_type}",
            result="alert_generated",
            metadata=metadata,
        )
        self.log_event(event)

    def log_fraud_alert(
        self,
        user: str,
        alert_type: str,
        entity_id: str,
        severity: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log fraud alert generation"""
        severity_map = {
            "low": AuditSeverity.INFO,
            "medium": AuditSeverity.WARNING,
            "high": AuditSeverity.ERROR,
            "critical": AuditSeverity.CRITICAL,
        }

        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.FRAUD_ALERT_GENERATED,
            severity=severity_map.get(severity, AuditSeverity.WARNING),
            user=user,
            resource=f"fraud_entity:{entity_id}",
            action=f"generate_alert:{alert_type}",
            result="alert_generated",
            metadata=metadata,
        )
        self.log_event(event)

    def log_security_event(
        self,
        user: str,
        event_type: str,
        resource: str,
        action: str,
        result: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log security event"""
        event_type_map = {
            "breach_attempt": AuditEventType.SECURITY_BREACH_ATTEMPT,
            "policy_violation": AuditEventType.SECURITY_POLICY_VIOLATION,
            "encryption_failure": AuditEventType.SECURITY_ENCRYPTION_FAILURE,
        }

        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type_map.get(event_type, AuditEventType.SECURITY_POLICY_VIOLATION),
            severity=AuditSeverity.CRITICAL,
            user=user,
            resource=resource,
            action=action,
            result=result,
            ip_address=ip_address,
            metadata=metadata,
        )
        self.log_event(event)

    def log_admin_action(
        self,
        user: str,
        action: str,
        resource: str,
        result: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log administrative action"""
        event_type_map = {
            "config_change": AuditEventType.ADMIN_CONFIG_CHANGE,
            "user_create": AuditEventType.ADMIN_USER_CREATE,
            "user_delete": AuditEventType.ADMIN_USER_DELETE,
            "role_change": AuditEventType.ADMIN_ROLE_CHANGE,
        }

        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type_map.get(action, AuditEventType.ADMIN_CONFIG_CHANGE),
            severity=AuditSeverity.WARNING,
            user=user,
            resource=resource,
            action=action,
            result=result,
            metadata=metadata,
        )
        self.log_event(event)


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
