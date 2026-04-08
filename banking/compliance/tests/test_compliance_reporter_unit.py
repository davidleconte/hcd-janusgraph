"""
Unit tests for ComplianceReporter.

Tests the compliance reporting with mocked dependencies.
All tests are deterministic with fixed timestamps and mocked file I/O.

Created: 2026-04-07
Phase 3: Compliance Module Testing
"""

import json
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open

import pytest

from banking.compliance.compliance_reporter import (
    ComplianceReporter,
    ComplianceMetrics,
    ComplianceViolation
)

# Fixed timestamp for deterministic tests
FIXED_TIMESTAMP = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def temp_log_dir():
    """Create temporary log directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_audit_events():
    """Create sample audit events."""
    return [
        {
            "timestamp": FIXED_TIMESTAMP.isoformat(),
            "event_type": "data_access",
            "severity": "info",
            "user": "user1@example.com",
            "resource": "customer:12345",
            "action": "query",
            "result": "success"
        },
        {
            "timestamp": (FIXED_TIMESTAMP + timedelta(hours=1)).isoformat(),
            "event_type": "auth_failed",
            "severity": "warning",
            "user": "user2@example.com",
            "resource": "authentication_system",
            "action": "login",
            "result": "failure"
        },
        {
            "timestamp": (FIXED_TIMESTAMP + timedelta(hours=2)).isoformat(),
            "event_type": "authz_denied",
            "severity": "warning",
            "user": "user3@example.com",
            "resource": "admin:settings",
            "action": "write",
            "result": "denied"
        }
    ]


@pytest.fixture
def sample_compliance_metrics():
    """Create sample compliance metrics."""
    return ComplianceMetrics(
        period_start=FIXED_TIMESTAMP.isoformat(),
        period_end=(FIXED_TIMESTAMP + timedelta(days=30)).isoformat(),
        total_events=100,
        events_by_type={"data_access": 50, "auth_login": 30, "auth_failed": 20},
        events_by_severity={"info": 70, "warning": 25, "error": 5},
        unique_users=10,
        unique_resources=25,
        failed_auth_attempts=20,
        denied_access_attempts=5,
        gdpr_requests=3,
        aml_alerts=2,
        fraud_alerts=1,
        security_incidents=0,
        admin_actions=5
    )


class TestComplianceMetrics:
    """Test ComplianceMetrics dataclass."""

    def test_metrics_creation(self):
        """Test creating compliance metrics."""
        metrics = ComplianceMetrics(
            period_start=FIXED_TIMESTAMP.isoformat(),
            period_end=(FIXED_TIMESTAMP + timedelta(days=30)).isoformat(),
            total_events=100,
            events_by_type={"data_access": 50},
            events_by_severity={"info": 70},
            unique_users=10,
            unique_resources=25,
            failed_auth_attempts=5,
            denied_access_attempts=2,
            gdpr_requests=1,
            aml_alerts=0,
            fraud_alerts=0,
            security_incidents=0,
            admin_actions=3
        )
        
        assert metrics.total_events == 100
        assert metrics.unique_users == 10
        assert metrics.failed_auth_attempts == 5

    def test_metrics_to_dict(self, sample_compliance_metrics):
        """Test converting metrics to dictionary."""
        metrics_dict = sample_compliance_metrics.to_dict()
        
        assert metrics_dict["total_events"] == 100
        assert metrics_dict["unique_users"] == 10
        assert metrics_dict["events_by_type"]["data_access"] == 50


class TestComplianceViolation:
    """Test ComplianceViolation dataclass."""

    def test_violation_creation(self):
        """Test creating a compliance violation."""
        violation = ComplianceViolation(
            timestamp=FIXED_TIMESTAMP.isoformat(),
            violation_type="excessive_failed_auth",
            severity="high",
            description="Multiple failed login attempts",
            user="user@example.com",
            resource="authentication_system",
            recommendation="Investigate potential brute force attack"
        )
        
        assert violation.violation_type == "excessive_failed_auth"
        assert violation.severity == "high"
        assert violation.user == "user@example.com"


class TestComplianceReporterInitialization:
    """Test ComplianceReporter initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        reporter = ComplianceReporter()
        
        assert reporter.log_dir == Path("/var/log/janusgraph")

    def test_init_with_custom_log_dir(self, temp_log_dir):
        """Test initialization with custom log directory."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        assert reporter.log_dir == Path(temp_log_dir)


class TestComplianceReporterLogParsing:
    """Test audit log parsing."""

    def test_parse_audit_log_empty_file(self, temp_log_dir):
        """Test parsing empty audit log."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        # Create empty log file
        log_path = Path(temp_log_dir) / "audit.log"
        log_path.touch()
        
        events = reporter.parse_audit_log("audit.log")
        
        assert len(events) == 0

    def test_parse_audit_log_nonexistent_file(self, temp_log_dir):
        """Test parsing nonexistent audit log."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        events = reporter.parse_audit_log("nonexistent.log")
        
        assert len(events) == 0

    def test_parse_audit_log_with_events(self, temp_log_dir, sample_audit_events):
        """Test parsing audit log with events."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        # Write events to log file
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path, "w") as f:
            for event in sample_audit_events:
                f.write(json.dumps(event) + "\n")
        
        events = reporter.parse_audit_log("audit.log")
        
        assert len(events) == 3
        assert events[0]["event_type"] == "data_access"

    def test_parse_audit_log_with_date_filter(self, temp_log_dir, sample_audit_events):
        """Test parsing audit log with date range filter."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        # Write events to log file
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path, "w") as f:
            for event in sample_audit_events:
                f.write(json.dumps(event) + "\n")
        
        # Filter to only first event
        start_date = FIXED_TIMESTAMP
        end_date = FIXED_TIMESTAMP + timedelta(minutes=30)
        
        events = reporter.parse_audit_log("audit.log", start_date, end_date)
        
        assert len(events) == 1
        assert events[0]["event_type"] == "data_access"

    def test_parse_audit_log_skips_invalid_json(self, temp_log_dir):
        """Test that invalid JSON lines are skipped."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        # Write mix of valid and invalid JSON
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path, "w") as f:
            f.write('{"event_type": "data_access", "timestamp": "2026-01-01T00:00:00+00:00"}\n')
            f.write('invalid json line\n')
            f.write('{"event_type": "auth_login", "timestamp": "2026-01-01T01:00:00+00:00"}\n')
        
        events = reporter.parse_audit_log("audit.log")
        
        assert len(events) == 2  # Only valid JSON lines


