# Remediation Plan: workingB+ → Production Ready (A)

**Date:** 2026-02-15  
**Release Tag:** `workingB+`  
**Current Score:** B (83/100)  
**Target Score:** A (92+/100)  
**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Watstonx.Data Global Product Specialist (GPS)  
**Status:** Active

---

## TL;DR

This plan addresses 5 P0 blockers and 5 P1 improvements identified in the production readiness assessment. Estimated effort: **3–4 days** for P0 (required before any production deployment), **2–3 days** for P1 (recommended within 2 weeks).

---

## Current State Summary

| Category | Score | Key Issue |
|----------|-------|-----------|
| Code Quality | 87 | Dead import, inline imports, dangerous default |
| Testing | 82 | 2 failing tests, 14 skipped, no coverage measurement |
| Security | 72 | **`.env` tracked in git** (P0 critical) |
| Documentation | 90 | Possible stale docs, inflated self-assessment |
| Infrastructure | 83 | 2 unhealthy containers, CI not verified |
| Determinism | 93 | Operational `datetime.now()` in stats (acceptable) |

---

## P0 — Must Fix Before Production

### P0-1: Remove `.env` from Git Tracking

**Priority:** CRITICAL  
**Estimated Effort:** 30 minutes  
**Risk if Ignored:** Credential leak if real passwords are ever placed in `.env`  
**Category:** Security

**Problem:**  
`.env` and `config/compose/.env` are tracked in git despite `.gitignore` rules. The `.gitignore` was added after the files were committed, so git continues tracking them. Current content contains placeholder passwords (`CHANGE_ME_TO_SECURE_PASSWORD_MIN_16_CHARS`), not real secrets — but this is a ticking time bomb.

**Remediation Steps:**

```bash
# 1. Verify current .env content contains no real secrets
cat .env | grep -v "^#" | grep -v "^$"
cat config/compose/.env | grep -v "^#" | grep -v "^$"

# 2. Copy to .env.example (strip any real values, keep structure)
cp .env .env.example
cp config/compose/.env config/compose/.env.example

# 3. Remove from git tracking (keeps local file)
git rm --cached .env config/compose/.env

# 4. Verify .gitignore covers both paths
grep -n "\.env" .gitignore

# 5. Commit the removal
git add .env.example config/compose/.env.example .gitignore
git commit -m "security: remove .env from git tracking, add .env.example

BREAKING: .env is no longer tracked. Copy .env.example to .env
and fill in your credentials before running.

Co-Authored-By: AdaL <adal@sylph.ai>"

# 6. Force-push to rewrite history (OPTIONAL - only if repo is private)
# git filter-branch --force --index-filter \
#   'git rm --cached --ignore-unmatch .env config/compose/.env' \
#   --prune-empty -- --all
```

**Verification:**
- `git ls-files --cached .env` returns empty
- `git status` shows clean after `.env` exists locally but is untracked
- CI pipeline still works (reads from environment, not committed file)

**Acceptance Criteria:**
- [ ] `.env` not in `git ls-files`
- [ ] `.env.example` exists with placeholder values
- [ ] README updated with "copy .env.example to .env" instruction

---

### P0-2: Fix 2 Failing Vault Error Scenario Tests

**Priority:** HIGH  
**Estimated Effort:** 1–2 hours  
**Risk if Ignored:** Silent test regression masking real Vault issues  
**Category:** Testing

**Problem:**  
Two tests in `tests/unit/test_vault_error_scenarios.py` are failing:
- `TestSecretErrors::test_list_failure`
- `TestListOperations::test_list_permission_denied`

**Remediation Steps:**

1. Run the failing tests with verbose output:
   ```bash
   conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest \
     tests/unit/test_vault_error_scenarios.py -v --tb=long --no-cov
   ```

2. Analyze failure:
   - If mock/patch issue → fix test expectations
   - If Vault API changed → update client code
   - If environmental → add proper skip conditions

3. Fix or skip with documented reason:
   ```python
   @pytest.mark.skipif(
       not os.getenv("VAULT_TOKEN"),
       reason="Vault token not configured"
   )
   ```

**Verification:**
- `pytest tests/unit/test_vault_error_scenarios.py -v` → all pass or skip with reason
- No silent failures in CI

**Acceptance Criteria:**
- [ ] 0 failing tests in `test_vault_error_scenarios.py`
- [ ] Each skip (if any) has a documented reason

---

### P0-3: Investigate and Fix 2 Unhealthy Containers

**Priority:** HIGH  
**Estimated Effort:** 1–2 hours  
**Risk if Ignored:** Monitoring blind spots, user-facing tools unavailable  
**Category:** Infrastructure

**Problem:**  
Two containers report unhealthy status:
- `janusgraph-demo_opensearch-dashboards_1` — Web UI for OpenSearch
- `janusgraph-demo_janusgraph-visualizer_1` — Graph visualization tool

