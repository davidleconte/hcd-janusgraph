# Remediation Plan: B+ (90) → A+ (98+)

**Date:** 2026-02-15  
**Current Score:** B+ (90/100)  
**Target Score:** A+ (98+/100)  
**Author:** David LECONTE  
**Status:** Draft

---

## TL;DR

Three objectives: (1) eliminate all 57 skipped integration tests, (2) raise line coverage from 83% to 100%, (3) achieve A+ grade. This requires fixing environment/data issues for integration tests, writing ~1,643 lines of new test code for coverage gaps, fixing 8 unit test failures, and polishing performance/deployment categories. **Estimated effort: 8–12 days.**

---

## Current State

| Metric | Current | Target |
|--------|---------|--------|
| Integration tests | 145 pass / 57 skip / 0 fail | 202 pass / 0 skip / 0 fail |
| Unit tests | 2,539 pass / 8 fail / 7 skip | 2,554+ pass / 0 fail / 0 skip |
| Line coverage (CI) | 83.06% (gate: 60%) | 100% (gate: 100%) |
| Grade | B+ (90/100) | A+ (98+/100) |
| Containers | 18/18 running | 18/18 healthy |

### Category Scores (Current → Target)

| Category | Current | Target | Gap |
|----------|---------|--------|-----|
| Security | 95 | 99 | MFA completion, cert rotation automation |
| Code Quality | 98 | 100 | Fix 8 unit failures, 0 dead code |
| Testing | 90 | 100 | 0 skips, 100% coverage, mutation testing |
| Documentation | 95 | 98 | Freshness audit, API docs |
| Performance | 85 | 96 | Benchmark baselines, query optimization |
| Maintainability | 95 | 98 | Dependency audit, refactor low-coverage modules |
| Deployment | 90 | 97 | Health check hardening, rollback automation |
| Compliance | 98 | 100 | Complete GDPR data flow docs |

---

## Objective 1: Zero Skipped Integration Tests (57 → 0)

### Root Cause Analysis

The 57 skipped tests fall into 4 categories:

| Category | Est. Tests | Root Cause | Fix |
|----------|-----------|------------|-----|
| **Missing env vars** | ~20 | `PULSAR_INTEGRATION`, `VAULT_ADDR`, `VAULT_TOKEN` not set | Set env vars before test run |
| **Service connectivity at import time** | ~15 | Module-level availability checks fail despite services running | Fix connection params (port, SSL, host) |
| **Missing test data** | ~12 | "No accounts in graph", "person_vectors index not created" | Pre-load test data before integration suite |
| **FraudDetector init failures** | ~10 | FraudDetector/AMLDetector can't connect to services | Fix init params, ensure graph schema loaded |

### Affected Test Files

| File | Skip Count (est.) | Primary Cause |
|------|-------------------|---------------|
| `test_e2e_streaming.py` | ~8 | Pulsar/OpenSearch connectivity |
| `test_e2e_streaming_enhanced.py` | ~8 | Pulsar/OpenSearch connectivity |
| `test_e2e_streaming_pipeline.py` | ~6 | JanusGraph/OpenSearch connectivity |
| `test_e2e_hcd_opensearch.py` | ~10 | Mixed: connectivity + missing data (person_vectors) |
| `test_e2e_fraud_aml_pipeline.py` | ~6 | FraudDetector init + Pulsar |
| `test_fraud_detection_methods.py` | ~10 | FraudDetector init + missing graph data |
| `test_fraud_aml_detection.py` | ~4 | Module-level skipif marker |
| `test_streaming_integration.py` | ~2 | `PULSAR_INTEGRATION` env var |
| `test_vault_integration.py` | ~1 | Vault token |
| `test_credential_rotation.py` | ~2 | Vault + JanusGraph connectivity |

### Action Items

#### 1.1 Fix Environment Variables (Est: 30 min)

Ensure all integration test runs include:
```bash
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=$(cat .vault-keys | grep ROOT_TOKEN | cut -d= -f2)
export PULSAR_INTEGRATION=1
export OPENSEARCH_USE_SSL=false
export JANUSGRAPH_USE_SSL=false
export JANUSGRAPH_PORT=18182
```

Create a `scripts/testing/run_integration_tests.sh` wrapper that sources these automatically.

#### 1.2 Fix Service Connectivity Checks (~20 tests, Est: 2-3 hours)

