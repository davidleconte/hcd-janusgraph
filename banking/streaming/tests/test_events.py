"""
Unit tests for EntityEvent and related classes.

Tests cover:
- Event creation and validation
- Serialization/deserialization (JSON, bytes)
- Pulsar message format conversion
- Batch operations
- Factory functions

Created: 2026-02-04
"""

import pytest
import json
import uuid

from banking.streaming.events import (
    EntityEvent,
    EntityEventBatch,
    create_person_event,
    create_account_event,
    create_transaction_event,
    create_company_event,
)


class TestEntityEvent:
    """Tests for EntityEvent dataclass."""
    
    def test_create_valid_event(self):
        """Test creating a valid event."""
        event = EntityEvent(
            entity_id="test-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John Doe"}
        )
        
        assert event.entity_id == "test-123"
        assert event.event_type == "create"
        assert event.entity_type == "person"
        assert event.payload == {"name": "John Doe"}
        assert event.version == 1
        assert event.event_id is not None
        assert event.timestamp is not None
    
    def test_event_with_embedding_text(self):
        """Test event with text_for_embedding."""
        event = EntityEvent(
            entity_id="test-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John Doe"},
            text_for_embedding="John Doe"
        )
        
        assert event.text_for_embedding == "John Doe"
    
    def test_invalid_event_type(self):
        """Test that invalid event_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid event_type"):
            EntityEvent(
                entity_id="test-123",
                event_type="invalid",
                entity_type="person",
                payload={}
            )
    
    def test_invalid_entity_type(self):
        """Test that invalid entity_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid entity_type"):
            EntityEvent(
                entity_id="test-123",
                event_type="create",
                entity_type="invalid",
                payload={}
            )
    
    def test_missing_entity_id(self):
        """Test that missing entity_id raises ValueError."""
        with pytest.raises(ValueError, match="entity_id is required"):
            EntityEvent(
                entity_id="",
                event_type="create",
                entity_type="person",
                payload={}
            )
    
    def test_invalid_payload_type(self):
        """Test that non-dict payload raises ValueError."""
        with pytest.raises(ValueError, match="payload must be a dictionary"):
            EntityEvent(
                entity_id="test-123",
                event_type="create",
                entity_type="person",
                payload="not a dict"
            )
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        event = EntityEvent(
            entity_id="test-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John"},
            source="test"
        )
        
        d = event.to_dict()
        
        assert d['entity_id'] == "test-123"
        assert d['event_type'] == "create"
        assert d['entity_type'] == "person"
        assert d['payload'] == {"name": "John"}
        assert d['source'] == "test"
        assert d['version'] == 1
        assert 'timestamp' in d
        assert 'event_id' in d
    
    def test_to_json(self):
        """Test JSON serialization."""
        event = EntityEvent(
            entity_id="test-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John"}
        )
        
        json_str = event.to_json()
        parsed = json.loads(json_str)
        
        assert parsed['entity_id'] == "test-123"
        assert parsed['entity_type'] == "person"
    
    def test_to_bytes(self):
        """Test bytes serialization."""
        event = EntityEvent(
            entity_id="test-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John"}
        )
        
        data = event.to_bytes()
        
        assert isinstance(data, bytes)
        assert b"test-123" in data
    
    def test_to_pulsar_message(self):
        """Test Pulsar message format."""
        event = EntityEvent(
            entity_id="test-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John"}
        )
        
        msg = event.to_pulsar_message()
        
        assert msg['partition_key'] == "test-123"
        assert isinstance(msg['sequence_id'], int)
        assert isinstance(msg['content'], bytes)
    
    def test_get_topic(self):
        """Test topic generation."""
        event = EntityEvent(
            entity_id="test-123",
            event_type="create",
            entity_type="person",
            payload={}
        )
        
        assert event.get_topic() == "persistent://public/banking/persons-events"
        
        event2 = EntityEvent(
            entity_id="test-456",
            event_type="create",
            entity_type="account",
            payload={}
        )
        
        assert event2.get_topic() == "persistent://public/banking/accounts-events"
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'entity_id': 'test-123',
            'event_type': 'update',
            'entity_type': 'person',
            'payload': {'name': 'Jane'},
            'version': 2
        }
        
        event = EntityEvent.from_dict(data)
        
        assert event.entity_id == 'test-123'
        assert event.event_type == 'update'
        assert event.version == 2
    
    def test_from_json(self):
        """Test creation from JSON string."""
        json_str = json.dumps({
            'entity_id': 'test-123',
            'event_type': 'create',
            'entity_type': 'person',
            'payload': {'name': 'John'}
        })
        
        event = EntityEvent.from_json(json_str)
        
        assert event.entity_id == 'test-123'
    
    def test_from_bytes(self):
        """Test creation from bytes."""
        original = EntityEvent(
            entity_id="test-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John"}
        )
        
        data = original.to_bytes()
        restored = EntityEvent.from_bytes(data)
        
        assert restored.entity_id == original.entity_id
        assert restored.event_type == original.event_type
        assert restored.payload == original.payload
    
    def test_roundtrip_serialization(self):
        """Test complete serialization roundtrip."""
        original = EntityEvent(
            entity_id=str(uuid.uuid4()),
            event_type="create",
            entity_type="company",
            payload={"name": "ACME Corp", "industry": "Tech"},
            text_for_embedding="ACME Corp",
            source="test",
            version=1
        )
        
        # Dict roundtrip
        restored_dict = EntityEvent.from_dict(original.to_dict())
        assert restored_dict.entity_id == original.entity_id
        assert restored_dict.payload == original.payload
        
        # JSON roundtrip
        restored_json = EntityEvent.from_json(original.to_json())
        assert restored_json.entity_id == original.entity_id
        
        # Bytes roundtrip
        restored_bytes = EntityEvent.from_bytes(original.to_bytes())
        assert restored_bytes.entity_id == original.entity_id


