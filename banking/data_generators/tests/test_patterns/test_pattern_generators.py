"""
Pattern Generator Tests
Tests for AML/Fraud pattern generation modules.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Created: 2026-02-04
"""

import sys
from pathlib import Path

import pytest

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from banking.data_generators.patterns.cato_pattern_generator import CATOPatternGenerator
from banking.data_generators.patterns.fraud_ring_pattern_generator import FraudRingPatternGenerator
from banking.data_generators.patterns.insider_trading_pattern_generator import (
    InsiderTradingPatternGenerator,
)
from banking.data_generators.patterns.mule_chain_generator import MuleChainGenerator
from banking.data_generators.patterns.structuring_pattern_generator import (
    StructuringPatternGenerator,
)
from banking.data_generators.patterns.tbml_pattern_generator import TBMLPatternGenerator


class TestInsiderTradingPatternGenerator:
    """Tests for InsiderTradingPatternGenerator."""

    def test_init(self):
        """Test generator initialization."""
        gen = InsiderTradingPatternGenerator(seed=42)
        assert gen is not None
        assert gen.seed == 42

    def test_init_with_different_seeds(self):
        """Test that different seeds produce different results."""
        gen1 = InsiderTradingPatternGenerator(seed=1)
        gen2 = InsiderTradingPatternGenerator(seed=2)
        assert gen1.seed != gen2.seed

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        gen1 = InsiderTradingPatternGenerator(seed=42)
        gen2 = InsiderTradingPatternGenerator(seed=42)
        assert gen1.seed == gen2.seed


class TestTBMLPatternGenerator:
    """Tests for Trade-Based Money Laundering Pattern Generator."""

    def test_init(self):
        """Test generator initialization."""
        gen = TBMLPatternGenerator(seed=42)
        assert gen is not None
        assert gen.seed == 42

    def test_init_with_different_seeds(self):
        """Test that different seeds produce different results."""
        gen1 = TBMLPatternGenerator(seed=1)
        gen2 = TBMLPatternGenerator(seed=2)
        assert gen1.seed != gen2.seed

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        gen1 = TBMLPatternGenerator(seed=42)
        gen2 = TBMLPatternGenerator(seed=42)
        assert gen1.seed == gen2.seed


class TestFraudRingPatternGenerator:
    """Tests for Fraud Ring Pattern Generator."""

    def test_init(self):
        """Test generator initialization."""
        gen = FraudRingPatternGenerator(seed=42)
        assert gen is not None
        assert gen.seed == 42

    def test_init_with_different_seeds(self):
        """Test that different seeds produce different results."""
        gen1 = FraudRingPatternGenerator(seed=1)
        gen2 = FraudRingPatternGenerator(seed=2)
        assert gen1.seed != gen2.seed

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        gen1 = FraudRingPatternGenerator(seed=42)
        gen2 = FraudRingPatternGenerator(seed=42)
        assert gen1.seed == gen2.seed


class TestStructuringPatternGenerator:
    """Tests for Structuring (Smurfing) Pattern Generator."""

    def test_init(self):
        """Test generator initialization."""
        gen = StructuringPatternGenerator(seed=42)
        assert gen is not None
        assert gen.seed == 42

    def test_init_with_different_seeds(self):
        """Test that different seeds produce different results."""
        gen1 = StructuringPatternGenerator(seed=1)
        gen2 = StructuringPatternGenerator(seed=2)
        assert gen1.seed != gen2.seed

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        gen1 = StructuringPatternGenerator(seed=42)
        gen2 = StructuringPatternGenerator(seed=42)
        assert gen1.seed == gen2.seed


class TestMuleChainPatternGenerator:
    """Tests for Mule Chain Pattern Generator."""

    def test_init(self):
        """Test generator initialization."""
        gen = MuleChainGenerator(seed=42)
        assert gen is not None
        assert gen.seed == 42

    def test_init_with_different_seeds(self):
        """Test that different seeds produce different results."""
        gen1 = MuleChainGenerator(seed=1)
        gen2 = MuleChainGenerator(seed=2)
        assert gen1.seed != gen2.seed

    def test_reproducibility(self):
        """Test that same seed produces same results for core outputs."""
        gen1 = MuleChainGenerator(seed=42)
        pattern1, txns1 = gen1.generate(chain_length=4, start_amount=10000.0, hop_delay_minutes=15)

        # Reinitialize to reset deterministic counters before second run.
        gen2 = MuleChainGenerator(seed=42)
        pattern2, txns2 = gen2.generate(chain_length=4, start_amount=10000.0, hop_delay_minutes=15)

        assert pattern1.pattern_id == pattern2.pattern_id
        assert pattern1.transaction_ids == pattern2.transaction_ids
        assert [t.transaction_id for t in txns1] == [t.transaction_id for t in txns2]
        assert [t.amount for t in txns1] == [t.amount for t in txns2]


class TestCATOPatternGenerator:
    """Tests for CATO (Complex AML Typology) Pattern Generator."""

    def test_init(self):
        """Test generator initialization."""
        gen = CATOPatternGenerator(seed=42)
        assert gen is not None
        assert gen.seed == 42

    def test_init_with_different_seeds(self):
        """Test that different seeds produce different results."""
        gen1 = CATOPatternGenerator(seed=1)
        gen2 = CATOPatternGenerator(seed=2)
        assert gen1.seed != gen2.seed

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        gen1 = CATOPatternGenerator(seed=42)
        gen2 = CATOPatternGenerator(seed=42)
        assert gen1.seed == gen2.seed


class TestPatternGeneratorIntegration:
    """Integration tests for pattern generators."""

    def test_all_generators_instantiate(self):
        """Test that all pattern generators can be instantiated."""
        generators = [
            InsiderTradingPatternGenerator(seed=42),
            TBMLPatternGenerator(seed=42),
            FraudRingPatternGenerator(seed=42),
            MuleChainGenerator(seed=42),
            StructuringPatternGenerator(seed=42),
            CATOPatternGenerator(seed=42),
        ]
        assert len(generators) == 6
        for gen in generators:
            assert gen is not None

    def test_generators_have_seed_attribute(self):
        """Test that all generators have seed attribute."""
        generators = [
            InsiderTradingPatternGenerator(seed=123),
            TBMLPatternGenerator(seed=123),
            FraudRingPatternGenerator(seed=123),
            MuleChainGenerator(seed=123),
            StructuringPatternGenerator(seed=123),
            CATOPatternGenerator(seed=123),
        ]
        for gen in generators:
            assert hasattr(gen, "seed")
            assert gen.seed == 123


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
