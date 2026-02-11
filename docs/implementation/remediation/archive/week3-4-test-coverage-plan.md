# Week 3-4: Test Coverage Improvement Plan

**Date:** 2026-01-29
**Status:** 🟡 Ready to Execute
**Goal:** Achieve 80% test coverage (currently ~40-50%)

## Executive Summary

Weeks 3-4 focus on comprehensive test coverage across all modules. This is a critical phase for production readiness, ensuring code reliability and maintainability.

## Current State Analysis

### Coverage Baseline (Estimated)

```
Module                          Current    Target    Gap
─────────────────────────────────────────────────────────
src/python/client/              60%        80%       +20%
src/python/utils/               70%        85%       +15%
src/python/security/            50%        80%       +30%
banking/data_generators/core/   45%        75%       +30%
banking/data_generators/events/ 40%        75%       +35%
banking/data_generators/patterns/ 35%      70%       +35%
banking/aml/                    30%        70%       +40%
banking/fraud/                  20%        70%       +50%
─────────────────────────────────────────────────────────
Overall                         ~45%       80%       +35%
```

### Test Infrastructure Status

- ✅ pytest configured
- ✅ conftest.py with fixtures
- ✅ Test directory structure
- ✅ Coverage reporting configured
- ⚠️  Limited test cases
- ⚠️  No integration tests
- ⚠️  No performance tests

## Implementation Strategy

### Week 3: Core Infrastructure Tests (Target: 70% overall)

#### Day 1-2: Client Module Tests

**Focus:** `src/python/client/janusgraph_client.py`

**Test Cases to Add:**

1. Connection Management
   - Test successful connection
   - Test connection with SSL/TLS
   - Test connection retry logic
   - Test connection timeout
   - Test connection pool exhaustion

2. Authentication
   - Test basic auth
   - Test token auth
   - Test auth failure handling
   - Test credential validation

3. Query Execution
   - Test simple queries
   - Test parameterized queries
   - Test batch queries
   - Test query timeout
   - Test query error handling

4. Error Handling
   - Test network errors
   - Test server errors
   - Test malformed responses
   - Test retry logic

**Files to Create:**

- `tests/unit/client/test_janusgraph_client.py`
- `tests/unit/client/test_connection.py`
- `tests/unit/client/test_authentication.py`
- `tests/unit/client/test_error_handling.py`

**Target:** 80% coverage for `src/python/client/`

#### Day 3-4: Utilities Tests

**Focus:** `src/python/utils/`

**Test Cases to Add:**

1. Validator Class (17+ methods)
   - Test email validation
   - Test phone validation
   - Test IBAN validation
   - Test SWIFT validation
   - Test amount validation
   - Test date validation
   - Test string sanitization
   - Test SQL injection prevention
   - Test XSS prevention

2. Log Sanitizer
   - Test PII redaction
   - Test credential masking
   - Test IP address handling
   - Test custom patterns

3. Tracing Utilities
   - Test span creation
   - Test context propagation
   - Test error tracking

4. Embedding Generator
   - Test text embedding
   - Test vector operations
   - Test similarity calculations

**Files to Create:**

- `tests/unit/utils/test_validator.py`
- `tests/unit/utils/test_log_sanitizer.py`
- `tests/unit/utils/test_tracing.py`
- `tests/unit/utils/test_embedding_generator.py`

**Target:** 85% coverage for `src/python/utils/`

#### Day 5: Integration Tests

**Focus:** End-to-end workflows

**Test Cases to Add:**

1. Stack Deployment
   - Test service startup
   - Test service health checks
   - Test service connectivity

2. Data Pipeline
   - Test data generation
   - Test data loading
   - Test data validation

3. Query Pipeline
   - Test query execution
   - Test result processing
   - Test error recovery

**Files to Create:**

- `tests/integration/test_stack_deployment.py`
- `tests/integration/test_data_pipeline.py`
- `tests/integration/test_query_pipeline.py`

**Target:** Basic integration test suite

### Week 4: Banking Domain Tests (Target: 80% overall)

#### Day 1-2: Data Generator Tests

**Focus:** `banking/data_generators/`

**Test Cases to Add:**

