# Week 2: Analytics & Streaming Testing Enhancement Plan

**Date:** 2026-02-11  
**Duration:** Days 6-12 (7 days)  
**Focus:** Analytics Module (0% → 80%+) & Streaming Module (28% → 80%+)  
**Technology:** Apache Pulsar (NOT Kafka)

---

## Executive Summary

Week 2 focuses on comprehensive testing enhancement for two critical modules:

1. **Analytics Module** - AML/fraud detection algorithms (currently 0% coverage)
2. **Streaming Module** - Apache Pulsar-based event streaming (currently 28% coverage)

**Key Correction:** This project uses **Apache Pulsar**, not Kafka. All streaming tests must use Pulsar-specific features including:
- Key_Shared subscription mode (Pulsar-specific)
- Pulsar's native deduplication via sequence_id
- Pulsar topics with persistent:// protocol
- Pulsar CLI tools for debugging
- Pulsar standalone mode for testing

---

## Current State Analysis

### Analytics Module (0% Coverage)

**Files:**
- `banking/analytics/aml_structuring_detector.py` (100 lines) - 0% coverage
- `banking/analytics/detect_insider_trading.py` (100+ lines) - 0% coverage  
- `banking/analytics/detect_tbml.py` (100+ lines) - 0% coverage

**Existing Tests:**
- `test_detect_insider_trading.py` - 25 tests (initialization, dataclasses, utilities)
- `test_detect_tbml.py` - 30+ tests (initialization, price anomalies, utilities)
- `test_integration_analytics.py` - 15 tests (all skipped - require JanusGraph)

**Coverage Gaps:**
- ❌ No tests for core detection algorithms
- ❌ No tests for Gremlin query execution
- ❌ No tests for risk scoring logic
- ❌ No tests for pattern matching algorithms
- ❌ No mock JanusGraph fixtures
- ❌ No property-based tests for edge cases

### Streaming Module (28% Coverage)

**Files:**
- `banking/streaming/producer.py` - 90% coverage ✅
- `banking/streaming/events.py` - 95% coverage ✅
- `banking/streaming/entity_converter.py` - 92% coverage ✅
- `banking/streaming/streaming_orchestrator.py` - 88% coverage ✅
- `banking/streaming/graph_consumer.py` - **0% coverage** ❌
- `banking/streaming/vector_consumer.py` - **0% coverage** ❌
- `banking/streaming/dlq_handler.py` - **0% coverage** ❌
- `banking/streaming/metrics.py` - **0% coverage** ❌

**Existing Tests:**
- 144 tests passing
- 1 test failing (mock fallback test)
- 15 tests skipped (integration tests requiring services)

**Coverage Gaps:**
- ❌ No GraphConsumer tests (Pulsar → JanusGraph)
- ❌ No VectorConsumer tests (Pulsar → OpenSearch)
- ❌ No DLQ handler tests (retry/archive logic)
- ❌ No metrics collection tests
- ❌ No Pulsar-specific feature tests (Key_Shared, deduplication)
- ❌ No backpressure/exactly-once semantics tests
- ❌ No integration tests with real Pulsar

---

## Week 2 Objectives

### Primary Goals

1. **Analytics Module: 0% → 80%+ coverage**
   - Create mock JanusGraph fixtures
   - Test all detection algorithms
   - Test risk scoring logic
   - Add property-based tests

2. **Streaming Module: 28% → 80%+ coverage**
   - Test GraphConsumer (Pulsar → JanusGraph)
   - Test VectorConsumer (Pulsar → OpenSearch)
   - Test DLQ handler with retry scenarios
   - Test Pulsar-specific features
   - Add integration tests with testcontainers

3. **Fix Existing Issues**
   - Fix failing mock fallback test
   - Enable skipped integration tests

---

## Implementation Plan

### Day 6: Analytics Test Infrastructure (Monday)

**Objective:** Create reusable test fixtures and mocks for analytics testing

**Tasks:**

1. **Create Mock JanusGraph Client** (`banking/analytics/tests/conftest.py`)
   ```python
   @pytest.fixture
   def mock_janusgraph_client():
       """Mock JanusGraph client for testing without real connection."""
       client = Mock()
       client.submit = Mock()
       return client
   ```