**Remediation Steps:**

1. Check container logs:
   ```bash
   podman logs --tail 50 janusgraph-demo_opensearch-dashboards_1
   podman logs --tail 50 janusgraph-demo_janusgraph-visualizer_1
   ```

2. Check health check configuration:
   ```bash
   podman inspect janusgraph-demo_opensearch-dashboards_1 | grep -A 10 "Healthcheck"
   podman inspect janusgraph-demo_janusgraph-visualizer_1 | grep -A 10 "Healthcheck"
   ```

3. Common fixes:
   - **OpenSearch Dashboards**: Often fails health check due to security plugin mismatch. Fix: disable security plugin or configure correct credentials in `opensearch_dashboards.yml`
   - **JanusGraph Visualizer**: May need correct JanusGraph endpoint URL. Fix: verify `JANUSGRAPH_URL` env var points to correct host:port

4. Restart after fix:
   ```bash
   cd config/compose
   podman-compose -p janusgraph-demo restart opensearch-dashboards janusgraph-visualizer
   ```

**Verification:**
- `podman ps` shows all containers as `healthy`
- OpenSearch Dashboards accessible at `http://localhost:5601`
- JanusGraph Visualizer accessible at its configured port

**Acceptance Criteria:**
- [ ] 15/15 containers healthy
- [ ] Both UIs accessible via browser

---

### P0-4: Verify CI Pipeline Passes

**Priority:** HIGH  
**Estimated Effort:** 2–4 hours  
**Risk if Ignored:** Unknown quality gate status — may be shipping broken code  
**Category:** Testing / CI

**Problem:**  
10 CI workflow files exist in `.github/workflows/` but there is no evidence they pass. Historical CI runs showed cascading failures.

**Remediation Steps:**

1. List all workflows and their last status:
   ```bash
   gh run list --limit 20
   ```

2. Trigger a fresh CI run:
   ```bash
   git commit --allow-empty -m "ci: trigger full pipeline verification" && git push
   ```

3. Monitor each workflow:
   ```bash
   gh run watch
   ```

4. For each failing workflow:
   - Read logs: `gh run view <run-id> --log-failed`
   - Fix the root cause (not `|| true` workarounds)
   - Re-run: `gh run rerun <run-id>`

5. Document any intentionally skipped workflows with reasons

**Verification:**
- `gh run list` shows all 10 workflows with ✓ status
- No `|| true` masks in CI scripts

**Acceptance Criteria:**
- [ ] All 10 workflows pass on latest commit
- [ ] No `|| true` in coverage/test gates
- [ ] CI badge in README reflects actual status

---

### P0-5: Measure Actual Test Line Coverage

**Priority:** HIGH  
**Estimated Effort:** 1 hour  
**Risk if Ignored:** Unknown coverage — can't enforce quality gates  
**Category:** Testing

**Problem:**  
AGENTS.md claims ~18% line coverage but no fresh measurement exists. CI quality gate requires ≥60%.

**Remediation Steps:**

1. Run full coverage measurement:
   ```bash
   conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest \
     tests/unit/ banking/data_generators/tests/ \
     --cov=src --cov=banking --cov-report=term-missing \
     --cov-report=html --timeout=120 -q 2>&1 | tail -30
   ```

2. Analyze results by module:
   - Identify modules below 60% threshold
   - Prioritize high-risk modules (client, API, security)

3. If overall coverage is below 60%:
   - Write targeted tests for uncovered critical paths
   - Focus on: `src/python/api/`, `banking/streaming/`, `banking/aml/`

4. Update AGENTS.md with actual coverage numbers

**Verification:**
- `htmlcov/index.html` contains current coverage report
- Coverage number documented in AGENTS.md matches reality
- CI quality gate passes with actual threshold (no `|| true`)

**Acceptance Criteria:**
- [ ] Fresh coverage report generated
- [ ] AGENTS.md updated with actual numbers
- [ ] Plan to reach 60% if currently below

---

## P1 — Recommended Within 2 Weeks

### P1-1: Triage 14 Skipped Generator Tests

**Priority:** MEDIUM  
**Estimated Effort:** 2–3 hours  
**Category:** Testing

**Problem:**  
14 tests in `banking/data_generators/tests/` are skipped with unknown reasons.

**Remediation Steps:**

1. Identify all skipped tests:
   ```bash
   conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest \
     banking/data_generators/tests/ -v --timeout=120 --no-cov 2>&1 | grep SKIPPED
   ```

2. For each skipped test:
   - If requires service → mark with `@pytest.mark.integration` + skip reason
   - If broken → fix or remove with comment
   - If redundant → remove

3. Target: 0 unexplained skips

**Acceptance Criteria:**
- [ ] Every skip has a documented reason (`reason="..."` in skipif)
- [ ] No silently skipped tests

