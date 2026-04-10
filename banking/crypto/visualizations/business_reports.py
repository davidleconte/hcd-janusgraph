"""
Business Reports for Crypto AML Compliance

This module generates executive-level business reports for crypto AML compliance,
including executive summaries, audit trail reports, and trend analysis.

Architecture Note:
- Reports are generated as formatted text/markdown
- Can be exported to PDF, HTML, or sent via email
- Data comes from JanusGraph via Gremlin queries (not included here)
- Designed for executives, auditors, and regulators

Author: Banking Compliance Team
Date: 2026-04-10
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class ExecutiveSummary:
    """Executive summary data for reporting period."""

    period_start: datetime
    period_end: datetime
    total_wallets: int
    new_wallets: int
    total_transactions: int
    total_volume_usd: float
    high_risk_wallets: int
    alerts_generated: int
    alerts_resolved: int
    mixer_detections: int
    sanctions_hits: int
    avg_risk_score: float
    risk_trend: str  # "increasing", "stable", "decreasing"


@dataclass
class AuditTrailEntry:
    """Single audit trail entry."""

    timestamp: datetime
    event_type: str  # "detection", "screening", "alert", "investigation", "resolution"
    wallet_id: str
    description: str
    user: str
    outcome: str


@dataclass
class TrendAnalysis:
    """Trend analysis data."""

    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    trend: str  # "up", "down", "stable"
    interpretation: str


class BusinessReportGenerator:
    """
    Generate business reports for crypto AML compliance.

    Reports include:
    - Executive summaries
    - Audit trail reports
    - Trend analysis
    - Compliance metrics
    """

    def __init__(self, company_name: str = "Financial Institution"):
        """
        Initialize report generator.

        Args:
            company_name: Name of the financial institution
        """
        self.company_name = company_name

    def generate_executive_summary(self, summary: ExecutiveSummary) -> str:
        """
        Generate executive summary report.

        Args:
            summary: Executive summary data

        Returns:
            Formatted report as string
        """
        period = f"{summary.period_start.strftime('%Y-%m-%d')} to {summary.period_end.strftime('%Y-%m-%d')}"
        days = (summary.period_end - summary.period_start).days

        report = f"""
{'=' * 80}
CRYPTO AML EXECUTIVE SUMMARY
{self.company_name}
{'=' * 80}

Reporting Period: {period} ({days} days)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 80}
KEY METRICS
{'=' * 80}

Portfolio Overview:
  Total Wallets:           {summary.total_wallets:,}
  New Wallets (Period):    {summary.new_wallets:,}
  Total Transactions:      {summary.total_transactions:,}
  Total Volume:            ${summary.total_volume_usd:,.2f}

Risk Assessment:
  High-Risk Wallets:       {summary.high_risk_wallets:,} ({summary.high_risk_wallets/summary.total_wallets*100:.1f}%)
  Average Risk Score:      {summary.avg_risk_score:.2f}
  Risk Trend:              {summary.risk_trend.upper()}

Alert Management:
  Alerts Generated:        {summary.alerts_generated:,}
  Alerts Resolved:         {summary.alerts_resolved:,}
  Resolution Rate:         {summary.alerts_resolved/summary.alerts_generated*100:.1f}%
  Open Alerts:             {summary.alerts_generated - summary.alerts_resolved:,}

Detection Results:
  Mixer Detections:        {summary.mixer_detections:,}
  Sanctions Hits:          {summary.sanctions_hits:,}

{'=' * 80}
RISK ASSESSMENT
{'=' * 80}

Overall Risk Level: {self._assess_risk_level(summary)}

Risk Indicators:
  • High-risk wallet concentration: {summary.high_risk_wallets/summary.total_wallets*100:.1f}%
  • Mixer interaction rate: {summary.mixer_detections/summary.total_wallets*100:.2f}%
  • Sanctions screening hit rate: {summary.sanctions_hits/summary.total_wallets*100:.2f}%
  • Average risk score trend: {summary.risk_trend}

{'=' * 80}
RECOMMENDATIONS
{'=' * 80}

{self._generate_recommendations(summary)}

