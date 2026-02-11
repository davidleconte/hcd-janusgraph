# Week 3 Day 17: Advanced Testing Patterns - Implementation Plan

**Date:** 2026-02-11  
**Version:** 1.0  
**Status:** Ready for Execution  
**Estimated Effort:** 5 hours

## Objective

Implement advanced testing patterns using property-based testing (Hypothesis) and mutation testing (mutmut) to further improve code quality and test effectiveness.

---

## Prerequisites

### Environment Setup

```bash
# Activate conda environment
conda activate janusgraph-analysis

# Install Hypothesis for property-based testing
uv pip install hypothesis

# Install mutmut for mutation testing
uv pip install mutmut

# Verify installations
python -c "import hypothesis; print(f'Hypothesis {hypothesis.__version__}')"
python -c "import mutmut; print('mutmut installed')"
```

---

## Task 1: Property-Based Testing for Data Generators

### Objective
Create property-based tests for data generators to verify invariants hold across wide range of inputs.

### File to Create
`banking/data_generators/tests/test_property_based.py` (300+ lines, 20+ tests)

### Test Categories

#### 1. Person Generator Properties (8 tests)
```python
from hypothesis import given, strategies as st
from banking.data_generators.core import PersonGenerator

@given(seed=st.integers(min_value=0, max_value=1000000))
def test_person_generator_deterministic(seed):
    """Property: Same seed produces same results."""
    gen1 = PersonGenerator(seed=seed)
    gen2 = PersonGenerator(seed=seed)
    
    person1 = gen1.generate()
    person2 = gen2.generate()
    
    assert person1["person_id"] == person2["person_id"]
    assert person1["name"] == person2["name"]

@given(count=st.integers(min_value=1, max_value=1000))
def test_person_generator_count(count):
    """Property: Generator produces exactly requested count."""
    gen = PersonGenerator(seed=42)
    persons = gen.generate_batch(count)
    assert len(persons) == count

@given(seed=st.integers(min_value=0))
def test_person_ids_unique(seed):
    """Property: All person IDs are unique."""
    gen = PersonGenerator(seed=seed)
    persons = gen.generate_batch(100)
    ids = [p["person_id"] for p in persons]
    assert len(ids) == len(set(ids))

@given(seed=st.integers(min_value=0))
def test_person_required_fields(seed):
    """Property: All persons have required fields."""
    gen = PersonGenerator(seed=seed)
    person = gen.generate()
    
    required_fields = ["person_id", "name", "email", "phone"]
    for field in required_fields:
        assert field in person
        assert person[field] is not None

@given(seed=st.integers(min_value=0))
def test_person_email_format(seed):
    """Property: All emails are valid format."""
    gen = PersonGenerator(seed=seed)
    persons = gen.generate_batch(50)
    
    for person in persons:
        email = person["email"]
        assert "@" in email
        assert "." in email.split("@")[1]

@given(seed=st.integers(min_value=0))
def test_person_risk_score_range(seed):
    """Property: Risk scores are in valid range [0, 1]."""
    gen = PersonGenerator(seed=seed)
    persons = gen.generate_batch(50)
    
    for person in persons:
        if "risk_score" in person:
            assert 0 <= person["risk_score"] <= 1

@given(seed=st.integers(min_value=0), count=st.integers(min_value=10, max_value=100))
def test_person_generator_no_exceptions(seed, count):
    """Property: Generator never raises exceptions for valid inputs."""
    gen = PersonGenerator(seed=seed)
    persons = gen.generate_batch(count)
    assert len(persons) == count

@given(seed=st.integers(min_value=0))
def test_person_data_types(seed):
    """Property: All fields have correct data types."""
    gen = PersonGenerator(seed=seed)
    person = gen.generate()
    
    assert isinstance(person["person_id"], str)
    assert isinstance(person["name"], str)
    assert isinstance(person["email"], str)
```