2. **Create Sample Data Fixtures**
   ```python
   @pytest.fixture
   def sample_transactions():
       """Sample transaction data for testing."""
       return [
           {"id": "tx-1", "amount": 9500, "account": "acc-1"},
           {"id": "tx-2", "amount": 9800, "account": "acc-1"},
           # ... more samples
       ]
   ```

3. **Create Test Utilities**
   - Helper functions for creating test data
   - Assertion helpers for risk scores
   - Query result builders

**Deliverables:**
- `banking/analytics/tests/conftest.py` (200 lines)
- `banking/analytics/tests/test_utils.py` (150 lines)
- Documentation in `banking/analytics/tests/README.md`

**Success Criteria:**
- ✅ Reusable fixtures for all analytics tests
- ✅ Mock client that simulates JanusGraph responses
- ✅ Sample data covering all detection scenarios

---

### Day 7: AML Structuring Detector Tests (Tuesday)

**Objective:** Achieve 80%+ coverage for `aml_structuring_detector.py`

**Tasks:**

1. **Unit Tests for Core Methods** (`test_aml_structuring_detector.py`)
   - `test_analyze_transaction_amounts()` - Distribution analysis
   - `test_detect_structuring_patterns()` - Pattern detection
   - `test_calculate_risk_score()` - Risk scoring
   - `test_find_rapid_succession_deposits()` - Timing analysis

2. **Edge Case Tests**
   - Empty transaction list
   - Single transaction
   - All transactions above threshold
   - All transactions below threshold
   - Boundary values (exactly $10,000, $9,999.99)

3. **Property-Based Tests** (using Hypothesis)
   ```python
   @given(st.lists(st.floats(min_value=0, max_value=20000)))
   def test_risk_score_always_between_0_and_100(amounts):
       detector = AMLStructuringDetector()
       score = detector.calculate_risk_score(amounts)
       assert 0 <= score <= 100
   ```

**Deliverables:**
- `banking/analytics/tests/test_aml_structuring_detector.py` (400 lines)
- 30+ unit tests
- 10+ property-based tests

**Success Criteria:**
- ✅ 80%+ line coverage for `aml_structuring_detector.py`
- ✅ All detection algorithms tested
- ✅ Edge cases handled correctly

---

### Day 8: Insider Trading Detector Tests (Wednesday)

**Objective:** Achieve 80%+ coverage for `detect_insider_trading.py`

**Tasks:**

1. **Timing Correlation Tests**
   - `test_find_pre_announcement_trades()` - Complete implementation
   - `test_calculate_timing_risk()` - All scenarios
   - `test_detect_suspicious_timing()` - Pattern matching

2. **Coordinated Trading Tests**
   - `test_detect_coordinated_trades()` - Multiple traders
   - `test_cluster_trades_by_time()` - Time window clustering
   - `test_calculate_coordination_risk()` - Risk scoring

3. **Communication Analysis Tests**
   - `test_analyze_communications()` - Keyword detection
   - `test_link_communications_to_trades()` - Temporal linking
   - `test_calculate_communication_risk()` - Risk assessment

4. **Network Analysis Tests**
   - `test_build_trader_network()` - Graph construction
   - `test_find_insider_connections()` - Relationship detection
   - `test_calculate_network_risk()` - Network-based risk

**Deliverables:**
- Enhanced `test_detect_insider_trading.py` (600 lines total)
- 40+ comprehensive tests
- Integration with mock JanusGraph

**Success Criteria:**
- ✅ 80%+ line coverage for `detect_insider_trading.py`
- ✅ All detection patterns tested
- ✅ Complex scenarios validated

---

### Day 9: TBML Detector Tests (Thursday)

**Objective:** Achieve 80%+ coverage for `detect_tbml.py`

**Tasks:**

1. **Carousel Fraud Tests**
   - `test_detect_circular_loops()` - Loop detection
   - `test_calculate_loop_risk()` - Risk scoring
   - `test_find_carousel_patterns()` - Pattern matching

2. **Price Anomaly Tests**
   - `test_detect_over_invoicing()` - Over-pricing detection
   - `test_detect_under_invoicing()` - Under-pricing detection
   - `test_calculate_price_deviation()` - Deviation calculation

3. **Shell Company Tests**
   - `test_identify_shell_companies()` - Shell detection
   - `test_analyze_company_network()` - Network analysis
   - `test_calculate_shell_risk()` - Risk assessment

