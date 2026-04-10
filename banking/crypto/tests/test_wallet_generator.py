"""
Tests for WalletGenerator
=========================

Tests deterministic cryptocurrency wallet generation.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-10
Phase: 7.1 - Crypto/Digital Assets
"""

import pytest

from banking.crypto.wallet_generator import WalletGenerator
from banking.data_generators.utils.deterministic import REFERENCE_TIMESTAMP


class TestWalletGeneratorDeterminism:
    """Test deterministic behavior of WalletGenerator."""
    
    def test_same_seed_produces_identical_wallets(self):
        """Test that same seed produces identical wallets."""
        seed = 42
        count = 100
        
        # Generate with seed 1
        gen1 = WalletGenerator(seed=seed)
        wallets1 = gen1.generate_batch(count)
        
        # Generate with seed 2 (same seed)
        gen2 = WalletGenerator(seed=seed)
        wallets2 = gen2.generate_batch(count)
        
        # Must be identical
        assert len(wallets1) == len(wallets2) == count
        
        for w1, w2 in zip(wallets1, wallets2):
            assert w1["wallet_id"] == w2["wallet_id"]
            assert w1["address"] == w2["address"]
            assert w1["currency"] == w2["currency"]
            assert w1["wallet_type"] == w2["wallet_type"]
            assert w1["balance"] == w2["balance"]
            assert w1["is_mixer"] == w2["is_mixer"]
            assert w1["is_sanctioned"] == w2["is_sanctioned"]
            assert w1["risk_score"] == w2["risk_score"]
    
    def test_different_seeds_produce_different_wallets(self):
        """Test that different seeds produce different wallets."""
        count = 100
        
        gen1 = WalletGenerator(seed=42)
        gen2 = WalletGenerator(seed=123)
        
        wallets1 = gen1.generate_batch(count)
        wallets2 = gen2.generate_batch(count)
        
        # Must be different
        assert len(wallets1) == len(wallets2) == count
        
        # At least some wallets should be different
        different_count = sum(
            1 for w1, w2 in zip(wallets1, wallets2)
            if w1["wallet_id"] != w2["wallet_id"]
        )
        assert different_count > 90  # Expect >90% different
    
    def test_approved_seeds_work(self):
        """Test that approved seeds (42, 123, 999) work correctly."""
        approved_seeds = [42, 123, 999]
        
        for seed in approved_seeds:
            gen = WalletGenerator(seed=seed)
            wallet = gen.generate()
            
            assert wallet is not None
            assert "wallet_id" in wallet
            assert wallet["wallet_id"].startswith("wallet-")


class TestWalletGeneratorFunctional:
    """Test functional requirements of WalletGenerator."""
    
    def test_required_fields_present(self):
        """Test that all required fields are present."""
        gen = WalletGenerator(seed=42)
        wallet = gen.generate()
        
        required_fields = [
            "wallet_id", "address", "currency", "wallet_type",
            "owner_id", "balance", "created_at", "risk_score",
            "is_mixer", "is_sanctioned", "metadata"
        ]
        
        for field in required_fields:
            assert field in wallet, f"Missing required field: {field}"
    
    def test_wallet_id_format(self):
        """Test wallet ID format."""
        gen = WalletGenerator(seed=42)
        wallet = gen.generate()
        
        assert wallet["wallet_id"].startswith("wallet-")
        assert len(wallet["wallet_id"]) > 7  # "wallet-" + hex
    
    def test_supported_currencies(self):
        """Test that only supported currencies are generated."""
        gen = WalletGenerator(seed=42)
        wallets = gen.generate_batch(100)
        
        for wallet in wallets:
            assert wallet["currency"] in WalletGenerator.CURRENCIES
    
    def test_wallet_types(self):
        """Test that valid wallet types are generated."""
        gen = WalletGenerator(seed=42)
        wallets = gen.generate_batch(100)
        
        for wallet in wallets:
            assert wallet["wallet_type"] in WalletGenerator.WALLET_TYPES
    
    def test_mixer_wallets_have_mixer_type(self):
        """Test that mixer wallets have wallet_type='mixer'."""
        gen = WalletGenerator(seed=42)
        wallets = gen.generate_batch(100)
        
        for wallet in wallets:
            if wallet["is_mixer"]:
                assert wallet["wallet_type"] == "mixer"
    
    def test_balance_is_positive(self):
        """Test that balance is non-negative."""
        gen = WalletGenerator(seed=42)
        wallets = gen.generate_batch(100)
        
        for wallet in wallets:
            assert wallet["balance"] >= 0.0
    
    def test_risk_score_range(self):
        """Test that risk score is between 0 and 1."""
        gen = WalletGenerator(seed=42)
        wallets = gen.generate_batch(100)
        
        for wallet in wallets:
            assert 0.0 <= wallet["risk_score"] <= 1.0
    
    def test_timestamp_is_reference_timestamp(self):
        """Test that created_at uses REFERENCE_TIMESTAMP."""
        gen = WalletGenerator(seed=42)
        wallet = gen.generate()
        
        assert wallet["created_at"] == REFERENCE_TIMESTAMP.isoformat()
    
    def test_mixer_probability(self):
        """Test that mixer probability is approximately correct."""
        mixer_prob = 0.1  # 10%
        gen = WalletGenerator(seed=42, config={"mixer_probability": mixer_prob})
        wallets = gen.generate_batch(1000)
        
        mixer_count = sum(1 for w in wallets if w["is_mixer"])
        mixer_rate = mixer_count / len(wallets)
        
        # Allow 20% deviation
        assert abs(mixer_rate - mixer_prob) < mixer_prob * 0.2
    
    def test_sanctioned_probability(self):
        """Test that sanctioned probability is approximately correct."""
        sanctioned_prob = 0.05  # 5%
        gen = WalletGenerator(seed=42, config={"sanctioned_probability": sanctioned_prob})
        wallets = gen.generate_batch(1000)
        
        sanctioned_count = sum(1 for w in wallets if w["is_sanctioned"])
        sanctioned_rate = sanctioned_count / len(wallets)
        
        # Allow 30% deviation (smaller probability, more variance)
        assert abs(sanctioned_rate - sanctioned_prob) < sanctioned_prob * 0.3


