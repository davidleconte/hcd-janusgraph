# Data Generators Test Suite

Comprehensive testing framework for the synthetic data generation system.

## Overview

This test suite provides extensive coverage for all data generator components including:

- **Unit Tests**: Individual generator testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Benchmarks**: Speed and scalability testing
- **Data Quality Validation**: Statistical and referential integrity testing

## Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and fixtures
├── requirements-test.txt          # Test dependencies
├── run_tests.sh                   # Test runner script
├── README.md                      # This file
├── test_core/                     # Core generator tests
│   ├── test_person_generator.py
│   ├── test_company_generator.py
│   └── test_account_generator.py
├── test_events/                   # Event generator tests
│   ├── test_transaction_generator.py
│   ├── test_communication_generator.py
│   └── test_trade_generator.py
├── test_patterns/                 # Pattern generator tests
│   ├── test_insider_trading_pattern.py
│   ├── test_tbml_pattern.py
│   └── test_fraud_ring_pattern.py
├── test_orchestration/            # Orchestration tests
│   └── test_master_orchestrator.py
├── test_integration/              # Integration tests
│   ├── test_janusgraph_integration.py
│   ├── test_opensearch_integration.py
│   └── test_end_to_end.py
└── test_performance/              # Performance benchmarks
    └── test_benchmarks.py
```

## Installation

Install test dependencies:

```bash
pip install -r tests/requirements-test.txt
```

Or using uv:

```bash
uv pip install -r tests/requirements-test.txt
```

## Running Tests

### Quick Start

Run all fast tests (excludes slow, integration, and benchmark tests):

```bash
cd banking/data_generators/tests
./run_tests.sh fast
```

### Test Categories

**Smoke Tests** (quick validation):
```bash
./run_tests.sh smoke
```

**Unit Tests** (all unit tests):
```bash
./run_tests.sh unit
```

**Integration Tests** (requires running services):
```bash
./run_tests.sh integration
```

**Performance Benchmarks**:
```bash
./run_tests.sh performance
```

**All Tests**:
```bash
./run_tests.sh all
```

**With Coverage Report**:
```bash
./run_tests.sh coverage
```

### Verbose Output

Add `-v` or `--verbose` for detailed output:

```bash
./run_tests.sh unit -v
```

### Direct Pytest Usage

Run specific test files:
```bash
pytest test_core/test_person_generator.py -v
```

Run specific test classes:
```bash
pytest test_core/test_person_generator.py::TestPersonGeneratorFunctional -v
```

Run specific test methods:
```bash
pytest test_core/test_person_generator.py::TestPersonGeneratorFunctional::test_required_fields_present -v
```

Run tests by marker:
```bash
pytest -m "not slow"              # Exclude slow tests
pytest -m "benchmark"             # Only benchmark tests
pytest -m "integration"           # Only integration tests
```

## Test Markers

Tests are marked with the following pytest markers:

- `@pytest.mark.slow` - Tests that take significant time (>1 second)
- `@pytest.mark.integration` - Tests requiring external services
- `@pytest.mark.benchmark` - Performance benchmark tests

## Fixtures

Common fixtures available in all tests (defined in `conftest.py`):

### Generator Fixtures
- `person_generator` - PersonGenerator instance
- `company_generator` - CompanyGenerator instance
- `account_generator` - AccountGenerator instance
- `transaction_generator` - TransactionGenerator instance
- `communication_generator` - CommunicationGenerator instance
- `trade_generator` - TradeGenerator instance
- `travel_generator` - TravelGenerator instance
- `document_generator` - DocumentGenerator instance

### Entity Fixtures
- `sample_person` - Single generated person
- `sample_persons` - List of 10 persons
- `sample_company` - Single generated company
- `sample_companies` - List of 5 companies
- `sample_account` - Single generated account
- `sample_accounts` - List of 10 accounts
- `sample_transaction` - Single generated transaction
- `sample_transactions` - List of 20 transactions

### Orchestrator Fixtures
- `small_orchestrator` - Orchestrator with small config (10/5/20 entities)
- `medium_orchestrator` - Orchestrator with medium config (100/50/200 entities)

## Test Coverage

Target coverage: **>90%** across all modules

Generate coverage report:
```bash
./run_tests.sh coverage
```

View HTML coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Writing Tests

### Test Class Structure

```python
import pytest

class TestMyGeneratorSmoke:
    """Smoke tests - basic functionality"""
    
    def test_initialization(self, my_generator):
        assert my_generator is not None

