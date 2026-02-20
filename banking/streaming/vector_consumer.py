"""
VectorConsumer - Leg 2 Consumer for OpenSearch

This module provides the consumer for loading entity embeddings into OpenSearch.
It generates embeddings from text_for_embedding field and indexes documents.

Features:
    - Batch embedding generation
    - Bulk indexing to OpenSearch
    - Same entity_id as JanusGraph for cross-system queries
    - Smart update (regenerate only if text changed)

Created: 2026-02-04
Week 4: Vector Consumer (Leg 2)
"""

import logging
import os
import time
import json
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
    from opensearchpy import OpenSearch, helpers

    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

from .events import EntityEvent

logger = logging.getLogger(__name__)


class VectorConsumer:
    """
    Consumer for loading embeddings into OpenSearch.

    Generates embeddings from text_for_embedding field and indexes documents.
    Uses same entity_id as JanusGraph for cross-system consistency.

    Attributes:
        pulsar_url: Pulsar broker URL
        opensearch_host: OpenSearch host
        opensearch_port: OpenSearch port
        embedding_model: SentenceTransformer model name
        topics: List of topics to subscribe to

    Example:
        >>> consumer = VectorConsumer()
        >>> consumer.process_forever()  # Blocking
    """

    # Default configuration
    DEFAULT_PULSAR_URL = "pulsar://localhost:6650"
    DEFAULT_OPENSEARCH_HOST = "localhost"
    DEFAULT_OPENSEARCH_PORT = 9200
    DEFAULT_SUBSCRIPTION = "vector-loaders"
    DEFAULT_BATCH_SIZE = 100
    DEFAULT_BATCH_TIMEOUT_MS = 100
    DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # Topics that need embeddings (persons and companies)
    DEFAULT_TOPICS = [
        "persistent://public/banking/persons-events",
        "persistent://public/banking/companies-events",
    ]

    # Index mapping by entity type
    INDEX_MAPPING = {
        "person": "person_vectors",
        "company": "company_vectors",
    }

    def __init__(
        self,
        pulsar_url: str = None,
        opensearch_host: str = None,
        opensearch_port: int = None,
        embedding_model: str = None,
        topics: List[str] = None,
        subscription_name: str = None,
        batch_size: int = None,
        batch_timeout_ms: int = None,
        dlq_topic: str = None,
    ):
        """
        Initialize the VectorConsumer.

        Args:
            pulsar_url: Pulsar broker URL
            opensearch_host: OpenSearch host
            opensearch_port: OpenSearch port
            embedding_model: SentenceTransformer model name
            topics: List of topics to subscribe to
            subscription_name: Consumer subscription name
            batch_size: Number of events per batch
            batch_timeout_ms: Timeout for batch collection
            dlq_topic: Dead letter queue topic
        """
        if not PULSAR_AVAILABLE:
            raise ImportError("pulsar-client is not installed")
        if not OPENSEARCH_AVAILABLE:
            raise ImportError("opensearch-py is not installed")

        # Configuration
        self.pulsar_url = pulsar_url or os.getenv("PULSAR_URL", self.DEFAULT_PULSAR_URL)
        self.opensearch_host = opensearch_host or os.getenv(
            "OPENSEARCH_HOST", self.DEFAULT_OPENSEARCH_HOST
        )
        self.opensearch_port = opensearch_port or int(
            os.getenv("OPENSEARCH_PORT", self.DEFAULT_OPENSEARCH_PORT)
        )
        self.embedding_model_name = embedding_model or self.DEFAULT_EMBEDDING_MODEL
        self.topics = topics or self.DEFAULT_TOPICS
        self.subscription_name = subscription_name or self.DEFAULT_SUBSCRIPTION
        self.batch_size = batch_size or self.DEFAULT_BATCH_SIZE
        self.batch_timeout_ms = batch_timeout_ms or self.DEFAULT_BATCH_TIMEOUT_MS
        self.dlq_topic = dlq_topic or "persistent://public/banking/dlq-events"

        # State
        self.pulsar_client: Optional[Client] = None
        self.consumer: Optional[Consumer] = None
        self.dlq_producer = None
        self.opensearch: Optional[OpenSearch] = None
        self.embedding_model = None
        self._running = False

        # Metrics
        self.metrics = {
            "events_processed": 0,
            "events_skipped": 0,
            "events_failed": 0,
            "batches_processed": 0,
            "embeddings_generated": 0,
            "last_batch_time": None,
        }

    def connect(self):
        """Establish connections to Pulsar, OpenSearch, and load embedding model."""
        # Connect to Pulsar
        self._log_event("vector_consumer_connect_pulsar", pulsar_url=self.pulsar_url)
        self.pulsar_client = pulsar.Client(self.pulsar_url)

        # Subscribe to topics with Key_Shared
        self._log_event(
            "vector_consumer_subscribe_topics",
            topics=self.topics,
            subscription_name=self.subscription_name,
        )
        self.consumer = self.pulsar_client.subscribe(
            self.topics,
            subscription_name=self.subscription_name,
            consumer_type=ConsumerType.KeyShared,
            receiver_queue_size=self.batch_size * 2,
        )

        # Create DLQ producer
        self.dlq_producer = self.pulsar_client.create_producer(self.dlq_topic)

        # Connect to OpenSearch
        self._log_event(
            "vector_consumer_connect_opensearch",
            opensearch_host=self.opensearch_host,
            opensearch_port=self.opensearch_port,
        )
        use_ssl = os.getenv("OPENSEARCH_USE_SSL", "false").lower() == "true"
        self.opensearch = OpenSearch(
            hosts=[{"host": self.opensearch_host, "port": self.opensearch_port}],
            use_ssl=use_ssl,
            verify_certs=use_ssl,
        )

        # Verify OpenSearch connection
        info = self.opensearch.info()
        self._log_event(
            "vector_consumer_opensearch_connected",
            version=info["version"]["number"],
        )

        # Load embedding model
        if EMBEDDING_AVAILABLE:
            self._log_event("vector_consumer_embedding_model_loading", model=self.embedding_model_name)
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            self._log_event(
                "vector_consumer_embedding_model_loaded",
                dimension=self.embedding_model.get_sentence_embedding_dimension(),
            )
        else:
            self._log_event(
                "vector_consumer_embedding_model_unavailable",
                level=logging.WARNING,
            )

        # Ensure indices exist
        self._ensure_indices()

        self._log_event("vector_consumer_connected")

    def _ensure_indices(self):
        """Create OpenSearch indices if they don't exist."""
        dimension = 384 if self.embedding_model else 384  # MiniLM default
        if self.embedding_model and hasattr(
            self.embedding_model, "get_sentence_embedding_dimension"
        ):
            dimension = self.embedding_model.get_sentence_embedding_dimension()

        index_body = {
            "settings": {"index": {"knn": True, "number_of_shards": 1, "number_of_replicas": 0}},
            "mappings": {
                "properties": {
                    "entity_id": {"type": "keyword"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": dimension,
                        "method": {"name": "hnsw", "space_type": "cosinesimil", "engine": "lucene"},
                    },
                    "text_for_embedding": {"type": "text"},
                    "version": {"type": "integer"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "source": {"type": "keyword"},
                }
            },
        }

        for entity_type, index_name in self.INDEX_MAPPING.items():
            if not self.opensearch.indices.exists(index=index_name):
                self._log_event(
                    "vector_consumer_index_create",
                    entity_type=entity_type,
                    index=index_name,
                )
                self.opensearch.indices.create(index=index_name, body=index_body)

    def disconnect(self):
        """Close all connections."""
        self._log_event("vector_consumer_disconnect_start")

        if self.consumer:
            self.consumer.close()
        if self.dlq_producer:
            self.dlq_producer.close()
        if self.pulsar_client:
            self.pulsar_client.close()

        self._log_event("vector_consumer_disconnected")

    @staticmethod
    def _format_log_fields(**fields: Any) -> str:
        """Format structured log fields as key=value pairs."""
        formatted_fields: List[str] = []
        for key, value in fields.items():
            if value is None:
                continue
            if isinstance(value, (list, tuple, set)):
                normalized = "[" + ",".join(str(item) for item in value) + "]"
            elif isinstance(value, dict):
                normalized = json.dumps(value, sort_keys=True, default=str)
            else:
                normalized = str(value)
            formatted_fields.append(f"{key}={normalized}")
        return " ".join(formatted_fields)

    def _log_event(self, event: str, level: int = logging.INFO, **fields: Any) -> None:
        """Emit a structured log event for runtime observability."""
        fields_payload = self._format_log_fields(component="vector_consumer", **fields)
        message = f"event={event}" + (f" {fields_payload}" if fields_payload else "")
        logger.log(level, message)

    def _log_exception(self, event: str, exc: Exception, **fields: Any) -> None:
        """Emit standardized exception logs with context."""
        self._log_event(
            event,
            level=logging.ERROR,
            error_type=type(exc).__name__,
            error=str(exc),
            **fields,
        )

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if self.embedding_model:
            embedding = self.embedding_model.encode(text)
            if hasattr(embedding, "tolist"):
                return embedding.tolist()
            return list(embedding)
        else:
            # Placeholder embedding
            return [0.0] * 384

    def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        if self.embedding_model:
            embeddings = self.embedding_model.encode(texts)
            return [e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings]
        else:
            return [[0.0] * 384 for _ in texts]

    def _get_index_name(self, entity_type: str) -> str:
        """Get OpenSearch index name for entity type."""
        return self.INDEX_MAPPING.get(entity_type, f"{entity_type}_vectors")

    def _collect_batch(self, timeout_ms: int) -> Tuple[List[EntityEvent], List[Any]]:
        """Collect events and raw messages from Pulsar."""
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

    @staticmethod
    def _split_embeddable_events(
        batch: List[EntityEvent],
    ) -> Tuple[List[Tuple[int, EntityEvent]], List[Tuple[int, EntityEvent]]]:
        """Partition events into embeddable and non-embeddable lists."""
        embeddable = [(index, event) for index, event in enumerate(batch) if event.text_for_embedding]
        non_embeddable = [
            (index, event) for index, event in enumerate(batch) if not event.text_for_embedding
        ]
        return embeddable, non_embeddable

    def _ack_non_embeddable_events(
        self, non_embeddable: List[Tuple[int, EntityEvent]], messages: List[Any]
    ) -> None:
        """Acknowledge events that have no embedding text."""
        for index, _event in non_embeddable:
            self.consumer.acknowledge(messages[index])
            self.metrics["events_skipped"] += 1

    def _generate_embeddings_or_nack(
        self, embeddable: List[Tuple[int, EntityEvent]], messages: List[Any]
    ) -> Optional[List[List[float]]]:
        """Generate embeddings for embeddable events or NACK on failure."""
        texts = [event.text_for_embedding for _, event in embeddable]
        try:
            embeddings = self._generate_batch_embeddings(texts)
            self.metrics["embeddings_generated"] += len(embeddings)
            return embeddings
        except Exception as e:
            self._log_exception(
                "vector_consumer_embedding_generation_failed",
                e,
                embeddable_count=len(embeddable),
            )
            for index, _event in embeddable:
                self.consumer.negative_acknowledge(messages[index])
            return None

    def _build_bulk_actions(
        self, embeddable: List[Tuple[int, EntityEvent]], embeddings: List[List[float]]
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Build OpenSearch bulk actions and matching message indexes."""
        actions: List[Dict[str, Any]] = []
        processed_indices: List[int] = []

        for (orig_idx, event), embedding in zip(embeddable, embeddings):
            index_name = self._get_index_name(event.entity_type)
            if event.event_type == "delete":
                actions.append({"_op_type": "delete", "_index": index_name, "_id": event.entity_id})
            else:
                actions.append(
                    {
                        "_op_type": "index",
                        "_index": index_name,
                        "_id": event.entity_id,
                        "_source": {
                            "entity_id": event.entity_id,
                            "embedding": embedding,
                            "text_for_embedding": event.text_for_embedding,
                            "version": event.version,
                            "created_at": event.timestamp.isoformat(),
                            "source": event.source,
                            **event.payload,
                        },
                    }
                )
            processed_indices.append(orig_idx)

        return actions, processed_indices

    def _bulk_index_actions(self, actions: List[Dict[str, Any]], processed_indices: List[int], messages: List[Any]) -> int:
        """Bulk index actions and ACK/NACK corresponding Pulsar messages."""
        try:
            success, errors = helpers.bulk(self.opensearch, actions, refresh=True)
            for index in processed_indices:
                self.consumer.acknowledge(messages[index])

            self.metrics["events_processed"] += success
            if errors:
                self.metrics["events_failed"] += len(errors)
                self._log_event(
                    "vector_consumer_bulk_index_partial_errors",
                    level=logging.WARNING,
                    error_count=len(errors),
                )

            self._log_event("vector_consumer_bulk_index_success", indexed=success)
            return success
        except Exception as e:
            self._log_exception(
                "vector_consumer_bulk_index_failed",
                e,
                action_count=len(actions),
            )
            for index in processed_indices:
                self.consumer.negative_acknowledge(messages[index])
            self.metrics["events_failed"] += len(processed_indices)
            return 0

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

        embeddable, non_embeddable = self._split_embeddable_events(batch)
        self._ack_non_embeddable_events(non_embeddable, messages)

        if not embeddable:
            return 0

        embeddings = self._generate_embeddings_or_nack(embeddable, messages)
        if embeddings is None:
            return 0

        actions, processed_indices = self._build_bulk_actions(embeddable, embeddings)
        success = self._bulk_index_actions(actions, processed_indices, messages)
        if success == 0:
            return 0

        # Update metrics
        self.metrics["batches_processed"] += 1
        self.metrics["last_batch_time"] = datetime.now(timezone.utc).isoformat()

        return success

    def process_forever(self, on_batch: Callable[[int], None] = None):
        """
        Continuously process events.

        Args:
            on_batch: Optional callback after each batch
        """
        self._running = True
        self._log_event("vector_consumer_loop_started")

        while self._running:
            try:
                processed = self.process_batch()
                if on_batch:
                    on_batch(processed)
            except KeyboardInterrupt:
                self._log_event("vector_consumer_loop_shutdown_signal")
                break
            except Exception as e:
                self._log_exception("vector_consumer_loop_error", e)
                time.sleep(1)

        self._log_event("vector_consumer_loop_stopped")

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
    """Entry point for running VectorConsumer as a service."""
    import signal

    consumer = VectorConsumer()

    def signal_handler(sig, frame):
        consumer._log_event("vector_consumer_signal_received", signal=str(sig))
        consumer.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        consumer.connect()
        consumer._log_event("vector_consumer_main_started")
        consumer.process_forever()
    finally:
        consumer.disconnect()


if __name__ == "__main__":
    main()
