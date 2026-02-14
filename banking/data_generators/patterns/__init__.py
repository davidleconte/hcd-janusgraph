"""
Pattern Generators Package
==========================

Pattern generators for detecting sophisticated financial crime patterns including
insider trading, trade-based money laundering, fraud rings, structuring, and CATO.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

from .cato_pattern_generator import CATOPatternGenerator
from .fraud_ring_pattern_generator import FraudRingPatternGenerator
from .insider_trading_pattern_generator import InsiderTradingPatternGenerator
from .structuring_pattern_generator import StructuringPatternGenerator
from .tbml_pattern_generator import TBMLPatternGenerator

__all__ = [
    "InsiderTradingPatternGenerator",
    "TBMLPatternGenerator",
    "FraudRingPatternGenerator",
    "StructuringPatternGenerator",
    "CATOPatternGenerator",
]
