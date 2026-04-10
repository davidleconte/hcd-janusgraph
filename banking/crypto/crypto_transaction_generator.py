"""
Cryptocurrency Transaction Generator
=====================================

Generates deterministic cryptocurrency transactions for AML/compliance testing.

Features:
- 100% deterministic with seed
- Transaction types (transfer, exchange, purchase, sale)
- Fee calculation
- Confirmation tracking
- Risk scoring
- Suspicious activity flagging

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-10
Phase: 7.1 - Crypto/Digital Assets
"""

import logging
from typing import Any, Dict, List, Optional

from banking.data_generators.core.base_generator import BaseGenerator
from banking.data_generators.utils.deterministic import REFERENCE_TIMESTAMP, seeded_uuid_hex

logger = logging.getLogger(__name__)


class CryptoTransactionGenerator(BaseGenerator[Dict[str, Any]]):
    """
    Generate deterministic cryptocurrency transactions.
    
    All transactions are fully reproducible with the same seed.
    Requires a list of wallets to generate transactions between them.
    
    Example:
        >>> wallets = wallet_gen.generate_batch(100)
        >>> tx_gen = CryptoTransactionGenerator(wallets, seed=42)
        >>> transaction = tx_gen.generate()
        >>> print(transaction["transaction_id"])  # Always same with seed=42
        'ctx-ABC123DEF456'
    """
    
    # Transaction types
    TRANSACTION_TYPES = ["transfer", "exchange", "purchase", "sale", "deposit", "withdrawal"]
    
    # Fee ranges by currency (as percentage of amount)
    FEE_RANGES = {
        "BTC": (0.0001, 0.001),
        "ETH": (0.0005, 0.005),
        "USDT": (0.0001, 0.001),
        "USDC": (0.0001, 0.001),
        "XRP": (0.00001, 0.0001),
        "ADA": (0.0001, 0.001),
        "SOL": (0.0001, 0.001),
        "DOT": (0.0001, 0.001),
        "MATIC": (0.0001, 0.001),
        "AVAX": (0.0001, 0.001)
    }
    
    def __init__(
        self,
        wallets: List[Dict[str, Any]],
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize transaction generator.
        
        Args:
            wallets: List of wallet dictionaries to generate transactions between
            seed: Random seed for reproducibility (42, 123, or 999)
            locale: Faker locale (default: en_US)
            config: Additional configuration
        """
        super().__init__(seed=seed, locale=locale, config=config)
        
        if not wallets:
            raise ValueError("wallets list cannot be empty")
        
        self.wallets = wallets
        
        # Configuration
        self.suspicious_probability = config.get("suspicious_probability", 0.1) if config else 0.1
        
        logger.info(
            f"CryptoTransactionGenerator initialized with seed={seed}, "
            f"{len(wallets)} wallets, "
            f"suspicious_prob={self.suspicious_probability}"
        )
    
    def generate(self) -> Dict[str, Any]:
        """
        Generate a single cryptocurrency transaction.
        
        Returns:
            Dictionary with transaction data:
            - transaction_id: Unique deterministic ID
            - tx_hash: Blockchain transaction hash
            - from_wallet: Source wallet ID
            - to_wallet: Destination wallet ID
            - amount: Transaction amount
            - currency: Cryptocurrency type
            - fee: Transaction fee
            - timestamp: Transaction timestamp (REFERENCE_TIMESTAMP)
            - confirmations: Number of confirmations
            - block_height: Block height
            - transaction_type: Type of transaction
            - is_suspicious: Whether transaction is suspicious
            - risk_score: Risk score (0.0-1.0)
            - metadata: Additional metadata
        """
        # Generate deterministic transaction ID
        transaction_id = seeded_uuid_hex("ctx-", seed=self.seed)
        
        # Select from and to wallets (ensure different wallets)
        from_wallet = self.faker.random_element(self.wallets)
        to_wallet = self.faker.random_element(
            [w for w in self.wallets if w["wallet_id"] != from_wallet["wallet_id"]]
        )
        
        # Use currency from source wallet
        currency = from_wallet["currency"]
        
        # Generate transaction amount
        amount = self._generate_amount(from_wallet, currency)
        
        # Calculate fee
        fee = self._calculate_fee(amount, currency)
        
        # Generate transaction type
        transaction_type = self.faker.random_element(self.TRANSACTION_TYPES)
        
        # Determine if suspicious
        is_suspicious = self._is_suspicious(from_wallet, to_wallet, amount)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(
            from_wallet, to_wallet, amount, is_suspicious
        )
        
        # Generate blockchain data
        tx_hash = self._generate_tx_hash()
        confirmations = self.faker.random_int(0, 100)
        block_height = self.faker.random_int(700000, 800000)
        
        transaction = {
            "transaction_id": transaction_id,
            "tx_hash": tx_hash,
            "from_wallet": from_wallet["wallet_id"],
            "to_wallet": to_wallet["wallet_id"],
            "amount": amount,
            "currency": currency,
            "fee": fee,
            "timestamp": REFERENCE_TIMESTAMP.isoformat(),
            "confirmations": confirmations,
            "block_height": block_height,
            "transaction_type": transaction_type,
            "is_suspicious": is_suspicious,
            "risk_score": risk_score,
            "metadata": {
                "generation_seed": self.seed,
                "generator_version": "1.0.0",
                "from_wallet_type": from_wallet["wallet_type"],
                "to_wallet_type": to_wallet["wallet_type"]
            }
        }
        
        self.generated_count += 1
        
        return transaction
    
    def _generate_amount(
        self,
        from_wallet: Dict[str, Any],
        currency: str
    ) -> float:
        """
        Generate transaction amount based on wallet balance and currency.
        
        Args:
            from_wallet: Source wallet
            currency: Cryptocurrency type
            
        Returns:
            Transaction amount
        """
        # Amount ranges by currency
        amount_ranges = {
            "BTC": (0.001, 10.0),
            "ETH": (0.01, 100.0),
            "USDT": (10.0, 100000.0),
            "USDC": (10.0, 100000.0),
            "XRP": (10.0, 10000.0),
            "ADA": (10.0, 10000.0),
            "SOL": (0.1, 1000.0),
            "DOT": (1.0, 1000.0),
            "MATIC": (10.0, 10000.0),
            "AVAX": (0.1, 1000.0)
        }
        
        min_amt, max_amt = amount_ranges.get(currency, (0.001, 10.0))
        
        # Don't exceed wallet balance (if balance is set)
        balance = from_wallet.get("balance", max_amt)
        if balance > 0:
            max_amt = min(max_amt, balance * 0.9)  # Use up to 90% of balance
        
        amount = self.faker.random.uniform(min_amt, max_amt)
        
        # Round to 8 decimal places (standard for crypto)
        return round(amount, 8)
    
    def _calculate_fee(self, amount: float, currency: str) -> float:
        """
        Calculate transaction fee.
        
        Args:
            amount: Transaction amount
            currency: Cryptocurrency type
            
        Returns:
            Transaction fee
        """
        fee_min, fee_max = self.FEE_RANGES.get(currency, (0.0001, 0.001))
        fee_percentage = self.faker.random.uniform(fee_min, fee_max)
        fee = amount * fee_percentage
        
        return round(fee, 8)
    
    def _generate_tx_hash(self) -> str:
        """
        Generate deterministic transaction hash.
        
        Returns:
            64-character hex string (SHA-256 style)
        """
        hex_chars = "0123456789abcdef"
        tx_hash = "0x" + "".join(
            self.faker.random.choice(hex_chars) for _ in range(64)
        )
        return tx_hash
    
    def _is_suspicious(
        self,
        from_wallet: Dict[str, Any],
        to_wallet: Dict[str, Any],
        amount: float
    ) -> bool:
        """
        Determine if transaction is suspicious.
        
        Args:
            from_wallet: Source wallet
            to_wallet: Destination wallet
            amount: Transaction amount
            
        Returns:
            True if suspicious
        """
        # Transactions involving mixers are suspicious
        if from_wallet.get("is_mixer") or to_wallet.get("is_mixer"):
            return True
        
        # Transactions involving sanctioned wallets are suspicious
        if from_wallet.get("is_sanctioned") or to_wallet.get("is_sanctioned"):
            return True
        
        # Large amounts are suspicious
        if amount > 1000:  # Threshold varies by currency
            return True
        
        # Random suspicious transactions
        if self.faker.random.random() < self.suspicious_probability:
            return True
        
        return False
    
    def _calculate_risk_score(
        self,
        from_wallet: Dict[str, Any],
        to_wallet: Dict[str, Any],
        amount: float,
        is_suspicious: bool
    ) -> float:
        """
        Calculate transaction risk score.
        
        Args:
            from_wallet: Source wallet
            to_wallet: Destination wallet
            amount: Transaction amount
            is_suspicious: Whether transaction is suspicious
            
        Returns:
            Risk score (0.0-1.0)
        """
        score = 0.0
        
        # Wallet risk scores
        score += from_wallet.get("risk_score", 0.0) * 0.3
        score += to_wallet.get("risk_score", 0.0) * 0.3
        
        # Suspicious flag
        if is_suspicious:
            score += 0.4
        
        # Amount risk (higher amounts = higher risk)
        if amount > 1000:
            score += 0.2
        elif amount > 100:
            score += 0.1
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def generate_batch(
        self,
        count: int,
        show_progress: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate a batch of transactions.
        
        Args:
            count: Number of transactions to generate
            show_progress: Whether to show progress
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        
        for i in range(count):
            transaction = self.generate()
            transactions.append(transaction)
            
            if show_progress and (i + 1) % 100 == 0:
                logger.info(f"Generated {i + 1}/{count} transactions")
        
        logger.info(
            f"Generated {count} transactions: "
            f"{sum(1 for tx in transactions if tx['is_suspicious'])} suspicious"
        )
        
        return transactions

# Made with Bob
