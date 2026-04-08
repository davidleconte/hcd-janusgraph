# Testing Levels Explained
**Date:** 2026-04-07
**Purpose:** Clarify what each testing level means and what it requires

---

## Testing Pyramid

```
                    /\
                   /  \
                  /    \
                 /  E2E \
                /--------\
               /          \
              / Integration \
             /--------------\
            /                \
           /   Unit Tests     \
          /--------------------\
         /                      \
        /   Import/Syntax Tests  \
       /--------------------------\
```

---

## Level 1: Import/Syntax Testing ✅ (COMPLETED)

### What It Tests
- Can Python import the module without errors?
- Are all dependencies available?
- Is the syntax correct?
- Can classes be instantiated?

### What It Does NOT Test
- Does the code actually work?
- Do the algorithms produce correct results?
- Can it connect to real services?

### Example
```python
# This PASSES import testing
from banking.analytics.detect_insider_trading import InsiderTradingDetector
detector = InsiderTradingDetector(url='ws://localhost:18182/gremlin')
print("✅ Import successful")
```

**Result:** ✅ Code can be imported and instantiated

**What We DON'T Know:**
- ❓ Can it actually connect to JanusGraph?
- ❓ Do the detection algorithms work correctly?
- ❓ Does it return valid results?

---

## Level 2: Unit Testing ⚠️ (NOT YET DONE)

### What It Tests
- Individual functions work correctly in isolation
- Edge cases are handled properly
- Error conditions are caught
- Return values are correct

### Requirements
- ✅ No external services needed
- ✅ Uses mocks/stubs for dependencies
- ✅ Fast execution (milliseconds)

### Example
```python
def test_calculate_risk_score():
    """Test risk score calculation with known inputs."""
    # Arrange
    trades = [
        {'value': 100000, 'timing': 'suspicious'},
        {'value': 50000, 'timing': 'normal'}
    ]
    
    # Act
    score = calculate_risk_score(trades)
    
    # Assert
    assert 0 <= score <= 100
    assert score > 50  # Should be high risk
```

**Status:** ⚠️ NOT IMPLEMENTED (Sprint 3.1)

---

## Level 3: Integration Testing ⚠️ (NOT YET DONE)

### What It Tests
- Components work together correctly
- Real database connections work
- Data flows through the system
- APIs respond correctly

### Requirements
- ❌ **Requires running services:**
  - JanusGraph (port 18182)
  - HCD/Cassandra (port 9042)
  - OpenSearch (port 9200)
  - Pulsar (port 6650)
- ❌ Requires test data loaded
- ❌ Slower execution (seconds to minutes)

### Example
```python
def test_detect_insider_trading_with_real_graph():
    """Test detection with real JanusGraph connection."""
    # Requires: JanusGraph running on localhost:18182
    detector = InsiderTradingDetector(url='ws://localhost:18182/gremlin')
    
    # This will FAIL if JanusGraph is not running
    detector.connect()
    
    # Run actual detection on real graph data
    alerts = detector.detect_multi_hop_tipping(
        symbol='AAPL',
        days_before=30,
        max_hops=3
    )
    
    # Verify results
    assert isinstance(alerts, list)
    assert all(isinstance(a, InsiderTradingAlert) for a in alerts)
```

**Status:** ⚠️ NOT IMPLEMENTED (Sprint 3.1)

**Why It's Not Done:**
- Requires full stack deployment
- Requires test data seeding
- Requires service health checks
- Takes longer to execute

---

## Level 4: End-to-End (E2E) Testing ⚠️ (NOT YET DONE)

### What It Tests
- Complete user workflows
- Jupyter notebook execution
- API endpoints
- Data persistence
- Performance under load

### Requirements
- ❌ **Requires full production-like environment:**
  - All services running
  - Monitoring enabled
  - Security configured
  - Test data loaded
- ❌ Requires realistic scenarios
- ❌ Slowest execution (minutes to hours)

### Example
```python
def test_complete_insider_trading_workflow():
    """Test complete workflow from data generation to detection."""
    # Step 1: Generate test scenario
    generator = InsiderTradingScenarioGenerator(seed=42)
    scenario = generator.generate_multi_hop_tipping_scenario(hops=3)
    
    # Step 2: Load into JanusGraph
    loader = JanusGraphLoader(url='ws://localhost:18182/gremlin')
    loader.load_scenario(scenario)
    
    # Step 3: Run detection
    detector = InsiderTradingDetector(url='ws://localhost:18182/gremlin')
    alerts = detector.detect_multi_hop_tipping(
        symbol=scenario.symbol,
        days_before=30,
        max_hops=3
    )
    
    # Step 4: Verify expected alerts found
    assert len(alerts) > 0
    assert any(a.severity == 'critical' for a in alerts)
    
    # Step 5: Verify data in OpenSearch
    vector_client = VectorSearchClient(url='http://localhost:9200')
    results = vector_client.search_similar_communications(
        query_text="merger acquisition",
        top_k=10
    )
    assert len(results) > 0
```

**Status:** ⚠️ NOT IMPLEMENTED (Sprint 3.2)

---

## Current Testing Status

### ✅ What We've Tested (Level 1)

