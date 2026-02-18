"""
Unit tests for Fraud Detection Models

Test Coverage Target: 60%+
Total Tests: 15+

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-11
"""

from banking.fraud.models import HIGH_RISK_MERCHANTS, FraudAlert, FraudScore


class TestFraudAlert:
    """Test FraudAlert dataclass (6 tests)"""

    def test_fraud_alert_creation(self):
        """Test creating fraud alert with all fields"""
        alert = FraudAlert(
            alert_id="alert-123",
            alert_type="velocity",
            severity="high",
            transaction_id="txn-456",
            account_id="acc-789",
            customer_id="cust-001",
            customer_name="John Doe",
            amount=5000.0,
            merchant="Suspicious Store",
            fraud_score=0.85,
            risk_factors=["rapid_transactions", "high_amount"],
            similar_cases=[{"case_id": "case-1", "similarity": 0.9}],
            timestamp="2026-02-11T20:00:00Z",
            metadata={"ip": "192.168.1.1", "device": "mobile"},
        )

        assert alert.alert_id == "alert-123"
        assert alert.alert_type == "velocity"
        assert alert.severity == "high"
        assert alert.fraud_score == 0.85
        assert len(alert.risk_factors) == 2

    def test_fraud_alert_high_severity(self):
        """Test high severity fraud alert"""
        alert = FraudAlert(
            alert_id="alert-456",
            alert_type="account_takeover",
            severity="critical",
            transaction_id="txn-789",
            account_id="acc-123",
            customer_id="cust-002",
            customer_name="Jane Smith",
            amount=10000.0,
            merchant="Crypto Exchange",
            fraud_score=0.95,
            risk_factors=["account_takeover", "unusual_location", "high_amount"],
            similar_cases=[],
            timestamp="2026-02-11T21:00:00Z",
            metadata={},
        )

        assert alert.severity == "critical"
        assert alert.fraud_score > 0.9
        assert "account_takeover" in alert.risk_factors

    def test_fraud_alert_with_similar_cases(self):
        """Test fraud alert with similar historical cases"""
        similar_cases = [
            {"case_id": "case-1", "similarity": 0.92, "outcome": "confirmed_fraud"},
            {"case_id": "case-2", "similarity": 0.88, "outcome": "confirmed_fraud"},
        ]

        alert = FraudAlert(
            alert_id="alert-789",
            alert_type="merchant_fraud",
            severity="high",
            transaction_id="txn-111",
            account_id="acc-222",
            customer_id="cust-003",
            customer_name="Bob Johnson",
            amount=3000.0,
            merchant="Compromised Merchant",
            fraud_score=0.80,
            risk_factors=["merchant_fraud"],
            similar_cases=similar_cases,
            timestamp="2026-02-11T22:00:00Z",
            metadata={"merchant_id": "merch-999"},
        )

        assert len(alert.similar_cases) == 2
        assert alert.similar_cases[0]["similarity"] > 0.9

    def test_fraud_alert_empty_risk_factors(self):
        """Test fraud alert with no risk factors"""
        alert = FraudAlert(
            alert_id="alert-000",
            alert_type="behavioral",
            severity="low",
            transaction_id="txn-000",
            account_id="acc-000",
            customer_id="cust-000",
            customer_name="Test User",
            amount=100.0,
            merchant="Normal Store",
            fraud_score=0.15,
            risk_factors=[],
            similar_cases=[],
            timestamp="2026-02-11T23:00:00Z",
            metadata={},
        )

        assert len(alert.risk_factors) == 0
        assert alert.fraud_score < 0.25

    def test_fraud_alert_dataclass_equality(self):
        """Test dataclass equality"""
        alert1 = FraudAlert(
            "a1",
            "velocity",
            "high",
            "t1",
            "acc1",
            "c1",
            "John",
            1000.0,
            "Store",
            0.8,
            [],
            [],
            "2026-02-11",
            {},
        )
        alert2 = FraudAlert(
            "a1",
            "velocity",
            "high",
            "t1",
            "acc1",
            "c1",
            "John",
            1000.0,
            "Store",
            0.8,
            [],
            [],
            "2026-02-11",
            {},
        )
        assert alert1 == alert2

    def test_fraud_alert_metadata_types(self):
        """Test various metadata types"""
        alert = FraudAlert(
            alert_id="alert-meta",
            alert_type="network",
            severity="medium",
            transaction_id="txn-meta",
            account_id="acc-meta",
            customer_id="cust-meta",
            customer_name="Meta User",
            amount=2500.0,
            merchant="Test Merchant",
            fraud_score=0.60,
            risk_factors=["network_anomaly"],
            similar_cases=[],
            timestamp="2026-02-11T23:30:00Z",
            metadata={
                "ip": "10.0.0.1",
                "device": "desktop",
                "location": {"lat": 40.7128, "lon": -74.0060},
                "user_agent": "Mozilla/5.0",
                "session_id": "sess-123",
                "attempts": 3,
            },
        )

        assert isinstance(alert.metadata["ip"], str)
        assert isinstance(alert.metadata["location"], dict)
        assert isinstance(alert.metadata["attempts"], int)


