"""
Identity Fraud Detection Module
================================

Synthetic identity fraud detection and prevention for banking compliance.

This module provides tools for:
- Generating synthetic identities for testing
- Validating identity authenticity
- Detecting bust-out schemes
- Pattern injection for fraud scenarios

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.2 - Synthetic Identity Fraud Detection
"""

from .bust_out_detector import (
    BustOutDetectionResult,
    BustOutDetector,
    BustOutIndicator,
)
from .identity_validator import (
    IdentityValidator,
    SharedAttributeCluster,
    ValidationResult,
)
from .synthetic_identity_generator import (
    CreditTier,
    IdentityType,
    SyntheticIdentityGenerator,
)
from .synthetic_identity_pattern_generator import (
    PatternConfig,
    PatternType,
    SyntheticIdentityPatternGenerator,
)

__all__ = [
    "SyntheticIdentityGenerator",
    "SyntheticIdentityPatternGenerator",
    "IdentityType",
    "CreditTier",
    "PatternType",
    "PatternConfig",
    "IdentityValidator",
    "ValidationResult",
    "SharedAttributeCluster",
    "BustOutDetector",
    "BustOutDetectionResult",
    "BustOutIndicator",
]

__version__ = "1.0.0"

# Made with Bob
