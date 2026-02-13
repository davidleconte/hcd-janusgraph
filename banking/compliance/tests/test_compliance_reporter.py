"""
Tests for ComplianceReporter

Covers: report generation, metric calculation, violation detection, export.
"""

import csv
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from banking.compliance.compliance_reporter import (
    ComplianceMetrics,
    ComplianceReporter,
    ComplianceViolation,
    generate_compliance_report,
)


@pytest.fixture
def sample_events():
    return [
        {
            "timestamp": "2026-01-15T10:00:00+00:00",
            "event_type": "auth_login",
            "severity": "info",
            "user": "alice",
            "resource": "system",
            "action": "login",
            "result": "success",
        },
        {
            "timestamp": "2026-01-15T10:05:00+00:00",
            "event_type": "auth_failed",
            "severity": "warning",
            "user": "bob",
            "resource": "system",
            "action": "login",
            "result": "failure",
        },
        {
            "timestamp": "2026-01-15T10:10:00+00:00",
            "event_type": "data_access",
            "severity": "info",
            "user": "alice",
            "resource": "customer:123",
            "action": "read",
            "result": "success",
        },
        {
            "timestamp": "2026-01-15T11:00:00+00:00",
            "event_type": "authz_denied",
            "severity": "warning",
            "user": "bob",
            "resource": "admin_panel",
            "action": "access",
            "result": "denied",
        },
        {
            "timestamp": "2026-01-15T12:00:00+00:00",
            "event_type": "gdpr_data_request",
            "severity": "info",
            "user": "alice",
            "resource": "customer:456",
            "action": "access",
            "result": "success",
        },
        {
            "timestamp": "2026-01-15T13:00:00+00:00",
            "event_type": "aml_alert_generated",
            "severity": "warning",
            "user": "system",
            "resource": "account:789",
            "action": "alert",
            "result": "generated",
        },
        {
            "timestamp": "2026-01-15T14:00:00+00:00",
            "event_type": "fraud_alert_generated",
            "severity": "error",
            "user": "system",
            "resource": "tx:101",
            "action": "alert",
            "result": "generated",
        },
        {
            "timestamp": "2026-01-15T15:00:00+00:00",
            "event_type": "security_breach_attempt",
            "severity": "critical",
            "user": "unknown",
            "resource": "firewall",
            "action": "intrusion_attempt",
            "result": "blocked",
        },
        {
            "timestamp": "2026-01-15T16:00:00+00:00",
            "event_type": "admin_config_change",
            "severity": "warning",
            "user": "admin",
            "resource": "config",
            "action": "config_change",
            "result": "success",
        },
    ]


@pytest.fixture
def audit_log_dir(sample_events):
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit.log"
        with open(log_path, "w") as f:
            for event in sample_events:
                f.write(json.dumps(event) + "\n")
        yield tmpdir


@pytest.fixture
def reporter(audit_log_dir):
    return ComplianceReporter(log_dir=audit_log_dir)


class TestComplianceMetrics:
    def test_to_dict(self):
        m = ComplianceMetrics(
            period_start="2026-01-01",
            period_end="2026-01-31",
            total_events=10,
            events_by_type={"auth_login": 5},
            events_by_severity={"info": 5},
            unique_users=3,
            unique_resources=4,
            failed_auth_attempts=1,
            denied_access_attempts=0,
            gdpr_requests=1,
            aml_alerts=1,
            fraud_alerts=1,
            security_incidents=0,
            admin_actions=1,
        )
        d = m.to_dict()
        assert d["total_events"] == 10
        assert d["events_by_type"] == {"auth_login": 5}


class TestParseAuditLog:
    def test_parse_all_events(self, reporter):
        events = reporter.parse_audit_log("audit.log")
        assert len(events) == 9

    def test_parse_with_date_filter(self, reporter):
        start = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 15, 16, 0, 0, tzinfo=timezone.utc)
        events = reporter.parse_audit_log("audit.log", start_date=start, end_date=end)
        assert len(events) >= 3

    def test_parse_nonexistent_file(self, reporter):
        events = reporter.parse_audit_log("nonexistent.log")
        assert events == []

    def test_parse_malformed_json(self, audit_log_dir):
        log_path = Path(audit_log_dir) / "bad.log"
        with open(log_path, "w") as f:
            f.write("not json\n")
            f.write('{"timestamp": "2026-01-15T10:00:00+00:00", "event_type": "auth_login", "severity": "info", "user": "a", "resource": "b", "action": "c", "result": "d"}\n')
        r = ComplianceReporter(log_dir=audit_log_dir)
        events = r.parse_audit_log("bad.log")
        assert len(events) == 1


class TestCalculateMetrics:
    def test_metrics_calculation(self, reporter, sample_events):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        metrics = reporter.calculate_metrics(sample_events, start, end)

        assert metrics.total_events == 9
        assert metrics.unique_users == 5
        assert metrics.failed_auth_attempts == 1
        assert metrics.denied_access_attempts == 1
        assert metrics.gdpr_requests == 1
        assert metrics.aml_alerts == 1
        assert metrics.fraud_alerts == 1
        assert metrics.security_incidents == 1
        assert metrics.admin_actions == 1


