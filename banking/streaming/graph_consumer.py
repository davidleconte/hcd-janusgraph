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
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

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
    from gremlin_python.process.graph_traversal import GraphTraversalSource, __

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
        dlq_topic: str = None,
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
        self.pulsar_url = pulsar_url or os.getenv("PULSAR_URL", self.DEFAULT_PULSAR_URL)
        self.janusgraph_url = janusgraph_url or os.getenv(
            "JANUSGRAPH_URL", self.DEFAULT_JANUSGRAPH_URL
        )
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
            "events_processed": 0,
            "events_failed": 0,
            "batches_processed": 0,
            "last_batch_time": None,
        }

    def connect(self):
        """Establish connections to Pulsar and JanusGraph."""
        logger.info("Connecting to Pulsar at %s", self.pulsar_url)
        self.pulsar_client = pulsar.Client(self.pulsar_url)

        logger.info("Subscribing to topics: %s", self.topics)
        self.consumer = self.pulsar_client.subscribe(
            self.topics,
            subscription_name=self.subscription_name,
            consumer_type=ConsumerType.KeyShared,
            receiver_queue_size=self.batch_size * 2,
        )

        self.dlq_producer = self.pulsar_client.create_producer(self.dlq_topic)

        logger.info("Connecting to JanusGraph at %s", self.janusgraph_url)
        self.connection = DriverRemoteConnection(self.janusgraph_url, "g")
        self.g = traversal().with_remote(self.connection)

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

    @staticmethod
    def _is_timestamp_like_key(key: str) -> bool:
        """Return True when a payload key likely contains a timestamp value."""
        return "timestamp" in key or "date" in key or "_at" in key

    def _to_graph_property_value(self, key: str, value: Any) -> Any:
        """Normalize payload values for JanusGraph property storage."""
        if isinstance(value, (int, float, bool)):
            return value

        if isinstance(value, str) and self._is_timestamp_like_key(key):
            try:
                parsed_dt = datetime.fromisoformat(value)
                return int(parsed_dt.timestamp())
            except (ValueError, TypeError):
                return str(value)

        return str(value)

    def _apply_payload_properties(
        self, traversal_obj: Any, payload: Dict[str, Any], skip_keys: set[str]
    ) -> Any:
        """Apply sanitized payload properties to a traversal."""
        for key, value in payload.items():
            if value is None or key in skip_keys:
                continue
            traversal_obj = traversal_obj.property(key, self._to_graph_property_value(key, value))
        return traversal_obj

    def _process_create_event(self, event: EntityEvent, skip_keys: set[str]) -> bool:
        """Handle idempotent create events."""
        entity_id = event.entity_id
        entity_type = event.entity_type

        traversal_obj = (
            self.g.V()
            .has(entity_type, "entity_id", entity_id)
            .fold()
            .coalesce(__.unfold(), __.add_v(entity_type).property("entity_id", entity_id))
            .property("version", event.version)
            .property("created_at", int(event.timestamp.timestamp()))
            .property("source", event.source or "unknown")
        )

        traversal_obj = self._apply_payload_properties(traversal_obj, event.payload, skip_keys)
        traversal_obj.iterate()
        logger.debug("Created/updated vertex: %s:%s", entity_type, entity_id)
        return True

    def _is_stale_update(self, entity_type: str, entity_id: str, version: int) -> bool:
        """Return True when an incoming update version is stale."""
        existing = self.g.V().has(entity_type, "entity_id", entity_id).value_map("version").toList()
        if not existing:
            return False

        current_version = existing[0].get("version", [0])[0]
        if current_version >= version:
            logger.warning(
                "Skipping stale update for %s: current=%s, event=%s",
                entity_id,
                current_version,
                version,
            )
            return True
        return False

    def _process_update_event(self, event: EntityEvent, skip_keys: set[str]) -> bool:
        """Handle update events with optimistic concurrency checks."""
        entity_id = event.entity_id
        entity_type = event.entity_type

        if self._is_stale_update(entity_type, entity_id, event.version):
            return True

        traversal_obj = (
            self.g.V()
            .has(entity_type, "entity_id", entity_id)
            .property("version", event.version)
            .property("updated_at", int(event.timestamp.timestamp()))
        )
        traversal_obj = self._apply_payload_properties(traversal_obj, event.payload, skip_keys)
        traversal_obj.iterate()

        logger.debug("Updated vertex: %s:%s", entity_type, entity_id)
        return True

    def _process_delete_event(self, event: EntityEvent) -> bool:
        """Handle delete events."""
        self.g.V().has(event.entity_type, "entity_id", event.entity_id).drop().iterate()
        logger.debug("Deleted vertex: %s:%s", event.entity_type, event.entity_id)
        return True

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
            skip_keys = {"created_at", "updated_at", "entity_id", "version", "source"}
            if event.event_type == "create":
                return self._process_create_event(event, skip_keys)
            if event.event_type == "update":
                return self._process_update_event(event, skip_keys)
            if event.event_type == "delete":
                return self._process_delete_event(event)

            logger.warning("Unknown event type '%s' for event %s", event.event_type, event.event_id)
            return True

        except Exception as e:
            logger.error("Failed to process event %s: %s", event.event_id, e)
            return False

    def _collect_batch(self, timeout_ms: int) -> Tuple[List[EntityEvent], List[Any]]:
        """Collect a batch of events and matching Pulsar messages."""
        batch: List[EntityEvent] = []
        messages: List[Any] = []
        start_time = time.time()

        while len(batch) < self.batch_size:
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms >= timeout_ms and batch:
                break

            remaining_ms = max(1, int(timeout_ms - elapsed_ms))
            try:
                message = self.consumer.receive(timeout_millis=remaining_ms)
                event = EntityEvent.from_bytes(message.data())
            except Exception:
                break

            batch.append(event)
            messages.append(message)

        return batch, messages

    def _process_collected_batch(
        self, batch: List[EntityEvent], messages: List[Any]
    ) -> Tuple[int, List[Tuple[Any, EntityEvent]]]:
        """Process collected events and ACK successful ones."""
        processed = 0
        failed: List[Tuple[Any, EntityEvent]] = []

        for index, event in enumerate(batch):
            try:
                if self.process_event(event):
                    self.consumer.acknowledge(messages[index])
                    processed += 1
                else:
                    failed.append((messages[index], event))
            except Exception as e:
                logger.error("Error processing event %s: %s", event.event_id, e)
                failed.append((messages[index], event))

        return processed, failed

    def _route_failed_events_to_dlq(self, failed: List[Tuple[Any, EntityEvent]]) -> None:
        """Send failed events to DLQ, then ACK or NACK depending on outcome."""
        for message, event in failed:
            try:
                self.dlq_producer.send(
                    content=event.to_bytes(),
                    properties={"error": "processing_failed", "original_topic": event.get_topic()},
                )
                self.consumer.acknowledge(message)
            except Exception as e:
                logger.error("Failed to send to DLQ: %s", e)
                self.consumer.negative_acknowledge(message)

    def _record_batch_metrics(self, processed: int, failed_count: int) -> None:
        """Update consumer metrics after a batch run."""
        self.metrics["events_processed"] += processed
        self.metrics["events_failed"] += failed_count
        self.metrics["batches_processed"] += 1
        self.metrics["last_batch_time"] = datetime.now(timezone.utc).isoformat()

    def process_batch(self, timeout_ms: int = None) -> int:
        """
        Collect and process a batch of events.

        Args:
            timeout_ms: Timeout for collecting events

        Returns:
            Number of events processed
        """
        timeout_ms = timeout_ms or self.batch_timeout_ms
        batch, messages = self._collect_batch(timeout_ms)

        if not batch:
            return 0

        processed, failed = self._process_collected_batch(batch, messages)
        self._route_failed_events_to_dlq(failed)
        self._record_batch_metrics(processed, len(failed))

        logger.info("Processed batch: %d success, %d failed", processed, len(failed))
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
                logger.error("Error in processing loop: %s", e)
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
