"""
StreamingOrchestrator - Pulsar-Integrated Data Generation
=========================================================

Extends MasterOrchestrator to publish generated entities to Apache Pulsar,
enabling dual-path ingestion to JanusGraph and OpenSearch.

Created: 2026-02-06
Week 2: Event Schema & Producers - Integration Phase
"""

import logging
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from datetime import datetime

from banking.data_generators.orchestration.master_orchestrator import (
    MasterOrchestrator, 
    GenerationConfig, 
    GenerationStats
)
from .events import EntityEvent
from .producer import EntityProducer, MockEntityProducer, get_producer
from .entity_converter import convert_entity_to_event

logger = logging.getLogger(__name__)


@dataclass
class StreamingConfig(GenerationConfig):
    """Extended configuration with streaming options."""
    
    # Streaming settings
    enable_streaming: bool = True
    pulsar_url: str = "pulsar://localhost:6650"
    pulsar_namespace: str = "public/banking"
    use_mock_producer: bool = False
    
    # Batching
    streaming_batch_size: int = 100
    flush_after_phase: bool = True


@dataclass 
class StreamingStats(GenerationStats):
    """Extended statistics with streaming metrics."""
    
    events_published: int = 0
    events_failed: int = 0
    events_by_type: Dict[str, int] = field(default_factory=dict)
    streaming_errors: List[str] = field(default_factory=list)