class TestMyGeneratorFunctional:
    """Functional tests - correct behavior"""
    
    def test_required_fields(self, sample_entity):
        assert sample_entity.id
        assert sample_entity.name

class TestMyGeneratorEdgeCases:
    """Edge case tests"""
    
    def test_boundary_conditions(self, my_generator):
        # Test edge cases
        pass

class TestMyGeneratorPerformance:
    """Performance tests"""
    
    @pytest.mark.benchmark
    def test_generation_speed(self, my_generator, benchmark):
        result = benchmark(my_generator.generate)
        assert result is not None
```

### Using Fixtures

```python
def test_with_fixtures(self, person_generator, sample_accounts):
    """Test using multiple fixtures"""
    person = person_generator.generate()
    account = sample_accounts[0]
    
    assert person.person_id
    assert account.account_id
```

### Marking Tests

```python
@pytest.mark.slow
def test_large_batch(self):
    """This test takes a long time"""
    pass

@pytest.mark.integration
def test_database_connection(self):
    """This test requires external services"""
    pass

@pytest.mark.benchmark
def test_performance(self, benchmark):
    """This is a performance benchmark"""
    pass
```

## Performance Benchmarks

### Benchmark Results Format

Benchmarks output detailed statistics:

```
Name (time in ms)                Min      Max     Mean   StdDev
test_person_generation         1.234    2.345    1.567    0.123
test_transaction_generation    0.456    1.234    0.789    0.089
```

### Throughput Tests

Throughput tests measure entities/second:

```
Person throughput: 1234 entities/sec
Transaction throughput: 5678 entities/sec
End-to-end throughput: 2345 entities/sec
```

### Scalability Tests

Scalability tests measure performance at different scales:

- **Small scale**: 100 entities
- **Medium scale**: 1,000 entities
- **Large scale**: 10,000 entities

## Integration Tests

Integration tests require running services:

### Prerequisites

1. **JanusGraph**: Running on localhost:8182
2. **OpenSearch**: Running on localhost:9200

### Running Integration Tests

```bash
# Start services first
docker-compose up -d

# Run integration tests
./run_tests.sh integration

# Stop services
docker-compose down
```

### Skipping Integration Tests

Integration tests are automatically skipped if services are not available:

```python
@pytest.mark.integration
def test_janusgraph_connection(self):
    pytest.skip("Requires running JanusGraph instance")
```

## Data Quality Validation

### Referential Integrity

Tests verify that all foreign key relationships are valid:

```python
def test_referential_integrity(self):
    # Verify accounts reference valid persons/companies
    # Verify transactions reference valid accounts
    pass
```

### Statistical Validation

Tests verify statistical properties of generated data:

```python
def test_age_distribution(self):
    # Verify age distribution is realistic
    assert 30 <= avg_age <= 60
```

### Uniqueness Validation

Tests verify ID uniqueness:

```python
def test_unique_ids(self):
    # Verify all IDs are unique
    assert len(ids) == len(set(ids))
```

## Continuous Integration

### GitHub Actions

Example workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
      - name: Run tests
        run: |
          cd banking/data_generators/tests
          ./run_tests.sh fast
      - name: Generate coverage
        run: |
          cd banking/data_generators/tests
          ./run_tests.sh coverage
```

## Troubleshooting

### Common Issues

**Import errors**:
```bash
# Ensure package is installed in development mode
pip install -e .
```

**Fixture not found**:
```bash
# Ensure conftest.py is in the tests directory
# Check fixture name spelling
```

**Slow tests timing out**:
```bash
# Increase timeout
pytest --timeout=300
```

**Integration tests failing**:
```bash
# Check services are running
docker-compose ps

# Check service logs
docker-compose logs janusgraph
docker-compose logs opensearch
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Fast Tests**: Keep unit tests fast (<100ms)
3. **Clear Names**: Use descriptive test names
4. **Arrange-Act-Assert**: Follow AAA pattern
5. **Use Fixtures**: Reuse common setup code
6. **Mark Appropriately**: Use markers for slow/integration tests
7. **Test Edge Cases**: Include boundary conditions
8. **Document Tests**: Add docstrings explaining what is tested

## Contributing

When adding new generators or features:

1. Add corresponding test file in appropriate directory
2. Include smoke, functional, edge case, and performance tests
3. Use existing fixtures where possible
4. Add new fixtures to `conftest.py` if needed
5. Update this README with new test categories
6. Ensure coverage remains >90%

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/mark.html)
- [Pytest Benchmark](https://pytest-benchmark.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)