4. **Phantom Shipment Tests**
   - `test_detect_phantom_shipments()` - Non-existent goods
   - `test_validate_shipment_data()` - Data validation
   - `test_calculate_phantom_risk()` - Risk scoring

**Deliverables:**
- Enhanced `test_detect_tbml.py` (700 lines total)
- 45+ comprehensive tests
- Complex fraud scenario coverage

**Success Criteria:**
- ✅ 80%+ line coverage for `detect_tbml.py`
- ✅ All TBML patterns tested
- ✅ Multi-step fraud scenarios validated

---

### Day 10: Streaming Consumer Tests (Friday)

**Objective:** Test GraphConsumer and VectorConsumer with Pulsar

**Tasks:**

1. **GraphConsumer Tests** (`test_graph_consumer.py`)
   ```python
   class TestGraphConsumer:
       def test_initialization(self):
           """Test consumer initialization with Pulsar."""
           
       def test_process_person_event(self, mock_janusgraph):
           """Test processing person event to JanusGraph."""
           
       def test_batch_processing(self, mock_janusgraph):
           """Test batch processing with transaction commit."""
           
       def test_key_shared_subscription(self):
           """Test Pulsar Key_Shared subscription mode."""
           
       def test_idempotent_operations(self):
           """Test fold/coalesce pattern for idempotency."""
           
       def test_error_handling_with_nack(self):
           """Test NACK on processing errors."""
   ```

2. **VectorConsumer Tests** (`test_vector_consumer.py`)
   ```python
   class TestVectorConsumer:
       def test_initialization(self):
           """Test consumer initialization."""
           
       def test_generate_embeddings(self):
           """Test embedding generation from text."""
           
       def test_bulk_indexing(self, mock_opensearch):
           """Test bulk indexing to OpenSearch."""
           
       def test_entity_id_consistency(self):
           """Test same entity_id across systems."""
           
       def test_smart_update(self):
           """Test regenerate only if text changed."""
   ```

3. **Pulsar-Specific Feature Tests**
   - Test Key_Shared subscription (Pulsar-specific)
   - Test sequence_id deduplication (Pulsar-specific)
   - Test persistent:// topic protocol
   - Test partition key routing

**Deliverables:**
- `banking/streaming/tests/test_graph_consumer.py` (500 lines)
- `banking/streaming/tests/test_vector_consumer.py` (450 lines)
- 40+ consumer tests

**Success Criteria:**
- ✅ 80%+ coverage for both consumers
- ✅ Pulsar-specific features tested
- ✅ Error handling validated

---

### Day 11: DLQ Handler & Metrics Tests (Saturday)

**Objective:** Test DLQ retry logic and metrics collection

**Tasks:**

1. **DLQ Handler Tests** (`test_dlq_handler.py`)
   ```python
   class TestDLQHandler:
       def test_send_to_dlq(self):
           """Test sending failed message to DLQ."""
           
       def test_retry_with_backoff(self):
           """Test exponential backoff retry."""
           
       def test_max_retries_exceeded(self):
           """Test archive after max retries."""
           
       def test_process_dlq_batch(self):
           """Test batch processing from DLQ."""
           
       def test_retry_success(self):
           """Test successful retry and ACK."""
   ```

2. **Metrics Tests** (`test_metrics.py`)
   ```python
   class TestStreamingMetrics:
       def test_events_published_counter(self):
           """Test events published metric."""
           
       def test_publish_latency_histogram(self):
           """Test publish latency tracking."""
           
       def test_dlq_messages_counter(self):
           """Test DLQ message counting."""
           
       def test_prometheus_format(self):
           """Test Prometheus metrics output."""
   ```

3. **Retry Scenario Tests**
   - Transient failures (network timeout)
   - Permanent failures (invalid data)
   - Partial batch failures
   - DLQ overflow handling

**Deliverables:**
- `banking/streaming/tests/test_dlq_handler.py` (400 lines)
- `banking/streaming/tests/test_metrics.py` (300 lines)
- 35+ tests

**Success Criteria:**
- ✅ 80%+ coverage for DLQ handler
- ✅ 80%+ coverage for metrics
- ✅ All retry scenarios tested

---

### Day 12: Integration Tests & Validation (Sunday)

