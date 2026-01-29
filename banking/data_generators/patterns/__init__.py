"""
Pattern Generators Package
==========================

Pattern generators for detecting sophisticated financial crime patterns including
insider trading, trade-based money laundering, fraud rings, structuring, and CATO.

Author: IBM Bob
Date: 2026-01-28
"""

from .insider_trading_pattern_generator import InsiderTradingPatternGenerator
from .tbml_pattern_generator import TBMLPatternGenerator
from .fraud_ring_pattern_generator import FraudRingPatternGenerator
from .structuring_pattern_generator import StructuringPatternGenerator
from .cato_pattern_generator import CATOPatternGenerator

__all__ = [
    'InsiderTradingPatternGenerator',
    'TBMLPatternGenerator',
    'FraudRingPatternGenerator',
    'StructuringPatternGenerator',
    'CATOPatternGenerator',
]