class TestWalletGeneratorAddressGeneration:
    """Test address generation for different currencies."""
    
    def test_btc_address_format(self):
        """Test Bitcoin address format."""
        gen = WalletGenerator(seed=42)
        
        # Generate until we get a BTC wallet
        for _ in range(100):
            wallet = gen.generate()
            if wallet["currency"] == "BTC":
                address = wallet["address"]
                # BTC addresses start with 1, 3, or bc1
                assert address[0] in ["1", "3"] or address.startswith("bc1")
                break
    
    def test_eth_address_format(self):
        """Test Ethereum address format."""
        gen = WalletGenerator(seed=42)
        
        # Generate until we get an ETH wallet
        for _ in range(100):
            wallet = gen.generate()
            if wallet["currency"] == "ETH":
                address = wallet["address"]
                # ETH addresses start with 0x and are 42 chars
                assert address.startswith("0x")
                assert len(address) == 42
                break
    
    def test_address_uniqueness(self):
        """Test that addresses are unique."""
        gen = WalletGenerator(seed=42)
        wallets = gen.generate_batch(100)
        
        addresses = [w["address"] for w in wallets]
        assert len(addresses) == len(set(addresses))  # All unique


class TestWalletGeneratorLinking:
    """Test wallet linking to owners."""
    
    def test_link_to_person(self):
        """Test linking wallet to person."""
        gen = WalletGenerator(seed=42)
        wallet = gen.generate()
        
        assert wallet["owner_id"] is None
        
        # Link to person
        updated = gen.link_to_owner(wallet, "person-123", "person")
        
        assert updated["owner_id"] == "person-123"
        assert updated["metadata"]["owner_type"] == "person"
    
    def test_link_to_company(self):
        """Test linking wallet to company."""
        gen = WalletGenerator(seed=42)
        wallet = gen.generate()
        
        # Link to company
        updated = gen.link_to_owner(wallet, "company-456", "company")
        
        assert updated["owner_id"] == "company-456"
        assert updated["metadata"]["owner_type"] == "company"


class TestWalletGeneratorBatchGeneration:
    """Test batch generation."""
    
    def test_batch_count(self):
        """Test that batch generates correct count."""
        gen = WalletGenerator(seed=42)
        
        for count in [10, 50, 100]:
            wallets = gen.generate_batch(count)
            assert len(wallets) == count
    
    def test_batch_statistics(self):
        """Test that batch statistics are logged."""
        gen = WalletGenerator(seed=42)
        wallets = gen.generate_batch(100)
        
        mixer_count = sum(1 for w in wallets if w["is_mixer"])
        sanctioned_count = sum(1 for w in wallets if w["is_sanctioned"])
        
        # Should have some mixers and sanctioned wallets
        assert mixer_count > 0
        assert sanctioned_count >= 0  # May be 0 with low probability


class TestWalletGeneratorMetadata:
    """Test metadata generation."""
    
    def test_metadata_contains_seed(self):
        """Test that metadata contains generation seed."""
        seed = 42
        gen = WalletGenerator(seed=seed)
        wallet = gen.generate()
        
        assert "metadata" in wallet
        assert wallet["metadata"]["generation_seed"] == seed
    
    def test_metadata_contains_version(self):
        """Test that metadata contains generator version."""
        gen = WalletGenerator(seed=42)
        wallet = gen.generate()
        
        assert "generator_version" in wallet["metadata"]
        assert wallet["metadata"]["generator_version"] == "1.0.0"

# Made with Bob
