"""Tests for banking.data_generators.patterns modules."""

import pytest

from banking.data_generators.core.account_generator import AccountGenerator
from banking.data_generators.core.company_generator import CompanyGenerator
from banking.data_generators.core.person_generator import PersonGenerator
from banking.data_generators.events.communication_generator import CommunicationGenerator
from banking.data_generators.events.trade_generator import TradeGenerator
from banking.data_generators.events.transaction_generator import TransactionGenerator
from banking.data_generators.patterns.cato_pattern_generator import CATOPatternGenerator
from banking.data_generators.patterns.fraud_ring_pattern_generator import FraudRingPatternGenerator
from banking.data_generators.patterns.insider_trading_pattern_generator import (
    InsiderTradingPatternGenerator,
)
from banking.data_generators.patterns.structuring_pattern_generator import (
    StructuringPatternGenerator,
)
from banking.data_generators.patterns.tbml_pattern_generator import TBMLPatternGenerator


class TestStructuringPatternGenerator:
    def test_init(self):
        gen = StructuringPatternGenerator(seed=42)
        assert gen is not None

    def test_generate(self):
        gen = StructuringPatternGenerator(seed=42)
        pattern = gen.generate()
        assert pattern is not None


class TestFraudRingPatternGenerator:
    def test_init(self):
        gen = FraudRingPatternGenerator(seed=42)
        assert gen is not None

    def test_generate(self):
        gen = FraudRingPatternGenerator(seed=42)
        assert gen.seed == 42


class TestInsiderTradingPatternGenerator:
    def test_init(self):
        gen = InsiderTradingPatternGenerator(seed=42)
        assert gen is not None


class TestCATOPatternGenerator:
    def test_init(self):
        gen = CATOPatternGenerator(seed=42)
        assert gen is not None


class TestTBMLPatternGenerator:
    def test_init(self):
        gen = TBMLPatternGenerator(seed=42)
        assert gen is not None
