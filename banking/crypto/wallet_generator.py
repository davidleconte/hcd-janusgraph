"""
Cryptocurrency Wallet Generator
================================

Generates deterministic cryptocurrency wallets for AML/compliance testing.

Features:
- 100% deterministic with seed
- Multiple currencies (BTC, ETH, USDT, XRP, ADA, etc.)
- Wallet types (hot, cold, custodial, non-custodial, mixer)
- Risk scoring
- Sanctions screening flags

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-10
Phase: 7.1 - Crypto/Digital Assets
"""

import logging
from typing import Any, Dict, List, Optional

from banking.data_generators.core.base_generator import BaseGenerator
from banking.data_generators.utils.deterministic import REFERENCE_TIMESTAMP, seeded_uuid_hex

logger = logging.getLogger(__name__)


class WalletGenerator(BaseGenerator[Dict[str, Any]]):
    """
    Generate deterministic cryptocurrency wallets.
    
    All wallets are fully reproducible with the same seed.
    Uses seeded_uuid_hex() for wallet IDs and deterministic address generation.
    
    Example:
        >>> gen = WalletGenerator(seed=42)
        >>> wallet = gen.generate()
        >>> print(wallet["wallet_id"])  # Always same with seed=42
        'wallet-ABC123DEF456'
    """
    
    # Supported cryptocurrencies
    CURRENCIES = ["BTC", "ETH", "USDT", "USDC", "XRP", "ADA", "SOL", "DOT", "MATIC", "AVAX"]
    
    # Wallet types
    WALLET_TYPES = ["hot", "cold", "custodial", "non-custodial", "exchange", "mixer"]
    
    # Address prefixes by currency
    ADDRESS_PREFIXES = {
        "BTC": ["1", "3", "bc1"],
        "ETH": ["0x"],
        "USDT": ["0x"],  # ERC-20
        "USDC": ["0x"],  # ERC-20
        "XRP": ["r"],
        "ADA": ["addr1"],
        "SOL": [""],  # Base58
        "DOT": ["1"],
        "MATIC": ["0x"],
        "AVAX": ["0x"]
    }
    
    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize wallet generator.
        
        Args:
            seed: Random seed for reproducibility (42, 123, or 999)
            locale: Faker locale (default: en_US)
            config: Additional configuration
        """
        super().__init__(seed=seed, locale=locale, config=config)
        
        # Configuration
        self.mixer_probability = config.get("mixer_probability", 0.05) if config else 0.05
        self.sanctioned_probability = config.get("sanctioned_probability", 0.02) if config else 0.02
        
        logger.info(
            f"WalletGenerator initialized with seed={seed}, "
            f"mixer_prob={self.mixer_probability}, "
            f"sanctioned_prob={self.sanctioned_probability}"
        )
    
    def generate(self) -> Dict[str, Any]:
        """
        Generate a single cryptocurrency wallet.
        
        Returns:
            Dictionary with wallet data:
            - wallet_id: Unique deterministic ID
            - address: Blockchain address
            - currency: Cryptocurrency type
            - wallet_type: Type of wallet
            - owner_id: Link to person/company (None initially)
            - balance: Current balance
            - created_at: Creation timestamp (REFERENCE_TIMESTAMP)
            - risk_score: Risk score (0.0-1.0)
            - is_mixer: Whether this is a mixer/tumbler
            - is_sanctioned: Whether wallet is on sanctions list
            - metadata: Additional metadata
        """
        # Generate deterministic wallet ID
        wallet_id = seeded_uuid_hex("wallet-", seed=self.seed)
        
        # Select currency
        currency = self.faker.random_element(self.CURRENCIES)
        
        # Determine if mixer or sanctioned (deterministic)
        is_mixer = self.faker.random.random() < self.mixer_probability
        is_sanctioned = self.faker.random.random() < self.sanctioned_probability
        
        # Select wallet type (mixers are always "mixer" type)
        if is_mixer:
            wallet_type = "mixer"
        else:
            wallet_type = self.faker.random_element(
                [t for t in self.WALLET_TYPES if t != "mixer"]
            )
        
        # Generate deterministic address
        address = self._generate_address(currency)
        
        # Generate balance (mixers have higher balances)
        if is_mixer:
            balance = round(self.faker.random.uniform(100, 10000), 8)
        else:
            balance = round(self.faker.random.uniform(0, 100), 8)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(is_mixer, is_sanctioned, wallet_type)
        
        wallet = {
            "wallet_id": wallet_id,
            "address": address,
            "currency": currency,
            "wallet_type": wallet_type,
            "owner_id": None,  # Will be linked later
            "balance": balance,
            "created_at": REFERENCE_TIMESTAMP.isoformat(),
            "risk_score": risk_score,
            "is_mixer": is_mixer,
            "is_sanctioned": is_sanctioned,
            "metadata": {
                "generation_seed": self.seed,
                "generator_version": "1.0.0"
            }
        }
        
        self.generated_count += 1
        
        return wallet
    
    def _generate_address(self, currency: str) -> str:
        """
        Generate deterministic blockchain address.
        
        Args:
            currency: Cryptocurrency type
            
        Returns:
            Deterministic blockchain address
        """
        prefixes = self.ADDRESS_PREFIXES.get(currency, ["0x"])
        prefix = self.faker.random_element(prefixes)
        
        # Generate deterministic hex string
        if currency in ["BTC", "XRP", "ADA", "DOT"]:
            # Base58-like addresses (25-35 chars)
            length = self.faker.random_int(25, 35)
            chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
            address_body = "".join(
                self.faker.random.choice(chars) for _ in range(length)
            )
        else:
            # Hex addresses (40 chars for ETH-like)
            hex_chars = "0123456789abcdef"
            address_body = "".join(
                self.faker.random.choice(hex_chars) for _ in range(40)
            )
        
        return f"{prefix}{address_body}"
    
    def _calculate_risk_score(
        self,
        is_mixer: bool,
        is_sanctioned: bool,
        wallet_type: str
    ) -> float:
        """
        Calculate wallet risk score.
        
        Args:
            is_mixer: Whether wallet is a mixer
            is_sanctioned: Whether wallet is sanctioned
            wallet_type: Type of wallet
            
        Returns:
            Risk score (0.0-1.0)
        """
        score = 0.0
        
        # Sanctioned wallets are highest risk
        if is_sanctioned:
            score += 0.8
        
        # Mixers are high risk
        if is_mixer:
            score += 0.6
        
        # Wallet type risk
        type_risk = {
            "mixer": 0.6,
            "exchange": 0.2,
            "hot": 0.3,
            "cold": 0.1,
            "custodial": 0.2,
            "non-custodial": 0.3
        }
        score += type_risk.get(wallet_type, 0.2)
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def generate_batch(
        self,
        count: int,
        show_progress: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate a batch of wallets.
        
        Args:
            count: Number of wallets to generate
            show_progress: Whether to show progress
            
        Returns:
            List of wallet dictionaries
        """
        wallets = []
        
        for i in range(count):
            wallet = self.generate()
            wallets.append(wallet)
            
            if show_progress and (i + 1) % 100 == 0:
                logger.info(f"Generated {i + 1}/{count} wallets")
        
        logger.info(
            f"Generated {count} wallets: "
            f"{sum(1 for w in wallets if w['is_mixer'])} mixers, "
            f"{sum(1 for w in wallets if w['is_sanctioned'])} sanctioned"
        )
        
        return wallets
    
    def link_to_owner(
        self,
        wallet: Dict[str, Any],
        owner_id: str,
        owner_type: str = "person"
    ) -> Dict[str, Any]:
        """
        Link wallet to an owner (person or company).
        
        Args:
            wallet: Wallet dictionary
            owner_id: Owner's ID
            owner_type: Type of owner ("person" or "company")
            
        Returns:
            Updated wallet dictionary
        """
        wallet["owner_id"] = owner_id
        wallet["metadata"]["owner_type"] = owner_type
        
        return wallet

# Made with Bob
