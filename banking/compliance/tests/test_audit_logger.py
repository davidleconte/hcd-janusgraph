"""
Tests for Audit Logger

Validates compliance logging functionality including:
- Event creation and serialization
- Severity-based filtering
- GDPR audit trail requirements
- AML/Fraud alert logging
- Security event logging
"""

import json
import tempfile
from pathlib import Path

import pytest

from banking.compliance.audit_logger import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
    AuditSeverity,
    get_audit_logger,
)


class TestAuditEvent:
    """Test AuditEvent data class"""

    def test_audit_event_creation(self):
        """Test creating an audit event"""
        event = AuditEvent(
            timestamp="2026-01-29T00:00:00.000000",
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test_user",
            resource="customer_data",
            action="read",
            result="success",
        )

        assert event.user == "test_user"
        assert event.resource == "customer_data"
        assert event.action == "read"
        assert event.result == "success"
        assert event.event_type == AuditEventType.DATA_ACCESS
        assert event.severity == AuditSeverity.INFO

    def test_audit_event_with_metadata(self):
        """Test audit event with metadata"""
        metadata = {"ip_address": "192.168.1.1", "session_id": "abc123"}

        event = AuditEvent(
            timestamp="2026-01-29T00:00:00.000000",
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test_user",
            resource="customer_data",
            action="read",
            result="success",
            ip_address="192.168.1.1",
            session_id="abc123",
            metadata=metadata,
        )

        assert event.ip_address == "192.168.1.1"
        assert event.session_id == "abc123"
        assert event.metadata == metadata

    def test_audit_event_to_dict(self):
        """Test converting audit event to dictionary"""
        event = AuditEvent(
            timestamp="2026-01-29T00:00:00.000000",
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test_user",
            resource="customer_data",
            action="read",
            result="success",
        )

        event_dict = event.to_dict()

        assert event_dict["user"] == "test_user"
        assert event_dict["resource"] == "customer_data"
        assert event_dict["event_type"] == "data_access"
        assert event_dict["severity"] == "info"

    def test_audit_event_to_json(self):
        """Test converting audit event to JSON"""
        event = AuditEvent(
            timestamp="2026-01-29T00:00:00.000000",
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test_user",
            resource="customer_data",
            action="read",
            result="success",
        )

        json_str = event.to_json()
        parsed = json.loads(json_str)

        assert parsed["user"] == "test_user"
        assert parsed["event_type"] == "data_access"