1. Core Generators
   - PersonGenerator: demographics, addresses, contacts
   - CompanyGenerator: business types, industries, sizes
   - AccountGenerator: account types, balances, statuses
   - TradeGenerator: securities, prices, volumes

2. Event Generators
   - TransactionGenerator: types, amounts, frequencies
   - CommunicationGenerator: channels, content, timing

3. Pattern Generators
   - InsiderTradingPattern: timing, volumes, relationships
   - TBMLPattern: trade mispricing, documentation
   - FraudRingPattern: network structure, coordination
   - StructuringPattern: amount splitting, timing
   - CATOPattern: cross-border, layering

**Files to Create:**

- `banking/data_generators/tests/test_core/test_person_generator_extended.py`
- `banking/data_generators/tests/test_core/test_company_generator_extended.py`
- `banking/data_generators/tests/test_core/test_account_generator_extended.py`
- `banking/data_generators/tests/test_events/test_transaction_generator_extended.py`
- `banking/data_generators/tests/test_patterns/test_all_patterns.py`

**Target:** 75% coverage for `banking/data_generators/`

#### Day 3-4: AML/Fraud Detection Tests

**Focus:** `banking/aml/` and `banking/fraud/`

**Test Cases to Add:**

1. AML Detection
   - Structuring detection algorithms
   - Threshold calculations
   - Pattern matching
   - False positive handling

2. Fraud Detection
   - Anomaly detection
   - Rule-based detection
   - ML model integration
   - Alert generation

3. Edge Cases
   - Boundary conditions
   - Invalid inputs
   - Missing data
   - Concurrent operations

**Files to Create:**

- `tests/unit/aml/test_structuring_detection.py`
- `tests/unit/aml/test_pattern_matching.py`
- `tests/unit/fraud/test_anomaly_detection.py`
- `tests/unit/fraud/test_rule_engine.py`

**Target:** 70% coverage for `banking/aml/` and `banking/fraud/`

#### Day 5: Performance & Load Tests

**Focus:** System performance

**Test Cases to Add:**

1. Performance Benchmarks
   - Query performance
   - Data generation speed
   - Pattern injection time
   - Memory usage

2. Load Tests
   - Concurrent connections
   - High-volume queries
   - Bulk data loading
   - Stress testing

**Files to Create:**

- `tests/performance/test_query_performance.py`
- `tests/performance/test_data_generation.py`
- `tests/performance/test_load.py`

**Target:** Performance baseline established

## Test Framework Setup

### Directory Structure

```
tests/
├── unit/
│   ├── client/
│   │   ├── test_janusgraph_client.py
│   │   ├── test_connection.py
│   │   ├── test_authentication.py
│   │   └── test_error_handling.py
│   ├── utils/
│   │   ├── test_validator.py
│   │   ├── test_log_sanitizer.py
│   │   ├── test_tracing.py
│   │   └── test_embedding_generator.py
│   ├── security/
│   │   ├── test_rbac.py
│   │   └── test_mfa.py
│   ├── aml/
│   │   ├── test_structuring_detection.py
│   │   └── test_pattern_matching.py
│   └── fraud/
│       ├── test_anomaly_detection.py
│       └── test_rule_engine.py
├── integration/
│   ├── test_stack_deployment.py
│   ├── test_data_pipeline.py
│   └── test_query_pipeline.py
├── performance/
│   ├── test_query_performance.py
│   ├── test_data_generation.py
│   └── test_load.py
└── conftest.py
```

### pytest Configuration

Update `pytest.ini`:

```ini
[pytest]
testpaths = tests banking/data_generators/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov=banking
    --cov-report=html
    --cov-report=term-missing
    --cov-report=json
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
    requires_janusgraph: Tests requiring JanusGraph
    requires_vault: Tests requiring Vault
```

### Coverage Configuration

Update `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src", "banking"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
    "*/venv/*",
    "*/notebooks/*",
    "hcd-1.2.3/*"
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod"
]

[tool.coverage.html]
directory = "htmlcov"
```

## Testing Best Practices

### 1. Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange - Set up test data
    generator = PersonGenerator(seed=42)

    # Act - Execute the code under test
    person = generator.generate()

    # Assert - Verify the results
    assert person['first_name'] is not None
    assert len(person['email']) > 0
