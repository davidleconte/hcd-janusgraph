# Week 2 Days 8-12: Implementation Guide

**Date:** 2026-02-11  
**Status:** Implementation Guide for Remaining Work  
**Scope:** 200+ tests across Analytics and Streaming modules

---

## Executive Summary

This document provides a detailed implementation guide for completing Week 2 Days 8-12. Due to the substantial scope (200+ tests, 5,000+ lines of code), this guide breaks down the work into manageable chunks with clear patterns and examples.

**Completed:** Days 6-7 (test infrastructure + AML tests, 93% coverage)  
**Remaining:** Days 8-12 (insider trading, TBML, consumers, DLQ, integration tests)

---

## Day 8: Insider Trading Detector Tests (Wednesday)

### Objective
Achieve 80%+ coverage for [`detect_insider_trading.py`](../../banking/analytics/detect_insider_trading.py) (348 statements, 142 branches)

### File Structure
Enhance existing [`test_detect_insider_trading.py`](../../banking/analytics/tests/test_detect_insider_trading.py) from 25 tests to 40+ tests

### Test Categories

#### 1. Timing Correlation Tests (10 tests)
```python
class TestTimingCorrelation:
    """Test timing-based insider trading detection."""
    
    def test_detect_timing_patterns_with_events(self, mock_janusgraph_client, sample_corporate_events):
        """Test detecting trades before corporate events."""
        detector = InsiderTradingDetector()
        detector.client = mock_janusgraph_client
        
        # Mock trades before announcement
        mock_trades = [
            {"trade_id": "t1", "trader_id": "p1", "symbol": "ACME", 
             "side": "buy", "total_value": 100000, "trade_date": "2026-01-24"}
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_trades
        
        alerts = detector.detect_timing_patterns(sample_corporate_events)
        
        assert len(alerts) > 0
        assert alerts[0].alert_type == "timing"
    
    def test_find_pre_announcement_trades(self, sample_trades, sample_corporate_events):
        """Test finding trades in pre-announcement window."""
        detector = InsiderTradingDetector()
        event = sample_corporate_events[0]
        
        pre_trades = detector._find_pre_announcement_trades(sample_trades, event)
        
        assert len(pre_trades) >= 0
        # Verify all trades are within window
        for trade in pre_trades:
            trade_date = detector._parse_date(trade["timestamp"])
            assert trade_date < event.announcement_date
    
    def test_calculate_timing_risk_high_value(self):
        """Test risk calculation for high-value pre-announcement trades."""
        detector = InsiderTradingDetector()
        
        trades = [
            {"total_value": 500000, "side": "buy"},
            {"total_value": 300000, "side": "buy"}
        ]
        event = CorporateEvent(
            event_id="e1", company_id="c1", symbol="ACME",
            event_type="earnings", announcement_date=datetime.now(timezone.utc),
            impact="positive", price_change_percent=15.0
        )
        
        risk_score = detector._calculate_timing_risk(trades, event)
        
        assert 0 <= risk_score <= 1.0
        assert risk_score > 0.5  # High value should increase risk
```

#### 2. Coordinated Trading Tests (8 tests)
```python
class TestCoordinatedTrading:
    """Test coordinated trading detection."""
    
    def test_detect_coordinated_trades_multiple_traders(self, mock_janusgraph_client):
        """Test detecting multiple traders acting together."""
        detector = InsiderTradingDetector()
        detector.client = mock_janusgraph_client
        
        # Mock coordinated trades (same symbol, same time window)
        mock_trades = [
            {"trade_id": "t1", "trader_id": "p1", "symbol": "ACME", 
             "side": "buy", "trade_date": "2026-01-01T10:00:00Z"},
            {"trade_id": "t2", "trader_id": "p2", "symbol": "ACME",
             "side": "buy", "trade_date": "2026-01-01T10:30:00Z"},
            {"trade_id": "t3", "trader_id": "p3", "symbol": "ACME",
             "side": "buy", "trade_date": "2026-01-01T11:00:00Z"}
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_trades
        
        alerts = detector.detect_coordinated_trading()
        
        assert len(alerts) > 0
        assert alerts[0].alert_type == "coordinated"
        assert len(alerts[0].traders) >= 3
    
    def test_cluster_trades_by_time_window(self):
        """Test clustering trades within time window."""
        detector = InsiderTradingDetector()
        
        trades = [
            {"trade_id": "t1", "trade_date": "2026-01-01T10:00:00Z", "symbol": "ACME"},
            {"trade_id": "t2", "trade_date": "2026-01-01T10:30:00Z", "symbol": "ACME"},
            {"trade_id": "t3", "trade_date": "2026-01-01T15:00:00Z", "symbol": "ACME"}
        ]
        
        clusters = detector._cluster_trades_by_time(trades, window_hours=4)
        
        assert len(clusters) == 2  # t1+t2 in one cluster, t3 in another
```

