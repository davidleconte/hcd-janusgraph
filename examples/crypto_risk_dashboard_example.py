"""
Crypto Risk Dashboard Example

Demonstrates how to create a comprehensive risk monitoring dashboard
for crypto AML compliance using the RiskDashboard class.

This example generates sample data to show dashboard capabilities.
In production, data would come from JanusGraph via Gremlin queries.

Author: Banking Compliance Team
Date: 2026-04-10
"""

from datetime import datetime, timedelta
from typing import List, Tuple

from banking.crypto.visualizations import (
    AlertSummary,
    RiskDashboard,
    RiskMetrics,
    create_risk_dashboard,
)


def generate_sample_metrics() -> RiskMetrics:
    """Generate sample risk metrics for demonstration."""
    return RiskMetrics(
        total_wallets=1000,
        high_risk_wallets=45,
        medium_risk_wallets=180,
        low_risk_wallets=775,
        mixer_interactions=23,
        sanctioned_wallets=8,
        suspicious_transactions=67,
        total_transactions=15420,
        alerts_last_24h=12,
        alerts_last_7d=89,
        avg_risk_score=0.32,
        timestamp=datetime.now(),
    )


def generate_sample_alerts() -> List[AlertSummary]:
    """Generate sample alerts for demonstration."""
    now = datetime.now()
    alerts = []

    # Critical alerts
    alerts.append(
        AlertSummary(
            alert_id="ALT-001",
            alert_type="mixer",
            severity="critical",
            wallet_id="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            description="Multiple mixer interactions detected",
            timestamp=now - timedelta(hours=2),
            status="investigating",
        )
    )

    alerts.append(
        AlertSummary(
            alert_id="ALT-002",
            alert_type="sanctions",
            severity="critical",
            wallet_id="0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
            description="Transaction with sanctioned jurisdiction",
            timestamp=now - timedelta(hours=5),
            status="open",
        )
    )

    # High severity alerts
    for i in range(3, 8):
        alerts.append(
            AlertSummary(
                alert_id=f"ALT-{i:03d}",
                alert_type="high_value" if i % 2 == 0 else "velocity",
                severity="high",
                wallet_id=f"0x{i:040x}",
                description=f"Suspicious activity pattern {i}",
                timestamp=now - timedelta(hours=i * 2),
                status="investigating" if i % 2 == 0 else "open",
            )
        )

    # Medium severity alerts
    for i in range(8, 15):
        alerts.append(
            AlertSummary(
                alert_id=f"ALT-{i:03d}",
                alert_type="velocity",
                severity="medium",
                wallet_id=f"0x{i:040x}",
                description=f"Elevated transaction velocity",
                timestamp=now - timedelta(days=i - 7),
                status="resolved" if i % 3 == 0 else "open",
            )
        )

    return alerts


def generate_sample_risk_trend() -> List[Tuple[datetime, float]]:
    """Generate sample risk score trend for demonstration."""
    now = datetime.now()
    trend = []

    # Generate 30 days of trend data
    for i in range(30, 0, -1):
        date = now - timedelta(days=i)
        # Simulate increasing risk over time with some variation
        base_risk = 0.25 + (30 - i) * 0.003
        variation = (i % 7) * 0.01 - 0.03
        risk_score = max(0.2, min(0.5, base_risk + variation))
        trend.append((date, risk_score))

    return trend


