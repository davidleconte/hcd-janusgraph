"""
Cryptocurrency AML Detection Module

This module provides comprehensive cryptocurrency Anti-Money Laundering (AML) detection capabilities:
- Wallet generation and management
- Transaction generation and tracking
- Mixer/tumbler detection
- Sanctions screening (OFAC, UN, EU)
- Risk scoring and recommendations

Author: AI Assistant
Date: 2026-04-10
Version: 1.0
"""

from banking.crypto.wallet_generator import WalletGenerator
from banking.crypto.crypto_transaction_generator import CryptoTransactionGenerator
from banking.crypto.mixer_detector import (
    MixerDetector,
    MixerDetectionResult,
    MixerPath,
)
from banking.crypto.sanctions_screener import (
    SanctionsScreener,
    SanctionsScreeningResult,
    SanctionsMatch,
)

__all__ = [
    # Wallet generation
    "WalletGenerator",
    # Transaction generation
    "CryptoTransactionGenerator",
    # Mixer detection
    "MixerDetector",
    "MixerDetectionResult",
    "MixerPath",
    # Sanctions screening
    "SanctionsScreener",
    "SanctionsScreeningResult",
    "SanctionsMatch",
]

__version__ = "1.0.0"

# Made with Bob
