# Contract Freeze Matrix (FR-002)

**Date:** 2026-03-27  
**Created (UTC):** 2026-03-27T18:19:26Z  
**POC:** Platform Engineering + Domain Engineering + Compliance  
**Status:** Active (Immutable Contract Baseline)  
**TL;DR:** This matrix freezes current cross-system contracts (IDs, streaming events, index fields, API/repository outputs) to prevent regressions during fraud-realism improvements.

---

## 1) Purpose and Scope

This contract freeze applies to the integration path:

**data generators -> streaming events -> graph/search consumers -> repository/API outputs -> notebooks**

Any change violating these contracts requires:
1. explicit contract versioning decision,
2. synchronized code/test updates,
3. full gate revalidation under go/no-go policy.

---

## 2) Immutable Contract Matrix

| Contract ID | Domain | Source of Truth | Frozen Contract | Must-Not-Break Invariants | Validation Command(s) |
|---|---|---|---|---|---|
| CF-001 | Deterministic ID generation | `banking/data_generators/utils/deterministic.py` | `seeded_uuid_hex(prefix="", seed=None)` deterministic SHA-256/counter mechanism; current generated ID shape is 12-char uppercase hex for base entities; prefixed forms exist (e.g., `TXN-...`, `TRADE-...`) | Seeded reproducibility and stable ID semantics across runs | `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/data_generators/tests -v --no-cov` |
| CF-002 | Streaming event wire schema | `banking/streaming/events.py` | Required event fields: `entity_id`, `event_type`, `entity_type`, `payload`; valid enums for event/entity types; topic convention `persistent://public/banking/{entity_type}s-events` with `company -> companies-events` | Schema compatibility for producer/consumer; no silent field removal/rename | `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/streaming/tests -v --no-cov` |
| CF-003 | Streaming ordering/partitioning | `banking/streaming/events.py` + producer paths | Partition key behavior is tied to `entity_id` for per-entity order consistency | Do not alter per-entity ordering semantics without migration strategy | `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest banking/streaming/tests -v --no-cov` |
| CF-004 | OpenSearch embedding dimensions | `src/python/utils/embedding_generator.py` | Model dimension expectations: MiniLM=384, MPNet=768; embedding field contract uses vector field expectations in search paths | No ingest with incompatible vector dimensions/index mappings | `conda run -n janusgraph-analysis PYTHONPATH=. OPENSEARCH_USE_SSL=false python -m pytest tests/integration -k opensearch -v --no-cov --timeout=120` |
| CF-005 | Repository flattening contract | `src/python/repository/graph_repository.py` | Repository outputs must keep flattening semantics (`_flatten_value_map`) so JanusGraph list wrappers do not leak into API/notebook contracts | Response shape stability for downstream API/notebooks | `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest tests/unit -v --no-cov` |
| CF-006 | API response model contract | `src/python/api/models.py` | Key fraud/AML response models (e.g., UBO, structuring outputs) must remain backward-compatible unless explicitly versioned | No breaking field rename/removal without migration/versioning | `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest tests/unit -v --no-cov` |
| CF-007 | Deterministic proof compatibility | `scripts/testing/*`, `scripts/deployment/*` | Current deterministic proof flow must remain passable after contract-safe changes | Gate order, drift behavior, baseline comparability | `bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json` |

---

## 3) Backward-Compatibility Rules

1. **No breaking schema changes in place** for event/API payloads without explicit contract versioning.
2. **Additive-first rule:** new fields allowed when backward-compatible; removals/renames require migration docs/tests.
3. **Index compatibility first:** OpenSearch mapping changes must include dimension and query-compat checks.
4. **Notebook consumers protected:** repository/API shape changes must not break existing notebook assumptions.

---

## 4) Known Gaps (Must Be Addressed in Follow-up Tickets)

1. No dedicated automated pre-ingest guard that enforces embedding dimension compatibility before ingestion.
2. No single unified contract test that validates generator IDs -> stream payload -> repository/API -> notebook assumptions end-to-end.
3. Some domain entities (e.g., travel/cross-border cases) are enum-listed but not yet fully formalized as stable response contracts.

---

## 5) Non-Freeze / Unverified Claims (Explicitly Excluded)

The following are intentionally **not frozen** due to uncertainty or prior mismatch:

- 32-char ID-length claims (current deterministic utility indicates 12-char base IDs in active behavior).
- Any undocumented OpenSearch field contract not traceable to current code paths.
- Any notebook-only inferred schema not represented in source code models/contracts.

---

## 6) FR-002 Completion Criteria

FR-002 is considered complete when:
1. This matrix is published and checkpointed.
2. Required validation commands pass on current branch.
3. Any detected contract gaps are ticketed (P1/P2) without breaking baseline behavior.
4. Future tickets reference this matrix in their gate checklist.

---

## 7) Related Documents

- `docs/operations/baseline-assessment-matrix-2026-03-27.md`
- `docs/operations/baseline-protection-test-plan.md`
- `docs/operations/fraud-realism-ticketized-execution-board-2026-03-27.md`
- `docs/operations/do-not-break-remediation-improvement-plan-2026-03-27.md`

---

## 8) Execution Evidence Update (UTC 2026-03-27)

### CF-004 remediation applied
- **Issue observed:** `TypeError: IndicesClient.exists() takes 1 positional argument but 2 positional arguments ... were given`
- **Location:** `tests/integration/test_e2e_streaming.py` (`TestE2EOpenSearchIntegration::test_opensearch_index_operations`)
- **Root cause:** Positional usage against OpenSearch client index APIs in current `opensearch-py` behavior.
- **Fix applied (contract-safe):**
  - `client.indices.exists(test_index)` -> `client.indices.exists(index=test_index)`
  - `client.indices.create(test_index)` -> `client.indices.create(index=test_index)`
  - `client.indices.delete(test_index)` -> `client.indices.delete(index=test_index)`

### Validation evidence
1. Targeted CF-004 test:
   - `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest tests/integration/test_e2e_streaming.py::TestE2EOpenSearchIntegration::test_opensearch_index_operations -v --no-cov --timeout=120`
   - **Result:** `PASSED`
2. Full E2E streaming integration file:
   - `conda run -n janusgraph-analysis PYTHONPATH=. python -m pytest tests/integration/test_e2e_streaming.py -v --no-cov --timeout=120`
   - **Result:** `12 passed` (0 failed)

### FR-002 gate impact
- **CF-004 status:** ✅ Restored/Green
- **Contract impact:** No schema or behavior broadening; compatibility fix only for client invocation semantics.
- **Risk level:** Low (localized test compatibility correction, validated by targeted and full-file integration pass).
