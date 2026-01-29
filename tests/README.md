# Tests Directory

This directory contains automated tests for the HCD + JanusGraph banking compliance system, including unit tests, integration tests, and performance tests.

**Date:** 2026-01-28  
**Version:** 1.0  
**Status:** Active

## Directory Structure

```
tests/
├── __init__.py          # Package initialization
├── fixtures/            # Test fixtures and sample data
├── unit/                # Unit tests for individual components
├── integration/         # Integration tests for full stack
└── performance/         # Performance and load tests
```

## Test Categories

### Unit Tests (`unit/`)

Tests for individual components in isolation.

#### [`test_connection.py`](unit/test_connection.py)
- **Purpose:** Test database connection handling
- **Coverage:** Connection pooling, error handling, retries
- **Dependencies:** Mock JanusGraph server
- **Run:** `pytest tests/unit/test_connection.py -v`

#### [`test_graph.py`](unit/test_graph.py)
- **Purpose:** Test graph operations
- **Coverage:** Vertex/edge creation, queries, traversals
- **Dependencies:** In-memory graph or test database
- **Run:** `pytest tests/unit/test_graph.py -v`

#### [`test_janusgraph_client_enhanced.py`](unit/test_janusgraph_client_enhanced.py)
- **Purpose:** Test enhanced JanusGraph client functionality
- **Coverage:** Advanced queries, batch operations, error handling
- **Dependencies:** Mock client or test database
- **Run:** `pytest tests/unit/test_janusgraph_client_enhanced.py -v`

#### [`test_validation.py`](unit/test_validation.py)
- **Purpose:** Test data validation functions
- **Coverage:** Input validation, schema validation, constraint checking
- **Dependencies:** None (pure functions)
- **Run:** `pytest tests/unit/test_validation.py -v`

### Integration Tests (`integration/`)

Tests for complete system integration and workflows.

#### [`test_full_stack.py`](integration/test_full_stack.py)
- **Purpose:** Test complete stack deployment and functionality
- **Coverage:** All services, end-to-end workflows, data flow
- **Dependencies:** Full stack must be running
- **Run:** `pytest tests/integration/test_full_stack.py -v`
- **Duration:** ~5-10 minutes

#### [`test_janusgraph_client.py`](integration/test_janusgraph_client.py)
- **Purpose:** Test JanusGraph client against live database
- **Coverage:** Real database operations, schema management, queries
- **Dependencies:** JanusGraph and HCD running
- **Run:** `pytest tests/integration/test_janusgraph_client.py -v`

#### [`requirements.txt`](integration/requirements.txt)
- **Purpose:** Integration test dependencies
- **Contents:** pytest, gremlinpython, requests, etc.

### Performance Tests (`performance/`)

Tests for system performance and scalability.

#### [`test_load.py`](performance/test_load.py)
- **Purpose:** Load testing and performance benchmarks
- **Coverage:** Query performance, throughput, concurrent operations
- **Dependencies:** Full stack running, test data loaded
- **Run:** `pytest tests/performance/test_load.py -v`
- **Metrics:** Response time, throughput, resource usage

### Test Fixtures (`fixtures/`)

Reusable test data and configurations.

- Sample graph data
- Mock objects
- Test configurations
- Shared utilities

## Running Tests

### Prerequisites

1. **Install test dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   pip install -r tests/integration/requirements.txt
   ```

2. **For integration tests, start the stack:**
   ```bash
   cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
   ```

### Run All Tests

```bash
# From project root
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov=banking --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Performance tests only
pytest tests/performance/ -v
```

### Run Specific Test Files

```bash
# Single test file
pytest tests/unit/test_connection.py -v

# Single test class
pytest tests/unit/test_connection.py::TestConnection -v

# Single test method
pytest tests/unit/test_connection.py::TestConnection::test_connect -v
```

### Using Test Scripts

```bash
# Run all tests via script
./scripts/testing/run_tests.sh all

# Run specific category
./scripts/testing/run_tests.sh unit
./scripts/testing/run_tests.sh integration
./scripts/testing/run_tests.sh performance

# Run integration tests only
./scripts/testing/run_integration_tests.sh
```

## Test Configuration

### pytest Configuration

Configuration in [`pytest.ini`](../pytest.ini):
- Test discovery patterns
- Coverage settings
- Markers for test categorization
- Output formatting

### Environment Variables

Tests use environment variables for configuration:

```bash
# JanusGraph connection
JANUSGRAPH_HOST=localhost
JANUSGRAPH_PORT=8182

# OpenSearch connection
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200

# Test database
TEST_DB_NAME=test_graph
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.performance   # Performance test
@pytest.mark.slow          # Slow-running test
@pytest.mark.requires_db   # Requires database
```

Run tests by marker:
```bash
pytest -m unit              # Run only unit tests
pytest -m "not slow"        # Skip slow tests
pytest -m "integration and not slow"  # Integration tests, skip slow
```

## Writing Tests

### Test Structure

```python
import pytest
from banking.module import function_to_test

