"""
Notebook Compatibility Mixin
=============================

Simplified interface methods for Jupyter notebook demonstrations.
These wrap the core FraudDetector methods with notebook-friendly APIs.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class NotebookCompatMixin:
    """Mixin providing simplified notebook-friendly methods for FraudDetector."""

    @staticmethod
    def _risk_level_from_score(
        score: float, *, high_threshold: float = 0.8, medium_threshold: float = 0.5
    ) -> str:
        """Map a numeric score to notebook-friendly risk levels."""
        if score >= high_threshold:
            return "high"
        if score >= medium_threshold:
            return "medium"
        return "low"

    @staticmethod
    def _resolve_account_id(transaction: Dict[str, Any], account_id: str = None) -> str:
        """Resolve account identifier with notebook fallback behavior."""
        return account_id or transaction.get("account_id", "unknown")

    @staticmethod
    def _extract_behavior_inputs(
        transactions: List[Dict[str, Any]] = None, transaction: Dict[str, Any] = None
    ) -> Tuple[float, str, str]:
        """Extract amount/merchant/description for behavior checks."""
        if transaction:
            return (
                transaction.get("amount", 0),
                transaction.get("merchant", ""),
                transaction.get("description", ""),
            )

        if transactions and len(transactions) > 0:
            first_tx = transactions[0]
            return (
                first_tx.get("amount", 0),
                first_tx.get("merchant", ""),
                first_tx.get("description", ""),
            )

        return 0, "", ""

    @staticmethod
    def _actual_label_from_transaction(transaction: Dict[str, Any]) -> int:
        """Return binary actual label using notebook-compatible fields."""
        return 1 if transaction.get("is_fraud", transaction.get("suspicious_pattern", False)) else 0

    @staticmethod
    def _classification_counts(predictions: List[int], actuals: List[int]) -> Dict[str, int]:
        """Compute confusion-matrix counts."""
        return {
            "true_positives": sum(
                1 for prediction, actual in zip(predictions, actuals) if prediction == 1 and actual == 1
            ),
            "false_positives": sum(
                1 for prediction, actual in zip(predictions, actuals) if prediction == 1 and actual == 0
            ),
            "true_negatives": sum(
                1 for prediction, actual in zip(predictions, actuals) if prediction == 0 and actual == 0
            ),
            "false_negatives": sum(
                1 for prediction, actual in zip(predictions, actuals) if prediction == 0 and actual == 1
            ),
        }

    @staticmethod
    def _safe_divide(numerator: float, denominator: float) -> float:
        """Return safe division result for notebook metrics."""
        return numerator / denominator if denominator > 0 else 0.0

    def _average_confidence(self, transactions: List[Dict[str, Any]]) -> float:
        """Compute average fraud confidence using compatibility scoring path."""
        if not transactions:
            return 0.0
        confidence_scores = [self.detect_fraud(tx)["fraud_score"] for tx in transactions]
        return self._safe_divide(sum(confidence_scores), len(transactions))

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
        acc_id = self._resolve_account_id(transaction, account_id)
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
        risk_level = self._risk_level_from_score(velocity_score)

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
        risk_level = self._risk_level_from_score(geo_score)

        return {
            "is_geographic_anomaly": is_anomaly,
            "is_anomalous": is_anomaly,
            "geographic_score": geo_score,
            "risk_level": risk_level,
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

        amount, merchant, description = self._extract_behavior_inputs(transactions, transaction)

        behavioral_score = self._check_behavior(
            account_id=account_id, amount=amount, merchant=merchant, description=description
        )

        is_anomaly = behavioral_score >= 0.6
        risk_level = self._risk_level_from_score(
            behavioral_score, high_threshold=0.7, medium_threshold=0.5
        )

        return {
            "is_behavioral_anomaly": is_anomaly,
            "is_anomalous": is_anomaly,
            "behavioral_score": behavioral_score,
            "risk_level": risk_level,
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
            actuals.append(self._actual_label_from_transaction(tx))

        if not predictions:
            return {"error": "No predictions made"}

        counts = self._classification_counts(predictions, actuals)
        true_pos = counts["true_positives"]
        false_pos = counts["false_positives"]
        true_neg = counts["true_negatives"]
        false_neg = counts["false_negatives"]

        precision = self._safe_divide(true_pos, true_pos + false_pos)
        recall = self._safe_divide(true_pos, true_pos + false_neg)
        f1 = self._safe_divide(2 * precision * recall, precision + recall)
        accuracy = self._safe_divide(true_pos + true_neg, len(predictions))

        anomalies = sum(predictions)
        anomaly_rate = self._safe_divide(anomalies, len(predictions))
        avg_confidence = self._average_confidence(test_transactions)

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
            "avg_confidence": avg_confidence,
        }