**Objective:** Create end-to-end integration tests with real Pulsar

**Tasks:**

1. **Pulsar Integration Tests** (`test_pulsar_integration.py`)
   ```python
   @pytest.mark.integration
   class TestPulsarIntegration:
       def test_producer_consumer_e2e(self, pulsar_container):
           """Test full producer → Pulsar → consumer flow."""
           
       def test_key_shared_ordering(self, pulsar_container):
           """Test entity-level ordering with Key_Shared."""
           
       def test_deduplication(self, pulsar_container):
           """Test Pulsar native deduplication."""
           
       def test_backpressure_handling(self, pulsar_container):
           """Test consumer backpressure."""
           
       def test_exactly_once_semantics(self, pulsar_container):
           """Test exactly-once delivery."""
   ```

2. **Testcontainers Setup**
   ```python
   @pytest.fixture(scope="module")
   def pulsar_container():
       """Start Pulsar container for integration tests."""
       with PulsarContainer("apachepulsar/pulsar:3.2.0") as pulsar:
           yield pulsar
   ```

3. **Analytics Integration Tests**
   - Enable skipped JanusGraph integration tests
   - Add testcontainers for JanusGraph
   - Test full detection workflows

4. **Coverage Validation**
   ```bash
   # Run full test suite with coverage
   pytest banking/analytics/tests/ banking/streaming/tests/ \
     --cov=banking.analytics --cov=banking.streaming \
     --cov-report=html --cov-report=term-missing \
     --cov-fail-under=80
   ```

**Deliverables:**
- `banking/streaming/tests/test_pulsar_integration.py` (600 lines)
- `banking/analytics/tests/test_janusgraph_integration.py` (400 lines)
- Integration test documentation

**Success Criteria:**
- ✅ All integration tests passing
- ✅ Analytics module: 80%+ coverage
- ✅ Streaming module: 80%+ coverage
- ✅ No failing tests

---

## Apache Pulsar Testing Specifics

### Key Differences from Kafka

| Feature | Kafka | Pulsar | Testing Impact |
|---------|-------|--------|----------------|
| **Subscription** | Consumer Groups | Key_Shared, Exclusive, Failover, Shared | Test subscription modes |
| **Deduplication** | Manual (idempotent producer) | Native (sequence_id) | Test built-in dedup |
| **Ordering** | Partition-level | Key-level (Key_Shared) | Test entity-level ordering |
| **Protocol** | kafka:// | pulsar:// or persistent:// | Use correct URLs |
| **CLI Tools** | kafka-console-* | pulsar-admin, pulsar-client | Use Pulsar CLI |
| **Testcontainers** | KafkaContainer | PulsarContainer | Use Pulsar container |

### Pulsar-Specific Test Scenarios

1. **Key_Shared Subscription Mode**
   ```python
   def test_key_shared_ordering():
       """Test that messages with same key go to same consumer."""
       # Create 2 consumers with Key_Shared
       # Send messages with same entity_id
       # Verify all go to same consumer
       # Verify ordering maintained
   ```

2. **Native Deduplication**
   ```python
   def test_pulsar_deduplication():
       """Test Pulsar's built-in deduplication."""
       # Send same message twice with same sequence_id
       # Verify only processed once
       # No manual dedup logic needed
   ```

3. **Persistent Topics**
   ```python
   def test_persistent_topics():
       """Test persistent:// topic protocol."""
       topic = "persistent://public/banking/persons-events"
       # Verify messages survive broker restart
   ```

4. **Pulsar CLI Integration**
   ```python
   def test_pulsar_admin_commands():
       """Test Pulsar admin operations."""
       # List topics
       # Check stats
       # Peek messages
       # Verify subscriptions
   ```

---

## Testing Tools & Dependencies

### Required Packages

```bash
# Install with uv (MANDATORY)
uv pip install pytest pytest-cov pytest-mock pytest-asyncio
uv pip install hypothesis  # Property-based testing
uv pip install testcontainers[pulsar]  # Pulsar integration tests
uv pip install pulsar-client>=3.4.0  # Apache Pulsar client
```

### Test Configuration

**pytest.ini additions:**
```ini
[pytest]
markers =
    analytics: Analytics module tests
    streaming: Streaming module tests
    pulsar: Pulsar-specific tests
    integration: Integration tests requiring services
    slow: Slow-running tests
```

