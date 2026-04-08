"""
Additional tests to achieve 100% coverage for ComplianceReporter.

These tests cover the remaining uncovered branch partials:
- Line 270->267: Unencrypted data access detection (metadata.get("encrypted", True) == False)
- Line 527->exit: HTML format export

Created: 2026-04-08
Phase 3: Compliance Module 100% Coverage
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from banking.compliance.compliance_reporter import ComplianceReporter


# Fixed timestamp for deterministic tests
FIXED_TIMESTAMP = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def temp_log_dir():
    """Create temporary log directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_audit_logger(temp_log_dir):
    """Create mock audit logger with test data."""
    mock_logger = MagicMock()
    
    # Create test audit log file
    log_path = Path(temp_log_dir) / "audit.log"
    with open(log_path, "w") as f:
        # Write test events
        events = [
            {
                "timestamp": "2026-01-01T00:00:00Z",
                "event_type": "data_access",
                "user": "user1",
                "resource": "customer:123",
                "action": "query",
                "result": "success",
                "metadata": {"encrypted": False}  # Unencrypted access
            },
            {
                "timestamp": "2026-01-01T01:00:00Z",
                "event_type": "data_access",
                "user": "user2",
                "resource": "account:456",
                "action": "query",
                "result": "success",
                "metadata": {"encrypted": True}  # Encrypted access
            },
            {
                "timestamp": "2026-01-01T02:00:00Z",
                "event_type": "auth_login",
                "user": "user3",
                "action": "login",
                "result": "success"
            }
        ]
        for event in events:
            f.write(json.dumps(event) + "\n")
    
    mock_logger.log_dir = temp_log_dir
    return mock_logger


class TestUnencryptedDataAccessDetection:
    """Test unencrypted data access detection (line 270->267)."""
    
    def test_soc2_report_detects_unencrypted_access(self, mock_audit_logger):
        """Test that SOC 2 report detects unencrypted data access."""
        reporter = ComplianceReporter(mock_audit_logger)
        
        # Generate SOC 2 report
        report = reporter.generate_soc2_report(
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 2, tzinfo=timezone.utc)
        )
        
        # Verify unencrypted access was detected
        assert "violations" in report
        violations = report["violations"]
        
        # Should have at least one unencrypted_data_access violation
        unencrypted_violations = [
            v for v in violations 
            if v["violation_type"] == "unencrypted_data_access"
        ]
        assert len(unencrypted_violations) > 0
        
        # Verify violation details
        violation = unencrypted_violations[0]
        assert violation["severity"] == "high"
        assert "user1" in violation["description"]
    
    def test_soc2_report_with_encrypted_metadata_true(self, temp_log_dir):
        """Test that encrypted access (metadata.encrypted=True) is not flagged."""
        # Create audit log with only encrypted access
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path, "w") as f:
            event = {
                "timestamp": "2026-01-01T00:00:00Z",
                "event_type": "data_access",
                "user": "user1",
                "resource": "customer:123",
                "action": "query",
                "result": "success",
                "metadata": {"encrypted": True}  # Explicitly encrypted
            }
            f.write(json.dumps(event) + "\n")
        
        mock_logger = MagicMock()
        mock_logger.log_dir = temp_log_dir
        
        reporter = ComplianceReporter(mock_logger)
        report = reporter.generate_soc2_report(
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 2, tzinfo=timezone.utc)
        )
        
        # Should have no unencrypted_data_access violations
        violations = report.get("violations", [])
        unencrypted_violations = [
            v for v in violations 
            if v["violation_type"] == "unencrypted_data_access"
        ]
        assert len(unencrypted_violations) == 0
    
    def test_soc2_report_with_missing_encrypted_field(self, temp_log_dir):
        """Test that missing 'encrypted' field defaults to True (no violation)."""
        # Create audit log without encrypted field in metadata
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path, "w") as f:
            event = {
                "timestamp": "2026-01-01T00:00:00Z",
                "event_type": "data_access",
                "user": "user1",
                "resource": "customer:123",
                "action": "query",
                "result": "success",
                "metadata": {"other_field": "value"}  # No 'encrypted' field
            }
            f.write(json.dumps(event) + "\n")
        
        mock_logger = MagicMock()
        mock_logger.log_dir = temp_log_dir
        
        reporter = ComplianceReporter(mock_logger)
        report = reporter.generate_soc2_report(
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 2, tzinfo=timezone.utc)
        )
        
        # Should have no violations (defaults to encrypted=True)
        violations = report.get("violations", [])
        unencrypted_violations = [
            v for v in violations 
            if v["violation_type"] == "unencrypted_data_access"
        ]
        assert len(unencrypted_violations) == 0


class TestHTMLExportFormat:
    """Test HTML export format (line 527->exit)."""
    
    def test_export_report_html_format(self, mock_audit_logger, temp_log_dir):
        """Test exporting report in HTML format."""
        reporter = ComplianceReporter(mock_audit_logger)
        
        # Generate a simple report
        report = {
            "report_type": "test",
            "period": "2026-01",
            "metrics": {
                "total_events": 100,
                "violations": 5
            }
        }
        
        # Export as HTML
        output_path = Path(temp_log_dir) / "report.html"
        reporter.export_report(report, str(output_path), format="html")
        
        # Verify HTML file was created
        assert output_path.exists()
        
        # Verify HTML content
        with open(output_path) as f:
            html_content = f.read()
        
        # Should contain HTML tags
        assert "<html>" in html_content
        assert "</html>" in html_content
        assert "<body>" in html_content
        assert "</body>" in html_content
        
        # Should contain report data
        assert "test" in html_content or "Test" in html_content
        assert "2026-01" in html_content
    
    def test_export_report_html_with_violations(self, mock_audit_logger, temp_log_dir):
        """Test HTML export includes violations."""
        reporter = ComplianceReporter(mock_audit_logger)
        
        # Generate report with violations
        report = {
            "report_type": "soc2",
            "period": "2026-01",
            "violations": [
                {
                    "timestamp": "2026-01-01T00:00:00Z",
                    "violation_type": "unencrypted_data_access",
                    "severity": "high",
                    "description": "Unencrypted access detected"
                }
            ],
            "metrics": {
                "total_violations": 1
            }
        }
        
        # Export as HTML
        output_path = Path(temp_log_dir) / "violations_report.html"
        reporter.export_report(report, str(output_path), format="html")
        
        # Verify HTML file was created
        assert output_path.exists()
        
        # Verify violations are in HTML
        with open(output_path) as f:
            html_content = f.read()
        
        assert "unencrypted_data_access" in html_content or "Unencrypted" in html_content
        assert "high" in html_content or "High" in html_content


# Summary of coverage improvements:
# 1. Line 270->267: Covered by test_soc2_report_detects_unencrypted_access
# 2. Line 527->exit: Covered by test_export_report_html_format
# 3. Additional edge cases for robustness
#
# Expected coverage after these tests: 100% for compliance_reporter.py

# Made with Bob
