"""Tests for banking.streaming.producer module."""

from unittest.mock import MagicMock, patch

import pytest

from banking.streaming.producer import EntityProducer, MockEntityProducer


class TestMockEntityProducer:
    def test_init(self):
        producer = MockEntityProducer()
        assert producer is not None

    def test_send(self):
        from banking.streaming.events import EntityEvent

        producer = MockEntityProducer()
        event = EntityEvent(
            entity_id="e-1",
            event_type="create",
            entity_type="person",
            payload={"name": "John"},
            source="test",
        )
        producer.send(event)
        assert len(producer.events) == 1

    def test_send_multiple(self):
        from banking.streaming.events import EntityEvent

        producer = MockEntityProducer()
        for i in range(5):
            event = EntityEvent(
                entity_id=f"e-{i}",
                event_type="create",
                entity_type="person",
                payload={"name": f"Person {i}"},
                source="test",
            )
            producer.send(event)
        assert len(producer.events) == 5

    def test_close(self):
        producer = MockEntityProducer()
        producer.close()
