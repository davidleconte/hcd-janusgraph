"""
Tests for Fraud Detection Module

Comprehensive test suite covering:
- Fraud detector initialization
- Transaction scoring
- Velocity checks
- Network analysis
- Merchant fraud detection
- Behavioral analysis
- Account takeover detection
- Similar case finding
- Alert generation
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from banking.fraud.fraud_detection import FraudDetector, FraudScore


class TestFraudDetectorInitialization:
    """Test fraud detector initialization"""

    def test_default_initialization(self):
        """Test detector initializes with default parameters"""
        with (
            patch("banking.fraud.fraud_detection.EmbeddingGenerator"),
            patch("banking.fraud.fraud_detection.VectorSearchClient"),
        ):
            detector = FraudDetector()

            assert detector.graph_url == "ws://localhost:8182/gremlin"
            assert detector.fraud_index == "fraud_cases"

    def test_custom_hosts_ports(self):
        """Test detector with custom hosts and ports"""
        with (
            patch("banking.fraud.fraud_detection.EmbeddingGenerator"),
            patch("banking.fraud.fraud_detection.VectorSearchClient"),
        ):
            detector = FraudDetector(
                janusgraph_host="graph.example.com",
                janusgraph_port=9999,
                opensearch_host="search.example.com",
                opensearch_port=9201,
            )

            assert detector.graph_url == "ws://graph.example.com:9999/gremlin"

    def test_embedding_model_configuration(self):
        """Test custom embedding model configuration"""
        with (
            patch("banking.fraud.fraud_detection.EmbeddingGenerator") as mock_gen,
            patch("banking.fraud.fraud_detection.VectorSearchClient"),
        ):
            FraudDetector(embedding_model="custom-model")

            mock_gen.assert_called_once_with(model_name="custom-model")


class TestTransactionScoring:
    """Test transaction fraud scoring"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_score_transaction_basic(self, mock_search, mock_gen):
        """Test basic transaction scoring"""
        detector = FraudDetector()

        # Mock the scoring methods
        detector._check_velocity = Mock(return_value=0.3)
        detector._check_network = Mock(return_value=0.2)
        detector._check_merchant = Mock(return_value=0.1)
        detector._check_behavior = Mock(return_value=0.2)

        score = detector.score_transaction(
            transaction_id="TX-001",
            account_id="ACC-123",
            amount=100.0,
            merchant="Test Merchant",
            description="Test transaction",
        )

        assert isinstance(score, FraudScore)
        assert score.transaction_id == "TX-001"
        assert 0.0 <= score.overall_score <= 1.0
        assert score.velocity_score == 0.3
        assert score.network_score == 0.2
        assert score.merchant_score == 0.1
        assert score.behavioral_score == 0.2

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_score_transaction_weighted_average(self, mock_search, mock_gen):
        """Test weighted average calculation"""
        detector = FraudDetector()

        detector._check_velocity = Mock(return_value=0.8)
        detector._check_network = Mock(return_value=0.6)
        detector._check_merchant = Mock(return_value=0.4)
        detector._check_behavior = Mock(return_value=0.2)

        score = detector.score_transaction(
            transaction_id="TX-001",
            account_id="ACC-123",
            amount=1000.0,
            merchant="Merchant",
            description="Description",
        )

        # Verify weighted calculation: 0.8*0.3 + 0.6*0.25 + 0.4*0.25 + 0.2*0.2
        expected = 0.8 * 0.3 + 0.6 * 0.25 + 0.4 * 0.25 + 0.2 * 0.2
        assert abs(score.overall_score - expected) < 0.01


