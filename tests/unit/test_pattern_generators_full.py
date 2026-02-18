"""Tests for banking.data_generators.patterns modules with generated entities."""

from datetime import datetime, timezone
from decimal import Decimal

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
from banking.data_generators.utils.data_models import Pattern, RiskLevel


@pytest.fixture
def persons():
    return PersonGenerator(seed=42).generate_batch(10)


@pytest.fixture
def companies():
    return CompanyGenerator(seed=42).generate_batch(5)


@pytest.fixture
def accounts():
    return AccountGenerator(seed=42).generate_batch(10)


@pytest.fixture
def transactions():
    return TransactionGenerator(seed=42).generate_batch(20)


@pytest.fixture
def communications():
    return CommunicationGenerator(seed=42).generate_batch(10)


@pytest.fixture
def trades():
    return TradeGenerator(seed=42).generate_batch(10)


class TestStructuringPatternGenerator:
    def test_init(self):
        gen = StructuringPatternGenerator(seed=42)
        assert gen is not None
        assert gen.txn_gen is not None

    def test_generate_default(self):
        gen = StructuringPatternGenerator(seed=42)
        pattern = gen.generate()
        assert isinstance(pattern, Pattern)
        assert pattern.pattern_type == "structuring"
        assert pattern.confidence_score > 0
        assert pattern.transaction_count > 0
        assert pattern.total_value > 0
        assert isinstance(pattern.risk_level, RiskLevel)
        assert len(pattern.indicators) > 0
        assert len(pattern.red_flags) > 0

    def test_generate_classic_structuring(self):
        gen = StructuringPatternGenerator(seed=42)
        pattern = gen.generate(pattern_type="classic_structuring")
        assert pattern.metadata["pattern_subtype"] == "classic_structuring"

    def test_generate_smurfing(self):
        gen = StructuringPatternGenerator(seed=42)
        pattern = gen.generate(pattern_type="smurfing", smurf_count=5)
        assert pattern.metadata["smurf_count"] == 5
        indicators = pattern.indicators
        assert any("smurf" in i.lower() or "coordinated" in i.lower() for i in indicators)

    def test_generate_geographic_smurfing(self):
        gen = StructuringPatternGenerator(seed=42)
        pattern = gen.generate(pattern_type="geographic_smurfing")
        assert "geographic" in " ".join(pattern.indicators).lower()

    def test_generate_temporal_smurfing(self):
        gen = StructuringPatternGenerator(seed=42)
        pattern = gen.generate(pattern_type="temporal_smurfing")
        assert "temporal" in " ".join(pattern.indicators).lower()

    def test_generate_account_hopping(self):
        gen = StructuringPatternGenerator(seed=42)
        pattern = gen.generate(pattern_type="account_hopping")
        assert "account" in " ".join(pattern.indicators).lower()

    def test_generate_with_custom_params(self):
        gen = StructuringPatternGenerator(seed=42)
        pattern = gen.generate(
            smurf_count=3,
            transaction_count=10,
            time_window_hours=48,
        )
        assert pattern.metadata["smurf_count"] == 3
        assert pattern.metadata["time_window_hours"] == 48

    def test_generate_batch(self):
        gen = StructuringPatternGenerator(seed=42)
        patterns = gen.generate_batch(3)
        assert len(patterns) == 3
        assert all(isinstance(p, Pattern) for p in patterns)

    def test_determine_risk_level_critical(self):
        gen = StructuringPatternGenerator(seed=42)
        level = gen._determine_risk_level(0.9, Decimal("200000"))
        assert level == RiskLevel.CRITICAL

    def test_determine_risk_level_high(self):
        gen = StructuringPatternGenerator(seed=42)
        level = gen._determine_risk_level(0.75, Decimal("30000"))
        assert level == RiskLevel.HIGH

    def test_determine_risk_level_medium(self):
        gen = StructuringPatternGenerator(seed=42)
        level = gen._determine_risk_level(0.6, Decimal("5000"))
        assert level == RiskLevel.MEDIUM

    def test_determine_risk_level_low(self):
        gen = StructuringPatternGenerator(seed=42)
        level = gen._determine_risk_level(0.3, Decimal("1000"))
        assert level == RiskLevel.LOW

    def test_calculate_severity_score(self):
        gen = StructuringPatternGenerator(seed=42)
        score = gen._calculate_severity_score(0.8, Decimal("200000"), 6, 7)
        assert 0.0 <= score <= 1.0

    def test_generate_indicators(self):
        gen = StructuringPatternGenerator(seed=42)
        indicators = gen._generate_indicators("smurfing", list(range(25)), 6)
        assert "structuring_detected" in indicators
        assert "large_smurf_network" in indicators
        assert "high_transaction_frequency" in indicators

    def test_generate_red_flags_high_value(self):
        gen = StructuringPatternGenerator(seed=42)
        flags = gen._generate_red_flags("classic", list(range(20)), Decimal("200000"))
        assert "high_total_value" in flags
        assert "excessive_transaction_count" in flags


class TestFraudRingPatternGenerator:
    def test_init(self):
        gen = FraudRingPatternGenerator(seed=42)
        assert gen is not None
        assert gen.seed == 42

    def test_generate(self):
        gen = FraudRingPatternGenerator(seed=42)
        pattern = gen.generate()
        assert isinstance(pattern, Pattern)
        assert pattern.pattern_type in ("fraud_ring", "money_mule_network")

    def test_generate_batch(self):
        gen = FraudRingPatternGenerator(seed=42)
        patterns = gen.generate_batch(2)
        assert len(patterns) == 2


class TestInsiderTradingPatternGenerator:
    def test_init(self):
        gen = InsiderTradingPatternGenerator(seed=42)
        assert gen is not None

    def test_generate(self):
        gen = InsiderTradingPatternGenerator(seed=42)
        result = gen.generate()
        if isinstance(result, tuple):
            pattern = result[0]
        else:
            pattern = result
        assert isinstance(pattern, Pattern)

    def test_generate_batch(self):
        gen = InsiderTradingPatternGenerator(seed=42)
        patterns = gen.generate_batch(2)
        assert len(patterns) == 2


class TestCATOPatternGenerator:
    def test_init(self):
        gen = CATOPatternGenerator(seed=42)
        assert gen is not None

    def test_generate(self):
        gen = CATOPatternGenerator(seed=42)
        pattern = gen.generate()
        assert isinstance(pattern, Pattern)

    def test_generate_batch(self):
        gen = CATOPatternGenerator(seed=42)
        patterns = gen.generate_batch(2)
        assert len(patterns) == 2


class TestTBMLPatternGenerator:
    def test_init(self):
        gen = TBMLPatternGenerator(seed=42)
        assert gen is not None

    def test_generate(self):
        gen = TBMLPatternGenerator(seed=42)
        result = gen.generate()
        if isinstance(result, tuple):
            pattern = result[0]
        else:
            pattern = result
        assert isinstance(pattern, Pattern)

    def test_generate_batch(self):
        gen = TBMLPatternGenerator(seed=42)
        patterns = gen.generate_batch(2)
        assert len(patterns) == 2