def generate_sample_top_risks() -> List[Tuple[str, float, str]]:
    """Generate sample top high-risk wallets for demonstration."""
    return [
        ("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", 0.95, "Multiple mixer interactions"),
        ("0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063", 0.92, "Sanctioned jurisdiction"),
        ("0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", 0.88, "High-value suspicious transactions"),
        ("0x514910771AF9Ca656af840dff83E8264EcF986CA", 0.85, "Rapid transaction velocity"),
        ("0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9", 0.82, "Layering pattern detected"),
        ("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", 0.78, "Round-robin mixer usage"),
        ("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", 0.75, "Peeling chain detected"),
        ("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 0.72, "Multiple high-risk connections"),
        ("0xdAC17F958D2ee523a2206206994597C13D831ec7", 0.68, "Suspicious transaction patterns"),
        ("0x6B175474E89094C44Da98b954EedeAC495271d0F", 0.65, "Elevated risk indicators"),
    ]


def main():
    """Run the risk dashboard example."""
    print("=" * 70)
    print("Crypto AML Risk Dashboard Example")
    print("=" * 70)
    print()

    # Generate sample data
    print("Generating sample data...")
    metrics = generate_sample_metrics()
    alerts = generate_sample_alerts()
    risk_trend = generate_sample_risk_trend()
    top_risks = generate_sample_top_risks()

    print(f"  Metrics: {metrics.total_wallets} wallets, {metrics.total_transactions} transactions")
    print(f"  Alerts: {len(alerts)} recent alerts")
    print(f"  Risk Trend: {len(risk_trend)} data points")
    print(f"  Top Risks: {len(top_risks)} high-risk wallets")
    print()

    # Create dashboard using factory function
    print("Creating risk dashboard...")
    fig = create_risk_dashboard(
        metrics=metrics,
        alerts=alerts,
        risk_trend=risk_trend,
        top_risks=top_risks,
        title="Crypto AML Risk Dashboard - Live Monitoring",
    )

    # Save to HTML
    output_file = "crypto_risk_dashboard.html"
    fig.write_html(output_file)

    print(f"✅ Dashboard saved to: {output_file}")
    print()

    # Display summary statistics
    print("=" * 70)
    print("Dashboard Summary")
    print("=" * 70)
    print()
    print(f"Risk Distribution:")
    print(f"  High Risk:   {metrics.high_risk_wallets:4d} wallets ({metrics.high_risk_wallets/metrics.total_wallets*100:.1f}%)")
    print(f"  Medium Risk: {metrics.medium_risk_wallets:4d} wallets ({metrics.medium_risk_wallets/metrics.total_wallets*100:.1f}%)")
    print(f"  Low Risk:    {metrics.low_risk_wallets:4d} wallets ({metrics.low_risk_wallets/metrics.total_wallets*100:.1f}%)")
    print()
    print(f"Alert Summary:")
    print(f"  Last 24 hours: {metrics.alerts_last_24h} alerts")
    print(f"  Last 7 days:   {metrics.alerts_last_7d} alerts")
    print()
    print(f"Key Metrics:")
    print(f"  Mixer Interactions:      {metrics.mixer_interactions}")
    print(f"  Sanctioned Wallets:      {metrics.sanctioned_wallets}")
    print(f"  Suspicious Transactions: {metrics.suspicious_transactions}")
    print(f"  Average Risk Score:      {metrics.avg_risk_score:.2f}")
    print()

    # Alert breakdown by severity
    critical = sum(1 for a in alerts if a.severity == "critical")
    high = sum(1 for a in alerts if a.severity == "high")
    medium = sum(1 for a in alerts if a.severity == "medium")
    low = sum(1 for a in alerts if a.severity == "low")

    print(f"Alert Severity Breakdown:")
    print(f"  Critical: {critical}")
    print(f"  High:     {high}")
    print(f"  Medium:   {medium}")
    print(f"  Low:      {low}")
    print()

    print("=" * 70)
    print("Dashboard Features:")
    print("=" * 70)
    print("  ✅ Risk distribution pie chart")
    print("  ✅ 7-day alert trend")
    print("  ✅ Top 10 high-risk wallets")
    print("  ✅ Mixer interaction indicator")
    print("  ✅ Recent alerts table")
    print("  ✅ 30-day risk score trend")
    print()
    print(f"Open the dashboard: {output_file}")
    print()


if __name__ == "__main__":
    main()

# Made with Bob
