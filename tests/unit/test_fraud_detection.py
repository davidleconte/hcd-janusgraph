#!/usr/bin/env python3
"""Tests for Fraud Detection module."""

import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from banking.fraud.fraud_detection import FraudAlert, FraudScore, FraudDetector


class TestFraudAlert:
    """Test FraudAlert dataclass."""

    def test_fraud_alert_creation(self):
        alert = FraudAlert(
            alert_id="alert-123",
            alert_type="velocity",
            severity="high",
            transaction_id="txn-456",
            account_id="acc-789",
            customer_id="cust-012",
            customer_name="John Doe",
            amount=5000.0,
            merchant="Test Merchant",
            fraud_score=0.85,
            risk_factors=["high_velocity", "new_merchant"],
            similar_cases=[],
            timestamp="2026-02-06T12:00:00Z",
            metadata={}
        )
        assert alert.alert_id == "alert-123"
        assert alert.severity == "high"
        assert alert.fraud_score == 0.85

    def test_fraud_alert_types(self):
        for alert_type in ["velocity", "network", "merchant", "account_takeover"]:
            alert = FraudAlert(
                alert_id="test",
                alert_type=alert_type,
                severity="medium",
                transaction_id="txn",
                account_id="acc",
                customer_id="cust",
                customer_name="Test",
                amount=100.0,
                merchant="Test",
                fraud_score=0.5,
                risk_factors=[],
                similar_cases=[],
                timestamp="2026-01-01",
                metadata={}
            )
            assert alert.alert_type == alert_type


class TestFraudScore:
    """Test FraudScore dataclass."""

    def test_fraud_score_creation(self):
        score = FraudScore(
            transaction_id="txn-123",
            overall_score=0.75,
            velocity_score=0.8,
            network_score=0.6,
            merchant_score=0.7,
            behavioral_score=0.9,
            risk_level="high",
            recommendation="review"
        )
        assert score.overall_score == 0.75
        assert score.risk_level == "high"
        assert score.recommendation == "review"

    def test_score_recommendations(self):
        for rec in ["block", "review", "approve"]:
            score = FraudScore(
                transaction_id="txn",
                overall_score=0.5,
                velocity_score=0.5,
                network_score=0.5,
                merchant_score=0.5,
                behavioral_score=0.5,
                risk_level="medium",
                recommendation=rec
            )
            assert score.recommendation == rec


class TestFraudDetector:
    """Test FraudDetector class."""

    def test_detector_thresholds(self):
        assert FraudDetector.CRITICAL_THRESHOLD == 0.9
        assert FraudDetector.HIGH_THRESHOLD == 0.75
        assert FraudDetector.MEDIUM_THRESHOLD == 0.5
        assert FraudDetector.LOW_THRESHOLD == 0.25

    def test_velocity_limits(self):
        assert FraudDetector.MAX_TRANSACTIONS_PER_HOUR == 10
        assert FraudDetector.MAX_AMOUNT_PER_HOUR == 5000.0
        assert FraudDetector.MAX_TRANSACTIONS_PER_DAY == 50
        assert FraudDetector.MAX_AMOUNT_PER_DAY == 20000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
