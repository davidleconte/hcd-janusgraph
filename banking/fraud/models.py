"""
Fraud Detection Data Models
============================

Dataclasses for fraud alerts, scores, and risk assessment.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class FraudAlert:
    """Fraud detection alert."""

    alert_id: str
    alert_type: str
    severity: str
    transaction_id: str
    account_id: str
    customer_id: str
    customer_name: str
    amount: float
    merchant: str
    fraud_score: float
    risk_factors: List[str]
    similar_cases: List[Dict]
    timestamp: str
    metadata: Dict[str, Any]


@dataclass
class FraudScore:
    """Fraud risk score for a transaction."""

    transaction_id: str
    overall_score: float
    velocity_score: float
    network_score: float
    merchant_score: float
    behavioral_score: float
    risk_level: str
    recommendation: str


HIGH_RISK_MERCHANTS: Dict[str, float] = {
    "crypto": 0.7,
    "bitcoin": 0.7,
    "coinbase": 0.5,
    "binance": 0.6,
    "wire transfer": 0.6,
    "western union": 0.5,
    "moneygram": 0.5,
    "casino": 0.6,
    "gambling": 0.6,
    "betting": 0.5,
    "poker": 0.5,
    "jewelry": 0.4,
    "electronics": 0.3,
    "luxury": 0.4,
    "online gaming": 0.4,
    "virtual": 0.3,
    "money order": 0.5,
    "prepaid card": 0.4,
    "gift card": 0.4,
}
