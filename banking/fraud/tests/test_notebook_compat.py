"""
Tests for NotebookCompatMixin to increase coverage from 14% to 80%+.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from banking.fraud.fraud_detection import FraudDetector


@pytest.fixture
def detector():
    with patch("banking.fraud.fraud_detection.VectorSearchClient"), \
         patch("banking.fraud.fraud_detection.EmbeddingGenerator"):
        return FraudDetector()


class TestTrainAnomalyModel:
    def test_train_basic(self, detector):
        txs = [{"amount": 100}, {"amount": 200}, {"amount": 300}]
        result = detector.train_anomaly_model(txs)
        assert result["training_samples"] == 3
        assert result["status"] == "trained"
        assert result["mean_amount"] == 200.0
        assert result["model_type"] == "IsolationForest"

    def test_train_empty(self, detector):
        result = detector.train_anomaly_model([])
        assert result["training_samples"] == 0
        assert result["mean_amount"] == 0

    def test_train_single(self, detector):
        result = detector.train_anomaly_model([{"amount": 500}])
        assert result["training_samples"] == 1
        assert result["std_amount"] == 0.0


class TestDetectFraud:
    def test_detect_normal_transaction(self, detector):
        tx = {"transaction_id": "tx-1", "account_id": "acc-1", "amount": 50, "merchant": "Store"}
        result = detector.detect_fraud(tx)
        assert "is_fraud" in result
        assert "fraud_score" in result
        assert "risk_level" in result
        assert isinstance(result["fraud_score"], float)

    def test_detect_with_explicit_account(self, detector):
        tx = {"transaction_id": "tx-2", "amount": 100}
        result = detector.detect_fraud(tx, account_id="acc-99")
        assert "is_fraud" in result

    def test_detect_missing_fields(self, detector):
        result = detector.detect_fraud({})
        assert "is_fraud" in result


class TestCheckVelocity:
    def test_velocity_with_transactions(self, detector):
        txs = [{"amount": 100} for _ in range(5)]
        result = detector.check_velocity("acc-1", transactions=txs)
        assert "is_velocity_anomaly" in result
        assert "velocity_score" in result
        assert result["transaction_count"] == 5
        assert result["account_id"] == "acc-1"

    def test_velocity_high(self, detector):
        txs = [{"amount": 100} for _ in range(100)]
        result = detector.check_velocity("acc-1", transactions=txs)
        assert result["velocity_score"] >= 0.7
        assert result["is_suspicious"] is True

    def test_velocity_without_transactions(self, detector):
        result = detector.check_velocity("acc-1")
        assert "velocity_score" in result
        assert result["transaction_count"] == 0


class TestDetectGeographicAnomaly:
    def test_normal_transaction(self, detector):
        tx = {"merchant": "Local Store", "location": "New York"}
        result = detector.detect_geographic_anomaly(tx)
        assert result["is_geographic_anomaly"] is False
        assert result["geographic_score"] == 0.3

    def test_overseas_merchant(self, detector):
        tx = {"merchant": "Overseas Trading Co", "location": "London"}
        result = detector.detect_geographic_anomaly(tx)
        assert result["is_geographic_anomaly"] is True
        assert result["geographic_score"] == 0.7
        assert result["distance_km"] == 5000

    def test_international_merchant(self, detector):
        tx = {"merchant": "International Wire", "city": "Tokyo"}
        result = detector.detect_geographic_anomaly(tx)
        assert result["is_geographic_anomaly"] is True

    def test_foreign_atm(self, detector):
        tx = {"merchant": "ATM Withdrawal", "location": "foreign city"}
        result = detector.detect_geographic_anomaly(tx)
        assert result["geographic_score"] == 0.8
        assert result["distance_km"] == 8000

    def test_with_account_id(self, detector):
        tx = {"merchant": "Store", "amount": 50}
        result = detector.detect_geographic_anomaly(tx, account_id="acc-1")
        assert "is_geographic_anomaly" in result


class TestAnalyzeBehavioralPattern:
    def test_with_transaction(self, detector):
        tx = {"amount": 5000, "merchant": "Luxury Store", "description": "Purchase"}
        result = detector.analyze_behavioral_pattern("acc-1", transaction=tx)
        assert "is_behavioral_anomaly" in result
        assert "behavioral_score" in result
        assert result["account_id"] == "acc-1"

    def test_with_transactions_list(self, detector):
        txs = [{"amount": 100, "merchant": "Store", "description": "Coffee"}]
        result = detector.analyze_behavioral_pattern("acc-1", transactions=txs)
        assert "behavioral_score" in result

    def test_with_historical_transactions(self, detector):
        hist = [{"amount": 200, "merchant": "Shop", "description": "Groceries"}]
        result = detector.analyze_behavioral_pattern("acc-1", historical_transactions=hist)
        assert "behavioral_score" in result

    def test_empty(self, detector):
        result = detector.analyze_behavioral_pattern("acc-1")
        assert "behavioral_score" in result


class TestCalculateFraudScore:
    def test_basic(self, detector):
        tx = {"transaction_id": "tx-1", "amount": 100, "merchant": "Store"}
        result = detector.calculate_fraud_score(tx)
        assert "is_fraud" in result
        assert "fraud_score" in result


class TestEvaluateModel:
    def test_evaluate_basic(self, detector):
        detector._get_traversal = Mock(side_effect=Exception("no connection"))
        txs = [
            {"transaction_id": "tx-1", "amount": 100, "is_fraud": False},
            {"transaction_id": "tx-2", "amount": 50000, "is_fraud": True},
        ]
        result = detector.evaluate_model(txs)
        assert "precision" in result
        assert "recall" in result
        assert "f1_score" in result
        assert "accuracy" in result
        assert result["total_samples"] == 2

    def test_evaluate_empty(self, detector):
        result = detector.evaluate_model([])
        assert result == {"error": "No predictions made"}

    def test_evaluate_all_normal(self, detector):
        detector._get_traversal = Mock(side_effect=Exception("no connection"))
        txs = [{"transaction_id": f"tx-{i}", "amount": 50, "is_fraud": False} for i in range(5)]
        result = detector.evaluate_model(txs)
        assert result["true_negatives"] >= 0
        assert result["anomaly_rate"] >= 0.0

    def test_evaluate_with_suspicious_pattern(self, detector):
        detector._get_traversal = Mock(side_effect=Exception("no connection"))
        txs = [{"transaction_id": "tx-1", "amount": 100, "suspicious_pattern": True}]
        result = detector.evaluate_model(txs)
        assert result["total_samples"] == 1
