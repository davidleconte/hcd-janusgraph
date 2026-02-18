"""
Tests for the real EntityProducer class (mocked Pulsar).

Covers: __init__, _connect, _get_topic, _get_producer, send, send_async,
send_batch, flush, close, context manager, is_connected, get_stats.
"""

from unittest.mock import Mock, patch

import pytest

from banking.streaming.events import EntityEvent


class TestEntityProducerInit:
    """Test EntityProducer initialization."""

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    def test_init_defaults(self, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_pulsar.Client.return_value = Mock()
        producer = EntityProducer()
        assert producer.pulsar_url == EntityProducer.DEFAULT_PULSAR_URL
        assert producer.namespace == EntityProducer.DEFAULT_NAMESPACE
        assert producer.batch_size == EntityProducer.DEFAULT_BATCH_SIZE
        assert producer.batch_delay_ms == EntityProducer.DEFAULT_BATCH_DELAY_MS
        assert producer.compression is True
        assert producer._connected is True
        mock_pulsar.Client.assert_called_once()

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    def test_init_custom(self, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_pulsar.Client.return_value = Mock()
        producer = EntityProducer(
            pulsar_url="pulsar://custom:6650",
            namespace="test/ns",
            batch_size=500,
            batch_delay_ms=50,
            compression=False,
        )
        assert producer.pulsar_url == "pulsar://custom:6650"
        assert producer.namespace == "test/ns"
        assert producer.batch_size == 500
        assert producer.batch_delay_ms == 50
        assert producer.compression is False

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", False)
    def test_init_no_pulsar(self):
        from banking.streaming.producer import EntityProducer

        with pytest.raises(ImportError, match="pulsar-client is not installed"):
            EntityProducer()

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    def test_init_connection_failure(self, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_pulsar.Client.side_effect = Exception("Connection refused")
        with pytest.raises(RuntimeError, match="Failed to connect"):
            EntityProducer()


class TestEntityProducerTopicRouting:
    """Test topic routing and producer caching."""

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    def test_get_topic(self, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_pulsar.Client.return_value = Mock()
        producer = EntityProducer()
        assert producer._get_topic("person") == "persistent://public/banking/persons-events"
        assert producer._get_topic("account") == "persistent://public/banking/accounts-events"

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_get_producer_creates_and_caches(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_producer_obj = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.create_producer.return_value = mock_producer_obj
        mock_comp.ZSTD = "ZSTD"

        producer = EntityProducer()
        p1 = producer._get_producer("person")
        p2 = producer._get_producer("person")
        assert p1 is p2
        mock_client.create_producer.assert_called_once()

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_get_producer_no_compression(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.create_producer.return_value = Mock()

        producer = EntityProducer(compression=False)
        producer._get_producer("person")
        call_kwargs = mock_client.create_producer.call_args
        assert "compression_type" not in (call_kwargs.kwargs if call_kwargs.kwargs else {})


class TestEntityProducerSend:
    """Test send and send_async."""

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_send_sync(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_prod = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.create_producer.return_value = mock_prod

        producer = EntityProducer()
        event = EntityEvent(
            entity_id="p-1", event_type="create", entity_type="person", payload={"name": "John"}
        )
        producer.send(event)
        mock_prod.send.assert_called_once()

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_send_async_with_callback(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_prod = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.create_producer.return_value = mock_prod

        producer = EntityProducer()
        cb = Mock()
        event = EntityEvent(entity_id="p-1", event_type="create", entity_type="person", payload={})
        producer.send(event, callback=cb)
        mock_prod.send_async.assert_called_once()

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_send_not_connected(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_pulsar.Client.return_value = Mock()
        producer = EntityProducer()
        producer._connected = False
        event = EntityEvent(entity_id="p-1", event_type="create", entity_type="person", payload={})
        with pytest.raises(RuntimeError, match="Not connected"):
            producer.send(event)

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_send_producer_error(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_prod = Mock()
        mock_prod.send.side_effect = Exception("Send failed")
        mock_pulsar.Client.return_value = mock_client
        mock_client.create_producer.return_value = mock_prod

        producer = EntityProducer()
        event = EntityEvent(entity_id="p-1", event_type="create", entity_type="person", payload={})
        with pytest.raises(Exception, match="Send failed"):
            producer.send(event)


class TestEntityProducerSendBatch:
    """Test batch sending."""

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_send_batch_success(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_prod = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.create_producer.return_value = mock_prod

        producer = EntityProducer()
        events = [
            EntityEvent(entity_id=f"p-{i}", event_type="create", entity_type="person", payload={})
            for i in range(5)
        ]
        results = producer.send_batch(events)
        assert mock_prod.send.call_count == 5
        topic = producer._get_topic("person")
        assert results[topic] == 5

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_send_batch_partial_failure(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_prod = Mock()
        mock_prod.send.side_effect = [None, Exception("fail"), None]
        mock_pulsar.Client.return_value = mock_client
        mock_client.create_producer.return_value = mock_prod

        producer = EntityProducer()
        events = [
            EntityEvent(entity_id=f"p-{i}", event_type="create", entity_type="person", payload={})
            for i in range(3)
        ]
        results = producer.send_batch(events)
        topic = producer._get_topic("person")
        assert results[topic] == 2

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_send_batch_multi_topic(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.create_producer.return_value = Mock()

        producer = EntityProducer()
        events = [
            EntityEvent(entity_id="p-1", event_type="create", entity_type="person", payload={}),
            EntityEvent(entity_id="a-1", event_type="create", entity_type="account", payload={}),
        ]
        results = producer.send_batch(events)
        assert len(results) == 2


class TestEntityProducerFlushClose:
    """Test flush, close, context manager, stats."""

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_flush(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_prod = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.create_producer.return_value = mock_prod

        producer = EntityProducer()
        producer._get_producer("person")
        producer.flush()
        mock_prod.flush.assert_called_once()

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_close(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_prod = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.create_producer.return_value = mock_prod

        producer = EntityProducer()
        producer._get_producer("person")
        producer.close()
        mock_prod.flush.assert_called_once()
        mock_prod.close.assert_called_once()
        mock_client.close.assert_called_once()
        assert producer._connected is False
        assert len(producer.producers) == 0

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_close_producer_error(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_prod = Mock()
        mock_prod.flush.side_effect = Exception("flush error")
        mock_pulsar.Client.return_value = mock_client
        mock_client.create_producer.return_value = mock_prod

        producer = EntityProducer()
        producer._get_producer("person")
        producer.close()
        assert producer._connected is False

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_close_client_error(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_client.close.side_effect = Exception("client close error")
        mock_pulsar.Client.return_value = mock_client

        producer = EntityProducer()
        producer.close()
        assert producer._connected is False

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_context_manager(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_pulsar.Client.return_value = mock_client

        with EntityProducer() as producer:
            assert producer.is_connected is True
        mock_client.close.assert_called_once()

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    @patch("banking.streaming.producer.CompressionType")
    def test_get_stats(self, mock_comp, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_client = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.create_producer.return_value = Mock()

        producer = EntityProducer()
        producer._get_producer("person")
        stats = producer.get_stats()
        assert stats["connected"] is True
        assert stats["producer_count"] == 1
        assert len(stats["topics"]) == 1
        assert "pulsar_url" in stats
        assert "namespace" in stats

    @patch("banking.streaming.producer.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.producer.pulsar")
    def test_is_connected(self, mock_pulsar):
        from banking.streaming.producer import EntityProducer

        mock_pulsar.Client.return_value = Mock()
        producer = EntityProducer()
        assert producer.is_connected is True
        producer._connected = False
        assert producer.is_connected is False
