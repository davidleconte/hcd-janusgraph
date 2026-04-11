# Phase 7 Week 4 - Test Failure Fixes

**Date:** 2026-04-11  
**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team  
**Status:** In Progress

## Overview

This document tracks the fixes for the remaining 7 test failures in the Graph-Based Fraud Detection system.

## Test Failures Analysis

### 1. Network Analyzer Issues (2 tests)

#### test_risk_score_low_centrality
**File:** `banking/graph/tests/test_network_analyzer.py:51`  
**Issue:** Risk score calculation doesn't properly handle low centrality values  
**Expected:** Risk score < 30 for low centrality (all metrics = 0.1)  
**Actual:** Risk score likely higher due to formula  
**Root Cause:** Formula in `CentralityMetrics.get_risk_score()` multiplies by 100 at the end

**Fix:**
```python
# Current formula (line 59-66):
risk_score = (
    self.degree_centrality * 20 +
    self.betweenness_centrality * 30 +
    self.closeness_centrality * 20 +
    self.pagerank * 20 +
    self.eigenvector_centrality * 10
)
return min(100.0, risk_score * 100)

# With all values = 0.1:
# risk_score = (0.1*20 + 0.1*30 + 0.1*20 + 0.1*20 + 0.1*10) = 10.0
# return min(100.0, 10.0 * 100) = 100.0  # WRONG!

# Should be:
return min(100.0, risk_score)  # Already scaled 0-100
```

#### test_calculate_centrality_single_node
**File:** `banking/graph/tests/test_network_analyzer.py:247`  
**Issue:** Single node graph causes issues with closeness centrality  
**Expected:** All centrality metrics = 0.0 for isolated node  
**Actual:** closeness_centrality may be undefined or NaN  
**Root Cause:** NetworkX closeness_centrality returns 0.0 for single node, but test expects it

**Fix:** Add special handling for single-node graphs in `calculate_centrality()`

### 2. Community Detector Issues (2 tests)

#### test_detect_fraud_ring_shared_ssn
**File:** `banking/graph/tests/test_community_detector.py:282`  
**Issue:** Fraud ring detection fails when identities share SSN  
**Expected:** At least 1 fraud ring detected (5 identities with same SSN)  
**Actual:** No fraud rings detected  
**Root Cause:** Network building may not create edges for shared SSN, or community detection doesn't group them

**Fix:** Verify `NetworkAnalyzer.build_network()` creates edges for shared SSN (lines 218-227)

#### test_multiple_fraud_rings
**File:** `banking/graph/tests/test_community_detector.py:308`  
**Issue:** Multiple fraud rings not detected  
**Expected:** 2 fraud rings (5 identities each with different SSNs)  
**Actual:** Fewer than 2 detected  
**Root Cause:** Same as above - network building or community detection

**Fix:** Same as above

### 3. Pattern Analyzer Issues (1 test)

#### test_detect_layering_patterns_shallow
**File:** `banking/graph/tests/test_pattern_analyzer.py:463`  
**Issue:** Shallow layering structures incorrectly flagged  
**Expected:** 0 patterns (depth=2, min_depth=3)  
**Actual:** 1 pattern detected  
**Root Cause:** BFS layer counting includes root as layer 0, so depth=3 when should be 2

**Fix:** Adjust depth calculation in `detect_layering_patterns()` (line 492)
```python
# Current:
depth = len(layers)  # Includes root layer

# Should be:
depth = len(layers) - 1  # Exclude root layer, count only downstream layers
# OR adjust the comparison:
if depth > min_depth:  # Use > instead of >=
```

### 4. Visualizer Issues (4 tests)

#### test_compute_layout_deterministic & test_layout_deterministic
**File:** `banking/graph/tests/test_visualizer.py:186, 412`  
**Issue:** Layout positions not identical across runs  
**Expected:** pos1[node] == pos2[node] for all nodes  
**Actual:** Positions differ slightly  
**Root Cause:** NetworkX spring_layout uses seed=42 but may have floating point precision issues, or tuple comparison fails

**Fix:** Use approximate comparison or ensure exact determinism
```python
# In test, use:
import numpy as np
for node in G.nodes():
    np.testing.assert_array_almost_equal(pos1[node], pos2[node], decimal=10)
```

#### test_style_nodes_by_community
**File:** `banking/graph/tests/test_visualizer.py:257`  
**Issue:** Community styling fails  
**Expected:** Nodes in same community have same color  
**Actual:** Colors may differ or test comparison fails  
**Root Cause:** Color palette access or color comparison

**Fix:** Verify color assignment logic in `style_nodes_by_community()` (lines 268-271)

#### test_visualize_with_communities
**File:** `banking/graph/tests/test_visualizer.py:347`  
**Issue:** Visualization with communities fails  
**Expected:** fig is not None  
**Actual:** May return None or raise exception  
**Root Cause:** Plotly not available or community styling fails

**Fix:** Ensure graceful handling when plotly unavailable

## Fix Priority

1. **High Priority (Blocking):**
   - test_risk_score_low_centrality (formula bug)
   - test_detect_layering_patterns_shallow (logic bug)

2. **Medium Priority (Integration):**
   - test_detect_fraud_ring_shared_ssn
   - test_multiple_fraud_rings

3. **Low Priority (Test Implementation):**
   - test_calculate_centrality_single_node
   - test_compute_layout_deterministic
   - test_layout_deterministic
   - test_style_nodes_by_community
   - test_visualize_with_communities

## Implementation Plan

### Step 1: Fix CentralityMetrics.get_risk_score()
- Remove `* 100` multiplication
- Risk score already scaled 0-100

### Step 2: Fix detect_layering_patterns()
- Change `if depth >= min_depth:` to `if depth > min_depth:`
- OR change `depth = len(layers) - 1`

### Step 3: Fix single node handling
- Add special case for single-node graphs in calculate_centrality()

### Step 4: Fix fraud ring detection
- Verify network building creates edges for shared SSN
- Check community detection parameters

### Step 5: Fix visualizer determinism
- Use numpy array comparison in tests
- Ensure exact seed usage

### Step 6: Fix community styling
- Verify color assignment
- Add better error handling

## Testing Strategy

After each fix:
1. Run specific test: `pytest banking/graph/tests/test_X.py::TestClass::test_method -v`
2. Run all graph tests: `pytest banking/graph/tests/ -v`
3. Verify no regressions

## Success Criteria

- All 139 tests pass (100%)
- No new test failures introduced
- Production code changes minimal and safe
- All fixes documented

---

**Status:** Ready to implement fixes