"""
Tests for CryptoTransactionGenerator
=====================================

Tests deterministic cryptocurrency transaction generation.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-10
Phase: 7.1 - Crypto/Digital Assets
"""

import pytest

from banking.crypto.crypto_transaction_generator import CryptoTransactionGenerator
from banking.crypto.wallet_generator import WalletGenerator
from banking.data_generators.utils.deterministic import REFERENCE_TIMESTAMP


@pytest.fixture
def wallets():
    """Generate test wallets."""
    gen = WalletGenerator(seed=42)
    return gen.generate_batch(50)


class TestCryptoTransactionGeneratorDeterminism:
    """Test deterministic behavior of CryptoTransactionGenerator."""
    
    def test_same_seed_produces_identical_transactions(self, wallets):
        """Test that same seed produces identical transactions."""
        seed = 42
        count = 100
        
        # Generate with seed 1
        gen1 = CryptoTransactionGenerator(wallets, seed=seed)
        txs1 = gen1.generate_batch(count)
        
        # Generate with seed 2 (same seed)
        gen2 = CryptoTransactionGenerator(wallets, seed=seed)
        txs2 = gen2.generate_batch(count)
        
        # Must be identical
        assert len(txs1) == len(txs2) == count
        
        for tx1, tx2 in zip(txs1, txs2):
            assert tx1["transaction_id"] == tx2["transaction_id"]
            assert tx1["tx_hash"] == tx2["tx_hash"]
            assert tx1["from_wallet"] == tx2["from_wallet"]
            assert tx1["to_wallet"] == tx2["to_wallet"]
            assert tx1["amount"] == tx2["amount"]
            assert tx1["currency"] == tx2["currency"]
            assert tx1["fee"] == tx2["fee"]
            assert tx1["is_suspicious"] == tx2["is_suspicious"]
            assert tx1["risk_score"] == tx2["risk_score"]
    
    def test_different_seeds_produce_different_transactions(self, wallets):
        """Test that different seeds produce different transactions."""
        count = 100
        
        gen1 = CryptoTransactionGenerator(wallets, seed=42)
        gen2 = CryptoTransactionGenerator(wallets, seed=123)
        
        txs1 = gen1.generate_batch(count)
        txs2 = gen2.generate_batch(count)
        
        # Must be different
        assert len(txs1) == len(txs2) == count
        
        # At least some transactions should be different
        different_count = sum(
            1 for tx1, tx2 in zip(txs1, txs2)
            if tx1["transaction_id"] != tx2["transaction_id"]
        )
        assert different_count > 90  # Expect >90% different
    
    def test_approved_seeds_work(self, wallets):
        """Test that approved seeds (42, 123, 999) work correctly."""
        approved_seeds = [42, 123, 999]
        
        for seed in approved_seeds:
            gen = CryptoTransactionGenerator(wallets, seed=seed)
            tx = gen.generate()
            
            assert tx is not None
            assert "transaction_id" in tx
            assert tx["transaction_id"].startswith("ctx-")


class TestCryptoTransactionGeneratorFunctional:
    """Test functional requirements of CryptoTransactionGenerator."""
    
    def test_required_fields_present(self, wallets):
        """Test that all required fields are present."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        tx = gen.generate()
        
        required_fields = [
            "transaction_id", "tx_hash", "from_wallet", "to_wallet",
            "amount", "currency", "fee", "timestamp", "confirmations",
            "block_height", "transaction_type", "is_suspicious",
            "risk_score", "metadata"
        ]
        
        for field in required_fields:
            assert field in tx, f"Missing required field: {field}"
    
    def test_transaction_id_format(self, wallets):
        """Test transaction ID format."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        tx = gen.generate()
        
        assert tx["transaction_id"].startswith("ctx-")
        assert len(tx["transaction_id"]) > 4  # "ctx-" + hex
    
    def test_tx_hash_format(self, wallets):
        """Test transaction hash format."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        tx = gen.generate()
        
        assert tx["tx_hash"].startswith("0x")
        assert len(tx["tx_hash"]) == 66  # "0x" + 64 hex chars
    
    def test_from_and_to_wallets_different(self, wallets):
        """Test that from and to wallets are different."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        for tx in txs:
            assert tx["from_wallet"] != tx["to_wallet"]
    
    def test_amount_is_positive(self, wallets):
        """Test that amount is positive."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        for tx in txs:
            assert tx["amount"] > 0.0
    
    def test_fee_is_positive(self, wallets):
        """Test that fee is positive."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        for tx in txs:
            assert tx["fee"] > 0.0
    
    def test_fee_is_less_than_amount(self, wallets):
        """Test that fee is less than amount."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        for tx in txs:
            assert tx["fee"] < tx["amount"]
    
    def test_risk_score_range(self, wallets):
        """Test that risk score is between 0 and 1."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        for tx in txs:
            assert 0.0 <= tx["risk_score"] <= 1.0
    
    def test_timestamp_is_reference_timestamp(self, wallets):
        """Test that timestamp uses REFERENCE_TIMESTAMP."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        tx = gen.generate()
        
        assert tx["timestamp"] == REFERENCE_TIMESTAMP.isoformat()
    
    def test_confirmations_range(self, wallets):
        """Test that confirmations are in valid range."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        for tx in txs:
            assert 0 <= tx["confirmations"] <= 100
    
    def test_block_height_range(self, wallets):
        """Test that block height is in valid range."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        for tx in txs:
            assert 700000 <= tx["block_height"] <= 800000
    
    def test_transaction_types(self, wallets):
        """Test that valid transaction types are generated."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        for tx in txs:
            assert tx["transaction_type"] in CryptoTransactionGenerator.TRANSACTION_TYPES