class StreamingOrchestrator(MasterOrchestrator):
    """
    Streaming-enabled orchestrator that publishes entities to Pulsar.
    
    Extends MasterOrchestrator to add Pulsar integration. Each generated
    entity is published as an EntityEvent to the appropriate topic.
    
    Features:
    - Automatic event conversion and publishing
    - Batched publishing for efficiency
    - Mock producer support for testing
    - Comprehensive statistics tracking
    
    Example:
        >>> config = StreamingConfig(
        ...     seed=42,
        ...     person_count=100,
        ...     enable_streaming=True
        ... )
        >>> orchestrator = StreamingOrchestrator(config)
        >>> stats = orchestrator.generate_all()
        >>> print(f"Published {stats.events_published} events")
    """
    
    def __init__(
        self, 
        config: Optional[StreamingConfig] = None,
        producer: Optional[Union[EntityProducer, MockEntityProducer]] = None
    ):
        """
        Initialize StreamingOrchestrator.
        
        Args:
            config: Streaming configuration (uses defaults if None)
            producer: Optional pre-configured producer (useful for testing)
        """
        # Convert GenerationConfig to StreamingConfig if needed
        if config is None:
            config = StreamingConfig()
        elif not isinstance(config, StreamingConfig):
            # Copy GenerationConfig fields to StreamingConfig
            streaming_config = StreamingConfig()
            for field_name in vars(config):
                if hasattr(streaming_config, field_name):
                    setattr(streaming_config, field_name, getattr(config, field_name))
            config = streaming_config
        
        # Initialize parent
        super().__init__(config)
        
        # Override stats with streaming stats
        self.stats = StreamingStats()
        self.config: StreamingConfig = config
        
        # Initialize producer
        self.producer = producer
        self._owns_producer = False
        
        if config.enable_streaming and producer is None:
            self._init_producer()
    
    def _init_producer(self):
        """Initialize the Pulsar producer."""
        try:
            self.producer = get_producer(
                mock=self.config.use_mock_producer,
                pulsar_url=self.config.pulsar_url,
                namespace=self.config.pulsar_namespace
            )
            self._owns_producer = True
            logger.info(f"Initialized producer: {type(self.producer).__name__}")
        except Exception as e:
            logger.warning(f"Failed to initialize Pulsar producer: {e}")
            logger.warning("Falling back to MockEntityProducer")
            self.producer = MockEntityProducer()
            self._owns_producer = True
    
    def _publish_entity(self, entity: Any, event_type: str = 'create') -> bool:
        """
        Publish a single entity to Pulsar.
        
        Args:
            entity: Entity to publish
            event_type: Event type ('create', 'update', 'delete')
        
        Returns:
            True if published successfully, False otherwise
        """
        if not self.config.enable_streaming or self.producer is None:
            return True
        
        try:
            event = convert_entity_to_event(
                entity,
                event_type=event_type,
                source=f"StreamingOrchestrator"
            )
            self.producer.send(event)
            
            # Update statistics
            self.stats.events_published += 1
            entity_type = event.entity_type
            self.stats.events_by_type[entity_type] = \
                self.stats.events_by_type.get(entity_type, 0) + 1
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish entity: {e}")
            self.stats.events_failed += 1
            self.stats.streaming_errors.append(str(e))
            return False
    
    def _publish_entities(self, entities: List[Any], event_type: str = 'create') -> int:
        """
        Publish multiple entities to Pulsar.
        
        Args:
            entities: List of entities to publish
            event_type: Event type for all entities
        
        Returns:
            Number of successfully published entities
        """
        if not self.config.enable_streaming or self.producer is None:
            return len(entities)
        
        published = 0
        for entity in entities:
            if self._publish_entity(entity, event_type):
                published += 1
        
        return published
    
    def _generate_core_entities(self):
        """Generate core entities with streaming."""
        logger.info("\n" + "=" * 80)
        logger.info("Phase 1: Generating Core Entities (with Streaming)")
        logger.info("=" * 80)
        
        # Generate persons
        logger.info(f"Generating {self.config.person_count} persons...")
        for i in range(self.config.person_count):
            person = self.person_gen.generate()
            self.persons.append(person)
            self._publish_entity(person)
            
            if (i + 1) % 100 == 0:
                logger.info(f"  Generated and published {i + 1}/{self.config.person_count} persons")
        
        self.stats.persons_generated = len(self.persons)
        logger.info(f"✓ Generated {self.stats.persons_generated} persons")
        
        # Generate companies
        logger.info(f"\nGenerating {self.config.company_count} companies...")
        for i in range(self.config.company_count):
            company = self.company_gen.generate()
            self.companies.append(company)
            self._publish_entity(company)
            
            if (i + 1) % 10 == 0:
                logger.info(f"  Generated and published {i + 1}/{self.config.company_count} companies")
        
        self.stats.companies_generated = len(self.companies)
        logger.info(f"✓ Generated {self.stats.companies_generated} companies")
        
        # Generate accounts
        logger.info(f"\nGenerating {self.config.account_count} accounts...")
        import random
        for i in range(self.config.account_count):
            if random.random() < 0.8:  # 80% person accounts
                owner = random.choice(self.persons)
                account = self.account_gen.generate(
                    owner_id=owner.id,
                    owner_type="person"
                )
            else:  # 20% company accounts
                owner = random.choice(self.companies)
                account = self.account_gen.generate(
                    owner_id=owner.id,
                    owner_type="company"
                )
            self.accounts.append(account)
            self._publish_entity(account)
            
            if (i + 1) % 100 == 0:
                logger.info(f"  Generated and published {i + 1}/{self.config.account_count} accounts")
        
        self.stats.accounts_generated = len(self.accounts)
        logger.info(f"✓ Generated {self.stats.accounts_generated} accounts")
        
        # Flush after phase
        if self.config.flush_after_phase and self.producer:
            self.producer.flush()
            logger.info("Flushed producer after core entities phase")
    
    def _generate_events(self):
        """Generate events with streaming."""
        logger.info("\n" + "=" * 80)
        logger.info("Phase 2: Generating Events (with Streaming)")
        logger.info("=" * 80)
        
        import random
        
        # Generate transactions
        if self.config.transaction_count > 0:
            logger.info(f"Generating {self.config.transaction_count} transactions...")
            for i in range(self.config.transaction_count):
                from_account = random.choice(self.accounts)
                to_account = random.choice(self.accounts)
                
                transaction = self.transaction_gen.generate(
                    from_account_id=from_account.id,
                    to_account_id=to_account.id
                )
                self.transactions.append(transaction)
                self._publish_entity(transaction)
                
                if (i + 1) % 1000 == 0:
                    logger.info(f"  Generated and published {i + 1}/{self.config.transaction_count} transactions")
            
            self.stats.transactions_generated = len(self.transactions)
            logger.info(f"✓ Generated {self.stats.transactions_generated} transactions")
        
        # Generate communications
        if self.config.communication_count > 0:
            logger.info(f"\nGenerating {self.config.communication_count} communications...")
            for i in range(self.config.communication_count):
                sender = random.choice(self.persons)
                recipient = random.choice(self.persons)
                while recipient.id == sender.id and len(self.persons) > 1:
                    recipient = random.choice(self.persons)
                
                communication = self.communication_gen.generate(
                    sender_id=sender.id,
                    recipient_id=recipient.id
                )
                self.communications.append(communication)
                self._publish_entity(communication)
                
                if (i + 1) % 1000 == 0:
                    logger.info(f"  Generated and published {i + 1}/{self.config.communication_count} communications")
            
            self.stats.communications_generated = len(self.communications)
            logger.info(f"✓ Generated {self.stats.communications_generated} communications")
        
        # Generate trades
        if self.config.trade_count > 0:
            logger.info(f"\nGenerating {self.config.trade_count} trades...")
            for i in range(self.config.trade_count):
                trade = self.trade_gen.generate()
                self.trades.append(trade)
                self._publish_entity(trade)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"  Generated and published {i + 1}/{self.config.trade_count} trades")
            
            self.stats.trades_generated = len(self.trades)
            logger.info(f"✓ Generated {self.stats.trades_generated} trades")
        
        # Generate travel records
        if self.config.travel_count > 0:
            logger.info(f"\nGenerating {self.config.travel_count} travel records...")
            for i in range(self.config.travel_count):
                traveler = random.choice(self.persons)
                travel = self.travel_gen.generate(traveler_id=traveler.person_id)
                self.travels.append(travel)
                self._publish_entity(travel)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"  Generated and published {i + 1}/{self.config.travel_count} travel records")
            
            self.stats.travels_generated = len(self.travels)
            logger.info(f"✓ Generated {self.stats.travels_generated} travel records")
        
        # Generate documents
        if self.config.document_count > 0:
            logger.info(f"\nGenerating {self.config.document_count} documents...")
            for i in range(self.config.document_count):
                document = self.document_gen.generate()
                self.documents.append(document)
                self._publish_entity(document)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"  Generated and published {i + 1}/{self.config.document_count} documents")
            
            self.stats.documents_generated = len(self.documents)
            logger.info(f"✓ Generated {self.stats.documents_generated} documents")
        
        # Flush after phase
        if self.config.flush_after_phase and self.producer:
            self.producer.flush()
            logger.info("Flushed producer after events phase")
    
    def generate_all(self) -> StreamingStats:
        """
        Generate complete dataset with streaming to Pulsar.
        
        Returns:
            StreamingStats with generation and streaming metrics
        """
        logger.info("=" * 80)
        logger.info("Starting Streaming Data Generation")
        logger.info(f"Streaming enabled: {self.config.enable_streaming}")
        logger.info(f"Producer type: {type(self.producer).__name__ if self.producer else 'None'}")
        logger.info("=" * 80)
        
        try:
            # Phase 1: Generate core entities
            self._generate_core_entities()
            
            # Phase 2: Generate events
            self._generate_events()
            
            # Phase 3: Generate patterns (uses parent implementation)
            self._generate_patterns()
            
            # Phase 4: Export data
            self._export_data()
            
            # Finalize
            self.stats.finalize()
            
            # Final flush
            if self.producer:
                self.producer.flush()
            
            logger.info("=" * 80)
            logger.info("Streaming Data Generation Complete")
            logger.info(f"Total records: {self.stats.total_records:,}")
            logger.info(f"Events published: {self.stats.events_published:,}")
            logger.info(f"Events failed: {self.stats.events_failed:,}")
            logger.info(f"Generation time: {self.stats.generation_time_seconds:.2f}s")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error during streaming generation: {e}")
            self.stats.errors.append(str(e))
            raise
        
        return self.stats
    
    def close(self):
        """Clean up resources."""
        if self._owns_producer and self.producer:
            self.producer.close()
            logger.info("Closed producer")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def get_streaming_stats(self) -> Dict[str, Any]:
        """Get streaming-specific statistics."""
        return {
            'events_published': self.stats.events_published,
            'events_failed': self.stats.events_failed,
            'events_by_type': self.stats.events_by_type,
            'streaming_errors': self.stats.streaming_errors,
            'producer_stats': self.producer.get_stats() if self.producer else None
        }


__all__ = [
    'StreamingConfig',
    'StreamingStats',
    'StreamingOrchestrator',
]