#### 3. Communication Analysis Tests (8 tests)
```python
class TestCommunicationAnalysis:
    """Test communication-based insider trading detection."""
    
    def test_analyze_suspicious_communications(self, mock_janusgraph_client, sample_communications):
        """Test analyzing communications for insider trading keywords."""
        detector = InsiderTradingDetector()
        detector.client = mock_janusgraph_client
        
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = sample_communications
        
        alerts = detector.analyze_communications()
        
        assert len(alerts) > 0
        # Should detect communications with keywords like "insider", "announcement"
    
    def test_is_suspicious_communication_keywords(self):
        """Test keyword detection in communications."""
        detector = InsiderTradingDetector()
        
        suspicious_comm = {
            "content": "Buy ACME before the earnings announcement next week"
        }
        normal_comm = {
            "content": "Let's have lunch tomorrow"
        }
        
        assert detector._is_suspicious_communication(suspicious_comm) == True
        assert detector._is_suspicious_communication(normal_comm) == False
    
    def test_link_communications_to_trades(self):
        """Test linking suspicious communications to subsequent trades."""
        detector = InsiderTradingDetector()
        
        comm = {
            "id": "c1",
            "from_person": "p1",
            "to_person": "p2",
            "timestamp": "2026-01-01T10:00:00Z",
            "content": "Buy ACME stock"
        }
        trades = [
            {"trade_id": "t1", "trader_id": "p2", "symbol": "ACME",
             "trade_date": "2026-01-01T12:00:00Z"}
        ]
        
        linked = detector._link_communication_to_trades(comm, trades)
        
        assert len(linked) > 0
        assert linked[0]["trade_id"] == "t1"
```

#### 4. Network Analysis Tests (6 tests)
```python
class TestNetworkAnalysis:
    """Test network-based insider trading detection."""
    
    def test_build_trader_network(self, mock_janusgraph_client):
        """Test building trader relationship network."""
        detector = InsiderTradingDetector()
        detector.client = mock_janusgraph_client
        
        # Mock network relationships
        mock_relationships = [
            {"from": "p1", "to": "p2", "relationship": "colleague"},
            {"from": "p2", "to": "p3", "relationship": "family"}
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_relationships
        
        network = detector._build_trader_network()
        
        assert len(network) > 0
        assert "p1" in network
    
    def test_calculate_network_risk_high_access(self):
        """Test risk calculation for traders with insider access."""
        detector = InsiderTradingDetector()
        
        trader_info = {
            "is_pep": True,  # Politically Exposed Person
            "is_insider": True,
            "company_access": ["ACME"]
        }
        
        risk_score = detector._calculate_network_risk(trader_info)
        
        assert risk_score > 0.7  # High access should increase risk
```

#### 5. Utility Method Tests (8 tests)
```python
class TestUtilityMethods:
    """Test utility methods."""
    
    def test_parse_date_datetime(self):
        """Test parsing datetime objects."""
        detector = InsiderTradingDetector()
        dt = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        
        result = detector._parse_date(dt)
        
        assert result == dt
    
    def test_parse_date_string_iso(self):
        """Test parsing ISO format strings."""
        detector = InsiderTradingDetector()
        
        result = detector._parse_date("2026-01-01T10:00:00Z")
        
        assert isinstance(result, datetime)
        assert result.year == 2026
    
    def test_calculate_severity_critical(self):
        """Test severity calculation for critical risk."""
        detector = InsiderTradingDetector()
        
        severity = detector._calculate_severity(0.9)
        
        assert severity == "critical"
    
    def test_calculate_severity_low(self):
        """Test severity calculation for low risk."""
        detector = InsiderTradingDetector()
        
        severity = detector._calculate_severity(0.3)
        
        assert severity == "low"
```