class TestAuditLogger:
    """Test AuditLogger functionality"""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def audit_logger(self, temp_log_dir):
        """Create audit logger with temporary directory"""
        return AuditLogger(log_dir=temp_log_dir, log_file="test_audit.log")

    def test_audit_logger_initialization(self, temp_log_dir):
        """Test audit logger initialization"""
        logger = AuditLogger(log_dir=temp_log_dir)

        assert logger.log_dir == Path(temp_log_dir)
        assert logger.log_file == "audit.log"
        assert logger.min_severity == AuditSeverity.INFO

    def test_log_directory_creation(self, temp_log_dir):
        """Test that log directory is created if it doesn't exist"""
        log_dir = Path(temp_log_dir) / "nested" / "logs"
        AuditLogger(log_dir=str(log_dir))

        assert log_dir.exists()

    def test_log_event(self, audit_logger, temp_log_dir):
        """Test logging an event"""
        event = AuditEvent(
            timestamp="2026-01-29T00:00:00.000000",
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test_user",
            resource="customer_data",
            action="read",
            result="success",
        )

        audit_logger.log_event(event)

        # Verify log file was created and contains event
        log_file = Path(temp_log_dir) / "test_audit.log"
        assert log_file.exists()

        with open(log_file, "r") as f:
            log_content = f.read()
            assert "test_user" in log_content
            assert "customer_data" in log_content

    def test_severity_filtering(self, temp_log_dir):
        """Test that events below minimum severity are not logged"""
        logger = AuditLogger(
            log_dir=temp_log_dir, log_file="filtered.log", min_severity=AuditSeverity.WARNING
        )

        # This should not be logged (INFO < WARNING)
        info_event = AuditEvent(
            timestamp="2026-01-29T00:00:00.000000",
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test_user",
            resource="data",
            action="read",
            result="success",
        )

        # This should be logged (WARNING >= WARNING)
        warning_event = AuditEvent(
            timestamp="2026-01-29T00:00:00.000000",
            event_type=AuditEventType.AUTH_FAILED,
            severity=AuditSeverity.WARNING,
            user="test_user",
            resource="auth",
            action="login",
            result="failure",
        )

        logger.log_event(info_event)
        logger.log_event(warning_event)

        log_file = Path(temp_log_dir) / "filtered.log"
        with open(log_file, "r") as f:
            log_content = f.read()
            assert "data_access" not in log_content
            assert "auth_failed" in log_content

    def test_log_data_access(self, audit_logger, temp_log_dir):
        """Test logging data access event"""
        audit_logger.log_data_access(
            user="analyst@example.com",
            resource="customer:12345",
            action="query",
            result="success",
            ip_address="192.168.1.100",
            session_id="sess_abc123",
            metadata={"query": "g.V().has('customerId', '12345')"},
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_content = f.read()
            log_data = json.loads(log_content)

            assert log_data["user"] == "analyst@example.com"
            assert log_data["resource"] == "customer:12345"
            assert log_data["event_type"] == "data_access"
            assert log_data["ip_address"] == "192.168.1.100"

    def test_log_data_modification(self, audit_logger, temp_log_dir):
        """Test logging data modification event"""
        audit_logger.log_data_modification(
            user="admin@example.com",
            resource="account:67890",
            action="update_balance",
            old_value=1000.00,
            new_value=1500.00,
            ip_address="192.168.1.101",
            session_id="sess_xyz789",
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_content = f.read()
            log_data = json.loads(log_content)

            assert log_data["user"] == "admin@example.com"
            assert log_data["event_type"] == "data_update"
            assert log_data["metadata"]["old_value"] == "1000.0"
            assert log_data["metadata"]["new_value"] == "1500.0"

    def test_log_authentication_success(self, audit_logger, temp_log_dir):
        """Test logging successful authentication"""
        audit_logger.log_authentication(
            user="user@example.com",
            action="login",
            result="success",
            ip_address="192.168.1.102",
            metadata={"method": "password"},
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            assert log_data["event_type"] == "auth_login"
            assert log_data["severity"] == "info"
            assert log_data["result"] == "success"

    def test_log_authentication_failure(self, audit_logger, temp_log_dir):
        """Test logging failed authentication"""
        audit_logger.log_authentication(
            user="attacker@example.com",
            action="login",
            result="failure",
            ip_address="192.168.1.200",
            metadata={"reason": "invalid_password", "attempts": 3},
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            assert log_data["event_type"] == "auth_failed"
            assert log_data["severity"] == "warning"
            assert log_data["result"] == "failure"

    def test_log_authorization_granted(self, audit_logger, temp_log_dir):
        """Test logging authorization granted"""
        audit_logger.log_authorization(
            user="user@example.com",
            resource="sensitive_data",
            action="read",
            result="granted",
            ip_address="192.168.1.103",
            metadata={"role": "analyst"},
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            assert log_data["event_type"] == "authz_granted"
            assert log_data["severity"] == "info"

    def test_log_authorization_denied(self, audit_logger, temp_log_dir):
        """Test logging authorization denied"""
        audit_logger.log_authorization(
            user="user@example.com",
            resource="admin_panel",
            action="access",
            result="denied",
            ip_address="192.168.1.104",
            metadata={"required_role": "admin", "user_role": "user"},
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            assert log_data["event_type"] == "authz_denied"
            assert log_data["severity"] == "warning"

    def test_log_gdpr_data_request(self, audit_logger, temp_log_dir):
        """Test logging GDPR data subject access request"""
        audit_logger.log_gdpr_request(
            user="dpo@example.com",
            request_type="access",
            subject_id="customer_12345",
            result="completed",
            metadata={
                "request_id": "gdpr_req_001",
                "data_exported": True,
                "format": "JSON",
            },
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            assert log_data["event_type"] == "gdpr_data_request"
            assert log_data["resource"] == "gdpr_subject:customer_12345"
            assert log_data["metadata"]["request_id"] == "gdpr_req_001"

    def test_log_gdpr_deletion_request(self, audit_logger, temp_log_dir):
        """Test logging GDPR right to be forgotten request"""
        audit_logger.log_gdpr_request(
            user="dpo@example.com",
            request_type="deletion",
            subject_id="customer_67890",
            result="completed",
            metadata={
                "request_id": "gdpr_del_001",
                "records_deleted": 42,
                "verification_required": True,
            },
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            assert log_data["event_type"] == "gdpr_data_deletion"
            assert log_data["metadata"]["records_deleted"] == 42

    def test_log_aml_alert_low_severity(self, audit_logger, temp_log_dir):
        """Test logging low severity AML alert"""
        audit_logger.log_aml_alert(
            user="aml_system",
            alert_type="unusual_pattern",
            entity_id="account_12345",
            severity="low",
            metadata={
                "pattern": "multiple_small_deposits",
                "transaction_count": 5,
                "total_amount": 4500.00,
            },
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            assert log_data["event_type"] == "aml_alert_generated"
            assert log_data["severity"] == "info"
            assert log_data["resource"] == "aml_entity:account_12345"

    def test_log_aml_alert_critical_severity(self, audit_logger, temp_log_dir):
        """Test logging critical severity AML alert"""
        audit_logger.log_aml_alert(
            user="aml_system",
            alert_type="structuring",
            entity_id="account_67890",
            severity="critical",
            metadata={
                "pattern": "structuring_detected",
                "transaction_count": 15,
                "total_amount": 149000.00,
                "threshold": 10000.00,
                "sar_required": True,
            },
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            assert log_data["event_type"] == "aml_alert_generated"
            assert log_data["severity"] == "critical"
            assert log_data["metadata"]["sar_required"] is True

    def test_log_fraud_alert(self, audit_logger, temp_log_dir):
        """Test logging fraud alert"""
        audit_logger.log_fraud_alert(
            user="fraud_system",
            alert_type="card_not_present",
            entity_id="transaction_99999",
            severity="high",
            metadata={
                "transaction_amount": 5000.00,
                "merchant": "suspicious_merchant",
                "location": "foreign_country",
                "risk_score": 0.95,
            },
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            assert log_data["event_type"] == "fraud_alert_generated"
            assert log_data["severity"] == "error"
            assert log_data["metadata"]["risk_score"] == 0.95

    def test_log_security_breach_attempt(self, audit_logger, temp_log_dir):
        """Test logging security breach attempt"""
        audit_logger.log_security_event(
            user="unknown",
            event_type="breach_attempt",
            resource="database",
            action="sql_injection",
            result="blocked",
            ip_address="192.168.1.250",
            metadata={
                "attack_type": "sql_injection",
                "payload": "' OR '1'='1",
                "blocked_by": "waf",
            },
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            assert log_data["event_type"] == "security_breach_attempt"
            assert log_data["severity"] == "critical"
            assert log_data["result"] == "blocked"

    def test_log_admin_config_change(self, audit_logger, temp_log_dir):
        """Test logging administrative configuration change"""
        audit_logger.log_admin_action(
            user="admin@example.com",
            action="config_change",
            resource="janusgraph_config",
            result="success",
            metadata={
                "setting": "storage.batch-loading",
                "old_value": "false",
                "new_value": "true",
            },
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            assert log_data["event_type"] == "admin_config_change"
            assert log_data["severity"] == "warning"
            assert log_data["metadata"]["setting"] == "storage.batch-loading"

    def test_multiple_events_logged(self, audit_logger, temp_log_dir):
        """Test logging multiple events"""
        # Log multiple events
        audit_logger.log_data_access(
            user="user1", resource="data1", action="read", result="success"
        )
        audit_logger.log_data_access(
            user="user2", resource="data2", action="read", result="success"
        )
        audit_logger.log_authentication(user="user3", action="login", result="success")

        # Verify all events are logged
        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 3

            # Parse and verify each event
            events = [json.loads(line) for line in lines]
            assert events[0]["user"] == "user1"
            assert events[1]["user"] == "user2"
            assert events[2]["user"] == "user3"

    def test_get_audit_logger_singleton(self, temp_log_dir):
        """Test global audit logger singleton"""
        # Reset global logger for test
        import banking.compliance.audit_logger as audit_module

        audit_module._audit_logger = None

        # Create logger with temp directory
        logger1 = AuditLogger(log_dir=temp_log_dir)
        audit_module._audit_logger = logger1

        logger2 = get_audit_logger()
        assert logger1 is logger2


class TestAuditEventTypes:
    """Test audit event type coverage"""

    def test_all_event_types_defined(self):
        """Verify all required event types are defined"""
        required_types = [
            "DATA_ACCESS",
            "DATA_QUERY",
            "DATA_EXPORT",
            "DATA_CREATE",
            "DATA_UPDATE",
            "DATA_DELETE",
            "AUTH_LOGIN",
            "AUTH_LOGOUT",
            "AUTH_FAILED",
            "GDPR_DATA_REQUEST",
            "GDPR_DATA_DELETION",
            "AML_ALERT_GENERATED",
            "FRAUD_ALERT_GENERATED",
            "SECURITY_BREACH_ATTEMPT",
            "ADMIN_CONFIG_CHANGE",
        ]

        for event_type in required_types:
            assert hasattr(AuditEventType, event_type)

    def test_all_severity_levels_defined(self):
        """Verify all severity levels are defined"""
        required_severities = ["INFO", "WARNING", "ERROR", "CRITICAL"]

        for severity in required_severities:
            assert hasattr(AuditSeverity, severity)


class TestComplianceRequirements:
    """Test compliance-specific requirements"""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def audit_logger(self, temp_log_dir):
        """Create audit logger with temporary directory"""
        return AuditLogger(log_dir=temp_log_dir, log_file="test_audit.log")

    def test_gdpr_article_30_compliance(self, audit_logger, temp_log_dir):
        """Test GDPR Article 30 compliance (Records of Processing Activities)"""
        # Log various data processing activities
        audit_logger.log_data_access(
            user="processor@example.com",
            resource="personal_data",
            action="process",
            result="success",
            metadata={
                "purpose": "customer_analytics",
                "legal_basis": "legitimate_interest",
                "data_categories": ["name", "email", "transaction_history"],
            },
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            # Verify required GDPR fields are present
            assert "timestamp" in log_data
            assert "user" in log_data
            assert "resource" in log_data
            assert "action" in log_data
            assert log_data["metadata"]["purpose"] == "customer_analytics"
            assert log_data["metadata"]["legal_basis"] == "legitimate_interest"

    def test_soc2_access_control_logging(self, audit_logger, temp_log_dir):
        """Test SOC 2 access control logging requirements"""
        # Log access control events
        audit_logger.log_authorization(
            user="user@example.com",
            resource="sensitive_financial_data",
            action="read",
            result="granted",
            metadata={"role": "financial_analyst", "department": "finance"},
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            # Verify SOC 2 requirements
            assert log_data["user"] == "user@example.com"
            assert log_data["resource"] == "sensitive_financial_data"
            assert log_data["result"] == "granted"
            assert "timestamp" in log_data

    def test_bsa_aml_reporting_requirements(self, audit_logger, temp_log_dir):
        """Test Bank Secrecy Act / AML reporting requirements"""
        # Log suspicious activity
        audit_logger.log_aml_alert(
            user="aml_system",
            alert_type="suspicious_activity",
            entity_id="customer_12345",
            severity="high",
            metadata={
                "sar_filed": True,
                "sar_number": "SAR-2026-001",
                "filing_date": "2026-01-29",
                "narrative": "Multiple structured transactions below CTR threshold",
            },
        )

        log_file = Path(temp_log_dir) / "test_audit.log"
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())

            # Verify BSA/AML requirements
            assert log_data["metadata"]["sar_filed"] is True
            assert "sar_number" in log_data["metadata"]
            assert "filing_date" in log_data["metadata"]
