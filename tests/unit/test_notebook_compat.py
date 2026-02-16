"""
Tests for NotebookCompatMixin - the Jupyter notebook compatibility layer.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from banking.fraud.notebook_compat import NotebookCompatMixin


class MockFraudDetector(NotebookCompatMixin):
    """Mock FraudDetector that provides the base methods NotebookCompatMixin wraps."""

    HIGH_THRESHOLD = 0.8
    MAX_TRANSACTIONS_PER_HOUR = 10

    def __init__(self):
        self._trained = False
        self._training_mean = 0
        self._training_std = 1

    def score_transaction(self, transaction_id, account_id, amount, merchant, description, **kw):
        score = MagicMock()
        score.overall_score = min(1.0, amount / 50000)
        score.risk_level = "high" if score.overall_score >= 0.8 else "low"
        score.recommendation = "block" if score.overall_score >= 0.8 else "allow"
        score.velocity_score = 0.3
        score.network_score = 0.2
        score.merchant_score = 0.1
        score.behavioral_score = 0.15
        return score

    def _check_velocity(self, account_id, amount, timestamp):
        return 0.5

    def _check_behavior(self, account_id, amount, merchant, description):
        return 0.4


class TestTrainAnomalyModel:
    def test_train_with_transactions(self):
        detector = MockFraudDetector()
        txns = [{"amount": 100}, {"amount": 200}, {"amount": 300}]
        result = detector.train_anomaly_model(txns)
        assert result["training_samples"] == 3
        assert result["status"] == "trained"
        assert result["mean_amount"] == 200.0
        assert detector._trained is True

    def test_train_with_empty_transactions(self):
        detector = MockFraudDetector()
        result = detector.train_anomaly_model([])
        assert result["training_samples"] == 0
        assert result["mean_amount"] == 0


class TestDetectFraud:
    def test_detect_fraud_low_amount(self):
        detector = MockFraudDetector()
        result = detector.detect_fraud({"transaction_id": "t1", "amount": 100, "merchant": "Shop"})
        assert result["is_fraud"] is False
        assert "fraud_score" in result
        assert "velocity_score" in result

    def test_detect_fraud_high_amount(self):
        detector = MockFraudDetector()
        result = detector.detect_fraud({"transaction_id": "t2", "amount": 50000, "merchant": "X"})
        assert result["is_fraud"] is True

    def test_detect_fraud_with_account_id(self):
        detector = MockFraudDetector()
        result = detector.detect_fraud({"amount": 100}, account_id="acc-123")
        assert result["is_fraud"] is False


class TestCheckVelocity:
    def test_check_velocity_with_transactions(self):
        detector = MockFraudDetector()
        txns = [{"amount": 100}] * 15
        result = detector.check_velocity("acc-1", transactions=txns)
        assert result["is_velocity_anomaly"] is True
        assert result["transaction_count"] == 15

    def test_check_velocity_without_transactions(self):
        detector = MockFraudDetector()
        result = detector.check_velocity("acc-1")
        assert "velocity_score" in result
        assert result["transaction_count"] == 0

    def test_check_velocity_low_count(self):
        detector = MockFraudDetector()
        txns = [{"amount": 100}] * 2
        result = detector.check_velocity("acc-1", transactions=txns)
        assert result["is_velocity_anomaly"] is False


class TestDetectGeographicAnomaly:
    def test_normal_transaction(self):
        detector = MockFraudDetector()
        result = detector.detect_geographic_anomaly({"merchant": "Local Shop", "location": "NYC"})
        assert result["is_geographic_anomaly"] is False
        assert result["geographic_score"] == 0.3

    def test_overseas_transaction(self):
        detector = MockFraudDetector()
        result = detector.detect_geographic_anomaly({"merchant": "Overseas Trading Co"})
        assert result["is_geographic_anomaly"] is True
        assert result["geographic_score"] == 0.7

    def test_international_transaction(self):
        detector = MockFraudDetector()
        result = detector.detect_geographic_anomaly({"merchant": "International Wires"})
        assert result["is_geographic_anomaly"] is True

    def test_foreign_atm(self):
        detector = MockFraudDetector()
        result = detector.detect_geographic_anomaly(
            {"merchant": "ATM Withdrawal", "location": "foreign city"}
        )
        assert result["is_geographic_anomaly"] is True
        assert result["distance_km"] == 8000


class TestAnalyzeBehavioralPattern:
    def test_with_transaction(self):
        detector = MockFraudDetector()
        result = detector.analyze_behavioral_pattern(
            "acc-1", transaction={"amount": 500, "merchant": "Shop"}
        )
        assert "behavioral_score" in result
        assert "is_behavioral_anomaly" in result

    def test_with_transactions_list(self):
        detector = MockFraudDetector()
        result = detector.analyze_behavioral_pattern(
            "acc-1", transactions=[{"amount": 300, "merchant": "Store"}]
        )
        assert result["account_id"] == "acc-1"

    def test_with_historical_transactions(self):
        detector = MockFraudDetector()
        result = detector.analyze_behavioral_pattern(
            "acc-1", historical_transactions=[{"amount": 200}]
        )
        assert result["account_id"] == "acc-1"

    def test_with_no_data(self):
        detector = MockFraudDetector()
        result = detector.analyze_behavioral_pattern("acc-1")
        assert result["account_id"] == "acc-1"

    def test_with_trained_model(self):
        detector = MockFraudDetector()
        detector.train_anomaly_model([{"amount": 100}, {"amount": 200}])
        result = detector.analyze_behavioral_pattern(
            "acc-1", transaction={"amount": 500}
        )
        assert result["typical_amount"] == 150.0


class TestCalculateFraudScore:
    def test_calculate_fraud_score(self):
        detector = MockFraudDetector()
        result = detector.calculate_fraud_score({"amount": 100, "merchant": "Shop"})
        assert "fraud_score" in result
        assert "is_fraud" in result


class TestEvaluateModel:
    def test_evaluate_with_test_data(self):
        detector = MockFraudDetector()
        test_data = [
            {"amount": 100, "is_fraud": False},
            {"amount": 50000, "is_fraud": True},
            {"amount": 200, "suspicious_pattern": False},
        ]
        result = detector.evaluate_model(test_data)
        assert result["total_samples"] == 3
        assert "precision" in result
        assert "recall" in result
        assert "f1_score" in result
        assert "accuracy" in result

    def test_evaluate_empty_data(self):
        detector = MockFraudDetector()
        result = detector.evaluate_model([])
        assert result == {"error": "No predictions made"}
