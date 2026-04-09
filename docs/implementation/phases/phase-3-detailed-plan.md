# Phase 3: Pattern Generator Tests - Detailed Plan

**Date:** 2026-04-08  
**Status:** Planning  
**Actual Scope:** 62 failing tests (not 32 as originally estimated)  
**Estimated Duration:** 3-4 hours

---

## 🎯 Problem Statement

All pattern generator tests are failing because of an **API mismatch**:

**Current Implementation:**
```python
def generate(...) -> Tuple[Pattern, List[Any], List[Any]]:
    """Returns (Pattern, [Trade], [Communication])"""
```

**Test Expectations:**
```python
pattern = generator.generate()
assert isinstance(pattern, Pattern)  # FAILS - pattern is a tuple!
```

---

## 📊 Scope Analysis

### Test Distribution

| Generator | Tests | Status | Priority |
|-----------|-------|--------|----------|
| FraudRing | 19 | ✅ PASSING | N/A |
| Structuring | 14 | ✅ PASSING | N/A |
| InsiderTrading | 12 | ❌ FAILING | HIGH |
| CATO | 12 | ❌ FAILING | MEDIUM |
| MuleChain | 12 | ❌ FAILING | MEDIUM |
| TBML | 14 | ❌ FAILING | LOW |
| **TOTAL** | **83** | **62 FAILING** | - |

### Why FraudRing and Structuring Pass

These generators likely return just `Pattern` objects, not tuples. Need to verify their implementation.

---

## 🔍 Architectural Decision Required

### Option A: Update Tests to Handle Tuples (Recommended)

**Pros:**
- Preserves current API
- Tests get access to generated trades and communications
- More comprehensive testing possible
- No breaking changes to production code

**Cons:**
- Need to update 62 tests
- More complex test assertions

**Implementation:**
```python
# BEFORE
pattern = generator.generate()
assert isinstance(pattern, Pattern)

# AFTER
result = generator.generate()
assert isinstance(result, tuple)
assert len(result) == 3
pattern, trades, communications = result
assert isinstance(pattern, Pattern)
assert isinstance(trades, list)
assert isinstance(communications, list)
```

**Estimated Effort:** 3-4 hours (62 tests × 3-4 minutes each)

---

### Option B: Add Wrapper Method (Quick Fix)

**Pros:**
- Minimal test changes
- Backward compatible
- Quick implementation

**Cons:**
- Adds API complexity
- Tests lose access to trades/communications
- Doesn't fix root cause

**Implementation:**
```python
# Add to each generator class
def generate_pattern_only(self, **kwargs) -> Pattern:
    """Generate pattern without trades/communications."""
    pattern, _, _ = self.generate(**kwargs)
    return pattern

# Update tests
pattern = generator.generate_pattern_only()
assert isinstance(pattern, Pattern)
```

**Estimated Effort:** 1-2 hours (add method + update 62 tests)

---

### Option C: Change Generator API (Breaking Change)

**Pros:**
- Simplifies API
- Tests work as-is
- Cleaner interface

**Cons:**
- **BREAKING CHANGE** - affects production code
- Need to update all generator callers
- May break orchestration logic
- Requires full regression testing

**Implementation:**
```python
# Change return type
def generate(...) -> Pattern:
    """Generate pattern only."""
    # Store trades/communications as instance variables
    self._last_trades = trades
    self._last_communications = communications
    return pattern
```

**Estimated Effort:** 6-8 hours (risky, requires full testing)

---

## 📋 Recommended Approach: Option A (Update Tests)

### Phase 3.1: InsiderTrading (12 tests) - HIGH PRIORITY

**File:** `banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py`

**Tests to Fix:**
1. `test_generate_default_pattern` - Unpack tuple
2. `test_pattern_has_required_fields` - Unpack tuple
3. `test_pattern_indicators_present` - Unpack tuple
4. `test_pattern_metadata_present` - Unpack tuple
5. `test_deterministic_with_same_seed` - Unpack both results
6. `test_pattern_entity_ids_present` - Unpack tuple
7. `test_pattern_risk_level_set` - Unpack tuple
8. `test_pattern_severity_score_range` - Unpack tuple
9. `test_pattern_dates_set` - Unpack tuple
10. `test_pattern_detection_date_set` - Unpack tuple
11. `test_pattern_transaction_count` - Unpack tuple
12. `test_pattern_total_value` - Unpack tuple

**Template Fix:**
```python
def test_generate_default_pattern(self, insider_trading_gen):
    """Test generating pattern with default parameters."""
    result = insider_trading_gen.generate()
    
    # Unpack tuple
    assert isinstance(result, tuple), "generate() should return tuple"
    assert len(result) == 3, "Tuple should have 3 elements"
    pattern, trades, communications = result
    
    # Original assertions
    assert isinstance(pattern, Pattern)
    assert pattern.pattern_type == "insider_trading"
    
    # Bonus: Verify trades and communications
    assert isinstance(trades, list)
    assert isinstance(communications, list)
    assert len(trades) > 0, "Should generate trades"
```