class TestComplianceReporterMetricsCalculation:
    """Test metrics calculation."""

    def test_calculate_metrics_empty_events(self, temp_log_dir):
        """Test calculating metrics with no events."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        metrics = reporter.calculate_metrics(
            [],
            FIXED_TIMESTAMP,
            FIXED_TIMESTAMP + timedelta(days=30)
        )
        
        assert metrics.total_events == 0
        assert metrics.unique_users == 0
        assert metrics.failed_auth_attempts == 0

    def test_calculate_metrics_with_events(self, temp_log_dir, sample_audit_events):
        """Test calculating metrics with events."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        metrics = reporter.calculate_metrics(
            sample_audit_events,
            FIXED_TIMESTAMP,
            FIXED_TIMESTAMP + timedelta(days=1)
        )
        
        assert metrics.total_events == 3
        assert metrics.unique_users == 3
        assert metrics.failed_auth_attempts == 1
        assert metrics.denied_access_attempts == 1

    def test_calculate_metrics_counts_event_types(self, temp_log_dir, sample_audit_events):
        """Test that metrics correctly count event types."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        metrics = reporter.calculate_metrics(
            sample_audit_events,
            FIXED_TIMESTAMP,
            FIXED_TIMESTAMP + timedelta(days=1)
        )
        
        assert metrics.events_by_type["data_access"] == 1
        assert metrics.events_by_type["auth_failed"] == 1
        assert metrics.events_by_type["authz_denied"] == 1

    def test_calculate_metrics_counts_severity(self, temp_log_dir, sample_audit_events):
        """Test that metrics correctly count severity levels."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        metrics = reporter.calculate_metrics(
            sample_audit_events,
            FIXED_TIMESTAMP,
            FIXED_TIMESTAMP + timedelta(days=1)
        )
        
        assert metrics.events_by_severity["info"] == 1
        assert metrics.events_by_severity["warning"] == 2


