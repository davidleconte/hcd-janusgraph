"""
Synthetic Data Generators for Banking Compliance

This package provides comprehensive synthetic data generation for testing
advanced financial crime detection patterns including:
- Insider trading
- Trade-based money laundering (TBML)
- Fraud rings
- AML structuring
- Corporate account takeover (CATO)

Version: 1.0.0
Author: IBM Bob
Date: 2026-01-28
"""

__version__ = "1.0.0"
__author__ = "IBM Bob"

from banking.data_generators.core.person_generator import PersonGenerator
from banking.data_generators.core.company_generator import CompanyGenerator
from banking.data_generators.core.account_generator import AccountGenerator

__all__ = [
    'PersonGenerator',
    'CompanyGenerator',
    'AccountGenerator',
]

