"""
Unit tests for VectorConsumer.

Tests cover:
- Initialization and configuration
- Connection management (Pulsar, OpenSearch, embedding model)
- Event processing and embedding generation
- Batch processing
- Index management
- Error handling and DLQ
- Metrics tracking
- Context manager usage

Created: 2026-02-11
Week 2 Day 10: VectorConsumer Tests
"""

from unittest.mock import Mock, patch

import pytest

from banking.streaming.events import EntityEvent
from banking.streaming.vector_consumer import VectorConsumer


class TestVectorConsumerInitialization:
    """Test VectorConsumer initialization and configuration."""

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        consumer = VectorConsumer()

        assert consumer.pulsar_url == VectorConsumer.DEFAULT_PULSAR_URL
        assert consumer.opensearch_host == VectorConsumer.DEFAULT_OPENSEARCH_HOST
        assert consumer.opensearch_port == VectorConsumer.DEFAULT_OPENSEARCH_PORT
        assert consumer.embedding_model_name == VectorConsumer.DEFAULT_EMBEDDING_MODEL
        assert consumer.topics == VectorConsumer.DEFAULT_TOPICS
        assert consumer.subscription_name == VectorConsumer.DEFAULT_SUBSCRIPTION
        assert consumer.batch_size == VectorConsumer.DEFAULT_BATCH_SIZE
        assert consumer.batch_timeout_ms == VectorConsumer.DEFAULT_BATCH_TIMEOUT_MS

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        consumer = VectorConsumer(
            pulsar_url="pulsar://custom:6650",
            opensearch_host="custom-host",
            opensearch_port=9201,
            embedding_model="custom-model",
            topics=["custom-topic"],
            subscription_name="custom-sub",
            batch_size=50,
            batch_timeout_ms=200,
            dlq_topic="custom-dlq",
        )

        assert consumer.pulsar_url == "pulsar://custom:6650"
        assert consumer.opensearch_host == "custom-host"
        assert consumer.opensearch_port == 9201
        assert consumer.embedding_model_name == "custom-model"
        assert consumer.topics == ["custom-topic"]
        assert consumer.subscription_name == "custom-sub"
        assert consumer.batch_size == 50
        assert consumer.batch_timeout_ms == 200
        assert consumer.dlq_topic == "custom-dlq"

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", False)
    def test_init_without_pulsar(self):
        """Test initialization fails without pulsar-client."""
        with pytest.raises(ImportError, match="pulsar-client is not installed"):
            VectorConsumer()

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", False)
    def test_init_without_opensearch(self):
        """Test initialization fails without opensearch-py."""
        with pytest.raises(ImportError, match="opensearch-py is not installed"):
            VectorConsumer()

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_initial_state(self):
        """Test initial state of consumer."""
        consumer = VectorConsumer()

        assert consumer.pulsar_client is None
        assert consumer.consumer is None
        assert consumer.dlq_producer is None
        assert consumer.opensearch is None
        assert consumer.embedding_model is None
        assert consumer._running is False

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_initial_metrics(self):
        """Test initial metrics state."""
        consumer = VectorConsumer()

        assert consumer.metrics["events_processed"] == 0
        assert consumer.metrics["events_skipped"] == 0
        assert consumer.metrics["events_failed"] == 0
        assert consumer.metrics["batches_processed"] == 0
        assert consumer.metrics["embeddings_generated"] == 0
        assert consumer.metrics["last_batch_time"] is None

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_index_mapping(self):
        """Test index mapping configuration."""
        assert VectorConsumer.INDEX_MAPPING["person"] == "person_vectors"
        assert VectorConsumer.INDEX_MAPPING["company"] == "company_vectors"


