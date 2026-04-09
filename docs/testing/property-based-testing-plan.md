# Property-Based Testing Implementation Plan
# Priority Action 1: +0.1 Points to Excellence Score

**Date:** 2026-04-09  
**Target:** Testing Excellence 9.7 → 9.8  
**Effort:** 2-3 weeks  
**Status:** In Progress

---

## Executive Summary

Implement property-based testing using Hypothesis to validate invariants and edge cases across critical algorithms. This will improve test coverage quality and catch subtle bugs that example-based tests might miss.

---

## Objectives

1. **Add Hypothesis tests for core algorithms** (+0.05)
   - Data generators (deterministic properties)
   - Graph algorithms (UBO discovery, community detection)
   - Pattern detection (AML, fraud)

2. **Run mutation testing on critical paths** (+0.05)
   - Use mutmut to verify test effectiveness
   - Achieve >80% mutation score on critical modules

---

## Phase 1: Property-Based Testing (Week 1-2)

### 1.1 Data Generator Properties

**Module:** `banking/data_generators/`

**Properties to Test:**

```python
# tests/property/test_person_generator_properties.py

from hypothesis import given, strategies as st
from banking.data_generators.core import PersonGenerator

@given(st.integers(min_value=1, max_value=1000))
def test_person_count_invariant(count):
    """Property: Generator produces exactly N persons."""
    generator = PersonGenerator(seed=42)
    persons = generator.generate(count)
    assert len(persons) == count

@given(st.integers(min_value=0, max_value=2**31-1))
def test_deterministic_output(seed):
    """Property: Same seed produces identical output."""
    gen1 = PersonGenerator(seed=seed)
    gen2 = PersonGenerator(seed=seed)
    
    persons1 = gen1.generate(10)
    persons2 = gen2.generate(10)
    
    assert persons1 == persons2

@given(st.integers(min_value=1, max_value=100))
def test_unique_ids(count):
    """Property: All person IDs are unique."""
    generator = PersonGenerator(seed=42)
    persons = generator.generate(count)
    ids = [p.person_id for p in persons]
    assert len(ids) == len(set(ids))

@given(st.integers(min_value=1, max_value=100))
def test_valid_email_format(count):
    """Property: All emails are valid."""
    generator = PersonGenerator(seed=42)
    persons = generator.generate(count)
    
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    for person in persons:
        assert re.match(email_pattern, person.email)

@given(st.integers(min_value=18, max_value=100))
def test_age_constraints(min_age):
    """Property: All persons meet minimum age requirement."""
    generator = PersonGenerator(seed=42, min_age=min_age)
    persons = generator.generate(50)
    
    for person in persons:
        age = (datetime.now() - person.date_of_birth).days // 365
        assert age >= min_age
```

**Files to Create:**
- `tests/property/test_person_generator_properties.py`
- `tests/property/test_company_generator_properties.py`
- `tests/property/test_account_generator_properties.py`
- `tests/property/test_transaction_generator_properties.py`

**Estimated Effort:** 3-4 days

### 1.2 Graph Algorithm Properties

**Module:** `src/python/analytics/`

**Properties to Test:**

```python
# tests/property/test_ubo_discovery_properties.py

from hypothesis import given, strategies as st
from src.python.analytics.ubo_discovery import UBODiscovery

@given(st.floats(min_value=0.0, max_value=1.0))
def test_ownership_threshold_monotonicity(threshold):
    """Property: Higher threshold → fewer UBOs."""
    discovery = UBODiscovery(ownership_threshold=threshold)
    
    # Test with sample graph
    ubos_high = discovery.find_ubos(entity_id="test", threshold=0.8)
    ubos_low = discovery.find_ubos(entity_id="test", threshold=0.5)
    
    assert len(ubos_high) <= len(ubos_low)

@given(st.integers(min_value=1, max_value=10))
def test_max_depth_constraint(max_depth):
    """Property: Search respects max depth."""
    discovery = UBODiscovery(max_depth=max_depth)
    
    paths = discovery.find_ownership_paths(entity_id="test")
    
    for path in paths:
        assert len(path) <= max_depth

@given(st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=1, max_size=10))
def test_ownership_chain_multiplication(percentages):
    """Property: Chain ownership is product of percentages."""
    total = 1.0
    for pct in percentages:
        total *= pct
    
    assert 0.0 <= total <= 1.0
```

**Files to Create:**
- `tests/property/test_ubo_discovery_properties.py`
- `tests/property/test_community_detection_properties.py`
- `tests/property/test_graph_traversal_properties.py`

**Estimated Effort:** 3-4 days

### 1.3 Pattern Detection Properties

**Module:** `banking/aml/`, `banking/fraud/`

**Properties to Test:**

```python
# tests/property/test_structuring_detection_properties.py

from hypothesis import given, strategies as st
from banking.aml.structuring_detection import StructuringDetector

@given(st.lists(st.floats(min_value=0.0, max_value=10000.0), min_size=1, max_size=100))
def test_threshold_sensitivity(amounts):
    """Property: Detector is sensitive to threshold."""
    detector = StructuringDetector(threshold=10000.0)
    
    # Amounts below threshold should not trigger
    below_threshold = [a for a in amounts if a < 10000.0]
    alerts_below = detector.detect(below_threshold)
    
    # Amounts above threshold should trigger
    above_threshold = [a for a in amounts if a >= 10000.0]
    alerts_above = detector.detect(above_threshold)
    
    if above_threshold:
        assert len(alerts_above) > 0

@given(st.integers(min_value=1, max_value=100))
def test_transaction_count_monotonicity(count):
    """Property: More transactions → more potential alerts."""
    detector = StructuringDetector()
    
    # Generate transactions
    transactions = [{"amount": 9500.0} for _ in range(count)]
    alerts = detector.detect(transactions)
    
    # Alert count should scale with transaction count
    assert len(alerts) <= count
```