#### 2. Account Generator Properties (6 tests)
```python
@given(seed=st.integers(min_value=0))
def test_account_generator_deterministic(seed):
    """Property: Same seed produces same results."""
    # Similar to person generator

@given(seed=st.integers(min_value=0))
def test_account_balance_non_negative(seed):
    """Property: Account balances are non-negative."""
    gen = AccountGenerator(seed=seed)
    accounts = gen.generate_batch(50)
    
    for account in accounts:
        assert account["balance"] >= 0

@given(seed=st.integers(min_value=0))
def test_account_ids_unique(seed):
    """Property: All account IDs are unique."""
    # Similar to person IDs

@given(seed=st.integers(min_value=0))
def test_account_required_fields(seed):
    """Property: All accounts have required fields."""
    # Similar to person required fields

@given(seed=st.integers(min_value=0))
def test_account_types_valid(seed):
    """Property: Account types are from valid set."""
    gen = AccountGenerator(seed=seed)
    accounts = gen.generate_batch(50)
    
    valid_types = {"checking", "savings", "investment"}
    for account in accounts:
        assert account["account_type"] in valid_types

@given(seed=st.integers(min_value=0), count=st.integers(min_value=1, max_value=100))
def test_account_generator_no_exceptions(seed, count):
    """Property: Generator never raises exceptions."""
    # Similar to person generator
```

#### 3. Transaction Generator Properties (6 tests)
```python
@given(seed=st.integers(min_value=0))
def test_transaction_amount_positive(seed):
    """Property: Transaction amounts are positive."""
    gen = TransactionGenerator(seed=seed)
    transactions = gen.generate_batch(50)
    
    for txn in transactions:
        assert txn["amount"] > 0

@given(seed=st.integers(min_value=0))
def test_transaction_timestamps_ordered(seed):
    """Property: Transactions have valid timestamps."""
    gen = TransactionGenerator(seed=seed)
    transactions = gen.generate_batch(50)
    
    for txn in transactions:
        assert "timestamp" in txn
        # Verify timestamp is valid datetime

@given(seed=st.integers(min_value=0))
def test_transaction_ids_unique(seed):
    """Property: All transaction IDs are unique."""
    # Similar to other ID uniqueness tests

@given(seed=st.integers(min_value=0))
def test_transaction_required_fields(seed):
    """Property: All transactions have required fields."""
    required_fields = ["transaction_id", "from_account", "to_account", "amount"]
    # Similar to other required fields tests

@given(seed=st.integers(min_value=0))
def test_transaction_accounts_different(seed):
    """Property: From and to accounts are different."""
    gen = TransactionGenerator(seed=seed)
    transactions = gen.generate_batch(50)
    
    for txn in transactions:
        assert txn["from_account"] != txn["to_account"]

@given(seed=st.integers(min_value=0), count=st.integers(min_value=1, max_value=100))
def test_transaction_generator_no_exceptions(seed, count):
    """Property: Generator never raises exceptions."""
    # Similar to other generators
```

### Success Criteria
- 20+ property-based tests created
- All tests pass
- Tests verify invariants across wide input range
- Hypothesis finds no counterexamples

---

## Task 2: Property-Based Testing for Analytics

### Objective
Create property-based tests for analytics modules to verify detection algorithms maintain invariants.

### File to Create
`banking/analytics/tests/test_property_based.py` (250+ lines, 15+ tests)

### Test Categories