### Coverage Configuration

**pyproject.toml additions:**
```toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/conftest.py",
]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

---

## Success Metrics

### Coverage Targets

| Module | Current | Target | Tests Added |
|--------|---------|--------|-------------|
| `aml_structuring_detector.py` | 0% | 80%+ | 40+ |
| `detect_insider_trading.py` | 0% | 80%+ | 40+ |
| `detect_tbml.py` | 0% | 80%+ | 45+ |
| `graph_consumer.py` | 0% | 80%+ | 25+ |
| `vector_consumer.py` | 0% | 80%+ | 25+ |
| `dlq_handler.py` | 0% | 80%+ | 20+ |
| `metrics.py` | 0% | 80%+ | 15+ |
| **Overall Analytics** | **0%** | **80%+** | **125+** |
| **Overall Streaming** | **28%** | **80%+** | **85+** |

### Quality Gates

- ✅ All tests passing (0 failures)
- ✅ Analytics coverage ≥ 80%
- ✅ Streaming coverage ≥ 80%
- ✅ No skipped integration tests (when services available)
- ✅ Property-based tests for critical algorithms
- ✅ Pulsar-specific features tested
- ✅ Documentation updated

---

## Risk Mitigation

### Potential Issues

1. **Pulsar Container Startup Time**
   - **Risk:** Slow test execution
   - **Mitigation:** Use module-scoped fixtures, parallel test execution

2. **JanusGraph Mock Complexity**
   - **Risk:** Mocks don't match real behavior
   - **Mitigation:** Validate mocks against real JanusGraph responses

3. **Flaky Integration Tests**
   - **Risk:** Tests fail intermittently
   - **Mitigation:** Add retries, proper wait conditions, cleanup

4. **Coverage Measurement Accuracy**
   - **Risk:** Coverage reports don't reflect actual testing
   - **Mitigation:** Manual code review, branch coverage analysis

---

## Deliverables Summary

### Code Artifacts

1. **Analytics Tests** (1,700+ lines)
   - `conftest.py` - Fixtures and mocks
   - `test_utils.py` - Test utilities
   - `test_aml_structuring_detector.py` - AML tests
   - Enhanced `test_detect_insider_trading.py` - Insider trading tests
   - Enhanced `test_detect_tbml.py` - TBML tests
   - `test_janusgraph_integration.py` - Integration tests

2. **Streaming Tests** (2,250+ lines)
   - `test_graph_consumer.py` - GraphConsumer tests
   - `test_vector_consumer.py` - VectorConsumer tests
   - `test_dlq_handler.py` - DLQ tests
   - `test_metrics.py` - Metrics tests
   - `test_pulsar_integration.py` - Pulsar integration tests

3. **Documentation** (500+ lines)
   - `banking/analytics/tests/README.md` - Analytics testing guide
   - `banking/streaming/tests/README.md` - Streaming testing guide
   - Updated `banking/streaming/README.md` - Pulsar testing section

### Reports

1. **Week 2 Progress Report** - Daily progress tracking
2. **Coverage Report** - HTML coverage report with line-by-line analysis
3. **Test Execution Report** - pytest HTML report with all test results

---

## Next Steps (Week 3)

After Week 2 completion:

1. **Week 3: Streaming Advanced Testing** (Days 13-18)
   - Performance testing (throughput, latency)
   - Chaos engineering (broker failures, network partitions)
   - Multi-consumer scenarios
   - Schema evolution testing

2. **Week 4: Exception Handling** (Days 19-25)
   - Custom exception hierarchy
   - Module-specific exception handling
   - Exception testing

3. **Week 5: Validation & Documentation** (Days 26-30)
   - Final validation
   - Documentation updates
   - Team training

---

## Conclusion

Week 2 will transform the Analytics and Streaming modules from minimal/no coverage to production-ready with 80%+ test coverage. The focus on Apache Pulsar-specific features ensures tests accurately reflect the actual streaming architecture.

**Expected Outcome:**
- Analytics: 0% → 80%+ coverage (125+ new tests)
- Streaming: 28% → 80%+ coverage (85+ new tests)
- All Pulsar-specific features tested
- Integration tests with real services
- Production-ready test infrastructure

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-11  
**Status:** Ready for Implementation