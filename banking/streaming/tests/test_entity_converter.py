"""
Unit Tests for Entity Converter
===============================

Tests for converting generated entities to EntityEvents.

Created: 2026-02-06
"""

import pytest
from dataclasses import dataclass
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from banking.streaming.entity_converter import (
    entity_to_dict,
    get_entity_id,
    get_entity_type,
    get_text_for_embedding,
    convert_entity_to_event,
    convert_entities_to_events,
)
from banking.streaming.events import EntityEvent


# Test fixtures - Mock entity classes
@dataclass
class MockPerson:
    id: str
    first_name: str
    last_name: str
    email: str


@dataclass
class MockAccount:
    account_id: str
    account_type: str
    balance: float


@dataclass
class MockTransaction:
    transaction_id: str
    amount: float
    from_account: str
    to_account: str


@dataclass
class MockCompany:
    company_id: str
    name: str
    industry: str


@dataclass
class MockCommunication:
    communication_id: str
    sender_id: str
    recipient_id: str
    content: str


class PydanticPerson(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str


class TestEntityToDict:
    """Tests for entity_to_dict function."""
    
    def test_dataclass_conversion(self):
        """Test converting a dataclass to dict."""
        person = MockPerson(
            id="p-123",
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        result = entity_to_dict(person)
        
        assert isinstance(result, dict)
        assert result['id'] == "p-123"
        assert result['first_name'] == "John"
        assert result['last_name'] == "Doe"
        assert result['email'] == "john@example.com"
    
    def test_pydantic_model_conversion(self):
        """Test converting a Pydantic model to dict."""
        person = PydanticPerson(
            id="p-456",
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com"
        )
        result = entity_to_dict(person)
        
        assert isinstance(result, dict)
        assert result['id'] == "p-456"
        assert result['first_name'] == "Jane"
    
    def test_invalid_entity_raises_error(self):
        """Test that non-convertible objects raise ValueError."""
        with pytest.raises(ValueError):
            entity_to_dict("not an entity")


class TestGetEntityId:
    """Tests for get_entity_id function."""
    
    def test_id_field(self):
        """Test extracting 'id' field."""
        person = MockPerson(id="p-123", first_name="John", last_name="Doe", email="j@e.com")
        assert get_entity_id(person) == "p-123"
    
    def test_account_id_field(self):
        """Test extracting 'account_id' field."""
        account = MockAccount(account_id="a-456", account_type="checking", balance=1000.0)
        assert get_entity_id(account) == "a-456"
    
    def test_transaction_id_field(self):
        """Test extracting 'transaction_id' field."""
        txn = MockTransaction(
            transaction_id="t-789",
            amount=100.0,
            from_account="a-1",
            to_account="a-2"
        )
        assert get_entity_id(txn) == "t-789"
    
    def test_company_id_field(self):
        """Test extracting 'company_id' field."""
        company = MockCompany(company_id="c-101", name="Acme Corp", industry="Tech")
        assert get_entity_id(company) == "c-101"
    
    def test_communication_id_field(self):
        """Test extracting 'communication_id' field."""
        comm = MockCommunication(
            communication_id="comm-202",
            sender_id="p-1",
            recipient_id="p-2",
            content="Hello"
        )
        assert get_entity_id(comm) == "comm-202"
    
    def test_missing_id_raises_error(self):
        """Test that missing ID field raises ValueError."""
        @dataclass
        class NoIdEntity:
            name: str
        
        entity = NoIdEntity(name="test")
        with pytest.raises(ValueError):
            get_entity_id(entity)


class TestGetEntityType:
    """Tests for get_entity_type function."""
    
    def test_person_type(self):
        """Test detecting person entity type."""
        person = MockPerson(id="p-1", first_name="J", last_name="D", email="j@e.com")
        assert get_entity_type(person) == "person"
    
    def test_account_type(self):
        """Test detecting account entity type."""
        account = MockAccount(account_id="a-1", account_type="checking", balance=0.0)
        assert get_entity_type(account) == "account"
    
    def test_transaction_type(self):
        """Test detecting transaction entity type."""
        txn = MockTransaction(transaction_id="t-1", amount=50.0, from_account="a-1", to_account="a-2")
        assert get_entity_type(txn) == "transaction"
    
    def test_company_type(self):
        """Test detecting company entity type."""
        company = MockCompany(company_id="c-1", name="Corp", industry="Tech")
        assert get_entity_type(company) == "company"
    
    def test_communication_type(self):
        """Test detecting communication entity type."""
        comm = MockCommunication(communication_id="cm-1", sender_id="p-1", recipient_id="p-2", content="Hi")
        assert get_entity_type(comm) == "communication"


class TestGetTextForEmbedding:
    """Tests for get_text_for_embedding function."""
    
    def test_person_embedding_text(self):
        """Test extracting embedding text for person."""
        person = MockPerson(id="p-1", first_name="John", last_name="Doe", email="j@e.com")
        result = get_text_for_embedding(person, "person")
        assert "John" in result
        assert "Doe" in result
    
    def test_company_embedding_text(self):
        """Test extracting embedding text for company."""
        company = MockCompany(company_id="c-1", name="Acme Corporation", industry="Tech")
        result = get_text_for_embedding(company, "company")
        assert result == "Acme Corporation"
    
    def test_communication_embedding_text(self):
        """Test extracting embedding text for communication."""
        comm = MockCommunication(
            communication_id="cm-1",
            sender_id="p-1",
            recipient_id="p-2",
            content="This is a test message"
        )
        result = get_text_for_embedding(comm, "communication")
        assert result == "This is a test message"
    
    def test_transaction_no_embedding(self):
        """Test that transactions return None for embedding."""
        txn = MockTransaction(transaction_id="t-1", amount=50.0, from_account="a-1", to_account="a-2")
        result = get_text_for_embedding(txn, "transaction")
        assert result is None
    
    def test_account_no_embedding(self):
        """Test that accounts return None for embedding."""
        account = MockAccount(account_id="a-1", account_type="checking", balance=100.0)
        result = get_text_for_embedding(account, "account")
        assert result is None


class TestConvertEntityToEvent:
    """Tests for convert_entity_to_event function."""
    
    def test_basic_conversion(self):
        """Test basic entity to event conversion."""
        person = MockPerson(id="p-123", first_name="John", last_name="Doe", email="john@example.com")
        event = convert_entity_to_event(person)
        
        assert isinstance(event, EntityEvent)
        assert event.entity_id == "p-123"
        assert event.entity_type == "person"
        assert event.event_type == "create"
        assert event.payload['first_name'] == "John"
        assert "John" in (event.text_for_embedding or "")
    
    def test_update_event_type(self):
        """Test creating an update event."""
        person = MockPerson(id="p-123", first_name="John", last_name="Doe", email="john@example.com")
        event = convert_entity_to_event(person, event_type="update")
        
        assert event.event_type == "update"
    
    def test_delete_event_type(self):
        """Test creating a delete event."""
        person = MockPerson(id="p-123", first_name="John", last_name="Doe", email="john@example.com")
        event = convert_entity_to_event(person, event_type="delete")
        
        assert event.event_type == "delete"
    
    def test_custom_source(self):
        """Test custom source parameter."""
        person = MockPerson(id="p-123", first_name="John", last_name="Doe", email="john@example.com")
        event = convert_entity_to_event(person, source="TestGenerator")
        
        assert event.source == "TestGenerator"
    
    def test_custom_version(self):
        """Test custom version parameter."""
        person = MockPerson(id="p-123", first_name="John", last_name="Doe", email="john@example.com")
        event = convert_entity_to_event(person, version=5)
        
        assert event.version == 5
    
    def test_metadata(self):
        """Test metadata parameter."""
        person = MockPerson(id="p-123", first_name="John", last_name="Doe", email="john@example.com")
        event = convert_entity_to_event(person, metadata={"batch_id": "b-1"})
        
        assert event.metadata == {"batch_id": "b-1"}
    
    def test_event_has_valid_topic(self):
        """Test that converted event has valid topic."""
        person = MockPerson(id="p-123", first_name="John", last_name="Doe", email="john@example.com")
        event = convert_entity_to_event(person)
        
        topic = event.get_topic()
        assert "persons-events" in topic
    
    def test_account_conversion(self):
        """Test account entity conversion."""
        account = MockAccount(account_id="a-456", account_type="savings", balance=5000.0)
        event = convert_entity_to_event(account)
        
        assert event.entity_id == "a-456"
        assert event.entity_type == "account"
        assert event.payload['balance'] == 5000.0
    
    def test_transaction_conversion(self):
        """Test transaction entity conversion."""
        txn = MockTransaction(
            transaction_id="t-789",
            amount=1500.0,
            from_account="a-1",
            to_account="a-2"
        )
        event = convert_entity_to_event(txn)
        
        assert event.entity_id == "t-789"
        assert event.entity_type == "transaction"
        assert event.payload['amount'] == 1500.0


class TestConvertEntitiesToEvents:
    """Tests for convert_entities_to_events function."""
    
    def test_batch_conversion(self):
        """Test converting multiple entities to events."""
        persons = [
            MockPerson(id=f"p-{i}", first_name=f"Person{i}", last_name="Test", email=f"p{i}@test.com")
            for i in range(5)
        ]
        events = convert_entities_to_events(persons)
        
        assert len(events) == 5
        for i, event in enumerate(events):
            assert event.entity_id == f"p-{i}"
            assert event.entity_type == "person"
            assert event.event_type == "create"
    
    def test_batch_with_event_type(self):
        """Test batch conversion with specific event type."""
        accounts = [
            MockAccount(account_id=f"a-{i}", account_type="checking", balance=float(i * 100))
            for i in range(3)
        ]
        events = convert_entities_to_events(accounts, event_type="update")
        
        assert all(e.event_type == "update" for e in events)
    
    def test_batch_with_source(self):
        """Test batch conversion with source."""
        companies = [
            MockCompany(company_id=f"c-{i}", name=f"Company{i}", industry="Tech")
            for i in range(2)
        ]
        events = convert_entities_to_events(companies, source="BatchImport")
        
        assert all(e.source == "BatchImport" for e in events)
    
    def test_empty_batch(self):
        """Test converting empty list."""
        events = convert_entities_to_events([])
        assert events == []


class TestEventSerialization:
    """Tests for event serialization after conversion."""
    
    def test_to_json(self):
        """Test that converted event can be serialized to JSON."""
        person = MockPerson(id="p-123", first_name="John", last_name="Doe", email="john@example.com")
        event = convert_entity_to_event(person)
        
        json_str = event.to_json()
        assert isinstance(json_str, str)
        assert "p-123" in json_str
        assert "person" in json_str
    
    def test_to_pulsar_message(self):
        """Test that converted event produces valid Pulsar message."""
        person = MockPerson(id="p-123", first_name="John", last_name="Doe", email="john@example.com")
        event = convert_entity_to_event(person)
        
        msg = event.to_pulsar_message()
        assert 'partition_key' in msg
        assert 'sequence_id' in msg
        assert 'content' in msg
        assert msg['partition_key'] == "p-123"
    
    def test_roundtrip_serialization(self):
        """Test serialization and deserialization roundtrip."""
        person = MockPerson(id="p-123", first_name="John", last_name="Doe", email="john@example.com")
        event = convert_entity_to_event(person, source="Test", version=2)
        
        # Serialize
        json_str = event.to_json()
        
        # Deserialize
        restored = EntityEvent.from_json(json_str)
        
        assert restored.entity_id == event.entity_id
        assert restored.entity_type == event.entity_type
        assert restored.event_type == event.event_type
        assert restored.source == event.source
        assert restored.version == event.version


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
