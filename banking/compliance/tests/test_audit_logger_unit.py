"""
Unit tests for AuditLogger.

Tests the compliance audit logging with mocked dependencies.
All tests are deterministic with fixed timestamps and mocked file I/O.

Created: 2026-04-07
Phase 3: Compliance Module Testing
"""

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open

import pytest

from banking.compliance.audit_logger import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity
)

# Fixed timestamp for deterministic tests
FIXED_TIMESTAMP = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def temp_log_dir():
    """Create temporary log directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_audit_event():
    """Create a sample audit event."""
    return AuditEvent(
        timestamp=FIXED_TIMESTAMP.isoformat(),
        event_type=AuditEventType.DATA_ACCESS,
        severity=AuditSeverity.INFO,
        user="test_user",
        resource="customer:12345",
        action="query",
        result="success",
        ip_address="192.168.1.1",
        session_id="sess-123",
        metadata={"query": "SELECT * FROM customers"}
    )


class TestAuditEventType:
    """Test AuditEventType enum."""

    def test_data_access_events(self):
        """Test data access event types."""
        assert AuditEventType.DATA_ACCESS.value == "data_access"
        assert AuditEventType.DATA_QUERY.value == "data_query"
        assert AuditEventType.DATA_EXPORT.value == "data_export"

    def test_data_modification_events(self):
        """Test data modification event types."""
        assert AuditEventType.DATA_CREATE.value == "data_create"
        assert AuditEventType.DATA_UPDATE.value == "data_update"
        assert AuditEventType.DATA_DELETE.value == "data_delete"

    def test_authentication_events(self):
        """Test authentication event types."""
        assert AuditEventType.AUTH_LOGIN.value == "auth_login"
        assert AuditEventType.AUTH_LOGOUT.value == "auth_logout"
        assert AuditEventType.AUTH_FAILED.value == "auth_failed"
        assert AuditEventType.AUTH_MFA.value == "auth_mfa"

    def test_authorization_events(self):
        """Test authorization event types."""
        assert AuditEventType.AUTHZ_GRANTED.value == "authz_granted"
        assert AuditEventType.AUTHZ_DENIED.value == "authz_denied"
        assert AuditEventType.AUTHZ_ESCALATION.value == "authz_escalation"

    def test_compliance_events(self):
        """Test compliance event types."""
        assert AuditEventType.GDPR_DATA_REQUEST.value == "gdpr_data_request"
        assert AuditEventType.GDPR_DATA_DELETION.value == "gdpr_data_deletion"
        assert AuditEventType.AML_ALERT_GENERATED.value == "aml_alert_generated"
        assert AuditEventType.FRAUD_ALERT_GENERATED.value == "fraud_alert_generated"

    def test_security_events(self):
        """Test security event types."""
        assert AuditEventType.SECURITY_BREACH_ATTEMPT.value == "security_breach_attempt"
        assert AuditEventType.SECURITY_POLICY_VIOLATION.value == "security_policy_violation"
        assert AuditEventType.VALIDATION_FAILURE.value == "validation_failure"


class TestAuditSeverity:
    """Test AuditSeverity enum."""

    def test_severity_levels(self):
        """Test all severity levels."""
        assert AuditSeverity.INFO.value == "info"
        assert AuditSeverity.WARNING.value == "warning"
        assert AuditSeverity.ERROR.value == "error"
        assert AuditSeverity.CRITICAL.value == "critical"


class TestAuditEvent:
    """Test AuditEvent dataclass."""

    def test_audit_event_creation(self):
        """Test creating an audit event."""
        event = AuditEvent(
            timestamp=FIXED_TIMESTAMP.isoformat(),
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test_user",
            resource="customer:12345",
            action="query",
            result="success"
        )
        
        assert event.timestamp == FIXED_TIMESTAMP.isoformat()
        assert event.event_type == AuditEventType.DATA_ACCESS
        assert event.severity == AuditSeverity.INFO
        assert event.user == "test_user"
        assert event.resource == "customer:12345"
        assert event.action == "query"
        assert event.result == "success"

    def test_audit_event_with_optional_fields(self, sample_audit_event):
        """Test audit event with optional fields."""
        assert sample_audit_event.ip_address == "192.168.1.1"
        assert sample_audit_event.session_id == "sess-123"
        assert sample_audit_event.metadata == {"query": "SELECT * FROM customers"}

    def test_audit_event_to_dict(self, sample_audit_event):
        """Test converting audit event to dictionary."""
        event_dict = sample_audit_event.to_dict()
        
        assert event_dict["timestamp"] == FIXED_TIMESTAMP.isoformat()
        assert event_dict["event_type"] == "data_access"
        assert event_dict["severity"] == "info"
        assert event_dict["user"] == "test_user"
        assert event_dict["resource"] == "customer:12345"

    def test_audit_event_to_json(self, sample_audit_event):
        """Test converting audit event to JSON."""
        json_str = sample_audit_event.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["event_type"] == "data_access"
        assert parsed["severity"] == "info"
        assert parsed["user"] == "test_user"


class TestAuditLoggerInitialization:
    """Test AuditLogger initialization."""

    def test_init_with_defaults(self, temp_log_dir):
        """Test initialization with default values."""
        logger = AuditLogger(log_dir=temp_log_dir)
        
        assert logger.log_dir == Path(temp_log_dir)
        assert logger.log_file == "audit.log"
        assert logger.min_severity == AuditSeverity.INFO

    def test_init_with_custom_values(self, temp_log_dir):
        """Test initialization with custom values."""
        logger = AuditLogger(
            log_dir=temp_log_dir,
            log_file="custom_audit.log",
            min_severity=AuditSeverity.WARNING
        )
        
        assert logger.log_file == "custom_audit.log"
        assert logger.min_severity == AuditSeverity.WARNING

    def test_init_creates_log_directory(self, temp_log_dir):
        """Test that initialization creates log directory."""
        log_dir = Path(temp_log_dir) / "subdir"
        logger = AuditLogger(log_dir=str(log_dir))
        
        assert log_dir.exists()

    def test_init_configures_logger(self, temp_log_dir):
        """Test that initialization configures logger."""
        logger = AuditLogger(log_dir=temp_log_dir)
        
        assert logger.logger is not None
        assert logger.logger.name == "audit"
        assert logger.logger.propagate is False


class TestAuditLoggerEventLogging:
    """Test event logging functionality."""

    @patch('banking.compliance.audit_logger.datetime')
    def test_log_event_writes_json(self, mock_datetime, temp_log_dir, sample_audit_event):
        """Test that log_event writes JSON to file."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        logger.log_event(sample_audit_event)
        
        # Read log file
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        # Parse JSON
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "data_access"
        assert parsed["user"] == "test_user"

    def test_log_event_respects_severity_threshold(self, temp_log_dir):
        """Test that log_event respects minimum severity."""
        logger = AuditLogger(log_dir=temp_log_dir, min_severity=AuditSeverity.WARNING)
        
        # INFO event should not be logged
        info_event = AuditEvent(
            timestamp=FIXED_TIMESTAMP.isoformat(),
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test_user",
            resource="test",
            action="query",
            result="success"
        )
        logger.log_event(info_event)
        
        # WARNING event should be logged
        warning_event = AuditEvent(
            timestamp=FIXED_TIMESTAMP.isoformat(),
            event_type=AuditEventType.AUTH_FAILED,
            severity=AuditSeverity.WARNING,
            user="test_user",
            resource="test",
            action="login",
            result="failure"
        )
        logger.log_event(warning_event)
        
        # Check log file
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            lines = f.readlines()
        
        assert len(lines) == 1  # Only WARNING event logged
        parsed = json.loads(lines[0])
        assert parsed["severity"] == "warning"


