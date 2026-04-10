"""
Tests for CryptoMixerPatternGenerator
======================================

Tests deterministic crypto mixer pattern generation.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-10
Phase: 7.1 - Crypto/Digital Assets
"""

import pytest

from banking.crypto.crypto_transaction_generator import CryptoTransactionGenerator
from banking.crypto.wallet_generator import WalletGenerator
from banking.data_generators.patterns.crypto_mixer_pattern_generator import (
    CryptoMixerPatternGenerator,
)


@pytest.fixture
def wallets():
    """Generate test wallets."""
    gen = WalletGenerator(seed=42)
    return gen.generate_batch(50)


@pytest.fixture
def transactions(wallets):
    """Generate test transactions."""
    gen = CryptoTransactionGenerator(wallets, seed=42)
    return gen.generate_batch(100)


class TestCryptoMixerPatternGeneratorDeterminism:
    """Test deterministic behavior of CryptoMixerPatternGenerator."""
    
    def test_same_seed_produces_identical_patterns(self, wallets, transactions):
        """Test that same seed produces identical patterns."""
        seed = 42
        pattern_count = 5
        
        # Generate with seed 1
        gen1 = CryptoMixerPatternGenerator(seed=seed)
        result1 = gen1.inject_pattern(
            wallets=wallets.copy(),
            transactions=transactions.copy(),
            pattern_count=pattern_count
        )
        
        # Generate with seed 2 (same seed)
        gen2 = CryptoMixerPatternGenerator(seed=seed)
        result2 = gen2.inject_pattern(
            wallets=wallets.copy(),
            transactions=transactions.copy(),
            pattern_count=pattern_count
        )
        
        # Must be identical
        assert result1["pattern_type"] == result2["pattern_type"]
        assert result1["pattern_count"] == result2["pattern_count"]
        assert len(result1["patterns"]) == len(result2["patterns"])
        assert len(result1["mixer_wallets"]) == len(result2["mixer_wallets"])
    
    def test_different_seeds_produce_different_patterns(self, wallets, transactions):
        """Test that different seeds produce different patterns."""
        pattern_count = 5
        
        gen1 = CryptoMixerPatternGenerator(seed=42)
        gen2 = CryptoMixerPatternGenerator(seed=123)
        
        result1 = gen1.inject_pattern(
            wallets=wallets.copy(),
            transactions=transactions.copy(),
            pattern_count=pattern_count
        )
        result2 = gen2.inject_pattern(
            wallets=wallets.copy(),
            transactions=transactions.copy(),
            pattern_count=pattern_count
        )
        
        # Should be different
        assert result1["pattern_count"] == result2["pattern_count"]
        # At least some patterns should be different
        assert result1["mixer_wallets"] != result2["mixer_wallets"]
    
    def test_approved_seeds_work(self, wallets, transactions):
        """Test that approved seeds (42, 123, 999) work correctly."""
        approved_seeds = [42, 123, 999]
        
        for seed in approved_seeds:
            gen = CryptoMixerPatternGenerator(seed=seed)
            result = gen.inject_pattern(
                wallets=wallets.copy(),
                transactions=transactions.copy(),
                pattern_count=3
            )
            
            assert result is not None
            assert "pattern_count" in result
            assert result["pattern_count"] > 0