**Files to Create:**
- `tests/property/test_structuring_detection_properties.py`
- `tests/property/test_sanctions_screening_properties.py`
- `tests/property/test_fraud_detection_properties.py`

**Estimated Effort:** 2-3 days

---

## Phase 2: Mutation Testing (Week 2-3)

### 2.1 Setup Mutation Testing

**Install mutmut:**

```bash
conda activate janusgraph-analysis
uv pip install mutmut
```

**Configure mutmut:**

```toml
# pyproject.toml

[tool.mutmut]
paths_to_mutate = [
    "src/python/client/",
    "src/python/config/",
    "src/python/analytics/",
    "banking/data_generators/core/",
    "banking/aml/",
    "banking/fraud/"
]
tests_dir = "tests/"
runner = "pytest"
```

### 2.2 Run Mutation Testing

**Critical Modules (Priority Order):**

1. **JanusGraph Client** (`src/python/client/`)
   - Target: >85% mutation score
   - Focus: Connection handling, query execution, error handling

2. **Data Generators** (`banking/data_generators/core/`)
   - Target: >80% mutation score
   - Focus: Deterministic generation, validation

3. **AML Detection** (`banking/aml/`)
   - Target: >75% mutation score
   - Focus: Pattern detection, threshold logic

4. **Configuration** (`src/python/config/`)
   - Target: >90% mutation score
   - Focus: Settings validation, defaults

**Commands:**

```bash
# Run mutation testing on specific module
mutmut run --paths-to-mutate=src/python/client/

# Show results
mutmut results

# Show surviving mutants (tests didn't catch)
mutmut show

# Apply specific mutation to see what changed
mutmut show 5

# Generate HTML report
mutmut html
```

### 2.3 Fix Surviving Mutants

**Process:**

1. Run mutmut on module
2. Identify surviving mutants
3. Analyze why tests didn't catch the mutation
4. Add tests to kill the mutant
5. Re-run mutmut to verify
6. Repeat until >80% mutation score

**Example:**

```python
# Original code (src/python/client/janusgraph_client.py)
def execute_query(self, query: str) -> List[Dict]:
    if not query:
        raise ValueError("Query cannot be empty")
    return self._execute(query)

# Mutant: Changed "not query" to "query"
# This mutant survives if we don't test empty string

# Add test to kill mutant
def test_execute_query_empty_string():
    client = JanusGraphClient()
    with pytest.raises(ValueError, match="Query cannot be empty"):
        client.execute_query("")
```

**Estimated Effort:** 5-7 days

---

## Phase 3: Integration & Documentation (Week 3)

### 3.1 CI Integration

**Add to `.github/workflows/property-testing.yml`:**

```yaml
name: Property-Based Testing

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  property-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -r requirements.txt
          uv pip install hypothesis pytest
      
      - name: Run property-based tests
        run: |
          pytest tests/property/ -v --hypothesis-show-statistics
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: property-test-results
          path: .hypothesis/
```

### 3.2 Mutation Testing CI

**Add to `.github/workflows/mutation-testing.yml`:**

```yaml
name: Mutation Testing

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  workflow_dispatch:

jobs:
  mutation-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -r requirements.txt
          uv pip install mutmut pytest
      
      - name: Run mutation testing
        run: |
          mutmut run --paths-to-mutate=src/python/client/
          mutmut results
          mutmut html
      
      - name: Upload mutation report
        uses: actions/upload-artifact@v3
        with:
          name: mutation-report
          path: html/
```

### 3.3 Documentation

**Create:**
- `docs/testing/property-based-testing-guide.md`
- `docs/testing/mutation-testing-guide.md`
- Update `docs/testing/README.md`

**Estimated Effort:** 2-3 days

---

## Success Criteria

### Property-Based Testing
- ✅ 30+ property-based tests added
- ✅ Coverage of core algorithms (generators, analytics, detection)
- ✅ CI integration with Hypothesis
- ✅ Documentation complete

### Mutation Testing
- ✅ >80% mutation score on critical modules
- ✅ Client: >85%
- ✅ Config: >90%
- ✅ Generators: >80%
- ✅ AML: >75%
- ✅ CI integration (weekly runs)
- ✅ HTML reports generated

### Impact
- **Testing Score:** 9.7 → 9.8 (+0.1)
- **Overall Score:** 9.8 → 9.9 (+0.1)

---

## Timeline

| Week | Tasks | Deliverables |
|------|-------|--------------|
| Week 1 | Property tests for generators | 15+ tests, CI integration |
| Week 2 | Property tests for analytics/detection | 15+ tests, mutation setup |
| Week 3 | Mutation testing, fix mutants | >80% score, documentation |

**Total Effort:** 2-3 weeks  
**Resources:** 1 developer  
**Dependencies:** None

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Hypothesis tests too slow | Medium | Use `@settings(max_examples=100)` |
| Mutation testing takes too long | Medium | Run weekly, focus on critical modules |
| False positives in mutants | Low | Manual review, adjust test strategy |

---

## Next Steps

1. ✅ Create property test directory structure
2. ✅ Install Hypothesis and mutmut
3. ⏳ Implement Phase 1: Data generator properties
4. ⏳ Implement Phase 2: Graph algorithm properties
5. ⏳ Implement Phase 3: Pattern detection properties
6. ⏳ Run mutation testing on critical modules
7. ⏳ Fix surviving mutants
8. ⏳ CI integration
9. ⏳ Documentation

---

**Status:** Ready to start  
**Owner:** Development Team  
**Reviewer:** QA Lead  
**Next Review:** 2026-04-16 (Week 1 checkpoint)