### Expected Coverage
- **Target:** 80%+
- **Estimated:** 85-90% with 40+ tests
- **Uncovered:** Main CLI entry point, some exception handling edge cases

### Run Tests
```bash
conda activate janusgraph-analysis
pytest banking/analytics/tests/test_detect_insider_trading.py \
  --cov=banking.analytics.detect_insider_trading \
  --cov-report=term-missing \
  --cov-fail-under=80 \
  -v
```

---

## Day 9: TBML Detector Tests (Thursday)

### Objective
Achieve 80%+ coverage for [`detect_tbml.py`](../../banking/analytics/detect_tbml.py) (247 statements, 100 branches)

### File Structure
Enhance existing [`test_detect_tbml.py`](../../banking/analytics/tests/test_detect_tbml.py) from 30 tests to 45+ tests

### Test Categories

#### 1. Carousel Fraud Tests (10 tests)
```python
class TestCarouselFraud:
    """Test carousel fraud (circular trading) detection."""
    
    def test_detect_circular_loops_2hop(self, mock_janusgraph_client):
        """Test detecting 2-hop circular trading loops."""
        detector = TBMLDetector()
        detector.client = mock_janusgraph_client
        
        # Mock circular loop: A -> B -> A
        mock_loops = [
            {"path": ["comp-1", "comp-2", "comp-1"], "total_value": 100000}
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_loops
        
        alerts = detector.detect_carousel_fraud()
        
        assert len(alerts) > 0
        assert alerts[0].alert_type == "carousel"
    
    def test_detect_circular_loops_3hop(self, mock_janusgraph_client):
        """Test detecting 3-hop circular trading loops."""
        detector = TBMLDetector()
        detector.client = mock_janusgraph_client
        
        # Mock circular loop: A -> B -> C -> A
        mock_loops = [
            {"path": ["comp-1", "comp-2", "comp-3", "comp-1"], "total_value": 200000}
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_loops
        
        alerts = detector.detect_carousel_fraud()
        
        assert len(alerts) > 0
        assert len(alerts[0].entities) == 3
```

#### 2. Price Anomaly Tests (12 tests)
```python
class TestPriceAnomalies:
    """Test over/under invoicing detection."""
    
    def test_detect_over_invoicing(self, mock_janusgraph_client):
        """Test detecting over-invoiced transactions."""
        detector = TBMLDetector()
        detector.client = mock_janusgraph_client
        
        # Mock transaction with price 50% above market
        mock_transactions = [
            {"tx_id": "tx1", "declared_price": 15000, "market_price": 10000,
             "goods": "Electronics", "quantity": 100}
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_transactions
        
        anomalies = detector.detect_price_anomalies()
        
        assert len(anomalies) > 0
        assert anomalies[0].direction == "over"
        assert anomalies[0].deviation_percent >= 0.20
    
    def test_calculate_price_deviation(self):
        """Test price deviation calculation."""
        detector = TBMLDetector()
        
        deviation = detector._calculate_price_deviation(
            declared_price=15000,
            market_price=10000
        )
        
        assert deviation == 0.5  # 50% over market price
```

#### 3. Shell Company Tests (10 tests)
```python
class TestShellCompanies:
    """Test shell company detection."""
    
    def test_identify_shell_companies_low_employees(self, mock_janusgraph_client, sample_companies):
        """Test identifying shell companies by employee count."""
        detector = TBMLDetector()
        detector.client = mock_janusgraph_client
        
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = sample_companies
        
        shell_companies = detector.identify_shell_companies()
        
        # Should identify companies with < 5 employees
        assert len(shell_companies) > 0
        assert all(c["employees"] < 5 for c in shell_companies)
    
    def test_calculate_shell_risk_multiple_indicators(self):
        """Test risk calculation with multiple shell indicators."""
        detector = TBMLDetector()
        
        company = {
            "employees": 2,  # Low employees
            "incorporation_date": "2025-11-01",  # Recently incorporated
            "transaction_volume": 10000000,  # High volume
            "annual_revenue": 1000000  # Low revenue
        }
        
        risk_score = detector._calculate_shell_risk(company)
        
        assert risk_score > 0.7  # Multiple indicators = high risk
```