class TestRiskLevelDetermination:
    """Test risk level and recommendation logic"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_critical_risk_level(self, mock_search, mock_gen):
        """Test critical risk level assignment"""
        detector = FraudDetector()

        # High scores across all checks
        detector._check_velocity = Mock(return_value=1.0)
        detector._check_network = Mock(return_value=1.0)
        detector._check_merchant = Mock(return_value=1.0)
        detector._check_behavior = Mock(return_value=1.0)

        score = detector.score_transaction("TX-001", "ACC-123", 5000.0, "Merchant", "Description")

        assert score.risk_level == "critical"
        assert score.recommendation == "block"

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_high_risk_level(self, mock_search, mock_gen):
        """Test high risk level assignment

        Weighted score calculation:
        0.9 * 0.3 + 0.75 * 0.25 + 0.75 * 0.25 + 0.75 * 0.2 = 0.27 + 0.1875 + 0.1875 + 0.15 = 0.795 >= 0.75 (HIGH)
        """
        detector = FraudDetector()

        detector._check_velocity = Mock(return_value=0.9)
        detector._check_network = Mock(return_value=0.75)
        detector._check_merchant = Mock(return_value=0.75)
        detector._check_behavior = Mock(return_value=0.75)

        score = detector.score_transaction("TX-001", "ACC-123", 1000.0, "Merchant", "Description")

        assert score.risk_level == "high"
        assert score.recommendation == "review"

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_medium_risk_level(self, mock_search, mock_gen):
        """Test medium risk level assignment"""
        detector = FraudDetector()

        detector._check_velocity = Mock(return_value=0.5)
        detector._check_network = Mock(return_value=0.5)
        detector._check_merchant = Mock(return_value=0.5)
        detector._check_behavior = Mock(return_value=0.5)

        score = detector.score_transaction("TX-001", "ACC-123", 500.0, "Merchant", "Description")

        assert score.risk_level == "medium"
        assert score.recommendation == "review"

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_low_risk_level(self, mock_search, mock_gen):
        """Test low risk level assignment"""
        detector = FraudDetector()

        detector._check_velocity = Mock(return_value=0.1)
        detector._check_network = Mock(return_value=0.1)
        detector._check_merchant = Mock(return_value=0.1)
        detector._check_behavior = Mock(return_value=0.1)

        score = detector.score_transaction("TX-001", "ACC-123", 50.0, "Merchant", "Description")

        assert score.risk_level == "low"
        assert score.recommendation == "approve"


class TestVelocityChecks:
    """Test transaction velocity checking"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_velocity_thresholds(self, mock_search, mock_gen):
        """Test velocity threshold constants"""
        detector = FraudDetector()

        assert detector.MAX_TRANSACTIONS_PER_HOUR == 10
        assert detector.MAX_AMOUNT_PER_HOUR == 5000.0
        assert detector.MAX_TRANSACTIONS_PER_DAY == 50
        assert detector.MAX_AMOUNT_PER_DAY == 20000.0

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_check_velocity_error_handling(self, mock_search, mock_gen):
        """Test velocity check error handling"""
        detector = FraudDetector()

        # Should return 0.0 on error, not raise exception
        score = detector._check_velocity("ACC-123", 100.0, datetime.now(timezone.utc))

        assert score == 0.0


class TestNetworkAnalysis:
    """Test fraud network analysis"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_check_network_error_handling(self, mock_search, mock_gen):
        """Test network check error handling"""
        detector = FraudDetector()

        # Should return 0.0 on error
        score = detector._check_network("ACC-123")

        assert score == 0.0


class TestMerchantFraudDetection:
    """Test merchant fraud detection"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_check_merchant_basic(self, mock_search, mock_gen):
        """Test basic merchant check"""
        detector = FraudDetector()

        score = detector._check_merchant("Test Merchant")

        # Current implementation returns low risk
        assert 0.0 <= score <= 1.0


class TestBehavioralAnalysis:
    """Test behavioral pattern analysis"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_check_behavior_basic(self, mock_search, mock_gen):
        """Test basic behavioral check"""
        detector = FraudDetector()

        score = detector._check_behavior("ACC-123", 100.0, "Merchant", "Description")

        assert 0.0 <= score <= 1.0


class TestAccountTakeoverDetection:
    """Test account takeover detection"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_detect_takeover_no_transactions(self, mock_search, mock_gen):
        """Test takeover detection with no transactions"""
        detector = FraudDetector()

        is_takeover, confidence, indicators = detector.detect_account_takeover("ACC-123", [])

        assert is_takeover is False
        assert confidence == 0.0
        assert len(indicators) == 0

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_detect_takeover_unusual_amount(self, mock_search, mock_gen):
        """Test takeover detection with unusual transaction amount"""
        detector = FraudDetector()

        transactions = [
            {"amount": 100.0, "timestamp": datetime.now(timezone.utc)},
            {"amount": 100.0, "timestamp": datetime.now(timezone.utc)},
            {"amount": 100.0, "timestamp": datetime.now(timezone.utc)},
            {"amount": 5000.0, "timestamp": datetime.now(timezone.utc)},  # Unusual
        ]

        is_takeover, confidence, indicators = detector.detect_account_takeover(
            "ACC-123", transactions
        )

        assert confidence > 0.0
        if is_takeover:
            assert len(indicators) > 0
            assert any("large" in ind.lower() for ind in indicators)

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_detect_takeover_normal_pattern(self, mock_search, mock_gen):
        """Test takeover detection with normal pattern"""
        detector = FraudDetector()

        transactions = [
            {"amount": 100.0, "timestamp": datetime.now(timezone.utc)},
            {"amount": 110.0, "timestamp": datetime.now(timezone.utc)},
            {"amount": 105.0, "timestamp": datetime.now(timezone.utc)},
        ]

        is_takeover, confidence, indicators = detector.detect_account_takeover(
            "ACC-123", transactions
        )

        assert is_takeover is False
        assert confidence <= 0.5