class TestComplianceReporterViolationDetection:
    """Test violation detection."""

    def test_detect_violations_empty_events(self, temp_log_dir):
        """Test detecting violations with no events."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        violations = reporter.detect_violations([])
        
        assert len(violations) == 0

    def test_detect_violations_excessive_failed_auth(self, temp_log_dir):
        """Test detecting excessive failed authentication attempts."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        # Create 5 failed auth events for same user
        events = []
        for i in range(5):
            events.append({
                "timestamp": (FIXED_TIMESTAMP + timedelta(minutes=i)).isoformat(),
                "event_type": "auth_failed",
                "severity": "warning",
                "user": "attacker@example.com",
                "resource": "authentication_system",
                "action": "login",
                "result": "failure"
            })
        
        violations = reporter.detect_violations(events)
        
        assert len(violations) == 1
        assert violations[0].violation_type == "excessive_failed_auth"
        assert violations[0].severity == "high"
        assert violations[0].user == "attacker@example.com"

    def test_detect_violations_unauthorized_access(self, temp_log_dir):
        """Test detecting unauthorized access attempts."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        events = [{
            "timestamp": FIXED_TIMESTAMP.isoformat(),
            "event_type": "authz_denied",
            "severity": "warning",
            "user": "user@example.com",
            "resource": "admin:settings",
            "action": "write",
            "result": "denied"
        }]
        
        violations = reporter.detect_violations(events)
        
        assert len(violations) == 1
        assert violations[0].violation_type == "unauthorized_access_attempt"
        assert violations[0].severity == "medium"

    def test_detect_violations_security_breach(self, temp_log_dir):
        """Test detecting security breach attempts."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        events = [{
            "timestamp": FIXED_TIMESTAMP.isoformat(),
            "event_type": "security_breach_attempt",
            "severity": "critical",
            "user": "attacker@example.com",
            "resource": "database",
            "action": "sql_injection",
            "result": "blocked"
        }]
        
        violations = reporter.detect_violations(events)
        
        assert len(violations) == 1
        assert violations[0].violation_type == "security_breach_attempt"
        assert violations[0].severity == "critical"

    def test_detect_violations_unencrypted_data_access(self, temp_log_dir):
        """Test detecting unencrypted data access."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        events = [{
            "timestamp": FIXED_TIMESTAMP.isoformat(),
            "event_type": "data_access",
            "severity": "info",
            "user": "user@example.com",
            "resource": "customer:12345",
            "action": "query",
            "result": "success",
            "metadata": {"encrypted": False}
        }]
        
        violations = reporter.detect_violations(events)
        
        assert len(violations) == 1
        assert violations[0].violation_type == "unencrypted_data_access"
        assert violations[0].severity == "high"


class TestComplianceReporterGDPRReport:
    """Test GDPR report generation."""

    def test_generate_gdpr_report_empty(self, temp_log_dir):
        """Test generating GDPR report with no events."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        # Create empty log file
        log_path = Path(temp_log_dir) / "audit.log"
        log_path.touch()
        
        report = reporter.generate_gdpr_report(
            FIXED_TIMESTAMP,
            FIXED_TIMESTAMP + timedelta(days=30)
        )
        
        assert report is not None
        # Report structure depends on implementation


