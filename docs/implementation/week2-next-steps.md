# Week 2 Implementation: Next Steps

**Date:** 2026-02-11  
**Status:** Days 6-7 Complete, Days 8-12 Ready for Implementation  
**Current Coverage:** Analytics 31%, Streaming 28%  
**Target Coverage:** 80%+ for both modules

---

## 🎯 Immediate Next Steps (Choose Your Path)

### Option A: Continue Week 2 Implementation (Recommended)

**Start with Day 8: Insider Trading Detector Tests**

This is the natural next step after completing AML tests:

```bash
# 1. Activate environment
conda activate janusgraph-analysis

# 2. Review the implementation guide
cat docs/implementation/WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md

# 3. Create the test file
# File: banking/analytics/tests/test_detect_insider_trading.py
# Size: ~800 lines
# Tests: 40+ tests
# Target: 80%+ coverage

# 4. Run tests as you build
cd banking/analytics/tests
pytest test_detect_insider_trading.py -v --cov=banking.analytics.detect_insider_trading

# 5. Validate coverage
pytest test_detect_insider_trading.py --cov=banking.analytics.detect_insider_trading --cov-report=term-missing
```

**What You'll Implement:**
- ✅ 10 timing correlation tests (pre-announcement trades)
- ✅ 8 coordinated trading tests (multiple traders)
- ✅ 8 communication analysis tests (suspicious keywords)
- ✅ 6 network analysis tests (insider relationships)
- ✅ 8 utility method tests (date parsing, severity)

**Time Estimate:** 4-6 hours  
**Deliverable:** 800 lines, 40+ tests, 80%+ coverage

---

### Option B: High-Value Priority Implementation

**Focus on Streaming Consumers First (Highest Business Value)**

If you want to prioritize the most critical components:

```bash
# 1. Activate environment
conda activate janusgraph-analysis

# 2. Start with GraphConsumer tests
# File: banking/streaming/tests/test_graph_consumer.py
# Size: ~500 lines
# Tests: 25+ tests
# Target: 80%+ coverage

# 3. Then VectorConsumer tests
# File: banking/streaming/tests/test_vector_consumer.py
# Size: ~450 lines
# Tests: 25+ tests
# Target: 80%+ coverage

# 4. Run tests
cd banking/streaming/tests
pytest test_graph_consumer.py test_vector_consumer.py -v --cov=banking.streaming
```

**Why This Path:**
- ✅ Tests the core data pipeline (Pulsar → JanusGraph → OpenSearch)
- ✅ Validates exactly-once semantics
- ✅ Tests entity-level ordering (Key_Shared subscription)
- ✅ Highest business impact

**Time Estimate:** 6-8 hours  
**Deliverable:** 950 lines, 50+ tests, 80%+ coverage for consumers

---

## 📋 Complete Implementation Sequence

### Week 2 Remaining Work (Days 8-12)

| Day | Module | Tests | Lines | Time | Priority |
|-----|--------|-------|-------|------|----------|
| **Day 8** | Insider Trading | 40+ | 800 | 4-6h | High |
| **Day 9** | TBML Detector | 45+ | 900 | 4-6h | High |
| **Day 10** | Consumers | 50+ | 950 | 6-8h | **Critical** |
| **Day 11** | DLQ & Metrics | 35+ | 700 | 4-5h | Medium |
| **Day 12** | Integration | 25+ | 1,000 | 6-8h | High |
| **TOTAL** | | **195+** | **4,350** | **24-33h** | |

---

## 🚀 Quick Start Commands

### For Day 8 (Insider Trading)

```bash
# Navigate to test directory
cd banking/analytics/tests

# Create test file from template
cat > test_detect_insider_trading.py << 'EOF'
"""
Unit tests for insider trading detection.

Test Categories:
1. Timing Correlation Tests (10 tests)
2. Coordinated Trading Tests (8 tests)
3. Communication Analysis Tests (8 tests)
4. Network Analysis Tests (6 tests)
5. Utility Method Tests (8 tests)

Target Coverage: 80%+
"""
import pytest
from datetime import datetime, timedelta
from banking.analytics.detect_insider_trading import InsiderTradingDetector

# ... (follow patterns from WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md)
EOF

# Run tests
pytest test_detect_insider_trading.py -v --cov=banking.analytics.detect_insider_trading
```

