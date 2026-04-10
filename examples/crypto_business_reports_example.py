"""
Crypto Business Reports Example

Demonstrates how to generate executive-level business reports
for crypto AML compliance using the BusinessReportGenerator class.

This example generates sample data to show report capabilities.
In production, data would come from JanusGraph via Gremlin queries.

Author: Banking Compliance Team
Date: 2026-04-10
"""

from datetime import datetime, timedelta
from typing import List

from banking.crypto.visualizations import (
    AuditTrailEntry,
    ExecutiveSummary,
    TrendAnalysis,
    generate_audit_trail_report,
    generate_executive_summary_report,
    generate_trend_analysis_report,
)


def generate_sample_executive_summary() -> ExecutiveSummary:
    """Generate sample executive summary for demonstration."""
    now = datetime.now()
    return ExecutiveSummary(
        period_start=now - timedelta(days=30),
        period_end=now,
        total_wallets=1000,
        new_wallets=150,
        total_transactions=15420,
        total_volume_usd=45_678_900.50,
        high_risk_wallets=45,
        alerts_generated=89,
        alerts_resolved=76,
        mixer_detections=23,
        sanctions_hits=8,
        avg_risk_score=0.32,
        risk_trend="stable",
    )


def generate_sample_audit_trail() -> List[AuditTrailEntry]:
    """Generate sample audit trail entries for demonstration."""
    now = datetime.now()
    entries = []

    # Recent detections
    entries.append(
        AuditTrailEntry(
            timestamp=now - timedelta(hours=2),
            event_type="detection",
            wallet_id="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            description="Mixer interaction detected - 3 hops to known mixer",
            user="system",
            outcome="Alert ALT-001 generated",
        )
    )

    entries.append(
        AuditTrailEntry(
            timestamp=now - timedelta(hours=5),
            event_type="screening",
            wallet_id="0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
            description="Sanctions screening - High-risk jurisdiction detected",
            user="system",
            outcome="Alert ALT-002 generated",
        )
    )

    # Investigations
    entries.append(
        AuditTrailEntry(
            timestamp=now - timedelta(hours=8),
            event_type="investigation",
            wallet_id="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            description="Enhanced due diligence initiated",
            user="analyst@example.com",
            outcome="Investigation in progress",
        )
    )

    entries.append(
        AuditTrailEntry(
            timestamp=now - timedelta(days=1),
            event_type="investigation",
            wallet_id="0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
            description="High-value transaction review",
            user="analyst@example.com",
            outcome="Legitimate business activity confirmed",
        )
    )

    # Resolutions
    entries.append(
        AuditTrailEntry(
            timestamp=now - timedelta(days=1, hours=2),
            event_type="resolution",
            wallet_id="0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
            description="Alert ALT-045 resolved",
            user="analyst@example.com",
            outcome="False positive - No action required",
        )
    )

    entries.append(
        AuditTrailEntry(
            timestamp=now - timedelta(days=2),
            event_type="resolution",
            wallet_id="0x514910771AF9Ca656af840dff83E8264EcF986CA",
            description="Alert ALT-038 resolved",
            user="senior_analyst@example.com",
            outcome="SAR filed - Account restricted",
        )
    )

    # More historical entries
    for i in range(3, 8):
        entries.append(
            AuditTrailEntry(
                timestamp=now - timedelta(days=i),
                event_type="detection" if i % 2 == 0 else "screening",
                wallet_id=f"0x{i:040x}",
                description=f"Automated {'detection' if i % 2 == 0 else 'screening'} event {i}",
                user="system",
                outcome=f"Alert ALT-{i:03d} generated",
            )
        )

    return entries


