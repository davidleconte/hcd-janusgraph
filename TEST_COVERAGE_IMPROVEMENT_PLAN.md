# Test Coverage Improvement Plan
# Achieving 70%+ Coverage While Maintaining Determinism

**Date:** 2026-04-07  
**Goal:** Increase test coverage for 6 modules from current levels to 70%+ while maintaining deterministic behavior  
**Estimated Effort:** 6-8 weeks  
**Priority:** High

---

## Executive Summary

This plan addresses test coverage gaps in 6 critical modules while ensuring all tests remain deterministic and reproducible. The strategy focuses on unit tests with mocked dependencies, deterministic test data, and fixed seeds.

### Current vs Target Coverage

| Module | Current | Target | Gap | Priority | Effort |
|--------|---------|--------|-----|----------|--------|
| `streaming` | 28% | 70%+ | 42% | P0 | 2 weeks |
| `aml` | 25% | 70%+ | 45% | P0 | 2 weeks |
| `compliance` | 25% | 70%+ | 45% | P1 | 1 week |
| `fraud` | 23% | 70%+ | 47% | P0 | 2 weeks |
| `data_generators.patterns` | 13% | 70%+ | 57% | P1 | 1 week |
| `analytics` | 0% | 70%+ | 70% | P1 | 1 week |

**Total Effort:** 9 weeks (can be parallelized to 6-8 weeks)

---

## Determinism Principles

### Core Requirements

1. **Fixed Seeds** - All random operations use fixed seeds
2. **Mocked External Dependencies** - No real Pulsar/JanusGraph/OpenSearch in unit tests
3. **Deterministic Time** - Use fixed timestamps, not `datetime.now()`
4. **Reproducible Data** - Same inputs always produce same outputs
5. **No Network I/O** - All external calls mocked
6. **Isolated Tests** - No shared state between tests

### Test Categories

```python
# Unit Tests (70% of coverage target)
- Pure logic testing
- Mocked dependencies
- Fast execution (<1s per test)
- No external services

# Integration Tests (existing, 30% of coverage)
- Real services (already exist)
- E2E workflows
- Slower execution
- Covered by existing 202 E2E tests
```

---

## Module 1: Streaming Module (28% → 70%+)

### Current State
- **Files:** `producer.py`, `graph_consumer.py`, `vector_consumer.py`, `dlq_handler.py`, `metrics.py`
- **Current Coverage:** 28% (integration-tested via 202 E2E tests)
- **Gap:** Missing unit tests for edge cases, error handling, retry logic

### Test Strategy

#### 1.1 Producer Tests (`test_producer_unit.py`)