#### 1. AML Structuring Detector Properties (5 tests)
```python
from hypothesis import given, strategies as st
from banking.analytics import AMLStructuringDetector

@given(threshold=st.floats(min_value=0.0, max_value=1.0))
def test_structuring_threshold_respected(threshold):
    """Property: Detector respects configured threshold."""
    detector = AMLStructuringDetector(threshold=threshold)
    # Generate test data
    # Verify detections respect threshold

@given(transaction_count=st.integers(min_value=0, max_value=100))
def test_structuring_handles_any_count(transaction_count):
    """Property: Detector handles any transaction count."""
    detector = AMLStructuringDetector()
    # Generate transactions
    # Verify no exceptions

@given(seed=st.integers(min_value=0))
def test_structuring_deterministic(seed):
    """Property: Same data produces same results."""
    detector = AMLStructuringDetector()
    # Generate data with seed
    # Run twice, verify same results

@given(threshold=st.floats(min_value=0.0, max_value=1.0))
def test_structuring_risk_scores_in_range(threshold):
    """Property: Risk scores are in [0, 1]."""
    detector = AMLStructuringDetector(threshold=threshold)
    # Generate data
    # Verify all risk scores in range

@given(transaction_count=st.integers(min_value=1, max_value=50))
def test_structuring_no_false_negatives_obvious(transaction_count):
    """Property: Obvious patterns are detected."""
    detector = AMLStructuringDetector(threshold=0.5)
    # Generate obvious structuring pattern
    # Verify detection
```

#### 2. Insider Trading Detector Properties (5 tests)
```python
@given(threshold=st.floats(min_value=0.0, max_value=1.0))
def test_insider_trading_threshold_respected(threshold):
    """Property: Detector respects configured threshold."""
    # Similar to structuring

@given(trade_count=st.integers(min_value=0, max_value=100))
def test_insider_trading_handles_any_count(trade_count):
    """Property: Detector handles any trade count."""
    # Similar to structuring

@given(seed=st.integers(min_value=0))
def test_insider_trading_deterministic(seed):
    """Property: Same data produces same results."""
    # Similar to structuring

@given(threshold=st.floats(min_value=0.0, max_value=1.0))
def test_insider_trading_risk_scores_in_range(threshold):
    """Property: Risk scores are in [0, 1]."""
    # Similar to structuring

@given(trade_count=st.integers(min_value=1, max_value=50))
def test_insider_trading_temporal_ordering(trade_count):
    """Property: Trades are analyzed in temporal order."""
    # Verify temporal analysis
```

#### 3. TBML Detector Properties (5 tests)
```python
@given(threshold=st.floats(min_value=0.0, max_value=1.0))
def test_tbml_threshold_respected(threshold):
    """Property: Detector respects configured threshold."""
    # Similar to other detectors

@given(transaction_count=st.integers(min_value=0, max_value=100))
def test_tbml_handles_any_count(transaction_count):
    """Property: Detector handles any transaction count."""
    # Similar to other detectors

@given(seed=st.integers(min_value=0))
def test_tbml_deterministic(seed):
    """Property: Same data produces same results."""
    # Similar to other detectors

@given(threshold=st.floats(min_value=0.0, max_value=1.0))
def test_tbml_risk_scores_in_range(threshold):
    """Property: Risk scores are in [0, 1]."""
    # Similar to other detectors

@given(transaction_count=st.integers(min_value=1, max_value=50))
def test_tbml_trade_patterns_valid(transaction_count):
    """Property: Detected patterns are valid."""
    # Verify pattern validity
```

### Success Criteria
- 15+ property-based tests created
- All tests pass
- Tests verify algorithm invariants
- Hypothesis finds no counterexamples

---

## Task 3: Mutation Testing Configuration

### Objective
Configure and run mutation testing to verify test suite effectiveness.

### File to Create
`.mutmut-config` (mutation testing configuration)

### Configuration
```ini
[mutmut]
paths_to_mutate=src/python/,banking/
tests_dir=tests/,banking/tests/
runner=pytest
dict_synonyms=Struct, NamedStruct
```

### Mutation Testing Commands

```bash
# Run mutation testing on exceptions module
mutmut run --paths-to-mutate=src/python/exceptions.py

# Show results
mutmut results

# Show specific mutants
mutmut show <mutant-id>

# Generate HTML report
mutmut html
```

### Target Modules for Mutation Testing

1. **src/python/exceptions.py**
   - Target: >90% mutation score
   - Focus: Exception hierarchy, utility functions

2. **banking/exceptions.py**
   - Target: >90% mutation score
   - Focus: Banking exception hierarchy

3. **banking/streaming/producer.py**
   - Target: >80% mutation score
   - Focus: Producer logic, error handling

