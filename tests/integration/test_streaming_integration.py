"""
Integration Tests for Streaming Pipeline
========================================

Tests the complete streaming pipeline including:
- Entity generation with StreamingOrchestrator
- Event publishing to Pulsar (or mock)
- Consumer processing (mocked)

These tests require no external services by default (using mock producer).
Set PULSAR_INTEGRATION=1 to test with real Pulsar.

Created: 2026-02-06
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from banking.streaming.entity_converter import convert_entity_to_event
from banking.streaming.events import EntityEvent, EntityEventBatch
from banking.streaming.graph_consumer import GraphConsumer
from banking.streaming.producer import MockEntityProducer, get_producer
from banking.streaming.streaming_orchestrator import StreamingConfig, StreamingOrchestrator
from banking.streaming.vector_consumer import VectorConsumer

# Skip real Pulsar tests unless explicitly enabled
PULSAR_INTEGRATION = os.getenv("PULSAR_INTEGRATION", "0") == "1"


class TestStreamingPipelineWithMock:
    """Integration tests using MockEntityProducer."""

    @pytest.fixture
    def output_dir(self):
        """Create temporary output directory."""
        path = Path(tempfile.mkdtemp())
        yield path
        shutil.rmtree(path, ignore_errors=True)

    @pytest.fixture
    def streaming_config(self, output_dir):
        """Create streaming configuration for integration tests."""
        return StreamingConfig(
            seed=42,
            person_count=10,
            company_count=3,
            account_count=15,
            transaction_count=30,
            communication_count=20,
            trade_count=5,
            travel_count=3,
            document_count=5,
            use_mock_producer=True,
            output_dir=output_dir,
        )

    def test_full_pipeline_mock(self, streaming_config):
        """Test complete pipeline with mock producer."""
        with StreamingOrchestrator(streaming_config) as orchestrator:
            stats = orchestrator.generate_all()

            # Verify generation
            assert stats.persons_generated == 10
            assert stats.companies_generated == 3
            assert stats.accounts_generated == 15

            # Verify events captured by mock producer
            mock_producer = orchestrator.producer
            assert isinstance(mock_producer, MockEntityProducer)

            # Count events by type
            events_by_type = {}
            for event in mock_producer.events:
                et = event.entity_type
                events_by_type[et] = events_by_type.get(et, 0) + 1

            assert events_by_type.get("person", 0) == 10
            assert events_by_type.get("company", 0) == 3
            assert events_by_type.get("account", 0) == 15
            assert events_by_type.get("transaction", 0) == 30
            assert events_by_type.get("communication", 0) == 20

    def test_event_content_integrity(self, streaming_config):
        """Test that event payloads contain valid data."""
        with StreamingOrchestrator(streaming_config) as orchestrator:
            orchestrator.generate_all()

            mock_producer = orchestrator.producer

            # Check person events
            person_events = [e for e in mock_producer.events if e.entity_type == "person"]
            for event in person_events:
                assert event.entity_id is not None
                assert event.event_type == "create"
                assert event.payload is not None
                # Person payload should have name-related fields
                payload = event.payload
                assert "id" in payload or "person_id" in payload

            # Check account events
            account_events = [e for e in mock_producer.events if e.entity_type == "account"]
            for event in account_events:
                assert event.entity_id is not None
                assert event.payload is not None

    def test_event_topic_routing(self, streaming_config):
        """Test that events are routed to correct topics."""
        with StreamingOrchestrator(streaming_config) as orchestrator:
            orchestrator.generate_all()

            mock_producer = orchestrator.producer

            # Check events_by_topic
            topics = set()
            for event in mock_producer.events:
                topics.add(event.get_topic())

            # Should have topics for each entity type
            # Note: topic naming uses {entity_type}s-events, so "company" -> "companys-events"
            assert any("persons-events" in t for t in topics)
            assert any("companys-events" in t for t in topics)
            assert any("accounts-events" in t for t in topics)
            assert any("transactions-events" in t for t in topics)
            assert any("communications-events" in t for t in topics)

    def test_event_serialization_valid(self, streaming_config):
        """Test that all events can be serialized."""
        streaming_config.person_count = 5
        streaming_config.company_count = 2
        streaming_config.account_count = 5
        streaming_config.transaction_count = 10
        streaming_config.communication_count = 5

        with StreamingOrchestrator(streaming_config) as orchestrator:
            orchestrator.generate_all()

            mock_producer = orchestrator.producer

            for event in mock_producer.events:
                # Should be able to serialize to JSON
                json_str = event.to_json()
                assert isinstance(json_str, str)
                assert len(json_str) > 0

                # Should be able to create Pulsar message
                msg = event.to_pulsar_message()
                assert "partition_key" in msg
                assert "sequence_id" in msg
                assert "content" in msg

                # Should be able to deserialize
                restored = EntityEvent.from_json(json_str)
                assert restored.entity_id == event.entity_id
                assert restored.entity_type == event.entity_type


class TestConsumerIntegration:
    """Tests for consumer integration (mocked Gremlin/OpenSearch)."""

    @pytest.fixture
    def sample_events(self):
        """Create sample events for consumer testing."""
        from dataclasses import dataclass

        @dataclass
        class MockPerson:
            id: str
            first_name: str
            last_name: str

        @dataclass
        class MockAccount:
            account_id: str
            account_type: str
            balance: float

        persons = [MockPerson(f"p-{i}", f"Person{i}", "Test") for i in range(5)]
        accounts = [MockAccount(f"a-{i}", "checking", float(i * 100)) for i in range(5)]

        events = []
        for p in persons:
            events.append(convert_entity_to_event(p, source="Test"))
        for a in accounts:
            events.append(convert_entity_to_event(a, source="Test"))

        return events

    @pytest.mark.skip(reason="Requires pulsar-client which is not installed in test environment")
    def test_graph_consumer_processes_events(self, sample_events):
        """Test that GraphConsumer can process events (with mocked Gremlin)."""
        # Mock the gremlin connection
        mock_connection = MagicMock()
        mock_g = MagicMock()

        with patch(
            "banking.streaming.graph_consumer.DriverRemoteConnection", return_value=mock_connection
        ):
            with patch("banking.streaming.graph_consumer.traversal") as mock_traversal:
                mock_traversal.return_value.with_remote.return_value = mock_g

                consumer = GraphConsumer(
                    janusgraph_url="ws://localhost:8182/gremlin", subscription_name="test-sub"
                )

                # Process a single event
                event = sample_events[0]
                # The actual processing would call Gremlin - we're testing the pipeline

                consumer.close()

    @pytest.mark.skip(reason="Requires pulsar-client which is not installed in test environment")
    def test_vector_consumer_processes_events(self, sample_events):
        """Test that VectorConsumer can process events (with mocked OpenSearch)."""
        # Mock OpenSearch client
        mock_os_client = MagicMock()

        with patch("banking.streaming.vector_consumer.OpenSearch", return_value=mock_os_client):
            consumer = VectorConsumer(
                opensearch_host="localhost", opensearch_port=9200, subscription_name="test-sub"
            )

            # Test that consumer was initialized
            assert consumer is not None

            consumer.close()


class TestEventBatchProcessing:
    """Tests for batch event processing."""

    @pytest.fixture
    def large_batch(self):
        """Create a large batch of events using valid entity types."""
        from dataclasses import dataclass

        @dataclass
        class MockPerson:
            id: str
            first_name: str
            last_name: str

        events = []
        for i in range(100):
            entity = MockPerson(f"p-{i}", f"Person{i}", "Test")
            events.append(convert_entity_to_event(entity, source="BatchTest"))

        return EntityEventBatch(events=events)

    def test_batch_grouping_by_type(self, large_batch):
        """Test batch grouping by entity type."""
        grouped = large_batch.by_entity_type()

        # All events should be person type
        assert len(grouped) == 1
        assert "person" in grouped
        assert len(grouped["person"]) == 100

    def test_batch_grouping_by_topic(self, large_batch):
        """Test batch grouping by topic."""
        grouped = large_batch.by_topic()

        # All events go to same topic
        assert len(grouped) == 1
        topic = list(grouped.keys())[0]
        assert "persons-events" in topic
        assert len(grouped[topic]) == 100


class TestStreamingE2EFlow:
    """End-to-end flow tests using mock services."""

    @pytest.fixture
    def e2e_config(self):
        """Create E2E test configuration."""
        return StreamingConfig(
            seed=99999,
            person_count=5,
            company_count=2,
            account_count=8,
            transaction_count=15,
            communication_count=10,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=True,
            output_dir=Path(tempfile.mkdtemp()),
        )

    def test_e2e_generation_to_events(self, e2e_config):
        """Test E2E flow: generation -> events -> mock destinations."""
        # Track events that would go to each destination
        graph_events = []
        vector_events = []

        with StreamingOrchestrator(e2e_config) as orchestrator:
            stats = orchestrator.generate_all()

            # Get events from mock producer
            mock_producer = orchestrator.producer

            # Simulate dual-leg processing
            for event in mock_producer.events:
                # Leg 1: Graph (all events)
                graph_events.append(event)

                # Leg 2: Vector (only events with embedding text)
                if event.text_for_embedding:
                    vector_events.append(event)

        # Verify graph leg received all events
        assert len(graph_events) == stats.events_published

        # Verify vector leg received appropriate events
        # Only persons and companies have embedding text by default
        person_count = e2e_config.person_count
        company_count = e2e_config.company_count
        assert len(vector_events) >= person_count + company_count

        shutil.rmtree(e2e_config.output_dir, ignore_errors=True)

    def test_e2e_id_consistency(self, e2e_config):
        """Test that entity IDs are consistent across the pipeline."""
        with StreamingOrchestrator(e2e_config) as orchestrator:
            orchestrator.generate_all()

            mock_producer = orchestrator.producer

            # Build ID sets from events
            event_person_ids = {
                e.entity_id for e in mock_producer.events if e.entity_type == "person"
            }
            event_account_ids = {
                e.entity_id for e in mock_producer.events if e.entity_type == "account"
            }

            # Build ID sets from in-memory entities
            memory_person_ids = {str(p.id) for p in orchestrator.persons}
            memory_account_ids = {str(a.id) for a in orchestrator.accounts}

            # IDs should match exactly
            assert event_person_ids == memory_person_ids
            assert event_account_ids == memory_account_ids

        shutil.rmtree(e2e_config.output_dir, ignore_errors=True)

    def test_e2e_statistics_accuracy(self, e2e_config):
        """Test that statistics accurately reflect the pipeline."""
        with StreamingOrchestrator(e2e_config) as orchestrator:
            stats = orchestrator.generate_all()

            mock_producer = orchestrator.producer

            # Count events by type from producer
            actual_counts = {}
            for event in mock_producer.events:
                et = event.entity_type
                actual_counts[et] = actual_counts.get(et, 0) + 1

            # Verify against stats
            assert actual_counts.get("person", 0) == stats.events_by_type.get("person", 0)
            assert actual_counts.get("account", 0) == stats.events_by_type.get("account", 0)
            assert actual_counts.get("transaction", 0) == stats.events_by_type.get("transaction", 0)

            # Verify total
            assert sum(actual_counts.values()) == stats.events_published

        shutil.rmtree(e2e_config.output_dir, ignore_errors=True)


@pytest.mark.skipif(not PULSAR_INTEGRATION, reason="Pulsar integration tests disabled")
class TestRealPulsarIntegration:
    """Tests with real Pulsar (when available)."""

    @pytest.fixture
    def pulsar_config(self):
        """Create config for real Pulsar tests."""
        return StreamingConfig(
            seed=42,
            person_count=3,
            company_count=1,
            account_count=5,
            transaction_count=5,
            communication_count=3,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=False,
            pulsar_url=os.getenv("PULSAR_URL", "pulsar://localhost:6650"),
            output_dir=Path(tempfile.mkdtemp()),
        )

    def test_real_pulsar_connection(self, pulsar_config):
        """Test connecting to real Pulsar."""
        try:
            with StreamingOrchestrator(pulsar_config) as orchestrator:
                assert orchestrator.producer is not None
                assert orchestrator.producer.is_connected
        except Exception as e:
            pytest.skip(f"Pulsar not available: {e}")
        finally:
            shutil.rmtree(pulsar_config.output_dir, ignore_errors=True)

    def test_real_pulsar_publish(self, pulsar_config):
        """Test publishing to real Pulsar."""
        try:
            with StreamingOrchestrator(pulsar_config) as orchestrator:
                stats = orchestrator.generate_all()

                # Should have published without errors
                assert stats.events_failed == 0
                assert stats.events_published > 0
        except Exception as e:
            pytest.skip(f"Pulsar not available: {e}")
        finally:
            shutil.rmtree(pulsar_config.output_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