class TestEntityEventBatch:
    """Tests for EntityEventBatch."""
    
    def test_create_batch(self):
        """Test creating a batch of events."""
        events = [
            EntityEvent(
                entity_id=f"test-{i}",
                event_type="create",
                entity_type="person",
                payload={"name": f"Person {i}"}
            )
            for i in range(5)
        ]
        
        batch = EntityEventBatch(events=events)
        
        assert len(batch) == 5
        assert batch.batch_id is not None
    
    def test_batch_iteration(self):
        """Test iterating over batch."""
        events = [
            EntityEvent(
                entity_id=f"test-{i}",
                event_type="create",
                entity_type="person",
                payload={}
            )
            for i in range(3)
        ]
        
        batch = EntityEventBatch(events=events)
        
        ids = [e.entity_id for e in batch]
        assert ids == ["test-0", "test-1", "test-2"]
    
    def test_by_entity_type(self):
        """Test grouping by entity type."""
        events = [
            EntityEvent(entity_id="p1", event_type="create", entity_type="person", payload={}),
            EntityEvent(entity_id="a1", event_type="create", entity_type="account", payload={}),
            EntityEvent(entity_id="p2", event_type="create", entity_type="person", payload={}),
        ]
        
        batch = EntityEventBatch(events=events)
        grouped = batch.by_entity_type()
        
        assert len(grouped['person']) == 2
        assert len(grouped['account']) == 1
    
    def test_by_topic(self):
        """Test grouping by topic."""
        events = [
            EntityEvent(entity_id="p1", event_type="create", entity_type="person", payload={}),
            EntityEvent(entity_id="c1", event_type="create", entity_type="company", payload={}),
        ]
        
        batch = EntityEventBatch(events=events)
        grouped = batch.by_topic()
        
        assert "persistent://public/banking/persons-events" in grouped
        assert "persistent://public/banking/companys-events" in grouped


class TestFactoryFunctions:
    """Tests for convenience factory functions."""
    
    def test_create_person_event(self):
        """Test person event factory."""
        event = create_person_event(
            person_id="person-123",
            name="John Doe",
            payload={"email": "john@example.com"},
            source="test"
        )
        
        assert event.entity_id == "person-123"
        assert event.entity_type == "person"
        assert event.text_for_embedding == "John Doe"
        assert event.source == "test"
    
    def test_create_account_event(self):
        """Test account event factory."""
        event = create_account_event(
            account_id="acc-123",
            payload={"balance": 1000.0}
        )
        
        assert event.entity_id == "acc-123"
        assert event.entity_type == "account"
        assert event.text_for_embedding is None
    
    def test_create_transaction_event(self):
        """Test transaction event factory."""
        event = create_transaction_event(
            transaction_id="txn-123",
            payload={"amount": 500.0, "currency": "USD"}
        )
        
        assert event.entity_id == "txn-123"
        assert event.entity_type == "transaction"
    
    def test_create_company_event(self):
        """Test company event factory."""
        event = create_company_event(
            company_id="comp-123",
            name="ACME Corp",
            payload={"industry": "Tech"}
        )
        
        assert event.entity_id == "comp-123"
        assert event.entity_type == "company"
        assert event.text_for_embedding == "ACME Corp"