4. **banking/streaming/events.py**
   - Target: >85% mutation score
   - Focus: Event creation, serialization

### Success Criteria
- Mutation testing configured
- >80% mutation score for core modules
- >85% mutation score for exception modules
- Identified weak tests improved

---

## Task 4: Documentation

### File to Create
`docs/implementation/WEEK3_DAY17_SUMMARY.md`

### Content Structure

1. **Overview**
   - Property-based testing implementation
   - Mutation testing results
   - Key findings

2. **Property-Based Testing Results**
   - Tests created (35+ total)
   - Invariants verified
   - Counterexamples found (if any)

3. **Mutation Testing Results**
   - Mutation scores by module
   - Weak tests identified
   - Improvements made

4. **Lessons Learned**
   - What worked well
   - Challenges overcome
   - Best practices

5. **Next Steps**
   - Day 18 preparation
   - Performance optimization targets

---

## Execution Checklist

### Setup Phase
- [ ] Activate conda environment
- [ ] Install Hypothesis: `uv pip install hypothesis`
- [ ] Install mutmut: `uv pip install mutmut`
- [ ] Verify installations

### Implementation Phase
- [ ] Create `banking/data_generators/tests/test_property_based.py`
- [ ] Implement 20+ property tests for generators
- [ ] Run tests: `pytest banking/data_generators/tests/test_property_based.py -v`
- [ ] Verify all tests pass

- [ ] Create `banking/analytics/tests/test_property_based.py`
- [ ] Implement 15+ property tests for analytics
- [ ] Run tests: `pytest banking/analytics/tests/test_property_based.py -v`
- [ ] Verify all tests pass

### Mutation Testing Phase
- [ ] Create `.mutmut-config`
- [ ] Run mutation testing on `src/python/exceptions.py`
- [ ] Run mutation testing on `banking/exceptions.py`
- [ ] Run mutation testing on `banking/streaming/producer.py`
- [ ] Analyze results and improve weak tests
- [ ] Generate HTML report

### Documentation Phase
- [ ] Create `docs/implementation/WEEK3_DAY17_SUMMARY.md`
- [ ] Document property-based testing results
- [ ] Document mutation testing results
- [ ] Document lessons learned
- [ ] Update todo list

---

## Expected Deliverables

1. **Property-Based Tests**
   - `banking/data_generators/tests/test_property_based.py` (300+ lines, 20+ tests)
   - `banking/analytics/tests/test_property_based.py` (250+ lines, 15+ tests)

2. **Mutation Testing**
   - `.mutmut-config` (configuration file)
   - Mutation testing reports (HTML)
   - Improved tests based on mutation findings

3. **Documentation**
   - `docs/implementation/WEEK3_DAY17_SUMMARY.md` (400+ lines)

4. **Metrics**
   - 35+ property-based tests
   - >80% mutation score
   - 100% test pass rate

---

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Property Tests Created | 35+ | Pending |
| Property Tests Pass Rate | 100% | Pending |
| Mutation Score (exceptions) | >85% | Pending |
| Mutation Score (streaming) | >80% | Pending |
| Documentation | Complete | Pending |

---

## Risk Mitigation

### Risk: Hypothesis finds counterexamples
**Mitigation:** Fix generator logic or adjust property constraints

### Risk: Low mutation score
**Mitigation:** Add tests for uncovered mutations, improve test assertions

### Risk: Performance issues with property tests
**Mitigation:** Reduce example count, use `@settings(max_examples=100)`

---

## Notes

- Property-based tests may take longer to run (use `@settings(max_examples=50)` for faster feedback)
- Mutation testing can be slow (run on specific modules first)
- Focus on high-value invariants (uniqueness, ranges, required fields)
- Document any interesting counterexamples found by Hypothesis

---

**Document Status:** Ready for Execution  
**Estimated Time:** 5 hours  
**Prerequisites:** Weeks 1-2 complete, Week 3 Days 13-16 complete  
**Next:** Week 3 Day 18 - Performance Optimization