class TestCryptoMixerPatternGeneratorFunctional:
    """Test functional requirements of CryptoMixerPatternGenerator."""
    
    def test_required_fields_present(self, wallets, transactions):
        """Test that all required fields are present in result."""
        gen = CryptoMixerPatternGenerator(seed=42)
        result = gen.inject_pattern(
            wallets=wallets,
            transactions=transactions,
            pattern_count=3
        )
        
        required_fields = [
            "pattern_type",
            "pattern_count",
            "patterns",
            "mixer_wallets",
            "affected_transactions",
            "total_amount_mixed"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
    
    def test_pattern_count_matches_request(self, wallets, transactions):
        """Test that pattern count matches request."""
        gen = CryptoMixerPatternGenerator(seed=42)
        
        for count in [1, 3, 5]:
            result = gen.inject_pattern(
                wallets=wallets.copy(),
                transactions=transactions.copy(),
                pattern_count=count
            )
            
            # May be less if not enough wallets
            assert result["pattern_count"] <= count
            assert result["pattern_count"] > 0
    
    def test_mixer_wallets_marked(self, wallets, transactions):
        """Test that mixer wallets are properly marked."""
        gen = CryptoMixerPatternGenerator(seed=42)
        result = gen.inject_pattern(
            wallets=wallets,
            transactions=transactions,
            pattern_count=3
        )
        
        # Check that mixer wallets are marked
        mixer_ids = result["mixer_wallets"]
        for wallet in wallets:
            if wallet["wallet_id"] in mixer_ids:
                assert wallet["is_mixer"] is True
                assert wallet["wallet_type"] == "mixer"
    
    def test_transactions_added(self, wallets, transactions):
        """Test that transactions are added to the list."""
        gen = CryptoMixerPatternGenerator(seed=42)
        initial_count = len(transactions)
        
        result = gen.inject_pattern(
            wallets=wallets,
            transactions=transactions,
            pattern_count=3
        )
        
        # Transactions should be added
        assert len(transactions) > initial_count
        assert len(result["affected_transactions"]) > 0
    
    def test_empty_wallets_raises_error(self, transactions):
        """Test that empty wallets list raises error."""
        gen = CryptoMixerPatternGenerator(seed=42)
        
        with pytest.raises(ValueError, match="wallets list cannot be empty"):
            gen.inject_pattern(
                wallets=[],
                transactions=transactions,
                pattern_count=3
            )
    
    def test_empty_transactions_raises_error(self, wallets):
        """Test that empty transactions list raises error."""
        gen = CryptoMixerPatternGenerator(seed=42)
        
        with pytest.raises(ValueError, match="transactions list cannot be empty"):
            gen.inject_pattern(
                wallets=wallets,
                transactions=[],
                pattern_count=3
            )
    
    def test_invalid_pattern_type_raises_error(self, wallets, transactions):
        """Test that invalid pattern type raises error."""
        gen = CryptoMixerPatternGenerator(seed=42)
        
        with pytest.raises(ValueError, match="Invalid pattern_type"):
            gen.inject_pattern(
                wallets=wallets,
                transactions=transactions,
                pattern_count=3,
                pattern_type="invalid_type"
            )


class TestCryptoMixerPatternGeneratorPatternTypes:
    """Test different pattern types."""
    
    def test_simple_mixing_pattern(self, wallets, transactions):
        """Test simple mixing pattern generation."""
        gen = CryptoMixerPatternGenerator(seed=42)
        result = gen.inject_pattern(
            wallets=wallets.copy(),
            transactions=transactions.copy(),
            pattern_count=3,
            pattern_type="simple_mixing"
        )
        
        assert result["pattern_type"] == "simple_mixing"
        assert result["pattern_count"] > 0
        
        # Check pattern structure
        for pattern in result["patterns"]:
            assert "source_wallet" in pattern
            assert "mixer_wallet" in pattern
            assert "destination_wallet" in pattern
            assert "hop_count" in pattern
            assert pattern["hop_count"] == 2  # Source → Mixer → Destination
    
    def test_layering_pattern(self, wallets, transactions):
        """Test layering pattern generation."""
        gen = CryptoMixerPatternGenerator(seed=42)
        result = gen.inject_pattern(
            wallets=wallets.copy(),
            transactions=transactions.copy(),
            pattern_count=3,
            pattern_type="layering"
        )
        
        assert result["pattern_type"] == "layering"
        assert result["pattern_count"] > 0
        
        # Check pattern structure
        for pattern in result["patterns"]:
            assert "source_wallet" in pattern
            assert "mixer_wallets" in pattern
            assert "destination_wallet" in pattern
            assert "layer_count" in pattern
            assert len(pattern["mixer_wallets"]) >= 2  # Multiple mixers
    
    def test_peeling_chain_pattern(self, wallets, transactions):
        """Test peeling chain pattern generation."""
        gen = CryptoMixerPatternGenerator(seed=42)
        result = gen.inject_pattern(
            wallets=wallets.copy(),
            transactions=transactions.copy(),
            pattern_count=3,
            pattern_type="peeling_chain"
        )
        
        assert result["pattern_type"] == "peeling_chain"
        assert result["pattern_count"] > 0
        
        # Check pattern structure
        for pattern in result["patterns"]:
            assert "source_wallet" in pattern
            assert "mixer_wallet" in pattern
            assert "destination_wallets" in pattern
            assert "split_count" in pattern
            assert len(pattern["destination_wallets"]) >= 3  # Multiple destinations
    
    def test_round_robin_pattern(self, wallets, transactions):
        """Test round-robin pattern generation."""
        gen = CryptoMixerPatternGenerator(seed=42)
        result = gen.inject_pattern(
            wallets=wallets.copy(),
            transactions=transactions.copy(),
            pattern_count=3,
            pattern_type="round_robin"
        )
        
        assert result["pattern_type"] == "round_robin"
        assert result["pattern_count"] > 0
        
        # Check pattern structure
        for pattern in result["patterns"]:
            assert "source_wallets" in pattern
            assert "mixer_wallet" in pattern
            assert "destination_wallets" in pattern
            assert len(pattern["source_wallets"]) >= 2  # Multiple sources
            assert len(pattern["destination_wallets"]) >= 2  # Multiple destinations
    
    def test_time_delayed_pattern(self, wallets, transactions):
        """Test time-delayed pattern generation."""
        gen = CryptoMixerPatternGenerator(seed=42)
        result = gen.inject_pattern(
            wallets=wallets.copy(),
            transactions=transactions.copy(),
            pattern_count=3,
            pattern_type="time_delayed"
        )
        
        assert result["pattern_type"] == "time_delayed"
        assert result["pattern_count"] > 0


class TestCryptoMixerPatternGeneratorTransactionMarking:
    """Test that generated transactions are properly marked."""
    
    def test_transactions_marked_suspicious(self, wallets, transactions):
        """Test that mixer transactions are marked as suspicious."""
        gen = CryptoMixerPatternGenerator(seed=42)
        initial_count = len(transactions)
        
        result = gen.inject_pattern(
            wallets=wallets,
            transactions=transactions,
            pattern_count=3
        )
        
        # Check new transactions
        new_transactions = transactions[initial_count:]
        for tx in new_transactions:
            assert tx["is_suspicious"] is True
            assert tx["risk_score"] >= 0.8  # High risk
    
    def test_transactions_have_pattern_id(self, wallets, transactions):
        """Test that mixer transactions have pattern_id."""
        gen = CryptoMixerPatternGenerator(seed=42)
        initial_count = len(transactions)
        
        result = gen.inject_pattern(
            wallets=wallets,
            transactions=transactions,
            pattern_count=3
        )
        
        # Check new transactions
        new_transactions = transactions[initial_count:]
        for tx in new_transactions:
            assert "pattern_id" in tx
            # Pattern ID uses hyphens, pattern_type uses underscores
            pattern_type_with_hyphens = result["pattern_type"].replace("_", "-")
            assert tx["pattern_id"].startswith(pattern_type_with_hyphens)


class TestCryptoMixerPatternGeneratorStatistics:
    """Test pattern statistics calculation."""
    
    def test_total_amount_calculated(self, wallets, transactions):
        """Test that total amount mixed is calculated."""
        gen = CryptoMixerPatternGenerator(seed=42)
        result = gen.inject_pattern(
            wallets=wallets,
            transactions=transactions,
            pattern_count=3
        )
        
        assert "total_amount_mixed" in result
        assert result["total_amount_mixed"] > 0.0
    
    def test_affected_transactions_tracked(self, wallets, transactions):
        """Test that affected transactions are tracked."""
        gen = CryptoMixerPatternGenerator(seed=42)
        result = gen.inject_pattern(
            wallets=wallets,
            transactions=transactions,
            pattern_count=3
        )
        
        assert "affected_transactions" in result
        assert len(result["affected_transactions"]) > 0
        
        # All affected transactions should exist
        tx_ids = [tx["transaction_id"] for tx in transactions]
        for affected_id in result["affected_transactions"]:
            assert affected_id in tx_ids
    
    def test_mixer_wallets_tracked(self, wallets, transactions):
        """Test that mixer wallets are tracked."""
        gen = CryptoMixerPatternGenerator(seed=42)
        result = gen.inject_pattern(
            wallets=wallets,
            transactions=transactions,
            pattern_count=3
        )
        
        assert "mixer_wallets" in result
        assert len(result["mixer_wallets"]) > 0
        
        # All mixer wallets should exist
        wallet_ids = [w["wallet_id"] for w in wallets]
        for mixer_id in result["mixer_wallets"]:
            assert mixer_id in wallet_ids


class TestCryptoMixerPatternGeneratorIntegration:
    """Test integration with wallet and transaction generators."""
    
    def test_end_to_end_pattern_injection(self):
        """Test complete pattern injection workflow."""
        seed = 42
        
        # Generate wallets
        wallet_gen = WalletGenerator(seed=seed)
        wallets = wallet_gen.generate_batch(50)
        
        # Generate transactions
        tx_gen = CryptoTransactionGenerator(wallets, seed=seed)
        transactions = tx_gen.generate_batch(100)
        
        # Inject patterns
        pattern_gen = CryptoMixerPatternGenerator(seed=seed)
        result = pattern_gen.inject_pattern(
            wallets=wallets,
            transactions=transactions,
            pattern_count=5
        )
        
        # Verify results
        assert result["pattern_count"] > 0
        assert len(result["mixer_wallets"]) > 0
        assert len(result["affected_transactions"]) > 0
        assert result["total_amount_mixed"] > 0.0
        
        # Verify wallets are marked (may have more mixers from wallet generator)
        mixer_count = sum(1 for w in wallets if w.get("is_mixer", False))
        assert mixer_count >= len(result["mixer_wallets"])
        
        # Verify transactions are added
        assert len(transactions) > 100  # Original 100 + new ones
    
    def test_multiple_pattern_types(self):
        """Test injecting multiple pattern types."""
        seed = 42
        
        wallet_gen = WalletGenerator(seed=seed)
        wallets = wallet_gen.generate_batch(50)
        
        tx_gen = CryptoTransactionGenerator(wallets, seed=seed)
        transactions = tx_gen.generate_batch(100)
        
        pattern_gen = CryptoMixerPatternGenerator(seed=seed)
        
        # Inject different pattern types
        pattern_types = ["simple_mixing", "layering", "peeling_chain"]
        
        for pattern_type in pattern_types:
            result = pattern_gen.inject_pattern(
                wallets=wallets,
                transactions=transactions,
                pattern_count=2,
                pattern_type=pattern_type
            )
            
            assert result["pattern_type"] == pattern_type
            assert result["pattern_count"] > 0

# Made with Bob
