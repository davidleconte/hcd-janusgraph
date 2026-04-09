# Implementation Plan: detect_semantic_patterns Full Coverage

**Target:** Achieve 95%+ coverage for `enhanced_structuring_detection.py` by covering lines 328-438 in `detect_semantic_patterns` method.

**Current Status:** 79% coverage, missing 110 lines in complex semantic analysis method

---

## Analysis of Uncovered Code (Lines 328-438)

### Code Structure Breakdown

The `detect_semantic_patterns` method has several distinct sections that need coverage:

1. **Transaction Processing (Lines 328-342)**
   - Building transaction descriptions for embedding
   - Creating rich text representations
   - Data preparation for semantic analysis

2. **Embedding Generation (Lines 343-350)**
   - Generating embeddings using ML model
   - Creating similarity matrix with numpy

3. **Cluster Detection (Lines 351-377)**
   - Pairwise similarity analysis
   - Identifying transaction clusters
   - Account and person ID extraction

4. **Pattern Creation (Lines 378-443)**
   - Risk score calculation
   - StructuringPattern object creation
   - Cluster processing and logging

---

## Implementation Strategy

### Phase 1: Mock-Based Unit Tests (Recommended)

**Approach:** Create comprehensive unit tests with mocked dependencies to achieve line coverage without requiring full OpenSearch/JanusGraph integration.

#### 1.1 Mock Infrastructure Setup

```python
# Required mocks for semantic patterns testing
@patch("banking.aml.enhanced_structuring_detection.DriverRemoteConnection")
@patch("banking.aml.enhanced_structuring_detection.traversal")
@patch("banking.aml.enhanced_structuring_detection.VectorSearchClient")
@patch("banking.aml.enhanced_structuring_detection.EmbeddingGenerator")
@patch("numpy.dot")
@patch("numpy.where")
@patch("numpy.mean")
```

#### 1.2 Test Cases to Implement

**Test File:** `test_semantic_patterns_coverage.py`

1. **Basic Flow Coverage (Lines 328-342)**
   ```python
   def test_semantic_patterns_transaction_processing():
       """Test transaction text building and data preparation."""
   ```

2. **Embedding Generation (Lines 343-350)**
   ```python
   def test_semantic_patterns_embedding_generation():
       """Test embedding generation and similarity matrix creation."""
   ```

3. **Insufficient Cluster Size (Lines 361-362)**
   ```python
   def test_semantic_patterns_insufficient_cluster_size():
       """Test early return when cluster size < min_cluster_size."""
   ```

4. **Multiple Account Detection (Lines 367-377)**
   ```python
   def test_semantic_patterns_multiple_accounts():
       """Test account and person ID extraction from clusters."""
   ```

5. **Total Amount Below Threshold (Lines 381-382)**
   ```python
   def test_semantic_patterns_amount_below_threshold():
       """Test skip when total amount < STRUCTURING_THRESHOLD."""
   ```

6. **Pattern Creation and Risk Scoring (Lines 383-402)**
   ```python
   def test_semantic_patterns_pattern_creation():
       """Test StructuringPattern creation with risk scoring."""
   ```

7. **Person Name Handling (Lines 388-393)**
   ```python
   def test_semantic_patterns_person_name_extraction():
       """Test person name extraction from list/string formats."""
   ```

8. **Cluster Processing (Lines 434-436)**
   ```python
   def test_semantic_patterns_cluster_processing():
       """Test marking transactions as processed."""
   ```

#### 1.3 Mock Data Structures

```python
# Sample transaction data for testing
MOCK_TRANSACTIONS = [
    {
        "tx_id": "tx-001",
        "amount": 9500.0,
        "description": "ATM Withdrawal",
        "merchant": "Bank ATM",
        "account_id": "acc-123",
        "person_id": ["person-001"],
        "person_name": ["John Doe"],
        "timestamp": 1234567890000
    },
    # ... more transactions
]

# Mock embedding matrix
MOCK_EMBEDDINGS = np.array([
    [0.1, 0.2, 0.3],  # Transaction 1 embedding
    [0.15, 0.25, 0.35],  # Similar to transaction 1
    [0.8, 0.9, 0.1],   # Different transaction
])

# Mock similarity matrix
MOCK_SIMILARITY_MATRIX = np.array([
    [1.0, 0.9, 0.2],   # High similarity between tx1 and tx2
    [0.9, 1.0, 0.1],
    [0.2, 0.1, 1.0]
])
```

### Phase 2: Integration Tests (Optional Enhancement)

**Approach:** Create integration tests that require actual OpenSearch and JanusGraph services.

#### 2.1 Test Environment Setup

```python
# Integration test requirements
@pytest.mark.integration
@pytest.mark.skipif(not OPENSEARCH_AVAILABLE, reason="OpenSearch not available")
def test_semantic_patterns_full_integration():
    """Full integration test with real services."""
```

#### 2.2 Test Data Preparation