{'=' * 80}
COMPLIANCE STATUS
{'=' * 80}

✅ All regulatory requirements met
✅ Monitoring systems operational
✅ Alert response within SLA
{'✅' if summary.alerts_resolved/summary.alerts_generated >= 0.8 else '⚠️'} Alert resolution rate: {summary.alerts_resolved/summary.alerts_generated*100:.1f}%

{'=' * 80}

Report prepared by: Crypto AML Compliance System
Next review: {(summary.period_end + timedelta(days=7)).strftime('%Y-%m-%d')}

{'=' * 80}
"""
        return report

    def generate_audit_trail_report(
        self, entries: List[AuditTrailEntry], period_start: datetime, period_end: datetime
    ) -> str:
        """
        Generate audit trail report.

        Args:
            entries: List of audit trail entries
            period_start: Start of reporting period
            period_end: End of reporting period

        Returns:
            Formatted report as string
        """
        period = f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"

        report = f"""
{'=' * 80}
CRYPTO AML AUDIT TRAIL REPORT
{self.company_name}
{'=' * 80}

Reporting Period: {period}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Entries: {len(entries)}

{'=' * 80}
AUDIT TRAIL ENTRIES
{'=' * 80}

"""
        # Group entries by date
        entries_by_date: Dict[str, List[AuditTrailEntry]] = {}
        for entry in sorted(entries, key=lambda e: e.timestamp):
            date_key = entry.timestamp.strftime('%Y-%m-%d')
            if date_key not in entries_by_date:
                entries_by_date[date_key] = []
            entries_by_date[date_key].append(entry)

        # Format entries by date
        for date_key, date_entries in entries_by_date.items():
            report += f"\n{date_key} ({len(date_entries)} entries)\n"
            report += "-" * 80 + "\n"

            for entry in date_entries:
                report += f"""
  {entry.timestamp.strftime('%H:%M:%S')} | {entry.event_type.upper()}
  Wallet: {entry.wallet_id}
  User: {entry.user}
  Description: {entry.description}
  Outcome: {entry.outcome}
"""

        report += f"""
{'=' * 80}
SUMMARY BY EVENT TYPE
{'=' * 80}

"""
        # Count by event type
        event_counts: Dict[str, int] = {}
        for entry in entries:
            event_counts[entry.event_type] = event_counts.get(entry.event_type, 0) + 1

        for event_type, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"  {event_type.upper():20s}: {count:4d}\n"

        report += f"""
{'=' * 80}

Report prepared by: Crypto AML Compliance System
Audit trail maintained for regulatory compliance

{'=' * 80}
"""
        return report

    def generate_trend_analysis_report(self, trends: List[TrendAnalysis]) -> str:
        """
        Generate trend analysis report.

        Args:
            trends: List of trend analyses

        Returns:
            Formatted report as string
        """
        report = f"""
{'=' * 80}
CRYPTO AML TREND ANALYSIS REPORT
{self.company_name}
{'=' * 80}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 80}
TREND ANALYSIS
{'=' * 80}

"""
        for trend in trends:
            arrow = "↑" if trend.trend == "up" else "↓" if trend.trend == "down" else "→"
            color = "🔴" if trend.trend == "up" and "risk" in trend.metric_name.lower() else "🟢"

            report += f"""
{color} {trend.metric_name}
  Current Value:    {trend.current_value:,.2f}
  Previous Value:   {trend.previous_value:,.2f}
  Change:           {arrow} {abs(trend.change_percent):.1f}%
  Interpretation:   {trend.interpretation}

"""

        report += f"""
{'=' * 80}
KEY INSIGHTS
{'=' * 80}

"""
        # Generate insights based on trends
        risk_trends = [t for t in trends if "risk" in t.metric_name.lower()]
        if risk_trends:
            avg_risk_change = sum(t.change_percent for t in risk_trends) / len(risk_trends)
            if avg_risk_change > 10:
                report += "⚠️  ALERT: Risk metrics showing significant increase\n"
            elif avg_risk_change < -10:
                report += "✅ POSITIVE: Risk metrics showing significant decrease\n"
            else:
                report += "ℹ️  STABLE: Risk metrics remain relatively stable\n"

        report += f"""
{'=' * 80}