class TestDetectViolations:
    def test_detect_unauthorized_access(self, reporter, sample_events):
        violations = reporter.detect_violations(sample_events)
        types = [v.violation_type for v in violations]
        assert "unauthorized_access_attempt" in types

    def test_detect_security_breach(self, reporter, sample_events):
        violations = reporter.detect_violations(sample_events)
        types = [v.violation_type for v in violations]
        assert "security_breach_attempt" in types

    def test_detect_excessive_failed_auth(self, reporter):
        events = [
            {
                "timestamp": "2026-01-15T10:00:00+00:00",
                "event_type": "auth_failed",
                "severity": "warning",
                "user": "attacker",
                "resource": "system",
                "action": "login",
                "result": "failure",
            }
        ] * 6
        violations = reporter.detect_violations(events)
        types = [v.violation_type for v in violations]
        assert "excessive_failed_auth" in types

    def test_detect_unencrypted_data_access(self, reporter):
        events = [
            {
                "timestamp": "2026-01-15T10:00:00+00:00",
                "event_type": "data_access",
                "severity": "info",
                "user": "alice",
                "resource": "sensitive_data",
                "action": "read",
                "result": "success",
                "metadata": {"encrypted": False},
            }
        ]
        violations = reporter.detect_violations(events)
        types = [v.violation_type for v in violations]
        assert "unencrypted_data_access" in types

    def test_no_violations_on_clean_data(self, reporter):
        events = [
            {
                "timestamp": "2026-01-15T10:00:00+00:00",
                "event_type": "auth_login",
                "severity": "info",
                "user": "alice",
                "resource": "system",
                "action": "login",
                "result": "success",
            }
        ]
        violations = reporter.detect_violations(events)
        assert len(violations) == 0


class TestGDPRReport:
    def test_gdpr_report_structure(self, reporter):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        report = reporter.generate_gdpr_report(start, end)

        assert report["report_type"] == "GDPR Article 30 - Records of Processing Activities"
        assert "summary" in report
        assert report["summary"]["access_requests"] >= 0


class TestSOC2Report:
    def test_soc2_report_structure(self, reporter):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        report = reporter.generate_soc2_report(start, end)

        assert "SOC 2" in report["report_type"]
        assert "summary" in report
        assert "successful_logins" in report["summary"]


class TestAMLReport:
    def test_aml_report_structure(self, reporter):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        report = reporter.generate_aml_report(start, end)

        assert "BSA/AML" in report["report_type"]
        assert "summary" in report


class TestComprehensiveReport:
    def test_comprehensive_report_structure(self, reporter):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        report = reporter.generate_comprehensive_report(start, end)

        assert report["report_type"] == "Comprehensive Compliance Report"
        assert "metrics" in report
        assert "violations" in report
        assert "gdpr_summary" in report
        assert "soc2_summary" in report
        assert "aml_summary" in report


class TestExportReport:
    def test_export_json(self, reporter):
        report = {"report_type": "test", "data": [1, 2, 3]}
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "report.json")
            reporter.export_report(report, path, format="json")
            with open(path) as f:
                loaded = json.load(f)
            assert loaded["report_type"] == "test"

    def test_export_csv(self, reporter):
        report = {"metrics": {"total_events": 10, "users": 5}}
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "report.csv")
            reporter.export_report(report, path, format="csv")
            with open(path) as f:
                reader = csv.reader(f)
                rows = list(reader)
            assert rows[0] == ["Metric", "Value"]

    def test_export_html(self, reporter):
        report = {
            "report_type": "Test Report",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "generated_at": "2026-02-01",
            "metrics": {"total": 10},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "report.html")
            reporter.export_report(report, path, format="html")
            with open(path) as f:
                html = f.read()
            assert "Test Report" in html
            assert "<table>" in html


class TestConvenienceFunction:
    def test_generate_gdpr(self, audit_log_dir):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        report = generate_compliance_report("gdpr", start, end, log_dir=audit_log_dir)
        assert "GDPR" in report["report_type"]

    def test_generate_soc2(self, audit_log_dir):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        report = generate_compliance_report("soc2", start, end, log_dir=audit_log_dir)
        assert "SOC 2" in report["report_type"]

    def test_generate_aml(self, audit_log_dir):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        report = generate_compliance_report("aml", start, end, log_dir=audit_log_dir)
        assert "BSA/AML" in report["report_type"]

    def test_generate_comprehensive(self, audit_log_dir):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        report = generate_compliance_report("comprehensive", start, end, log_dir=audit_log_dir)
        assert report["report_type"] == "Comprehensive Compliance Report"

    def test_generate_with_output_file(self, audit_log_dir):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmpdir:
            output = str(Path(tmpdir) / "out.json")
            report = generate_compliance_report("gdpr", start, end, log_dir=audit_log_dir, output_file=output)
            assert Path(output).exists()


class TestComplianceViolation:
    def test_violation_fields(self):
        v = ComplianceViolation(
            timestamp="2026-01-15T10:00:00",
            violation_type="test",
            severity="high",
            description="Test violation",
            user="alice",
            resource="data",
            recommendation="Fix it",
        )
        assert v.violation_type == "test"
        assert v.severity == "high"