class TestSimilarCaseFinding:
    """Test similar fraud case finding"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_find_similar_cases_basic(self, mock_search, mock_gen):
        """Test finding similar fraud cases"""
        detector = FraudDetector()

        # Mock embedding generation
        mock_gen_instance = mock_gen.return_value
        mock_gen_instance.encode_for_search.return_value = [0.1] * 384

        # Mock search results
        mock_search_instance = mock_search.return_value
        mock_search_instance.search.return_value = [
            {"source": {"case_id": "CASE-001", "description": "Similar case 1"}},
            {"source": {"case_id": "CASE-002", "description": "Similar case 2"}},
        ]

        detector.generator = mock_gen_instance
        detector.search_client = mock_search_instance

        cases = detector.find_similar_fraud_cases(description="Test fraud", amount=1000.0, k=5)

        assert len(cases) == 2
        assert cases[0]["case_id"] == "CASE-001"

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_find_similar_cases_error_handling(self, mock_search, mock_gen):
        """Test error handling in similar case finding"""
        detector = FraudDetector()

        # Mock to raise exception
        mock_gen_instance = mock_gen.return_value
        mock_gen_instance.encode_for_search.side_effect = Exception("Test error")
        detector.generator = mock_gen_instance

        cases = detector.find_similar_fraud_cases("Test", 100.0)

        assert cases == []


class TestAlertGeneration:
    """Test fraud alert generation"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_generate_alert_below_threshold(self, mock_search, mock_gen):
        """Test no alert for low-risk transactions"""
        detector = FraudDetector()

        score = FraudScore(
            transaction_id="TX-001",
            overall_score=0.3,  # Below medium threshold
            velocity_score=0.2,
            network_score=0.2,
            merchant_score=0.2,
            behavioral_score=0.2,
            risk_level="low",
            recommendation="approve",
        )

        transaction_data = {
            "account_id": "ACC-123",
            "customer_id": "CUST-456",
            "customer_name": "John Doe",
            "amount": 100.0,
            "merchant": "Test Merchant",
            "description": "Test transaction",
        }

        alert = detector.generate_alert(score, transaction_data)

        assert alert is None

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_generate_alert_velocity_type(self, mock_search, mock_gen):
        """Test velocity alert type"""
        detector = FraudDetector()
        detector.find_similar_fraud_cases = Mock(return_value=[])

        score = FraudScore(
            transaction_id="TX-001",
            overall_score=0.8,
            velocity_score=0.9,  # High velocity
            network_score=0.3,
            merchant_score=0.2,
            behavioral_score=0.2,
            risk_level="high",
            recommendation="review",
        )

        transaction_data = {
            "account_id": "ACC-123",
            "customer_id": "CUST-456",
            "customer_name": "John Doe",
            "amount": 1000.0,
            "merchant": "Test Merchant",
            "description": "Test transaction",
        }

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert alert.alert_type == "velocity"
        assert alert.severity == "high"

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_generate_alert_network_type(self, mock_search, mock_gen):
        """Test network alert type"""
        detector = FraudDetector()
        detector.find_similar_fraud_cases = Mock(return_value=[])

        score = FraudScore(
            transaction_id="TX-001",
            overall_score=0.75,
            velocity_score=0.3,
            network_score=0.9,  # High network score
            merchant_score=0.2,
            behavioral_score=0.2,
            risk_level="high",
            recommendation="review",
        )

        transaction_data = {
            "account_id": "ACC-123",
            "customer_id": "CUST-456",
            "customer_name": "John Doe",
            "amount": 1000.0,
            "merchant": "Test Merchant",
            "description": "Test transaction",
        }

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert alert.alert_type == "network"

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_generate_alert_merchant_type(self, mock_search, mock_gen):
        """Test merchant alert type"""
        detector = FraudDetector()
        detector.find_similar_fraud_cases = Mock(return_value=[])

        score = FraudScore(
            transaction_id="TX-001",
            overall_score=0.75,
            velocity_score=0.3,
            network_score=0.3,
            merchant_score=0.9,  # High merchant score
            behavioral_score=0.2,
            risk_level="high",
            recommendation="review",
        )

        transaction_data = {
            "account_id": "ACC-123",
            "customer_id": "CUST-456",
            "customer_name": "John Doe",
            "amount": 1000.0,
            "merchant": "Suspicious Merchant",
            "description": "Test transaction",
        }

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert alert.alert_type == "merchant"

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_generate_alert_risk_factors(self, mock_search, mock_gen):
        """Test risk factors in alert"""
        detector = FraudDetector()
        detector.find_similar_fraud_cases = Mock(return_value=[])

        score = FraudScore(
            transaction_id="TX-001",
            overall_score=0.8,
            velocity_score=0.7,
            network_score=0.6,
            merchant_score=0.5,
            behavioral_score=0.4,
            risk_level="high",
            recommendation="review",
        )

        transaction_data = {
            "account_id": "ACC-123",
            "customer_id": "CUST-456",
            "customer_name": "John Doe",
            "amount": 1000.0,
            "merchant": "Test Merchant",
            "description": "Test transaction",
        }

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert len(alert.risk_factors) > 0
        # All scores > 0.5 should be in risk factors
        assert any("velocity" in rf.lower() for rf in alert.risk_factors)
        assert any("network" in rf.lower() for rf in alert.risk_factors)

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_generate_alert_with_similar_cases(self, mock_search, mock_gen):
        """Test alert includes similar cases"""
        detector = FraudDetector()

        similar_cases = [
            {"case_id": "CASE-001", "description": "Similar fraud 1"},
            {"case_id": "CASE-002", "description": "Similar fraud 2"},
        ]
        detector.find_similar_fraud_cases = Mock(return_value=similar_cases)

        score = FraudScore(
            transaction_id="TX-001",
            overall_score=0.8,
            velocity_score=0.7,
            network_score=0.6,
            merchant_score=0.5,
            behavioral_score=0.4,
            risk_level="high",
            recommendation="review",
        )

        transaction_data = {
            "account_id": "ACC-123",
            "customer_id": "CUST-456",
            "customer_name": "John Doe",
            "amount": 1000.0,
            "merchant": "Test Merchant",
            "description": "Test transaction",
        }

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert len(alert.similar_cases) == 2
        assert alert.similar_cases[0]["case_id"] == "CASE-001"