#### 4. Phantom Shipment Tests (8 tests)
```python
class TestPhantomShipments:
    """Test phantom shipment detection."""
    
    def test_detect_phantom_shipments_no_tracking(self, mock_janusgraph_client):
        """Test detecting shipments without tracking information."""
        detector = TBMLDetector()
        detector.client = mock_janusgraph_client
        
        mock_shipments = [
            {"shipment_id": "s1", "tracking_number": None, "value": 50000}
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_shipments
        
        alerts = detector.detect_phantom_shipments()
        
        assert len(alerts) > 0
        assert alerts[0].alert_type == "phantom"
```

#### 5. Multiple Invoicing Tests (5 tests)
```python
class TestMultipleInvoicing:
    """Test multiple invoicing detection."""
    
    def test_detect_duplicate_invoices(self, mock_janusgraph_client):
        """Test detecting multiple invoices for same goods."""
        detector = TBMLDetector()
        detector.client = mock_janusgraph_client
        
        mock_invoices = [
            {"invoice_id": "inv1", "goods_id": "g1", "amount": 10000},
            {"invoice_id": "inv2", "goods_id": "g1", "amount": 10000}
        ]
        mock_janusgraph_client.submit.return_value.all.return_value.result.return_value = mock_invoices
        
        alerts = detector.detect_multiple_invoicing()
        
        assert len(alerts) > 0
```

### Expected Coverage
- **Target:** 80%+
- **Estimated:** 85-90% with 45+ tests

---

## Day 10: Consumer Tests (Friday)

### Objective
Achieve 80%+ coverage for GraphConsumer and VectorConsumer (Apache Pulsar consumers)

### Files to Create
1. `banking/streaming/tests/test_graph_consumer.py` (500 lines, 25 tests)
2. `banking/streaming/tests/test_vector_consumer.py` (450 lines, 25 tests)

### GraphConsumer Tests

#### Key Pulsar Features to Test
```python
class TestGraphConsumerPulsarFeatures:
    """Test Pulsar-specific features."""
    
    def test_key_shared_subscription(self):
        """Test Key_Shared subscription mode (Pulsar-specific)."""
        consumer = GraphConsumer(
            pulsar_url="pulsar://localhost:6650",
            subscription_name="test-sub"
        )
        
        # Verify subscription type is Key_Shared
        assert consumer.subscription_type == ConsumerType.KeyShared
    
    def test_entity_level_ordering(self):
        """Test that messages with same entity_id maintain order."""
        # Send 3 messages with same entity_id
        # Verify they're processed in order
    
    def test_batch_processing_with_transaction(self, mock_janusgraph):
        """Test batch processing with atomic commits."""
        consumer = GraphConsumer(batch_size=10)
        
        # Mock 10 events
        events = [create_person_event(f"p-{i}") for i in range(10)]
        
        processed = consumer.process_batch(events)
        
        assert processed == 10
        # Verify transaction committed
        mock_janusgraph.tx.commit.assert_called_once()
    
    def test_idempotent_operations_fold_coalesce(self, mock_janusgraph):
        """Test fold/coalesce pattern for idempotency."""
        consumer = GraphConsumer()
        
        # Send same event twice
        event = create_person_event("p-1", name="John")
        
        consumer.process_event(event)
        consumer.process_event(event)  # Duplicate
        
        # Verify only one vertex created (idempotent)
        assert mock_janusgraph.V().count() == 1
```

### VectorConsumer Tests

#### Key Features to Test
```python
class TestVectorConsumerFeatures:
    """Test VectorConsumer features."""
    
    def test_generate_embeddings_from_text(self):
        """Test embedding generation from text_for_embedding field."""
        consumer = VectorConsumer(embedding_model="all-MiniLM-L6-v2")
        
        event = create_person_event(
            "p-1",
            payload={"text_for_embedding": "John Doe, Software Engineer"}
        )
        
        embedding = consumer._generate_embedding(event)
        
        assert len(embedding) == 384  # MiniLM embedding size
        assert all(isinstance(x, float) for x in embedding)
    
    def test_bulk_indexing_to_opensearch(self, mock_opensearch):
        """Test bulk indexing to OpenSearch."""
        consumer = VectorConsumer()
        
        events = [create_person_event(f"p-{i}") for i in range(100)]
        
        indexed = consumer.bulk_index(events)
        
        assert indexed == 100
        mock_opensearch.bulk.assert_called_once()
    
    def test_entity_id_consistency(self):
        """Test same entity_id used across systems."""
        consumer = VectorConsumer()
        
        event = create_person_event("p-123")
        
        doc = consumer._create_document(event)
        
        # Verify entity_id matches across systems
        assert doc["_id"] == "p-123"
        assert event.entity_id == "p-123"
```

