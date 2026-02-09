"""
Tests for AML Structuring Detection Module

Comprehensive test suite covering:
- Structuring detector initialization
- Smurfing pattern detection
- Layering pattern detection
- Network structuring detection
- Pattern analysis algorithms
- Alert generation
- Risk scoring
- Confidence calculation
"""

from datetime import datetime, timezone
from decimal import Decimal

from banking.aml.structuring_detection import StructuringDetector, StructuringPattern


class TestStructuringDetectorInitialization:
    """Test detector initialization and configuration"""

    def test_default_initialization(self):
        """Test detector initializes with default parameters"""
        detector = StructuringDetector()

        assert detector.ctr_threshold == Decimal("10000.00")
        assert detector.suspicious_threshold == Decimal("9000.00")
        assert detector.graph_url == "ws://localhost:8182/gremlin"

    def test_custom_threshold(self):
        """Test detector with custom CTR threshold"""
        custom_threshold = Decimal("5000.00")
        detector = StructuringDetector(ctr_threshold=custom_threshold)

        assert detector.ctr_threshold == custom_threshold
        assert detector.suspicious_threshold == custom_threshold * Decimal("0.9")

    def test_custom_host_port(self):
        """Test detector with custom host and port"""
        detector = StructuringDetector(janusgraph_host="graph.example.com", janusgraph_port=9999)

        assert detector.graph_url == "ws://graph.example.com:9999/gremlin"


class TestSmurfingPatternAnalysis:
    """Test smurfing pattern analysis logic"""

    def test_analyze_smurfing_pattern_basic(self):
        """Test basic smurfing pattern analysis"""
        detector = StructuringDetector()

        # Create mock transactions just below threshold
        transactions = [
            {"id": "TX-001", "amount": 9500.0, "timestamp": 1000000},
            {"id": "TX-002", "amount": 9600.0, "timestamp": 1001000},
            {"id": "TX-003", "amount": 9700.0, "timestamp": 1002000},
        ]

        pattern = detector._analyze_smurfing_pattern(
            account_id="ACC-123", transactions=transactions, time_window_hours=24
        )

        assert pattern is not None
        assert pattern.pattern_type == "smurfing"
        assert pattern.account_ids == ["ACC-123"]
        assert pattern.transaction_count == 3
        assert pattern.total_amount > Decimal("28000")
        assert pattern.confidence_score > 0.0

    def test_analyze_smurfing_high_confidence(self):
        """Test high confidence smurfing pattern"""
        detector = StructuringDetector()

        # Multiple similar amounts just below threshold in short window
        transactions = [
            {"id": f"TX-{i:03d}", "amount": 9800.0, "timestamp": 1000000 + i * 1000}
            for i in range(5)
        ]

        pattern = detector._analyze_smurfing_pattern(
            account_id="ACC-123", transactions=transactions, time_window_hours=6  # Short window
        )

        assert pattern is not None
        assert pattern.confidence_score >= 0.7
        assert pattern.risk_level in ["high", "critical"]
        assert len(pattern.indicators) >= 3

    def test_analyze_smurfing_low_variance(self):
        """Test detection of similar transaction amounts"""
        detector = StructuringDetector()

        # Very similar amounts (low variance)
        transactions = [
            {"id": "TX-001", "amount": 9500.0, "timestamp": 1000000},
            {"id": "TX-002", "amount": 9505.0, "timestamp": 1001000},
            {"id": "TX-003", "amount": 9510.0, "timestamp": 1002000},
        ]

        pattern = detector._analyze_smurfing_pattern(
            account_id="ACC-123", transactions=transactions, time_window_hours=24
        )

        assert pattern is not None
        assert any(
            "similar" in ind.lower() or "variance" in ind.lower() for ind in pattern.indicators
        )

    def test_analyze_smurfing_empty_transactions(self):
        """Test handling of empty transaction list"""
        detector = StructuringDetector()

        pattern = detector._analyze_smurfing_pattern(
            account_id="ACC-123", transactions=[], time_window_hours=24
        )

        assert pattern is None