```python
# Create test data in JanusGraph
def setup_semantic_test_data():
    """Create transactions with known semantic patterns."""
    # Insert transactions with similar descriptions
    # Insert accounts and persons
    # Return expected pattern results
```

### Phase 3: Performance and Edge Case Tests

#### 3.1 Performance Tests

```python
def test_semantic_patterns_large_dataset():
    """Test with 500+ transactions (limit case)."""

def test_semantic_patterns_memory_efficiency():
    """Test memory usage with large similarity matrices."""
```

#### 3.2 Edge Case Tests

```python
def test_semantic_patterns_empty_descriptions():
    """Test handling of empty/null descriptions."""

def test_semantic_patterns_numpy_errors():
    """Test numpy operation error handling."""

def test_semantic_patterns_embedding_failures():
    """Test embedding generation failures."""
```

---

## Implementation Timeline

### Week 1: Mock-Based Unit Tests
- **Day 1-2:** Set up mock infrastructure and basic flow tests
- **Day 3-4:** Implement cluster detection and pattern creation tests
- **Day 5:** Edge cases and error handling tests

### Week 2: Integration Tests (Optional)
- **Day 1-2:** Set up integration test environment
- **Day 3-4:** Create test data and full integration tests
- **Day 5:** Performance and stress tests

### Week 3: Optimization and Documentation
- **Day 1-2:** Optimize test performance and reliability
- **Day 3-4:** Document test patterns and maintenance
- **Day 5:** Final coverage verification and reporting

---

## Expected Coverage Improvement

### Target Metrics
- **Current:** 79% coverage (47 lines uncovered)
- **After Phase 1:** 92-95% coverage (~15-20 lines uncovered)
- **After Phase 2:** 95-98% coverage (~5-10 lines uncovered)

### Remaining Uncovered Lines (Post-Implementation)
- Exception handling edge cases in numpy operations
- Rare conditional branches in person name extraction
- Performance optimization paths

---

## Technical Challenges and Solutions

### Challenge 1: Complex Numpy Operations
**Problem:** Similarity matrix operations are hard to mock realistically
**Solution:** Use actual small numpy arrays in tests, mock only the embedding generation

### Challenge 2: Nested Data Structures
**Problem:** Transaction data has complex nested lists/dictionaries
**Solution:** Create comprehensive mock data factories with all edge cases

### Challenge 3: ML Model Dependencies
**Problem:** EmbeddingGenerator requires ML models
**Solution:** Mock the encode() method to return predictable embeddings

### Challenge 4: Graph Query Complexity
**Problem:** Complex Gremlin queries are hard to mock
**Solution:** Mock the final toList() result with realistic transaction data

---

## Implementation Priority

### High Priority (Must Have)
1. **Basic flow coverage** - Lines 328-350 (transaction processing, embeddings)
2. **Cluster detection logic** - Lines 351-377 (similarity analysis)
3. **Pattern creation** - Lines 378-430 (risk scoring, object creation)

### Medium Priority (Should Have)
4. **Edge case handling** - Empty data, insufficient clusters
5. **Error handling** - Exception paths and recovery
6. **Performance cases** - Large datasets, memory limits

### Low Priority (Nice to Have)
7. **Integration tests** - Full service integration
8. **Stress tests** - Performance under load
9. **Regression tests** - Prevent future coverage loss

---

## Success Criteria

### Coverage Metrics
- [ ] Achieve 95%+ line coverage for `enhanced_structuring_detection.py`
- [ ] Cover all major branches in `detect_semantic_patterns`
- [ ] Maintain existing test quality and performance

### Test Quality
- [ ] All tests pass consistently (no flaky tests)
- [ ] Tests run in <10 seconds total
- [ ] Clear test documentation and maintainability

### Code Quality
- [ ] No reduction in existing functionality
- [ ] Proper error handling coverage
- [ ] Realistic mock data and scenarios

---

## Risk Mitigation

### Risk 1: Test Complexity
**Mitigation:** Start with simple mock-based tests, gradually add complexity

### Risk 2: Performance Impact
**Mitigation:** Use small datasets in tests, mock expensive operations

### Risk 3: Maintenance Burden
**Mitigation:** Create reusable test utilities and clear documentation

### Risk 4: False Coverage
**Mitigation:** Verify tests actually exercise the intended code paths

---

## Conclusion

This plan provides a systematic approach to achieving 95%+ coverage for the `detect_semantic_patterns` method through:

1. **Comprehensive mock-based unit tests** (primary approach)
2. **Optional integration tests** (for full validation)
3. **Performance and edge case coverage** (for robustness)

The mock-based approach is recommended as it provides:
- ✅ Fast execution (no external dependencies)
- ✅ Reliable results (deterministic mocks)
- ✅ Easy maintenance (no service setup required)
- ✅ High coverage (can test all code paths)

**Estimated Effort:** 15-20 hours for Phase 1 (mock tests), 10-15 hours for Phase 2 (integration tests)
**Expected Coverage:** 95%+ line coverage, 90%+ branch coverage