class TestVectorConsumerConnection:
    """Test connection management."""

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.EMBEDDING_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    @patch("banking.streaming.vector_consumer.SentenceTransformer")
    @patch.dict("os.environ", {"OPENSEARCH_USE_SSL": "false"})
    def test_connect_success(self, mock_transformer, mock_opensearch_class, mock_pulsar):
        """Test successful connection to all services."""
        # Setup Pulsar mocks
        mock_client = Mock()
        mock_consumer = Mock()
        mock_producer = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.subscribe.return_value = mock_consumer
        mock_client.create_producer.return_value = mock_producer

        # Setup OpenSearch mocks
        mock_opensearch = Mock()
        mock_opensearch.info.return_value = {"version": {"number": "2.0.0"}}
        mock_opensearch.indices.exists.return_value = True
        mock_opensearch_class.return_value = mock_opensearch

        # Setup embedding model mock
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model

        consumer = VectorConsumer()
        consumer.connect()

        # Verify Pulsar connection
        mock_pulsar.Client.assert_called_once_with(consumer.pulsar_url)
        mock_client.subscribe.assert_called_once()
        mock_client.create_producer.assert_called_once()

        # Verify OpenSearch connection
        mock_opensearch_class.assert_called_once()
        mock_opensearch.info.assert_called_once()

        # Verify embedding model loaded
        mock_transformer.assert_called_once_with(consumer.embedding_model_name)

        assert consumer.pulsar_client == mock_client
        assert consumer.consumer == mock_consumer
        assert consumer.dlq_producer == mock_producer
        assert consumer.opensearch == mock_opensearch
        assert consumer.embedding_model == mock_model

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.EMBEDDING_AVAILABLE", False)
    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    @patch.dict("os.environ", {"OPENSEARCH_USE_SSL": "false"})
    def test_connect_without_embedding_model(self, mock_opensearch_class, mock_pulsar):
        """Test connection without sentence-transformers."""
        # Setup mocks
        mock_client = Mock()
        mock_consumer = Mock()
        mock_producer = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.subscribe.return_value = mock_consumer
        mock_client.create_producer.return_value = mock_producer

        mock_opensearch = Mock()
        mock_opensearch.info.return_value = {"version": {"number": "2.0.0"}}
        mock_opensearch.indices.exists.return_value = True
        mock_opensearch_class.return_value = mock_opensearch

        consumer = VectorConsumer()
        consumer.connect()

        # Should connect but embedding_model is None
        assert consumer.embedding_model is None

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.pulsar")
    def test_connect_pulsar_failure(self, mock_pulsar):
        """Test connection failure to Pulsar."""
        mock_pulsar.Client.side_effect = Exception("Connection failed")

        consumer = VectorConsumer()

        with pytest.raises(Exception, match="Connection failed"):
            consumer.connect()

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_disconnect(self):
        """Test disconnection closes all resources."""
        consumer = VectorConsumer()

        # Mock connections
        consumer.consumer = Mock()
        consumer.dlq_producer = Mock()
        consumer.pulsar_client = Mock()

        consumer.disconnect()

        consumer.consumer.close.assert_called_once()
        consumer.dlq_producer.close.assert_called_once()
        consumer.pulsar_client.close.assert_called_once()

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.EMBEDDING_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    @patch("banking.streaming.vector_consumer.SentenceTransformer")
    @patch.dict("os.environ", {"OPENSEARCH_USE_SSL": "false"})
    def test_ensure_indices_creates_missing(
        self, mock_transformer, mock_opensearch_class, mock_pulsar
    ):
        """Test index creation for missing indices."""
        # Setup mocks
        mock_client = Mock()
        mock_consumer = Mock()
        mock_producer = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.subscribe.return_value = mock_consumer
        mock_client.create_producer.return_value = mock_producer

        mock_opensearch = Mock()
        mock_opensearch.info.return_value = {"version": {"number": "2.0.0"}}
        mock_opensearch.indices.exists.return_value = False  # Indices don't exist
        mock_opensearch_class.return_value = mock_opensearch

        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model

        consumer = VectorConsumer()
        consumer.connect()

        # Verify indices were created
        assert mock_opensearch.indices.create.call_count == 2  # person and company


class TestVectorConsumerEmbedding:
    """Test embedding generation."""

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_generate_embedding_with_model(self):
        """Test embedding generation with model."""
        consumer = VectorConsumer()

        # Mock embedding model
        mock_model = Mock()
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3]
        mock_model.encode.return_value = mock_embedding
        consumer.embedding_model = mock_model

        embedding = consumer._generate_embedding("test text")

        assert embedding == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once_with("test text")

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_generate_embedding_without_model(self):
        """Test embedding generation without model (placeholder)."""
        consumer = VectorConsumer()
        consumer.embedding_model = None

        embedding = consumer._generate_embedding("test text")

        assert len(embedding) == 384
        assert all(v == 0.0 for v in embedding)

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_generate_batch_embeddings_with_model(self):
        """Test batch embedding generation with model."""
        consumer = VectorConsumer()

        # Mock embedding model
        mock_model = Mock()
        mock_embeddings = [Mock(), Mock()]
        mock_embeddings[0].tolist.return_value = [0.1, 0.2]
        mock_embeddings[1].tolist.return_value = [0.3, 0.4]
        mock_model.encode.return_value = mock_embeddings
        consumer.embedding_model = mock_model

        texts = ["text1", "text2"]
        embeddings = consumer._generate_batch_embeddings(texts)

        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2]
        assert embeddings[1] == [0.3, 0.4]
        mock_model.encode.assert_called_once_with(texts)

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_generate_batch_embeddings_without_model(self):
        """Test batch embedding generation without model."""
        consumer = VectorConsumer()
        consumer.embedding_model = None

        texts = ["text1", "text2", "text3"]
        embeddings = consumer._generate_batch_embeddings(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)
        assert all(all(v == 0.0 for v in e) for e in embeddings)

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_get_index_name(self):
        """Test getting index name for entity type."""
        consumer = VectorConsumer()

        assert consumer._get_index_name("person") == "person_vectors"
        assert consumer._get_index_name("company") == "company_vectors"
        assert consumer._get_index_name("unknown") == "unknown_vectors"