class TestAlertMetadata:
    """Test alert metadata and attributes"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_alert_id_format(self, mock_search, mock_gen):
        """Test alert ID format"""
        detector = FraudDetector()
        detector.find_similar_fraud_cases = Mock(return_value=[])

        score = FraudScore(
            transaction_id="TX-001",
            overall_score=0.8,
            velocity_score=0.7,
            network_score=0.6,
            merchant_score=0.5,
            behavioral_score=0.4,
            risk_level="high",
            recommendation="review",
        )

        transaction_data = {
            "account_id": "ACC-123",
            "customer_id": "CUST-456",
            "customer_name": "John Doe",
            "amount": 1000.0,
            "merchant": "Test Merchant",
            "description": "Test transaction",
        }

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert alert.alert_id.startswith("FRAUD_TX-001_")

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_alert_includes_transaction_data(self, mock_search, mock_gen):
        """Test alert includes all transaction data"""
        detector = FraudDetector()
        detector.find_similar_fraud_cases = Mock(return_value=[])

        score = FraudScore(
            transaction_id="TX-001",
            overall_score=0.8,
            velocity_score=0.7,
            network_score=0.6,
            merchant_score=0.5,
            behavioral_score=0.4,
            risk_level="high",
            recommendation="review",
        )

        transaction_data = {
            "account_id": "ACC-123",
            "customer_id": "CUST-456",
            "customer_name": "John Doe",
            "amount": 1000.0,
            "merchant": "Test Merchant",
            "description": "Test transaction",
        }

        alert = detector.generate_alert(score, transaction_data)

        assert alert is not None
        assert alert.transaction_id == "TX-001"
        assert alert.account_id == "ACC-123"
        assert alert.customer_id == "CUST-456"
        assert alert.customer_name == "John Doe"
        assert alert.amount == 1000.0
        assert alert.merchant == "Test Merchant"
        assert alert.fraud_score == 0.8


class TestThresholdConstants:
    """Test threshold constant values"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_risk_thresholds(self, mock_search, mock_gen):
        """Test risk threshold constants"""
        detector = FraudDetector()

        assert detector.CRITICAL_THRESHOLD == 0.9
        assert detector.HIGH_THRESHOLD == 0.75
        assert detector.MEDIUM_THRESHOLD == 0.5
        assert detector.LOW_THRESHOLD == 0.25

        # Verify ordering
        assert detector.CRITICAL_THRESHOLD > detector.HIGH_THRESHOLD
        assert detector.HIGH_THRESHOLD > detector.MEDIUM_THRESHOLD
        assert detector.MEDIUM_THRESHOLD > detector.LOW_THRESHOLD