class TestComplianceReporterEdgeCases:
    """Test edge cases."""

    def test_parse_log_with_missing_timestamp(self, temp_log_dir):
        """Test parsing log with missing timestamp field."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        # Write event without timestamp
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path, "w") as f:
            f.write('{"event_type": "data_access", "user": "test"}\n')
        
        # Should skip event with missing timestamp
        events = reporter.parse_audit_log(
            "audit.log",
            FIXED_TIMESTAMP,
            FIXED_TIMESTAMP + timedelta(days=1)
        )
        
        assert len(events) == 0

    def test_calculate_metrics_with_duplicate_users(self, temp_log_dir):
        """Test metrics calculation with duplicate users."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        events = [
            {
                "timestamp": FIXED_TIMESTAMP.isoformat(),
                "event_type": "data_access",
                "severity": "info",
                "user": "user1@example.com",
                "resource": "resource1",
                "action": "query",
                "result": "success"
            },
            {
                "timestamp": (FIXED_TIMESTAMP + timedelta(hours=1)).isoformat(),
                "event_type": "data_access",
                "severity": "info",
                "user": "user1@example.com",  # Same user
                "resource": "resource2",
                "action": "query",
                "result": "success"
            }
        ]
        
        metrics = reporter.calculate_metrics(
            events,
            FIXED_TIMESTAMP,
            FIXED_TIMESTAMP + timedelta(days=1)
        )
        
        assert metrics.total_events == 2
        assert metrics.unique_users == 1  # Only one unique user

    def test_detect_violations_below_threshold(self, temp_log_dir):
        """Test that violations below threshold are not detected."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        # Create only 4 failed auth events (below threshold of 5)
        events = []
        for i in range(4):
            events.append({
                "timestamp": (FIXED_TIMESTAMP + timedelta(minutes=i)).isoformat(),
                "event_type": "auth_failed",
                "severity": "warning",
                "user": "user@example.com",
                "resource": "authentication_system",
                "action": "login",
                "result": "failure"
            })
        
        violations = reporter.detect_violations(events)
        
        # Should not detect excessive_failed_auth violation
        excessive_auth_violations = [
            v for v in violations if v.violation_type == "excessive_failed_auth"
        ]
        assert len(excessive_auth_violations) == 0


class TestComplianceReporterComplexScenarios:
    """Test complex reporting scenarios."""

    def test_multiple_violation_types(self, temp_log_dir):
        """Test detecting multiple violation types in same report."""
        reporter = ComplianceReporter(log_dir=temp_log_dir)
        
        events = []
        
        # Add excessive failed auth
        for i in range(5):
            events.append({
                "timestamp": (FIXED_TIMESTAMP + timedelta(minutes=i)).isoformat(),
                "event_type": "auth_failed",
                "severity": "warning",
                "user": "attacker@example.com",
                "resource": "authentication_system",
                "action": "login",
                "result": "failure"
            })
        
        # Add unauthorized access
        events.append({
            "timestamp": (FIXED_TIMESTAMP + timedelta(hours=1)).isoformat(),
            "event_type": "authz_denied",
            "severity": "warning",
            "user": "user@example.com",
            "resource": "admin:settings",
            "action": "write",
            "result": "denied"
        })
        
        # Add security breach
        events.append({
            "timestamp": (FIXED_TIMESTAMP + timedelta(hours=2)).isoformat(),
            "event_type": "security_breach_attempt",
            "severity": "critical",
            "user": "hacker@example.com",
            "resource": "database",
            "action": "sql_injection",
            "result": "blocked"
        })
        
        violations = reporter.detect_violations(events)
        
        assert len(violations) >= 3
        violation_types = {v.violation_type for v in violations}
        assert "excessive_failed_auth" in violation_types
        assert "unauthorized_access_attempt" in violation_types
        assert "security_breach_attempt" in violation_types

# Made with Bob