```python
"""Unit tests for EntityProducer with mocked Pulsar."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from banking.streaming.producer import EntityProducer
from banking.streaming.events import EntityEvent

class TestEntityProducerUnit:
    """Unit tests for EntityProducer (deterministic, no real Pulsar)."""
    
    @pytest.fixture
    def mock_pulsar_client(self):
        """Mock Pulsar client for deterministic testing."""
        with patch('banking.streaming.producer.pulsar') as mock_pulsar:
            mock_client = MagicMock()
            mock_producer = MagicMock()
            mock_client.create_producer.return_value = mock_producer
            mock_pulsar.Client.return_value = mock_client
            mock_pulsar.CompressionType.ZSTD = 'ZSTD'
            yield mock_pulsar, mock_client, mock_producer
    
    def test_producer_initialization(self, mock_pulsar_client):
        """Test producer initializes with correct config."""
        mock_pulsar, mock_client, _ = mock_pulsar_client
        
        producer = EntityProducer(
            pulsar_url="pulsar://test:6650",
            namespace="test/banking",
            batch_size=500,
            compression=True
        )
        
        assert producer.pulsar_url == "pulsar://test:6650"
        assert producer.namespace == "test/banking"
        assert producer.batch_size == 500
        assert producer._connected is True
        mock_pulsar.Client.assert_called_once()
    
    def test_get_topic_routing(self, mock_pulsar_client):
        """Test topic routing logic (deterministic)."""
        _, _, _ = mock_pulsar_client
        producer = EntityProducer()
        
        # Test entity type to topic mapping
        assert producer._get_topic("person") == "persistent://public/banking/persons-events"
        assert producer._get_topic("company") == "persistent://public/banking/companies-events"
        assert producer._get_topic("account") == "persistent://public/banking/accounts-events"
        assert producer._get_topic("transaction") == "persistent://public/banking/transactions-events"
    
    def test_send_event_success(self, mock_pulsar_client):
        """Test successful event send (deterministic)."""
        _, _, mock_producer = mock_pulsar_client
        producer = EntityProducer()
        
        event = EntityEvent(
            entity_id="test-123",
            event_type="create",
            entity_type="person",
            payload={"name": "Test User"},
            timestamp="2026-01-01T00:00:00Z"  # Fixed timestamp
        )
        
        producer.send(event)
        
        # Verify producer.send was called with correct args
        mock_producer.send.assert_called_once()
        call_args = mock_producer.send.call_args
        assert call_args.kwargs['partition_key'] == "test-123"
    
    def test_send_event_not_connected(self, mock_pulsar_client):
        """Test send fails when not connected."""
        _, _, _ = mock_pulsar_client
        producer = EntityProducer()
        producer._connected = False
        
        event = EntityEvent(
            entity_id="test-123",
            event_type="create",
            entity_type="person",
            payload={}
        )
        
        with pytest.raises(RuntimeError, match="Not connected to Pulsar"):
            producer.send(event)
    
    def test_send_batch_groups_by_topic(self, mock_pulsar_client):
        """Test batch send groups events by topic (deterministic)."""
        _, _, mock_producer = mock_pulsar_client
        producer = EntityProducer()
        
        events = [
            EntityEvent(entity_id=f"p-{i}", event_type="create", 
                       entity_type="person", payload={}) 
            for i in range(5)
        ] + [
            EntityEvent(entity_id=f"c-{i}", event_type="create",
                       entity_type="company", payload={})
            for i in range(3)
        ]
        
        results = producer.send_batch(events)
        
        # Should have sent to 2 topics
        assert len(results) == 2
        assert results.get("persistent://public/banking/persons-events") == 5
        assert results.get("persistent://public/banking/companies-events") == 3
    
    def test_connection_failure_handling(self, mock_pulsar_client):
        """Test connection failure raises RuntimeError."""
        mock_pulsar, _, _ = mock_pulsar_client
        mock_pulsar.Client.side_effect = Exception("Connection refused")
        
        with pytest.raises(RuntimeError, match="Failed to connect to Pulsar"):
            EntityProducer()
    
    def test_producer_context_manager(self, mock_pulsar_client):
        """Test producer works as context manager."""
        _, mock_client, _ = mock_pulsar_client
        
        with EntityProducer() as producer:
            assert producer._connected is True
        
        # Verify cleanup called
        mock_client.close.assert_called_once()
```

**Coverage Target:** 70%+ for `producer.py`  
**Test Count:** 15-20 unit tests  
**Determinism:** ✅ All mocked, fixed timestamps, no network I/O

#### 1.2 Consumer Tests (`test_graph_consumer_unit.py`, `test_vector_consumer_unit.py`)

Similar pattern:
- Mock Pulsar consumer
- Mock JanusGraph/OpenSearch clients
- Test message processing logic
- Test error handling and DLQ routing
- Test metrics collection

#### 1.3 DLQ Handler Tests (`test_dlq_handler_unit.py`)

- Test DLQ message routing
- Test retry logic with fixed delays
- Test max retry limits
- Test message expiration

**Estimated Effort:** 2 weeks  
**Files to Create:**
- `banking/streaming/tests/test_producer_unit.py` (new)
- `banking/streaming/tests/test_graph_consumer_unit.py` (new)
- `banking/streaming/tests/test_vector_consumer_unit.py` (new)
- `banking/streaming/tests/test_dlq_handler_unit.py` (new)
- `banking/streaming/tests/test_metrics_unit.py` (new)

---

## Module 2: AML Module (25% → 70%+)

### Current State
- **Files:** `structuring_detection.py`, `enhanced_structuring_detection.py`, `sanctions_screening.py`
- **Current Coverage:** 25% (integration-tested)
- **Gap:** Missing unit tests for detection algorithms

### Test Strategy

#### 2.1 Structuring Detection Tests (`test_structuring_detection_unit.py`)

