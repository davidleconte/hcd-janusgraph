"""
Unit tests for VectorConsumer.

Tests the OpenSearch vector consumer with mocked dependencies.
All tests are deterministic with fixed timestamps and mocked external services.

Created: 2026-04-07
"""

import sys
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch, call

import pytest

# Mock pulsar before importing VectorConsumer
mock_pulsar = MagicMock()
mock_pulsar.Client = MagicMock
mock_pulsar.Consumer = MagicMock
mock_pulsar.ConsumerType = MagicMock()
mock_pulsar.ConsumerType.KeyShared = "KeyShared"
sys.modules['pulsar'] = mock_pulsar

# Mock opensearchpy
mock_opensearch = MagicMock()
mock_opensearch.OpenSearch = MagicMock
mock_opensearch.helpers = MagicMock()
sys.modules['opensearchpy'] = mock_opensearch

# Mock sentence_transformers
mock_sentence_transformers = MagicMock()
mock_sentence_transformers.SentenceTransformer = MagicMock
sys.modules['sentence_transformers'] = mock_sentence_transformers

from banking.streaming.vector_consumer import VectorConsumer
from banking.streaming.events import EntityEvent

# Fixed timestamp for deterministic tests
FIXED_TIMESTAMP = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def mock_opensearch_client():
    """Mock OpenSearch client."""
    client = MagicMock()
    client.info.return_value = {"version": {"number": "2.11.0"}}
    client.indices.exists.return_value = False
    client.indices.create.return_value = {"acknowledged": True}
    return client


@pytest.fixture
def mock_pulsar_client():
    """Mock Pulsar client."""
    client = MagicMock()
    consumer = MagicMock()
    producer = MagicMock()
    
    client.subscribe.return_value = consumer
    client.create_producer.return_value = producer
    
    return client, consumer, producer


@pytest.fixture
def mock_embedding_model():
    """Mock SentenceTransformer model."""
    model = MagicMock()
    model.get_sentence_embedding_dimension.return_value = 384
    model.encode.return_value = [[0.1] * 384]
    return model


@pytest.fixture
def sample_person_event():
    """Create a sample person event."""
    return EntityEvent(
        entity_id="p-123",
        entity_type="person",
        event_type="create",
        timestamp=FIXED_TIMESTAMP,
        version=1,
        source="test",
        text_for_embedding="John Doe, age 30, software engineer",
        payload={"name": "John Doe", "age": 30}
    )


@pytest.fixture
def sample_company_event():
    """Create a sample company event."""
    return EntityEvent(
        entity_id="c-456",
        entity_type="company",
        event_type="create",
        timestamp=FIXED_TIMESTAMP,
        version=1,
        source="test",
        text_for_embedding="Acme Corp, technology company",
        payload={"name": "Acme Corp"}
    )


