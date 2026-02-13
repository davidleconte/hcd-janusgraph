"""Tests for banking.compliance.compliance_reporter module."""
import json
import os
import pytest
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from banking.compliance.compliance_reporter import (
    ComplianceMetrics,
    ComplianceReporter,
    ComplianceViolation,
)


@pytest.fixture
def sample_events():
    return [
        {"event_type": "auth_failed", "severity": "warning", "user": "alice", "resource": "api", "timestamp": "2026-01-15T10:00:00+00:00"},
        {"event_type": "auth_failed", "severity": "warning", "user": "alice", "resource": "api", "timestamp": "2026-01-15T10:01:00+00:00"},
        {"event_type": "auth_failed", "severity": "warning", "user": "alice", "resource": "api", "timestamp": "2026-01-15T10:02:00+00:00"},
        {"event_type": "auth_failed", "severity": "warning", "user": "alice", "resource": "api", "timestamp": "2026-01-15T10:03:00+00:00"},
        {"event_type": "auth_failed", "severity": "warning", "user": "alice", "resource": "api", "timestamp": "2026-01-15T10:04:00+00:00"},
        {"event_type": "authz_denied", "severity": "warning", "user": "bob", "resource": "admin_panel", "timestamp": "2026-01-15T11:00:00+00:00"},
        {"event_type": "data_access", "severity": "info", "user": "carol", "resource": "customer:123", "timestamp": "2026-01-15T12:00:00+00:00"},
        {"event_type": "gdpr_data_request", "severity": "info", "user": "dave", "resource": "customer:456", "timestamp": "2026-01-15T13:00:00+00:00"},
        {"event_type": "aml_alert_generated", "severity": "high", "user": "system", "resource": "account:789", "timestamp": "2026-01-15T14:00:00+00:00"},
        {"event_type": "fraud_alert_generated", "severity": "high", "user": "system", "resource": "tx:101", "timestamp": "2026-01-15T15:00:00+00:00"},
        {"event_type": "security_breach_attempt", "severity": "critical", "user": "unknown", "resource": "firewall", "timestamp": "2026-01-15T16:00:00+00:00"},
        {"event_type": "admin_config_change", "severity": "info", "user": "admin", "resource": "settings", "timestamp": "2026-01-15T17:00:00+00:00"},
    ]


@pytest.fixture
def log_dir(sample_events):
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "audit.log")
        with open(log_file, "w") as f:
            for event in sample_events:
                f.write(json.dumps(event) + "\n")
            f.write("invalid json line\n")
        yield tmpdir


class TestComplianceMetrics:
    def test_to_dict(self):
        m = ComplianceMetrics(
            period_start="2026-01-01", period_end="2026-01-31",
            total_events=100, events_by_type={"auth": 50}, events_by_severity={"high": 10},
            unique_users=5, unique_resources=20, failed_auth_attempts=3,
            denied_access_attempts=2, gdpr_requests=1, aml_alerts=1,
            fraud_alerts=1, security_incidents=0, admin_actions=2,
        )
        d = m.to_dict()
        assert d["total_events"] == 100
        assert d["events_by_type"] == {"auth": 50}


class TestComplianceReporter:
    def test_init(self):
        reporter = ComplianceReporter("/var/log/test")
        assert reporter.log_dir == Path("/var/log/test")

    def test_parse_audit_log(self, log_dir):
        reporter = ComplianceReporter(log_dir)
        events = reporter.parse_audit_log("audit.log")
        assert len(events) == 12

    def test_parse_audit_log_missing_file(self, log_dir):
        reporter = ComplianceReporter(log_dir)
        events = reporter.parse_audit_log("nonexistent.log")
        assert events == []

    def test_parse_audit_log_with_date_filter(self, log_dir):
        reporter = ComplianceReporter(log_dir)
        start = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc)
        events = reporter.parse_audit_log("audit.log", start_date=start, end_date=end)
        assert len(events) >= 2

    def test_calculate_metrics(self, log_dir, sample_events):
        reporter = ComplianceReporter(log_dir)
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        metrics = reporter.calculate_metrics(sample_events, start, end)
        assert isinstance(metrics, ComplianceMetrics)
        assert metrics.total_events == 12
        assert metrics.failed_auth_attempts == 5
        assert metrics.denied_access_attempts == 1
        assert metrics.gdpr_requests == 1
        assert metrics.aml_alerts == 1
        assert metrics.fraud_alerts == 1
        assert metrics.security_incidents == 1
        assert metrics.admin_actions == 1
        assert metrics.unique_users > 0
        assert metrics.unique_resources > 0

    def test_detect_violations(self, log_dir, sample_events):
        reporter = ComplianceReporter(log_dir)
        events_with_action = []
        for e in sample_events:
            ec = dict(e)
            ec.setdefault("action", ec.get("event_type", "unknown"))
            events_with_action.append(ec)
        violations = reporter.detect_violations(events_with_action)
        assert len(violations) >= 1
        auth_violations = [v for v in violations if v.violation_type == "excessive_failed_auth"]
        assert len(auth_violations) == 1
        assert auth_violations[0].user == "alice"


class TestComplianceViolation:
    def test_creation(self):
        v = ComplianceViolation(
            timestamp="2026-01-15T10:00:00",
            violation_type="test",
            severity="high",
            description="Test violation",
            user="alice",
            resource="api",
            recommendation="Fix it",
        )
        assert v.violation_type == "test"
        assert v.severity == "high"
