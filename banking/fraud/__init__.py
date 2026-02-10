"""
Fraud Detection Module
======================
Real-time fraud detection using graph analysis and ML.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
"""

from banking.fraud.fraud_detection import FraudDetector
from banking.fraud.models import FraudAlert, FraudScore, HIGH_RISK_MERCHANTS

__all__ = ["FraudDetector", "FraudAlert", "FraudScore", "HIGH_RISK_MERCHANTS"]
