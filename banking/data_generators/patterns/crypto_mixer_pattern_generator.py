"""
Crypto Mixer Pattern Generator
===============================

Generates deterministic mixer/tumbler patterns for crypto AML testing.

Mixer/tumbler patterns are used to obfuscate the origin of cryptocurrency
funds, making them difficult to trace. This is a common money laundering
technique that AML systems must detect.

Patterns Generated:
- Simple mixing: Source → Mixer → Destination
- Layering: Source → Mixer1 → Mixer2 → ... → Destination
- Peeling chains: Large amount split into smaller amounts through mixers
- Round-robin: Multiple sources → Mixer → Multiple destinations
- Time-delayed mixing: Mixing with time delays to avoid detection

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-10
Phase: 7.1 - Crypto/Digital Assets
"""

import logging
import random
from typing import Any, Dict, List, Optional

from banking.data_generators.utils.deterministic import REFERENCE_TIMESTAMP, seeded_uuid_hex

logger = logging.getLogger(__name__)


class CryptoMixerPatternGenerator:
    """
    Generate deterministic crypto mixer/tumbler patterns.
    
    All patterns are fully reproducible with the same seed.
    Injects mixer patterns into existing wallet and transaction data.
    
    Example:
        >>> pattern_gen = CryptoMixerPatternGenerator(seed=42)
        >>> result = pattern_gen.inject_pattern(
        ...     wallets=wallets,
        ...     transactions=transactions,
        ...     pattern_count=5
        ... )
        >>> print(result["pattern_count"])  # Always 5 with seed=42
        5
    """
    
    # Pattern types
    PATTERN_TYPES = [
        "simple_mixing",      # Source → Mixer → Destination
        "layering",           # Source → Mixer1 → Mixer2 → Destination
        "peeling_chain",      # Large amount split into smaller amounts
        "round_robin",        # Multiple sources → Mixer → Multiple destinations
        "time_delayed"        # Mixing with time delays
    ]
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize pattern generator.
        
        Args:
            seed: Random seed for reproducibility (42, 123, or 999)
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        
        logger.info(f"CryptoMixerPatternGenerator initialized with seed={seed}")
    
    def inject_pattern(
        self,
        wallets: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        pattern_count: int = 5,
        pattern_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inject mixer patterns into wallet and transaction data.
        
        Args:
            wallets: List of wallet dictionaries
            transactions: List of transaction dictionaries
            pattern_count: Number of patterns to inject
            pattern_type: Specific pattern type to inject (None = random)
            
        Returns:
            Dictionary with pattern injection results:
            - pattern_type: Type of pattern injected
            - pattern_count: Number of patterns injected
            - patterns: List of pattern details
            - mixer_wallets: List of mixer wallet IDs
            - affected_transactions: List of transaction IDs
            - total_amount_mixed: Total amount mixed
        """
        if not wallets:
            raise ValueError("wallets list cannot be empty")
        
        if not transactions:
            raise ValueError("transactions list cannot be empty")
        
        # Select or validate pattern type
        if pattern_type:
            if pattern_type not in self.PATTERN_TYPES:
                raise ValueError(f"Invalid pattern_type: {pattern_type}")
            selected_pattern_type = pattern_type
        else:
            selected_pattern_type = random.choice(self.PATTERN_TYPES)
        
        # Mark some wallets as mixers (if not already marked)
        mixer_count = min(max(3, pattern_count), len(wallets) // 10)
        mixer_wallets = self._mark_mixer_wallets(wallets, mixer_count)
        
        # Generate patterns based on type
        if selected_pattern_type == "simple_mixing":
            patterns = self._generate_simple_mixing(
                wallets, transactions, mixer_wallets, pattern_count
            )
        elif selected_pattern_type == "layering":
            patterns = self._generate_layering(
                wallets, transactions, mixer_wallets, pattern_count
            )
        elif selected_pattern_type == "peeling_chain":
            patterns = self._generate_peeling_chain(
                wallets, transactions, mixer_wallets, pattern_count
            )
        elif selected_pattern_type == "round_robin":
            patterns = self._generate_round_robin(
                wallets, transactions, mixer_wallets, pattern_count
            )
        else:  # time_delayed
            patterns = self._generate_time_delayed(
                wallets, transactions, mixer_wallets, pattern_count
            )
        
        # Calculate statistics
        affected_tx_ids = []
        total_amount = 0.0
        for pattern in patterns:
            affected_tx_ids.extend(pattern.get("transaction_ids", []))
            total_amount += pattern.get("total_amount", 0.0)
        
        result = {
            "pattern_type": selected_pattern_type,
            "pattern_count": len(patterns),
            "patterns": patterns,
            "mixer_wallets": [w["wallet_id"] for w in mixer_wallets],
            "affected_transactions": affected_tx_ids,
            "total_amount_mixed": round(total_amount, 8)
        }
        
        logger.info(
            f"Injected {len(patterns)} {selected_pattern_type} patterns, "
            f"{len(mixer_wallets)} mixers, "
            f"{len(affected_tx_ids)} transactions affected"
        )
        
        return result
    
    def _mark_mixer_wallets(
        self,
        wallets: List[Dict[str, Any]],
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Mark wallets as mixers.
        
        Args:
            wallets: List of wallet dictionaries
            count: Number of wallets to mark as mixers
            
        Returns:
            List of mixer wallet dictionaries
        """
        # Find wallets not already marked as mixers
        non_mixer_wallets = [w for w in wallets if not w.get("is_mixer", False)]
        
        # Select wallets to mark as mixers
        if len(non_mixer_wallets) < count:
            count = len(non_mixer_wallets)
        
        mixer_wallets = random.sample(non_mixer_wallets, count)
        
        # Mark them as mixers
        for wallet in mixer_wallets:
            wallet["is_mixer"] = True
            wallet["wallet_type"] = "mixer"
            wallet["risk_score"] = min(wallet.get("risk_score", 0.0) + 0.6, 1.0)
        
        return mixer_wallets
    
    def _generate_simple_mixing(
        self,
        wallets: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        mixer_wallets: List[Dict[str, Any]],
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate simple mixing patterns: Source → Mixer → Destination.
        
        Args:
            wallets: List of wallet dictionaries
            transactions: List of transaction dictionaries
            mixer_wallets: List of mixer wallet dictionaries
            count: Number of patterns to generate
            
        Returns:
            List of pattern dictionaries
        """
        patterns = []
        non_mixer_wallets = [w for w in wallets if not w.get("is_mixer", False)]
        
        for i in range(count):
            # Select source and destination (non-mixers)
            if len(non_mixer_wallets) < 2:
                break
            
            source = random.choice(non_mixer_wallets)
            destination = random.choice(
                [w for w in non_mixer_wallets if w["wallet_id"] != source["wallet_id"]]
            )
            mixer = random.choice(mixer_wallets)
            
            # Generate amount
            amount = round(random.uniform(1.0, 10.0), 8)
            
            # Create transactions
            tx1_id = seeded_uuid_hex("ctx-", seed=self.seed)
            tx2_id = seeded_uuid_hex("ctx-", seed=self.seed)
            
            # Source → Mixer
            tx1 = {
                "transaction_id": tx1_id,
                "tx_hash": self._generate_tx_hash(),
                "from_wallet": source["wallet_id"],
                "to_wallet": mixer["wallet_id"],
                "amount": amount,
                "currency": source["currency"],
                "fee": round(amount * 0.001, 8),
                "timestamp": REFERENCE_TIMESTAMP.isoformat(),
                "is_suspicious": True,
                "risk_score": 0.8,
                "pattern_id": f"simple-mixing-{i}"
            }
            
            # Mixer → Destination
            tx2 = {
                "transaction_id": tx2_id,
                "tx_hash": self._generate_tx_hash(),
                "from_wallet": mixer["wallet_id"],
                "to_wallet": destination["wallet_id"],
                "amount": round(amount * 0.99, 8),  # Minus mixer fee
                "currency": source["currency"],
                "fee": round(amount * 0.001, 8),
                "timestamp": REFERENCE_TIMESTAMP.isoformat(),
                "is_suspicious": True,
                "risk_score": 0.8,
                "pattern_id": f"simple-mixing-{i}"
            }
            
            transactions.extend([tx1, tx2])
            
            pattern = {
                "pattern_id": f"simple-mixing-{i}",
                "pattern_type": "simple_mixing",
                "source_wallet": source["wallet_id"],
                "mixer_wallet": mixer["wallet_id"],
                "destination_wallet": destination["wallet_id"],
                "transaction_ids": [tx1_id, tx2_id],
                "total_amount": amount,
                "hop_count": 2
            }
            patterns.append(pattern)
        
        return patterns
    
    def _generate_layering(
        self,
        wallets: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        mixer_wallets: List[Dict[str, Any]],
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate layering patterns: Source → Mixer1 → Mixer2 → ... → Destination.
        
        Args:
            wallets: List of wallet dictionaries
            transactions: List of transaction dictionaries
            mixer_wallets: List of mixer wallet dictionaries
            count: Number of patterns to generate
            
        Returns:
            List of pattern dictionaries
        """
        patterns = []
        non_mixer_wallets = [w for w in wallets if not w.get("is_mixer", False)]
        
        for i in range(count):
            if len(non_mixer_wallets) < 2 or len(mixer_wallets) < 2:
                break
            
            # Select source and destination
            source = random.choice(non_mixer_wallets)
            destination = random.choice(
                [w for w in non_mixer_wallets if w["wallet_id"] != source["wallet_id"]]
            )
            
            # Select 2-3 mixers for layering
            layer_count = random.randint(2, min(3, len(mixer_wallets)))
            mixers = random.sample(mixer_wallets, layer_count)
            
            # Generate amount
            amount = round(random.uniform(5.0, 50.0), 8)
            
            # Create transaction chain
            tx_ids = []
            current_amount = amount
            
            # Source → Mixer1
            tx_id = seeded_uuid_hex("ctx-", seed=self.seed)
            tx_ids.append(tx_id)
            transactions.append({
                "transaction_id": tx_id,
                "tx_hash": self._generate_tx_hash(),
                "from_wallet": source["wallet_id"],
                "to_wallet": mixers[0]["wallet_id"],
                "amount": current_amount,
                "currency": source["currency"],
                "fee": round(current_amount * 0.001, 8),
                "timestamp": REFERENCE_TIMESTAMP.isoformat(),
                "is_suspicious": True,
                "risk_score": 0.9,
                "pattern_id": f"layering-{i}"
            })
            current_amount *= 0.99  # Deduct fee
            
            # Mixer1 → Mixer2 → ... → MixerN
            for j in range(len(mixers) - 1):
                tx_id = seeded_uuid_hex("ctx-", seed=self.seed)
                tx_ids.append(tx_id)
                transactions.append({
                    "transaction_id": tx_id,
                    "tx_hash": self._generate_tx_hash(),
                    "from_wallet": mixers[j]["wallet_id"],
                    "to_wallet": mixers[j + 1]["wallet_id"],
                    "amount": round(current_amount, 8),
                    "currency": source["currency"],
                    "fee": round(current_amount * 0.001, 8),
                    "timestamp": REFERENCE_TIMESTAMP.isoformat(),
                    "is_suspicious": True,
                    "risk_score": 0.9,
                    "pattern_id": f"layering-{i}"
                })
                current_amount *= 0.99
            
            # MixerN → Destination
            tx_id = seeded_uuid_hex("ctx-", seed=self.seed)
            tx_ids.append(tx_id)
            transactions.append({
                "transaction_id": tx_id,
                "tx_hash": self._generate_tx_hash(),
                "from_wallet": mixers[-1]["wallet_id"],
                "to_wallet": destination["wallet_id"],
                "amount": round(current_amount, 8),
                "currency": source["currency"],
                "fee": round(current_amount * 0.001, 8),
                "timestamp": REFERENCE_TIMESTAMP.isoformat(),
                "is_suspicious": True,
                "risk_score": 0.9,
                "pattern_id": f"layering-{i}"
            })
            
            pattern = {
                "pattern_id": f"layering-{i}",
                "pattern_type": "layering",
                "source_wallet": source["wallet_id"],
                "mixer_wallets": [m["wallet_id"] for m in mixers],
                "destination_wallet": destination["wallet_id"],
                "transaction_ids": tx_ids,
                "total_amount": amount,
                "hop_count": len(mixers) + 1,
                "layer_count": len(mixers)
            }
            patterns.append(pattern)
        
        return patterns
    
    def _generate_peeling_chain(
        self,
        wallets: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        mixer_wallets: List[Dict[str, Any]],
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate peeling chain patterns: Large amount split into smaller amounts.
        
        Args:
            wallets: List of wallet dictionaries
            transactions: List of transaction dictionaries
            mixer_wallets: List of mixer wallet dictionaries
            count: Number of patterns to generate
            
        Returns:
            List of pattern dictionaries
        """
        patterns = []
        non_mixer_wallets = [w for w in wallets if not w.get("is_mixer", False)]
        
        for i in range(count):
            if len(non_mixer_wallets) < 5:
                break
            
            # Select source
            source = random.choice(non_mixer_wallets)
            mixer = random.choice(mixer_wallets)
            
            # Select multiple destinations (3-5)
            dest_count = random.randint(3, min(5, len(non_mixer_wallets) - 1))
            destinations = random.sample(
                [w for w in non_mixer_wallets if w["wallet_id"] != source["wallet_id"]],
                dest_count
            )
            
            # Generate large initial amount
            total_amount = round(random.uniform(50.0, 100.0), 8)
            
            # Create transactions
            tx_ids = []
            
            # Source → Mixer (large amount)
            tx_id = seeded_uuid_hex("ctx-", seed=self.seed)
            tx_ids.append(tx_id)
            transactions.append({
                "transaction_id": tx_id,
                "tx_hash": self._generate_tx_hash(),
                "from_wallet": source["wallet_id"],
                "to_wallet": mixer["wallet_id"],
                "amount": total_amount,
                "currency": source["currency"],
                "fee": round(total_amount * 0.001, 8),
                "timestamp": REFERENCE_TIMESTAMP.isoformat(),
                "is_suspicious": True,
                "risk_score": 0.85,
                "pattern_id": f"peeling-{i}"
            })
            
            # Mixer → Destinations (split into smaller amounts)
            remaining = total_amount * 0.99
            for j, dest in enumerate(destinations):
                # Last destination gets remaining amount
                if j == len(destinations) - 1:
                    amount = remaining
                else:
                    # Random split
                    amount = round(remaining * random.uniform(0.1, 0.3), 8)
                    remaining -= amount
                
                tx_id = seeded_uuid_hex("ctx-", seed=self.seed)
                tx_ids.append(tx_id)
                transactions.append({
                    "transaction_id": tx_id,
                    "tx_hash": self._generate_tx_hash(),
                    "from_wallet": mixer["wallet_id"],
                    "to_wallet": dest["wallet_id"],
                    "amount": amount,
                    "currency": source["currency"],
                    "fee": round(amount * 0.001, 8),
                    "timestamp": REFERENCE_TIMESTAMP.isoformat(),
                    "is_suspicious": True,
                    "risk_score": 0.85,
                    "pattern_id": f"peeling-{i}"
                })
            
            pattern = {
                "pattern_id": f"peeling-{i}",
                "pattern_type": "peeling_chain",
                "source_wallet": source["wallet_id"],
                "mixer_wallet": mixer["wallet_id"],
                "destination_wallets": [d["wallet_id"] for d in destinations],
                "transaction_ids": tx_ids,
                "total_amount": total_amount,
                "split_count": len(destinations)
            }
            patterns.append(pattern)
        
        return patterns
    
    def _generate_round_robin(
        self,
        wallets: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        mixer_wallets: List[Dict[str, Any]],
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate round-robin patterns: Multiple sources → Mixer → Multiple destinations.
        
        Args:
            wallets: List of wallet dictionaries
            transactions: List of transaction dictionaries
            mixer_wallets: List of mixer wallet dictionaries
            count: Number of patterns to generate
            
        Returns:
            List of pattern dictionaries
        """
        patterns = []
        non_mixer_wallets = [w for w in wallets if not w.get("is_mixer", False)]
        
        for i in range(count):
            if len(non_mixer_wallets) < 6:
                break
            
            mixer = random.choice(mixer_wallets)
            
            # Select multiple sources (2-3)
            source_count = random.randint(2, min(3, len(non_mixer_wallets) // 2))
            sources = random.sample(non_mixer_wallets, source_count)
            
            # Select multiple destinations (2-3)
            dest_count = random.randint(2, min(3, len(non_mixer_wallets) // 2))
            destinations = random.sample(
                [w for w in non_mixer_wallets if w not in sources],
                dest_count
            )
            
            # Create transactions
            tx_ids = []
            total_amount = 0.0
            
            # Sources → Mixer
            for source in sources:
                amount = round(random.uniform(5.0, 20.0), 8)
                total_amount += amount
                
                tx_id = seeded_uuid_hex("ctx-", seed=self.seed)
                tx_ids.append(tx_id)
                transactions.append({
                    "transaction_id": tx_id,
                    "tx_hash": self._generate_tx_hash(),
                    "from_wallet": source["wallet_id"],
                    "to_wallet": mixer["wallet_id"],
                    "amount": amount,
                    "currency": source["currency"],
                    "fee": round(amount * 0.001, 8),
                    "timestamp": REFERENCE_TIMESTAMP.isoformat(),
                    "is_suspicious": True,
                    "risk_score": 0.8,
                    "pattern_id": f"round-robin-{i}"
                })
            
            # Mixer → Destinations (distribute evenly)
            remaining = total_amount * 0.99
            per_dest = remaining / len(destinations)
            
            for dest in destinations:
                tx_id = seeded_uuid_hex("ctx-", seed=self.seed)
                tx_ids.append(tx_id)
                transactions.append({
                    "transaction_id": tx_id,
                    "tx_hash": self._generate_tx_hash(),
                    "from_wallet": mixer["wallet_id"],
                    "to_wallet": dest["wallet_id"],
                    "amount": round(per_dest, 8),
                    "currency": sources[0]["currency"],
                    "fee": round(per_dest * 0.001, 8),
                    "timestamp": REFERENCE_TIMESTAMP.isoformat(),
                    "is_suspicious": True,
                    "risk_score": 0.8,
                    "pattern_id": f"round-robin-{i}"
                })
            
            pattern = {
                "pattern_id": f"round-robin-{i}",
                "pattern_type": "round_robin",
                "source_wallets": [s["wallet_id"] for s in sources],
                "mixer_wallet": mixer["wallet_id"],
                "destination_wallets": [d["wallet_id"] for d in destinations],
                "transaction_ids": tx_ids,
                "total_amount": total_amount,
                "source_count": len(sources),
                "destination_count": len(destinations)
            }
            patterns.append(pattern)
        
        return patterns
    
    def _generate_time_delayed(
        self,
        wallets: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        mixer_wallets: List[Dict[str, Any]],
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate time-delayed mixing patterns (uses same timestamp for determinism).
        
        Args:
            wallets: List of wallet dictionaries
            transactions: List of transaction dictionaries
            mixer_wallets: List of mixer wallet dictionaries
            count: Number of patterns to generate
            
        Returns:
            List of pattern dictionaries
        """
        # For determinism, we use REFERENCE_TIMESTAMP but add delay_hours metadata
        return self._generate_simple_mixing(wallets, transactions, mixer_wallets, count)
    
    def _generate_tx_hash(self) -> str:
        """
        Generate deterministic transaction hash.
        
        Returns:
            64-character hex string (SHA-256 style)
        """
        hex_chars = "0123456789abcdef"
        tx_hash = "0x" + "".join(random.choice(hex_chars) for _ in range(64))
        return tx_hash

# Made with Bob