Many tests check service availability at **module import time** using socket connections or HTTP health checks. These often fail because:
- Wrong port (default 8182 vs mapped 18182)
- SSL mismatch (checking HTTPS when services use HTTP)
- Wrong hostname (localhost vs container name)

**Action:** Audit each test file's availability check functions and ensure they use the same connection parameters as the actual test fixtures (from conftest.py).

Files to audit:
- `test_e2e_streaming.py` lines ~60-100 (PULSAR_AVAILABLE, JANUSGRAPH_AVAILABLE, OPENSEARCH_AVAILABLE)
- `test_e2e_streaming_enhanced.py` lines ~80-120
- `test_e2e_streaming_pipeline.py` lines ~40-70
- `test_e2e_hcd_opensearch.py` lines ~80-130
- `test_e2e_fraud_aml_pipeline.py` lines ~60-100
- `test_fraud_detection_methods.py` lines ~50-80
- `test_fraud_aml_detection.py` lines ~30-50

#### 1.3 Pre-load Test Data (~12 tests, Est: 2-3 hours)

Tests skip because expected data doesn't exist. Need a **test data fixture** that:
1. Loads sample persons, accounts, transactions into JanusGraph
2. Creates `person_vectors` index in OpenSearch
3. Publishes sample events to Pulsar topics

**Action:** Create `tests/integration/conftest.py` session-scoped fixture that:
- Runs `MasterOrchestrator` with `seed=42, person_count=10` to populate graph
- Creates OpenSearch vector indices
- Verifies data is queryable before tests run

#### 1.4 Fix FraudDetector/AMLDetector Init (~10 tests, Est: 1-2 hours)

Multiple tests skip with "FraudDetector init failed". This suggests the detector classes can't connect to JanusGraph or OpenSearch during initialization.

**Action:** 
- Audit FraudDetector and AMLDetector constructors for connection params
- Ensure they use the same connection settings as the test environment
- If init is expensive, create session-scoped fixtures that share a single detector instance

#### 1.5 Fix Module-Level skipif Markers (~4 tests, Est: 30 min)

`test_fraud_aml_detection.py` has a `pytestmark = pytest.mark.skipif(...)` at module level. If the condition is stale, remove or update it.

---

## Objective 2: 100% Line Coverage (83% → 100%)

### Coverage Gap Analysis

**Total:** 10,931 statements, 1,643 uncovered (83.06%)