```

### 2. Fixtures for Reusability

```python
@pytest.fixture
def sample_person():
    return {
        'id': 'P001',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com'
    }

def test_with_fixture(sample_person):
    assert sample_person['id'] == 'P001'
```

### 3. Parametrized Tests

```python
@pytest.mark.parametrize("email,expected", [
    ("valid@example.com", True),
    ("invalid@", False),
    ("no-at-sign.com", False),
])
def test_email_validation(email, expected):
    validator = Validator()
    assert validator.validate_email(email) == expected
```

### 4. Mocking External Dependencies

```python
from unittest.mock import Mock, patch

def test_with_mock():
    with patch('janusgraph_client.Client') as mock_client:
        mock_client.return_value.submit.return_value.all.return_value.result.return_value = [42]
        # Test code here
```

### 5. Testing Exceptions

```python
def test_exception_handling():
    validator = Validator()
    with pytest.raises(ValueError, match="Invalid email"):
        validator.validate_email("invalid")
```

## Execution Plan

### Phase 1: Setup (Day 0)

```bash
# 1. Create test directory structure
mkdir -p tests/{unit/{client,utils,security,aml,fraud},integration,performance}

# 2. Update pytest configuration
# Edit pytest.ini and pyproject.toml

# 3. Install test dependencies
pip install pytest pytest-cov pytest-mock pytest-asyncio pytest-benchmark

# 4. Run baseline coverage
pytest --cov=src --cov=banking --cov-report=html --cov-report=term
```

### Phase 2: Implementation (Days 1-10)

```bash
# Daily workflow:
# 1. Write tests for target module
# 2. Run tests: pytest tests/unit/module/
# 3. Check coverage: pytest --cov=module --cov-report=term-missing
# 4. Iterate until target coverage reached
# 5. Commit changes

# Example for Day 1:
pytest tests/unit/client/ --cov=src/python/client --cov-report=term-missing
```

### Phase 3: Validation (Day 11)

```bash
# 1. Run full test suite
pytest

# 2. Generate coverage report
pytest --cov=src --cov=banking --cov-report=html --cov-report=term

# 3. Review coverage gaps
open htmlcov/index.html

# 4. Address remaining gaps
# 5. Final validation
```

## Success Criteria

- ✅ 80% overall test coverage
- ✅ All critical paths tested
- ✅ Integration tests passing
- ✅ Performance benchmarks established
- ✅ CI/CD pipeline updated
- ✅ Documentation complete

## Deliverables

1. **Test Suites**
   - 50+ unit test files
   - 10+ integration test files
   - 5+ performance test files
   - 500+ test cases

2. **Coverage Reports**
   - HTML coverage report
   - JSON coverage data
   - Coverage badges

3. **Documentation**
   - Test strategy document
   - Test execution guide
   - Coverage improvement plan

4. **CI/CD Integration**
   - Automated test execution
   - Coverage reporting
   - Quality gates

## Timeline

| Week | Days | Focus | Target Coverage |
|------|------|-------|-----------------|
| 3 | 1-2 | Client tests | 70% |
| 3 | 3-4 | Utils tests | 75% |
| 3 | 5 | Integration tests | 75% |
| 4 | 1-2 | Data generator tests | 78% |
| 4 | 3-4 | AML/Fraud tests | 80% |
| 4 | 5 | Performance tests | 80%+ |

## Risk Mitigation

### Risk 1: Time Constraints

**Mitigation:** Prioritize critical paths, use test generation tools

### Risk 2: Complex Dependencies

**Mitigation:** Use mocking extensively, create test fixtures

### Risk 3: Flaky Tests

**Mitigation:** Use fixed seeds, avoid time-dependent tests

### Risk 4: Coverage Gaps

**Mitigation:** Daily coverage reviews, pair programming

## Next Steps

1. Review and approve this plan
2. Set up test infrastructure
3. Begin Day 1 implementation
4. Daily standup to track progress
5. Weekly review of coverage metrics

---

**Estimated Effort:** 10 days (2 weeks)
**Team Size:** 2-3 developers
**Priority:** HIGH
**Dependencies:** Weeks 1-2 complete