class TestLayeringPatternAnalysis:
    """Test layering pattern analysis logic"""

    def test_analyze_layering_pattern_basic(self):
        """Test basic layering pattern analysis"""
        detector = StructuringDetector()

        transactions = [
            {"id": "TX-001", "amount": 5000.0, "timestamp": 1000000},
            {"id": "TX-002", "amount": 5000.0, "timestamp": 1001000},
        ]

        pattern = detector._analyze_layering_pattern(
            account_id="ACC-123", transactions=transactions, time_window_hours=48
        )

        assert pattern is not None
        assert pattern.pattern_type == "layering"
        assert pattern.transaction_count == 2
        assert "circular" in pattern.indicators[0].lower()

    def test_analyze_layering_confidence_scaling(self):
        """Test confidence increases with more transactions"""
        detector = StructuringDetector()

        # More transactions = higher confidence
        transactions_few = [
            {"id": f"TX-{i:03d}", "amount": 1000.0, "timestamp": 1000000 + i * 1000}
            for i in range(2)
        ]

        transactions_many = [
            {"id": f"TX-{i:03d}", "amount": 1000.0, "timestamp": 1000000 + i * 1000}
            for i in range(10)
        ]

        pattern_few = detector._analyze_layering_pattern("ACC-123", transactions_few, 48)
        pattern_many = detector._analyze_layering_pattern("ACC-123", transactions_many, 48)

        assert pattern_many.confidence_score > pattern_few.confidence_score

    def test_analyze_layering_insufficient_transactions(self):
        """Test handling of insufficient transactions"""
        detector = StructuringDetector()

        pattern = detector._analyze_layering_pattern(
            account_id="ACC-123",
            transactions=[{"id": "TX-001", "amount": 1000.0, "timestamp": 1000000}],
            time_window_hours=48,
        )

        assert pattern is None


class TestNetworkPatternAnalysis:
    """Test network structuring pattern analysis"""

    def test_analyze_network_pattern_basic(self):
        """Test basic network pattern analysis"""
        detector = StructuringDetector()

        account_ids = ["ACC-001", "ACC-002", "ACC-003"]
        transactions = [
            {"id": "TX-001", "amount": 9000.0, "timestamp": 1000000, "account": "ACC-001"},
            {"id": "TX-002", "amount": 9100.0, "timestamp": 1001000, "account": "ACC-002"},
            {"id": "TX-003", "amount": 9200.0, "timestamp": 1002000, "account": "ACC-003"},
        ]

        pattern = detector._analyze_network_pattern(
            account_ids=account_ids, transactions=transactions, time_window_hours=24
        )

        assert pattern is not None
        assert pattern.pattern_type == "network_structuring"
        assert len(pattern.account_ids) == 3
        assert pattern.transaction_count == 3
        assert "coordinated" in pattern.indicators[0].lower()

    def test_analyze_network_large_network(self):
        """Test large network increases confidence"""
        detector = StructuringDetector()

        # Larger network should have higher confidence
        account_ids_small = ["ACC-001", "ACC-002", "ACC-003"]
        account_ids_large = [f"ACC-{i:03d}" for i in range(10)]

        transactions = [
            {
                "id": f"TX-{i:03d}",
                "amount": 9000.0,
                "timestamp": 1000000 + i * 1000,
                "account": f"ACC-{i:03d}",
            }
            for i in range(10)
        ]

        pattern_small = detector._analyze_network_pattern(account_ids_small, transactions[:3], 24)
        pattern_large = detector._analyze_network_pattern(account_ids_large, transactions, 24)

        assert pattern_large.confidence_score > pattern_small.confidence_score
        assert pattern_large.risk_level in ["high", "critical"]

    def test_analyze_network_empty_transactions(self):
        """Test handling of empty transactions"""
        detector = StructuringDetector()

        pattern = detector._analyze_network_pattern(
            account_ids=["ACC-001", "ACC-002"], transactions=[], time_window_hours=24
        )

        assert pattern is None