class TestVectorConsumerInitialization:
    """Test VectorConsumer initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        consumer = VectorConsumer()
        
        assert consumer.pulsar_url == "pulsar://localhost:6650"
        assert consumer.opensearch_host == "localhost"
        assert consumer.opensearch_port == 9200
        assert consumer.embedding_model_name == "all-MiniLM-L6-v2"
        assert consumer.subscription_name == "vector-loaders"
        assert consumer.batch_size == 100
        assert consumer.batch_timeout_ms == 100
        assert consumer.topics == [
            "persistent://public/banking/persons-events",
            "persistent://public/banking/companies-events",
        ]

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        consumer = VectorConsumer(
            pulsar_url="pulsar://custom:6650",
            opensearch_host="custom-host",
            opensearch_port=9300,
            embedding_model="custom-model",
            topics=["custom-topic"],
            subscription_name="custom-sub",
            batch_size=50,
            batch_timeout_ms=200,
            dlq_topic="custom-dlq"
        )
        
        assert consumer.pulsar_url == "pulsar://custom:6650"
        assert consumer.opensearch_host == "custom-host"
        assert consumer.opensearch_port == 9300
        assert consumer.embedding_model_name == "custom-model"
        assert consumer.topics == ["custom-topic"]
        assert consumer.subscription_name == "custom-sub"
        assert consumer.batch_size == 50
        assert consumer.batch_timeout_ms == 200
        assert consumer.dlq_topic == "custom-dlq"

    def test_init_metrics_initialized(self):
        """Test that metrics are initialized to zero."""
        consumer = VectorConsumer()
        
        assert consumer.metrics["events_processed"] == 0
        assert consumer.metrics["events_skipped"] == 0
        assert consumer.metrics["events_failed"] == 0
        assert consumer.metrics["batches_processed"] == 0
        assert consumer.metrics["embeddings_generated"] == 0
        assert consumer.metrics["last_batch_time"] is None

    def test_init_state_initialized(self):
        """Test that state is initialized correctly."""
        consumer = VectorConsumer()
        
        assert consumer.pulsar_client is None
        assert consumer.consumer is None
        assert consumer.dlq_producer is None
        assert consumer.opensearch is None
        assert consumer.embedding_model is None
        assert consumer._running is False


class TestVectorConsumerConnection:
    """Test VectorConsumer connection management."""

    @patch('banking.streaming.vector_consumer.pulsar')
    @patch('banking.streaming.vector_consumer.OpenSearch')
    @patch('banking.streaming.vector_consumer.SentenceTransformer')
    def test_connect_establishes_all_connections(
        self, mock_st, mock_os, mock_pulsar_module, mock_opensearch_client
    ):
        """Test that connect establishes all required connections."""
        # Setup mocks
        mock_pulsar_client = MagicMock()
        mock_consumer = MagicMock()
        mock_producer = MagicMock()
        mock_pulsar_module.Client.return_value = mock_pulsar_client
        mock_pulsar_client.subscribe.return_value = mock_consumer
        mock_pulsar_client.create_producer.return_value = mock_producer
        
        mock_os.return_value = mock_opensearch_client
        mock_embedding = MagicMock()
        mock_embedding.get_sentence_embedding_dimension.return_value = 384
        mock_st.return_value = mock_embedding
        
        consumer = VectorConsumer()
        consumer.connect()
        
        # Verify Pulsar connection
        mock_pulsar_module.Client.assert_called_once_with("pulsar://localhost:6650")
        assert consumer.pulsar_client == mock_pulsar_client
        
        # Verify consumer subscription
        mock_pulsar_client.subscribe.assert_called_once()
        assert consumer.consumer == mock_consumer
        
        # Verify DLQ producer
        mock_pulsar_client.create_producer.assert_called_once()
        assert consumer.dlq_producer == mock_producer
        
        # Verify OpenSearch connection
        mock_os.assert_called_once()
        assert consumer.opensearch == mock_opensearch_client
        
        # Verify embedding model loaded
        mock_st.assert_called_once_with("all-MiniLM-L6-v2")
        assert consumer.embedding_model == mock_embedding

    @patch('banking.streaming.vector_consumer.pulsar')
    @patch('banking.streaming.vector_consumer.OpenSearch')
    def test_connect_creates_indices(self, mock_os, mock_pulsar_module, mock_opensearch_client):
        """Test that connect creates OpenSearch indices."""
        mock_pulsar_client = MagicMock()
        mock_pulsar_module.Client.return_value = mock_pulsar_client
        mock_pulsar_client.subscribe.return_value = MagicMock()
        mock_pulsar_client.create_producer.return_value = MagicMock()
        
        mock_os.return_value = mock_opensearch_client
        
        consumer = VectorConsumer()
        consumer.connect()
        
        # Verify indices checked
        assert mock_opensearch_client.indices.exists.call_count == 2
        
        # Verify indices created
        assert mock_opensearch_client.indices.create.call_count == 2

    def test_disconnect_closes_all_connections(self):
        """Test that disconnect closes all connections."""
        consumer = VectorConsumer()
        consumer.pulsar_client = MagicMock()
        consumer.consumer = MagicMock()
        consumer.dlq_producer = MagicMock()
        
        consumer.disconnect()
        
        consumer.consumer.close.assert_called_once()
        consumer.dlq_producer.close.assert_called_once()
        consumer.pulsar_client.close.assert_called_once()


class TestVectorConsumerEmbedding:
    """Test embedding generation."""

    def test_generate_embedding_with_model(self, mock_embedding_model):
        """Test embedding generation with loaded model."""
        consumer = VectorConsumer()
        consumer.embedding_model = mock_embedding_model
        mock_embedding_model.encode.return_value = [0.1] * 384
        
        embedding = consumer._generate_embedding("test text")
        
        assert len(embedding) == 384
        mock_embedding_model.encode.assert_called_once_with("test text")

    def test_generate_embedding_without_model(self):
        """Test embedding generation without model (placeholder)."""
        consumer = VectorConsumer()
        consumer.embedding_model = None
        
        embedding = consumer._generate_embedding("test text")
        
        assert len(embedding) == 384
        assert all(x == 0.0 for x in embedding)

    def test_generate_batch_embeddings_with_model(self, mock_embedding_model):
        """Test batch embedding generation with loaded model."""
        consumer = VectorConsumer()
        consumer.embedding_model = mock_embedding_model
        mock_embedding_model.encode.return_value = [[0.1] * 384, [0.2] * 384]
        
        texts = ["text1", "text2"]
        embeddings = consumer._generate_batch_embeddings(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384
        mock_embedding_model.encode.assert_called_once_with(texts)

    def test_generate_batch_embeddings_without_model(self):
        """Test batch embedding generation without model."""
        consumer = VectorConsumer()
        consumer.embedding_model = None
        
        texts = ["text1", "text2"]
        embeddings = consumer._generate_batch_embeddings(texts)
        
        assert len(embeddings) == 2
        assert all(len(e) == 384 for e in embeddings)
        assert all(all(x == 0.0 for x in e) for e in embeddings)


class TestVectorConsumerIndexMapping:
    """Test index name mapping."""

    def test_get_index_name_person(self):
        """Test index name for person entity."""
        consumer = VectorConsumer()
        assert consumer._get_index_name("person") == "person_vectors"

    def test_get_index_name_company(self):
        """Test index name for company entity."""
        consumer = VectorConsumer()
        assert consumer._get_index_name("company") == "company_vectors"

    def test_get_index_name_unknown(self):
        """Test index name for unknown entity type."""
        consumer = VectorConsumer()
        assert consumer._get_index_name("unknown") == "unknown_vectors"


class TestVectorConsumerBatchCollection:
    """Test batch collection from Pulsar."""

    def test_collect_batch_empty(self):
        """Test collecting empty batch."""
        consumer = VectorConsumer()
        consumer.consumer = MagicMock()
        consumer.consumer.receive.side_effect = Exception("Timeout")
        
        batch, messages = consumer._collect_batch(timeout_ms=100)
        
        assert len(batch) == 0
        assert len(messages) == 0

    def test_collect_batch_single_event(self, sample_person_event):
        """Test collecting single event."""
        consumer = VectorConsumer()
        consumer.consumer = MagicMock()
        
        mock_message = MagicMock()
        mock_message.data.return_value = sample_person_event.to_bytes()
        consumer.consumer.receive.side_effect = [mock_message, Exception("Timeout")]
        
        batch, messages = consumer._collect_batch(timeout_ms=100)
        
        assert len(batch) == 1
        assert len(messages) == 1
        assert batch[0].entity_id == "p-123"

    def test_collect_batch_respects_batch_size(self, sample_person_event):
        """Test that batch collection respects batch size limit."""
        consumer = VectorConsumer()
        consumer.batch_size = 2
        consumer.consumer = MagicMock()
        
        mock_message = MagicMock()
        mock_message.data.return_value = sample_person_event.to_bytes()
        consumer.consumer.receive.return_value = mock_message
        
        batch, messages = consumer._collect_batch(timeout_ms=1000)
        
        assert len(batch) == 2
        assert len(messages) == 2


class TestVectorConsumerEventPartitioning:
    """Test event partitioning logic."""

    def test_split_embeddable_events_all_embeddable(self, sample_person_event, sample_company_event):
        """Test splitting when all events are embeddable."""
        batch = [sample_person_event, sample_company_event]
        
        embeddable, non_embeddable = VectorConsumer._split_embeddable_events(batch)
        
        assert len(embeddable) == 2
        assert len(non_embeddable) == 0

    def test_split_embeddable_events_none_embeddable(self):
        """Test splitting when no events are embeddable."""
        event1 = EntityEvent(
            entity_id="p-1",
            entity_type="person",
            event_type="create",
            timestamp=FIXED_TIMESTAMP,
            version=1,
            source="test",
            text_for_embedding=None,
            payload={}
        )
        event2 = EntityEvent(
            entity_id="p-2",
            entity_type="person",
            event_type="create",
            timestamp=FIXED_TIMESTAMP,
            version=1,
            source="test",
            text_for_embedding="",
            payload={}
        )
        batch = [event1, event2]
        
        embeddable, non_embeddable = VectorConsumer._split_embeddable_events(batch)
        
        assert len(embeddable) == 0
        assert len(non_embeddable) == 2

    def test_split_embeddable_events_mixed(self, sample_person_event):
        """Test splitting with mixed embeddable/non-embeddable events."""
        event_no_text = EntityEvent(
            entity_id="p-2",
            entity_type="person",
            event_type="create",
            timestamp=FIXED_TIMESTAMP,
            version=1,
            source="test",
            text_for_embedding=None,
            payload={}
        )
        batch = [sample_person_event, event_no_text]
        
        embeddable, non_embeddable = VectorConsumer._split_embeddable_events(batch)
        
        assert len(embeddable) == 1
        assert len(non_embeddable) == 1
        assert embeddable[0][1].entity_id == "p-123"
        assert non_embeddable[0][1].entity_id == "p-2"


class TestVectorConsumerAcknowledgement:
    """Test message acknowledgement."""

    def test_ack_non_embeddable_events(self):
        """Test acknowledging non-embeddable events."""
        consumer = VectorConsumer()
        consumer.consumer = MagicMock()
        
        event = EntityEvent(
            entity_id="p-1",
            entity_type="person",
            event_type="create",
            timestamp=FIXED_TIMESTAMP,
            version=1,
            source="test",
            text_for_embedding=None,
            payload={}
        )
        non_embeddable = [(0, event), (1, event)]
        messages = [MagicMock(), MagicMock()]
        
        consumer._ack_non_embeddable_events(non_embeddable, messages)
        
        assert consumer.consumer.acknowledge.call_count == 2
        assert consumer.metrics["events_skipped"] == 2


class TestVectorConsumerBulkActions:
    """Test bulk action building."""

    def test_build_bulk_actions_create(self, sample_person_event):
        """Test building bulk actions for create event."""
        consumer = VectorConsumer()
        embeddable = [(0, sample_person_event)]
        embeddings = [[0.1] * 384]
        
        actions, indices = consumer._build_bulk_actions(embeddable, embeddings)
        
        assert len(actions) == 1
        assert len(indices) == 1
        assert actions[0]["_op_type"] == "index"
        assert actions[0]["_index"] == "person_vectors"
        assert actions[0]["_id"] == "p-123"
        assert actions[0]["_source"]["entity_id"] == "p-123"
        assert len(actions[0]["_source"]["embedding"]) == 384

    def test_build_bulk_actions_delete(self):
        """Test building bulk actions for delete event."""
        consumer = VectorConsumer()
        delete_event = EntityEvent(
            entity_id="p-123",
            entity_type="person",
            event_type="delete",
            timestamp=FIXED_TIMESTAMP,
            version=2,
            source="test",
            text_for_embedding="deleted",
            payload={}
        )
        embeddable = [(0, delete_event)]
        embeddings = [[0.1] * 384]
        
        actions, indices = consumer._build_bulk_actions(embeddable, embeddings)
        
        assert len(actions) == 1
        assert actions[0]["_op_type"] == "delete"
        assert actions[0]["_index"] == "person_vectors"
        assert actions[0]["_id"] == "p-123"

    def test_build_bulk_actions_multiple(self, sample_person_event, sample_company_event):
        """Test building bulk actions for multiple events."""
        consumer = VectorConsumer()
        embeddable = [(0, sample_person_event), (1, sample_company_event)]
        embeddings = [[0.1] * 384, [0.2] * 384]
        
        actions, indices = consumer._build_bulk_actions(embeddable, embeddings)
        
        assert len(actions) == 2
        assert len(indices) == 2
        assert actions[0]["_index"] == "person_vectors"
        assert actions[1]["_index"] == "company_vectors"


class TestVectorConsumerBulkIndexing:
    """Test bulk indexing to OpenSearch."""

    def test_bulk_index_actions_success(self):
        """Test successful bulk indexing."""
        consumer = VectorConsumer()
        consumer.opensearch = MagicMock()
        consumer.consumer = MagicMock()
        
        # Mock helpers.bulk to return success
        with patch('banking.streaming.vector_consumer.helpers') as mock_helpers:
            mock_helpers.bulk.return_value = (2, [])
            
            actions = [{"_op_type": "index"}, {"_op_type": "index"}]
            indices = [0, 1]
            messages = [MagicMock(), MagicMock()]
            
            success = consumer._bulk_index_actions(actions, indices, messages)
            
            assert success == 2
            assert consumer.metrics["events_processed"] == 2
            assert consumer.consumer.acknowledge.call_count == 2

    def test_bulk_index_actions_partial_errors(self):
        """Test bulk indexing with partial errors."""
        consumer = VectorConsumer()
        consumer.opensearch = MagicMock()
        consumer.consumer = MagicMock()
        
        with patch('banking.streaming.vector_consumer.helpers') as mock_helpers:
            mock_helpers.bulk.return_value = (1, [{"error": "failed"}])
            
            actions = [{"_op_type": "index"}, {"_op_type": "index"}]
            indices = [0, 1]
            messages = [MagicMock(), MagicMock()]
            
            success = consumer._bulk_index_actions(actions, indices, messages)
            
            assert success == 1
            assert consumer.metrics["events_processed"] == 1
            assert consumer.metrics["events_failed"] == 1

    def test_bulk_index_actions_failure(self):
        """Test bulk indexing complete failure."""
        consumer = VectorConsumer()
        consumer.opensearch = MagicMock()
        consumer.consumer = MagicMock()
        
        with patch('banking.streaming.vector_consumer.helpers') as mock_helpers:
            mock_helpers.bulk.side_effect = Exception("Connection failed")
            
            actions = [{"_op_type": "index"}]
            indices = [0]
            messages = [MagicMock()]
            
            success = consumer._bulk_index_actions(actions, indices, messages)
            
            assert success == 0
            assert consumer.metrics["events_failed"] == 1
            assert consumer.consumer.negative_acknowledge.call_count == 1


class TestVectorConsumerMetrics:
    """Test metrics collection."""

    def test_get_metrics_returns_copy(self):
        """Test that get_metrics returns a copy."""
        consumer = VectorConsumer()
        consumer.metrics["events_processed"] = 10
        
        metrics = consumer.get_metrics()
        metrics["events_processed"] = 20
        
        assert consumer.metrics["events_processed"] == 10

    def test_metrics_updated_on_processing(self):
        """Test that metrics are updated during processing."""
        consumer = VectorConsumer()
        consumer.consumer = MagicMock()
        consumer.opensearch = MagicMock()
        consumer.embedding_model = MagicMock()
        consumer.embedding_model.encode.return_value = [[0.1] * 384]
        
        # Mock batch collection
        event = EntityEvent(
            entity_id="p-1",
            entity_type="person",
            event_type="create",
            timestamp=FIXED_TIMESTAMP,
            version=1,
            source="test",
            text_for_embedding="test",
            payload={}
        )
        mock_message = MagicMock()
        mock_message.data.return_value = event.to_bytes()
        consumer.consumer.receive.side_effect = [mock_message, Exception("Timeout")]
        
        # Mock bulk indexing
        with patch('banking.streaming.vector_consumer.helpers') as mock_helpers:
            mock_helpers.bulk.return_value = (1, [])
            
            consumer.process_batch()
            
            assert consumer.metrics["events_processed"] == 1
            assert consumer.metrics["batches_processed"] == 1
            assert consumer.metrics["embeddings_generated"] == 1


class TestVectorConsumerContextManager:
    """Test context manager protocol."""

    @patch('banking.streaming.vector_consumer.pulsar')
    @patch('banking.streaming.vector_consumer.OpenSearch')
    def test_context_manager_enter(self, mock_os, mock_pulsar_module):
        """Test context manager __enter__."""
        mock_pulsar_client = MagicMock()
        mock_pulsar_module.Client.return_value = mock_pulsar_client
        mock_pulsar_client.subscribe.return_value = MagicMock()
        mock_pulsar_client.create_producer.return_value = MagicMock()
        
        mock_opensearch_client = MagicMock()
        mock_opensearch_client.info.return_value = {"version": {"number": "2.11.0"}}
        mock_opensearch_client.indices.exists.return_value = True
        mock_os.return_value = mock_opensearch_client
        
        consumer = VectorConsumer()
        
        with consumer as c:
            assert c == consumer
            assert consumer.pulsar_client is not None
            assert consumer.opensearch is not None

    def test_context_manager_exit(self):
        """Test context manager __exit__."""
        consumer = VectorConsumer()
        consumer.pulsar_client = MagicMock()
        consumer.consumer = MagicMock()
        consumer.dlq_producer = MagicMock()
        
        consumer.__exit__(None, None, None)
        
        consumer.consumer.close.assert_called_once()
        consumer.dlq_producer.close.assert_called_once()
        consumer.pulsar_client.close.assert_called_once()

    def test_context_manager_exit_with_exception(self):
        """Test context manager __exit__ with exception."""
        consumer = VectorConsumer()
        consumer.pulsar_client = MagicMock()
        consumer.consumer = MagicMock()
        consumer.dlq_producer = MagicMock()
        
        result = consumer.__exit__(ValueError, ValueError("test"), None)
        
        assert result is False  # Don't suppress exceptions
        consumer.consumer.close.assert_called_once()


class TestVectorConsumerProcessing:
    """Test event processing."""

    def test_stop_sets_running_flag(self):
        """Test that stop() sets _running flag."""
        consumer = VectorConsumer()
        consumer._running = True
        
        consumer.stop()
        
        assert consumer._running is False

    def test_process_batch_returns_zero_on_empty(self):
        """Test process_batch returns 0 for empty batch."""
        consumer = VectorConsumer()
        consumer.consumer = MagicMock()
        consumer.consumer.receive.side_effect = Exception("Timeout")
        
        result = consumer.process_batch()
        
        assert result == 0

    def test_process_batch_skips_non_embeddable(self):
        """Test process_batch skips events without text."""
        consumer = VectorConsumer()
        consumer.consumer = MagicMock()
        
        event = EntityEvent(
            entity_id="p-1",
            entity_type="person",
            event_type="create",
            timestamp=FIXED_TIMESTAMP,
            version=1,
            source="test",
            text_for_embedding=None,
            payload={}
        )
        mock_message = MagicMock()
        mock_message.data.return_value = event.to_bytes()
        consumer.consumer.receive.side_effect = [mock_message, Exception("Timeout")]
        
        result = consumer.process_batch()
        
        assert result == 0
        assert consumer.metrics["events_skipped"] == 1


class TestVectorConsumerEdgeCases:
    """Tests for edge cases and uncovered lines in VectorConsumer."""

    def test_import_error_pulsar_not_available(self):
        """Test ImportError when pulsar is not available (lines 29-31)."""
        # Temporarily set PULSAR_AVAILABLE to False
        import banking.streaming.vector_consumer as vc_module
        original_value = vc_module.PULSAR_AVAILABLE
        try:
            vc_module.PULSAR_AVAILABLE = False
            with pytest.raises(ImportError, match="pulsar-client is not installed"):
                VectorConsumer()
        finally:
            vc_module.PULSAR_AVAILABLE = original_value

    def test_import_error_opensearch_not_available(self):
        """Test ImportError when opensearch is not available (lines 37-38)."""
        # Temporarily set OPENSEARCH_AVAILABLE to False
        import banking.streaming.vector_consumer as vc_module
        original_pulsar = vc_module.PULSAR_AVAILABLE
        original_opensearch = vc_module.OPENSEARCH_AVAILABLE
        try:
            vc_module.PULSAR_AVAILABLE = True
            vc_module.OPENSEARCH_AVAILABLE = False
            with pytest.raises(ImportError, match="opensearch-py is not installed"):
                VectorConsumer()
        finally:
            vc_module.PULSAR_AVAILABLE = original_pulsar
            vc_module.OPENSEARCH_AVAILABLE = original_opensearch

    def test_import_error_embedding_not_available(self):
        """Test behavior when sentence_transformers is not available (line 43)."""
        # This is handled gracefully - EMBEDDING_AVAILABLE flag is checked
        import banking.streaming.vector_consumer as vc_module
        original_value = vc_module.EMBEDDING_AVAILABLE
        try:
            vc_module.EMBEDDING_AVAILABLE = False
            # Should still be able to create consumer, but embedding will fail
            consumer = VectorConsumer()
            assert consumer is not None
        finally:
            vc_module.EMBEDDING_AVAILABLE = original_value

    def test_init_with_environment_variables(self):
        """Test initialization with environment variables (lines 119-121)."""
        with patch.dict('os.environ', {
            'PULSAR_URL': 'pulsar://test:6650',
            'OPENSEARCH_HOST': 'test-host',
            'OPENSEARCH_PORT': '9300'
        }):
            consumer = VectorConsumer()
            assert consumer.pulsar_url == 'pulsar://test:6650'
            assert consumer.opensearch_host == 'test-host'
            assert consumer.opensearch_port == 9300

    def test_process_batch_with_decode_error(self):
        """Test process_batch handles decode errors gracefully."""
        consumer = VectorConsumer()
        consumer.consumer = MagicMock()
        
        # Create a message with invalid data
        mock_message = MagicMock()
        mock_message.data.return_value = b'invalid json data'
        consumer.consumer.receive.side_effect = [mock_message, Exception("Timeout")]
        
        result = consumer.process_batch()
        
        # Should handle error and return 0
        assert result == 0

    def test_generate_batch_embeddings_empty(self):
        """Test _generate_batch_embeddings with empty batch."""
        consumer = VectorConsumer()
        consumer.embedding_model = MagicMock()
        
        result = consumer._generate_batch_embeddings([])
        
        # Empty list is still passed to encode, so it will be called
        assert result == []

    def test_bulk_index_actions_with_opensearch_error(self):
        """Test _bulk_index_actions handles OpenSearch errors."""
        consumer = VectorConsumer()
        consumer.opensearch = MagicMock()
        consumer.consumer = MagicMock()  # Need to mock consumer for negative_acknowledge
        
        # Mock helpers.bulk to raise an exception
        with patch('banking.streaming.vector_consumer.helpers') as mock_helpers:
            mock_helpers.bulk.side_effect = Exception("OpenSearch error")
            
            actions = [{"_index": "test", "_id": "1", "_source": {"data": "test"}}]
            messages = [MagicMock()]
            result = consumer._bulk_index_actions(actions, [0], messages)
            
            # Should handle error gracefully and nack the message
            assert result == 0
            consumer.consumer.negative_acknowledge.assert_called_once()

    def test_disconnect_with_no_connections(self):
        """Test disconnect() when connections are not established."""
        consumer = VectorConsumer()
        # Don't call connect(), so connections are None
        
        # Should not raise an error
        consumer.disconnect()
        
        assert consumer._running is False

# Made with Bob
