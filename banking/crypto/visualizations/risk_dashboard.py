"""
Risk Dashboard for Crypto AML Monitoring

This module provides real-time risk monitoring dashboards for crypto AML compliance.
Displays key metrics, alerts, and trends for mixer detection and sanctions screening.

Architecture Note:
- Uses Plotly for interactive dashboards (HTML/JavaScript output)
- Data comes from JanusGraph via Gremlin queries (not included here)
- Dashboards are generated on-demand, not stored
- Designed for compliance officers and AML analysts

Author: Banking Compliance Team
Date: 2026-04-10
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots


@dataclass
class RiskMetrics:
    """Risk metrics for dashboard display."""

    total_wallets: int
    high_risk_wallets: int
    medium_risk_wallets: int
    low_risk_wallets: int
    mixer_interactions: int
    sanctioned_wallets: int
    suspicious_transactions: int
    total_transactions: int
    alerts_last_24h: int
    alerts_last_7d: int
    avg_risk_score: float
    timestamp: datetime


@dataclass
class AlertSummary:
    """Alert summary for dashboard display."""

    alert_id: str
    alert_type: str  # "mixer", "sanctions", "high_value", "velocity"
    severity: str  # "critical", "high", "medium", "low"
    wallet_id: str
    description: str
    timestamp: datetime
    status: str  # "open", "investigating", "resolved", "false_positive"


class RiskDashboard:
    """
    Real-time risk monitoring dashboard for crypto AML.

    Displays:
    - Risk score distribution
    - Alert trends over time
    - Top high-risk wallets
    - Mixer interaction statistics
    - Sanctions screening results
    """

    def __init__(self, title: str = "Crypto AML Risk Dashboard"):
        """
        Initialize risk dashboard.

        Args:
            title: Dashboard title
        """
        self.title = title

    def create_dashboard(
        self,
        metrics: RiskMetrics,
        alerts: List[AlertSummary],
        risk_trend: List[Tuple[datetime, float]],
        top_risks: List[Tuple[str, float, str]],
    ) -> go.Figure:
        """
        Create comprehensive risk dashboard.

        Args:
            metrics: Current risk metrics
            alerts: Recent alerts
            risk_trend: Risk score trend over time [(timestamp, avg_risk_score), ...]
            top_risks: Top high-risk wallets [(wallet_id, risk_score, reason), ...]

        Returns:
            Plotly figure with dashboard
        """
        # Create subplots: 2 rows, 3 columns
        fig = make_subplots(
            rows=2,
            cols=3,
            subplot_titles=(
                "Risk Distribution",
                "Alert Trends (7 Days)",
                "Top High-Risk Wallets",
                "Mixer Interactions",
                "Recent Alerts",
                "Risk Score Trend",
            ),
            specs=[
                [{"type": "pie"}, {"type": "bar"}, {"type": "bar"}],
                [{"type": "indicator"}, {"type": "table"}, {"type": "scatter"}],
            ],
            vertical_spacing=0.15,
            horizontal_spacing=0.1,
        )

        # 1. Risk Distribution (Pie Chart)
        fig.add_trace(
            go.Pie(
                labels=["High Risk", "Medium Risk", "Low Risk"],
                values=[
                    metrics.high_risk_wallets,
                    metrics.medium_risk_wallets,
                    metrics.low_risk_wallets,
                ],
                marker=dict(colors=["#d62728", "#ff7f0e", "#2ca02c"]),
                hole=0.3,
            ),
            row=1,
            col=1,
        )

        # 2. Alert Trends (Bar Chart)
        alert_counts = self._count_alerts_by_day(alerts)
        fig.add_trace(
            go.Bar(
                x=list(alert_counts.keys()),
                y=list(alert_counts.values()),
                marker=dict(color="#1f77b4"),
            ),
            row=1,
            col=2,
        )

        # 3. Top High-Risk Wallets (Horizontal Bar)
        if top_risks:
            wallet_ids = [w[0][:12] + "..." for w in top_risks[:10]]  # Truncate IDs
            risk_scores = [w[1] for w in top_risks[:10]]
            colors = ["#d62728" if s >= 0.8 else "#ff7f0e" for s in risk_scores]

            fig.add_trace(
                go.Bar(
                    y=wallet_ids,
                    x=risk_scores,
                    orientation="h",
                    marker=dict(color=colors),
                ),
                row=1,
                col=3,
            )

        # 4. Mixer Interactions (Indicator)
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=metrics.mixer_interactions,
                title={"text": "Mixer Interactions"},
                delta={"reference": metrics.mixer_interactions * 0.9},
                domain={"x": [0, 1], "y": [0, 1]},
            ),
            row=2,
            col=1,
        )

        # 5. Recent Alerts (Table)
        if alerts:
            recent_alerts = alerts[:10]  # Show last 10
            fig.add_trace(
                go.Table(
                    header=dict(
                        values=["Type", "Severity", "Wallet", "Status"],
                        fill_color="#1f77b4",
                        font=dict(color="white", size=12),
                    ),
                    cells=dict(
                        values=[
                            [a.alert_type for a in recent_alerts],
                            [a.severity for a in recent_alerts],
                            [a.wallet_id[:12] + "..." for a in recent_alerts],
                            [a.status for a in recent_alerts],
                        ],
                        fill_color=[
                            [
                                "#d62728" if a.severity == "critical" else
                                "#ff7f0e" if a.severity == "high" else
                                "#ffbb78" if a.severity == "medium" else
                                "#98df8a"
                                for a in recent_alerts
                            ]
                        ],
                        font=dict(size=11),
                    ),
                ),
                row=2,
                col=2,
            )

        # 6. Risk Score Trend (Line Chart)
        if risk_trend:
            timestamps = [t[0] for t in risk_trend]
            scores = [t[1] for t in risk_trend]

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=scores,
                    mode="lines+markers",
                    line=dict(color="#1f77b4", width=2),
                    marker=dict(size=6),
                ),
                row=2,
                col=3,
            )

        # Update layout
        fig.update_layout(
            title_text=self.title,
            title_font_size=20,
            showlegend=False,
            height=800,
            width=1400,
        )

        # Update axes
        fig.update_xaxes(title_text="Date", row=1, col=2)
        fig.update_yaxes(title_text="Alert Count", row=1, col=2)
        fig.update_xaxes(title_text="Risk Score", row=1, col=3)
        fig.update_xaxes(title_text="Date", row=2, col=3)
        fig.update_yaxes(title_text="Avg Risk Score", row=2, col=3)

        return fig

    def _count_alerts_by_day(self, alerts: List[AlertSummary]) -> Dict[str, int]:
        """
        Count alerts by day for the last 7 days.

        Args:
            alerts: List of alerts

        Returns:
            Dictionary mapping date string to alert count
        """
        # Get last 7 days
        today = datetime.now().date()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]

        # Count alerts per day
        counts = {date: 0 for date in dates}
        for alert in alerts:
            date_str = alert.timestamp.strftime("%Y-%m-%d")
            if date_str in counts:
                counts[date_str] += 1

        return counts

    def to_html(
        self,
        metrics: RiskMetrics,
        alerts: List[AlertSummary],
        risk_trend: List[Tuple[datetime, float]],
        top_risks: List[Tuple[str, float, str]],
        filename: str = "crypto_risk_dashboard.html",
    ) -> str:
        """
        Generate dashboard and save to HTML file.

        Args:
            metrics: Current risk metrics
            alerts: Recent alerts
            risk_trend: Risk score trend over time
            top_risks: Top high-risk wallets
            filename: Output filename

        Returns:
            Path to generated HTML file
        """
        fig = self.create_dashboard(metrics, alerts, risk_trend, top_risks)
        fig.write_html(filename)
        return filename


def create_risk_dashboard(
    metrics: RiskMetrics,
    alerts: List[AlertSummary],
    risk_trend: List[Tuple[datetime, float]],
    top_risks: List[Tuple[str, float, str]],
    title: str = "Crypto AML Risk Dashboard",
) -> go.Figure:
    """
    Factory function to create risk dashboard.

    Args:
        metrics: Current risk metrics
        alerts: Recent alerts
        risk_trend: Risk score trend over time
        top_risks: Top high-risk wallets
        title: Dashboard title

    Returns:
        Plotly figure with dashboard
    """
    dashboard = RiskDashboard(title=title)
    return dashboard.create_dashboard(metrics, alerts, risk_trend, top_risks)

# Made with Bob
