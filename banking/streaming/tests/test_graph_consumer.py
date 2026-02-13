"""
Unit tests for GraphConsumer.

Tests cover:
- Initialization and configuration
- Connection management (Pulsar, JanusGraph)
- Event processing (create, update, delete)
- Batch processing
- Error handling and DLQ
- Metrics tracking
- Context manager usage

Created: 2026-02-11
Week 2 Day 10: GraphConsumer Tests
"""

from unittest.mock import Mock, patch

import pytest

from banking.streaming.events import EntityEvent
from banking.streaming.graph_consumer import GraphConsumer


class TestGraphConsumerInitialization:
    """Test GraphConsumer initialization and configuration."""

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        consumer = GraphConsumer()

        assert consumer.pulsar_url == GraphConsumer.DEFAULT_PULSAR_URL
        assert consumer.janusgraph_url == GraphConsumer.DEFAULT_JANUSGRAPH_URL
        assert consumer.topics == GraphConsumer.DEFAULT_TOPICS
        assert consumer.subscription_name == GraphConsumer.DEFAULT_SUBSCRIPTION
        assert consumer.batch_size == GraphConsumer.DEFAULT_BATCH_SIZE
        assert consumer.batch_timeout_ms == GraphConsumer.DEFAULT_BATCH_TIMEOUT_MS
        assert consumer.dlq_topic == "persistent://public/banking/dlq-events"

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        consumer = GraphConsumer(
            pulsar_url="pulsar://custom:6650",
            janusgraph_url="ws://custom:8182/gremlin",
            topics=["custom-topic"],
            subscription_name="custom-sub",
            batch_size=50,
            batch_timeout_ms=200,
            dlq_topic="custom-dlq",
        )

        assert consumer.pulsar_url == "pulsar://custom:6650"
        assert consumer.janusgraph_url == "ws://custom:8182/gremlin"
        assert consumer.topics == ["custom-topic"]
        assert consumer.subscription_name == "custom-sub"
        assert consumer.batch_size == 50
        assert consumer.batch_timeout_ms == 200
        assert consumer.dlq_topic == "custom-dlq"

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", False)
    def test_init_without_pulsar(self):
        """Test initialization fails without pulsar-client."""
        with pytest.raises(ImportError, match="pulsar-client is not installed"):
            GraphConsumer()

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", False)
    def test_init_without_gremlin(self):
        """Test initialization fails without gremlinpython."""
        with pytest.raises(ImportError, match="gremlinpython is not installed"):
            GraphConsumer()

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_initial_state(self):
        """Test initial state of consumer."""
        consumer = GraphConsumer()

        assert consumer.pulsar_client is None
        assert consumer.consumer is None
        assert consumer.dlq_producer is None
        assert consumer.g is None
        assert consumer.connection is None
        assert consumer._running is False

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_initial_metrics(self):
        """Test initial metrics state."""
        consumer = GraphConsumer()

        assert consumer.metrics["events_processed"] == 0
        assert consumer.metrics["events_failed"] == 0
        assert consumer.metrics["batches_processed"] == 0
        assert consumer.metrics["last_batch_time"] is None


class TestGraphConsumerConnection:
    """Test connection management."""

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_connect_success(self, mock_traversal, mock_driver, mock_pulsar):
        """Test successful connection to Pulsar and JanusGraph."""
        # Setup mocks
        mock_client = Mock()
        mock_consumer = Mock()
        mock_producer = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.subscribe.return_value = mock_consumer
        mock_client.create_producer.return_value = mock_producer

        mock_connection = Mock()
        mock_driver.return_value = mock_connection

        mock_g = Mock()
        mock_traversal.return_value.with_remote.return_value = mock_g

        consumer = GraphConsumer()
        consumer.connect()

        # Verify Pulsar connection
        mock_pulsar.Client.assert_called_once_with(consumer.pulsar_url)
        mock_client.subscribe.assert_called_once()
        mock_client.create_producer.assert_called_once_with(consumer.dlq_topic)

        # Verify JanusGraph connection
        mock_driver.assert_called_once_with(consumer.janusgraph_url, "g")
        mock_traversal.return_value.with_remote.assert_called_once_with(mock_connection)

        assert consumer.pulsar_client == mock_client
        assert consumer.consumer == mock_consumer
        assert consumer.dlq_producer == mock_producer
        assert consumer.connection == mock_connection
        assert consumer.g == mock_g

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.pulsar")
    def test_connect_pulsar_failure(self, mock_pulsar):
        """Test connection failure to Pulsar."""
        mock_pulsar.Client.side_effect = Exception("Connection failed")

        consumer = GraphConsumer()

        with pytest.raises(Exception, match="Connection failed"):
            consumer.connect()

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_disconnect(self):
        """Test disconnection closes all resources."""
        consumer = GraphConsumer()

        # Mock connections
        consumer.consumer = Mock()
        consumer.dlq_producer = Mock()
        consumer.pulsar_client = Mock()
        consumer.connection = Mock()

        consumer.disconnect()

        consumer.consumer.close.assert_called_once()
        consumer.dlq_producer.close.assert_called_once()
        consumer.pulsar_client.close.assert_called_once()
        consumer.connection.close.assert_called_once()

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_disconnect_with_none_connections(self):
        """Test disconnect handles None connections gracefully."""
        consumer = GraphConsumer()

        # All connections are None
        consumer.disconnect()  # Should not raise exception


