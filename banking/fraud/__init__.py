"""
Fraud Detection Module
======================
Real-time fraud detection using graph analysis and ML.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
"""

from banking.fraud.fraud_detection import FraudDetector
from banking.fraud.models import HIGH_RISK_MERCHANTS, FraudAlert, FraudScore

__all__ = ["FraudDetector", "FraudAlert", "FraudScore", "HIGH_RISK_MERCHANTS"]