```python
"""Unit tests for StructuringDetector with mocked JanusGraph."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from banking.aml.structuring_detection import StructuringDetector, StructuringPattern

class TestStructuringDetectorUnit:
    """Unit tests for StructuringDetector (deterministic, no real graph)."""
    
    @pytest.fixture
    def mock_graph_connection(self):
        """Mock JanusGraph connection for deterministic testing."""
        with patch('banking.aml.structuring_detection.DriverRemoteConnection') as mock_conn:
            mock_traversal = MagicMock()
            mock_conn.return_value = mock_traversal
            yield mock_conn, mock_traversal
    
    @pytest.fixture
    def detector(self, mock_graph_connection):
        """Create detector with mocked connection."""
        detector = StructuringDetector(
            janusgraph_host="localhost",
            janusgraph_port=18182,
            use_ssl=False
        )
        return detector
    
    def test_detector_initialization(self, detector):
        """Test detector initializes with correct thresholds."""
        assert detector.ctr_threshold == Decimal("10000.00")
        assert detector.suspicious_threshold == Decimal("9000.00")
        assert detector.graph_url == "ws://localhost:18182/gremlin"
    
    def test_custom_ctr_threshold(self, mock_graph_connection):
        """Test custom CTR threshold (deterministic)."""
        detector = StructuringDetector(ctr_threshold=Decimal("5000.00"))
        assert detector.ctr_threshold == Decimal("5000.00")
        assert detector.suspicious_threshold == Decimal("4500.00")  # 90% of threshold
    
    def test_detect_smurfing_no_transactions(self, detector, mock_graph_connection):
        """Test smurfing detection with no suspicious transactions."""
        _, mock_traversal = mock_graph_connection
        
        # Mock empty transaction list
        mock_g = MagicMock()
        mock_g.V().has().out_e().has().has().project().by().by().by().by().toList.return_value = []
        detector._g = mock_g
        
        patterns = detector.detect_smurfing("ACC-001", time_window_hours=24)
        
        assert patterns == []
    
    def test_detect_smurfing_below_threshold(self, detector, mock_graph_connection):
        """Test smurfing detection with transactions below min count."""
        _, mock_traversal = mock_graph_connection
        
        # Mock 2 transactions (below min_transactions=3)
        mock_g = MagicMock()
        mock_g.V().has().out_e().has().has().project().by().by().by().by().toList.return_value = [
            {"id": "tx1", "amount": 9500.0, "timestamp": 1704067200000, "to_account": "ACC-002"},
            {"id": "tx2", "amount": 9800.0, "timestamp": 1704070800000, "to_account": "ACC-003"}
        ]
        detector._g = mock_g
        
        patterns = detector.detect_smurfing("ACC-001", time_window_hours=24, min_transactions=3)
        
        assert patterns == []
    
    def test_detect_smurfing_pattern_found(self, detector, mock_graph_connection):
        """Test smurfing pattern detection (deterministic)."""
        _, mock_traversal = mock_graph_connection
        
        # Mock 5 suspicious transactions (deterministic data)
        mock_g = MagicMock()
        transactions = [
            {"id": f"tx{i}", "amount": 9500.0 + (i * 100), 
             "timestamp": 1704067200000 + (i * 3600000), "to_account": f"ACC-{i+2}"}
            for i in range(5)
        ]
        mock_g.V().has().out_e().has().has().project().by().by().by().by().toList.return_value = transactions
        detector._g = mock_g
        
        patterns = detector.detect_smurfing("ACC-001", time_window_hours=24, min_transactions=3)
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "smurfing"
        assert len(pattern.transaction_ids) == 5
        assert pattern.total_amount > Decimal("47500.00")  # Sum of amounts
    
    def test_confidence_score_calculation(self, detector):
        """Test confidence score calculation (deterministic)."""
        # Test with high-confidence pattern
        transactions = [
            {"amount": 9900.0, "timestamp": 1704067200000},
            {"amount": 9950.0, "timestamp": 1704070800000},
            {"amount": 9980.0, "timestamp": 1704074400000},
            {"amount": 9990.0, "timestamp": 1704078000000}
        ]
        
        confidence = detector._calculate_confidence(transactions)
        
        # High confidence: amounts very close to threshold, regular timing
        assert confidence >= 0.85
    
    def test_risk_level_assignment(self, detector):
        """Test risk level assignment based on confidence (deterministic)."""
        assert detector._get_risk_level(0.95) == "critical"
        assert detector._get_risk_level(0.80) == "high"
        assert detector._get_risk_level(0.65) == "medium"
        assert detector._get_risk_level(0.40) == "low"
    
    def test_connection_retry_logic(self, detector, mock_graph_connection):
        """Test connection retry with exponential backoff."""
        mock_conn, _ = mock_graph_connection
        
        # First 2 attempts fail, 3rd succeeds
        mock_conn.side_effect = [
            Exception("Connection refused"),
            Exception("Connection refused"),
            MagicMock()
        ]
        
        # Should succeed after retries
        detector.connect()
        
        assert mock_conn.call_count == 3
    
    def test_circuit_breaker_opens_on_failures(self, detector):
        """Test circuit breaker opens after threshold failures."""
        # Simulate 5 consecutive failures
        for _ in range(5):
            detector._breaker.record_failure()
        
        # Circuit should be open
        assert detector._breaker.state.value == "open"
        assert not detector._breaker.allow_request()
```