class TestGraphConsumerEventProcessing:
    """Test event processing logic."""

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_process_create_event(self):
        """Test processing a create event."""
        consumer = GraphConsumer()

        # Mock graph traversal
        mock_g = Mock()
        mock_traversal = Mock()
        mock_g.V.return_value = mock_traversal
        mock_traversal.has.return_value = mock_traversal
        mock_traversal.fold.return_value = mock_traversal
        mock_traversal.coalesce.return_value = mock_traversal
        mock_traversal.property.return_value = mock_traversal
        mock_traversal.iterate.return_value = None

        consumer.g = mock_g

        event = EntityEvent(
            entity_id="p-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John Doe", "age": 30},
            version=1,
        )

        result = consumer.process_event(event)

        assert result is True
        mock_g.V.assert_called_once()
        mock_traversal.iterate.assert_called_once()

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_process_update_event(self):
        """Test processing an update event."""
        consumer = GraphConsumer()

        # Mock graph traversal for version check
        mock_g = Mock()
        mock_traversal = Mock()
        mock_g.V.return_value = mock_traversal
        mock_traversal.has.return_value = mock_traversal
        mock_traversal.value_map.return_value = mock_traversal
        mock_traversal.toList.return_value = [{"version": [0]}]  # Current version
        mock_traversal.property.return_value = mock_traversal
        mock_traversal.iterate.return_value = None

        consumer.g = mock_g

        event = EntityEvent(
            entity_id="p-123",
            event_type="update",
            entity_type="person",
            payload={"name": "John Updated"},
            version=2,
        )

        result = consumer.process_event(event)

        assert result is True
        assert mock_g.V.call_count >= 2  # Once for check, once for update

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_process_update_stale_version(self):
        """Test update with stale version is skipped."""
        consumer = GraphConsumer()

        # Mock graph traversal with higher current version
        mock_g = Mock()
        mock_traversal = Mock()
        mock_g.V.return_value = mock_traversal
        mock_traversal.has.return_value = mock_traversal
        mock_traversal.value_map.return_value = mock_traversal
        mock_traversal.toList.return_value = [{"version": [5]}]  # Higher version

        consumer.g = mock_g

        event = EntityEvent(
            entity_id="p-123",
            event_type="update",
            entity_type="person",
            payload={"name": "John"},
            version=2,  # Lower than current
        )

        result = consumer.process_event(event)

        assert result is True  # Returns True but skips update
        # Should not call iterate() for update
        mock_traversal.iterate.assert_not_called()

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_process_delete_event(self):
        """Test processing a delete event."""
        consumer = GraphConsumer()

        # Mock graph traversal
        mock_g = Mock()
        mock_traversal = Mock()
        mock_g.V.return_value = mock_traversal
        mock_traversal.has.return_value = mock_traversal
        mock_traversal.drop.return_value = mock_traversal
        mock_traversal.iterate.return_value = None

        consumer.g = mock_g

        event = EntityEvent(
            entity_id="p-123",
            event_type="delete",
            entity_type="person",
            payload={},
        )

        result = consumer.process_event(event)

        assert result is True
        mock_g.V.assert_called_once()
        mock_traversal.drop.assert_called_once()
        mock_traversal.iterate.assert_called_once()

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_process_event_with_exception(self):
        """Test event processing handles exceptions."""
        consumer = GraphConsumer()

        # Mock graph traversal that raises exception
        mock_g = Mock()
        mock_g.V.side_effect = Exception("Graph error")
        consumer.g = mock_g

        event = EntityEvent(
            entity_id="p-123",
            event_type="create",
            entity_type="person",
            payload={},
        )

        result = consumer.process_event(event)

        assert result is False

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_process_event_with_none_values(self):
        """Test processing event with None values in payload."""
        consumer = GraphConsumer()

        # Mock graph traversal
        mock_g = Mock()
        mock_traversal = Mock()
        mock_g.V.return_value = mock_traversal
        mock_traversal.has.return_value = mock_traversal
        mock_traversal.fold.return_value = mock_traversal
        mock_traversal.coalesce.return_value = mock_traversal
        mock_traversal.property.return_value = mock_traversal
        mock_traversal.iterate.return_value = None

        consumer.g = mock_g

        event = EntityEvent(
            entity_id="p-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John", "middle_name": None, "age": 30},
        )

        result = consumer.process_event(event)

        assert result is True
        # Should skip None values
        property_calls = [call for call in mock_traversal.property.call_args_list]
        # Should not include middle_name
        assert not any("middle_name" in str(call) for call in property_calls)


