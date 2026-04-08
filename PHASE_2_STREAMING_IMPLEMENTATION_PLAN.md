# Phase 2: Streaming Module Implementation Plan

**Date:** 2026-04-08  
**Status:** 🚧 IN PROGRESS  
**Target:** 80-94% → 100% coverage  
**Current:** 423 passing tests, 6 failing, 3 errors

---

## Current Coverage Analysis

### Coverage by File

| File | Coverage | Lines Missed | Priority |
|------|----------|--------------|----------|
| `producer.py` | 94% | 10 lines | Low (nearly complete) |
| `metrics.py` | 90% | 18 lines | Low |
| `vector_consumer.py` | 85% | 36 lines | Medium |
| `graph_consumer.py` | 84% | 40 lines | Medium |
| `events.py` | 81% | 20 lines | Medium |
| `dlq_handler.py` | 80% | 34 lines | Medium |
| `entity_converter.py` | 79% | 9 lines | Medium |
| `streaming_orchestrator.py` | 71% | 50 lines | **High** (most work needed) |

**Average:** ~83% (need +17% to reach 100%)

---

## Issues to Fix First

### Failing Tests (6)

1. **test_disconnect_closes_connections** - `graph_consumer_unit.py`
   - Issue: Expected 'close' to have been called
   - Fix: Update mock assertion

2. **test_get_metric** - `metrics_unit.py`
   - Issue: Mock method mismatch (get() vs __getitem__())
   - Fix: Update mock to use correct method

3. **test_get_producer_with_compression** - `producer_unit.py`
   - Issue: CompressionType enum vs string comparison
   - Fix: Update assertion to compare enum values

4. **test_stats_finalization** - `streaming_orchestrator.py`
   - Issue: generation_time_seconds is 0.0
   - Fix: Mock time.time() to return different values

5. **test_full_generation_cycle** - `streaming_orchestrator.py`
   - Issue: Invalid seed 12345 (only 42, 123, 999 allowed)
   - Fix: Use approved seed (42)

6. **test_reproducibility_with_seed** - `streaming_orchestrator.py`
   - Issue: Invalid seed 12345 (only 42, 123, 999 allowed)
   - Fix: Use approved seed (42)

### Errors (3)

1. **test_send_to_dlq_on_processing_error** - Missing `DLQHandler` import
2. **test_retry_logic_on_transient_error** - Missing `DLQHandler` import
3. **test_metrics_incremented_on_success** - Missing `Counter` import

---

## Implementation Strategy

### Step 1: Fix Failing Tests (Priority 1)

**Estimated Time:** 2-3 hours

1. Fix seed validation issues (2 tests)
2. Fix mock assertions (3 tests)
3. Fix time mocking (1 test)
4. Fix missing imports (3 errors)

### Step 2: Add Coverage Tests (Priority 2)

**Estimated Time:** 1 week (40 hours)

#### 2.1 streaming_orchestrator.py (71% → 100%)

**Need:** ~15-20 tests

Missing coverage areas:
- Lines 91, 94-98: Initialization edge cases
- Lines 179-187: Error handling in generation
- Lines 203, 218, 240: Cleanup operations
- Lines 274, 299: Stats collection edge cases
- Lines 310-322, 326-341, 345-359: Pattern generation paths
- Lines 407-410: Finalization edge cases

**Tests to add:**
```python
# Error handling
def test_generation_with_invalid_config()
def test_generation_with_missing_generators()
def test_cleanup_on_generation_failure()

# Pattern generation
def test_pattern_generation_all_types()
def test_pattern_generation_selective()
def test_pattern_generation_with_errors()

# Stats collection
def test_stats_with_zero_records()
def test_stats_with_large_numbers()
def test_stats_memory_tracking()

# Edge cases
def test_concurrent_generation_calls()
def test_generation_with_mock_producer()
def test_generation_without_streaming()
```

#### 2.2 dlq_handler.py (80% → 100%)

**Need:** ~10 tests

Missing coverage areas:
- Lines 28-34: Initialization edge cases
- Lines 206-208, 258-260: Error handling
- Lines 311-314: Retry logic edge cases
- Lines 332-369: DLQ processing paths
- Lines 470, 478: Cleanup operations

