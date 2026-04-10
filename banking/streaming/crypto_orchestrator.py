"""
Crypto Streaming Orchestrator
==============================

Orchestrates cryptocurrency data generation and streaming to Pulsar.
Integrates wallet generation, transaction generation, pattern injection,
and event publishing.

Author: AI Assistant
Date: 2026-04-10
Phase: 7.2 - Crypto Streaming Integration
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from banking.crypto import (
    CryptoTransactionGenerator,
    MixerDetector,
    SanctionsScreener,
    WalletGenerator,
)
from banking.data_generators.patterns import CryptoMixerPatternGenerator
from banking.streaming.crypto_events import (
    create_crypto_transaction_event,
    create_mixer_detection_event,
    create_sanctions_screening_event,
    create_wallet_event,
)
from banking.streaming.producer import EntityProducer

logger = logging.getLogger(__name__)


class CryptoStreamingOrchestrator:
    """
    Orchestrate crypto data generation and streaming.
    
    Features:
    - Generate wallets and transactions
    - Inject mixer patterns
    - Run mixer detection
    - Run sanctions screening
    - Publish all events to Pulsar
    - Track statistics
    
    Example:
        >>> config = {
        ...     "seed": 42,
        ...     "wallet_count": 100,
        ...     "transaction_count": 500,
        ...     "mixer_pattern_count": 10,
        ...     "pulsar_url": "pulsar://localhost:6650"
        ... }
        >>> orchestrator = CryptoStreamingOrchestrator(config)
        >>> stats = orchestrator.run()
        >>> print(f"Published {stats['events_published']} events")
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        use_mock_producer: bool = False,
    ):
        """
        Initialize the orchestrator.
        
        Args:
            config: Configuration dictionary with:
                - seed: Random seed for reproducibility
                - wallet_count: Number of wallets to generate
                - transaction_count: Number of transactions to generate
                - mixer_pattern_count: Number of mixer patterns to inject
                - pulsar_url: Pulsar broker URL
                - output_dir: Optional output directory for exports
            use_mock_producer: Use mock producer for testing (no Pulsar required)
        """
        self.config = config
        self.seed = config.get("seed", 42)
        self.wallet_count = config.get("wallet_count", 100)
        self.transaction_count = config.get("transaction_count", 500)
        self.mixer_pattern_count = config.get("mixer_pattern_count", 10)
        self.pulsar_url = config.get("pulsar_url", "pulsar://localhost:6650")
        self.output_dir = config.get("output_dir")
        self.use_mock_producer = use_mock_producer
        
        # Initialize generators
        self.wallet_gen = WalletGenerator(seed=self.seed)
        self.pattern_gen = CryptoMixerPatternGenerator(seed=self.seed)
        self.mixer_detector = MixerDetector()
        self.sanctions_screener = SanctionsScreener()
        
        # Initialize producer
        if use_mock_producer:
            from banking.streaming.tests.mock_producer import MockProducer
            self.producer = MockProducer()
        else:
            self.producer = EntityProducer(pulsar_url=self.pulsar_url)
        
        # Statistics
        self.stats = {
            "wallets_generated": 0,
            "transactions_generated": 0,
            "patterns_injected": 0,
            "mixer_detections": 0,
            "sanctions_screenings": 0,
            "events_published": 0,
            "errors": 0,
        }
    
    def run(self) -> Dict[str, Any]:
        """
        Run the complete orchestration workflow.
        
        Returns:
            Statistics dictionary
        """
        logger.info("Starting crypto streaming orchestration")
        logger.info(f"Configuration: {self.config}")
        
        try:
            # Step 1: Generate wallets
            logger.info(f"Step 1: Generating {self.wallet_count} wallets...")
            wallets = self._generate_wallets()
            self.stats["wallets_generated"] = len(wallets)
            
            # Step 2: Generate transactions
            logger.info(f"Step 2: Generating {self.transaction_count} transactions...")
            transactions = self._generate_transactions(wallets)
            
            # Step 3: Inject mixer patterns
            logger.info(f"Step 3: Injecting {self.mixer_pattern_count} mixer patterns...")
            pattern_result = self._inject_patterns(wallets, transactions)
            self.stats["patterns_injected"] = len(pattern_result["patterns"])
            
            # Update transaction count after pattern injection (patterns add transactions)
            self.stats["transactions_generated"] = len(transactions)
            
            # Step 4: Run mixer detection
            logger.info("Step 4: Running mixer detection...")
            mixer_results = self._run_mixer_detection(wallets)
            self.stats["mixer_detections"] = len(mixer_results)
            
            # Step 5: Run sanctions screening
            logger.info("Step 5: Running sanctions screening...")
            sanctions_results = self._run_sanctions_screening(wallets)
            self.stats["sanctions_screenings"] = len(sanctions_results)
            
            # Step 6: Publish all events
            logger.info("Step 6: Publishing events to Pulsar...")
            self._publish_events(
                wallets,
                transactions,
                mixer_results,
                sanctions_results
            )
            
            logger.info("Orchestration complete")
            logger.info(f"Statistics: {self.stats}")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            self.stats["errors"] += 1
            raise
        finally:
            # Close producer
            if hasattr(self.producer, "close"):
                self.producer.close()
    
    def _generate_wallets(self) -> List[Dict[str, Any]]:
        """Generate cryptocurrency wallets."""
        wallets = self.wallet_gen.generate_batch(self.wallet_count)
        logger.info(f"Generated {len(wallets)} wallets")
        return wallets
    
    def _generate_transactions(
        self,
        wallets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate cryptocurrency transactions."""
        tx_gen = CryptoTransactionGenerator(wallets, seed=self.seed)
        transactions = tx_gen.generate_batch(self.transaction_count)
        logger.info(f"Generated {len(transactions)} transactions")
        return transactions
    
    def _inject_patterns(
        self,
        wallets: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Inject mixer patterns into transactions."""
        pattern_result = self.pattern_gen.inject_pattern(
            wallets=wallets,
            transactions=transactions,
            pattern_count=self.mixer_pattern_count,
            pattern_type=None  # Random pattern types
        )
        logger.info(
            f"Injected {len(pattern_result['patterns'])} patterns, "
            f"affected {len(pattern_result['affected_transactions'])} transactions"
        )
        return pattern_result
    
    def _run_mixer_detection(
        self,
        wallets: List[Dict[str, Any]]
    ) -> List[Any]:
        """Run mixer detection on all wallets."""
        # Create wallet data map
        wallet_data_map = {}
        for wallet in wallets:
            wallet_data_map[wallet["wallet_id"]] = {
                "is_mixer": wallet["is_mixer"],
                "mixer_paths": []  # Would be populated from graph traversal
            }
        
        # Batch detect
        results = self.mixer_detector.batch_detect(
            wallet_ids=[w["wallet_id"] for w in wallets],
            wallet_data_map=wallet_data_map
        )
        
        logger.info(f"Completed mixer detection for {len(results)} wallets")
        return results
    
    def _run_sanctions_screening(
        self,
        wallets: List[Dict[str, Any]]
    ) -> List[Any]:
        """Run sanctions screening on all wallets."""
        # Create wallet data map with random jurisdictions
        import random
        random.seed(self.seed)
        jurisdictions = ["US", "GB", "FR", "DE", "JP", "CN", "IR", "KP", "SY", "RU"]
        
        wallet_data_map = {}
        for wallet in wallets:
            wallet_data_map[wallet["wallet_id"]] = {
                "jurisdiction": random.choice(jurisdictions),
                "is_mixer": wallet["is_mixer"],
                "high_value_transactions": False,
                "rapid_movement": False,
            }
        
        # Batch screen
        results = self.sanctions_screener.batch_screen(
            wallet_ids=[w["wallet_id"] for w in wallets],
            wallet_data_map=wallet_data_map
        )
        
        logger.info(f"Completed sanctions screening for {len(results)} wallets")
        return results
    
    def _publish_events(
        self,
        wallets: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        mixer_results: List[Any],
        sanctions_results: List[Any]
    ) -> None:
        """Publish all events to Pulsar."""
        events_published = 0
        
        # Publish wallet events
        logger.info(f"Publishing {len(wallets)} wallet events...")
        for wallet in wallets:
            event = create_wallet_event(
                wallet_id=wallet["wallet_id"],
                wallet_data=wallet,
                source="orchestrator"
            )
            self.producer.send(event)
            events_published += 1
        
        # Publish transaction events
        logger.info(f"Publishing {len(transactions)} transaction events...")
        for tx in transactions:
            event = create_crypto_transaction_event(
                transaction_id=tx["transaction_id"],
                transaction_data=tx,
                source="orchestrator"
            )
            self.producer.send(event)
            events_published += 1
        
        # Publish mixer detection events
        logger.info(f"Publishing {len(mixer_results)} mixer detection events...")
        for result in mixer_results:
            event = create_mixer_detection_event(
                wallet_id=result.wallet_id,
                detection_result=result.to_dict(),
                source="orchestrator"
            )
            self.producer.send(event)
            events_published += 1
        
        # Publish sanctions screening events
        logger.info(f"Publishing {len(sanctions_results)} sanctions screening events...")
        for result in sanctions_results:
            event = create_sanctions_screening_event(
                wallet_id=result.wallet_id,
                screening_result=result.to_dict(),
                source="orchestrator"
            )
            self.producer.send(event)
            events_published += 1
        
        self.stats["events_published"] = events_published
        logger.info(f"Published {events_published} events to Pulsar")

# Made with Bob