### For Day 10 (Consumers - High Priority)

```bash
# Navigate to streaming tests
cd banking/streaming/tests

# Create GraphConsumer test file
cat > test_graph_consumer.py << 'EOF'
"""
Unit tests for GraphConsumer (Pulsar → JanusGraph).

Test Categories:
1. Initialization Tests (5 tests)
2. Message Processing Tests (8 tests)
3. Batch Processing Tests (5 tests)
4. Error Handling Tests (4 tests)
5. Idempotency Tests (3 tests)

Target Coverage: 80%+
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from banking.streaming.graph_consumer import GraphConsumer

# ... (follow patterns from WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md)
EOF

# Run tests
pytest test_graph_consumer.py -v --cov=banking.streaming.graph_consumer
```

---

## 📊 Progress Tracking

### Current Status

```
Week 2 Progress: 28% Complete (Days 6-7 done)

✅ Day 6: Test Infrastructure (450 lines) - COMPLETE
✅ Day 7: AML Tests (700 lines, 93% coverage) - COMPLETE
⏳ Day 8: Insider Trading Tests - READY TO START
⏳ Day 9: TBML Tests - READY TO START
⏳ Day 10: Consumer Tests - READY TO START (HIGH PRIORITY)
⏳ Day 11: DLQ & Metrics Tests - READY TO START
⏳ Day 12: Integration Tests - READY TO START
```

### Coverage Targets

| Module | Current | Target | Status |
|--------|---------|--------|--------|
| AML Detector | **93%** | 80%+ | ✅ Achieved |
| Insider Trading | 0% | 80%+ | 📝 Guide Ready |
| TBML Detector | 0% | 80%+ | 📝 Guide Ready |
| GraphConsumer | 0% | 80%+ | 📝 Guide Ready |
| VectorConsumer | 0% | 80%+ | 📝 Guide Ready |
| DLQ Handler | 0% | 80%+ | 📝 Guide Ready |
| Metrics | 0% | 80%+ | 📝 Guide Ready |

---

## 🔧 Implementation Resources

### Available Documentation

1. **Implementation Guide** (850 lines)
   - [`docs/implementation/WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md`](WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md)
   - Complete test patterns for all remaining days
   - Code examples for each test category
   - Mock setup patterns and assertion strategies

2. **Scope Analysis** (150 lines)
   - [`docs/implementation/WEEK2_IMPLEMENTATION_SCOPE_ANALYSIS.md`](WEEK2_IMPLEMENTATION_SCOPE_ANALYSIS.md)
   - Detailed scope breakdown
   - Phased implementation strategy
   - Resource estimation

3. **Test Infrastructure** (450 lines)
   - [`banking/analytics/tests/conftest.py`](../../banking/analytics/tests/conftest.py)
   - 11 reusable fixtures
   - Mock JanusGraph client
   - Sample data generators

4. **Working Example** (700 lines)
   - [`banking/analytics/tests/test_aml_structuring_detector.py`](../../banking/analytics/tests/test_aml_structuring_detector.py)
   - 38 tests achieving 93% coverage
   - Proven patterns to follow

### Key Patterns to Follow

**From AML Tests (93% Coverage):**
```python
# 1. Use fixtures from conftest.py
def test_detection(mock_graph_client, sample_accounts):
    detector = AMLStructuringDetector(mock_graph_client)
    results = detector.detect_structuring(sample_accounts)
    assert results is not None

# 2. Mock JanusGraph responses
mock_graph_client.execute_query.return_value = [
    {"account_id": "A1", "amount": 9500, "date": "2024-01-01"}
]

# 3. Test edge cases
def test_empty_input(mock_graph_client):
    detector = AMLStructuringDetector(mock_graph_client)
    results = detector.detect_structuring([])
    assert results == []

# 4. Validate coverage
pytest test_file.py --cov=module --cov-report=term-missing
```

