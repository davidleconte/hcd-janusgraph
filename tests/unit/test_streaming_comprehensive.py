"""Tests for banking.streaming modules."""
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from banking.streaming.events import EntityEvent
from banking.streaming.dlq_handler import DLQMessage, DLQHandler, DLQStats, MockDLQHandler
from banking.streaming.metrics import StreamingMetrics
from banking.streaming import entity_converter


class TestEntityEvent:
    def test_create_valid_event(self):
        event = EntityEvent(
            entity_id="e-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John"},
        )
        assert event.entity_id == "e-123"
        assert event.event_type == "create"
        assert event.entity_type == "person"
        assert event.payload == {"name": "John"}
        assert event.event_id
        assert event.timestamp

    def test_invalid_event_type(self):
        with pytest.raises(ValueError, match="Invalid event_type"):
            EntityEvent(entity_id="e-1", event_type="invalid", entity_type="person", payload={})

    def test_invalid_entity_type(self):
        with pytest.raises(ValueError, match="Invalid entity_type"):
            EntityEvent(entity_id="e-1", event_type="create", entity_type="invalid", payload={})

    def test_empty_entity_id(self):
        with pytest.raises(ValueError, match="entity_id is required"):
            EntityEvent(entity_id="", event_type="create", entity_type="person", payload={})

    def test_invalid_payload(self):
        with pytest.raises(ValueError, match="payload must be a dictionary"):
            EntityEvent(entity_id="e-1", event_type="create", entity_type="person", payload="bad")

    def test_to_dict(self):
        event = EntityEvent(
            entity_id="e-1", event_type="create", entity_type="person",
            payload={"k": "v"}, source="test", text_for_embedding="hello",
        )
        d = event.to_dict()
        assert d["entity_id"] == "e-1"
        assert d["event_type"] == "create"
        assert d["entity_type"] == "person"
        assert d["payload"] == {"k": "v"}
        assert d["source"] == "test"
        assert d["text_for_embedding"] == "hello"

    def test_to_json(self):
        event = EntityEvent(
            entity_id="e-1", event_type="create", entity_type="person", payload={"k": "v"},
        )
        j = event.to_json()
        parsed = json.loads(j)
        assert parsed["entity_id"] == "e-1"

    def test_all_valid_event_types(self):
        for et in ("create", "update", "delete"):
            event = EntityEvent(entity_id="e-1", event_type=et, entity_type="person", payload={})
            assert event.event_type == et

    def test_all_valid_entity_types(self):
        for ent in ("person", "account", "transaction", "company", "communication", "trade", "travel", "document"):
            event = EntityEvent(entity_id="e-1", event_type="create", entity_type=ent, payload={})
            assert event.entity_type == ent

    def test_metadata_optional(self):
        event = EntityEvent(
            entity_id="e-1", event_type="create", entity_type="person",
            payload={}, metadata={"key": "val"},
        )
        assert event.metadata == {"key": "val"}


class TestEntityEventFromDict:
    def test_from_dict(self):
        data = {
            "entity_id": "e-1", "event_type": "create", "entity_type": "person",
            "payload": {"name": "test"}, "event_id": "ev-1",
            "timestamp": "2026-01-01T00:00:00+00:00", "version": 1, "source": "test",
        }
        event = EntityEvent.from_dict(data)
        assert event.entity_id == "e-1"

    def test_from_json(self):
        data = {
            "entity_id": "e-1", "event_type": "create", "entity_type": "person",
            "payload": {"name": "test"},
        }
        event = EntityEvent.from_json(json.dumps(data))
        assert event.entity_id == "e-1"


class TestStreamingMetrics:
    def test_init(self):
        metrics = StreamingMetrics()
        assert metrics is not None

    def test_record_publish(self):
        metrics = StreamingMetrics()
        metrics.record_publish("person", "generator", 0.05)

    def test_record_publish_failure(self):
        metrics = StreamingMetrics()
        metrics.record_publish_failure("person", "generator", "timeout")

    def test_record_consume(self):
        metrics = StreamingMetrics()
        metrics.record_consume("person", "graph", 0.1)

    def test_record_consume_failure(self):
        metrics = StreamingMetrics()
        metrics.record_consume_failure("person", "graph", "parse_error")


class TestEntityConverter:
    def test_entity_to_dict_pydantic(self):
        from banking.streaming.entity_converter import entity_to_dict
        from banking.data_generators.utils.data_models import Person, Gender, RiskLevel
        from banking.data_generators.core.person_generator import PersonGenerator
        gen = PersonGenerator(seed=42)
        person = gen.generate()
        d = entity_to_dict(person)
        assert isinstance(d, dict)
        assert "first_name" in d

    def test_get_entity_id(self):
        from banking.streaming.entity_converter import get_entity_id
        class FakeEntity:
            entity_id = "e-123"
        assert get_entity_id(FakeEntity()) == "e-123"

    def test_get_entity_type(self):
        from banking.streaming.entity_converter import get_entity_type
        from banking.data_generators.core.person_generator import PersonGenerator
        gen = PersonGenerator(seed=42)
        person = gen.generate()
        etype = get_entity_type(person)
        assert etype == "person"


class TestDLQMessage:
    def test_create(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        msg = DLQMessage(
            original_topic="test-topic",
            original_event=None,
            failure_reason="parse error",
            failure_count=1,
            first_failure_time=now,
            last_failure_time=now,
            message_id="msg-1",
        )
        assert msg.original_topic == "test-topic"
        assert msg.failure_count == 1

    def test_dlq_message_to_dict(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        msg = DLQMessage(
            original_topic="t", original_event=None, failure_reason="err",
            failure_count=1, first_failure_time=now, last_failure_time=now, message_id="m1",
        )
        d = msg.to_dict()
        assert d["original_topic"] == "t"

    def test_dlq_stats(self):
        stats = DLQStats()
        assert stats.messages_processed == 0
        assert stats.messages_retried == 0

    def test_mock_dlq_handler(self):
        handler = MockDLQHandler()
        assert handler is not None