| Module | Coverage | Uncovered Lines | Effort |
|--------|----------|-----------------|--------|
| `init/load_data.py` | 0% | 37 | Low — write test that calls load functions with mock client |
| `performance/benchmark.py` | 70% | 43 | Medium — test benchmark runner with mock data |
| `api/main.py` | 64% | 25 | Medium — test app startup, middleware, error handlers |
| `api/routers/performance.py` | 62% | 32 | Medium — test performance endpoints with mocked clients |
| `analytics/ubo_discovery.py` | 74% | 46 | Medium — test UBO traversal edge cases |
| `utils/auth.py` | 82% | 3 | Low — cover 3 missing branches |
| `utils/tracing.py` | 90% | 12 | Low — test tracing decorator edge cases |
| `utils/vault_client.py` | 92% | 14 | Low — test error paths |
| `utils/validation.py` | 90% | 30 | Medium — cover validation edge cases |
| `utils/resilience.py` | 95% | 3 | Low — cover retry exhaustion path |
| `api/waf_middleware.py` | 90% | 11 | Low — test WAF edge cases |
| `client/connection_pool.py` | 91% | 12 | Low — test pool exhaustion, cleanup |
| `client/janusgraph_client.py` | 95% | 4 | Low — test error paths |
| `security/mfa.py` | 98% | 3 | Low — 1 branch |
| `security/query_sanitizer.py` | 94% | 8 | Low — cover sanitizer edge cases |
| `security/rbac.py` | 97% | 3 | Low — 2 branches |
| `performance/query_profiler.py` | 93% | 8 | Low — test profiler edge cases |
| `config/settings.py` | 96% | 1 | Low — 1 line |
| `api/models.py` | 94% | 7 | Low — test model validation |
| `api/dependencies.py` | 91% | 1 | Low — 1 branch |
| `init/initialize_graph.py` | 87% | 10 | Low — test schema init error paths |
| Various 99%+ modules | 99% | ~10 | Low — minor branch coverage |
| **banking/** modules (not shown above) | varies | ~1,300+ | **HIGH** — bulk of uncovered code |

### banking/ Module Coverage (Estimated)

The `banking/` tree has ~20,000+ lines. Modules like `streaming/`, `aml/`, `fraud/`, `compliance/`, `analytics/` are heavily under-tested at the unit level. Integration tests exercise them but don't count toward unit coverage in CI.

**Key banking/ coverage gaps (estimated):**

| Module | Est. Coverage | Est. Uncovered Lines | Effort |
|--------|---------------|---------------------|--------|
| `banking/streaming/` | ~28% | ~500 | High — mock Pulsar client, test all event types |
| `banking/aml/` | ~25% | ~300 | High — mock graph client, test detection algorithms |
| `banking/fraud/` | ~23% | ~400 | High — mock graph client, test detection methods |
| `banking/compliance/` | ~25% | ~200 | Medium — test audit logger, compliance reporter |
| `banking/analytics/` | ~0% | ~600 | High — test all analytics modules |
| `banking/data_generators/loaders/` | ~40% | ~200 | Medium — test loader with mock JanusGraph |
| `banking/data_generators/patterns/` | ~13% | ~300 | High — test all pattern generators |

### Action Items

#### 2.1 Raise CI Coverage Gate (Est: 5 min)

Update `.github/workflows/quality-gates.yml`:
```yaml
--cov-fail-under=100
```

#### 2.2 Write Tests for src/python/ Gaps (Est: 2-3 days)

Priority order (high-impact, low-effort first):
1. `init/load_data.py` — 37 lines, mock JanusGraph client
2. `api/main.py` — test app startup with TestClient
3. `api/routers/performance.py` — test endpoints with mocked dependencies
4. `performance/benchmark.py` — test runner with mock data
5. `analytics/ubo_discovery.py` — test traversal algorithms
6. Remaining 90%+ modules — surgical branch coverage additions

#### 2.3 Write Tests for banking/ Gaps (Est: 5-7 days)

This is the **bulk of the work**. ~2,500+ uncovered lines across banking modules.

Strategy:
1. **Mock-heavy unit tests** — don't require services, fast, reliable
2. **Parametrized tests** — cover multiple code paths efficiently
3. **Integration test coverage inclusion** — consider adding `--cov` to integration test runs

Priority order:
1. `banking/streaming/` — mock PulsarProducer/Consumer, test event processing
2. `banking/fraud/` — mock GraphRepository, test detection algorithms
3. `banking/aml/` — mock graph traversals, test structuring detection
4. `banking/analytics/` — mock data, test all detection modules
5. `banking/compliance/` — test audit logging, report generation
6. `banking/data_generators/patterns/` — test pattern injection with mock data
7. `banking/data_generators/loaders/` — test loader with mock JanusGraph

#### 2.4 Fix 8 Failing Unit Tests (Est: 2-3 hours)

| Test | Likely Cause | Fix |
|------|-------------|-----|
| 4x `test_benchmarks.py` (perf) | Timing-sensitive assertions | Relax thresholds or mock time |
| `test_graph_consumer.py::test_process_update_event` | Mock mismatch | Fix mock setup |
| `test_aml_structuring.py::test_default_initialization` | Constructor changes | Update test expectations |
| `test_complex_scenarios.py::test_new_account_first_transaction` | Logic change | Fix test or code |
| `test_fraud_detection.py::test_default_initialization` | Constructor changes | Update test expectations |

#### 2.5 Fix 7 Skipped Unit Tests (Est: 1 hour)

Identify and resolve or document all 7 skipped unit tests.

---

## Objective 3: A+ Grade (90 → 98+)

### Category-by-Category Improvement Plan

#### Security: 95 → 99 (Est: 1 day)

| Item | Action | Impact |
|------|--------|--------|
| MFA completion | Implement TOTP verification endpoint (currently stub) | +2 |
| Certificate rotation | Add automated cert renewal script | +1 |
| Security headers | Add CSP, HSTS headers to API middleware | +1 |

#### Code Quality: 98 → 100 (Est: 2 hours)

| Item | Action | Impact |
|------|--------|--------|
| Fix 8 unit failures | See §2.4 | +1 |
| Dead code removal | Run `vulture` and remove unused functions | +1 |

#### Testing: 90 → 100 (Est: 6-8 days)

| Item | Action | Impact |
|------|--------|--------|
| 100% line coverage | See §2.2-2.3 | +5 |
| 0 skipped tests | See §1.1-1.5 and §2.5 | +2 |
| 0 failing tests | See §2.4 | +1 |
| Mutation testing | Add mutmut CI step | +2 |

#### Documentation: 95 → 98 (Est: 1 day)

| Item | Action | Impact |
|------|--------|--------|
| API reference | Auto-generate from docstrings (pdoc/mkdocs) | +1 |
| Stale doc audit | Archive outdated phase docs | +1 |
| Runbook updates | Add troubleshooting for new modules | +1 |

#### Performance: 85 → 96 (Est: 2 days)

| Item | Action | Impact |
|------|--------|--------|
| Benchmark baselines | Establish P95 latency targets for all query types | +4 |
| Query optimization | Add query plan analysis, index usage validation | +3 |
| Load test results | Document concurrent user capacity | +2 |
| Cache hit rates | Add cache metrics to monitoring | +2 |

#### Maintainability: 95 → 98 (Est: 4 hours)

| Item | Action | Impact |
|------|--------|--------|
| Dependency audit | Run `pip-audit`, update vulnerable deps | +1 |
| Type coverage | Run `mypy --strict` on remaining modules | +1 |
| Complexity check | Run `radon` and refactor any CC > 10 | +1 |

#### Deployment: 90 → 97 (Est: 1 day)

| Item | Action | Impact |
|------|--------|--------|
| Health check hardening | Add deep health checks (DB connectivity, not just process) | +3 |
| Rollback automation | Script for rolling back to previous version | +2 |
| Blue-green readiness | Document blue-green deployment procedure | +2 |

#### Compliance: 98 → 100 (Est: 4 hours)

| Item | Action | Impact |
|------|--------|--------|
| GDPR data flow diagram | Complete data flow documentation | +1 |
| Audit log completeness | Verify all 30+ event types have tests | +1 |

---

## Timeline

| Phase | Items | Duration | Priority |
|-------|-------|----------|----------|
| **Phase 1: Quick Wins** | Env vars, CI gate, fix 8 unit failures, fix 7 skips | 1 day | Critical |
| **Phase 2: Integration Tests** | Service connectivity, test data, FraudDetector init | 3-4 days | Critical |
| **Phase 3: Unit Coverage (src/)** | Tests for all src/python/ gaps | 2-3 days | High |
| **Phase 4: Unit Coverage (banking/)** | Tests for all banking/ gaps (~2,500 lines) | 5-7 days | High |
| **Phase 5: Grade Polish** | Performance, deployment, docs, security hardening | 3-4 days | Medium |
| **Phase 6: Verification** | Full test suite, coverage report, grade audit | 1 day | Final |

**Total estimated effort: 15-20 days** (aggressive: 10-12 days with focus)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| 100% coverage requires testing generated/dead code | High | Medium | Identify truly unreachable code, exclude or remove |
| Performance benchmarks are inherently flaky | Medium | Low | Use statistical assertions, increase tolerance |
| Banking modules may have untestable external dependencies | Medium | High | Heavy mocking, dependency injection refactoring |
| Some integration test skips are legitimate (missing infra) | Low | Medium | Document as known limitations vs actual failures |

---

## Verification Commands

```bash
# Phase 1 verification
conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest tests/ banking/ \
  --ignore=tests/integration --ignore=tests/benchmarks --ignore=tests/performance \
  -k "not slow and not integration" --timeout=120 -q  # 0 failed, 0 skipped

# Phase 2 verification
source .vault-keys && \
conda run -n janusgraph-analysis PYTHONPATH=. \
  VAULT_ADDR=http://localhost:8200 VAULT_TOKEN=$VAULT_ROOT_TOKEN \
  PULSAR_INTEGRATION=1 OPENSEARCH_USE_SSL=false JANUSGRAPH_USE_SSL=false \
  python -m pytest tests/integration/ -v --no-cov --timeout=120  # 202 pass, 0 skip

# Phase 3-4 verification
conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest tests/ banking/ \
  --cov=src --cov=banking --cov-fail-under=100 \
  --ignore=tests/integration --ignore=tests/benchmarks --ignore=tests/performance \
  -k "not slow and not integration" --timeout=120  # 100% coverage

# Final verification
# All of the above + grade audit
```