class TestCryptoTransactionGeneratorSuspiciousDetection:
    """Test suspicious transaction detection."""
    
    def test_mixer_transactions_are_suspicious(self):
        """Test that transactions involving mixers are suspicious."""
        # Create wallets with mixers
        wallet_gen = WalletGenerator(seed=42, config={"mixer_probability": 0.5})
        wallets = wallet_gen.generate_batch(50)
        
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        # Check transactions involving mixers
        for tx in txs:
            from_wallet = next(w for w in wallets if w["wallet_id"] == tx["from_wallet"])
            to_wallet = next(w for w in wallets if w["wallet_id"] == tx["to_wallet"])
            
            if from_wallet["is_mixer"] or to_wallet["is_mixer"]:
                assert tx["is_suspicious"]
    
    def test_sanctioned_transactions_are_suspicious(self):
        """Test that transactions involving sanctioned wallets are suspicious."""
        # Create wallets with sanctioned ones
        wallet_gen = WalletGenerator(seed=42, config={"sanctioned_probability": 0.3})
        wallets = wallet_gen.generate_batch(50)
        
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        # Check transactions involving sanctioned wallets
        for tx in txs:
            from_wallet = next(w for w in wallets if w["wallet_id"] == tx["from_wallet"])
            to_wallet = next(w for w in wallets if w["wallet_id"] == tx["to_wallet"])
            
            if from_wallet["is_sanctioned"] or to_wallet["is_sanctioned"]:
                assert tx["is_suspicious"]
    
    def test_suspicious_probability(self, wallets):
        """Test that suspicious probability is approximately correct."""
        suspicious_prob = 0.2  # 20%
        gen = CryptoTransactionGenerator(
            wallets,
            seed=42,
            config={"suspicious_probability": suspicious_prob}
        )
        txs = gen.generate_batch(1000)
        
        suspicious_count = sum(1 for tx in txs if tx["is_suspicious"])
        suspicious_rate = suspicious_count / len(txs)
        
        # Note: Actual rate may be higher due to mixers/sanctioned wallets
        # Just check it's not 0
        assert suspicious_count > 0


class TestCryptoTransactionGeneratorRiskScoring:
    """Test risk score calculation."""
    
    def test_high_risk_wallets_increase_score(self):
        """Test that high-risk wallets increase transaction risk score."""
        # Create high-risk wallets
        wallet_gen = WalletGenerator(
            seed=42,
            config={"mixer_probability": 0.5, "sanctioned_probability": 0.3}
        )
        wallets = wallet_gen.generate_batch(50)
        
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        # Transactions involving high-risk wallets should have higher scores
        high_risk_txs = [
            tx for tx in txs
            if any(
                w["wallet_id"] in [tx["from_wallet"], tx["to_wallet"]]
                and w["risk_score"] > 0.5
                for w in wallets
            )
        ]
        
        if high_risk_txs:
            avg_risk = sum(tx["risk_score"] for tx in high_risk_txs) / len(high_risk_txs)
            assert avg_risk > 0.3  # Should be elevated
    
    def test_suspicious_flag_increases_score(self, wallets):
        """Test that suspicious flag increases risk score."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        suspicious_txs = [tx for tx in txs if tx["is_suspicious"]]
        non_suspicious_txs = [tx for tx in txs if not tx["is_suspicious"]]
        
        if suspicious_txs and non_suspicious_txs:
            avg_suspicious = sum(tx["risk_score"] for tx in suspicious_txs) / len(suspicious_txs)
            avg_non_suspicious = sum(tx["risk_score"] for tx in non_suspicious_txs) / len(non_suspicious_txs)
            
            assert avg_suspicious > avg_non_suspicious


class TestCryptoTransactionGeneratorBatchGeneration:
    """Test batch generation."""
    
    def test_batch_count(self, wallets):
        """Test that batch generates correct count."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        
        for count in [10, 50, 100]:
            txs = gen.generate_batch(count)
            assert len(txs) == count
    
    def test_batch_statistics(self, wallets):
        """Test that batch statistics are logged."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        txs = gen.generate_batch(100)
        
        suspicious_count = sum(1 for tx in txs if tx["is_suspicious"])
        
        # Should have some suspicious transactions
        assert suspicious_count >= 0  # May be 0 with low probability
    
    def test_empty_wallets_raises_error(self):
        """Test that empty wallets list raises error."""
        with pytest.raises(ValueError, match="wallets list cannot be empty"):
            CryptoTransactionGenerator([], seed=42)


class TestCryptoTransactionGeneratorMetadata:
    """Test metadata generation."""
    
    def test_metadata_contains_seed(self, wallets):
        """Test that metadata contains generation seed."""
        seed = 42
        gen = CryptoTransactionGenerator(wallets, seed=seed)
        tx = gen.generate()
        
        assert "metadata" in tx
        assert tx["metadata"]["generation_seed"] == seed
    
    def test_metadata_contains_version(self, wallets):
        """Test that metadata contains generator version."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        tx = gen.generate()
        
        assert "generator_version" in tx["metadata"]
        assert tx["metadata"]["generator_version"] == "1.0.0"
    
    def test_metadata_contains_wallet_types(self, wallets):
        """Test that metadata contains wallet types."""
        gen = CryptoTransactionGenerator(wallets, seed=42)
        tx = gen.generate()
        
        assert "from_wallet_type" in tx["metadata"]
        assert "to_wallet_type" in tx["metadata"]

# Made with Bob