---

## 🎯 Recommended Approach

### Session 1: Day 8 (Today)
**Goal:** Complete Insider Trading tests

```bash
# Time: 4-6 hours
# Deliverable: 800 lines, 40+ tests, 80%+ coverage

1. Review implementation guide (30 min)
2. Set up test file structure (30 min)
3. Implement timing correlation tests (1.5 hours)
4. Implement coordinated trading tests (1 hour)
5. Implement communication analysis tests (1 hour)
6. Implement network analysis tests (45 min)
7. Implement utility tests (45 min)
8. Validate coverage and fix gaps (30 min)
```

### Session 2: Day 9 (Next)
**Goal:** Complete TBML tests

```bash
# Time: 4-6 hours
# Deliverable: 900 lines, 45+ tests, 80%+ coverage

Follow same pattern as Day 8
```

### Session 3: Day 10 (High Priority)
**Goal:** Complete Consumer tests

```bash
# Time: 6-8 hours
# Deliverable: 950 lines, 50+ tests, 80%+ coverage

This is the most critical day - tests the core data pipeline
```

---

## ✅ Success Criteria

### For Each Day

- [ ] All tests pass (`pytest -v`)
- [ ] Coverage ≥80% (`pytest --cov --cov-report=term-missing`)
- [ ] No linting errors (`ruff check`)
- [ ] Type checking passes (`mypy`)
- [ ] Documentation updated

### For Week 2 Complete

- [ ] Analytics module: 80%+ coverage
- [ ] Streaming module: 80%+ coverage
- [ ] All 195+ tests passing
- [ ] Integration tests validate end-to-end workflows
- [ ] Documentation reflects all changes

---

## 🆘 Getting Help

### If You Get Stuck

1. **Review the working example:**
   ```bash
   cat banking/analytics/tests/test_aml_structuring_detector.py
   ```

2. **Check the implementation guide:**
   ```bash
   cat docs/implementation/WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md
   ```

3. **Run tests incrementally:**
   ```bash
   # Test one function at a time
   pytest test_file.py::TestClass::test_specific_function -v
   ```

4. **Check coverage gaps:**
   ```bash
   pytest --cov=module --cov-report=html
   open htmlcov/index.html
   ```

### Common Issues

**Issue:** Import errors
```bash
# Solution: Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Issue:** Mock not working
```bash
# Solution: Check mock setup in conftest.py
# Use the provided fixtures instead of creating new mocks
```

**Issue:** Coverage not reaching 80%
```bash
# Solution: Check coverage report for missing lines
pytest --cov=module --cov-report=term-missing
# Add tests for uncovered branches and edge cases
```

---

## 📞 Next Actions

### Choose Your Path:

**Option A: Sequential (Recommended)**
```bash
# Start with Day 8
cd banking/analytics/tests
# Create test_detect_insider_trading.py
# Follow WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md
```

**Option B: Priority-Based**
```bash
# Start with Day 10 (Consumers)
cd banking/streaming/tests
# Create test_graph_consumer.py and test_vector_consumer.py
# Follow WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md
```

**Option C: Request Assistance**
```bash
# Ask for specific day implementation
# Example: "Implement Day 8 - Insider Trading Tests"
```

---

## 📈 Expected Outcomes

### After Day 8
- ✅ Insider trading detection fully tested
- ✅ 40+ tests covering all detection algorithms
- ✅ 80%+ coverage for detect_insider_trading.py
- ✅ Analytics module coverage: ~45%

### After Day 10
- ✅ Core data pipeline fully tested
- ✅ Pulsar → JanusGraph → OpenSearch validated
- ✅ 50+ tests covering consumers
- ✅ Streaming module coverage: ~60%

### After Day 12 (Week 2 Complete)
- ✅ 195+ tests passing
- ✅ Analytics module: 80%+ coverage
- ✅ Streaming module: 80%+ coverage
- ✅ Integration tests validate end-to-end workflows
- ✅ Production-ready test suite

---

**Ready to start? Choose your path and let's implement! 🚀**