class TestAuditLoggerDataAccess:
    """Test data access logging."""

    @patch('banking.compliance.audit_logger.datetime')
    def test_log_data_access(self, mock_datetime, temp_log_dir):
        """Test logging data access event."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        logger.log_data_access(
            user="analyst@example.com",
            resource="customer:12345",
            action="query",
            result="success",
            ip_address="192.168.1.1",
            session_id="sess-123",
            metadata={"query": "SELECT * FROM customers"}
        )
        
        # Read and verify log
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "data_access"
        assert parsed["user"] == "analyst@example.com"
        assert parsed["resource"] == "customer:12345"
        assert parsed["action"] == "query"
        assert parsed["result"] == "success"


class TestAuditLoggerDataModification:
    """Test data modification logging."""

    @patch('banking.compliance.audit_logger.datetime')
    def test_log_data_modification(self, mock_datetime, temp_log_dir):
        """Test logging data modification event."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        logger.log_data_modification(
            user="admin@example.com",
            resource="customer:12345",
            action="update",
            old_value="John Doe",
            new_value="Jane Doe",
            ip_address="192.168.1.1",
            session_id="sess-123"
        )
        
        # Read and verify log
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "data_update"
        assert parsed["user"] == "admin@example.com"
        assert parsed["metadata"]["old_value"] == "John Doe"
        assert parsed["metadata"]["new_value"] == "Jane Doe"