class TestVectorConsumerBatchProcessing:
    """Test batch processing logic."""

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_process_batch_empty(self):
        """Test processing empty batch."""
        consumer = VectorConsumer()

        # Mock consumer that times out immediately
        mock_consumer = Mock()
        mock_consumer.receive.side_effect = Exception("Timeout")
        consumer.consumer = mock_consumer

        processed = consumer.process_batch(timeout_ms=10)

        assert processed == 0

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.helpers")
    def test_process_batch_success(self, mock_helpers):
        """Test successful batch processing."""
        consumer = VectorConsumer()

        # Mock messages with text_for_embedding
        mock_messages = []
        for i in range(3):
            msg = Mock()
            event = EntityEvent(
                entity_id=f"p-{i}",
                event_type="create",
                entity_type="person",
                payload={"name": f"Person {i}"},
                text_for_embedding=f"Person {i} description",
            )
            msg.data.return_value = event.to_bytes()
            mock_messages.append(msg)

        # Mock consumer
        mock_consumer = Mock()
        mock_consumer.receive.side_effect = mock_messages + [Exception("Timeout")]
        consumer.consumer = mock_consumer

        # Mock DLQ producer
        consumer.dlq_producer = Mock()

        # Mock OpenSearch
        consumer.opensearch = Mock()

        # Mock embedding generation
        consumer._generate_batch_embeddings = Mock(return_value=[[0.1] * 384] * 3)

        # Mock bulk index success
        mock_helpers.bulk.return_value = (3, [])

        processed = consumer.process_batch(timeout_ms=100)

        assert processed == 3
        assert consumer.metrics["events_processed"] == 3
        assert consumer.metrics["embeddings_generated"] == 3
        assert consumer.metrics["batches_processed"] == 1

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_process_batch_skips_non_embeddable(self):
        """Test batch processing skips events without text_for_embedding."""
        consumer = VectorConsumer()

        # Mock messages without text_for_embedding
        mock_messages = []
        for i in range(3):
            msg = Mock()
            event = EntityEvent(
                entity_id=f"a-{i}",
                event_type="create",
                entity_type="account",
                payload={"balance": 1000},
                text_for_embedding=None,  # No text
            )
            msg.data.return_value = event.to_bytes()
            mock_messages.append(msg)

        # Mock consumer
        mock_consumer = Mock()
        mock_consumer.receive.side_effect = mock_messages + [Exception("Timeout")]
        consumer.consumer = mock_consumer

        processed = consumer.process_batch(timeout_ms=100)

        assert processed == 0
        assert consumer.metrics["events_skipped"] == 3
        # All should be acknowledged
        assert mock_consumer.acknowledge.call_count == 3

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.helpers")
    def test_process_batch_mixed_embeddable(self, mock_helpers):
        """Test batch with mix of embeddable and non-embeddable events."""
        consumer = VectorConsumer()

        # Mock messages: 2 with text, 1 without
        mock_messages = []
        for i in range(3):
            msg = Mock()
            text = f"Person {i}" if i < 2 else None
            event = EntityEvent(
                entity_id=f"p-{i}",
                event_type="create",
                entity_type="person",
                payload={},
                text_for_embedding=text,
            )
            msg.data.return_value = event.to_bytes()
            mock_messages.append(msg)

        # Mock consumer
        mock_consumer = Mock()
        mock_consumer.receive.side_effect = mock_messages + [Exception("Timeout")]
        consumer.consumer = mock_consumer

        # Mock OpenSearch
        consumer.opensearch = Mock()
        consumer.dlq_producer = Mock()

        # Mock embedding generation
        consumer._generate_batch_embeddings = Mock(return_value=[[0.1] * 384] * 2)

        # Mock bulk index
        mock_helpers.bulk.return_value = (2, [])

        processed = consumer.process_batch(timeout_ms=100)

        assert processed == 2
        assert consumer.metrics["events_skipped"] == 1
        assert consumer.metrics["embeddings_generated"] == 2

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_process_batch_embedding_failure(self):
        """Test batch processing when embedding generation fails."""
        consumer = VectorConsumer()

        # Mock message
        msg = Mock()
        event = EntityEvent(
            entity_id="p-1",
            event_type="create",
            entity_type="person",
            payload={},
            text_for_embedding="test",
        )
        msg.data.return_value = event.to_bytes()

        # Mock consumer
        mock_consumer = Mock()
        mock_consumer.receive.side_effect = [msg, Exception("Timeout")]
        consumer.consumer = mock_consumer

        # Mock embedding generation failure
        consumer._generate_batch_embeddings = Mock(side_effect=Exception("Model error"))

        processed = consumer.process_batch(timeout_ms=100)

        assert processed == 0
        # Should NACK on embedding failure
        mock_consumer.negative_acknowledge.assert_called_once_with(msg)

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.helpers")
    def test_process_batch_bulk_index_failure(self, mock_helpers):
        """Test batch processing when bulk index fails."""
        consumer = VectorConsumer()

        # Mock message
        msg = Mock()
        event = EntityEvent(
            entity_id="p-1",
            event_type="create",
            entity_type="person",
            payload={},
            text_for_embedding="test",
        )
        msg.data.return_value = event.to_bytes()

        # Mock consumer
        mock_consumer = Mock()
        mock_consumer.receive.side_effect = [msg, Exception("Timeout")]
        consumer.consumer = mock_consumer

        # Mock OpenSearch
        consumer.opensearch = Mock()

        # Mock embedding generation
        consumer._generate_batch_embeddings = Mock(return_value=[[0.1] * 384])

        # Mock bulk index failure
        mock_helpers.bulk.side_effect = Exception("Index error")

        processed = consumer.process_batch(timeout_ms=100)

        assert processed == 0
        assert consumer.metrics["events_failed"] == 1
        mock_consumer.negative_acknowledge.assert_called_once_with(msg)

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.helpers")
    def test_process_batch_delete_event(self, mock_helpers):
        """Test processing delete events."""
        consumer = VectorConsumer()

        # Mock delete message
        msg = Mock()
        event = EntityEvent(
            entity_id="p-1",
            event_type="delete",
            entity_type="person",
            payload={},
            text_for_embedding="test",  # Has text but will be deleted
        )
        msg.data.return_value = event.to_bytes()

        # Mock consumer
        mock_consumer = Mock()
        mock_consumer.receive.side_effect = [msg, Exception("Timeout")]
        consumer.consumer = mock_consumer

        # Mock OpenSearch
        consumer.opensearch = Mock()

        # Mock embedding generation
        consumer._generate_batch_embeddings = Mock(return_value=[[0.1] * 384])

        # Mock bulk index
        mock_helpers.bulk.return_value = (1, [])

        processed = consumer.process_batch(timeout_ms=100)

        assert processed == 1
        # Verify delete operation was created
        bulk_call = mock_helpers.bulk.call_args[0][1]
        assert bulk_call[0]["_op_type"] == "delete"