def generate_sample_trends() -> List[TrendAnalysis]:
    """Generate sample trend analyses for demonstration."""
    return [
        TrendAnalysis(
            metric_name="Average Risk Score",
            current_value=0.32,
            previous_value=0.35,
            change_percent=-8.6,
            trend="down",
            interpretation="Risk score decreasing - Positive trend indicating improved portfolio quality",
        ),
        TrendAnalysis(
            metric_name="High-Risk Wallet Percentage",
            current_value=4.5,
            previous_value=5.2,
            change_percent=-13.5,
            trend="down",
            interpretation="High-risk wallet concentration decreasing - Enhanced screening measures effective",
        ),
        TrendAnalysis(
            metric_name="Alert Generation Rate",
            current_value=89.0,
            previous_value=76.0,
            change_percent=17.1,
            trend="up",
            interpretation="Alert volume increasing - May indicate emerging risk patterns or improved detection",
        ),
        TrendAnalysis(
            metric_name="Alert Resolution Rate",
            current_value=85.4,
            previous_value=82.1,
            change_percent=4.0,
            trend="up",
            interpretation="Resolution efficiency improving - Analyst productivity gains evident",
        ),
        TrendAnalysis(
            metric_name="Mixer Detection Rate",
            current_value=2.3,
            previous_value=2.8,
            change_percent=-17.9,
            trend="down",
            interpretation="Mixer activity decreasing - Deterrent effect of enhanced monitoring visible",
        ),
        TrendAnalysis(
            metric_name="Transaction Volume (USD)",
            current_value=45_678_900.0,
            previous_value=42_345_600.0,
            change_percent=7.9,
            trend="up",
            interpretation="Transaction volume growing - Business expansion within acceptable risk parameters",
        ),
    ]


def main():
    """Run the business reports example."""
    print("=" * 80)
    print("Crypto AML Business Reports Example")
    print("=" * 80)
    print()

    # Generate sample data
    print("Generating sample data...")
    executive_summary = generate_sample_executive_summary()
    audit_trail = generate_sample_audit_trail()
    trends = generate_sample_trends()

    print(f"  Executive Summary: 30-day period")
    print(f"  Audit Trail: {len(audit_trail)} entries")
    print(f"  Trend Analysis: {len(trends)} metrics")
    print()

    # Generate Executive Summary Report
    print("=" * 80)
    print("1. EXECUTIVE SUMMARY REPORT")
    print("=" * 80)
    print()

    exec_report = generate_executive_summary_report(
        summary=executive_summary, company_name="Demo Financial Institution"
    )
    print(exec_report)

    # Save to file
    with open("crypto_executive_summary.txt", "w") as f:
        f.write(exec_report)
    print("✅ Executive summary saved to: crypto_executive_summary.txt")
    print()

    # Generate Audit Trail Report
    print("=" * 80)
    print("2. AUDIT TRAIL REPORT")
    print("=" * 80)
    print()

    audit_report = generate_audit_trail_report(
        entries=audit_trail,
        period_start=executive_summary.period_start,
        period_end=executive_summary.period_end,
        company_name="Demo Financial Institution",
    )
    print(audit_report)

    # Save to file
    with open("crypto_audit_trail.txt", "w") as f:
        f.write(audit_report)
    print("✅ Audit trail report saved to: crypto_audit_trail.txt")
    print()

    # Generate Trend Analysis Report
    print("=" * 80)
    print("3. TREND ANALYSIS REPORT")
    print("=" * 80)
    print()

    trend_report = generate_trend_analysis_report(
        trends=trends, company_name="Demo Financial Institution"
    )
    print(trend_report)

    # Save to file
    with open("crypto_trend_analysis.txt", "w") as f:
        f.write(trend_report)
    print("✅ Trend analysis report saved to: crypto_trend_analysis.txt")
    print()

    # Summary
    print("=" * 80)
    print("REPORTS GENERATED")
    print("=" * 80)
    print()
    print("✅ crypto_executive_summary.txt - Executive-level overview")
    print("✅ crypto_audit_trail.txt - Detailed audit trail for compliance")
    print("✅ crypto_trend_analysis.txt - Trend analysis and insights")
    print()
    print("=" * 80)
    print("Report Features:")
    print("=" * 80)
    print("  ✅ Executive summaries with key metrics")
    print("  ✅ Risk assessment and recommendations")
    print("  ✅ Detailed audit trail for regulators")
    print("  ✅ Trend analysis with interpretations")
    print("  ✅ Compliance status tracking")
    print("  ✅ Automated insights and alerts")
    print()
    print("These reports can be:")
    print("  • Exported to PDF for distribution")
    print("  • Sent via email to stakeholders")
    print("  • Archived for regulatory compliance")
    print("  • Used in board presentations")
    print()


if __name__ == "__main__":
    main()

# Made with Bob