**Coverage Target:** 70%+ for `structuring_detection.py`  
**Test Count:** 20-25 unit tests  
**Determinism:** ✅ All mocked, fixed timestamps, deterministic calculations

#### 2.2 Sanctions Screening Tests

Similar pattern for sanctions screening with mocked data.

**Estimated Effort:** 2 weeks  
**Files to Create:**
- `banking/aml/tests/test_structuring_detection_unit.py` (new)
- `banking/aml/tests/test_enhanced_structuring_unit.py` (new)
- `banking/aml/tests/test_sanctions_screening_unit.py` (new)

---

## Module 3: Compliance Module (25% → 70%+)

### Current State
- **Files:** `audit_logger.py`, `compliance_reporter.py`
- **Current Coverage:** 25%
- **Gap:** Missing unit tests for report generation, log parsing

### Test Strategy

#### 3.1 Audit Logger Tests (`test_audit_logger_unit.py`)

```python
"""Unit tests for AuditLogger (deterministic)."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from banking.compliance.audit_logger import (
    AuditLogger, AuditEvent, AuditEventType, AuditSeverity
)

class TestAuditLoggerUnit:
    """Unit tests for AuditLogger (deterministic, no file I/O)."""
    
    @pytest.fixture
    def mock_file_system(self):
        """Mock file system for deterministic testing."""
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                yield mock_file, mock_mkdir
    
    @pytest.fixture
    def logger(self, mock_file_system):
        """Create audit logger with mocked file system."""
        return AuditLogger(log_dir="/tmp/test-logs")
    
    def test_logger_initialization(self, logger):
        """Test logger initializes with correct config."""
        assert logger.log_dir == Path("/tmp/test-logs")
    
    def test_log_event_creates_structured_json(self, logger, mock_file_system):
        """Test event logging creates structured JSON (deterministic)."""
        mock_file, _ = mock_file_system
        
        event = AuditEvent(
            timestamp="2026-01-01T00:00:00Z",  # Fixed timestamp
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test-user",
            resource="test-resource",
            action="read",
            result="success",
            metadata={"ip": "127.0.0.1"}
        )
        
        logger.log_event(event)
        
        # Verify JSON was written
        mock_file().write.assert_called()
        written_data = mock_file().write.call_args[0][0]
        parsed = json.loads(written_data)
        
        assert parsed["event_type"] == "data_access"
        assert parsed["user"] == "test-user"
        assert parsed["timestamp"] == "2026-01-01T00:00:00Z"
    
    def test_log_data_access(self, logger, mock_file_system):
        """Test data access logging helper (deterministic)."""
        logger.log_data_access(
            user="analyst@example.com",
            resource="customer:12345",
            action="query",
            result="success"
        )
        
        mock_file, _ = mock_file_system
        mock_file().write.assert_called()
    
    def test_log_authentication(self, logger, mock_file_system):
        """Test authentication logging (deterministic)."""
        logger.log_authentication(
            user="admin@example.com",
            action="login",
            result="success",
            mfa_used=True
        )
        
        mock_file, _ = mock_file_system
        mock_file().write.assert_called()
    
    def test_log_gdpr_request(self, logger, mock_file_system):
        """Test GDPR request logging (deterministic)."""
        logger.log_gdpr_request(
            user="user@example.com",
            request_type="data_access",
            subject_id="customer:12345"
        )
        
        mock_file, _ = mock_file_system
        mock_file().write.assert_called()
    
    def test_pii_sanitization(self, logger):
        """Test PII is sanitized in logs (deterministic)."""
        event = AuditEvent(
            timestamp="2026-01-01T00:00:00Z",
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user="test-user",
            resource="test-resource",
            action="read",
            result="success",
            metadata={
                "email": "user@example.com",
                "ssn": "123-45-6789",
                "credit_card": "4111-1111-1111-1111"
            }
        )
        
        sanitized = logger._sanitize_pii(event)
        
        # PII should be redacted
        assert "[REDACTED-EMAIL]" in str(sanitized.metadata)
        assert "[REDACTED-SSN]" in str(sanitized.metadata)
        assert "[REDACTED-CC]" in str(sanitized.metadata)
```

