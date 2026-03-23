# Codebase Improvement Plan

**Date:** 2026-03-23
**Target:** Improve test coverage, docstring coverage, and performance score

## Current State

| Metric | Current | Target |
|--------|---------|--------|
| Test Coverage | 81.43% | 90%+ |
| Docstring Coverage | 90.2% | 95%+ |
| Performance Score | 85/100 | 95/100 |

## Phase 1: Performance Optimizations (Quick Wins)

### 1.1 Sanctions Screening Cache
- **File:** `banking/aml/sanctions_screening.py`
- **Change:** Add LRU cache with 1-hour TTL for customer screening results
- **Impact:** Reduce OpenSearch load, faster repeated lookups

### 1.2 Async Parallel Fetching
- **File:** `src/python/api/main.py`
- **Change:** Convert sequential health/UBO fetches to `asyncio.gather`
- **Impact:** Reduce API response time by ~30-40%

### 1.3 Connection Pool Tuning
- **File:** `src/python/client/janusgraph_client.py`
- **Change:** Increase pool size based on 12-CPU allocation
- **Impact:** Better concurrency for notebook runs

### 1.4 Query Result Caching
- **File:** `src/python/repository/graph_repository.py`
- **Change:** Add LRU cache for frequently-accessed vertices
- **Impact:** Reduce repeated vertex lookups

## Phase 2: Test Coverage Improvements

### 2.1 Analytics Module (0% → 80%)
- **Files:** `banking/analytics/tests/`
- **Actions:**
  - Create `conftest.py` with scenario fixtures
  - Add tests for carousel fraud detection
  - Add tests for shell company detection
  - Add boundary value tests for scoring algorithms

### 2.2 Streaming Module (28% → 70%)
- **Files:** `banking/streaming/tests/`
- **Actions:**
  - Mock network partitions for DLQ testing
  - Test retry logic with connection errors
  - Add schema evolution tests

### 2.3 Patterns Module (13% → 60%)
- **Files:** `banking/data_generators/patterns/tests/`
- **Actions:**
  - Add hypothesis-based invariance tests
  - Test pattern injection with all entity types

### 2.4 Fraud/AML Modules (23-25% → 65%)
- **Files:** `banking/fraud/tests/`, `banking/aml/tests/`
- **Actions:**
  - Edge case tests for risk scoring
  - Boundary tests for threshold detection

## Phase 3: Docstring Coverage Improvements

### 3.1 Missing Docstrings
- **Priority Files:**
  - `banking/fraud/*.py` - Add `:param:`, `:return:`, `:raises:`
  - `banking/aml/enhanced_structuring_detection.py` - Add `Example:` blocks
  - `src/python/utils/*.py` - Add `:raises:` documentation

### 3.2 Automated Enforcement
- **File:** `pyproject.toml`
- **Change:** Add interrogate check with 95% threshold
- **File:** `.pre-commit-config.yaml`
- **Change:** Add docformatter hook

## Execution Order

1. ✅ Create plan (current step)
2. ✅ Phase 1: Performance (COMPLETE)
   - ✅ 1.1 Sanctions Screening Cache - TTLCache with 1-hour TTL, cache stats added
   - ⏳ 1.2 Async Parallel Fetching - Deferred (requires Gremlin async refactoring)
   - ✅ 1.3 Connection Pool Tuning - Added pool_size/max_workers params
   - ✅ 1.4 Query Result Caching - Added LRU cache to GraphRepository.get_vertex()
3. Phase 2: Test coverage (1 week)
4. Phase 3: Docstring coverage (2-3 days)
5. Run quality gates to verify improvements

## Success Criteria

- [ ] Test coverage ≥ 90%
- [ ] Docstring coverage ≥ 95%
- [x] Performance optimizations implemented
- [ ] All quality gates pass (mypy, ruff, pytest)
- [ ] Deterministic proof passes (15/15 notebooks)