class TestFeature:
    """Test suite for feature."""
    
    @pytest.fixture
    def setup_data(self):
        """Fixture to set up test data."""
        # Setup code
        data = create_test_data()
        yield data
        # Teardown code
        cleanup_test_data(data)
    
    def test_basic_functionality(self, setup_data):
        """Test basic functionality."""
        result = function_to_test(setup_data)
        assert result == expected_value
    
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
```

### Best Practices

1. **Test Naming:** Use descriptive names starting with `test_`
2. **Isolation:** Each test should be independent
3. **Fixtures:** Use fixtures for setup/teardown
4. **Assertions:** Use clear, specific assertions
5. **Documentation:** Add docstrings explaining test purpose
6. **Coverage:** Aim for >80% code coverage
7. **Performance:** Keep unit tests fast (<1s each)

### Example Unit Test

```python
import pytest
from banking.aml.sanctions import SanctionsScreener

class TestSanctionsScreener:
    """Test sanctions screening functionality."""
    
    @pytest.fixture
    def screener(self):
        """Create screener instance."""
        return SanctionsScreener()
    
    def test_exact_match(self, screener):
        """Test exact name match detection."""
        result = screener.screen("John Doe")
        assert result.is_match is True
        assert result.confidence > 0.95
    
    def test_fuzzy_match(self, screener):
        """Test fuzzy name matching."""
        result = screener.screen("Jon Doe")
        assert result.is_match is True
        assert 0.8 < result.confidence < 0.95
    
    def test_no_match(self, screener):
        """Test non-matching name."""
        result = screener.screen("Jane Smith")
        assert result.is_match is False
```

### Example Integration Test

```python
import pytest
from banking.client import JanusGraphClient

@pytest.mark.integration
class TestJanusGraphIntegration:
    """Integration tests for JanusGraph."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Create client connected to test database."""
        client = JanusGraphClient(
            host="localhost",
            port=8182
        )
        yield client
        client.close()
    
    def test_create_vertex(self, client):
        """Test vertex creation."""
        vertex = client.add_vertex("person", {
            "name": "Test User",
            "email": "test@example.com"
        })
        assert vertex.id is not None
        assert vertex.label == "person"
    
    def test_query_vertex(self, client):
        """Test vertex query."""
        results = client.query(
            "g.V().hasLabel('person').has('name', 'Test User')"
        )
        assert len(results) > 0
```

## Test Coverage

### Viewing Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov=banking --cov-report=html

# Open report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Goals

- **Overall:** >80% code coverage
- **Critical modules:** >90% coverage
  - Authentication/authorization
  - Data validation
  - Security functions
- **Business logic:** >85% coverage
  - AML detection
  - Fraud detection
  - Sanctions screening

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Pull requests
- Commits to main branch
- Scheduled daily runs

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pre-commit install
```

Hooks run:
- Linting (flake8, black)
- Type checking (mypy)
- Unit tests (fast tests only)

## Troubleshooting

### Common Issues

**Tests Fail with Connection Error**
```bash
# Check if services are running
docker ps

# Start services if needed
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
```

**Import Errors**
```bash
# Install package in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Slow Tests**
```bash
# Skip slow tests
pytest -m "not slow"

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

**Flaky Tests**
```bash
# Rerun failed tests
pytest --lf  # Last failed

# Rerun failed tests multiple times
pytest --reruns 3
```

### Debug Mode

```bash
# Run with verbose output
pytest -vv

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l
```

## Performance Benchmarks

### Expected Performance

- **Unit tests:** <1s per test
- **Integration tests:** 1-10s per test
- **Full test suite:** <5 minutes
- **Performance tests:** 5-30 minutes

### Optimization Tips

1. Use fixtures with appropriate scope
2. Mock external dependencies in unit tests
3. Use in-memory databases when possible
4. Run tests in parallel
5. Skip slow tests during development

## Related Documentation

- [Testing Guide](../docs/TESTING.md)
- [Development Guide](../docs/CONTRIBUTING.md)
- [CI/CD Documentation](../.github/workflows/README.md)
- [Code Quality Standards](../docs/DOCUMENTATION_STANDARDS.md)

## Contributing

When adding new tests:

1. Place in appropriate directory (unit/integration/performance)
2. Follow naming conventions
3. Add docstrings
4. Use appropriate markers
5. Update this README if adding new test categories
6. Ensure tests pass locally before committing
7. Maintain or improve code coverage

## Support

For testing issues:
- Check [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
- Review test output and logs
- Check service status with `docker ps`
- Consult [Documentation Index](../docs/INDEX.md)