**Tests to add:**
```python
def test_dlq_with_invalid_topic()
def test_dlq_max_retries_exceeded()
def test_dlq_message_expiration()
def test_dlq_batch_processing()
def test_dlq_cleanup_on_shutdown()
```

#### 2.3 graph_consumer.py (84% → 100%)

**Need:** ~8 tests

Missing coverage areas:
- Lines 29-31, 39-40: Initialization
- Lines 192, 196: Connection handling
- Lines 229-233: Error recovery
- Lines 267, 282, 315: Processing edge cases
- Lines 366-372, 392: Metrics collection
- Lines 420-427: Cleanup
- Lines 497-504, 538-560: Advanced features

**Tests to add:**
```python
def test_consumer_with_invalid_config()
def test_consumer_reconnect_on_failure()
def test_consumer_batch_processing()
def test_consumer_message_ordering()
def test_consumer_graceful_shutdown()
```

#### 2.4 vector_consumer.py (85% → 100%)

**Need:** ~8 tests

Similar to graph_consumer.py

#### 2.5 events.py (81% → 100%)

**Need:** ~5 tests

Missing coverage areas:
- Lines 35, 51-65: Event creation edge cases
- Lines 73-76: Validation
- Lines 205-216: Serialization edge cases

**Tests to add:**
```python
def test_event_with_invalid_type()
def test_event_with_missing_fields()
def test_event_serialization_edge_cases()
def test_event_deserialization_errors()
```

#### 2.6 entity_converter.py (79% → 100%)

**Need:** ~5 tests

Missing coverage areas:
- Lines 61, 95, 122, 124, 128, 130, 132, 135-140: Conversion edge cases

**Tests to add:**
```python
def test_convert_with_invalid_entity_type()
def test_convert_with_missing_required_fields()
def test_convert_with_extra_fields()
def test_convert_batch_entities()
```

#### 2.7 producer.py (94% → 100%)

**Need:** ~3 tests

Missing coverage areas:
- Lines 26-32: Initialization edge cases
- Lines 280-281, 287: Error handling
- Lines 313, 324: Cleanup

**Tests to add:**
```python
def test_producer_with_invalid_url()
def test_producer_send_timeout()
def test_producer_cleanup_on_error()
```

#### 2.8 metrics.py (90% → 100%)

**Need:** ~3 tests

Missing coverage areas:
- Lines 31-32, 63-64: Initialization
- Lines 80, 83-85: Counter operations
- Lines 101, 104-105: Gauge operations
- Lines 120, 123-124: Histogram operations
- Lines 138, 141-142: Summary operations
- Lines 241-247: Export edge cases

**Tests to add:**
```python
def test_metrics_with_invalid_names()
def test_metrics_concurrent_updates()
def test_metrics_export_formats()
```

---

## Total Effort Estimate

### Fixes
- **6 failing tests:** 2 hours
- **3 errors:** 1 hour
- **Total:** 3 hours

### New Tests
- **streaming_orchestrator:** 15-20 tests (8 hours)
- **dlq_handler:** 10 tests (4 hours)
- **graph_consumer:** 8 tests (4 hours)
- **vector_consumer:** 8 tests (4 hours)
- **events:** 5 tests (2 hours)
- **entity_converter:** 5 tests (2 hours)
- **producer:** 3 tests (1 hour)
- **metrics:** 3 tests (1 hour)
- **Total:** 57-62 tests (26 hours)

### Testing & Verification
- **Coverage verification:** 2 hours
- **Integration testing:** 2 hours
- **Documentation:** 2 hours
- **Total:** 6 hours

### Grand Total
**35 hours** (approximately 1 week of focused work)

---

## Success Criteria

- [ ] All 429 tests passing (423 + 6 fixed)
- [ ] All 3 errors resolved
- [ ] 57-62 new tests added
- [ ] 100% coverage for all 8 streaming files
- [ ] All tests deterministic (fixed seeds)
- [ ] Documentation updated

---

## Next Steps

1. **Immediate:** Fix 6 failing tests + 3 errors
2. **Short-term:** Add tests for streaming_orchestrator (highest priority)
3. **Medium-term:** Add tests for other files
4. **Final:** Verification and documentation

---

**Status:** Ready to begin implementation  
**Estimated Completion:** 1 week (35 hours)  
**Priority:** High (Phase 2 of 6)