class TestGraphConsumerBatchProcessing:
    """Test batch processing logic."""

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_process_batch_empty(self):
        """Test processing empty batch."""
        consumer = GraphConsumer()

        # Mock consumer that times out immediately
        mock_consumer = Mock()
        mock_consumer.receive.side_effect = Exception("Timeout")
        consumer.consumer = mock_consumer

        processed = consumer.process_batch(timeout_ms=10)

        assert processed == 0

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_process_batch_success(self):
        """Test successful batch processing."""
        consumer = GraphConsumer()

        # Mock messages
        mock_messages = []
        for i in range(3):
            msg = Mock()
            event = EntityEvent(
                entity_id=f"p-{i}",
                event_type="create",
                entity_type="person",
                payload={"name": f"Person {i}"},
            )
            msg.data.return_value = event.to_bytes()
            mock_messages.append(msg)

        # Mock consumer
        mock_consumer = Mock()
        mock_consumer.receive.side_effect = mock_messages + [Exception("Timeout")]
        consumer.consumer = mock_consumer

        # Mock DLQ producer
        consumer.dlq_producer = Mock()

        # Mock successful event processing
        consumer.process_event = Mock(return_value=True)

        processed = consumer.process_batch(timeout_ms=100)

        assert processed == 3
        assert consumer.metrics["events_processed"] == 3
        assert consumer.metrics["events_failed"] == 0
        assert consumer.metrics["batches_processed"] == 1
        assert consumer.metrics["last_batch_time"] is not None

        # Verify all messages acknowledged
        for msg in mock_messages:
            mock_consumer.acknowledge.assert_any_call(msg)

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_process_batch_with_failures(self):
        """Test batch processing with some failures."""
        consumer = GraphConsumer()

        # Mock messages
        mock_messages = []
        for i in range(3):
            msg = Mock()
            event = EntityEvent(
                entity_id=f"p-{i}",
                event_type="create",
                entity_type="person",
                payload={},
            )
            msg.data.return_value = event.to_bytes()
            mock_messages.append(msg)

        # Mock consumer
        mock_consumer = Mock()
        mock_consumer.receive.side_effect = mock_messages + [Exception("Timeout")]
        consumer.consumer = mock_consumer

        # Mock DLQ producer
        mock_dlq = Mock()
        consumer.dlq_producer = mock_dlq

        # Mock event processing: first succeeds, second fails, third succeeds
        consumer.process_event = Mock(side_effect=[True, False, True])

        processed = consumer.process_batch(timeout_ms=100)

        assert processed == 2
        assert consumer.metrics["events_processed"] == 2
        assert consumer.metrics["events_failed"] == 1

        # Verify DLQ send for failed event
        mock_dlq.send.assert_called_once()

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_process_batch_dlq_failure(self):
        """Test batch processing when DLQ send fails."""
        consumer = GraphConsumer()

        # Mock message
        msg = Mock()
        event = EntityEvent(
            entity_id="p-1",
            event_type="create",
            entity_type="person",
            payload={},
        )
        msg.data.return_value = event.to_bytes()

        # Mock consumer
        mock_consumer = Mock()
        mock_consumer.receive.side_effect = [msg, Exception("Timeout")]
        consumer.consumer = mock_consumer

        # Mock DLQ producer that fails
        mock_dlq = Mock()
        mock_dlq.send.side_effect = Exception("DLQ error")
        consumer.dlq_producer = mock_dlq

        # Mock event processing failure
        consumer.process_event = Mock(return_value=False)

        processed = consumer.process_batch(timeout_ms=100)

        assert processed == 0
        # Should NACK when DLQ fails
        mock_consumer.negative_acknowledge.assert_called_once_with(msg)

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_process_batch_respects_batch_size(self):
        """Test batch processing respects batch size limit."""
        consumer = GraphConsumer(batch_size=2)

        # Mock more messages than batch size
        mock_messages = []
        for i in range(5):
            msg = Mock()
            event = EntityEvent(
                entity_id=f"p-{i}",
                event_type="create",
                entity_type="person",
                payload={},
            )
            msg.data.return_value = event.to_bytes()
            mock_messages.append(msg)

        # Mock consumer
        mock_consumer = Mock()
        mock_consumer.receive.side_effect = mock_messages
        consumer.consumer = mock_consumer
        consumer.dlq_producer = Mock()

        # Mock successful processing
        consumer.process_event = Mock(return_value=True)

        processed = consumer.process_batch(timeout_ms=1000)

        # Should only process batch_size events
        assert processed == 2


