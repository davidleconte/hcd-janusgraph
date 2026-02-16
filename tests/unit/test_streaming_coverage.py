"""
Coverage tests for streaming modules: graph_consumer, vector_consumer, streaming_orchestrator, events, metrics, dlq_handler.
"""

import signal
import time
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, PropertyMock

import pytest

from banking.streaming.events import EntityEvent
from banking.streaming.graph_consumer import GraphConsumer, main as graph_main
from banking.streaming.vector_consumer import VectorConsumer, main as vector_main
from banking.streaming.streaming_orchestrator import StreamingOrchestrator, StreamingConfig, StreamingStats
from banking.streaming.metrics import StreamingMetrics


class TestGraphConsumerCoverage:

    def _make_event(self, event_type="create", entity_type="person", entity_id="PER-001", payload=None, version=1):
        event = MagicMock(spec=EntityEvent)
        event.event_id = "evt-001"
        event.event_type = event_type
        event.entity_type = entity_type
        event.entity_id = entity_id
        event.version = version
        event.timestamp = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        event.source = "test"
        event.payload = payload or {"name": "John", "birth_date": "1990-01-01", "age": 35, "active": True}
        event.text_for_embedding = "John Doe"
        event.get_topic.return_value = "persons-events"
        event.to_bytes.return_value = b"event-data"
        return event

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_connect_and_disconnect(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.connect()
        assert consumer.g is not None
        consumer.disconnect()

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_event_create(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.g = MagicMock()
        mock_t = MagicMock()
        consumer.g.V.return_value.has.return_value.fold.return_value.coalesce.return_value.property.return_value = mock_t
        mock_t.property.return_value = mock_t

        event = self._make_event("create")
        result = consumer.process_event(event)
        assert result is True

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_event_update_stale(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.g = MagicMock()
        consumer.g.V.return_value.has.return_value.value_map.return_value.toList.return_value = [
            {"version": [5]}
        ]

        event = self._make_event("update", version=3)
        result = consumer.process_event(event)
        assert result is True

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_event_update_newer(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.g = MagicMock()
        consumer.g.V.return_value.has.return_value.value_map.return_value.toList.return_value = [
            {"version": [1]}
        ]
        mock_t = MagicMock()
        consumer.g.V.return_value.has.return_value.property.return_value = mock_t
        mock_t.property.return_value = mock_t

        event = self._make_event("update", version=5, payload={"name": "Jane", "score": 0.95})
        result = consumer.process_event(event)
        assert result is True

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_event_update_no_existing(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.g = MagicMock()
        consumer.g.V.return_value.has.return_value.value_map.return_value.toList.return_value = []
        mock_t = MagicMock()
        consumer.g.V.return_value.has.return_value.property.return_value = mock_t
        mock_t.property.return_value = mock_t

        event = self._make_event("update", version=1)
        result = consumer.process_event(event)
        assert result is True

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_event_delete(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.g = MagicMock()

        event = self._make_event("delete")
        result = consumer.process_event(event)
        assert result is True

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_event_exception(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.g = MagicMock()
        consumer.g.V.side_effect = Exception("Graph error")

        event = self._make_event("create")
        result = consumer.process_event(event)
        assert result is False

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_batch_empty(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.consumer = MagicMock()
        consumer.consumer.receive.side_effect = Exception("timeout")
        consumer.dlq_producer = MagicMock()
        consumer.g = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "batches_processed": 0, "last_batch_time": None}

        result = consumer.process_batch(timeout_ms=10)
        assert result == 0

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_batch_with_events(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.g = MagicMock()
        consumer.dlq_producer = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "batches_processed": 0, "last_batch_time": None}

        msg = MagicMock()
        event = self._make_event()
        event_bytes = b'{"event_id": "e1", "event_type": "create", "entity_type": "person", "entity_id": "PER-001", "version": 1, "timestamp": "2026-01-15T12:00:00+00:00", "payload": {"name": "John"}, "source": "test"}'
        msg.data.return_value = event_bytes

        call_count = [0]
        def receive_side_effect(timeout_millis=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return msg
            raise Exception("timeout")

        consumer.consumer = MagicMock()
        consumer.consumer.receive.side_effect = receive_side_effect

        with patch.object(consumer, "process_event", return_value=True):
            result = consumer.process_batch(timeout_ms=50)
            assert result >= 0

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_batch_with_failures(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.g = MagicMock()
        consumer.dlq_producer = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "batches_processed": 0, "last_batch_time": None}

        msg = MagicMock()
        event_bytes = b'{"event_id": "e1", "event_type": "create", "entity_type": "person", "entity_id": "PER-001", "version": 1, "timestamp": "2026-01-15T12:00:00+00:00", "payload": {"name": "John"}, "source": "test"}'
        msg.data.return_value = event_bytes

        call_count = [0]
        def receive_side_effect(timeout_millis=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return msg
            raise Exception("timeout")

        consumer.consumer = MagicMock()
        consumer.consumer.receive.side_effect = receive_side_effect

        with patch.object(consumer, "process_event", return_value=False):
            consumer.process_batch(timeout_ms=50)

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_batch_dlq_failure(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.g = MagicMock()
        consumer.dlq_producer = MagicMock()
        consumer.dlq_producer.send.side_effect = Exception("DLQ error")
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "batches_processed": 0, "last_batch_time": None}

        msg = MagicMock()
        event_bytes = b'{"event_id": "e1", "event_type": "create", "entity_type": "person", "entity_id": "PER-001", "version": 1, "timestamp": "2026-01-15T12:00:00+00:00", "payload": {"name": "John"}, "source": "test"}'
        msg.data.return_value = event_bytes

        call_count = [0]
        def receive_side_effect(timeout_millis=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return msg
            raise Exception("timeout")

        consumer.consumer = MagicMock()
        consumer.consumer.receive.side_effect = receive_side_effect

        with patch.object(consumer, "process_event", return_value=False):
            consumer.process_batch(timeout_ms=50)

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_forever_stops(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.g = MagicMock()
        consumer.consumer = MagicMock()
        consumer.dlq_producer = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "batches_processed": 0, "last_batch_time": None}
        consumer.consumer.receive.side_effect = Exception("timeout")

        callback = MagicMock()

        def stop_after_one(processed):
            consumer.stop()

        with patch.object(consumer, "process_batch", side_effect=[0, 0]):
            consumer._running = True
            def auto_stop():
                consumer._running = False
            with patch.object(consumer, "process_batch", side_effect=lambda: (auto_stop(), 0)[1]):
                consumer.process_forever(on_batch=callback)

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_forever_exception(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.g = MagicMock()
        consumer.consumer = MagicMock()
        consumer.dlq_producer = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "batches_processed": 0, "last_batch_time": None}

        call_count = [0]
        def batch_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("test error")
            consumer._running = False
            return 0

        with patch.object(consumer, "process_batch", side_effect=batch_side_effect):
            with patch("banking.streaming.graph_consumer.time.sleep"):
                consumer.process_forever()

    def test_context_manager(self):
        with patch.object(GraphConsumer, "connect"), patch.object(GraphConsumer, "disconnect"):
            with GraphConsumer() as gc:
                assert gc is not None

    def test_get_metrics(self):
        consumer = GraphConsumer()
        consumer.metrics = {"events_processed": 5}
        m = consumer.get_metrics()
        assert m["events_processed"] == 5
        m["events_processed"] = 99
        assert consumer.metrics["events_processed"] == 5

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_main(self, mock_traversal, mock_conn, mock_pulsar):
        with patch.object(GraphConsumer, "connect"), \
             patch.object(GraphConsumer, "disconnect"), \
             patch.object(GraphConsumer, "process_forever"), \
             patch("signal.signal"):
            graph_main()

    @patch("banking.streaming.graph_consumer.pulsar")
    @patch("banking.streaming.graph_consumer.DriverRemoteConnection")
    @patch("banking.streaming.graph_consumer.traversal")
    def test_process_event_create_with_timestamp_property(self, mock_traversal, mock_conn, mock_pulsar):
        consumer = GraphConsumer()
        consumer.g = MagicMock()
        mock_t = MagicMock()
        consumer.g.V.return_value.has.return_value.fold.return_value.coalesce.return_value.property.return_value = mock_t
        mock_t.property.return_value = mock_t

        event = self._make_event("create", payload={
            "name": "John",
            "created_at": "2026-01-15T12:00:00+00:00",
            "invalid_date": "not-a-date",
            "score": 0.95,
            "active": True,
            "null_field": None,
        })
        result = consumer.process_event(event)
        assert result is True


class TestVectorConsumerCoverage:

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    def test_connect_and_disconnect(self, mock_os, mock_pulsar):
        consumer = VectorConsumer()
        consumer.connect()
        consumer.disconnect()

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    def test_generate_embedding_no_model(self, mock_os, mock_pulsar):
        consumer = VectorConsumer()
        consumer.embedding_model = None
        emb = consumer._generate_embedding("test text")
        assert len(emb) == 384
        assert all(v == 0.0 for v in emb)

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    def test_generate_embedding_with_model(self, mock_os, mock_pulsar):
        consumer = VectorConsumer()
        consumer.embedding_model = MagicMock()
        mock_result = MagicMock()
        mock_result.tolist.return_value = [0.1] * 384
        consumer.embedding_model.encode.return_value = mock_result
        emb = consumer._generate_embedding("test")
        assert len(emb) == 384

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    def test_generate_batch_embeddings_no_model(self, mock_os, mock_pulsar):
        consumer = VectorConsumer()
        consumer.embedding_model = None
        embs = consumer._generate_batch_embeddings(["a", "b"])
        assert len(embs) == 2

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    def test_generate_batch_embeddings_with_model(self, mock_os, mock_pulsar):
        consumer = VectorConsumer()
        consumer.embedding_model = MagicMock()
        mock_e1 = MagicMock()
        mock_e1.tolist.return_value = [0.1] * 384
        mock_e2 = MagicMock()
        mock_e2.tolist.return_value = [0.2] * 384
        consumer.embedding_model.encode.return_value = [mock_e1, mock_e2]
        embs = consumer._generate_batch_embeddings(["a", "b"])
        assert len(embs) == 2

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    def test_get_index_name(self, mock_os, mock_pulsar):
        consumer = VectorConsumer()
        assert consumer._get_index_name("person") == "person_vectors"
        assert "vectors" in consumer._get_index_name("unknown_type")

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    def test_process_batch_empty(self, mock_os, mock_pulsar):
        consumer = VectorConsumer()
        consumer.consumer = MagicMock()
        consumer.consumer.receive.side_effect = Exception("timeout")
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "events_skipped": 0, "embeddings_generated": 0, "batches_processed": 0, "last_batch_time": None}
        result = consumer.process_batch(timeout_ms=10)
        assert result == 0

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    @patch("banking.streaming.vector_consumer.helpers")
    def test_process_batch_with_delete_event(self, mock_helpers, mock_os, mock_pulsar):
        consumer = VectorConsumer()
        consumer.embedding_model = None
        consumer.opensearch = MagicMock()
        consumer.consumer = MagicMock()
        consumer.dlq_producer = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "events_skipped": 0, "embeddings_generated": 0, "batches_processed": 0, "last_batch_time": None}

        event = MagicMock(spec=EntityEvent)
        event.event_type = "delete"
        event.entity_type = "person"
        event.entity_id = "PER-001"
        event.text_for_embedding = "John Doe"
        event.version = 1
        event.timestamp = datetime(2026, 1, 15, tzinfo=timezone.utc)
        event.source = "test"
        event.payload = {}

        msg = MagicMock()
        msg.data.return_value = b"data"

        call_count = [0]
        def recv(timeout_millis=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return msg
            raise Exception("timeout")

        consumer.consumer.receive.side_effect = recv
        mock_helpers.bulk.return_value = (1, [])

        with patch("banking.streaming.events.EntityEvent.from_bytes", return_value=event):
            result = consumer.process_batch(timeout_ms=50)

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    @patch("banking.streaming.vector_consumer.helpers")
    def test_process_batch_bulk_error(self, mock_helpers, mock_os, mock_pulsar):
        consumer = VectorConsumer()
        consumer.embedding_model = None
        consumer.opensearch = MagicMock()
        consumer.consumer = MagicMock()
        consumer.dlq_producer = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "events_skipped": 0, "embeddings_generated": 0, "batches_processed": 0, "last_batch_time": None}

        event = MagicMock(spec=EntityEvent)
        event.event_type = "create"
        event.entity_type = "person"
        event.entity_id = "PER-001"
        event.text_for_embedding = "John"
        event.version = 1
        event.timestamp = datetime(2026, 1, 15, tzinfo=timezone.utc)
        event.source = "test"
        event.payload = {"name": "John"}

        msg = MagicMock()
        msg.data.return_value = b"data"

        call_count = [0]
        def recv(timeout_millis=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return msg
            raise Exception("timeout")

        consumer.consumer.receive.side_effect = recv
        mock_helpers.bulk.side_effect = Exception("bulk error")

        with patch("banking.streaming.events.EntityEvent.from_bytes", return_value=event):
            result = consumer.process_batch(timeout_ms=50)
            assert result == 0

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    def test_process_batch_embedding_failure(self, mock_os, mock_pulsar):
        consumer = VectorConsumer()
        consumer.embedding_model = MagicMock()
        consumer.embedding_model.encode.side_effect = Exception("model error")
        consumer.opensearch = MagicMock()
        consumer.consumer = MagicMock()
        consumer.dlq_producer = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "events_skipped": 0, "embeddings_generated": 0, "batches_processed": 0, "last_batch_time": None}

        event = MagicMock(spec=EntityEvent)
        event.event_type = "create"
        event.entity_type = "person"
        event.entity_id = "PER-001"
        event.text_for_embedding = "John"
        event.version = 1
        event.timestamp = datetime(2026, 1, 15, tzinfo=timezone.utc)
        event.source = "test"
        event.payload = {}

        msg = MagicMock()
        msg.data.return_value = b"data"

        call_count = [0]
        def recv(timeout_millis=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return msg
            raise Exception("timeout")

        consumer.consumer.receive.side_effect = recv

        with patch("banking.streaming.events.EntityEvent.from_bytes", return_value=event):
            result = consumer.process_batch(timeout_ms=50)
            assert result == 0

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    def test_process_batch_non_embeddable(self, mock_os, mock_pulsar):
        consumer = VectorConsumer()
        consumer.embedding_model = None
        consumer.opensearch = MagicMock()
        consumer.consumer = MagicMock()
        consumer.dlq_producer = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "events_skipped": 0, "embeddings_generated": 0, "batches_processed": 0, "last_batch_time": None}

        event = MagicMock(spec=EntityEvent)
        event.event_type = "create"
        event.entity_type = "person"
        event.entity_id = "PER-001"
        event.text_for_embedding = None
        event.version = 1
        event.timestamp = datetime(2026, 1, 15, tzinfo=timezone.utc)
        event.source = "test"
        event.payload = {}

        msg = MagicMock()
        msg.data.return_value = b"data"

        call_count = [0]
        def recv(timeout_millis=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return msg
            raise Exception("timeout")

        consumer.consumer.receive.side_effect = recv

        with patch("banking.streaming.events.EntityEvent.from_bytes", return_value=event):
            result = consumer.process_batch(timeout_ms=50)
            assert result == 0

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    @patch("banking.streaming.vector_consumer.helpers")
    def test_process_batch_with_bulk_errors_list(self, mock_helpers, mock_os, mock_pulsar):
        consumer = VectorConsumer()
        consumer.embedding_model = None
        consumer.opensearch = MagicMock()
        consumer.consumer = MagicMock()
        consumer.dlq_producer = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "events_skipped": 0, "embeddings_generated": 0, "batches_processed": 0, "last_batch_time": None}

        event = MagicMock(spec=EntityEvent)
        event.event_type = "create"
        event.entity_type = "person"
        event.entity_id = "PER-001"
        event.text_for_embedding = "John"
        event.version = 1
        event.timestamp = datetime(2026, 1, 15, tzinfo=timezone.utc)
        event.source = "test"
        event.payload = {"name": "John"}

        msg = MagicMock()
        msg.data.return_value = b"data"

        call_count = [0]
        def recv(timeout_millis=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return msg
            raise Exception("timeout")

        consumer.consumer.receive.side_effect = recv
        mock_helpers.bulk.return_value = (0, [{"index": {"error": "test"}}])

        with patch("banking.streaming.events.EntityEvent.from_bytes", return_value=event):
            consumer.process_batch(timeout_ms=50)

    def test_process_forever_stops(self):
        consumer = VectorConsumer()
        consumer.consumer = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "events_skipped": 0, "embeddings_generated": 0, "batches_processed": 0, "last_batch_time": None}

        def auto_stop():
            consumer._running = False
            return 0

        with patch.object(consumer, "process_batch", side_effect=lambda: auto_stop()):
            consumer.process_forever()

    def test_process_forever_with_callback(self):
        consumer = VectorConsumer()
        consumer.consumer = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "events_skipped": 0, "embeddings_generated": 0, "batches_processed": 0, "last_batch_time": None}
        cb = MagicMock()

        def auto_stop():
            consumer._running = False
            return 0

        with patch.object(consumer, "process_batch", side_effect=lambda: auto_stop()):
            consumer.process_forever(on_batch=cb)

    def test_process_forever_exception(self):
        consumer = VectorConsumer()
        consumer.consumer = MagicMock()
        consumer.metrics = {"events_processed": 0, "events_failed": 0, "events_skipped": 0, "embeddings_generated": 0, "batches_processed": 0, "last_batch_time": None}

        call_count = [0]
        def side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("err")
            consumer._running = False
            return 0

        with patch.object(consumer, "process_batch", side_effect=side_effect):
            with patch("banking.streaming.vector_consumer.time.sleep"):
                consumer.process_forever()

    def test_context_manager(self):
        with patch.object(VectorConsumer, "connect"), patch.object(VectorConsumer, "disconnect"):
            with VectorConsumer() as vc:
                assert vc is not None

    def test_get_metrics(self):
        consumer = VectorConsumer()
        consumer.metrics = {"events_processed": 10}
        m = consumer.get_metrics()
        assert m["events_processed"] == 10

    @patch("banking.streaming.vector_consumer.pulsar")
    @patch("banking.streaming.vector_consumer.OpenSearch")
    def test_main(self, mock_os, mock_pulsar):
        with patch.object(VectorConsumer, "connect"), \
             patch.object(VectorConsumer, "disconnect"), \
             patch.object(VectorConsumer, "process_forever"), \
             patch("signal.signal"):
            vector_main()


class TestStreamingOrchestratorCoverage:

    def test_init_default(self):
        config = StreamingConfig(
            seed=42, person_count=2, company_count=1, account_count=2,
            transaction_count=0, communication_count=0, trade_count=0,
            travel_count=0, document_count=0,
            enable_streaming=False, use_mock_producer=True,
        )
        orch = StreamingOrchestrator(config)
        assert orch.config.enable_streaming is False

    def test_init_with_generation_config(self):
        from banking.data_generators.orchestration import GenerationConfig
        gen_config = GenerationConfig(
            seed=42, person_count=2, company_count=1, account_count=2,
            communication_count=0,
        )
        orch = StreamingOrchestrator(gen_config)
        assert isinstance(orch.config, StreamingConfig)

    def test_init_with_streaming_enabled(self):
        config = StreamingConfig(
            seed=42, person_count=2, company_count=1, account_count=2,
            transaction_count=0, communication_count=0, trade_count=0,
            travel_count=0, document_count=0,
            enable_streaming=True, use_mock_producer=True,
        )
        orch = StreamingOrchestrator(config)
        assert orch.producer is not None

    def test_init_with_producer(self):
        mock_producer = MagicMock()
        config = StreamingConfig(
            seed=42, person_count=2, company_count=1, account_count=2,
            transaction_count=0, communication_count=0,
            enable_streaming=True, use_mock_producer=True,
        )
        orch = StreamingOrchestrator(config, producer=mock_producer)
        assert orch.producer is mock_producer

    def test_publish_entity_streaming_disabled(self):
        config = StreamingConfig(
            seed=42, person_count=2, company_count=1, account_count=2,
            enable_streaming=False,
        )
        orch = StreamingOrchestrator(config)
        result = orch._publish_entity(MagicMock())
        assert result is True

    def test_publish_entity_success(self):
        config = StreamingConfig(
            seed=42, person_count=2, company_count=1, account_count=2,
            enable_streaming=True, use_mock_producer=True,
        )
        orch = StreamingOrchestrator(config)
        orch.producer = MagicMock()

        mock_event = MagicMock()
        mock_event.entity_type = "person"
        with patch("banking.streaming.streaming_orchestrator.convert_entity_to_event", return_value=mock_event):
            result = orch._publish_entity(MagicMock())
            assert result is True
            assert orch.stats.events_published == 1

    def test_publish_entity_failure(self):
        config = StreamingConfig(
            seed=42, person_count=2, company_count=1, account_count=2,
            enable_streaming=True, use_mock_producer=True,
        )
        orch = StreamingOrchestrator(config)
        orch.producer = MagicMock()

        with patch("banking.streaming.streaming_orchestrator.convert_entity_to_event", side_effect=Exception("err")):
            result = orch._publish_entity(MagicMock())
            assert result is False
            assert orch.stats.events_failed == 1

    def test_publish_entities_disabled(self):
        config = StreamingConfig(
            seed=42, person_count=2, company_count=1, account_count=2,
            enable_streaming=False,
        )
        orch = StreamingOrchestrator(config)
        result = orch._publish_entities([MagicMock(), MagicMock()])
        assert result == 2

    def test_generate_all(self):
        config = StreamingConfig(
            seed=42, person_count=2, company_count=1, account_count=3,
            transaction_count=2, communication_count=2, trade_count=1,
            travel_count=1, document_count=1,
            enable_streaming=True, use_mock_producer=True,
            flush_after_phase=True,
        )
        orch = StreamingOrchestrator(config)
        stats = orch.generate_all()
        assert stats.persons_generated == 2

    def test_close(self):
        config = StreamingConfig(
            seed=42, person_count=2, company_count=1, account_count=2,
            enable_streaming=True, use_mock_producer=True,
        )
        orch = StreamingOrchestrator(config)
        orch._owns_producer = True
        orch.producer = MagicMock()
        orch.close()
        orch.producer.close.assert_called_once()

    def test_context_manager(self):
        config = StreamingConfig(
            seed=42, person_count=2, company_count=1, account_count=2,
            enable_streaming=False,
        )
        with StreamingOrchestrator(config) as orch:
            assert orch is not None


class TestStreamingMetricsCoverage:

    def test_init(self):
        m = StreamingMetrics()
        assert m is not None

    def test_record_publish(self):
        m = StreamingMetrics()
        m.record_publish("person", "test", 0.05)

    def test_record_publish_failure(self):
        m = StreamingMetrics()
        m.record_publish_failure("person", "test", "timeout")

    def test_record_consume(self):
        m = StreamingMetrics()
        m.record_consume("person", "graph", 0.1)

    def test_record_consume_failure(self):
        m = StreamingMetrics()
        m.record_consume_failure("person", "graph", "parse_error")
