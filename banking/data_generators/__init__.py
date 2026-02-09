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
Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

__version__ = "1.0.0"
__author__ = "David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS"

from banking.data_generators.core.account_generator import AccountGenerator
from banking.data_generators.core.company_generator import CompanyGenerator
from banking.data_generators.core.person_generator import PersonGenerator

__all__ = [
    "PersonGenerator",
    "CompanyGenerator",
    "AccountGenerator",
]