---

### P1-2: Clean Up Inline Imports in Generators

**Priority:** LOW  
**Estimated Effort:** 1 hour  
**Category:** Code Quality

**Problem:**  
6 generator files have inline `from banking.data_generators.utils.deterministic import REFERENCE_TIMESTAMP` inside functions instead of top-level.

**Files affected:**
- `banking/data_generators/events/transaction_generator.py` (2 inline imports)
- `banking/data_generators/patterns/structuring_pattern_generator.py`
- `banking/data_generators/patterns/fraud_ring_pattern_generator.py`
- `banking/data_generators/patterns/insider_trading_pattern_generator.py`
- `banking/data_generators/patterns/tbml_pattern_generator.py`

**Remediation:**
Move imports to top of each file, alongside existing imports.

**Acceptance Criteria:**
- [ ] All `REFERENCE_TIMESTAMP` imports at top-level
- [ ] All tests still pass

---

### P1-3: Change Default `communication_count` in GenerationConfig

**Priority:** MEDIUM  
**Estimated Effort:** 30 minutes  
**Category:** Code Quality

**Problem:**  
`GenerationConfig.communication_count` defaults to 5000, which causes any test that forgets to set it to run for 90+ seconds.

**Remediation:**

```python
# In banking/data_generators/orchestration/master_orchestrator.py
communication_count: int = 200  # Was 5000 — reduced to prevent test timeouts
```

Update any tests that explicitly rely on the 5000 default.

**Acceptance Criteria:**
- [ ] Default changed to 200 (or similar reasonable value)
- [ ] All tests pass with new default
- [ ] AGENTS.md warning updated if default changes

---

### P1-4: Run Integration Test Suite

**Priority:** MEDIUM  
**Estimated Effort:** 1 hour  
**Category:** Testing

**Problem:**  
Integration tests (202/202) were last run before the deterministic pipeline changes. Need to verify no regressions.

**Remediation:**

```bash
conda run -n janusgraph-analysis PYTHONPATH=. VAULT_ADDR=http://localhost:8200 \
  VAULT_TOKEN=$VAULT_ROOT_TOKEN PULSAR_INTEGRATION=1 \
  python -m pytest tests/integration/ -v --no-cov --timeout=120
```

**Acceptance Criteria:**
- [ ] 202/202 integration tests pass (or document any new skips)

---

### P1-5: Documentation Freshness Audit

**Priority:** LOW  
**Estimated Effort:** 2–3 hours  
**Category:** Documentation

**Problem:**  
313 documentation files across multiple implementation phases. Some may be outdated or contradictory.

**Remediation:**

1. List all docs older than 30 days:
   ```bash
   find docs -name "*.md" -mtime +30 | wc -l
   ```

2. Review and archive outdated phase documents to `docs/archive/`

3. Verify AGENTS.md claims match reality:
   - Self-reported "A+ (98/100)" should be corrected to B (83/100) pending remediation
   - Test counts should match actual numbers

4. Update `docs/INDEX.md` navigation

**Acceptance Criteria:**
- [ ] Stale docs archived
- [ ] AGENTS.md self-assessment matches latest audit
- [ ] INDEX.md reflects current structure

---

## Timeline

| Phase | Items | Duration | Target Date |
|-------|-------|----------|-------------|
| **P0 Sprint** | P0-1 through P0-5 | 3–4 days | 2026-02-19 |
| **P1 Sprint** | P1-1 through P1-5 | 2–3 days | 2026-02-28 |
| **Re-assessment** | Full audit | 1 day | 2026-03-01 |

## Expected Score After Remediation

| Category | Current | After P0 | After P0+P1 |
|----------|---------|----------|-------------|
| Code Quality | 87 | 87 | 92 |
| Testing | 82 | 90 | 95 |
| Security | 72 | 88 | 90 |
| Documentation | 90 | 90 | 95 |
| Infrastructure | 83 | 92 | 93 |
| Determinism | 93 | 93 | 93 |
| **TOTAL** | **83** | **90** | **93** |

---

## Appendix: Verification Commands

```bash
# Post-remediation verification checklist
git ls-files --cached .env                              # Should be empty (P0-1)
pytest tests/unit/test_vault_error_scenarios.py -v      # Should pass (P0-2)
podman ps --filter health=unhealthy                     # Should be empty (P0-3)
gh run list --limit 10                                  # All ✓ (P0-4)
pytest --cov=src --cov=banking --cov-report=term        # Coverage % (P0-5)
pytest banking/data_generators/tests/ -v | grep SKIP    # Documented skips (P1-1)
grep "from banking.*deterministic" banking/data_generators/events/*.py banking/data_generators/patterns/*.py | grep -v "^[^:]*:from"  # No inline imports (P1-2)
pytest tests/integration/ -v --timeout=120              # 202/202 (P1-4)
```