**Coverage Target:** 70%+ for `audit_logger.py`  
**Test Count:** 15-20 unit tests  
**Determinism:** ✅ Mocked file I/O, fixed timestamps

#### 3.2 Compliance Reporter Tests

Similar pattern for compliance report generation.

**Estimated Effort:** 1 week  
**Files to Create:**
- `banking/compliance/tests/test_audit_logger_unit.py` (new)
- `banking/compliance/tests/test_compliance_reporter_unit.py` (new)

---

## Module 4: Fraud Module (23% → 70%+)

### Test Strategy

Similar to AML module:
- Mock JanusGraph and OpenSearch
- Test fraud detection algorithms with deterministic data
- Test velocity checks, network analysis, behavioral analysis
- Test risk scoring calculations

**Estimated Effort:** 2 weeks  
**Files to Create:**
- `banking/fraud/tests/test_fraud_detection_unit.py` (new)
- `banking/fraud/tests/test_fraud_models_unit.py` (new)
- `banking/fraud/tests/test_velocity_checks_unit.py` (new)

---

## Module 5: Data Generators Patterns (13% → 70%+)

### Test Strategy

```python
"""Unit tests for pattern injection (deterministic)."""

class TestPatternInjectionUnit:
    """Unit tests for fraud/AML pattern injection."""
    
    def test_smurfing_pattern_injection(self):
        """Test smurfing pattern injection with fixed seed."""
        generator = PatternGenerator(seed=42)  # Fixed seed
        
        persons = [Person(id=f"p-{i}", name=f"Person {i}") for i in range(10)]
        accounts = [Account(id=f"a-{i}", owner=f"p-{i}") for i in range(10)]
        
        # Inject pattern with deterministic behavior
        transactions = generator.inject_smurfing_pattern(
            accounts=accounts,
            pattern_count=1,
            seed=42  # Explicit seed
        )
        
        # Verify deterministic output
        assert len(transactions) > 0
        assert all(tx.amount < 10000 for tx in transactions)
        
        # Re-run with same seed should produce identical results
        transactions2 = generator.inject_smurfing_pattern(
            accounts=accounts,
            pattern_count=1,
            seed=42
        )
        
        assert transactions == transactions2  # Deterministic
```

**Estimated Effort:** 1 week  
**Files to Create:**
- `banking/data_generators/patterns/tests/test_pattern_injection_unit.py` (new)

---

## Module 6: Analytics Module (0% → 70%+)

### Test Strategy

```python
"""Unit tests for UBO discovery (deterministic)."""

class TestUBODiscoveryUnit:
    """Unit tests for UBO discovery with mocked graph."""
    
    @pytest.fixture
    def mock_graph(self):
        """Mock graph with deterministic ownership structure."""
        # Create deterministic ownership graph
        pass
    
    def test_ubo_discovery_simple_chain(self, mock_graph):
        """Test UBO discovery with simple ownership chain."""
        # Person A -> Company B -> Company C
        # UBO should be Person A
        pass
    
    def test_ubo_discovery_complex_structure(self, mock_graph):
        """Test UBO discovery with complex ownership."""
        # Multiple layers, shell companies, circular ownership
        pass
```

**Estimated Effort:** 1 week  
**Files to Create:**
- `banking/analytics/tests/test_ubo_discovery_unit.py` (new)

---

## Implementation Timeline

