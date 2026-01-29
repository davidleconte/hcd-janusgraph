# Week 3-4: Test Coverage Quick Start Guide

**Date:** 2026-01-29  
**Purpose:** Get started with test coverage improvement immediately  
**Time Required:** 15 minutes to first test results

## TL;DR - Run This Now

```bash
# 1. Ensure you're in the project root
cd /Users/david.leconte/Documents/Work/Demos/hcd-tarball-janusgraph

# 2. Activate environment (already done)
conda activate janusgraph-analysis

# 3. Run unit tests only (no services needed)
pytest tests/unit/ -v --cov=src --cov=banking --cov-report=html --cov-report=term-missing

# 4. View coverage report
open htmlcov/index.html
```

## What Just Happened?

The baseline test run revealed:
- ✅ **177 tests discovered** - test infrastructure is working perfectly
- ✅ **Test dependencies installed** - pytest, pytest-cov, pytest-mock all ready
- ⚠️ **Integration tests failed** - expected, services aren't running
- ✅ **Security tests passed** - tests not requiring services work fine

**This is good news!** The failures are environmental (services not running), not code defects.

## Understanding the Test Results

### Test Categories

#### 1. Unit Tests (✅ Ready to Run)
- **Location:** `tests/unit/`
- **Requirements:** None (no services needed)
- **Current:** ~50 tests in `test_validator.py`
- **Status:** Can run immediately

#### 2. Integration Tests (⚠️ Needs Services)
- **Location:** `tests/integration/`
- **Requirements:** JanusGraph, HCD, Prometheus, Grafana
- **Current:** 22 tests
- **Status:** Will run after services deployed

#### 3. Performance Tests (⚠️ Needs Services + Data)
- **Location:** `tests/performance/`
- **Requirements:** Full stack + initialized data
- **Current:** 7 tests
- **Status:** Will run after data loaded

## Immediate Next Steps

### Step 1: Run Unit Tests (5 minutes)

```bash
# Run existing unit tests
pytest tests/unit/ -v

# Expected output:
# tests/unit/utils/test_validator.py::TestEmailValidator::test_valid_email PASSED
# tests/unit/utils/test_validator.py::TestEmailValidator::test_invalid_email PASSED
# ... (50+ tests)
# ======================== 50+ passed in 2.5s ========================
```

### Step 2: Check Coverage (2 minutes)

```bash
# Generate coverage report
pytest tests/unit/ -v --cov=src --cov=banking --cov-report=html

# Open report
open htmlcov/index.html  # macOS
```

**What to look for:**
- Green lines = covered by tests
- Red lines = not covered
- Yellow lines = partially covered

### Step 3: Identify Gaps (5 minutes)

Look at the coverage report and identify:
1. **Files with 0% coverage** - need tests created
2. **Files with <50% coverage** - need more tests
3. **Critical paths not covered** - prioritize these

### Step 4: Create Your First Test (15 minutes)

Example: Testing JanusGraph client

```bash
# Create test file
mkdir -p tests/unit/client
touch tests/unit/client/test_janusgraph_client.py
```

Add this content:
```python
"""Tests for JanusGraph client"""
import pytest
from unittest.mock import Mock, patch
from src.python.client.janusgraph_client import JanusGraphClient


class TestJanusGraphClient:
    """Test JanusGraph client functionality"""
    
    def test_client_initialization(self):
        """Test client can be initialized"""
        client = JanusGraphClient(host='localhost', port=8182)
        assert client.host == 'localhost'
        assert client.port == 8182
    
    def test_connection_url_format(self):
        """Test connection URL is formatted correctly"""
        client = JanusGraphClient(host='example.com', port=9999)
        expected_url = 'ws://example.com:9999/gremlin'
        assert client.get_connection_url() == expected_url
    
    @patch('src.python.client.janusgraph_client.DriverRemoteConnection')
    def test_connect_success(self, mock_connection):
        """Test successful connection"""
        client = JanusGraphClient()
        result = client.connect()
        assert result is True
        mock_connection.assert_called_once()
    
    @patch('src.python.client.janusgraph_client.DriverRemoteConnection')
    def test_connect_failure(self, mock_connection):
        """Test connection failure handling"""
        mock_connection.side_effect = Exception("Connection refused")
        client = JanusGraphClient()
        result = client.connect()
        assert result is False
```

Run your new test:
```bash
pytest tests/unit/client/test_janusgraph_client.py -v
```

## Development Workflow

### Daily Workflow (Recommended)

```bash
# Morning: Check what needs testing
pytest --collect-only tests/unit/

# During development: Run tests for module you're working on
pytest tests/unit/client/ -v

# Before commit: Run all unit tests
pytest tests/unit/ -v --maxfail=1

# Before push: Run with coverage
pytest tests/unit/ -v --cov=src --cov=banking --cov-report=term-missing
```

### Test-Driven Development (TDD)

