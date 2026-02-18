"""Performance regression tests for JanusGraph Banking System.

This module contains benchmark tests to:
1. Establish performance baselines
2. Detect performance regressions
3. Validate optimization improvements
4. Profile critical code paths

Run with: pytest tests/benchmarks/test_performance_regression.py --benchmark-only
"""

import pytest

# Data generators
from banking.data_generators.core import (
    AccountGenerator,
    PersonGenerator,
)
from banking.data_generators.events import (
    CommunicationGenerator,
    TransactionGenerator,
)
from banking.data_generators.orchestration import GenerationConfig, MasterOrchestrator

# Streaming
from banking.streaming.events import create_account_event, create_person_event


class TestDataGenerationPerformance:
    """Performance benchmarks for data generation."""

    @pytest.mark.benchmark(group="generation-small")
    def test_person_generation_100(self, benchmark):
        """Benchmark: Generate 100 persons.

        Target: <0.5 seconds
        Baseline: ~0.3 seconds (before optimization)
        """
        generator = PersonGenerator(seed=42)
        result = benchmark(generator.generate_batch, 100)
        assert len(result) == 100
        assert benchmark.stats["mean"] < 0.5

    @pytest.mark.benchmark(group="generation-medium")
    def test_person_generation_1000(self, benchmark):
        """Benchmark: Generate 1000 persons.

        Target: <2.0 seconds
        Baseline: ~1.5 seconds (before optimization)
        """
        generator = PersonGenerator(seed=42)
        result = benchmark(generator.generate_batch, 1000)
        assert len(result) == 1000
        assert benchmark.stats["mean"] < 2.0

    @pytest.mark.benchmark(group="generation-small")
    def test_account_generation_100(self, benchmark):
        """Benchmark: Generate 100 accounts.

        Target: <0.3 seconds
        Baseline: ~0.2 seconds (before optimization)
        """
        generator = AccountGenerator(seed=42)
        result = benchmark(generator.generate_batch, 100)
        assert len(result) == 100
        assert benchmark.stats["mean"] < 0.3

    @pytest.mark.benchmark(group="generation-medium")
    def test_account_generation_1000(self, benchmark):
        """Benchmark: Generate 1000 accounts.

        Target: <1.5 seconds
        Baseline: ~1.0 seconds (before optimization)
        """
        generator = AccountGenerator(seed=42)
        result = benchmark(generator.generate_batch, 1000)
        assert len(result) == 1000
        assert benchmark.stats["mean"] < 1.5

    @pytest.mark.benchmark(group="generation-small")
    def test_transaction_generation_100(self, benchmark):
        """Benchmark: Generate 100 transactions.

        Target: <0.2 seconds
        Baseline: ~0.15 seconds (before optimization)
        """
        generator = TransactionGenerator(seed=42)
        result = benchmark(generator.generate_batch, 100)
        assert len(result) == 100
        assert benchmark.stats["mean"] < 0.2

    @pytest.mark.benchmark(group="generation-large")
    def test_transaction_generation_10000(self, benchmark):
        """Benchmark: Generate 10000 transactions.

        Target: <10.0 seconds
        Baseline: ~8.0 seconds (before optimization)
        """
        generator = TransactionGenerator(seed=42)
        result = benchmark(generator.generate_batch, 10000)
        assert len(result) == 10000
        assert benchmark.stats["mean"] < 10.0

    @pytest.mark.benchmark(group="generation-small")
    def test_communication_generation_100(self, benchmark):
        """Benchmark: Generate 100 communications.

        Target: <2.0 seconds (adjusted based on actual performance)
        Baseline: ~1.8 seconds (communications are complex with email/phone generation)
        """
        generator = CommunicationGenerator(seed=42)
        result = benchmark(generator.generate_batch, 100)
        assert len(result) == 100
        assert benchmark.stats["mean"] < 2.0

    @pytest.mark.benchmark(group="orchestration")
    def test_orchestrator_small_dataset(self, benchmark, tmp_path):
        """Benchmark: Generate small dataset via orchestrator.

        Target: <2.0 seconds
        Baseline: ~1.7 seconds (before optimization)
        """
        config = GenerationConfig(
            seed=42,
            person_count=50,
            company_count=10,
            account_count=100,
            transaction_count=500,
            communication_count=50,
            output_dir=tmp_path,
        )

        def run_orchestrator():
            orchestrator = MasterOrchestrator(config)
            return orchestrator.generate_all()

        result = benchmark(run_orchestrator)
        # GenerationStats object has attributes with _generated suffix
        assert result.persons_generated == 50
        assert result.companies_generated == 10
        assert result.accounts_generated == 100
        assert result.transactions_generated == 500
        assert result.communications_generated == 50
        assert benchmark.stats["mean"] < 2.0