class TestFraudScore:
    """Test FraudScore dataclass (5 tests)"""

    def test_fraud_score_creation(self):
        """Test creating fraud score"""
        score = FraudScore(
            transaction_id="txn-123",
            overall_score=0.75,
            velocity_score=0.80,
            network_score=0.60,
            merchant_score=0.70,
            behavioral_score=0.85,
            risk_level="high",
            recommendation="block",
        )

        assert score.transaction_id == "txn-123"
        assert score.overall_score == 0.75
        assert score.risk_level == "high"
        assert score.recommendation == "block"

    def test_fraud_score_low_risk(self):
        """Test low risk fraud score"""
        score = FraudScore(
            transaction_id="txn-456",
            overall_score=0.15,
            velocity_score=0.10,
            network_score=0.05,
            merchant_score=0.20,
            behavioral_score=0.25,
            risk_level="low",
            recommendation="approve",
        )

        assert score.overall_score < 0.25
        assert score.risk_level == "low"
        assert score.recommendation == "approve"

    def test_fraud_score_medium_risk(self):
        """Test medium risk fraud score"""
        score = FraudScore(
            transaction_id="txn-789",
            overall_score=0.55,
            velocity_score=0.50,
            network_score=0.45,
            merchant_score=0.60,
            behavioral_score=0.65,
            risk_level="medium",
            recommendation="review",
        )

        assert 0.25 < score.overall_score < 0.75
        assert score.risk_level == "medium"
        assert score.recommendation == "review"

    def test_fraud_score_critical_risk(self):
        """Test critical risk fraud score"""
        score = FraudScore(
            transaction_id="txn-critical",
            overall_score=0.95,
            velocity_score=0.90,
            network_score=0.95,
            merchant_score=0.98,
            behavioral_score=0.92,
            risk_level="critical",
            recommendation="block_and_alert",
        )

        assert score.overall_score > 0.9
        assert score.risk_level == "critical"
        assert "block" in score.recommendation

    def test_fraud_score_component_scores(self):
        """Test individual component scores"""
        score = FraudScore(
            transaction_id="txn-components",
            overall_score=0.65,
            velocity_score=0.80,  # High velocity
            network_score=0.30,  # Low network risk
            merchant_score=0.70,  # Medium-high merchant risk
            behavioral_score=0.50,  # Medium behavioral risk
            risk_level="medium",
            recommendation="review",
        )

        # Verify component scores are independent
        assert score.velocity_score > score.network_score
        assert score.merchant_score > score.behavioral_score
        assert all(
            0 <= s <= 1
            for s in [
                score.velocity_score,
                score.network_score,
                score.merchant_score,
                score.behavioral_score,
            ]
        )


class TestHighRiskMerchants:
    """Test HIGH_RISK_MERCHANTS dictionary (4 tests)"""

    def test_high_risk_merchants_exists(self):
        """Test HIGH_RISK_MERCHANTS dictionary exists"""
        assert HIGH_RISK_MERCHANTS is not None
        assert isinstance(HIGH_RISK_MERCHANTS, dict)
        assert len(HIGH_RISK_MERCHANTS) > 0

    def test_high_risk_merchants_crypto(self):
        """Test crypto-related merchants have high risk"""
        assert "crypto" in HIGH_RISK_MERCHANTS
        assert "bitcoin" in HIGH_RISK_MERCHANTS
        assert HIGH_RISK_MERCHANTS["crypto"] >= 0.5
        assert HIGH_RISK_MERCHANTS["bitcoin"] >= 0.5

    def test_high_risk_merchants_gambling(self):
        """Test gambling-related merchants have high risk"""
        assert "casino" in HIGH_RISK_MERCHANTS
        assert "gambling" in HIGH_RISK_MERCHANTS
        assert HIGH_RISK_MERCHANTS["casino"] >= 0.5
        assert HIGH_RISK_MERCHANTS["gambling"] >= 0.5

    def test_high_risk_merchants_score_range(self):
        """Test all merchant risk scores are in valid range"""
        for merchant, score in HIGH_RISK_MERCHANTS.items():
            assert 0.0 <= score <= 1.0, f"{merchant} score {score} out of range"
            assert isinstance(score, float), f"{merchant} score must be float"


# Total: 6 + 5 + 4 = 15 tests for models

# Made with Bob