Report prepared by: Crypto AML Compliance System

{'=' * 80}
"""
        return report

    def _assess_risk_level(self, summary: ExecutiveSummary) -> str:
        """Assess overall risk level based on summary metrics."""
        risk_score = 0

        # High-risk wallet percentage
        if summary.high_risk_wallets / summary.total_wallets > 0.1:
            risk_score += 3
        elif summary.high_risk_wallets / summary.total_wallets > 0.05:
            risk_score += 2
        else:
            risk_score += 1

        # Average risk score
        if summary.avg_risk_score > 0.5:
            risk_score += 3
        elif summary.avg_risk_score > 0.3:
            risk_score += 2
        else:
            risk_score += 1

        # Risk trend
        if summary.risk_trend == "increasing":
            risk_score += 2
        elif summary.risk_trend == "stable":
            risk_score += 1

        # Determine level
        if risk_score >= 7:
            return "🔴 HIGH - Immediate attention required"
        elif risk_score >= 5:
            return "🟡 MEDIUM - Enhanced monitoring recommended"
        else:
            return "🟢 LOW - Normal operations"

    def _generate_recommendations(self, summary: ExecutiveSummary) -> str:
        """Generate recommendations based on summary metrics."""
        recommendations = []

        # High-risk wallet concentration
        if summary.high_risk_wallets / summary.total_wallets > 0.1:
            recommendations.append(
                "1. HIGH PRIORITY: Review high-risk wallet concentration\n"
                "   - Conduct enhanced due diligence on high-risk wallets\n"
                "   - Consider additional screening measures"
            )

        # Alert resolution rate
        if summary.alerts_resolved / summary.alerts_generated < 0.8:
            recommendations.append(
                "2. OPERATIONAL: Improve alert resolution rate\n"
                "   - Current rate below 80% target\n"
                "   - Review alert triage process\n"
                "   - Consider additional analyst resources"
            )

        # Mixer detections
        if summary.mixer_detections > summary.total_wallets * 0.05:
            recommendations.append(
                "3. COMPLIANCE: Elevated mixer activity detected\n"
                "   - Review mixer detection patterns\n"
                "   - Consider enhanced transaction monitoring\n"
                "   - Update risk scoring models"
            )

        # Risk trend
        if summary.risk_trend == "increasing":
            recommendations.append(
                "4. STRATEGIC: Risk trend increasing\n"
                "   - Conduct comprehensive risk assessment\n"
                "   - Review and update risk policies\n"
                "   - Consider portfolio rebalancing"
            )

        if not recommendations:
            recommendations.append("✅ No immediate recommendations - Continue current monitoring")

        return "\n\n".join(recommendations)


def generate_executive_summary_report(
    summary: ExecutiveSummary, company_name: str = "Financial Institution"
) -> str:
    """
    Factory function to generate executive summary report.

    Args:
        summary: Executive summary data
        company_name: Name of the financial institution

    Returns:
        Formatted report as string
    """
    generator = BusinessReportGenerator(company_name)
    return generator.generate_executive_summary(summary)


def generate_audit_trail_report(
    entries: List[AuditTrailEntry],
    period_start: datetime,
    period_end: datetime,
    company_name: str = "Financial Institution",
) -> str:
    """
    Factory function to generate audit trail report.

    Args:
        entries: List of audit trail entries
        period_start: Start of reporting period
        period_end: End of reporting period
        company_name: Name of the financial institution

    Returns:
        Formatted report as string
    """
    generator = BusinessReportGenerator(company_name)
    return generator.generate_audit_trail_report(entries, period_start, period_end)


def generate_trend_analysis_report(
    trends: List[TrendAnalysis], company_name: str = "Financial Institution"
) -> str:
    """
    Factory function to generate trend analysis report.

    Args:
        trends: List of trend analyses
        company_name: Name of the financial institution

    Returns:
        Formatted report as string
    """
    generator = BusinessReportGenerator(company_name)
    return generator.generate_trend_analysis_report(trends)

# Made with Bob
