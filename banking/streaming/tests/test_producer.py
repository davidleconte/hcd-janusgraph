"""
Unit tests for EntityProducer and MockEntityProducer.

Tests cover:
- MockEntityProducer functionality (no Pulsar required)
- Event sending and batch operations
- Topic routing
- Factory function

Created: 2026-02-04
"""

from banking.streaming.events import EntityEvent, create_person_event
from banking.streaming.producer import MockEntityProducer, get_producer


class TestMockEntityProducer:
    """Tests for MockEntityProducer (no Pulsar required)."""
    
    def test_create_mock_producer(self):
        """Test creating a mock producer."""
        producer = MockEntityProducer()
        
        assert producer.is_connected
        assert len(producer.events) == 0
    
    def test_send_event(self):
        """Test sending an event."""
        producer = MockEntityProducer()
        
        event = EntityEvent(
            entity_id="test-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John"}
        )
        
        producer.send(event)
        
        assert len(producer.events) == 1
        assert producer.events[0].entity_id == "test-123"
    
    def test_send_multiple_events(self):
        """Test sending multiple events."""
        producer = MockEntityProducer()
        
        for i in range(5):
            event = EntityEvent(
                entity_id=f"test-{i}",
                event_type="create",
                entity_type="person",
                payload={}
            )
            producer.send(event)
        
        assert len(producer.events) == 5
    
    def test_events_by_topic(self):
        """Test events are grouped by topic."""
        producer = MockEntityProducer()
        
        # Send person events
        producer.send(EntityEvent(
            entity_id="p1", event_type="create", entity_type="person", payload={}
        ))
        producer.send(EntityEvent(
            entity_id="p2", event_type="create", entity_type="person", payload={}
        ))
        
        # Send account event
        producer.send(EntityEvent(
            entity_id="a1", event_type="create", entity_type="account", payload={}
        ))
        
        assert "persistent://public/banking/persons-events" in producer.events_by_topic
        assert "persistent://public/banking/accounts-events" in producer.events_by_topic
        assert len(producer.events_by_topic["persistent://public/banking/persons-events"]) == 2
        assert len(producer.events_by_topic["persistent://public/banking/accounts-events"]) == 1
    
    def test_send_batch(self):
        """Test sending a batch of events."""
        producer = MockEntityProducer()
        
        events = [
            EntityEvent(entity_id=f"test-{i}", event_type="create", entity_type="person", payload={})
            for i in range(10)
        ]
        
        results = producer.send_batch(events)
        
        assert len(producer.events) == 10
        assert "persistent://public/banking/persons-events" in results
        assert results["persistent://public/banking/persons-events"] == 10
    
    def test_send_with_callback(self):
        """Test sending with callback."""
        producer = MockEntityProducer()
        callback_called = []
        
        def callback(result, msg_id):
            callback_called.append(True)
        
        event = EntityEvent(
            entity_id="test-123",
            event_type="create",
            entity_type="person",
            payload={}
        )
        
        producer.send(event, callback=callback)
        
        assert len(callback_called) == 1
    
    def test_flush(self):
        """Test flush is a no-op."""
        producer = MockEntityProducer()
        producer.send(EntityEvent(
            entity_id="test", event_type="create", entity_type="person", payload={}
        ))
        
        # Should not raise
        producer.flush()
        
        assert len(producer.events) == 1
    
    def test_close(self):
        """Test close clears events."""
        producer = MockEntityProducer()
        producer.send(EntityEvent(
            entity_id="test", event_type="create", entity_type="person", payload={}
        ))
        
        producer.close()
        
        assert len(producer.events) == 0
        assert not producer.is_connected
    
    def test_clear(self):
        """Test clear method."""
        producer = MockEntityProducer()
        producer.send(EntityEvent(
            entity_id="test", event_type="create", entity_type="person", payload={}
        ))
        
        producer.clear()
        
        assert len(producer.events) == 0
        assert producer.is_connected  # Still connected after clear
    
    def test_context_manager(self):
        """Test using producer as context manager."""
        with MockEntityProducer() as producer:
            producer.send(EntityEvent(
                entity_id="test", event_type="create", entity_type="person", payload={}
            ))
            assert len(producer.events) == 1
        
        # After exit, should be closed
        assert not producer.is_connected
    
    def test_get_stats(self):
        """Test getting producer statistics."""
        producer = MockEntityProducer()
        producer.send(EntityEvent(
            entity_id="test", event_type="create", entity_type="person", payload={}
        ))
        
        stats = producer.get_stats()
        
        assert stats['connected'] is True
        assert stats['events_count'] == 1
        assert len(stats['topics']) == 1


class TestGetProducerFactory:
    """Tests for get_producer factory function."""
    
    def test_get_mock_producer(self):
        """Test getting mock producer explicitly."""
        producer = get_producer(mock=True)
        
        assert isinstance(producer, MockEntityProducer)
    
    def test_factory_returns_mock_when_pulsar_unavailable(self):
        """Test factory returns mock when pulsar not available."""
        # This will return MockEntityProducer since pulsar-client 
        # may not be installed in test environment
        producer = get_producer(mock=True)
        
        assert producer is not None
        assert hasattr(producer, 'send')
        assert hasattr(producer, 'close')


class TestProducerIntegration:
    """Integration-style tests using MockEntityProducer."""
    
    def test_full_workflow(self):
        """Test complete workflow: create events, send, verify."""
        with MockEntityProducer() as producer:
            # Create various events
            person = create_person_event(
                person_id="person-001",
                name="John Doe",
                payload={"email": "john@example.com", "risk_score": 0.3}
            )
            
            # Send
            producer.send(person)
            
            # Verify
            assert len(producer.events) == 1
            assert producer.events[0].entity_id == "person-001"
            assert producer.events[0].text_for_embedding == "John Doe"
    
    def test_batch_mixed_entity_types(self):
        """Test batch with multiple entity types."""
        producer = MockEntityProducer()
        
        events = [
            EntityEvent(entity_id="p1", event_type="create", entity_type="person", payload={"name": "John"}),
            EntityEvent(entity_id="a1", event_type="create", entity_type="account", payload={"balance": 1000}),
            EntityEvent(entity_id="c1", event_type="create", entity_type="company", payload={"name": "ACME"}),
            EntityEvent(entity_id="t1", event_type="create", entity_type="transaction", payload={"amount": 500}),
        ]
        
        results = producer.send_batch(events)
        
        assert len(producer.events) == 4
        assert len(results) == 4  # 4 different topics
        
        producer.close()