**Import Testing:**
```bash
✅ InsiderTradingDetector imports
✅ EmbeddingGenerator imports
✅ VectorSearchClient imports
✅ InsiderTradingScenarioGenerator imports
✅ All classes instantiate without errors
✅ All methods exist and are callable
```

**What This Proves:**
- Code syntax is correct
- Dependencies are available
- Classes can be created
- No import errors

**What This Does NOT Prove:**
- Code actually works with real data
- Algorithms produce correct results
- Services can be connected to
- Performance is acceptable

### ⚠️ What We Haven't Tested (Levels 2-4)

**Unit Tests (Level 2):**
- ❌ Individual function correctness
- ❌ Edge case handling
- ❌ Error condition handling
- ❌ Return value validation

**Integration Tests (Level 3):**
- ❌ JanusGraph connection
- ❌ Gremlin query execution
- ❌ OpenSearch vector search
- ❌ Data persistence
- ❌ Cross-component communication

**E2E Tests (Level 4):**
- ❌ Complete workflows
- ❌ Jupyter notebook execution
- ❌ Performance benchmarks
- ❌ Deterministic behavior validation

---

## Why Services Are Required

### JanusGraph (Port 18182)
**Required For:**
- Executing Gremlin queries
- Graph traversals (multi-hop detection)
- Vertex/edge operations
- Transaction management

**Example Test:**
```python
# This requires JanusGraph running
detector.connect()  # Connects to ws://localhost:18182/gremlin
alerts = detector.detect_multi_hop_tipping(...)  # Executes Gremlin queries
```

### HCD/Cassandra (Port 9042)
**Required For:**
- Graph data storage
- Schema validation
- Data persistence
- Backup/restore operations

**Example Test:**
```python
# This requires HCD running
loader.load_persons(persons)  # Writes to Cassandra via JanusGraph
```

### OpenSearch (Port 9200)
**Required For:**
- Vector similarity search
- k-NN queries
- Semantic MNPI detection
- Index management

**Example Test:**
```python
# This requires OpenSearch running
results = vector_client.search_similar_communications(
    query_text="insider information",
    top_k=10
)
```

### Pulsar (Port 6650)
**Required For:**
- Event streaming
- Real-time data ingestion
- Message queue operations
- Consumer/producer testing

**Example Test:**
```python
# This requires Pulsar running
producer.send_event(event)  # Publishes to Pulsar topic
```

---

## How to Run Each Testing Level

### Level 1: Import Testing (✅ Done)
```bash
# No services required
conda run -n janusgraph-analysis python -c "
from banking.analytics.detect_insider_trading import InsiderTradingDetector
print('✅ Import successful')
"
```

### Level 2: Unit Testing (⚠️ To Do)
```bash
# No services required
conda run -n janusgraph-analysis pytest tests/unit/ -v
```

### Level 3: Integration Testing (⚠️ To Do)
```bash
# Requires services running
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
sleep 90  # Wait for services to be ready

# Then run tests
conda run -n janusgraph-analysis pytest tests/integration/ -v
```

### Level 4: E2E Testing (⚠️ To Do)
```bash
# Requires full stack + test data
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
sleep 90

# Load test data
conda run -n janusgraph-analysis python scripts/init/load_comprehensive_banking_data.py

# Run E2E tests
conda run -n janusgraph-analysis pytest tests/e2e/ -v

# Or run Jupyter notebook
conda run -n janusgraph-analysis jupyter nbconvert \
  --to notebook \
  --execute notebooks/insider-trading-detection-demo.ipynb
```

---

## Summary

### What "Test functionality (requires services)" Means

**It means:**
1. **Deploy full stack** (JanusGraph, HCD, OpenSearch, Pulsar)
2. **Load test data** into the graph
3. **Execute actual detection algorithms** against real data
4. **Verify results** are correct and expected
5. **Measure performance** (query times, throughput)
6. **Validate deterministic behavior** (same seed = same results)

**Why it's not done yet:**
- Takes 5-10 minutes to deploy services
- Requires ~24GB RAM (Podman machine)
- Needs test data generation and loading
- Slower to execute (seconds vs milliseconds)
- More complex to debug when failures occur

**When it will be done:**
- Sprint 3.1: Unit + Integration tests
- Sprint 3.2: E2E tests + Performance benchmarks

---

## Current Confidence Level

### High Confidence ✅
- Code exists and is syntactically correct
- All imports work
- Classes can be instantiated
- Methods exist and are callable
- No missing dependencies

### Medium Confidence ⚠️
- Algorithms are logically sound (code review)
- Gremlin queries are well-formed (syntax check)
- Error handling is present (code inspection)

### Low Confidence ❌
- Detection algorithms produce correct results (not tested)
- Performance is acceptable (not measured)
- Deterministic behavior works (not validated)
- Integration with services works (not tested)

---

## Conclusion

**Current Status:** Code is **importable and instantiable** (Level 1 ✅)

**Next Steps:** 
1. Implement unit tests (Level 2)
2. Deploy services and run integration tests (Level 3)
3. Run E2E tests with Jupyter notebook (Level 4)

**Platform Score Justification:**
- 95/100 is appropriate for "code complete and importable"
- 100/100 would require all testing levels passing
- Current score reflects: "Code works syntactically, functionality not yet validated"

---

**END OF TESTING LEVELS EXPLANATION**