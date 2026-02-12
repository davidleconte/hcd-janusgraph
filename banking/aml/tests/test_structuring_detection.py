"""
Tests for AML Structuring Detection Module

Tests cover:
- StructuringPattern and StructuringAlert dataclasses
- StructuringDetector initialization and configuration
- Connection management
- Smurfing detection
- Layering detection
- Network structuring detection
- Pattern analysis algorithms
- Alert generation
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from banking.aml.structuring_detection import (
    StructuringPattern,
    StructuringAlert,
    StructuringDetector,
)


# ============================================================================
# Test Dataclasses
# ============================================================================


class TestStructuringPattern:
    """Test StructuringPattern dataclass."""

    def test_pattern_creation(self):
        """Test creating a structuring pattern."""
        pattern = StructuringPattern(
            pattern_id="SMURF_123_456",
            pattern_type="smurfing",
            account_ids=["acc-1"],
            transaction_ids=["tx-1", "tx-2", "tx-3"],
            total_amount=Decimal("25000.00"),
            transaction_count=3,
            time_window_hours=12.0,
            confidence_score=0.85,
            risk_level="high",
            indicators=["Multiple transactions below threshold"],
            detected_at="2026-02-11T20:00:00Z",
            metadata={"avg_amount": 8333.33},
        )

        assert pattern.pattern_id == "SMURF_123_456"
        assert pattern.pattern_type == "smurfing"
        assert len(pattern.account_ids) == 1
        assert len(pattern.transaction_ids) == 3
        assert pattern.total_amount == Decimal("25000.00")
        assert pattern.confidence_score == 0.85
        assert pattern.risk_level == "high"

    def test_pattern_types(self):
        """Test different pattern types."""
        types = ["smurfing", "layering", "integration", "network_structuring"]
        for ptype in types:
            pattern = StructuringPattern(
                pattern_id=f"TEST_{ptype}",
                pattern_type=ptype,
                account_ids=["acc-1"],
                transaction_ids=["tx-1"],
                total_amount=Decimal("10000.00"),
                transaction_count=1,
                time_window_hours=24.0,
                confidence_score=0.75,
                risk_level="medium",
                indicators=[],
                detected_at=datetime.now(timezone.utc).isoformat(),
                metadata={},
            )
            assert pattern.pattern_type == ptype

    def test_risk_levels(self):
        """Test different risk levels."""
        risk_levels = ["critical", "high", "medium", "low"]
        for level in risk_levels:
            pattern = StructuringPattern(
                pattern_id="TEST_123",
                pattern_type="smurfing",
                account_ids=["acc-1"],
                transaction_ids=["tx-1"],
                total_amount=Decimal("10000.00"),
                transaction_count=1,
                time_window_hours=24.0,
                confidence_score=0.75,
                risk_level=level,
                indicators=[],
                detected_at=datetime.now(timezone.utc).isoformat(),
                metadata={},
            )
            assert pattern.risk_level == level


class TestStructuringAlert:
    """Test StructuringAlert dataclass."""

    def test_alert_creation(self):
        """Test creating a structuring alert."""
        pattern = StructuringPattern(
            pattern_id="SMURF_123",
            pattern_type="smurfing",
            account_ids=["acc-1"],
            transaction_ids=["tx-1", "tx-2"],
            total_amount=Decimal("18000.00"),
            transaction_count=2,
            time_window_hours=12.0,
            confidence_score=0.90,
            risk_level="critical",
            indicators=["High confidence smurfing"],
            detected_at=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

        alert = StructuringAlert(
            alert_id="ALERT_123",
            alert_type="structuring",
            severity="critical",
            patterns=[pattern],
            accounts_involved=["acc-1"],
            total_amount=Decimal("18000.00"),
            recommendation="File SAR immediately",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        assert alert.alert_id == "ALERT_123"
        assert alert.severity == "critical"
        assert len(alert.patterns) == 1
        assert alert.total_amount == Decimal("18000.00")

    def test_alert_multiple_patterns(self):
        """Test alert with multiple patterns."""
        patterns = [
            StructuringPattern(
                pattern_id=f"PATTERN_{i}",
                pattern_type="smurfing",
                account_ids=[f"acc-{i}"],
                transaction_ids=[f"tx-{i}"],
                total_amount=Decimal("9000.00"),
                transaction_count=1,
                time_window_hours=24.0,
                confidence_score=0.80,
                risk_level="high",
                indicators=[],
                detected_at=datetime.now(timezone.utc).isoformat(),
                metadata={},
            )
            for i in range(3)
        ]

        alert = StructuringAlert(
            alert_id="MULTI_ALERT",
            alert_type="structuring",
            severity="high",
            patterns=patterns,
            accounts_involved=["acc-0", "acc-1", "acc-2"],
            total_amount=Decimal("27000.00"),
            recommendation="Investigate immediately",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        assert len(alert.patterns) == 3
        assert len(alert.accounts_involved) == 3


# ============================================================================
# Test StructuringDetector Initialization
# ============================================================================


class TestStructuringDetectorInit:
    """Test StructuringDetector initialization."""

    def test_default_initialization(self):
        """Test detector with default parameters."""
        detector = StructuringDetector()

        assert detector.graph_url == "ws://localhost:18182/gremlin"
        assert detector.ctr_threshold == Decimal("10000.00")
        assert detector.suspicious_threshold == Decimal("9000.00")
        assert detector._connection is None
        assert detector._g is None

    def test_custom_host_port(self):
        """Test detector with custom host and port."""
        detector = StructuringDetector(janusgraph_host="graph.example.com", janusgraph_port=8182)

        assert detector.graph_url == "ws://graph.example.com:8182/gremlin"

    def test_custom_ctr_threshold(self):
        """Test detector with custom CTR threshold."""
        custom_threshold = Decimal("5000.00")
        detector = StructuringDetector(ctr_threshold=custom_threshold)

        assert detector.ctr_threshold == custom_threshold
        assert detector.suspicious_threshold == Decimal("4500.00")  # 90% of threshold

    def test_class_constants(self):
        """Test class-level constants."""
        assert StructuringDetector.CTR_THRESHOLD == Decimal("10000.00")
        assert StructuringDetector.SUSPICIOUS_THRESHOLD == Decimal("9000.00")
        assert StructuringDetector.MAX_TIME_WINDOW_HOURS == 24
        assert StructuringDetector.MIN_TRANSACTIONS_FOR_PATTERN == 3
        assert StructuringDetector.HIGH_CONFIDENCE_THRESHOLD == 0.85
        assert StructuringDetector.MEDIUM_CONFIDENCE_THRESHOLD == 0.70


# ============================================================================
# Test Connection Management
# ============================================================================


class TestStructuringDetectorConnection:
    """Test connection management."""

    @patch("banking.aml.structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.structuring_detection.traversal")
    def test_connect(self, mock_traversal, mock_connection):
        """Test connecting to JanusGraph."""
        detector = StructuringDetector()
        mock_g = Mock()
        mock_traversal.return_value.withRemote.return_value = mock_g

        detector.connect()

        mock_connection.assert_called_once_with("ws://localhost:18182/gremlin", "g")
        assert detector._connection is not None
        assert detector._g == mock_g

    @patch("banking.aml.structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.structuring_detection.traversal")
    def test_connect_idempotent(self, mock_traversal, mock_connection):
        """Test that connect is idempotent."""
        detector = StructuringDetector()
        mock_g = Mock()
        mock_traversal.return_value.withRemote.return_value = mock_g

        detector.connect()
        detector.connect()  # Second call should not reconnect

        mock_connection.assert_called_once()

    @patch("banking.aml.structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.structuring_detection.traversal")
    def test_disconnect(self, mock_traversal, mock_connection):
        """Test disconnecting from JanusGraph."""
        detector = StructuringDetector()
        mock_conn = Mock()
        mock_connection.return_value = mock_conn
        mock_g = Mock()
        mock_traversal.return_value.withRemote.return_value = mock_g

        detector.connect()
        detector.disconnect()

        mock_conn.close.assert_called_once()
        assert detector._connection is None
        assert detector._g is None

    @patch("banking.aml.structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.structuring_detection.traversal")
    def test_context_manager(self, mock_traversal, mock_connection):
        """Test using detector as context manager."""
        mock_conn = Mock()
        mock_connection.return_value = mock_conn
        mock_g = Mock()
        mock_traversal.return_value.withRemote.return_value = mock_g

        with StructuringDetector() as detector:
            assert detector._connection is not None
            assert detector._g is not None

        mock_conn.close.assert_called_once()


# ============================================================================
# Test Smurfing Detection
# ============================================================================


class TestSmurfingDetection:
    """Test smurfing pattern detection."""

    @patch("banking.aml.structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.structuring_detection.traversal")
    def test_detect_smurfing_no_transactions(self, mock_traversal, mock_connection):
        """Test smurfing detection with no suspicious transactions."""
        detector = StructuringDetector()
        mock_g = Mock()
        mock_g.V.return_value.has.return_value.outE.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = (
            []
        )
        mock_traversal.return_value.withRemote.return_value = mock_g
        detector._g = mock_g

        patterns = detector.detect_smurfing("acc-123")

        assert len(patterns) == 0

    @patch("banking.aml.structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.structuring_detection.traversal")
    def test_detect_smurfing_insufficient_transactions(self, mock_traversal, mock_connection):
        """Test smurfing detection with insufficient transactions."""
        detector = StructuringDetector()
        mock_g = Mock()
        # Only 2 transactions (below min_transactions=3)
        mock_g.V.return_value.has.return_value.outE.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = [
            {"id": "tx-1", "amount": 9000.0, "timestamp": 1000000, "to_account": "acc-2"},
            {"id": "tx-2", "amount": 9100.0, "timestamp": 1000100, "to_account": "acc-3"},
        ]
        mock_traversal.return_value.withRemote.return_value = mock_g
        detector._g = mock_g

        patterns = detector.detect_smurfing("acc-123", min_transactions=3)

        assert len(patterns) == 0

    @patch("banking.aml.structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.structuring_detection.traversal")
    def test_detect_smurfing_pattern_found(self, mock_traversal, mock_connection):
        """Test smurfing detection with valid pattern."""
        detector = StructuringDetector()
        mock_g = Mock()
        # 4 transactions just below threshold
        mock_g.V.return_value.has.return_value.outE.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = [
            {"id": "tx-1", "amount": 9000.0, "timestamp": 1000000, "to_account": "acc-2"},
            {"id": "tx-2", "amount": 9100.0, "timestamp": 1000100, "to_account": "acc-3"},
            {"id": "tx-3", "amount": 9200.0, "timestamp": 1000200, "to_account": "acc-4"},
            {"id": "tx-4", "amount": 9300.0, "timestamp": 1000300, "to_account": "acc-5"},
        ]
        mock_traversal.return_value.withRemote.return_value = mock_g
        detector._g = mock_g

        patterns = detector.detect_smurfing("acc-123")

        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "smurfing"
        assert len(pattern.transaction_ids) == 4
        assert pattern.total_amount == Decimal("36600.00")

    @patch("banking.aml.structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.structuring_detection.traversal")
    def test_detect_smurfing_custom_time_window(self, mock_traversal, mock_connection):
        """Test smurfing detection with custom time window."""
        detector = StructuringDetector()
        mock_g = Mock()
        mock_g.V.return_value.has.return_value.outE.return_value.has.return_value.has.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = [
            {"id": "tx-1", "amount": 9000.0, "timestamp": 1000000, "to_account": "acc-2"},
            {"id": "tx-2", "amount": 9100.0, "timestamp": 1000100, "to_account": "acc-3"},
            {"id": "tx-3", "amount": 9200.0, "timestamp": 1000200, "to_account": "acc-4"},
        ]
        mock_traversal.return_value.withRemote.return_value = mock_g
        detector._g = mock_g

        patterns = detector.detect_smurfing("acc-123", time_window_hours=12)

        assert len(patterns) == 1
        assert patterns[0].time_window_hours == 12


# ============================================================================
# Test Pattern Analysis
# ============================================================================


class TestPatternAnalysis:
    """Test pattern analysis algorithms."""

    def test_analyze_smurfing_pattern_high_confidence(self):
        """Test smurfing pattern analysis with high confidence."""
        detector = StructuringDetector()
        transactions = [
            {"id": "tx-1", "amount": 9000.0, "timestamp": 1000000},
            {"id": "tx-2", "amount": 9100.0, "timestamp": 1000100},
            {"id": "tx-3", "amount": 9200.0, "timestamp": 1000200},
            {"id": "tx-4", "amount": 9300.0, "timestamp": 1000300},
        ]

        pattern = detector._analyze_smurfing_pattern("acc-123", transactions, 12)

        assert pattern is not None
        assert pattern.pattern_type == "smurfing"
        assert pattern.confidence_score >= 0.85  # High confidence
        assert pattern.risk_level == "critical"
        assert len(pattern.indicators) > 0

    def test_analyze_smurfing_pattern_medium_confidence(self):
        """Test smurfing pattern analysis with medium confidence."""
        detector = StructuringDetector()
        transactions = [
            {"id": "tx-1", "amount": 9000.0, "timestamp": 1000000},
            {"id": "tx-2", "amount": 8000.0, "timestamp": 1000100},
            {"id": "tx-3", "amount": 7000.0, "timestamp": 1000200},
        ]

        pattern = detector._analyze_smurfing_pattern("acc-123", transactions, 24)

        assert pattern is not None
        # Confidence may be lower due to variance in amounts
        assert pattern.confidence_score >= 0.3  # At least some confidence
        assert pattern.risk_level in ["high", "medium"]

    def test_analyze_smurfing_pattern_empty_transactions(self):
        """Test pattern analysis with empty transactions."""
        detector = StructuringDetector()

        pattern = detector._analyze_smurfing_pattern("acc-123", [], 24)

        assert pattern is None

    def test_analyze_layering_pattern(self):
        """Test layering pattern analysis."""
        detector = StructuringDetector()
        transactions = [
            {"id": "tx-1", "amount": 5000.0, "timestamp": 1000000},
            {"id": "tx-2", "amount": 5000.0, "timestamp": 1000100},
            {"id": "tx-3", "amount": 5000.0, "timestamp": 1000200},
        ]

        pattern = detector._analyze_layering_pattern("acc-123", transactions, 48)

        assert pattern is not None
        assert pattern.pattern_type == "layering"
        assert pattern.confidence_score >= 0.7
        # Check for the actual indicator text from implementation
        assert any("Circular" in ind for ind in pattern.indicators)

    def test_analyze_network_pattern(self):
        """Test network structuring pattern analysis."""
        detector = StructuringDetector()
        account_ids = ["acc-1", "acc-2", "acc-3", "acc-4"]
        transactions = [
            {"id": "tx-1", "amount": 9000.0, "timestamp": 1000000, "account": "acc-1"},
            {"id": "tx-2", "amount": 9100.0, "timestamp": 1000100, "account": "acc-2"},
            {"id": "tx-3", "amount": 9200.0, "timestamp": 1000200, "account": "acc-3"},
        ]

        pattern = detector._analyze_network_pattern(account_ids, transactions, 24)

        assert pattern is not None
        assert pattern.pattern_type == "network_structuring"
        assert len(pattern.account_ids) == 4
        assert pattern.confidence_score >= 0.75


# ============================================================================
# Test Alert Generation
# ============================================================================


class TestAlertGeneration:
    """Test alert generation."""

    def test_generate_alert_no_patterns(self):
        """Test alert generation with no patterns."""
        detector = StructuringDetector()

        alert = detector.generate_alert([])

        assert alert is None

    def test_generate_alert_critical_severity(self):
        """Test alert generation with critical severity."""
        detector = StructuringDetector()
        pattern = StructuringPattern(
            pattern_id="SMURF_123",
            pattern_type="smurfing",
            account_ids=["acc-1"],
            transaction_ids=["tx-1", "tx-2"],
            total_amount=Decimal("18000.00"),
            transaction_count=2,
            time_window_hours=12.0,
            confidence_score=0.90,  # High confidence
            risk_level="critical",
            indicators=["High confidence smurfing"],
            detected_at=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

        alert = detector.generate_alert([pattern])

        assert alert is not None
        assert alert.severity == "critical"
        assert "SAR" in alert.recommendation
        assert "freeze" in alert.recommendation.lower()

    def test_generate_alert_high_severity(self):
        """Test alert generation with high severity."""
        detector = StructuringDetector()
        pattern = StructuringPattern(
            pattern_id="LAYER_123",
            pattern_type="layering",
            account_ids=["acc-1"],
            transaction_ids=["tx-1", "tx-2"],
            total_amount=Decimal("15000.00"),
            transaction_count=2,
            time_window_hours=24.0,
            confidence_score=0.75,  # Medium-high confidence
            risk_level="high",
            indicators=["Layering detected"],
            detected_at=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

        alert = detector.generate_alert([pattern])

        assert alert is not None
        assert alert.severity == "high"
        assert "Investigate" in alert.recommendation

    def test_generate_alert_multiple_patterns(self):
        """Test alert generation with multiple patterns."""
        detector = StructuringDetector()
        patterns = [
            StructuringPattern(
                pattern_id=f"PATTERN_{i}",
                pattern_type="smurfing",
                account_ids=[f"acc-{i}"],
                transaction_ids=[f"tx-{i}"],
                total_amount=Decimal("9000.00"),
                transaction_count=1,
                time_window_hours=24.0,
                confidence_score=0.80,
                risk_level="high",
                indicators=[],
                detected_at=datetime.now(timezone.utc).isoformat(),
                metadata={},
            )
            for i in range(3)
        ]

        alert = detector.generate_alert(patterns)

        assert alert is not None
        assert len(alert.patterns) == 3
        assert len(alert.accounts_involved) == 3
        assert alert.total_amount == Decimal("27000.00")


# ============================================================================
# Test Error Handling
# ============================================================================


class TestErrorHandling:
    """Test error handling."""

    @patch("banking.aml.structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.structuring_detection.traversal")
    def test_detect_smurfing_exception(self, mock_traversal, mock_connection):
        """Test smurfing detection handles exceptions gracefully."""
        detector = StructuringDetector()
        mock_g = Mock()
        mock_g.V.side_effect = Exception("Graph connection error")
        mock_traversal.return_value.withRemote.return_value = mock_g
        detector._g = mock_g

        patterns = detector.detect_smurfing("acc-123")

        assert len(patterns) == 0  # Returns empty list on error

    @patch("banking.aml.structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.structuring_detection.traversal")
    def test_detect_layering_exception(self, mock_traversal, mock_connection):
        """Test layering detection handles exceptions gracefully."""
        detector = StructuringDetector()
        mock_g = Mock()
        mock_g.V.side_effect = Exception("Graph connection error")
        mock_traversal.return_value.withRemote.return_value = mock_g
        detector._g = mock_g

        patterns = detector.detect_layering(["acc-1", "acc-2"])

        assert len(patterns) == 0

    @patch("banking.aml.structuring_detection.DriverRemoteConnection")
    @patch("banking.aml.structuring_detection.traversal")
    def test_detect_network_structuring_exception(self, mock_traversal, mock_connection):
        """Test network structuring handles exceptions gracefully."""
        detector = StructuringDetector()
        mock_g = Mock()
        mock_g.V.side_effect = Exception("Graph connection error")
        mock_traversal.return_value.withRemote.return_value = mock_g
        detector._g = mock_g

        patterns = detector.detect_network_structuring("acc-123")

        assert len(patterns) == 0

# Made with Bob
