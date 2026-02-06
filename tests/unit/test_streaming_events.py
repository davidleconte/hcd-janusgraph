#!/usr/bin/env python3
"""Tests for streaming events module."""

import sys
from pathlib import Path
from datetime import datetime
import uuid

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from banking.streaming.events import EntityEvent, EntityEventBatch


class TestEntityEvent:
    @pytest.fixture
    def sample_event(self):
        return EntityEvent(
            entity_id=str(uuid.uuid4()),
            event_type="create",
            entity_type="person",
            payload={"name": "John Doe", "age": 30}
        )

    def test_event_creation(self, sample_event):
        assert sample_event.entity_id is not None
        assert sample_event.entity_type == "person"
        assert sample_event.event_type == "create"
        assert sample_event.payload["name"] == "John Doe"

    def test_event_types(self):
        for event_type in ["create", "update", "delete"]:
            event = EntityEvent(
                entity_id="test-123",
                event_type=event_type,
                entity_type="account",
                payload={}
            )
            assert event.event_type == event_type

    def test_entity_types(self):
        for entity_type in ["person", "account", "transaction", "company", "communication"]:
            event = EntityEvent(
                entity_id="test-123",
                event_type="create",
                entity_type=entity_type,
                payload={}
            )
            assert event.entity_type == entity_type

    def test_to_pulsar_message(self, sample_event):
        if hasattr(sample_event, 'to_pulsar_message'):
            msg = sample_event.to_pulsar_message()
            assert isinstance(msg, dict)
            assert 'partition_key' in msg
            assert 'content' in msg


class TestEntityEventBatch:
    def test_batch_creation(self):
        events = [
            EntityEvent(entity_id="1", event_type="create", entity_type="person", payload={}),
            EntityEvent(entity_id="2", event_type="create", entity_type="person", payload={})
        ]
        batch = EntityEventBatch(events=events)
        assert len(batch.events) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
