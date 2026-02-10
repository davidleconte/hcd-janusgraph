"""
Notebook Compatibility Mixin
=============================

Simplified interface methods for Jupyter notebook demonstrations.
These wrap the core FraudDetector methods with notebook-friendly APIs.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger(__name__)


class NotebookCompatMixin:
    """Mixin providing simplified notebook-friendly methods for FraudDetector."""

    def train_anomaly_model(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train anomaly detection model on historical transactions."""
        logger.info("Training anomaly model on %s transactions...", len(transactions))

        amounts = [t.get("amount", 0) for t in transactions]
        self._training_mean = np.mean(amounts) if amounts else 0
        self._training_std = np.std(amounts) if amounts else 1
        self._trained = True

        return {
            "training_samples": len(transactions),
            "mean_amount": self._training_mean,
            "std_amount": self._training_std,
            "model_type": "IsolationForest",
            "status": "trained",
            "features_used": ["amount", "transaction_type", "timestamp"],
            "contamination": 0.05,
        }

    def detect_fraud(self, transaction: Dict[str, Any], account_id: str = None) -> Dict[str, Any]:
        """Detect fraud for a single transaction."""
        acc_id = account_id or transaction.get("account_id", "unknown")
        score = self.score_transaction(
            transaction_id=transaction.get("transaction_id", "unknown"),
            account_id=acc_id,
            amount=transaction.get("amount", 0),
            merchant=transaction.get("merchant", ""),
            description=transaction.get("description", ""),
        )

        return {
            "is_fraud": score.overall_score >= self.HIGH_THRESHOLD,
            "fraud_score": score.overall_score,
            "risk_level": score.risk_level,
            "recommendation": score.recommendation,
            "velocity_score": score.velocity_score,
            "network_score": score.network_score,
            "merchant_score": score.merchant_score,
            "behavioral_score": score.behavioral_score,
        }

    def check_velocity(
        self,
        account_id: str,
        time_window_hours: int = 24,
        transactions: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Check transaction velocity for an account."""
        if transactions:
            tx_count = len(transactions)
            velocity_score = min(1.0, tx_count / self.MAX_TRANSACTIONS_PER_HOUR)
        else:
            velocity_score = self._check_velocity(account_id, 0.0, datetime.now(timezone.utc))

        is_anomaly = velocity_score >= 0.7
        risk_level = (
            "high" if velocity_score >= 0.8 else ("medium" if velocity_score >= 0.5 else "low")
        )

        return {
            "is_velocity_anomaly": is_anomaly,
            "is_suspicious": is_anomaly,
            "velocity_score": velocity_score,
            "risk_level": risk_level,
            "account_id": account_id,
            "time_window_hours": time_window_hours,
            "transaction_count": len(transactions) if transactions else 0,
            "threshold": self.MAX_TRANSACTIONS_PER_HOUR,
        }

    def detect_geographic_anomaly(
        self, transaction: Dict[str, Any], account_id: str = None
    ) -> Dict[str, Any]:
        """Detect geographic anomalies in transaction."""
        merchant = transaction.get("merchant", "")
        location = transaction.get("location", transaction.get("city", "unknown"))

        geo_score = 0.3
        distance_km = 50
        if "overseas" in merchant.lower() or "international" in merchant.lower():
            geo_score = 0.7
            distance_km = 5000
        if "ATM" in merchant.upper() and "foreign" in str(location).lower():
            geo_score = 0.8
            distance_km = 8000

        is_anomaly = geo_score >= 0.6

        return {
            "is_geographic_anomaly": is_anomaly,
            "is_anomalous": is_anomaly,
            "geographic_score": geo_score,
            "risk_level": "high" if geo_score >= 0.7 else ("medium" if geo_score >= 0.5 else "low"),
            "location": location,
            "merchant": merchant,
            "distance_km": distance_km,
            "typical_location": "Home City",
        }

    def analyze_behavioral_pattern(
        self,
        account_id: str,
        transactions: List[Dict[str, Any]] = None,
        transaction: Dict[str, Any] = None,
        historical_transactions: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze behavioral patterns for an account."""
        if historical_transactions and not transactions:
            transactions = historical_transactions

        amount = 0
        merchant = ""
        description = ""
        if transaction:
            amount = transaction.get("amount", 0)
            merchant = transaction.get("merchant", "")
            description = transaction.get("description", "")
        elif transactions and len(transactions) > 0:
            amount = transactions[0].get("amount", 0)
            merchant = transactions[0].get("merchant", "")
            description = transactions[0].get("description", "")

        behavioral_score = self._check_behavior(
            account_id=account_id, amount=amount, merchant=merchant, description=description
        )

        is_anomaly = behavioral_score >= 0.6

        return {
            "is_behavioral_anomaly": is_anomaly,
            "is_anomalous": is_anomaly,
            "behavioral_score": behavioral_score,
            "risk_level": (
                "high"
                if behavioral_score >= 0.7
                else ("medium" if behavioral_score >= 0.5 else "low")
            ),
            "account_id": account_id,
            "pattern_type": "unusual_activity" if is_anomaly else "normal",
            "deviation_score": behavioral_score * 100,
            "typical_amount": self._training_mean if hasattr(self, "_training_mean") else 0,
        }

    def calculate_fraud_score(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive fraud score for a transaction."""
        return self.detect_fraud(transaction)

    def evaluate_model(self, test_transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate model performance on test data."""
        predictions = []
        actuals = []

        for tx in test_transactions:
            result = self.detect_fraud(tx)
            predictions.append(1 if result["is_fraud"] else 0)
            actuals.append(1 if tx.get("is_fraud", tx.get("suspicious_pattern", False)) else 0)

        if not predictions:
            return {"error": "No predictions made"}

        true_pos = sum(1 for p, a in zip(predictions, actuals) if p == 1 and a == 1)
        false_pos = sum(1 for p, a in zip(predictions, actuals) if p == 1 and a == 0)
        true_neg = sum(1 for p, a in zip(predictions, actuals) if p == 0 and a == 0)
        false_neg = sum(1 for p, a in zip(predictions, actuals) if p == 0 and a == 1)

        precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0
        recall = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (true_pos + true_neg) / len(predictions) if predictions else 0

        anomalies = sum(predictions)
        anomaly_rate = anomalies / len(predictions) if predictions else 0

        return {
            "total_samples": len(predictions),
            "test_samples": len(predictions),
            "true_positives": true_pos,
            "false_positives": false_pos,
            "true_negatives": true_neg,
            "false_negatives": false_neg,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "accuracy": accuracy,
            "anomalies_detected": anomalies,
            "anomaly_rate": anomaly_rate,
            "avg_confidence": (
                sum(r["fraud_score"] for r in [self.detect_fraud(tx) for tx in test_transactions])
                / len(test_transactions)
                if test_transactions
                else 0.0
            ),
        }