class TestAuditLoggerAuthentication:
    """Test authentication logging."""

    @patch('banking.compliance.audit_logger.datetime')
    def test_log_authentication_login_success(self, mock_datetime, temp_log_dir):
        """Test logging successful login."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        logger.log_authentication(
            user="user@example.com",
            action="login",
            result="success",
            ip_address="192.168.1.1"
        )
        
        # Read and verify log
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "auth_login"
        assert parsed["severity"] == "info"
        assert parsed["result"] == "success"

    @patch('banking.compliance.audit_logger.datetime')
    def test_log_authentication_login_failure(self, mock_datetime, temp_log_dir):
        """Test logging failed login."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        logger.log_authentication(
            user="user@example.com",
            action="login",
            result="failure",
            ip_address="192.168.1.1"
        )
        
        # Read and verify log
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "auth_failed"
        assert parsed["severity"] == "warning"
        assert parsed["result"] == "failure"

    @patch('banking.compliance.audit_logger.datetime')
    def test_log_authentication_logout(self, mock_datetime, temp_log_dir):
        """Test logging logout."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        logger.log_authentication(
            user="user@example.com",
            action="logout",
            result="success",
            ip_address="192.168.1.1"
        )
        
        # Read and verify log
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "auth_logout"
        assert parsed["severity"] == "info"


class TestAuditLoggerAuthorization:
    """Test authorization logging."""

    @patch('banking.compliance.audit_logger.datetime')
    def test_log_authorization_granted(self, mock_datetime, temp_log_dir):
        """Test logging granted authorization."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        logger.log_authorization(
            user="user@example.com",
            resource="customer:12345",
            action="read",
            result="granted",
            ip_address="192.168.1.1"
        )
        
        # Read and verify log
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "authz_granted"
        assert parsed["severity"] == "info"
        assert parsed["result"] == "granted"

    @patch('banking.compliance.audit_logger.datetime')
    def test_log_authorization_denied(self, mock_datetime, temp_log_dir):
        """Test logging denied authorization."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        logger.log_authorization(
            user="user@example.com",
            resource="admin:settings",
            action="write",
            result="denied",
            ip_address="192.168.1.1"
        )
        
        # Read and verify log
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "authz_denied"
        assert parsed["severity"] == "warning"
        assert parsed["result"] == "denied"


class TestAuditLoggerSeverityOrdering:
    """Test severity ordering logic."""

    def test_severity_order_info_lowest(self, temp_log_dir):
        """Test that INFO is lowest severity."""
        logger = AuditLogger(log_dir=temp_log_dir, min_severity=AuditSeverity.INFO)
        
        # All severities should be logged
        for severity in [AuditSeverity.INFO, AuditSeverity.WARNING, AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
            event = AuditEvent(
                timestamp=FIXED_TIMESTAMP.isoformat(),
                event_type=AuditEventType.DATA_ACCESS,
                severity=severity,
                user="test",
                resource="test",
                action="test",
                result="test"
            )
            logger.log_event(event)
        
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            lines = f.readlines()
        
        assert len(lines) == 4

    def test_severity_order_warning_filters_info(self, temp_log_dir):
        """Test that WARNING severity filters INFO."""
        logger = AuditLogger(log_dir=temp_log_dir, min_severity=AuditSeverity.WARNING)
        
        # INFO should not be logged
        info_event = AuditEvent(
            timestamp=FIXED_TIMESTAMP.isoformat(),
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test",
            resource="test",
            action="test",
            result="test"
        )
        logger.log_event(info_event)
        
        # WARNING should be logged
        warning_event = AuditEvent(
            timestamp=FIXED_TIMESTAMP.isoformat(),
            event_type=AuditEventType.AUTH_FAILED,
            severity=AuditSeverity.WARNING,
            user="test",
            resource="test",
            action="test",
            result="test"
        )
        logger.log_event(warning_event)
        
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            lines = f.readlines()
        
        assert len(lines) == 1


class TestAuditLoggerEdgeCases:
    """Test edge cases."""

    def test_empty_metadata(self, temp_log_dir):
        """Test event with empty metadata."""
        event = AuditEvent(
            timestamp=FIXED_TIMESTAMP.isoformat(),
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test",
            resource="test",
            action="test",
            result="test",
            metadata={}
        )
        
        logger = AuditLogger(log_dir=temp_log_dir)
        logger.log_event(event)
        
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["metadata"] == {}

    def test_none_optional_fields(self, temp_log_dir):
        """Test event with None optional fields."""
        event = AuditEvent(
            timestamp=FIXED_TIMESTAMP.isoformat(),
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test",
            resource="test",
            action="test",
            result="test",
            ip_address=None,
            session_id=None,
            metadata=None
        )
        
        logger = AuditLogger(log_dir=temp_log_dir)
        logger.log_event(event)
        
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["ip_address"] is None
        assert parsed["session_id"] is None
        assert parsed["metadata"] is None

# Made with Bob
