"""
EntityProducer - Pulsar Producer for Banking Events

This module provides the producer class for publishing entity events
to Apache Pulsar. It routes events to appropriate topics based on entity_type.

Features:
    - Automatic topic routing based on entity_type
    - Batching and compression (ZSTD)
    - Deduplication via sequence_id
    - Entity-level ordering via partition_key

Created: 2026-02-04
Week 2: Event Schema & Producers
"""

import logging
import os
from typing import Dict, List, Optional, Any

try:
    import pulsar
    from pulsar import Client, Producer, CompressionType
    PULSAR_AVAILABLE = True
except ImportError:
    PULSAR_AVAILABLE = False
    pulsar = None
    # Define placeholder types for type hints when pulsar is not available
    Client = None
    Producer = None
    CompressionType = None

from .events import EntityEvent, EntityEventBatch

logger = logging.getLogger(__name__)


class EntityProducer:
    """
    Pulsar producer for publishing entity events.
    
    Routes events to appropriate topics based on entity_type.
    Supports batching, compression, and deduplication.
    
    Attributes:
        pulsar_url: Pulsar broker URL
        namespace: Pulsar namespace (default: public/banking)
        client: Pulsar client instance
        producers: Dictionary of producers by topic
    
    Example:
        >>> producer = EntityProducer()
        >>> event = EntityEvent(
        ...     entity_id="123",
        ...     event_type="create",
        ...     entity_type="person",
        ...     payload={"name": "John"}
        ... )
        >>> producer.send(event)
        >>> producer.close()
    
    Using context manager:
        >>> with EntityProducer() as producer:
        ...     producer.send(event)
    """
    
    # Default configuration
    DEFAULT_PULSAR_URL = "pulsar://localhost:6650"
    DEFAULT_NAMESPACE = "public/banking"
    
    # Batching configuration
    DEFAULT_BATCH_SIZE = 1000
    DEFAULT_BATCH_DELAY_MS = 100
    
    def __init__(
        self,
        pulsar_url: str = None,
        namespace: str = None,
        batch_size: int = None,
        batch_delay_ms: int = None,
        compression: bool = True
    ):
        """
        Initialize the EntityProducer.
        
        Args:
            pulsar_url: Pulsar broker URL (default: pulsar://localhost:6650 or PULSAR_URL env)
            namespace: Pulsar namespace (default: public/banking)
            batch_size: Maximum batch size (default: 1000)
            batch_delay_ms: Maximum batch delay in milliseconds (default: 100)
            compression: Enable ZSTD compression (default: True)
        
        Raises:
            ImportError: If pulsar-client is not installed
            RuntimeError: If connection to Pulsar fails
        """
        if not PULSAR_AVAILABLE:
            raise ImportError(
                "pulsar-client is not installed. "
                "Install with: pip install pulsar-client>=3.4.0"
            )
        
        # Configuration
        self.pulsar_url = pulsar_url or os.getenv('PULSAR_URL', self.DEFAULT_PULSAR_URL)
        self.namespace = namespace or os.getenv('PULSAR_NAMESPACE', self.DEFAULT_NAMESPACE)
        self.batch_size = batch_size or self.DEFAULT_BATCH_SIZE
        self.batch_delay_ms = batch_delay_ms or self.DEFAULT_BATCH_DELAY_MS
        self.compression = compression
        
        # State
        self.client: Optional[Client] = None
        self.producers: Dict[str, Producer] = {}
        self._connected = False
        
        # Connect
        self._connect()
    
    def _connect(self):
        """Establish connection to Pulsar broker."""
        try:
            logger.info(f"Connecting to Pulsar at {self.pulsar_url}")
            self.client = pulsar.Client(
                self.pulsar_url,
                operation_timeout_seconds=30,
                connection_timeout_ms=10000
            )
            self._connected = True
            logger.info("Connected to Pulsar successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Pulsar: {e}")
            raise RuntimeError(f"Failed to connect to Pulsar at {self.pulsar_url}: {e}")
    
    def _get_topic(self, entity_type: str) -> str:
        """Get the topic name for an entity type."""
        return f"persistent://{self.namespace}/{entity_type}s-events"
    
    def _get_producer(self, entity_type: str) -> Producer:
        """
        Get or create a producer for the given entity type.
        
        Producers are lazily created and cached by topic.
        """
        topic = self._get_topic(entity_type)
        
        if topic not in self.producers:
            logger.info(f"Creating producer for topic: {topic}")
            
            producer_config = {
                'topic': topic,
                'batching_enabled': True,
                'batching_max_messages': self.batch_size,
                'batching_max_publish_delay_ms': self.batch_delay_ms,
                'block_if_queue_full': True,
                'max_pending_messages': 10000,
            }
            
            if self.compression:
                producer_config['compression_type'] = CompressionType.ZSTD
            
            self.producers[topic] = self.client.create_producer(**producer_config)
            logger.info(f"Created producer for topic: {topic}")
        
        return self.producers[topic]
    
    def send(self, event: EntityEvent, callback=None) -> None:
        """
        Send an entity event to the appropriate Pulsar topic.
        
        The event is automatically routed to the correct topic based on entity_type.
        Uses partition_key for entity-level ordering and sequence_id for deduplication.
        
        Args:
            event: EntityEvent to send
            callback: Optional callback function for async confirmation
        
        Raises:
            ValueError: If event is invalid
            RuntimeError: If not connected to Pulsar
        """
        if not self._connected:
            raise RuntimeError("Not connected to Pulsar")
        
        producer = self._get_producer(event.entity_type)
        msg = event.to_pulsar_message()
        
        try:
            if callback:
                producer.send_async(
                    content=msg['content'],
                    partition_key=msg['partition_key'],
                    sequence_id=msg['sequence_id'],
                    callback=callback
                )
            else:
                producer.send(
                    content=msg['content'],
                    partition_key=msg['partition_key'],
                    sequence_id=msg['sequence_id']
                )
            
            logger.debug(f"Sent event {event.event_id} to topic {event.get_topic()}")
            
        except Exception as e:
            logger.error(f"Failed to send event {event.event_id}: {e}")
            raise
    
    def send_batch(self, events: List[EntityEvent]) -> Dict[str, int]:
        """
        Send a batch of events.
        
        Events are grouped by topic and sent efficiently.
        
        Args:
            events: List of EntityEvent objects
        
        Returns:
            Dictionary of {topic: count} for successfully sent events
        """
        batch = EntityEventBatch(events=events)
        results = {}
        
        for topic, topic_events in batch.by_topic().items():
            entity_type = topic_events[0].entity_type
            producer = self._get_producer(entity_type)
            
            count = 0
            for event in topic_events:
                try:
                    msg = event.to_pulsar_message()
                    producer.send(
                        content=msg['content'],
                        partition_key=msg['partition_key'],
                        sequence_id=msg['sequence_id']
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to send event {event.event_id}: {e}")
            
            results[topic] = count
            logger.info(f"Sent {count} events to {topic}")
        
        return results
    
    def flush(self):
        """Flush all pending messages."""
        for producer in self.producers.values():
            producer.flush()
        logger.debug("Flushed all producers")
    
    def close(self):
        """Close all producers and the client connection."""
        logger.info("Closing EntityProducer...")
        
        for topic, producer in self.producers.items():
            try:
                producer.flush()
                producer.close()
                logger.debug(f"Closed producer for {topic}")
            except Exception as e:
                logger.warning(f"Error closing producer for {topic}: {e}")
        
        self.producers.clear()
        
        if self.client:
            try:
                self.client.close()
                logger.info("Closed Pulsar client")
            except Exception as e:
                logger.warning(f"Error closing Pulsar client: {e}")
        
        self._connected = False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.close()
        return False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Pulsar."""
        return self._connected
    
    def get_stats(self) -> Dict[str, Any]:
        """Get producer statistics."""
        stats = {
            'connected': self._connected,
            'pulsar_url': self.pulsar_url,
            'namespace': self.namespace,
            'topics': list(self.producers.keys()),
            'producer_count': len(self.producers)
        }
        return stats


class MockEntityProducer:
    """
    Mock producer for testing without Pulsar.
    
    Stores events in memory instead of sending to Pulsar.
    Useful for unit tests and development without Pulsar running.
    
    Example:
        >>> producer = MockEntityProducer()
        >>> producer.send(event)
        >>> assert len(producer.events) == 1
    """
    
    def __init__(self):
        self.events: List[EntityEvent] = []
        self.events_by_topic: Dict[str, List[EntityEvent]] = {}
        self._connected = True
    
    def send(self, event: EntityEvent, callback=None):
        """Store event in memory."""
        self.events.append(event)
        
        topic = event.get_topic()
        if topic not in self.events_by_topic:
            self.events_by_topic[topic] = []
        self.events_by_topic[topic].append(event)
        
        logger.debug(f"MockProducer: Stored event {event.event_id}")
        
        if callback:
            callback(None, None)  # Simulate successful send
    
    def send_batch(self, events: List[EntityEvent]) -> Dict[str, int]:
        """Store batch of events in memory."""
        results = {}
        for event in events:
            self.send(event)
            topic = event.get_topic()
            results[topic] = results.get(topic, 0) + 1
        return results
    
    def flush(self):
        """No-op for mock."""
    
    def close(self):
        """Clear stored events."""
        self.events.clear()
        self.events_by_topic.clear()
        self._connected = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'connected': self._connected,
            'events_count': len(self.events),
            'topics': list(self.events_by_topic.keys())
        }
    
    def clear(self):
        """Clear all stored events."""
        self.events.clear()
        self.events_by_topic.clear()


def get_producer(mock: bool = False, **kwargs) -> EntityProducer:
    """
    Factory function to get the appropriate producer.
    
    Args:
        mock: If True, return MockEntityProducer
        **kwargs: Arguments passed to EntityProducer
    
    Returns:
        EntityProducer or MockEntityProducer instance
    """
    if mock or not PULSAR_AVAILABLE:
        logger.info("Using MockEntityProducer")
        return MockEntityProducer()
    return EntityProducer(**kwargs)