1. **Write test first** (it will fail)
2. **Write minimal code** to make it pass
3. **Refactor** while keeping tests green
4. **Repeat**

Example:
```bash
# 1. Write failing test
pytest tests/unit/client/test_new_feature.py -v
# FAILED - function doesn't exist yet

# 2. Implement feature
# ... edit src/python/client/janusgraph_client.py ...

# 3. Run test again
pytest tests/unit/client/test_new_feature.py -v
# PASSED - feature works!

# 4. Check coverage
pytest tests/unit/client/ -v --cov=src.python.client --cov-report=term-missing
```

## Common Test Patterns

### 1. Testing with Mocks
```python
from unittest.mock import Mock, patch

def test_with_mock():
    mock_client = Mock()
    mock_client.query.return_value = [1, 2, 3]
    result = mock_client.query("test")
    assert result == [1, 2, 3]
```

### 2. Testing Exceptions
```python
def test_exception_handling():
    with pytest.raises(ValueError):
        validate_email("invalid")
```

### 3. Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("test@example.com", True),
    ("invalid", False),
    ("", False),
])
def test_email_validation(input, expected):
    assert validate_email(input) == expected
```

### 4. Using Fixtures
```python
@pytest.fixture
def sample_data():
    return {"name": "John", "age": 30}

def test_with_fixture(sample_data):
    assert sample_data["name"] == "John"
```

## Troubleshooting

### Issue: "ModuleNotFoundError"
```bash
# Solution: Ensure project root is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/unit/ -v
```

### Issue: "No tests collected"
```bash
# Solution: Check test file naming
# Test files must start with "test_" or end with "_test.py"
# Test functions must start with "test_"

# Verify test discovery
pytest --collect-only tests/unit/
```

### Issue: "Import errors in tests"
```bash
# Solution: Check conftest.py is adding project root to path
# File: tests/conftest.py, line 18-20
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

### Issue: "Coverage not showing all files"
```bash
# Solution: Specify source directories explicitly
pytest tests/unit/ -v \
  --cov=src/python \
  --cov=banking/data_generators \
  --cov=banking/aml \
  --cov=banking/fraud \
  --cov-report=html
```

## Progress Tracking

### Daily Checklist

- [ ] Run unit tests: `pytest tests/unit/ -v`
- [ ] Check coverage: `pytest tests/unit/ --cov=src --cov=banking --cov-report=term`
- [ ] Create 1-2 new test files
- [ ] Add 10-20 new test cases
- [ ] Review coverage report
- [ ] Update progress in WEEK3-4_TEST_COVERAGE_PLAN.md

### Weekly Goals

**Week 3:**
- [ ] Client module: 80% coverage (Days 1-2)
- [ ] Utils module: 85% coverage (Days 3-4)
- [ ] Integration tests improved (Day 5)

**Week 4:**
- [ ] Data generators: 75% coverage (Days 6-7)
- [ ] AML/Fraud: 70% coverage (Days 8-9)
- [ ] Performance tests (Day 10)

## Resources

### Documentation
- [WEEK3-4_TEST_COVERAGE_PLAN.md](WEEK3-4_TEST_COVERAGE_PLAN.md) - Detailed 10-day plan
- [WEEK3-4_BASELINE_REPORT.md](WEEK3-4_BASELINE_REPORT.md) - Current state analysis
- [WEEK3-4_SUMMARY.md](WEEK3-4_SUMMARY.md) - Executive summary

### Test Examples
- `tests/unit/utils/test_validator.py` - 50+ test examples
- `tests/conftest.py` - Shared fixtures
- `tests/integration/test_full_stack.py` - Integration test patterns

### External Resources
- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)

## Getting Help

### Quick Commands Reference

```bash
# Run specific test file
pytest tests/unit/client/test_janusgraph_client.py -v

# Run specific test class
pytest tests/unit/client/test_janusgraph_client.py::TestJanusGraphClient -v

# Run specific test function
pytest tests/unit/client/test_janusgraph_client.py::TestJanusGraphClient::test_connect -v

# Run tests matching pattern
pytest -k "test_email" -v

# Run with verbose output
pytest -vv

# Run with print statements visible
pytest -s

# Stop on first failure
pytest --maxfail=1

# Show local variables on failure
pytest -l

# Generate coverage report
pytest --cov=src --cov-report=html

# Run only fast tests
pytest -m "not slow" -v
```

## Next Actions

1. **Right now:** Run `pytest tests/unit/ -v` to see current unit tests
2. **Today:** Review coverage report and identify gaps
3. **This week:** Follow Days 1-5 of WEEK3-4_TEST_COVERAGE_PLAN.md
4. **Next week:** Follow Days 6-10 of WEEK3-4_TEST_COVERAGE_PLAN.md

---

**Created:** 2026-01-29  
**Last Updated:** 2026-01-29  
**Status:** Ready for execution