class TestVectorConsumerContinuousProcessing:
    """Test continuous processing."""

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_stop(self):
        """Test stopping continuous processing."""
        consumer = VectorConsumer()
        consumer._running = True

        consumer.stop()

        assert consumer._running is False


class TestVectorConsumerMetrics:
    """Test metrics tracking."""

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    def test_get_metrics(self):
        """Test getting metrics."""
        consumer = VectorConsumer()

        consumer.metrics["events_processed"] = 100
        consumer.metrics["events_skipped"] = 10
        consumer.metrics["embeddings_generated"] = 90

        metrics = consumer.get_metrics()

        assert metrics["events_processed"] == 100
        assert metrics["events_skipped"] == 10
        assert metrics["embeddings_generated"] == 90
        assert isinstance(metrics, dict)

        # Verify it's a copy
        metrics["events_processed"] = 200
        assert consumer.metrics["events_processed"] == 100


class TestVectorConsumerContextManager:
    """Test context manager usage."""

    @patch("banking.streaming.vector_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.OPENSEARCH_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.EMBEDDING_AVAILABLE", True)
    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    @patch("banking.streaming.vector_consumer.SentenceTransformer")
    @patch.dict("os.environ", {"OPENSEARCH_USE_SSL": "false"})
    def test_context_manager(self, mock_transformer, mock_opensearch_class, mock_pulsar):
        """Test using VectorConsumer as context manager."""
        # Setup mocks
        mock_client = Mock()
        mock_consumer_obj = Mock()
        mock_producer = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.subscribe.return_value = mock_consumer_obj
        mock_client.create_producer.return_value = mock_producer

        mock_opensearch = Mock()
        mock_opensearch.info.return_value = {"version": {"number": "2.0.0"}}
        mock_opensearch.indices.exists.return_value = True
        mock_opensearch_class.return_value = mock_opensearch

        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model

        consumer = VectorConsumer()

        with consumer as c:
            assert c == consumer
            assert c.pulsar_client is not None
            assert c.consumer is not None
            assert c.opensearch is not None

        # Verify disconnect was called
        mock_consumer_obj.close.assert_called_once()
        mock_producer.close.assert_called_once()
        mock_client.close.assert_called_once()


# Made with Bob
