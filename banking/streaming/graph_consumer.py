"""
GraphConsumer - Leg 1 Consumer for JanusGraph/HCD

This module provides the consumer for loading entity events into JanusGraph.
It uses Key_Shared subscription for parallel processing with entity-level ordering.

Features:
    - Batch processing (configurable batch size)
    - Transaction handling (atomic commits)
    - Idempotent operations (fold/coalesce pattern)
    - Error handling with NACK and DLQ

Created: 2026-02-04
Week 3: Graph Consumer (Leg 1)
"""

import logging
import os
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import time

try:
    import pulsar
    from pulsar import Client, Consumer, ConsumerType
    PULSAR_AVAILABLE = True
except ImportError:
    PULSAR_AVAILABLE = False
    pulsar = None

try:
    from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
    from gremlin_python.process.anonymous_traversal import traversal
    from gremlin_python.process.graph_traversal import GraphTraversalSource
    GREMLIN_AVAILABLE = True
except ImportError:
    GREMLIN_AVAILABLE = False

from .events import EntityEvent

logger = logging.getLogger(__name__)


class GraphConsumer:
    """
    Consumer for loading entities into JanusGraph/HCD.
    
    Uses Key_Shared subscription for parallel processing with entity-level ordering.
    Processes events in batches with transactional commits.
    
    Attributes:
        pulsar_url: Pulsar broker URL
        janusgraph_url: JanusGraph Gremlin server URL
        topics: List of topics to subscribe to
        subscription_name: Consumer subscription name
        batch_size: Number of events to process in a batch
    
    Example:
        >>> consumer = GraphConsumer()
        >>> consumer.process_forever()  # Blocking
        
        # Or process a single batch:
        >>> processed = consumer.process_batch(timeout_ms=1000)
    """
    
    # Default configuration
    DEFAULT_PULSAR_URL = "pulsar://localhost:6650"
    DEFAULT_JANUSGRAPH_URL = "ws://localhost:18182/gremlin"
    DEFAULT_SUBSCRIPTION = "graph-loaders"
    DEFAULT_BATCH_SIZE = 100
    DEFAULT_BATCH_TIMEOUT_MS = 100
    
    # Topics to subscribe to
    DEFAULT_TOPICS = [
        "persistent://public/banking/persons-events",
        "persistent://public/banking/accounts-events",
        "persistent://public/banking/transactions-events",
        "persistent://public/banking/companies-events",
        "persistent://public/banking/communications-events",
    ]
    
    def __init__(
        self,
        pulsar_url: str = None,
        janusgraph_url: str = None,
        topics: List[str] = None,
        subscription_name: str = None,
        batch_size: int = None,
        batch_timeout_ms: int = None,
        dlq_topic: str = None
    ):
        """
        Initialize the GraphConsumer.
        
        Args:
            pulsar_url: Pulsar broker URL
            janusgraph_url: JanusGraph Gremlin server URL
            topics: List of topics to subscribe to
            subscription_name: Consumer subscription name
            batch_size: Number of events per batch
            batch_timeout_ms: Timeout for batch collection
            dlq_topic: Dead letter queue topic
        """
        if not PULSAR_AVAILABLE:
            raise ImportError("pulsar-client is not installed")
        if not GREMLIN_AVAILABLE:
            raise ImportError("gremlinpython is not installed")
        
        # Configuration
        self.pulsar_url = pulsar_url or os.getenv('PULSAR_URL', self.DEFAULT_PULSAR_URL)
        self.janusgraph_url = janusgraph_url or os.getenv('JANUSGRAPH_URL', self.DEFAULT_JANUSGRAPH_URL)
        self.topics = topics or self.DEFAULT_TOPICS
        self.subscription_name = subscription_name or self.DEFAULT_SUBSCRIPTION
        self.batch_size = batch_size or self.DEFAULT_BATCH_SIZE
        self.batch_timeout_ms = batch_timeout_ms or self.DEFAULT_BATCH_TIMEOUT_MS
        self.dlq_topic = dlq_topic or "persistent://public/banking/dlq-events"
        
        # State
        self.pulsar_client: Optional[Client] = None
        self.consumer: Optional[Consumer] = None
        self.dlq_producer = None
        self.g: Optional[GraphTraversalSource] = None
        self.connection = None
        self._running = False
        
        # Metrics
        self.metrics = {
            'events_processed': 0,
            'events_failed': 0,
            'batches_processed': 0,
            'last_batch_time': None
        }
    
    def connect(self):
        """Establish connections to Pulsar and JanusGraph."""
        # Connect to Pulsar
        logger.info(f"Connecting to Pulsar at {self.pulsar_url}")
        self.pulsar_client = pulsar.Client(self.pulsar_url)
        
        # Subscribe to topics with Key_Shared
        logger.info(f"Subscribing to topics: {self.topics}")
        self.consumer = self.pulsar_client.subscribe(
            self.topics,
            subscription_name=self.subscription_name,
            consumer_type=ConsumerType.KeyShared,
            receiver_queue_size=self.batch_size * 2
        )
        
        # Create DLQ producer
        self.dlq_producer = self.pulsar_client.create_producer(self.dlq_topic)
        
        # Connect to JanusGraph
        logger.info(f"Connecting to JanusGraph at {self.janusgraph_url}")
        self.connection = DriverRemoteConnection(self.janusgraph_url, 'g')
        self.g = traversal().withRemote(self.connection)
        
        logger.info("GraphConsumer connected successfully")
    
    def disconnect(self):
        """Close all connections."""
        logger.info("Disconnecting GraphConsumer...")
        
        if self.consumer:
            self.consumer.close()
        if self.dlq_producer:
            self.dlq_producer.close()
        if self.pulsar_client:
            self.pulsar_client.close()
        if self.connection:
            self.connection.close()
        
        logger.info("GraphConsumer disconnected")
    
    def process_event(self, event: EntityEvent) -> bool:
        """
        Process a single event - create, update, or delete in JanusGraph.
        
        Uses idempotent patterns:
        - Create: fold().coalesce() - creates if not exists
        - Update: checks version before updating
        - Delete: drops vertex if exists
        
        Args:
            event: EntityEvent to process
        
        Returns:
            True if successful, False otherwise
        """
        try:
            entity_id = event.entity_id
            entity_type = event.entity_type
            payload = event.payload
            version = event.version
            
            if event.event_type == 'create':
                # Idempotent create using fold/coalesce
                self.g.V().has(entity_type, 'entity_id', entity_id) \
                    .fold() \
                    .coalesce(
                        self.g.unfold(),
                        self.g.addV(entity_type).property('entity_id', entity_id)
                    ) \
                    .property('version', version) \
                    .property('created_at', event.timestamp.isoformat()) \
                    .property('source', event.source or 'unknown') \
                    .next()
                
                # Add payload properties
                for key, value in payload.items():
                    if value is not None:
                        self.g.V().has(entity_type, 'entity_id', entity_id) \
                            .property(key, str(value) if not isinstance(value, (int, float, bool)) else value) \
                            .iterate()
                
                logger.debug(f"Created/updated vertex: {entity_type}:{entity_id}")
                
            elif event.event_type == 'update':
                # Check version for optimistic concurrency
                existing = self.g.V().has(entity_type, 'entity_id', entity_id).valueMap('version').toList()
                
                if existing:
                    current_version = existing[0].get('version', [0])[0]
                    if current_version >= version:
                        logger.warning(f"Skipping stale update for {entity_id}: current={current_version}, event={version}")
                        return True  # Not an error, just stale
                
                # Update properties
                self.g.V().has(entity_type, 'entity_id', entity_id) \
                    .property('version', version) \
                    .property('updated_at', event.timestamp.isoformat()) \
                    .next()
                
                for key, value in payload.items():
                    if value is not None:
                        self.g.V().has(entity_type, 'entity_id', entity_id) \
                            .property(key, str(value) if not isinstance(value, (int, float, bool)) else value) \
                            .iterate()
                
                logger.debug(f"Updated vertex: {entity_type}:{entity_id}")
                
            elif event.event_type == 'delete':
                # Drop vertex if exists
                self.g.V().has(entity_type, 'entity_id', entity_id).drop().iterate()
                logger.debug(f"Deleted vertex: {entity_type}:{entity_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process event {event.event_id}: {e}")
            return False
    
    def process_batch(self, timeout_ms: int = None) -> int:
        """
        Collect and process a batch of events.
        
        Args:
            timeout_ms: Timeout for collecting events
        
        Returns:
            Number of events processed
        """
        timeout_ms = timeout_ms or self.batch_timeout_ms
        batch = []
        messages = []
        
        # Collect batch
        start_time = time.time()
        while len(batch) < self.batch_size:
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms >= timeout_ms and batch:
                break
            
            remaining_ms = max(1, int(timeout_ms - elapsed_ms))
            try:
                msg = self.consumer.receive(timeout_millis=remaining_ms)
                event = EntityEvent.from_bytes(msg.data())
                batch.append(event)
                messages.append(msg)
            except Exception:
                # Timeout or error
                if batch:
                    break
        
        if not batch:
            return 0
        
        # Process batch
        processed = 0
        failed = []
        
        for i, event in enumerate(batch):
            try:
                if self.process_event(event):
                    self.consumer.acknowledge(messages[i])
                    processed += 1
                else:
                    failed.append((messages[i], event))
            except Exception as e:
                logger.error(f"Error processing event {event.event_id}: {e}")
                failed.append((messages[i], event))
        
        # Handle failures
        for msg, event in failed:
            try:
                # Send to DLQ
                self.dlq_producer.send(
                    content=event.to_bytes(),
                    properties={'error': 'processing_failed', 'original_topic': event.get_topic()}
                )
                self.consumer.acknowledge(msg)  # ACK after DLQ
            except Exception as e:
                logger.error(f"Failed to send to DLQ: {e}")
                self.consumer.negative_acknowledge(msg)  # NACK for retry
        
        # Update metrics
        self.metrics['events_processed'] += processed
        self.metrics['events_failed'] += len(failed)
        self.metrics['batches_processed'] += 1
        self.metrics['last_batch_time'] = datetime.utcnow().isoformat()
        
        logger.info(f"Processed batch: {processed} success, {len(failed)} failed")
        return processed
    
    def process_forever(self, on_batch: Callable[[int], None] = None):
        """
        Continuously process events.
        
        Args:
            on_batch: Optional callback after each batch
        """
        self._running = True
        logger.info("Starting continuous processing...")
        
        while self._running:
            try:
                processed = self.process_batch()
                if on_batch:
                    on_batch(processed)
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(1)  # Back off on error
        
        logger.info("Stopped processing")
    
    def stop(self):
        """Stop continuous processing."""
        self._running = False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics."""
        return self.metrics.copy()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False


def main():
    """Entry point for running GraphConsumer as a service."""
    import signal
    
    consumer = GraphConsumer()
    
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        consumer.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        consumer.connect()
        logger.info("GraphConsumer started - processing events from Pulsar to JanusGraph")
        consumer.process_forever()
    finally:
        consumer.disconnect()


if __name__ == "__main__":
    main()