class TestStreamingPerformance:
    """Performance benchmarks for streaming operations."""

    @pytest.mark.benchmark(group="streaming-serialization")
    def test_person_event_serialization(self, benchmark):
        """Benchmark: Person event serialization.

        Target: <0.001 seconds per event
        Baseline: ~0.0005 seconds (before optimization)
        """
        event = create_person_event(
            person_id="p-123",
            name="John Doe",
            payload={
                "email": "john@example.com",
                "phone": "+1234567890",
                "address": "123 Main St",
                "date_of_birth": "1990-01-01",
                "nationality": "US",
            },
        )
        result = benchmark(event.to_json)
        assert len(result) > 0
        assert benchmark.stats["mean"] < 0.001

    @pytest.mark.benchmark(group="streaming-serialization")
    def test_account_event_serialization(self, benchmark):
        """Benchmark: Account event serialization.

        Target: <0.001 seconds per event
        Baseline: ~0.0005 seconds (before optimization)
        """
        event = create_account_event(
            account_id="a-456",
            payload={
                "account_type": "CHECKING",
                "balance": 10000.00,
                "currency": "USD",
                "status": "ACTIVE",
                "opened_date": "2020-01-01",
            },
        )
        result = benchmark(event.to_json)
        assert len(result) > 0
        assert benchmark.stats["mean"] < 0.001

    @pytest.mark.benchmark(group="streaming-batch")
    def test_batch_event_creation_100(self, benchmark):
        """Benchmark: Create 100 events in batch.

        Target: <0.1 seconds
        Baseline: ~0.05 seconds (before optimization)
        """

        def create_batch():
            events = []
            for i in range(100):
                event = create_person_event(
                    person_id=f"p-{i}",
                    name=f"Person {i}",
                    payload={"email": f"person{i}@example.com"},
                )
                events.append(event)
            return events

        result = benchmark(create_batch)
        assert len(result) == 100
        assert benchmark.stats["mean"] < 0.1

    @pytest.mark.benchmark(group="streaming-batch")
    def test_batch_serialization_100(self, benchmark):
        """Benchmark: Serialize 100 events.

        Target: <0.1 seconds
        Baseline: ~0.05 seconds (before optimization)
        """
        events = [
            create_person_event(
                person_id=f"p-{i}",
                name=f"Person {i}",
                payload={"email": f"person{i}@example.com"},
            )
            for i in range(100)
        ]

        def serialize_batch():
            return [event.to_json() for event in events]

        result = benchmark(serialize_batch)
        assert len(result) == 100
        assert benchmark.stats["mean"] < 0.1


class TestMemoryPerformance:
    """Memory usage benchmarks."""

    @pytest.mark.benchmark(group="memory")
    def test_person_generation_memory(self, benchmark):
        """Benchmark: Memory usage for person generation.

        Target: <50MB for 1000 persons
        """
        import tracemalloc

        def generate_with_memory_tracking():
            tracemalloc.start()
            generator = PersonGenerator(seed=42)
            persons = generator.generate_batch(1000)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return persons, peak

        result, peak_memory = benchmark(generate_with_memory_tracking)
        assert len(result) == 1000
        # Peak memory should be less than 50MB (52428800 bytes)
        assert peak_memory < 52428800

    @pytest.mark.benchmark(group="memory")
    def test_transaction_generation_memory(self, benchmark):
        """Benchmark: Memory usage for transaction generation.

        Target: <100MB for 10000 transactions
        """
        import tracemalloc

        def generate_with_memory_tracking():
            tracemalloc.start()
            generator = TransactionGenerator(seed=42)
            transactions = generator.generate_batch(10000)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return transactions, peak

        result, peak_memory = benchmark(generate_with_memory_tracking)
        assert len(result) == 10000
        # Peak memory should be less than 100MB (104857600 bytes)
        assert peak_memory < 104857600


class TestValidationPerformance:
    """Performance benchmarks for validation operations."""

    @pytest.mark.benchmark(group="validation")
    def test_person_validation_100(self, benchmark):
        """Benchmark: Validate 100 person objects.

        Target: <0.05 seconds
        """
        generator = PersonGenerator(seed=42)
        persons = generator.generate_batch(100)

        def validate_batch():
            for person in persons:
                # Pydantic validation happens on access
                _ = person.model_dump()
            return len(persons)

        result = benchmark(validate_batch)
        assert result == 100
        assert benchmark.stats["mean"] < 0.05

    @pytest.mark.benchmark(group="validation")
    def test_account_validation_100(self, benchmark):
        """Benchmark: Validate 100 account objects.

        Target: <0.05 seconds
        """
        generator = AccountGenerator(seed=42)
        accounts = generator.generate_batch(100)

        def validate_batch():
            for account in accounts:
                _ = account.model_dump()
            return len(accounts)

        result = benchmark(validate_batch)
        assert result == 100
        assert benchmark.stats["mean"] < 0.05


# Benchmark configuration
pytest_benchmark_config = {
    "min_rounds": 5,
    "max_time": 2.0,
    "warmup": True,
    "warmup_iterations": 2,
    "disable_gc": True,
    "timer": "time.perf_counter",
}


def pytest_configure(config):
    """Configure pytest-benchmark."""
    config.addinivalue_line("markers", "benchmark: Performance benchmark tests")


# Made with Bob
