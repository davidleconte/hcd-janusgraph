"""
Pytest Configuration and Fixtures for Analytics Tests
======================================================

Provides reusable fixtures and mocks for testing analytics modules:
- Mock JanusGraph client
- Sample data generators
- Test utilities

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-11
Week 2: Analytics Testing Infrastructure
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

import pytest

# ============================================================================
# Mock JanusGraph Client Fixtures
# ============================================================================


@pytest.fixture
def mock_janusgraph_client():
    """
    Mock JanusGraph client for testing without real connection.

    Provides a mock client with submit() method that returns configurable results.

    Example:
        >>> def test_query(mock_janusgraph_client):
        ...     mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = [100]
        ...     detector = AMLStructuringDetector()
        ...     detector.client = mock_janusgraph_client
        ...     result = detector._query("g.V().count()")
        ...     assert result == [100]
    """
    client = Mock()

    # Mock the submit() -> all() -> result() chain
    mock_result = Mock()
    mock_result.all = Mock()
    mock_result.all.return_value.result = Mock()

    client.submit = Mock(return_value=mock_result)
    client.close = Mock()

    return client


@pytest.fixture
def mock_janusgraph_with_data(mock_janusgraph_client):
    """
    Mock JanusGraph client pre-configured with sample data responses.

    Returns different data based on query patterns:
    - Vertex count queries return 1000
    - Transaction queries return sample transactions
    - Person queries return sample persons
    """

    def submit_handler(query: str):
        """Handle different query types."""
        mock_result = Mock()

        if "count()" in query:
            # Count queries
            mock_result.all.return_value.result.return_value = [1000]
        elif "transaction" in query.lower():
            # Transaction queries
            mock_result.all.return_value.result.return_value = [
                {"id": "tx-1", "amount": 9500, "timestamp": "2026-01-01T10:00:00Z"},
                {"id": "tx-2", "amount": 9800, "timestamp": "2026-01-01T10:05:00Z"},
                {"id": "tx-3", "amount": 5000, "timestamp": "2026-01-01T11:00:00Z"},
            ]
        elif "person" in query.lower():
            # Person queries
            mock_result.all.return_value.result.return_value = [
                {"id": "p-1", "name": "John Doe", "email": "john@example.com"},
                {"id": "p-2", "name": "Jane Smith", "email": "jane@example.com"},
            ]
        else:
            # Default empty result
            mock_result.all.return_value.result.return_value = []

        return mock_result

    mock_janusgraph_client.submit.side_effect = submit_handler
    return mock_janusgraph_client


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_transactions():
    """
    Sample transaction data for AML structuring detection tests.

    Includes various transaction patterns:
    - Just under $10K threshold (structuring)
    - Normal transactions
    - Large transactions
    - Rapid succession transactions
    """
    return [
        # Structuring pattern - Account 1
        {"id": "tx-1", "amount": 9500.00, "account": "acc-1", "timestamp": "2026-01-01T10:00:00Z"},
        {"id": "tx-2", "amount": 9800.00, "account": "acc-1", "timestamp": "2026-01-01T10:05:00Z"},
        {"id": "tx-3", "amount": 9700.00, "account": "acc-1", "timestamp": "2026-01-01T10:10:00Z"},
        # Normal transactions - Account 2
        {"id": "tx-4", "amount": 5000.00, "account": "acc-2", "timestamp": "2026-01-01T11:00:00Z"},
        {"id": "tx-5", "amount": 3000.00, "account": "acc-2", "timestamp": "2026-01-01T12:00:00Z"},
        # Large transaction - Account 3
        {"id": "tx-6", "amount": 15000.00, "account": "acc-3", "timestamp": "2026-01-01T13:00:00Z"},
        # Boundary cases
        {"id": "tx-7", "amount": 9999.99, "account": "acc-4", "timestamp": "2026-01-01T14:00:00Z"},
        {"id": "tx-8", "amount": 10000.00, "account": "acc-5", "timestamp": "2026-01-01T15:00:00Z"},
    ]


@pytest.fixture
def sample_trades():
    """
    Sample trade data for insider trading detection tests.

    Includes:
    - Pre-announcement trades
    - Coordinated trades
    - Normal trades
    """
    base_time = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

    return [
        # Pre-announcement trades (suspicious)
        {
            "id": "trade-1",
            "trader_id": "p-1",
            "symbol": "ACME",
            "side": "buy",
            "quantity": 1000,
            "price": 50.00,
            "timestamp": base_time - timedelta(days=7),
        },
        {
            "id": "trade-2",
            "trader_id": "p-2",
            "symbol": "ACME",
            "side": "buy",
            "quantity": 1500,
            "price": 50.50,
            "timestamp": base_time - timedelta(days=7, hours=2),
        },
        # Normal trades
        {
            "id": "trade-3",
            "trader_id": "p-3",
            "symbol": "BETA",
            "side": "sell",
            "quantity": 500,
            "price": 75.00,
            "timestamp": base_time - timedelta(days=30),
        },
    ]


@pytest.fixture
def sample_corporate_events():
    """
    Sample corporate events for insider trading detection.

    Includes:
    - Earnings announcements
    - Merger announcements
    - Product launches
    """
    base_time = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

    return [
        {
            "event_id": "event-1",
            "company_id": "comp-1",
            "symbol": "ACME",
            "event_type": "earnings",
            "announcement_date": base_time,
            "impact": "positive",
            "price_change_percent": 15.0,
        },
        {
            "event_id": "event-2",
            "company_id": "comp-2",
            "symbol": "BETA",
            "event_type": "merger",
            "announcement_date": base_time + timedelta(days=30),
            "impact": "positive",
            "price_change_percent": 25.0,
        },
    ]


@pytest.fixture
def sample_companies():
    """
    Sample company data for TBML detection tests.

    Includes:
    - Normal companies
    - Shell companies (suspicious indicators)
    - Recently incorporated companies
    """
    return [
        # Normal company
        {
            "id": "comp-1",
            "name": "Acme Corp",
            "employees": 500,
            "incorporation_date": "2010-01-01",
            "annual_revenue": 50000000,
        },
        # Shell company (suspicious)
        {
            "id": "comp-2",
            "name": "Quick Trade LLC",
            "employees": 2,
            "incorporation_date": "2025-11-01",
            "annual_revenue": 10000000,
        },
        # Recently incorporated
        {
            "id": "comp-3",
            "name": "New Ventures Inc",
            "employees": 10,
            "incorporation_date": "2025-09-01",
            "annual_revenue": 1000000,
        },
    ]


@pytest.fixture
def sample_trade_transactions():
    """
    Sample trade transactions for TBML detection.

    Includes:
    - Normal trades
    - Over-invoiced trades
    - Under-invoiced trades
    - Circular trading patterns
    """
    return [
        # Normal trade
        {
            "id": "ttx-1",
            "from_company": "comp-1",
            "to_company": "comp-2",
            "goods": "Electronics",
            "declared_price": 10000,
            "market_price": 10000,
            "quantity": 100,
        },
        # Over-invoiced (suspicious)
        {
            "id": "ttx-2",
            "from_company": "comp-2",
            "to_company": "comp-3",
            "goods": "Textiles",
            "declared_price": 15000,
            "market_price": 10000,
            "quantity": 100,
        },
        # Under-invoiced (suspicious)
        {
            "id": "ttx-3",
            "from_company": "comp-3",
            "to_company": "comp-1",
            "goods": "Machinery",
            "declared_price": 8000,
            "market_price": 12000,
            "quantity": 50,
        },
    ]


@pytest.fixture
def sample_communications():
    """
    Sample communication data for insider trading detection.

    Includes:
    - Normal communications
    - Suspicious communications (keywords)
    - Flagged communications
    """
    base_time = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

    return [
        # Suspicious communication
        {
            "id": "comm-1",
            "from_person": "p-1",
            "to_person": "p-2",
            "content": "Buy ACME before the announcement next week",
            "timestamp": base_time - timedelta(days=8),
            "flagged": True,
        },
        # Normal communication
        {
            "id": "comm-2",
            "from_person": "p-3",
            "to_person": "p-4",
            "content": "Let's have lunch tomorrow",
            "timestamp": base_time - timedelta(days=5),
            "flagged": False,
        },
        # Suspicious keywords
        {
            "id": "comm-3",
            "from_person": "p-2",
            "to_person": "p-1",
            "content": "Insider information: earnings will be great",
            "timestamp": base_time - timedelta(days=10),
            "flagged": True,
        },
    ]


# ============================================================================
# Test Utility Fixtures
# ============================================================================


@pytest.fixture
def risk_score_validator():
    """
    Validator for risk scores.

    Ensures risk scores are:
    - Between 0 and 100
    - Numeric
    - Not NaN
    """

    def validate(score: float, min_score: float = 0.0, max_score: float = 100.0) -> bool:
        """Validate risk score is within expected range."""
        if not isinstance(score, (int, float)):
            return False
        if score != score:  # Check for NaN
            return False
        return min_score <= score <= max_score

    return validate


@pytest.fixture
def alert_validator():
    """
    Validator for detection alerts.

    Ensures alerts have required fields and valid values.
    """

    def validate(alert: Dict[str, Any]) -> bool:
        """Validate alert structure and content."""
        required_fields = ["alert_id", "alert_type", "severity", "risk_score"]

        # Check required fields
        for field in required_fields:
            if field not in alert:
                return False

        # Validate severity
        valid_severities = ["critical", "high", "medium", "low"]
        if alert["severity"] not in valid_severities:
            return False

        # Validate risk score
        if not (0 <= alert["risk_score"] <= 100):
            return False

        return True

    return validate


@pytest.fixture
def query_result_builder():
    """
    Builder for mock JanusGraph query results.

    Simplifies creating mock query responses.
    """

    class QueryResultBuilder:
        """Builder for constructing mock query results."""

        def __init__(self):
            self.results = []

        def add_vertex(self, label: str, properties: Dict[str, Any]) -> "QueryResultBuilder":
            """Add a vertex to results."""
            vertex = {"label": label, **properties}
            self.results.append(vertex)
            return self

        def add_edge(
            self, label: str, from_id: str, to_id: str, properties: Optional[Dict[str, Any]] = None
        ) -> "QueryResultBuilder":
            """Add an edge to results."""
            edge = {"label": label, "from": from_id, "to": to_id, **(properties or {})}
            self.results.append(edge)
            return self

        def build(self) -> List[Dict[str, Any]]:
            """Build and return results."""
            return self.results

        def build_mock(self) -> Mock:
            """Build and return as mock result."""
            mock_result = Mock()
            mock_result.all.return_value.result.return_value = self.results
            return mock_result

    return QueryResultBuilder()


# ============================================================================
# Parametrize Helpers
# ============================================================================


def transaction_amounts_parametrize():
    """
    Parametrize decorator for transaction amount test cases.

    Returns test cases for various transaction amount scenarios.
    """
    return pytest.mark.parametrize(
        "amounts,expected_risk",
        [
            # All under threshold - high risk
            ([9500, 9800, 9700], "high"),
            # Mixed amounts - medium risk
            ([9500, 5000, 3000], "medium"),
            # All normal - low risk
            ([5000, 3000, 2000], "low"),
            # Single large transaction - low risk
            ([15000], "low"),
            # Boundary case - exactly at threshold
            ([10000, 10000], "low"),
            # Empty list - no risk
            ([], "none"),
        ],
    )


def insider_trading_scenarios_parametrize():
    """
    Parametrize decorator for insider trading test scenarios.
    """
    return pytest.mark.parametrize(
        "scenario,expected_alert_type",
        [
            ("pre_announcement_buy", "timing"),
            ("coordinated_trades", "coordinated"),
            ("suspicious_communication", "communication"),
            ("network_connection", "network"),
        ],
    )


# ============================================================================
# Markers
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "analytics: Analytics module tests")
    config.addinivalue_line("markers", "aml: AML detection tests")
    config.addinivalue_line("markers", "insider_trading: Insider trading detection tests")
    config.addinivalue_line("markers", "tbml: TBML detection tests")
    config.addinivalue_line("markers", "requires_janusgraph: Tests requiring JanusGraph connection")


# Made with Bob
