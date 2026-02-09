"""
Performance Benchmarks
======================

Performance benchmarks for data generation including:
- Generation speed tests
- Scalability tests
- Memory profiling
- Throughput tests

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import sys
import time

import pytest


@pytest.mark.benchmark
class TestGenerationSpeed:
    """Generation speed benchmarks"""

    def test_person_generation_speed(self, person_generator, benchmark):
        """Benchmark person generation speed"""
        result = benchmark(person_generator.generate)
        assert result is not None

    def test_company_generation_speed(self, company_generator, benchmark):
        """Benchmark company generation speed"""
        result = benchmark(company_generator.generate)
        assert result is not None

    def test_account_generation_speed(self, account_generator, sample_person, benchmark):
        """Benchmark account generation speed"""
        result = benchmark(account_generator.generate, owner=sample_person)
        assert result is not None

    def test_transaction_generation_speed(self, transaction_generator, sample_accounts, benchmark):
        """Benchmark transaction generation speed"""
        result = benchmark(
            transaction_generator.generate,
            from_account=sample_accounts[0],
            to_account=sample_accounts[1],
        )
        assert result is not None


@pytest.mark.slow
class TestScalability:
    """Scalability tests"""

    def test_small_scale_generation(self):
        """Test generation at small scale (100 entities)"""
        from banking.data_generators.orchestration import GenerationConfig, MasterOrchestrator

        config = GenerationConfig(
            seed=42, person_count=50, company_count=25, account_count=100, transaction_count=500
        )

        orchestrator = MasterOrchestrator(config)

        start = time.time()
        stats = orchestrator.generate_all()
        duration = time.time() - start

        # Should complete quickly
        assert duration < 2.0
        assert stats.persons_generated == 50

        # Calculate throughput
        entities_per_sec = (50 + 25 + 100) / duration
        print(f"\nSmall scale: {entities_per_sec:.0f} entities/sec")

    def test_medium_scale_generation(self):
        """Test generation at medium scale (1000 entities)"""
        from banking.data_generators.orchestration import GenerationConfig, MasterOrchestrator

        config = GenerationConfig(
            seed=42, person_count=500, company_count=250, account_count=1000, transaction_count=5000
        )

        orchestrator = MasterOrchestrator(config)

        start = time.time()
        stats = orchestrator.generate_all()
        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 10.0
        assert stats.persons_generated == 500

        # Calculate throughput
        entities_per_sec = (500 + 250 + 1000) / duration
        print(f"\nMedium scale: {entities_per_sec:.0f} entities/sec")

    def test_large_scale_generation(self):
        """Test generation at large scale (10000 entities)"""
        from banking.data_generators.orchestration import GenerationConfig, MasterOrchestrator

        config = GenerationConfig(
            seed=42,
            person_count=5000,
            company_count=2500,
            account_count=10000,
            transaction_count=50000,
        )

        orchestrator = MasterOrchestrator(config)

        start = time.time()
        stats = orchestrator.generate_all()
        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 60.0  # Less than 1 minute
        assert stats.persons_generated == 5000

        # Calculate throughput
        entities_per_sec = (5000 + 2500 + 10000) / duration
        print(f"\nLarge scale: {entities_per_sec:.0f} entities/sec")


@pytest.mark.slow
class TestMemoryProfiling:
    """Memory profiling tests"""

    def test_person_memory_usage(self, person_generator):
        """Test memory usage for person generation"""
        persons = [person_generator.generate() for _ in range(1000)]

        total_size = sum(sys.getsizeof(p) for p in persons)
        avg_size = total_size / len(persons)

        print(f"\nAverage person size: {avg_size:.0f} bytes")
        assert avg_size < 10000  # Less than 10KB per person

    def test_transaction_memory_usage(self, transaction_generator, sample_accounts):
        """Test memory usage for transaction generation"""
        transactions = [
            transaction_generator.generate(
                from_account=sample_accounts[0], to_account=sample_accounts[1]
            )
            for _ in range(1000)
        ]

        total_size = sum(sys.getsizeof(t) for t in transactions)
        avg_size = total_size / len(transactions)

        print(f"\nAverage transaction size: {avg_size:.0f} bytes")
        assert avg_size < 5000  # Less than 5KB per transaction

    def test_orchestrator_memory_efficiency(self):
        """Test orchestrator memory efficiency"""
        from banking.data_generators.orchestration import GenerationConfig, MasterOrchestrator

        config = GenerationConfig(
            seed=42,
            person_count=1000,
            company_count=500,
            account_count=2000,
            transaction_count=10000,
        )

        orchestrator = MasterOrchestrator(config)
        orchestrator.generate_all()

        # Check orchestrator size
        orch_size = sys.getsizeof(orchestrator)
        print(f"\nOrchestrator size: {orch_size / 1024 / 1024:.2f} MB")

        # Should not hold excessive memory
        assert orch_size < 100_000_000  # Less than 100MB


@pytest.mark.benchmark
class TestThroughput:
    """Throughput tests"""

    def test_person_throughput(self, person_generator):
        """Test person generation throughput"""
        count = 1000

        start = time.time()
        [person_generator.generate() for _ in range(count)]
        duration = time.time() - start

        throughput = count / duration
        print(f"\nPerson throughput: {throughput:.0f} entities/sec")

        # Should generate at least 500 persons/second
        assert throughput > 500

    def test_transaction_throughput(self, transaction_generator, sample_accounts):
        """Test transaction generation throughput"""
        count = 10000

        start = time.time()
        [
            transaction_generator.generate(
                from_account=sample_accounts[0], to_account=sample_accounts[1]
            )
            for _ in range(count)
        ]
        duration = time.time() - start

        throughput = count / duration
        print(f"\nTransaction throughput: {throughput:.0f} entities/sec")

        # Should generate at least 2000 transactions/second
        assert throughput > 2000

    def test_end_to_end_throughput(self):
        """Test end-to-end generation throughput"""
        from banking.data_generators.orchestration import GenerationConfig, MasterOrchestrator

        config = GenerationConfig(
            seed=42,
            person_count=1000,
            company_count=500,
            account_count=2000,
            transaction_count=10000,
        )

        orchestrator = MasterOrchestrator(config)

        start = time.time()
        stats = orchestrator.generate_all()
        duration = time.time() - start

        total_entities = (
            stats.persons_generated
            + stats.companies_generated
            + stats.accounts_generated
            + stats.transactions_generated
        )

        throughput = total_entities / duration
        print(f"\nEnd-to-end throughput: {throughput:.0f} entities/sec")

        # Should generate at least 1000 entities/second overall
        assert throughput > 1000


@pytest.mark.benchmark
class TestPatternInjectionPerformance:
    """Pattern injection performance tests"""

    def test_insider_trading_pattern_performance(self):
        """Test insider trading pattern injection performance"""
        from banking.data_generators.orchestration import GenerationConfig, MasterOrchestrator

        config = GenerationConfig(
            seed=42,
            person_count=100,
            company_count=50,
            account_count=200,
            transaction_count=1000,
            insider_trading_patterns=5,
        )

        orchestrator = MasterOrchestrator(config)

        start = time.time()
        orchestrator.generate_all()
        duration = time.time() - start

        print(f"\nInsider trading pattern injection: {duration:.2f}s")

        # Should complete quickly even with patterns
        assert duration < 5.0

    def test_multiple_patterns_performance(self):
        """Test multiple pattern types performance"""
        from banking.data_generators.orchestration import GenerationConfig, MasterOrchestrator

        config = GenerationConfig(
            seed=42,
            person_count=200,
            company_count=100,
            account_count=400,
            transaction_count=2000,
            insider_trading_patterns=2,
            tbml_patterns=2,
            fraud_ring_patterns=2,
            structuring_patterns=2,
            cato_patterns=2,
        )

        orchestrator = MasterOrchestrator(config)

        start = time.time()
        orchestrator.generate_all()
        duration = time.time() - start

        print(f"\nMultiple patterns injection: {duration:.2f}s")

        # Should complete in reasonable time
        assert duration < 10.0