class TestAlertGeneration:
    """Test alert generation from patterns"""

    def test_generate_alert_single_pattern(self):
        """Test alert generation from single pattern"""
        detector = StructuringDetector()

        pattern = StructuringPattern(
            pattern_id="SMURF_001",
            pattern_type="smurfing",
            account_ids=["ACC-123"],
            transaction_ids=["TX-001", "TX-002", "TX-003"],
            total_amount=Decimal("29000.00"),
            transaction_count=3,
            time_window_hours=24,
            confidence_score=0.85,
            risk_level="critical",
            indicators=["Multiple transactions below threshold"],
            detected_at=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

        alert = detector.generate_alert([pattern])

        assert alert is not None
        assert alert.alert_type == "structuring"
        assert alert.severity == "critical"
        assert len(alert.patterns) == 1
        assert len(alert.accounts_involved) == 1
        assert alert.total_amount == Decimal("29000.00")
        assert "SAR" in alert.recommendation

    def test_generate_alert_multiple_patterns(self):
        """Test alert generation from multiple patterns"""
        detector = StructuringDetector()

        patterns = [
            StructuringPattern(
                pattern_id=f"SMURF_{i:03d}",
                pattern_type="smurfing",
                account_ids=[f"ACC-{i:03d}"],
                transaction_ids=[f"TX-{i:03d}"],
                total_amount=Decimal("10000.00"),
                transaction_count=2,
                time_window_hours=24,
                confidence_score=0.75,
                risk_level="high",
                indicators=["Test indicator"],
                detected_at=datetime.now(timezone.utc).isoformat(),
                metadata={},
            )
            for i in range(3)
        ]

        alert = detector.generate_alert(patterns)

        assert alert is not None
        assert len(alert.patterns) == 3
        assert len(alert.accounts_involved) == 3
        assert alert.total_amount == Decimal("30000.00")

    def test_generate_alert_severity_levels(self):
        """Test alert severity determination"""
        detector = StructuringDetector()

        # High confidence -> critical severity
        pattern_critical = StructuringPattern(
            pattern_id="SMURF_001",
            pattern_type="smurfing",
            account_ids=["ACC-123"],
            transaction_ids=["TX-001"],
            total_amount=Decimal("10000.00"),
            transaction_count=1,
            time_window_hours=24,
            confidence_score=0.90,  # High confidence
            risk_level="critical",
            indicators=["Test"],
            detected_at=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

        # Medium confidence -> high severity
        pattern_high = StructuringPattern(
            pattern_id="SMURF_002",
            pattern_type="smurfing",
            account_ids=["ACC-456"],
            transaction_ids=["TX-002"],
            total_amount=Decimal("10000.00"),
            transaction_count=1,
            time_window_hours=24,
            confidence_score=0.75,  # Medium confidence
            risk_level="high",
            indicators=["Test"],
            detected_at=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

        alert_critical = detector.generate_alert([pattern_critical])
        alert_high = detector.generate_alert([pattern_high])

        assert alert_critical.severity == "critical"
        assert alert_high.severity == "high"
        assert "freeze" in alert_critical.recommendation.lower()
        assert "investigate" in alert_high.recommendation.lower()

    def test_generate_alert_empty_patterns(self):
        """Test handling of empty patterns list"""
        detector = StructuringDetector()

        alert = detector.generate_alert([])

        assert alert is None


class TestRiskLevelDetermination:
    """Test risk level calculation"""

    def test_risk_level_critical(self):
        """Test critical risk level assignment"""
        detector = StructuringDetector()

        transactions = [
            {"id": f"TX-{i:03d}", "amount": 9800.0, "timestamp": 1000000 + i * 1000}
            for i in range(5)
        ]

        pattern = detector._analyze_smurfing_pattern("ACC-123", transactions, 6)  # Short window

        assert pattern is not None
        if pattern.confidence_score >= detector.HIGH_CONFIDENCE_THRESHOLD:
            assert pattern.risk_level == "critical"

    def test_risk_level_high(self):
        """Test high risk level assignment"""
        detector = StructuringDetector()

        transactions = [
            {"id": f"TX-{i:03d}", "amount": 9500.0, "timestamp": 1000000 + i * 1000}
            for i in range(3)
        ]

        pattern = detector._analyze_smurfing_pattern("ACC-123", transactions, 12)

        assert pattern is not None
        assert pattern.risk_level in ["high", "medium", "critical"]


class TestConfidenceScoring:
    """Test confidence score calculation"""

    def test_confidence_multiple_indicators(self):
        """Test confidence increases with multiple indicators"""
        detector = StructuringDetector()

        # Transactions with multiple risk indicators
        transactions = [
            {"id": f"TX-{i:03d}", "amount": 9800.0, "timestamp": 1000000 + i * 1000}
            for i in range(5)
        ]

        pattern = detector._analyze_smurfing_pattern("ACC-123", transactions, 6)  # Short window

        assert pattern is not None
        assert pattern.confidence_score > 0.5
        assert len(pattern.indicators) >= 2

    def test_confidence_threshold_proximity(self):
        """Test confidence for amounts near threshold"""
        detector = StructuringDetector()

        # Amounts just below threshold
        transactions_near = [
            {"id": f"TX-{i:03d}", "amount": 9900.0, "timestamp": 1000000 + i * 1000}
            for i in range(3)
        ]

        # Amounts further from threshold
        transactions_far = [
            {"id": f"TX-{i:03d}", "amount": 8000.0, "timestamp": 1000000 + i * 1000}
            for i in range(3)
        ]

        pattern_near = detector._analyze_smurfing_pattern("ACC-123", transactions_near, 24)
        pattern_far = detector._analyze_smurfing_pattern("ACC-123", transactions_far, 24)

        # Transactions closer to threshold should have higher confidence
        assert pattern_near.confidence_score >= pattern_far.confidence_score


class TestPatternMetadata:
    """Test pattern metadata generation"""

    def test_smurfing_metadata(self):
        """Test smurfing pattern metadata"""
        detector = StructuringDetector()

        transactions = [
            {"id": "TX-001", "amount": 9500.0, "timestamp": 1000000},
            {"id": "TX-002", "amount": 9600.0, "timestamp": 1001000},
        ]

        pattern = detector._analyze_smurfing_pattern("ACC-123", transactions, 24)

        assert pattern is not None
        assert "avg_amount" in pattern.metadata
        assert "threshold" in pattern.metadata
        assert "variance" in pattern.metadata
        assert pattern.metadata["threshold"] == float(detector.ctr_threshold)

    def test_layering_metadata(self):
        """Test layering pattern metadata"""
        detector = StructuringDetector()

        transactions = [
            {"id": "TX-001", "amount": 5000.0, "timestamp": 1000000},
            {"id": "TX-002", "amount": 5000.0, "timestamp": 1001000},
        ]

        pattern = detector._analyze_layering_pattern("ACC-123", transactions, 48)

        assert pattern is not None
        assert "circular_pattern" in pattern.metadata
        assert pattern.metadata["circular_pattern"] is True

    def test_network_metadata(self):
        """Test network pattern metadata"""
        detector = StructuringDetector()

        account_ids = ["ACC-001", "ACC-002", "ACC-003"]
        transactions = [
            {
                "id": f"TX-{i:03d}",
                "amount": 9000.0,
                "timestamp": 1000000 + i * 1000,
                "account": f"ACC-{i:03d}",
            }
            for i in range(3)
        ]

        pattern = detector._analyze_network_pattern(account_ids, transactions, 24)

        assert pattern is not None
        assert "network_size" in pattern.metadata
        assert pattern.metadata["network_size"] == 3


class TestPatternIdentification:
    """Test pattern ID generation"""

    def test_smurfing_pattern_id_format(self):
        """Test smurfing pattern ID format"""
        detector = StructuringDetector()

        transactions = [{"id": "TX-001", "amount": 9500.0, "timestamp": 1000000}]

        pattern = detector._analyze_smurfing_pattern("ACC-123", transactions, 24)

        assert pattern is not None
        assert pattern.pattern_id.startswith("SMURF_ACC-123_")

    def test_layering_pattern_id_format(self):
        """Test layering pattern ID format"""
        detector = StructuringDetector()

        transactions = [
            {"id": "TX-001", "amount": 5000.0, "timestamp": 1000000},
            {"id": "TX-002", "amount": 5000.0, "timestamp": 1001000},
        ]

        pattern = detector._analyze_layering_pattern("ACC-123", transactions, 48)

        assert pattern is not None
        assert pattern.pattern_id.startswith("LAYER_ACC-123_")

    def test_network_pattern_id_format(self):
        """Test network pattern ID format"""
        detector = StructuringDetector()

        account_ids = ["ACC-001", "ACC-002"]
        transactions = [
            {"id": "TX-001", "amount": 9000.0, "timestamp": 1000000, "account": "ACC-001"}
        ]

        pattern = detector._analyze_network_pattern(account_ids, transactions, 24)

        assert pattern is not None
        assert pattern.pattern_id.startswith("NETWORK_")


class TestThresholdConfiguration:
    """Test threshold configuration and validation"""

    def test_default_thresholds(self):
        """Test default regulatory thresholds"""
        detector = StructuringDetector()

        assert detector.CTR_THRESHOLD == Decimal("10000.00")
        assert detector.SUSPICIOUS_THRESHOLD == Decimal("9000.00")
        assert detector.MAX_TIME_WINDOW_HOURS == 24
        assert detector.MIN_TRANSACTIONS_FOR_PATTERN == 3

    def test_custom_threshold_calculation(self):
        """Test suspicious threshold calculation"""
        custom_threshold = Decimal("5000.00")
        detector = StructuringDetector(ctr_threshold=custom_threshold)

        expected_suspicious = custom_threshold * Decimal("0.9")
        assert detector.suspicious_threshold == expected_suspicious

    def test_confidence_thresholds(self):
        """Test confidence threshold constants"""
        detector = StructuringDetector()

        assert detector.HIGH_CONFIDENCE_THRESHOLD == 0.85
        assert detector.MEDIUM_CONFIDENCE_THRESHOLD == 0.70
        assert detector.HIGH_CONFIDENCE_THRESHOLD > detector.MEDIUM_CONFIDENCE_THRESHOLD
