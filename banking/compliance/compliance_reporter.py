"""
Compliance Report Generator

Generates compliance reports for regulatory audits including:
- GDPR Article 30 Records of Processing Activities
- SOC 2 Type II Access Control Reports
- BSA/AML Suspicious Activity Reports
- PCI DSS Audit Reports
- Compliance Dashboard Metrics

Reports are generated from audit logs and provide:
- Summary statistics
- Detailed event listings
- Trend analysis
- Compliance violations
- Recommendations
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict



@dataclass
class ComplianceMetrics:
    """Compliance metrics for reporting period"""

    period_start: str
    period_end: str
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    unique_users: int
    unique_resources: int
    failed_auth_attempts: int
    denied_access_attempts: int
    gdpr_requests: int
    aml_alerts: int
    fraud_alerts: int
    security_incidents: int
    admin_actions: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return asdict(self)


@dataclass
class ComplianceViolation:
    """Compliance violation detected in audit logs"""

    timestamp: str
    violation_type: str
    severity: str
    description: str
    user: str
    resource: str
    recommendation: str


class ComplianceReporter:
    """
    Generate compliance reports from audit logs

    Features:
    - Parse structured JSON audit logs
    - Generate summary statistics
    - Identify compliance violations
    - Create regulatory reports
    - Export in multiple formats (JSON, CSV, HTML)
    """

    def __init__(self, log_dir: str = "/var/log/janusgraph"):
        """
        Initialize compliance reporter

        Args:
            log_dir: Directory containing audit logs
        """
        self.log_dir = Path(log_dir)

    def parse_audit_log(
        self, log_file: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Parse audit log file and filter by date range

        Args:
            log_file: Name of audit log file
            start_date: Start of reporting period (inclusive)
            end_date: End of reporting period (inclusive)

        Returns:
            List of audit events within date range
        """
        log_path = self.log_dir / log_file
        if not log_path.exists():
            return []

        events = []
        with open(log_path, "r") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())

                    # Filter by date range if specified
                    if start_date or end_date:
                        event_time = datetime.fromisoformat(event["timestamp"])
                        if start_date and event_time < start_date:
                            continue
                        if end_date and event_time > end_date:
                            continue

                    events.append(event)
                except (json.JSONDecodeError, KeyError):
                    continue

        return events

    def calculate_metrics(
        self, events: List[Dict[str, Any]], start_date: datetime, end_date: datetime
    ) -> ComplianceMetrics:
        """
        Calculate compliance metrics from audit events

        Args:
            events: List of audit events
            start_date: Start of reporting period
            end_date: End of reporting period

        Returns:
            ComplianceMetrics object
        """
        # Count events by type
        events_by_type = Counter(event["event_type"] for event in events)

        # Count events by severity
        events_by_severity = Counter(event["severity"] for event in events)

        # Count unique users and resources
        unique_users = len(set(event["user"] for event in events))
        unique_resources = len(set(event["resource"] for event in events))

        # Count specific event types
        failed_auth = sum(
            1 for event in events if event["event_type"] == "auth_failed"
        )
        denied_access = sum(
            1 for event in events if event["event_type"] == "authz_denied"
        )
        gdpr_requests = sum(
            1
            for event in events
            if event["event_type"]
            in ["gdpr_data_request", "gdpr_data_deletion", "gdpr_consent_change"]
        )
        aml_alerts = sum(
            1 for event in events if event["event_type"] == "aml_alert_generated"
        )
        fraud_alerts = sum(
            1 for event in events if event["event_type"] == "fraud_alert_generated"
        )
        security_incidents = sum(
            1
            for event in events
            if event["event_type"]
            in [
                "security_breach_attempt",
                "security_policy_violation",
                "security_encryption_failure",
            ]
        )
        admin_actions = sum(
            1
            for event in events
            if event["event_type"]
            in [
                "admin_config_change",
                "admin_user_create",
                "admin_user_delete",
                "admin_role_change",
            ]
        )

        return ComplianceMetrics(
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat(),
            total_events=len(events),
            events_by_type=dict(events_by_type),
            events_by_severity=dict(events_by_severity),
            unique_users=unique_users,
            unique_resources=unique_resources,
            failed_auth_attempts=failed_auth,
            denied_access_attempts=denied_access,
            gdpr_requests=gdpr_requests,
            aml_alerts=aml_alerts,
            fraud_alerts=fraud_alerts,
            security_incidents=security_incidents,
            admin_actions=admin_actions,
        )

    def detect_violations(self, events: List[Dict[str, Any]]) -> List[ComplianceViolation]:
        """
        Detect compliance violations in audit events

        Args:
            events: List of audit events

        Returns:
            List of detected violations
        """
        violations = []

        # Track failed authentication attempts per user
        failed_auth_by_user = defaultdict(list)
        for event in events:
            if event["event_type"] == "auth_failed":
                failed_auth_by_user[event["user"]].append(event)

        # Violation: Multiple failed authentication attempts
        for user, failed_events in failed_auth_by_user.items():
            if len(failed_events) >= 5:
                violations.append(
                    ComplianceViolation(
                        timestamp=failed_events[-1]["timestamp"],
                        violation_type="excessive_failed_auth",
                        severity="high",
                        description=f"User {user} had {len(failed_events)} failed authentication attempts",
                        user=user,
                        resource="authentication_system",
                        recommendation="Investigate potential brute force attack. Consider account lockout policy.",
                    )
                )

        # Track access to sensitive resources without proper authorization
        for event in events:
            if event["event_type"] == "authz_denied" and event["severity"] == "warning":
                violations.append(
                    ComplianceViolation(
                        timestamp=event["timestamp"],
                        violation_type="unauthorized_access_attempt",
                        severity="medium",
                        description=f"User {event['user']} attempted unauthorized access to {event['resource']}",
                        user=event["user"],
                        resource=event["resource"],
                        recommendation="Review user permissions and access control policies.",
                    )
                )

        # Track security incidents
        for event in events:
            if event["event_type"] in [
                "security_breach_attempt",
                "security_policy_violation",
            ]:
                violations.append(
                    ComplianceViolation(
                        timestamp=event["timestamp"],
                        violation_type=event["event_type"],
                        severity="critical",
                        description=f"Security incident: {event['action']} on {event['resource']}",
                        user=event["user"],
                        resource=event["resource"],
                        recommendation="Immediate investigation required. Review security logs and incident response procedures.",
                    )
                )

        # Track unencrypted data access (if metadata indicates)
        for event in events:
            if event["event_type"] == "data_access" and event.get("metadata"):
                metadata = event["metadata"]
                if isinstance(metadata, dict) and not metadata.get("encrypted", True):
                    violations.append(
                        ComplianceViolation(
                            timestamp=event["timestamp"],
                            violation_type="unencrypted_data_access",
                            severity="high",
                            description=f"Unencrypted data access by {event['user']}",
                            user=event["user"],
                            resource=event["resource"],
                            recommendation="Enable encryption for all data access. Review encryption policies.",
                        )
                    )

        return violations

    def generate_gdpr_report(
        self, start_date: datetime, end_date: datetime, log_file: str = "audit.log"
    ) -> Dict[str, Any]:
        """
        Generate GDPR Article 30 compliance report

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period
            log_file: Audit log file name

        Returns:
            GDPR compliance report
        """
        events = self.parse_audit_log(log_file, start_date, end_date)

        # Filter GDPR-related events
        gdpr_events = [
            event
            for event in events
            if event["event_type"]
            in [
                "gdpr_data_request",
                "gdpr_data_deletion",
                "gdpr_consent_change",
                "data_access",
                "data_update",
                "data_delete",
            ]
        ]

        # Group by data subject
        by_subject = defaultdict(list)
        for event in gdpr_events:
            resource = event["resource"]
            by_subject[resource].append(event)

        # Calculate statistics
        total_requests = sum(
            1
            for event in gdpr_events
            if event["event_type"]
            in ["gdpr_data_request", "gdpr_data_deletion", "gdpr_consent_change"]
        )
        access_requests = sum(
            1 for event in gdpr_events if event["event_type"] == "gdpr_data_request"
        )
        deletion_requests = sum(
            1 for event in gdpr_events if event["event_type"] == "gdpr_data_deletion"
        )
        consent_changes = sum(
            1 for event in gdpr_events if event["event_type"] == "gdpr_consent_change"
        )

        return {
            "report_type": "GDPR Article 30 - Records of Processing Activities",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_processing_activities": len(gdpr_events),
                "total_data_subjects": len(by_subject),
                "total_gdpr_requests": total_requests,
                "access_requests": access_requests,
                "deletion_requests": deletion_requests,
                "consent_changes": consent_changes,
            },
            "processing_activities": [
                {
                    "data_subject": subject,
                    "activity_count": len(activities),
                    "activities": activities,
                }
                for subject, activities in by_subject.items()
            ],
        }

    def generate_soc2_report(
        self, start_date: datetime, end_date: datetime, log_file: str = "audit.log"
    ) -> Dict[str, Any]:
        """
        Generate SOC 2 Type II access control report

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period
            log_file: Audit log file name

        Returns:
            SOC 2 compliance report
        """
        events = self.parse_audit_log(log_file, start_date, end_date)

        # Filter access control events
        access_events = [
            event
            for event in events
            if event["event_type"]
            in [
                "auth_login",
                "auth_logout",
                "auth_failed",
                "authz_granted",
                "authz_denied",
                "admin_user_create",
                "admin_user_delete",
                "admin_role_change",
            ]
        ]

        # Calculate statistics
        total_logins = sum(
            1 for event in access_events if event["event_type"] == "auth_login"
        )
        failed_logins = sum(
            1 for event in access_events if event["event_type"] == "auth_failed"
        )
        access_granted = sum(
            1 for event in access_events if event["event_type"] == "authz_granted"
        )
        access_denied = sum(
            1 for event in access_events if event["event_type"] == "authz_denied"
        )
        user_changes = sum(
            1
            for event in access_events
            if event["event_type"]
            in ["admin_user_create", "admin_user_delete", "admin_role_change"]
        )

        # Calculate success rate
        total_auth_attempts = total_logins + failed_logins
        success_rate = (
            (total_logins / total_auth_attempts * 100) if total_auth_attempts > 0 else 0
        )

        return {
            "report_type": "SOC 2 Type II - Access Control and Monitoring",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_access_events": len(access_events),
                "successful_logins": total_logins,
                "failed_logins": failed_logins,
                "authentication_success_rate": f"{success_rate:.2f}%",
                "access_granted": access_granted,
                "access_denied": access_denied,
                "user_management_changes": user_changes,
            },
            "access_control_events": access_events,
        }

    def generate_aml_report(
        self, start_date: datetime, end_date: datetime, log_file: str = "audit.log"
    ) -> Dict[str, Any]:
        """
        Generate BSA/AML compliance report

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period
            log_file: Audit log file name

        Returns:
            AML compliance report
        """
        events = self.parse_audit_log(log_file, start_date, end_date)

        # Filter AML events
        aml_events = [
            event
            for event in events
            if event["event_type"] == "aml_alert_generated"
        ]

        # Group by severity
        by_severity = defaultdict(list)
        for event in aml_events:
            by_severity[event["severity"]].append(event)

        # Count SARs filed
        sars_filed = sum(
            1
            for event in aml_events
            if event.get("metadata", {}).get("sar_filed", False)
        )

        return {
            "report_type": "BSA/AML - Suspicious Activity Monitoring",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_aml_alerts": len(aml_events),
                "critical_alerts": len(by_severity.get("critical", [])),
                "high_alerts": len(by_severity.get("error", [])),
                "medium_alerts": len(by_severity.get("warning", [])),
                "low_alerts": len(by_severity.get("info", [])),
                "sars_filed": sars_filed,
            },
            "alerts_by_severity": {
                severity: alerts for severity, alerts in by_severity.items()
            },
        }

    def generate_comprehensive_report(
        self, start_date: datetime, end_date: datetime, log_file: str = "audit.log"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period
            log_file: Audit log file name

        Returns:
            Comprehensive compliance report
        """
        events = self.parse_audit_log(log_file, start_date, end_date)
        metrics = self.calculate_metrics(events, start_date, end_date)
        violations = self.detect_violations(events)

        return {
            "report_type": "Comprehensive Compliance Report",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": metrics.to_dict(),
            "violations": [asdict(v) for v in violations],
            "gdpr_summary": self.generate_gdpr_report(start_date, end_date, log_file),
            "soc2_summary": self.generate_soc2_report(start_date, end_date, log_file),
            "aml_summary": self.generate_aml_report(start_date, end_date, log_file),
        }

    def export_report(
        self, report: Dict[str, Any], output_file: str, format: str = "json"
    ) -> None:
        """
        Export compliance report to file

        Args:
            report: Compliance report dictionary
            output_file: Output file path
            format: Export format (json, csv, html)
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
        elif format == "csv":
            # Export metrics as CSV
            import csv

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                for key, value in report.get("metrics", {}).items():
                    writer.writerow([key, value])
        elif format == "html":
            # Export as HTML report
            html = self._generate_html_report(report)
            with open(output_path, "w") as f:
                f.write(html)

    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML report from compliance data"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{report['report_type']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .critical {{ color: red; font-weight: bold; }}
        .warning {{ color: orange; }}
        .info {{ color: blue; }}
    </style>
</head>
<body>
    <h1>{report['report_type']}</h1>
    <p><strong>Period:</strong> {report['period_start']} to {report['period_end']}</p>
    <p><strong>Generated:</strong> {report['generated_at']}</p>
    
    <h2>Summary Metrics</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
"""
        for key, value in report.get("metrics", {}).items():
            html += f"        <tr><td>{key}</td><td>{value}</td></tr>\n"

        html += """
    </table>
</body>
</html>
"""
        return html


# Convenience function for generating reports
def generate_compliance_report(
    report_type: str,
    start_date: datetime,
    end_date: datetime,
    log_dir: str = "/var/log/janusgraph",
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate compliance report

    Args:
        report_type: Type of report (gdpr, soc2, aml, comprehensive)
        start_date: Start of reporting period
        end_date: End of reporting period
        log_dir: Directory containing audit logs
        output_file: Optional output file path

    Returns:
        Compliance report dictionary
    """
    reporter = ComplianceReporter(log_dir=log_dir)

    if report_type == "gdpr":
        report = reporter.generate_gdpr_report(start_date, end_date)
    elif report_type == "soc2":
        report = reporter.generate_soc2_report(start_date, end_date)
    elif report_type == "aml":
        report = reporter.generate_aml_report(start_date, end_date)
    else:
        report = reporter.generate_comprehensive_report(start_date, end_date)

    if output_file:
        reporter.export_report(report, output_file)

    return report

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
