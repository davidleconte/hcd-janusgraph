"""Tests for banking.fraud.models and notebook_compat modules."""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from banking.fraud.models import FraudAlert, FraudScore, HIGH_RISK_MERCHANTS


class TestFraudAlert:
    def test_creation(self):
        alert = FraudAlert(
            alert_id="FA-001", alert_type="velocity", severity="high",
            transaction_id="tx-1", account_id="a-1", customer_id="c-1",
            customer_name="John", amount=5000.0, merchant="crypto exchange",
            fraud_score=0.95, risk_factors=["high_velocity", "crypto"],
            similar_cases=[], timestamp="2026-01-15T10:00:00Z", metadata={},
        )
        assert alert.alert_id == "FA-001"
        assert alert.fraud_score == 0.95

    def test_all_fields(self):
        alert = FraudAlert(
            alert_id="FA-002", alert_type="network", severity="critical",
            transaction_id="tx-2", account_id="a-2", customer_id="c-2",
            customer_name="Jane", amount=50000.0, merchant="wire transfer",
            fraud_score=0.99, risk_factors=["fraud_ring", "large_amount"],
            similar_cases=[{"case_id": "C-1", "similarity": 0.9}],
            timestamp="2026-01-15T11:00:00Z",
            metadata={"ip": "192.168.1.1", "device": "unknown"},
        )
        assert len(alert.risk_factors) == 2
        assert len(alert.similar_cases) == 1


class TestFraudScore:
    def test_creation(self):
        score = FraudScore(
            transaction_id="tx-1", overall_score=0.85,
            velocity_score=0.9, network_score=0.7,
            merchant_score=0.8, behavioral_score=0.6,
            risk_level="high", recommendation="block",
        )
        assert score.overall_score == 0.85
        assert score.risk_level == "high"

    def test_low_risk(self):
        score = FraudScore(
            transaction_id="tx-2", overall_score=0.1,
            velocity_score=0.05, network_score=0.1,
            merchant_score=0.15, behavioral_score=0.1,
            risk_level="low", recommendation="allow",
        )
        assert score.risk_level == "low"


class TestHighRiskMerchants:
    def test_contains_crypto(self):
        assert "crypto" in HIGH_RISK_MERCHANTS
        assert HIGH_RISK_MERCHANTS["crypto"] == 0.7

    def test_contains_gambling(self):
        assert "casino" in HIGH_RISK_MERCHANTS
        assert "gambling" in HIGH_RISK_MERCHANTS

    def test_all_values_between_0_and_1(self):
        for merchant, score in HIGH_RISK_MERCHANTS.items():
            assert 0.0 <= score <= 1.0, f"{merchant} score {score} out of range"


class TestNotebookCompatMixin:
    def test_train_anomaly_model(self):
        from banking.fraud.notebook_compat import NotebookCompatMixin
        mixin = NotebookCompatMixin()
        transactions = [
            {"amount": 100}, {"amount": 200}, {"amount": 300},
            {"amount": 150}, {"amount": 250},
        ]
        result = mixin.train_anomaly_model(transactions)
        assert result["training_samples"] == 5
        assert result["status"] == "trained"
        assert result["mean_amount"] == 200.0
        assert mixin._trained is True

    def test_train_anomaly_model_empty(self):
        from banking.fraud.notebook_compat import NotebookCompatMixin
        mixin = NotebookCompatMixin()
        result = mixin.train_anomaly_model([])
        assert result["training_samples"] == 0
        assert result["mean_amount"] == 0