### Phase 1: Streaming Module (Weeks 1-2)
- Create unit tests for producer, consumers, DLQ handler
- Target: 70%+ coverage
- Verify deterministic behavior

### Phase 2: AML Module (Weeks 3-4)
- Create unit tests for structuring detection, sanctions screening
- Target: 70%+ coverage
- Verify deterministic behavior

### Phase 3: Fraud Module (Weeks 5-6)
- Create unit tests for fraud detection algorithms
- Target: 70%+ coverage
- Verify deterministic behavior

### Phase 4: Compliance, Patterns, Analytics (Weeks 7-9)
- Create unit tests for remaining modules
- Target: 70%+ coverage for each
- Verify deterministic behavior

### Phase 5: Integration & Verification (Week 9)
- Run full test suite
- Verify coverage targets met
- Verify deterministic behavior maintained
- Update coverage baselines

---

## Determinism Verification Checklist

For each new test file:

- [ ] All random operations use fixed seeds
- [ ] All timestamps are fixed (no `datetime.now()`)
- [ ] All external dependencies are mocked
- [ ] No network I/O in unit tests
- [ ] Tests pass consistently (run 10 times)
- [ ] Tests produce identical output with same inputs
- [ ] No flaky tests (timing-dependent)
- [ ] No shared state between tests
- [ ] Fixtures properly isolated
- [ ] Cleanup in teardown methods

---

## CI/CD Integration

### Update `.github/workflows/quality-gates.yml`

```yaml
- name: Run tests with coverage
  run: |
    PYTHONPATH=. pytest tests/ banking/ -v \
      --cov=src --cov=banking \
      --cov-report=xml \
      --cov-report=json \
      --cov-fail-under=70 \
      --timeout=120 \
      -k "not slow and not integration"

- name: Verify per-module coverage
  run: |
    python scripts/validation/check_module_coverage.py \
      --coverage-file coverage.json \
      --min-coverage 70 \
      --modules streaming,aml,compliance,fraud,data_generators.patterns,analytics
```

### Update `pyproject.toml`

```toml
[tool.coverage.report]
# Enforce 70% minimum per module
fail_under = 70

[tool.pytest.ini_options]
# Add new test paths
testpaths = [
    "tests",
    "banking/streaming/tests",
    "banking/aml/tests",
    "banking/compliance/tests",
    "banking/fraud/tests",
    "banking/data_generators/patterns/tests",
    "banking/analytics/tests"
]
```

---

## Success Criteria

### Coverage Targets Met
- [ ] `streaming`: 70%+ (from 28%)
- [ ] `aml`: 70%+ (from 25%)
- [ ] `compliance`: 70%+ (from 25%)
- [ ] `fraud`: 70%+ (from 23%)
- [ ] `data_generators.patterns`: 70%+ (from 13%)
- [ ] `analytics`: 70%+ (from 0%)

### Determinism Maintained
- [ ] All tests pass consistently (10 consecutive runs)
- [ ] No flaky tests introduced
- [ ] Deterministic pipeline still passes
- [ ] Baseline checksums unchanged

### Quality Gates
- [ ] CI passes with new tests
- [ ] No increase in test execution time (>10%)
- [ ] All tests properly documented
- [ ] Code review approved

---

## Risk Mitigation

### Risk 1: Breaking Deterministic Behavior
**Mitigation:** Run deterministic pipeline after each module completion

### Risk 2: Test Execution Time
**Mitigation:** Keep unit tests fast (<1s each), use mocks extensively

### Risk 3: Flaky Tests
**Mitigation:** Run each test 10 times before merging, fix any intermittent failures

### Risk 4: Coverage Regression
**Mitigation:** Enforce coverage gates in CI, block PRs that reduce coverage

---

## Next Steps

1. **Review and Approve Plan** (1 day)
2. **Set Up Test Infrastructure** (2 days)
   - Create test directory structure
   - Set up fixtures and mocks
   - Configure CI updates
3. **Begin Phase 1: Streaming Module** (2 weeks)
4. **Continue with remaining phases** (6-7 weeks)
5. **Final verification and documentation** (1 week)

---

**Total Timeline:** 9 weeks  
**Can be parallelized to:** 6-8 weeks with multiple developers  
**Priority:** High (addresses audit findings)  
**Owner:** Development Team  
**Reviewer:** QA Team + Platform Engineering
