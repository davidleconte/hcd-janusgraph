"""
Unit Tests for StreamingOrchestrator
====================================

Tests for the Pulsar-integrated data generation orchestrator.

Created: 2026-02-06
"""

import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from banking.streaming.producer import MockEntityProducer
from banking.streaming.streaming_orchestrator import (
    StreamingConfig,
    StreamingOrchestrator,
    StreamingStats,
)


class TestStreamingConfig:
    """Tests for StreamingConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = StreamingConfig()

        assert config.enable_streaming is True
        assert config.pulsar_url == "pulsar://localhost:6650"
        assert config.pulsar_namespace == "public/banking"
        assert config.use_mock_producer is False
        assert config.streaming_batch_size == 100
        assert config.flush_after_phase is True

    def test_inheritance_from_generation_config(self):
        """Test that StreamingConfig inherits GenerationConfig fields."""
        config = StreamingConfig(
            seed=42, person_count=50, company_count=10, account_count=100, enable_streaming=True
        )

        assert config.seed == 42
        assert config.person_count == 50
        assert config.company_count == 10
        assert config.account_count == 100

    def test_custom_streaming_settings(self):
        """Test custom streaming configuration."""
        config = StreamingConfig(
            pulsar_url="pulsar://custom:6650",
            pulsar_namespace="custom/namespace",
            use_mock_producer=True,
            streaming_batch_size=500,
        )

        assert config.pulsar_url == "pulsar://custom:6650"
        assert config.pulsar_namespace == "custom/namespace"
        assert config.use_mock_producer is True
        assert config.streaming_batch_size == 500


class TestStreamingStats:
    """Tests for StreamingStats dataclass."""

    def test_default_values(self):
        """Test default statistics values."""
        stats = StreamingStats()

        assert stats.events_published == 0
        assert stats.events_failed == 0
        assert stats.events_by_type == {}
        assert stats.streaming_errors == []

    def test_inheritance_from_generation_stats(self):
        """Test that StreamingStats inherits GenerationStats fields."""
        stats = StreamingStats()

        assert stats.persons_generated == 0
        assert stats.companies_generated == 0
        assert stats.accounts_generated == 0
        assert stats.transactions_generated == 0


class TestStreamingOrchestratorInitialization:
    """Tests for StreamingOrchestrator initialization."""

    def test_init_with_mock_producer(self):
        """Test initialization with mock producer."""
        config = StreamingConfig(
            seed=42,
            person_count=5,
            company_count=2,
            account_count=10,
            transaction_count=0,
            communication_count=0,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=True,
        )

        orchestrator = StreamingOrchestrator(config)

        assert orchestrator.producer is not None
        assert isinstance(orchestrator.producer, MockEntityProducer)
        orchestrator.close()

    def test_init_with_injected_producer(self):
        """Test initialization with injected producer."""
        mock_producer = MockEntityProducer()
        config = StreamingConfig(
            seed=42,
            person_count=5,
            company_count=2,
            account_count=10,
            transaction_count=0,
            communication_count=0,
            enable_streaming=True,
        )

        orchestrator = StreamingOrchestrator(config, producer=mock_producer)

        assert orchestrator.producer is mock_producer
        assert orchestrator._owns_producer is False

    def test_init_streaming_disabled(self):
        """Test initialization with streaming disabled."""
        config = StreamingConfig(
            seed=42,
            person_count=5,
            company_count=2,
            account_count=10,
            transaction_count=0,
            communication_count=0,
            enable_streaming=False,
        )

        orchestrator = StreamingOrchestrator(config)

        assert orchestrator.producer is None

    def test_context_manager(self):
        """Test context manager usage."""
        config = StreamingConfig(
            seed=42,
            person_count=5,
            company_count=2,
            account_count=10,
            transaction_count=0,
            communication_count=0,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=True,
        )

        with StreamingOrchestrator(config) as orchestrator:
            assert orchestrator.producer is not None
            assert orchestrator.producer.is_connected


class TestStreamingOrchestratorGeneration:
    """Tests for entity generation with streaming."""

    @pytest.fixture
    def small_config(self):
        """Create a small configuration for fast tests."""
        return StreamingConfig(
            seed=42,
            person_count=5,
            company_count=2,
            account_count=10,
            transaction_count=20,
            communication_count=10,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=True,
            output_dir=Path(tempfile.mkdtemp()),
        )

    @pytest.fixture
    def orchestrator(self, small_config):
        """Create orchestrator with small config."""
        orch = StreamingOrchestrator(small_config)
        yield orch
        orch.close()
        shutil.rmtree(small_config.output_dir, ignore_errors=True)

    def test_generate_all_basic(self, orchestrator):
        """Test basic generation with streaming."""
        stats = orchestrator.generate_all()

        assert stats.persons_generated == 5
        assert stats.companies_generated == 2
        assert stats.accounts_generated == 10
        assert stats.transactions_generated == 20
        assert stats.communications_generated == 10

    def test_events_published(self, orchestrator):
        """Test that events are published during generation."""
        stats = orchestrator.generate_all()

        # All entities should be published
        expected_events = (
            5 + 2 + 10 + 20 + 10
        )  # persons + companies + accounts + transactions + communications
        assert stats.events_published == expected_events
        assert stats.events_failed == 0

    def test_events_by_type_tracking(self, orchestrator):
        """Test that events are tracked by type."""
        stats = orchestrator.generate_all()

        assert stats.events_by_type.get("person", 0) == 5
        assert stats.events_by_type.get("company", 0) == 2
        assert stats.events_by_type.get("account", 0) == 10
        assert stats.events_by_type.get("transaction", 0) == 20
        assert stats.events_by_type.get("communication", 0) == 10

    def test_mock_producer_receives_events(self, orchestrator):
        """Test that mock producer receives all events."""
        orchestrator.generate_all()

        mock_producer = orchestrator.producer
        assert len(mock_producer.events) > 0

        # Check events are properly typed
        person_events = [e for e in mock_producer.events if e.entity_type == "person"]
        assert len(person_events) == 5

        account_events = [e for e in mock_producer.events if e.entity_type == "account"]
        assert len(account_events) == 10

    def test_event_payload_contains_data(self, orchestrator):
        """Test that event payloads contain entity data."""
        orchestrator.generate_all()

        mock_producer = orchestrator.producer
        person_events = [e for e in mock_producer.events if e.entity_type == "person"]

        for event in person_events:
            assert event.entity_id is not None
            assert event.payload is not None
            assert isinstance(event.payload, dict)

    def test_streaming_disabled_no_events(self):
        """Test that no events are published when streaming is disabled."""
        config = StreamingConfig(
            seed=42,
            person_count=5,
            company_count=2,
            account_count=10,
            transaction_count=0,
            communication_count=0,
            trade_count=0,
            travel_count=0,
            document_count=0,
            enable_streaming=False,
            output_dir=Path(tempfile.mkdtemp()),
        )

        with StreamingOrchestrator(config) as orchestrator:
            stats = orchestrator.generate_all()

            assert stats.events_published == 0
            assert orchestrator.producer is None

        shutil.rmtree(config.output_dir, ignore_errors=True)


class TestStreamingOrchestratorStats:
    """Tests for streaming statistics."""

    @pytest.fixture
    def orchestrator_with_events(self):
        """Create orchestrator that has generated events."""
        config = StreamingConfig(
            seed=42,
            person_count=10,
            company_count=5,
            account_count=20,
            transaction_count=50,
            communication_count=25,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=True,
            output_dir=Path(tempfile.mkdtemp()),
        )
        orchestrator = StreamingOrchestrator(config)
        orchestrator.generate_all()
        yield orchestrator
        orchestrator.close()
        shutil.rmtree(config.output_dir, ignore_errors=True)

    def test_get_streaming_stats(self, orchestrator_with_events):
        """Test get_streaming_stats method."""
        stats = orchestrator_with_events.get_streaming_stats()

        assert "events_published" in stats
        assert "events_failed" in stats
        assert "events_by_type" in stats
        assert "streaming_errors" in stats
        assert "producer_stats" in stats

    def test_stats_finalization(self, orchestrator_with_events):
        """Test that stats are properly finalized."""
        stats = orchestrator_with_events.stats

        assert stats.total_records > 0
        assert stats.generation_time_seconds > 0
        assert stats.end_time is not None


class TestStreamingOrchestratorErrorHandling:
    """Tests for error handling in StreamingOrchestrator."""

    def test_publish_failure_tracked(self):
        """Test that publish failures are tracked."""
        config = StreamingConfig(
            seed=42,
            person_count=3,
            company_count=1,
            account_count=5,
            transaction_count=0,
            communication_count=0,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=True,
            output_dir=Path(tempfile.mkdtemp()),
        )

        # Create a mock producer that fails
        failing_producer = MockEntityProducer()
        original_send = failing_producer.send
        fail_count = [0]

        def failing_send(event, callback=None):
            fail_count[0] += 1
            if fail_count[0] <= 2:  # Fail first 2 sends
                raise Exception("Simulated failure")
            return original_send(event, callback)

        failing_producer.send = failing_send

        orchestrator = StreamingOrchestrator(config, producer=failing_producer)
        stats = orchestrator.generate_all()

        # Some events should have failed
        assert stats.events_failed >= 2
        assert len(stats.streaming_errors) >= 2

        shutil.rmtree(config.output_dir, ignore_errors=True)

    @patch("banking.streaming.producer.pulsar")
    def test_fallback_to_mock_on_connection_failure(self, mock_pulsar):
        """Test fallback to MockEntityProducer when Pulsar unavailable."""
        mock_pulsar.Client.side_effect = Exception("Connection refused")

        config = StreamingConfig(
            seed=42,
            person_count=5,
            company_count=2,
            account_count=10,
            transaction_count=0,
            communication_count=0,
            trade_count=0,
            travel_count=0,
            document_count=0,
            pulsar_url="pulsar://nonexistent:6650",
            use_mock_producer=False,  # Try real, expect fallback
            output_dir=Path(tempfile.mkdtemp()),
        )

        orchestrator = StreamingOrchestrator(config)

        # Should have fallen back to mock producer
        assert isinstance(orchestrator.producer, MockEntityProducer)

        orchestrator.close()
        shutil.rmtree(config.output_dir, ignore_errors=True)


class TestStreamingOrchestratorWithRealGenerators:
    """Integration-style tests using real data generators."""

    @pytest.fixture
    def full_config(self):
        """Create configuration for more realistic tests."""
        return StreamingConfig(
            seed=12345,
            person_count=20,
            company_count=5,
            account_count=30,
            transaction_count=100,
            communication_count=50,
            trade_count=10,
            travel_count=5,
            document_count=10,
            use_mock_producer=True,
            output_dir=Path(tempfile.mkdtemp()),
        )

    def test_full_generation_cycle(self, full_config):
        """Test complete generation cycle with all entity types."""
        with StreamingOrchestrator(full_config) as orchestrator:
            stats = orchestrator.generate_all()

            # Verify all entities generated
            assert stats.persons_generated == 20
            assert stats.companies_generated == 5
            assert stats.accounts_generated == 30
            assert stats.transactions_generated == 100
            assert stats.communications_generated == 50
            assert stats.trades_generated == 10
            assert stats.travels_generated == 5
            assert stats.documents_generated == 10

            # Verify events published
            total_entities = 20 + 5 + 30 + 100 + 50 + 10 + 5 + 10
            assert stats.events_published == total_entities

            # Verify in-memory data
            assert len(orchestrator.persons) == 20
            assert len(orchestrator.companies) == 5
            assert len(orchestrator.accounts) == 30

        shutil.rmtree(full_config.output_dir, ignore_errors=True)

    def test_reproducibility_with_seed(self, full_config):
        """Test that same seed produces reproducible name patterns."""
        # Note: UUIDs are generated via uuid.uuid4() which is NOT seeded
        # So we test reproducibility of other seeded attributes like names

        # First generation
        with StreamingOrchestrator(full_config) as orchestrator1:
            orchestrator1.generate_all()
            # Get first names (which ARE seeded via Faker)
            names1 = [p.first_name for p in orchestrator1.persons]

        # Reset output dir
        shutil.rmtree(full_config.output_dir, ignore_errors=True)
        full_config.output_dir = Path(tempfile.mkdtemp())

        # Second generation with same seed
        full_config2 = StreamingConfig(
            seed=full_config.seed,
            person_count=full_config.person_count,
            company_count=full_config.company_count,
            account_count=full_config.account_count,
            transaction_count=full_config.transaction_count,
            communication_count=full_config.communication_count,
            trade_count=full_config.trade_count,
            travel_count=full_config.travel_count,
            document_count=full_config.document_count,
            use_mock_producer=True,
            output_dir=Path(tempfile.mkdtemp()),
        )

        with StreamingOrchestrator(full_config2) as orchestrator2:
            orchestrator2.generate_all()
            names2 = [p.first_name for p in orchestrator2.persons]

        # Names should be same due to same seed (Faker is seeded)
        assert names1 == names2

        shutil.rmtree(full_config.output_dir, ignore_errors=True)
        shutil.rmtree(full_config2.output_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
