"""Tests for banking.fraud.models module."""

from banking.fraud.models import HIGH_RISK_MERCHANTS, FraudAlert, FraudScore


class TestFraudAlert:
    def test_creation(self):
        alert = FraudAlert(
            alert_id="A-001",
            alert_type="velocity",
            severity="high",
            transaction_id="T-001",
            account_id="ACC-001",
            customer_id="C-001",
            customer_name="Test",
            amount=1000.0,
            merchant="crypto",
            fraud_score=0.95,
            risk_factors=["rapid_tx"],
            similar_cases=[],
            timestamp="2026-01-01T00:00:00Z",
            metadata={},
        )
        assert alert.alert_id == "A-001"
        assert alert.fraud_score == 0.95
        assert alert.severity == "high"


class TestFraudScore:
    def test_creation(self):
        score = FraudScore(
            transaction_id="T-001",
            overall_score=0.8,
            velocity_score=0.9,
            network_score=0.7,
            merchant_score=0.6,
            behavioral_score=0.5,
            risk_level="high",
            recommendation="block",
        )
        assert score.overall_score == 0.8
        assert score.risk_level == "high"


class TestHighRiskMerchants:
    def test_has_entries(self):
        assert len(HIGH_RISK_MERCHANTS) > 0

    def test_known_merchants(self):
        assert "crypto" in HIGH_RISK_MERCHANTS
        assert "casino" in HIGH_RISK_MERCHANTS
        assert HIGH_RISK_MERCHANTS["crypto"] == 0.7

    def test_values_are_floats(self):
        for name, score in HIGH_RISK_MERCHANTS.items():
            assert isinstance(score, float)
            assert 0 <= score <= 1
