"""Tests for banking.streaming consumer modules using mocks."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from banking.streaming.events import EntityEvent
from banking.streaming.graph_consumer import GREMLIN_AVAILABLE, PULSAR_AVAILABLE, GraphConsumer
from banking.streaming.vector_consumer import PULSAR_AVAILABLE as VP_AVAILABLE
from banking.streaming.vector_consumer import VectorConsumer


class TestGraphConsumerConstants:
    def test_defaults(self):
        assert GraphConsumer.DEFAULT_PULSAR_URL == "pulsar://localhost:6650"
        assert GraphConsumer.DEFAULT_JANUSGRAPH_URL == "ws://localhost:18182/gremlin"
        assert GraphConsumer.DEFAULT_SUBSCRIPTION == "graph-loaders"
        assert GraphConsumer.DEFAULT_BATCH_SIZE == 100
        assert GraphConsumer.DEFAULT_BATCH_TIMEOUT_MS == 100

    def test_default_topics(self):
        topics = GraphConsumer.DEFAULT_TOPICS
        assert len(topics) >= 4
        assert any("persons" in t for t in topics)
        assert any("accounts" in t for t in topics)
        assert any("transactions" in t for t in topics)

    @pytest.mark.skipif(
        not PULSAR_AVAILABLE or not GREMLIN_AVAILABLE, reason="Dependencies not available"
    )
    def test_init_default(self):
        consumer = GraphConsumer()
        assert consumer.pulsar_url == "pulsar://localhost:6650"
        assert consumer.batch_size == 100
        assert consumer.metrics["events_processed"] == 0

    @pytest.mark.skipif(
        not PULSAR_AVAILABLE or not GREMLIN_AVAILABLE, reason="Dependencies not available"
    )
    def test_init_custom(self):
        consumer = GraphConsumer(
            pulsar_url="pulsar://custom:6650",
            janusgraph_url="ws://custom:8182/gremlin",
            batch_size=50,
        )
        assert consumer.pulsar_url == "pulsar://custom:6650"
        assert consumer.janusgraph_url == "ws://custom:8182/gremlin"
        assert consumer.batch_size == 50

    @pytest.mark.skipif(
        not PULSAR_AVAILABLE or not GREMLIN_AVAILABLE, reason="Dependencies not available"
    )
    def test_disconnect_no_connections(self):
        consumer = GraphConsumer()
        consumer.disconnect()

    @pytest.mark.skipif(
        not PULSAR_AVAILABLE or not GREMLIN_AVAILABLE, reason="Dependencies not available"
    )
    def test_disconnect_with_connections(self):
        consumer = GraphConsumer()
        consumer.consumer = MagicMock()
        consumer.dlq_producer = MagicMock()
        consumer.pulsar_client = MagicMock()
        consumer.connection = MagicMock()
        consumer.disconnect()
        consumer.consumer.close.assert_called_once()
        consumer.dlq_producer.close.assert_called_once()
        consumer.pulsar_client.close.assert_called_once()
        consumer.connection.close.assert_called_once()

    @pytest.mark.skipif(
        not PULSAR_AVAILABLE or not GREMLIN_AVAILABLE, reason="Dependencies not available"
    )
    def test_process_event_create(self):
        consumer = GraphConsumer()
        mock_g = MagicMock()
        mock_traversal = MagicMock()
        mock_g.V.return_value = mock_traversal
        mock_traversal.has.return_value = mock_traversal
        mock_traversal.fold.return_value = mock_traversal
        mock_traversal.coalesce.return_value = mock_traversal
        mock_traversal.property.return_value = mock_traversal
        mock_traversal.iterate.return_value = None
        consumer.g = mock_g

        event = EntityEvent(
            entity_id="p-1",
            event_type="create",
            entity_type="person",
            payload={"first_name": "John", "last_name": "Smith"},
            source="test",
        )
        result = consumer.process_event(event)
        assert isinstance(result, bool)


class TestVectorConsumerConstants:
    def test_defaults(self):
        assert VectorConsumer.DEFAULT_PULSAR_URL == "pulsar://localhost:6650"
        assert VectorConsumer.DEFAULT_OPENSEARCH_HOST == "localhost"
        assert VectorConsumer.DEFAULT_OPENSEARCH_PORT == 9200
        assert VectorConsumer.DEFAULT_SUBSCRIPTION == "vector-loaders"
        assert VectorConsumer.DEFAULT_BATCH_SIZE == 100
        assert VectorConsumer.DEFAULT_EMBEDDING_MODEL == "all-MiniLM-L6-v2"

    def test_default_topics(self):
        topics = VectorConsumer.DEFAULT_TOPICS
        assert len(topics) >= 2
        assert any("persons" in t for t in topics)

    def test_index_mapping(self):
        mapping = VectorConsumer.INDEX_MAPPING
        assert "person" in mapping
        assert "company" in mapping

    @pytest.mark.skipif(not VP_AVAILABLE, reason="Pulsar not available")
    def test_init_custom(self):
        try:
            consumer = VectorConsumer(
                pulsar_url="pulsar://custom:6650",
                opensearch_host="custom-os",
                opensearch_port=9201,
                batch_size=50,
            )
            assert consumer.pulsar_url == "pulsar://custom:6650"
            assert consumer.opensearch_host == "custom-os"
            assert consumer.opensearch_port == 9201
        except ImportError:
            pytest.skip("opensearch-py not installed")

    @pytest.mark.skipif(not VP_AVAILABLE, reason="Pulsar not available")
    def test_disconnect_no_connections(self):
        try:
            consumer = VectorConsumer()
            consumer.disconnect()
        except ImportError:
            pytest.skip("opensearch-py not installed")