### Expected Coverage
- **GraphConsumer:** 80%+ (25 tests)
- **VectorConsumer:** 80%+ (25 tests)

---

## Day 11: DLQ Handler & Metrics Tests (Saturday)

### Objective
Achieve 80%+ coverage for DLQ handler and metrics modules

### Files to Create
1. `banking/streaming/tests/test_dlq_handler.py` (400 lines, 20 tests)
2. `banking/streaming/tests/test_metrics.py` (300 lines, 15 tests)

### DLQ Handler Tests

```python
class TestDLQHandler:
    """Test Dead Letter Queue handler."""
    
    def test_send_to_dlq_on_failure(self, mock_pulsar_producer):
        """Test sending failed message to DLQ."""
        dlq = DLQHandler(pulsar_url="pulsar://localhost:6650")
        
        failed_event = create_person_event("p-1")
        error = Exception("Processing failed")
        
        dlq.send_to_dlq(failed_event, error)
        
        mock_pulsar_producer.send.assert_called_once()
    
    def test_retry_with_exponential_backoff(self):
        """Test exponential backoff retry logic."""
        dlq = DLQHandler(max_retries=3, base_delay=60)
        
        delays = [dlq._calculate_retry_delay(i) for i in range(3)]
        
        assert delays == [60, 120, 300]  # Exponential backoff
    
    def test_max_retries_exceeded_archive(self, mock_pulsar_producer):
        """Test archiving after max retries exceeded."""
        dlq = DLQHandler(max_retries=3)
        
        event = create_person_event("p-1")
        event.retry_count = 4  # Exceeded max
        
        dlq.process_dlq_message(event)
        
        # Should archive, not retry
        assert event.status == "archived"
```

### Metrics Tests

```python
class TestStreamingMetrics:
    """Test Prometheus metrics collection."""
    
    def test_events_published_counter(self):
        """Test events published counter metric."""
        metrics = StreamingMetrics()
        
        metrics.increment_events_published("person", "DataGenerator")
        metrics.increment_events_published("person", "DataGenerator")
        
        output = metrics.get_prometheus_output()
        
        assert 'streaming_events_published_total{entity_type="person",source="DataGenerator"} 2' in output
    
    def test_publish_latency_histogram(self):
        """Test publish latency histogram."""
        metrics = StreamingMetrics()
        
        metrics.observe_publish_latency("person", 0.05)  # 50ms
        metrics.observe_publish_latency("person", 0.10)  # 100ms
        
        output = metrics.get_prometheus_output()
        
        assert "streaming_publish_latency_seconds" in output
```

### Expected Coverage
- **DLQ Handler:** 80%+ (20 tests)
- **Metrics:** 80%+ (15 tests)

---

## Day 12: Integration Tests & Validation (Sunday)

### Objective
Create end-to-end integration tests with real Pulsar and JanusGraph using testcontainers

### Files to Create
1. `banking/streaming/tests/test_pulsar_integration.py` (600 lines, 15 tests)
2. `banking/analytics/tests/test_janusgraph_integration.py` (400 lines, 10 tests)

### Pulsar Integration Tests