**Estimated Time:** 1 hour

---

### Phase 3.2: CATO (12 tests) - MEDIUM PRIORITY

**Similar fixes as InsiderTrading**

**Estimated Time:** 1 hour

---

### Phase 3.3: MuleChain (12 tests) - MEDIUM PRIORITY

**Similar fixes as InsiderTrading**

**Estimated Time:** 1 hour

---

### Phase 3.4: TBML (14 tests) - LOW PRIORITY

**Similar fixes as InsiderTrading**

**Estimated Time:** 1.5 hours

---

## 🔧 Implementation Strategy

### Step 1: Verify FraudRing/Structuring APIs (15 min)

Check why these pass:
```bash
grep -A 5 "def generate" banking/data_generators/patterns/fraud_ring_pattern_generator.py
grep -A 5 "def generate" banking/data_generators/patterns/structuring_pattern_generator.py
```

### Step 2: Create Helper Function (15 min)

Add to test file:
```python
def unpack_pattern_result(result):
    """Helper to unpack pattern generator results."""
    if isinstance(result, tuple):
        assert len(result) == 3, "Expected (pattern, trades, communications)"
        pattern, trades, communications = result
        assert isinstance(pattern, Pattern)
        assert isinstance(trades, list)
        assert isinstance(communications, list)
        return pattern, trades, communications
    else:
        # Legacy generators that return just Pattern
        assert isinstance(result, Pattern)
        return result, [], []
```

### Step 3: Update Tests Systematically (3 hours)

For each failing test:
1. Change `pattern = gen.generate()` to `result = gen.generate()`
2. Add `pattern, trades, comms = unpack_pattern_result(result)`
3. Keep original assertions
4. Optionally add assertions for trades/communications
5. Run test to verify
6. Move to next test

### Step 4: Verification (30 min)

```bash
# Run all pattern tests
pytest banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py -v

# Should see 83/83 passing
```

---

## 📈 Success Criteria

- ✅ All 62 failing tests pass
- ✅ No breaking changes to production code
- ✅ Tests verify tuple structure
- ✅ Tests verify trades and communications are generated
- ✅ Deterministic tests still work with same seeds

---

## 🚨 Risks and Mitigation

### Risk 1: Different generators have different return types

**Mitigation:** Use helper function that handles both cases

### Risk 2: Some tests may need trades/communications

**Mitigation:** Helper function returns all three, tests can use what they need

### Risk 3: Time estimate may be optimistic

**Mitigation:** Start with InsiderTrading (12 tests) as proof of concept, then reassess

---

## 📝 Alternative: Quick Win Strategy

If time is limited, implement **Option B (Wrapper Method)** for quick results:

1. Add `generate_pattern_only()` to each generator (30 min)
2. Update fixture to use new method (15 min)
3. All tests pass immediately (45 min total)

**Trade-off:** Tests don't verify trades/communications generation

---

## 🎯 Recommendation

**Start with Option A (Update Tests) for InsiderTrading only** (1 hour)

**Decision Point:** After InsiderTrading is complete:
- If smooth → Continue with CATO, MuleChain, TBML
- If problematic → Switch to Option B (Wrapper Method)

This gives us a **proof of concept** before committing to the full 3-4 hour effort.

---

## 📊 Progress Tracking

| Phase | Tests | Status | Time | Completion |
|-------|-------|--------|------|------------|
| 3.1 InsiderTrading | 12 | ⏳ Pending | 1h | 0% |
| 3.2 CATO | 12 | ⏳ Pending | 1h | 0% |
| 3.3 MuleChain | 12 | ⏳ Pending | 1h | 0% |
| 3.4 TBML | 14 | ⏳ Pending | 1.5h | 0% |
| **TOTAL** | **50** | **⏳ Pending** | **4.5h** | **0%** |

**Note:** FraudRing (19) and Structuring (14) already pass = 33 tests

**Overall:** 33 passing + 50 to fix = 83 total tests

---

## 🔄 Next Steps

1. **Verify FraudRing/Structuring APIs** - Understand why they pass
2. **Create helper function** - `unpack_pattern_result()`
3. **Fix InsiderTrading tests** - Proof of concept (1 hour)
4. **Decision point** - Continue or switch to Option B
5. **Complete remaining generators** - If Option A works well
6. **Final verification** - Run full test suite

---

**Created:** 2026-04-08  
**Author:** Bob (AI Assistant)  
**Status:** Ready for execution