class TestGraphConsumerContinuousProcessing:
    """Test continuous processing."""

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_stop(self):
        """Test stopping continuous processing."""
        consumer = GraphConsumer()
        consumer._running = True

        consumer.stop()

        assert consumer._running is False

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_process_forever_with_callback(self):
        """Test continuous processing with callback."""
        consumer = GraphConsumer()

        # Mock process_batch to return values then stop
        call_count = [0]

        def mock_process_batch():
            call_count[0] += 1
            if call_count[0] >= 3:
                consumer.stop()
            return call_count[0]

        consumer.process_batch = mock_process_batch

        callback_results = []

        def callback(processed):
            callback_results.append(processed)

        consumer.process_forever(on_batch=callback)

        assert len(callback_results) == 3
        assert callback_results == [1, 2, 3]


class TestGraphConsumerMetrics:
    """Test metrics tracking."""

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    def test_get_metrics(self):
        """Test getting metrics."""
        consumer = GraphConsumer()

        consumer.metrics["events_processed"] = 100
        consumer.metrics["events_failed"] = 5

        metrics = consumer.get_metrics()

        assert metrics["events_processed"] == 100
        assert metrics["events_failed"] == 5
        assert isinstance(metrics, dict)

        # Verify it's a copy
        metrics["events_processed"] = 200
        assert consumer.metrics["events_processed"] == 100


class TestGraphConsumerContextManager:
    """Test context manager usage."""

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_context_manager(self, mock_traversal, mock_driver, mock_pulsar):
        """Test using GraphConsumer as context manager."""
        # Setup mocks
        mock_client = Mock()
        mock_consumer_obj = Mock()
        mock_producer = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.subscribe.return_value = mock_consumer_obj
        mock_client.create_producer.return_value = mock_producer

        mock_connection = Mock()
        mock_driver.return_value = mock_connection

        mock_g = Mock()
        mock_traversal.return_value.with_remote.return_value = mock_g

        consumer = GraphConsumer()

        with consumer as c:
            assert c == consumer
            assert c.pulsar_client is not None
            assert c.consumer is not None
            assert c.g is not None

        # Verify disconnect was called
        mock_consumer_obj.close.assert_called_once()
        mock_producer.close.assert_called_once()
        mock_client.close.assert_called_once()
        mock_connection.close.assert_called_once()

    @patch("banking.streaming.graph_consumer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.GREMLIN_AVAILABLE", True)
    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_context_manager_with_exception(self, mock_traversal, mock_driver, mock_pulsar):
        """Test context manager handles exceptions."""
        # Setup mocks
        mock_client = Mock()
        mock_consumer_obj = Mock()
        mock_producer = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.subscribe.return_value = mock_consumer_obj
        mock_client.create_producer.return_value = mock_producer

        mock_connection = Mock()
        mock_driver.return_value = mock_connection

        mock_g = Mock()
        mock_traversal.return_value.with_remote.return_value = mock_g

        consumer = GraphConsumer()

        with pytest.raises(ValueError):
            with consumer:
                raise ValueError("Test error")

        # Verify disconnect was still called
        mock_consumer_obj.close.assert_called_once()
        mock_producer.close.assert_called_once()
        mock_client.close.assert_called_once()
        mock_connection.close.assert_called_once()

# Made with Bob