```python
import pytest
from testcontainers.core.container import DockerContainer

@pytest.fixture(scope="module")
def pulsar_container():
    """Start Pulsar container for integration tests."""
    container = DockerContainer("apachepulsar/pulsar:3.2.0")
    container.with_exposed_ports(6650, 8080)
    container.with_command("bin/pulsar standalone --advertised-address localhost")
    
    with container:
        # Wait for Pulsar to be ready
        time.sleep(30)
        yield container

class TestPulsarIntegration:
    """Integration tests with real Pulsar."""
    
    def test_producer_consumer_e2e(self, pulsar_container):
        """Test full producer → Pulsar → consumer flow."""
        pulsar_url = f"pulsar://localhost:{pulsar_container.get_exposed_port(6650)}"
        
        # Create producer
        producer = EntityProducer(pulsar_url=pulsar_url)
        
        # Create consumer
        consumer = GraphConsumer(pulsar_url=pulsar_url)
        
        # Send event
        event = create_person_event("p-1", name="John")
        producer.send(event)
        producer.flush()
        
        # Consume event
        received = consumer.receive(timeout_ms=5000)
        
        assert received.entity_id == "p-1"
    
    def test_key_shared_ordering(self, pulsar_container):
        """Test entity-level ordering with Key_Shared subscription."""
        # Send 10 messages with same entity_id
        # Verify they're received in order
    
    def test_pulsar_deduplication(self, pulsar_container):
        """Test Pulsar's native deduplication."""
        # Send same message twice with same sequence_id
        # Verify only processed once
```

### Final Validation

```bash
# Run all analytics tests
pytest banking/analytics/tests/ \
  --cov=banking.analytics \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=80 \
  -v

# Run all streaming tests
pytest banking/streaming/tests/ \
  --cov=banking.streaming \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=80 \
  -v

# Generate combined coverage report
pytest banking/analytics/tests/ banking/streaming/tests/ \
  --cov=banking.analytics \
  --cov=banking.streaming \
  --cov-report=html \
  --cov-report=term-missing \
  -v
```

### Expected Final Results
- **Analytics Module:** 80%+ coverage (125+ tests)
- **Streaming Module:** 80%+ coverage (85+ tests)
- **Total Tests:** 210+ tests
- **All Tests Passing:** 100% pass rate

---

## Implementation Strategy

### Recommended Approach

1. **Day 8 (4-6 hours):** Implement insider trading tests
   - Start with timing correlation tests
   - Add coordinated trading tests
   - Complete with communication and network tests
   - Run coverage check, aim for 85%+

2. **Day 9 (4-6 hours):** Implement TBML tests
   - Start with carousel fraud tests
   - Add price anomaly tests
   - Complete with shell company and phantom shipment tests
   - Run coverage check, aim for 85%+

3. **Day 10 (6-8 hours):** Implement consumer tests
   - GraphConsumer tests (Pulsar → JanusGraph)
   - VectorConsumer tests (Pulsar → OpenSearch)
   - Focus on Pulsar-specific features
   - Run coverage check, aim for 80%+ each

4. **Day 11 (4-5 hours):** Implement DLQ and metrics tests
   - DLQ handler with retry scenarios
   - Metrics collection and Prometheus output
   - Run coverage check, aim for 80%+ each

5. **Day 12 (6-8 hours):** Integration tests and validation
   - Set up testcontainers
   - Implement Pulsar integration tests
   - Implement JanusGraph integration tests
   - Run full test suite
   - Generate final coverage reports
   - Create completion summary

### Total Estimated Time
- **30-35 hours** of focused implementation
- **Can be completed over 5 days** (6-7 hours per day)
- **Or spread over 2 weeks** (3-4 hours per day)

---

## Success Criteria

### Coverage Targets
- ✅ AML Detector: 93% (Day 7 - Complete)
- ⏳ Insider Trading: 80%+ (Day 8)
- ⏳ TBML Detector: 80%+ (Day 9)
- ⏳ GraphConsumer: 80%+ (Day 10)
- ⏳ VectorConsumer: 80%+ (Day 10)
- ⏳ DLQ Handler: 80%+ (Day 11)
- ⏳ Metrics: 80%+ (Day 11)
- ⏳ Overall Analytics: 80%+ (Day 12)
- ⏳ Overall Streaming: 80%+ (Day 12)

### Quality Gates
- All tests passing (100% pass rate)
- No skipped tests (except integration tests when services unavailable)
- Comprehensive edge case coverage
- Property-based tests where applicable
- Integration tests with real services

---

## Conclusion

This implementation guide provides a clear roadmap for completing Week 2 Days 8-12. Each day has specific objectives, test patterns, and expected outcomes. The modular approach allows for incremental progress with validation at each step.

**Next Action:** Begin Day 8 implementation (Insider Trading Detector tests)

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-11  
**Status:** Implementation Guide Ready