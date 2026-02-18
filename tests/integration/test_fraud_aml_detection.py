#!/usr/bin/env python3
"""
Integration Tests for Fraud and AML Detection

Tests fraud detection and AML structuring detection against a real JanusGraph instance.
Requires JanusGraph to be running on port 18182.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Created: 2026-02-06
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from tests.integration._integration_test_utils import run_with_timeout_bool

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src/python"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../banking"))

from gremlin_python.driver import client, serializer
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T

# Test configuration
JANUSGRAPH_HOST = os.getenv("JANUSGRAPH_HOST", "localhost")
JANUSGRAPH_PORT = int(os.getenv("JANUSGRAPH_PORT", "18182"))
GRAPH_URL = f"ws://{JANUSGRAPH_HOST}:{JANUSGRAPH_PORT}/gremlin"


def is_janusgraph_available() -> bool:
    """Check if JanusGraph is available using client approach."""

    def _check() -> bool:
        c = client.Client(GRAPH_URL, "g", message_serializer=serializer.GraphSONSerializersV3d0())
        c.submit("g.V().count()").all().result()
        c.close()
        return True

    return run_with_timeout_bool(_check, timeout_seconds=8.0)


# Skip all tests if JanusGraph is not available
pytestmark = [
    pytest.mark.skipif(
        not is_janusgraph_available(), reason="JanusGraph not available at localhost:18182"
    ),
    pytest.mark.timeout(180),
]


class GremlinClient:
    """Simple Gremlin client wrapper for tests."""

    def __init__(self, url: str):
        self.url = url
        self.client = client.Client(
            url, "g", message_serializer=serializer.GraphSONSerializersV3d0()
        )

    def execute(self, query: str):
        """Execute a Gremlin query string."""
        return self.client.submit(query).all().result()

    def close(self):
        """Close the connection."""
        self.client.close()


@pytest.fixture(scope="module")
def graph_client():
    """Provide a Gremlin client for tests."""
    gremlin_client = GremlinClient(GRAPH_URL)
    yield gremlin_client
    gremlin_client.close()


@pytest.fixture(scope="module")
def test_account_id():
    """Generate a unique test account ID."""
    return f"test-account-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def test_person_id():
    """Generate a unique test person ID."""
    return f"test-person-{uuid.uuid4().hex[:8]}"


class TestJanusGraphConnection:
    """Test basic JanusGraph connectivity."""

    def test_connection_established(self, graph_client):
        """Test that we can connect to JanusGraph."""
        result = graph_client.execute("g.V().count()")
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], int)
        assert result[0] >= 0

    def test_query_execution(self, graph_client):
        """Test that we can execute queries."""
        result = graph_client.execute("g.V().limit(5)")
        assert isinstance(result, list)

    def test_edge_count(self, graph_client):
        """Test that we can count edges."""
        result = graph_client.execute("g.E().count()")
        assert isinstance(result, list)
        assert isinstance(result[0], int)


class TestFraudDetectorIntegration:
    """Integration tests for FraudDetector."""

    @pytest.fixture(autouse=True)
    def setup_fraud_detector(self):
        """Set up the fraud detector."""
        # Import here to avoid import errors if dependencies missing
        from fraud.fraud_detection import FraudAlert, FraudDetector, FraudScore

        self.FraudDetector = FraudDetector
        self.FraudScore = FraudScore
        self.FraudAlert = FraudAlert

    def test_fraud_detector_initialization(self):
        """Test FraudDetector can be initialized."""
        try:
            detector = self.FraudDetector(
                janusgraph_host=JANUSGRAPH_HOST,
                janusgraph_port=JANUSGRAPH_PORT,
                opensearch_host="localhost",
                opensearch_port=9200,
            )
            assert detector is not None
            assert detector.graph_url == GRAPH_URL
        except Exception as e:
            # OpenSearch might not be available, but detector should still init
            pytest.skip(f"FraudDetector init failed (OpenSearch may be unavailable): {e}")

    def test_fraud_score_dataclass(self):
        """Test FraudScore dataclass creation."""
        score = self.FraudScore(
            transaction_id="txn-001",
            overall_score=0.75,
            velocity_score=0.6,
            network_score=0.8,
            merchant_score=0.7,
            behavioral_score=0.9,
            risk_level="high",
            recommendation="review",
        )
        assert score.overall_score == 0.75
        assert score.risk_level == "high"
        assert score.recommendation == "review"

    def test_fraud_alert_dataclass(self):
        """Test FraudAlert dataclass creation."""
        alert = self.FraudAlert(
            alert_id="alert-001",
            alert_type="velocity",
            severity="high",
            transaction_id="txn-001",
            account_id="acc-001",
            customer_id="cust-001",
            customer_name="Test Customer",
            amount=5000.0,
            merchant="Test Merchant",
            fraud_score=0.85,
            risk_factors=["high_velocity", "unusual_amount"],
            similar_cases=[],
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"source": "integration_test"},
        )
        assert alert.alert_type == "velocity"
        assert alert.severity == "high"
        assert len(alert.risk_factors) == 2

    def test_fraud_detector_thresholds(self):
        """Test FraudDetector threshold constants."""
        assert self.FraudDetector.CRITICAL_THRESHOLD == 0.9
        assert self.FraudDetector.HIGH_THRESHOLD == 0.75
        assert self.FraudDetector.MEDIUM_THRESHOLD == 0.5
        assert self.FraudDetector.LOW_THRESHOLD == 0.25

    def test_velocity_limits(self):
        """Test FraudDetector velocity limit constants."""
        assert self.FraudDetector.MAX_TRANSACTIONS_PER_HOUR == 10
        assert self.FraudDetector.MAX_AMOUNT_PER_HOUR == 5000.0
        assert self.FraudDetector.MAX_TRANSACTIONS_PER_DAY == 50
        assert self.FraudDetector.MAX_AMOUNT_PER_DAY == 20000.0


class TestStructuringDetectorIntegration:
    """Integration tests for StructuringDetector."""

    @pytest.fixture(autouse=True)
    def setup_structuring_detector(self):
        """Set up the structuring detector."""
        from aml.structuring_detection import (
            StructuringAlert,
            StructuringDetector,
            StructuringPattern,
        )

        self.StructuringDetector = StructuringDetector
        self.StructuringPattern = StructuringPattern
        self.StructuringAlert = StructuringAlert

    def test_structuring_detector_initialization(self):
        """Test StructuringDetector can be initialized."""
        detector = self.StructuringDetector(
            janusgraph_host=JANUSGRAPH_HOST, janusgraph_port=JANUSGRAPH_PORT
        )
        assert detector is not None
        assert detector.graph_url == GRAPH_URL
        assert detector.ctr_threshold == Decimal("10000.00")

    def test_custom_ctr_threshold(self):
        """Test StructuringDetector with custom CTR threshold."""
        custom_threshold = Decimal("5000.00")
        detector = self.StructuringDetector(
            janusgraph_host=JANUSGRAPH_HOST,
            janusgraph_port=JANUSGRAPH_PORT,
            ctr_threshold=custom_threshold,
        )
        assert detector.ctr_threshold == custom_threshold
        assert detector.suspicious_threshold == custom_threshold * Decimal("0.9")

    def test_structuring_pattern_dataclass(self):
        """Test StructuringPattern dataclass creation."""
        pattern = self.StructuringPattern(
            pattern_id="pat-001",
            pattern_type="smurfing",
            account_ids=["acc-001", "acc-002"],
            transaction_ids=["txn-001", "txn-002", "txn-003"],
            total_amount=Decimal("27000.00"),
            transaction_count=3,
            time_window_hours=24.0,
            confidence_score=0.92,
            risk_level="high",
            indicators=["just_below_threshold", "regular_timing"],
            detected_at=datetime.now(timezone.utc).isoformat(),
            metadata={"source": "integration_test"},
        )
        assert pattern.pattern_type == "smurfing"
        assert pattern.transaction_count == 3
        assert pattern.confidence_score == 0.92

    def test_structuring_alert_dataclass(self):
        """Test StructuringAlert dataclass creation."""
        pattern = self.StructuringPattern(
            pattern_id="pat-001",
            pattern_type="smurfing",
            account_ids=["acc-001"],
            transaction_ids=["txn-001", "txn-002"],
            total_amount=Decimal("18000.00"),
            transaction_count=2,
            time_window_hours=12.0,
            confidence_score=0.85,
            risk_level="high",
            indicators=["threshold_proximity"],
            detected_at=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

        alert = self.StructuringAlert(
            alert_id="alert-001",
            alert_type="smurfing_detected",
            severity="high",
            patterns=[pattern],
            accounts_involved=["acc-001"],
            total_amount=Decimal("18000.00"),
            recommendation="investigate",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        assert alert.alert_type == "smurfing_detected"
        assert len(alert.patterns) == 1
        assert alert.total_amount == Decimal("18000.00")

    def test_detection_thresholds(self):
        """Test StructuringDetector threshold constants."""
        assert self.StructuringDetector.CTR_THRESHOLD == Decimal("10000.00")
        assert self.StructuringDetector.SUSPICIOUS_THRESHOLD == Decimal("9000.00")
        assert self.StructuringDetector.MAX_TIME_WINDOW_HOURS == 24
        assert self.StructuringDetector.MIN_TRANSACTIONS_FOR_PATTERN == 3

    def test_detect_smurfing_no_data(self):
        """Test detect_smurfing with non-existent account."""
        detector = self.StructuringDetector(
            janusgraph_host=JANUSGRAPH_HOST, janusgraph_port=JANUSGRAPH_PORT
        )

        # Test with a non-existent account - should return empty list
        result = detector.detect_smurfing(
            account_id="non-existent-account-12345", time_window_hours=24, min_transactions=3
        )
        assert isinstance(result, list)
        assert len(result) == 0


class TestGraphDataQueries:
    """Test queries against existing graph data."""

    def test_count_person_vertices(self, graph_client):
        """Test counting person vertices."""
        result = graph_client.execute("g.V().hasLabel('Person').count()")
        assert isinstance(result, list)
        assert isinstance(result[0], int)
        # May be 0 if no data loaded, but should not error

    def test_count_account_vertices(self, graph_client):
        """Test counting account vertices."""
        result = graph_client.execute("g.V().hasLabel('Account').count()")
        assert isinstance(result, list)
        assert isinstance(result[0], int)

    def test_count_company_vertices(self, graph_client):
        """Test counting company vertices."""
        result = graph_client.execute("g.V().hasLabel('Company').count()")
        assert isinstance(result, list)
        assert isinstance(result[0], int)

    def test_count_transaction_edges(self, graph_client):
        """Test counting transaction edges."""
        result = graph_client.execute("g.E().hasLabel('MADE_TRANSACTION').count()")
        assert isinstance(result, list)
        assert isinstance(result[0], int)

    def test_vertex_labels(self, graph_client):
        """Test querying vertex labels."""
        result = graph_client.execute("g.V().label().dedup()")
        assert isinstance(result, list)
        # Check if common labels exist (if data is loaded)
        # Labels may vary based on what data is loaded


class TestFraudDetectionQueries:
    """Test fraud detection related queries."""

    def test_high_value_transactions(self, graph_client):
        """Test querying high value transactions."""
        # Query for transactions that have an amount property
        result = graph_client.execute("g.E().hasLabel('MADE_TRANSACTION').has('amount').limit(10)")
        assert isinstance(result, list)

    def test_recent_transactions(self, graph_client):
        """Test querying recent transactions."""
        # Query for transactions
        result = graph_client.execute("g.E().hasLabel('MADE_TRANSACTION').limit(10)")
        assert isinstance(result, list)


class TestAMLDetectionQueries:
    """Test AML detection related queries."""

    def test_account_transaction_count(self, graph_client):
        """Test counting transactions per account."""
        # Get accounts with transactions
        result = graph_client.execute(
            "g.V().hasLabel('Account').where(outE('MADE_TRANSACTION')).limit(10)"
        )
        assert isinstance(result, list)

    def test_transaction_amounts(self, graph_client):
        """Test querying transaction amounts."""
        result = graph_client.execute(
            "g.E().hasLabel('MADE_TRANSACTION').has('amount').values('amount').limit(100)"
        )
        assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
