# Architectural Improvement Plan

**Date:** 2026-02-09
**Author:** David Leconte / AdaL
**Status:** In Progress
**Version:** 1.1

---

## TL;DR

The HCD + JanusGraph project has strong infrastructure (security, CI, monitoring, compliance) but its **internal software architecture** has accumulated structural debt. This plan addresses 10 improvements across 3 phases, targeting testability, maintainability, and clean domain boundaries. Estimated total effort: **3–5 engineering days**.

---

## Table of Contents

1. [Current State Assessment](#1-current-state-assessment)
2. [Problem Catalogue](#2-problem-catalogue)
3. [Phase 1 — Foundation (Day 1)](#3-phase-1--foundation-day-1)
4. [Phase 2 — Separation of Concerns (Days 2–3)](#4-phase-2--separation-of-concerns-days-23)
5. [Phase 3 — Advanced Patterns (Days 4–5)](#5-phase-3--advanced-patterns-days-45)
6. [Migration Strategy](#6-migration-strategy)
7. [Risk Assessment](#7-risk-assessment)
8. [Success Metrics](#8-success-metrics)
9. [Appendix — File-Level Impact Map](#9-appendix--file-level-impact-map)

---

## 1. Current State Assessment

### Strengths

- ✅ Centralized configuration via `pydantic-settings`
- ✅ Circuit breaker + retry logic (`src/python/utils/resilience.py`)
- ✅ 645 unit tests passing with good coverage on core modules
- ✅ PII-sanitized logging
- ✅ OpenTelemetry tracing integration
- ✅ Comprehensive compliance infrastructure

### Weaknesses

- ❌ Dual exception hierarchies creating confusion
- ❌ Monolithic API module (729 lines, 16 models, all routes)
- ✅ ~~Gremlin queries embedded in business logic~~ → Repository Pattern implemented
- ❌ No dependency injection — components create their own dependencies
- ❌ Blurry module boundaries in `banking/`
- ❌ Several 600–1000 line files violating Single Responsibility
- ❌ No abstract interfaces/protocols defining contracts
- ❌ Configuration sprawl (some modules use `os.getenv()` directly)

### Key Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Largest file (lines) | 999 (`fraud_detection.py`) | ≤400 |
| Models in `main.py` | 16 | 0 (moved to models/) |
| Exception modules | 2 (conflicting) | 1 |
| Direct DB queries in domain logic | ~~15~~ 0 (API routers) | 0 |
| Modules using `os.getenv()` directly | 5+ | 0 |

---

## 2. Problem Catalogue

### P1: Dual Exception Hierarchies

**Location:**

- `src/python/client/exceptions.py` — `ConnectionError`, `ValidationError`, `TimeoutError`, `QueryError`
- `src/python/utils/error_codes.py` — `ConnectionError`, `ValidationError`, `NotFoundError`, `AppException`

**Impact:** Developers don't know which to import. Tests catch the wrong one. Error handling is inconsistent.

**Root Cause:** Organic growth without a defined error strategy.

### P2: Monolithic API Module

**Location:** `src/python/api/main.py` (729 lines)

**Contains:**

- 16 Pydantic request/response models
- FastAPI app creation + lifespan
- CORS, rate limiting, error handling middleware
- Authentication logic
- 10+ route handlers
- Database connection management

**Impact:** Hard to test individual routes, impossible to reuse models elsewhere, merge conflicts in team development.

### P3: No Repository Layer

**Location:**

- `banking/fraud/fraud_detection.py` (999 lines) — raw Gremlin queries inline
- `banking/aml/structuring_detection.py` (521 lines) — raw Gremlin queries inline
- `banking/analytics/detect_insider_trading.py` (844 lines) — raw Gremlin queries inline

**Impact:** Business logic is untestable without a running JanusGraph instance. Database migration would require rewriting every detection module.

**Example of current coupling:**

```python
# Inside FraudDetector.detect_fraud_rings()
result = self.client.execute(
    "g.V().hasLabel('Person').as('p')"
    ".out('owns').hasLabel('Account').as('a')"
    ".in('owns').where(neq('p'))"
    ".path().by('name').by('accountNumber')"
)
```

This should be:

```python
# Inside FraudDetector.detect_fraud_rings()
candidates = self.graph_repo.get_shared_account_holders(min_shared=2)
```

### P4: No Dependency Injection

**Symptom:** Detection classes instantiate `JanusGraphClient()` internally or receive a raw connection.

**Impact:** Tests need to mock at the module level with `@patch`. Changing configuration requires editing class internals.

### P5: Blurry Banking Module Boundaries

**Current `banking/` structure:**

```text
banking/
├── aml/                    # Domain logic
├── analytics/              # Query analytics
├── compliance/             # Infrastructure
├── data/                   # Legacy data scripts
├── data_generators/        # Dev tooling
├── fraud/                  # Domain logic
├── notebooks/              # Demos
├── queries/                # Raw queries
├── schema/                 # Graph schema
├── scripts/                # Operational scripts
├── streaming/              # Infrastructure (Pulsar)
└── tests/                  # Cross-module tests
```

**Issue:** Domain logic (aml, fraud), infrastructure (streaming, compliance), tooling (data_generators), and presentation (notebooks) are all siblings with no clear layering.

### P6: Large Files Violating SRP

| File | Lines | Responsibilities |
|------|-------|-----------------|
| `fraud_detection.py` | 999 | Detection algorithms + DB queries + result formatting + risk scoring |
| `validation.py` | 912 | 30+ validator methods for different data types |
| `detect_insider_trading.py` | 844 | Detection + pattern matching + graph traversal |
| `janusgraph_loader.py` | 749 | Schema creation + ETL + validation + error handling |
| `api/main.py` | 729 | See P2 above |

### P7: No Abstract Interfaces

No `Protocol` or `ABC` classes exist. All contracts are implicit — you discover what a class expects by reading its code.

### P8: Configuration Sprawl

Modules bypassing `Settings`:

- `src/python/utils/vector_search.py` — `os.getenv('OPENSEARCH_USERNAME')`
- `src/python/utils/tracing.py` — `os.getenv('OTEL_SERVICE_NAME')`
- `banking/streaming/producer.py` — `os.getenv('PULSAR_URL')`
- Multiple other modules

### P9: No API Versioning

All routes at root level (`/healthz`, `/graph/stats`, `/ubo/discover`). No `/api/v1/` prefix for breaking change management.

### P10: No Internal Event Pattern

When fraud is detected, compliance reporting needs to be notified. Currently this requires direct function calls, creating tight coupling between detection and compliance.

---

## 3. Phase 1 — Foundation (Day 1)

### 3.1 Consolidate Exception Hierarchy

**Effort:** 1–2 hours | **Risk:** Low | **Files affected:** ~15

**Plan:**

1. Create `src/python/exceptions.py` as the single source of truth:

    ```python
    class AppError(Exception):
        """Base for all application errors."""
        def __init__(self, message: str, code: str = "UNKNOWN"):
            self.code = code
            super().__init__(message)

    class ConnectionError(AppError): ...
    class QueryError(AppError): ...
    class TimeoutError(AppError): ...
    class ValidationError(AppError): ...
    class NotFoundError(AppError): ...
    class AuthenticationError(AppError): ...
    class AuthorizationError(AppError): ...
    class CircuitOpenError(AppError): ...
    ```

2. Update `src/python/client/exceptions.py` to re-export from the new module (backward compat)
3. Update `src/python/utils/error_codes.py` to re-export from the new module
4. Grep all imports and update progressively
5. Run tests after each batch of changes

**Backward Compatibility:** Keep old modules as re-exports for one release cycle.

### 3.2 Extract Pydantic Models from `main.py`

**Effort:** 1 hour | **Risk:** Low | **Files affected:** 3–5

**Plan:**

1. Create `src/python/api/models/` directory:

    ```text
    src/python/api/models/
    ├── __init__.py         # Re-export all models
    ├── common.py           # ErrorResponse, PaginationParams
    ├── health.py           # HealthResponse, LivenessResponse
    ├── ubo.py              # UBORequest, UBOOwner, UBOResponse
    ├── structuring.py      # StructuringAlertRequest, StructuringAlert, StructuringResponse
    └── graph.py            # NetworkNode, NetworkEdge, NetworkResponse, GraphStatsResponse
    ```

2. Move models (cut-paste, no logic changes)
3. Update imports in `main.py`
4. Update test imports in `tests/unit/test_api_main.py`

### 3.3 Split API Routes into Routers

**Effort:** 2–3 hours | **Risk:** Medium (URL changes if not careful) | **Files affected:** 5–8

**Plan:**

1. Create `src/python/api/routers/`:

    ```text
    src/python/api/routers/
    ├── __init__.py
    ├── health.py           # GET /healthz, GET /readyz, GET /health
    ├── ubo.py              # POST /api/v1/ubo/discover
    ├── structuring.py      # POST /api/v1/structuring/detect
    ├── fraud.py            # POST /api/v1/fraud/rings, etc.
    └── graph.py            # GET /api/v1/graph/stats, etc.
    ```

2. Refactor `main.py` to:

    ```python
    # src/python/api/app.py (renamed from main.py)
    from src.python.api.routers import health, ubo, structuring, fraud, graph

    app = FastAPI(...)
    app.include_router(health.router)
    app.include_router(ubo.router, prefix="/api/v1")
    app.include_router(structuring.router, prefix="/api/v1")
    app.include_router(fraud.router, prefix="/api/v1")
    app.include_router(graph.router, prefix="/api/v1")
    ```

3. Keep old routes as redirects for backward compatibility (302 → new path)

**API Versioning:** Add `/api/v1/` prefix to all business routes. Health checks remain at root.

---

## 4. Phase 2 — Separation of Concerns (Days 2–3)

### 4.1 Extract Graph Repository Layer ✅ COMPLETED (2026-02-10)

**Effort:** 4–6 hours | **Risk:** Medium-High (touches core detection logic) | **Files affected:** 8–12

> **Implementation:** `src/python/repository/graph_repository.py` (207 lines, 100% test coverage).
> All 4 API routers refactored to use `GraphRepository` — zero inline Gremlin.
> 25 unit tests in `tests/unit/repository/test_graph_repository.py`.

**Plan:**

1. Define the repository protocol:

    ```python
    # src/python/repositories/protocols.py
    from typing import Protocol, List, Dict, Any, Optional
    from datetime import datetime

    class GraphRepository(Protocol):
        def get_person_by_id(self, person_id: str) -> Dict[str, Any]: ...
        def get_account_transactions(
            self, account_id: str, since: datetime, until: datetime
        ) -> List[Dict]: ...
        def get_shared_account_holders(self, min_shared: int) -> List[Dict]: ...
        def get_person_network(self, person_id: str, depth: int) -> Dict: ...
        def get_transaction_chain(
            self, start_account: str, max_hops: int
        ) -> List[Dict]: ...
        def count_vertices(self, label: Optional[str] = None) -> int: ...
        def count_edges(self, label: Optional[str] = None) -> int: ...
    ```

2. Implement the JanusGraph-specific repository:

    ```python
    # src/python/repositories/janusgraph_repo.py
    class JanusGraphRepository:
        def __init__(self, client: JanusGraphClient):
            self._client = client

        def get_account_transactions(
            self, account_id: str, since: datetime, until: datetime
        ) -> List[Dict]:
            query = (
                "g.V().has('Account', 'accountId', account_id)"
                ".inE('transaction').has('timestamp', between(since, until))"
                ".outV().valueMap(true)"
            )
            return self._client.execute(query)
    ```

3. Refactor detection modules to use repository:
    - `banking/fraud/fraud_detection.py` → inject `GraphRepository`
    - `banking/aml/structuring_detection.py` → inject `GraphRepository`
    - `banking/analytics/detect_insider_trading.py` → inject `GraphRepository`

4. Create `InMemoryGraphRepository` for testing:

    ```python
    # tests/fixtures/mock_graph_repo.py
    class InMemoryGraphRepository:
        def __init__(self, data: Dict[str, List]):
            self._persons = data.get("persons", [])
            self._transactions = data.get("transactions", [])
    ```

**Migration Strategy:**

- Start with `fraud_detection.py` as the pilot
- Extract queries one method at a time
- Run tests after each extraction
- Once validated, apply same pattern to remaining modules

### 4.2 Implement Dependency Injection Container

**Effort:** 2–3 hours | **Risk:** Low | **Files affected:** 5–8

**Plan:**

1. Create a simple container (no framework needed):

    ```python
    # src/python/container.py
    from dataclasses import dataclass, field
    from typing import Optional

    @dataclass
    class Container:
        settings: Settings
        _graph_client: Optional[JanusGraphClient] = field(default=None, init=False)
        _graph_repo: Optional[JanusGraphRepository] = field(default=None, init=False)

        @property
        def graph_client(self) -> JanusGraphClient:
            if not self._graph_client:
                self._graph_client = JanusGraphClient(
                    host=self.settings.janusgraph_host,
                    port=self.settings.janusgraph_port,
                    username=self.settings.janusgraph_username,
                    password=self.settings.janusgraph_password,
                )
            return self._graph_client

        @property
        def graph_repo(self) -> JanusGraphRepository:
            if not self._graph_repo:
                self._graph_repo = JanusGraphRepository(self.graph_client)
            return self._graph_repo

        @property
        def fraud_detector(self) -> FraudDetector:
            return FraudDetector(self.graph_repo)

        @property
        def structuring_detector(self) -> StructuringDetector:
            return StructuringDetector(self.graph_repo)

        def close(self) -> None:
            if self._graph_client:
                self._graph_client.close()
    ```

2. Wire into FastAPI lifespan:

    ```python
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings = get_settings()
        container = Container(settings=settings)
        app.state.container = container
        yield
        container.close()
    ```

3. Use in route handlers via dependency:

    ```python
    def get_container(request: Request) -> Container:
        return request.app.state.container

    @router.post("/fraud/rings")
    def detect_fraud_rings(
        request: FraudRequest,
        container: Container = Depends(get_container),
    ):
        detector = container.fraud_detector
        return detector.detect_rings(request.params)
    ```

### 4.3 Define Abstract Protocols

**Effort:** 1–2 hours | **Risk:** Low | **Files affected:** 3–5

**Plan:**

1. Create `src/python/protocols.py`:

    ```python
    from typing import Protocol, List, Dict, Any

    class GraphClient(Protocol):
        def execute(self, query: str) -> List[Any]: ...
        def connect(self) -> None: ...
        def close(self) -> None: ...
        def is_connected(self) -> bool: ...

    class DetectionService(Protocol):
        def detect(self, params: Dict[str, Any]) -> Dict[str, Any]: ...
    ```

2. Type-annotate key functions to accept protocols instead of concrete classes
3. This enables swapping JanusGraph for Neo4j/Neptune with zero domain code changes

---

## 5. Phase 3 — Advanced Patterns (Days 4–5)

### 5.1 Decompose Large Files

**Effort:** 3–4 hours | **Risk:** Medium

**`fraud_detection.py` (999 lines) → split into:**

```text
banking/fraud/
├── __init__.py
├── detector.py             # FraudDetector orchestrator (~200 lines)
├── ring_detection.py       # Fraud ring algorithms (~200 lines)
├── velocity_checks.py      # Velocity-based detection (~150 lines)
├── risk_scoring.py         # Risk score calculation (~150 lines)
└── models.py               # Fraud-specific data models (~100 lines)
```

**`validation.py` (912 lines) → split into:**

```text
src/python/utils/validation/
├── __init__.py             # Re-export Validator class
├── base.py                 # Base Validator + common utilities
├── string_validators.py    # String, email, URL validation
├── numeric_validators.py   # Number, port, range validation
├── graph_validators.py     # Gremlin query validation
└── date_validators.py      # Date/time validation
```

### 5.2 Consolidate Configuration Access

**Effort:** 1–2 hours | **Risk:** Low | **Files affected:** 5–8

**Plan:**

1. Remove all `os.getenv()` calls from business modules
2. Add missing fields to `Settings`:

    ```python
    class Settings(BaseSettings):
        # ... existing fields ...
        opensearch_username: Optional[str] = None
        opensearch_password: Optional[str] = None
        pulsar_url: str = "pulsar://localhost:6650"
        otel_service_name: str = "janusgraph-client"
    ```

3. Pass settings through DI container to all consumers

### 5.3 Internal Event Bus (Optional)

**Effort:** 3–4 hours | **Risk:** Medium

**Plan:**

1. Create a simple in-process event bus:

    ```python
    # src/python/events.py
    from dataclasses import dataclass
    from typing import Callable, Dict, List

    @dataclass
    class DomainEvent:
        event_type: str
        payload: Dict

    class EventBus:
        def __init__(self):
            self._handlers: Dict[str, List[Callable]] = {}

        def subscribe(self, event_type: str, handler: Callable) -> None:
            self._handlers.setdefault(event_type, []).append(handler)

        def publish(self, event: DomainEvent) -> None:
            for handler in self._handlers.get(event.event_type, []):
                handler(event)
    ```

2. Use for cross-domain communication:
    - Fraud detected → publish `FraudAlertEvent`
    - Compliance listener → logs audit event
    - Streaming listener → publishes to Pulsar

### 5.4 Restructure Banking Module

**Effort:** 2–3 hours | **Risk:** Medium (many path changes)

**Proposed structure:**

```text
banking/
├── domain/                 # Pure business logic
│   ├── aml/
│   │   ├── __init__.py
│   │   ├── structuring_detection.py
│   │   └── enhanced_structuring_detection.py
│   ├── fraud/
│   │   ├── __init__.py
│   │   ├── detector.py
│   │   ├── ring_detection.py
│   │   ├── velocity_checks.py
│   │   └── risk_scoring.py
│   └── compliance/
│       ├── __init__.py
│       ├── audit_logger.py
│       └── compliance_reporter.py
├── analytics/              # Read-side analytics
│   ├── detect_insider_trading.py
│   ├── detect_tbml.py
│   └── aml_structuring_detector.py
├── generators/             # Dev tooling (renamed from data_generators)
│   └── ... (unchanged internally)
├── infrastructure/         # External system integrations
│   ├── streaming/          # Pulsar
│   ├── loaders/            # JanusGraph bulk load
│   └── schema/             # Graph schema definitions
├── notebooks/              # Interactive demos
└── tests/                  # Cross-module tests
```

**Migration:** Use `git mv` to preserve history. Update all imports via `ruff` or `rope`.

---

## 6. Migration Strategy

### Principles

1. **Incremental** — each change is independently deployable
2. **Backward compatible** — old imports work via re-exports for 1 release
3. **Test-driven** — run full suite after every structural change
4. **Feature-flag optional** — new patterns can coexist with old ones

### Validation Checkpoints

After each sub-task:

1. `ruff check src/ banking/` → 0 errors
2. `pytest tests/ -q` → 645+ passed, 0 failed
3. `git commit` with descriptive message

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Import breakage in notebooks | High | Low | Keep re-exports in old locations |
| Test failures from refactoring | Medium | Medium | Run full suite after every change |
| API URL changes break consumers | Medium | High | Add redirect middleware for old paths |
| Over-engineering the DI | Low | Medium | Keep it simple — no framework, just a dataclass |
| Merge conflicts with other devs | Medium | Medium | Communicate plan, merge to master frequently |

---

## 8. Success Metrics

| Metric | Before | After Phase 1 | After Phase 3 |
|--------|--------|--------------|--------------|
| `main.py` lines | 729 | ~100 | ~100 |
| Largest file | 999 | 999 | ≤400 |
| Exception modules | 2 | 1 | 1 |
| Direct Gremlin in domain | ~15 queries | ~15 | 0 |
| `os.getenv()` in business code | 5+ | 5+ | 0 |
| Test isolation (no mock.patch) | Poor | Improved | Good |
| API versioning | None | `/api/v1/` | `/api/v1/` |

---

## 9. Appendix — File-Level Impact Map

### Phase 1 Files

| File | Action |
|------|--------|
| `src/python/exceptions.py` | **CREATE** — unified exception hierarchy |
| `src/python/client/exceptions.py` | MODIFY — re-export from new location |
| `src/python/utils/error_codes.py` | MODIFY — re-export from new location |
| `src/python/api/models/*.py` | **CREATE** — extracted from main.py |
| `src/python/api/routers/*.py` | **CREATE** — extracted from main.py |
| `src/python/api/main.py` | MODIFY → rename to `app.py`, slim down |

### Phase 2 Files

| File | Action |
|------|--------|
| `src/python/protocols.py` | **CREATE** — abstract interfaces |
| `src/python/repositories/protocols.py` | **CREATE** — repository contracts |
| `src/python/repositories/janusgraph_repo.py` | **CREATE** — JanusGraph implementation |
| `src/python/container.py` | **CREATE** — DI container |
| `banking/fraud/fraud_detection.py` | MODIFY — inject repository |
| `banking/aml/structuring_detection.py` | MODIFY — inject repository |
| `tests/fixtures/mock_graph_repo.py` | **CREATE** — test repository |

### Phase 3 Files

| File | Action |
|------|--------|
| `banking/fraud/detector.py` | **CREATE** — split from fraud_detection.py |
| `banking/fraud/ring_detection.py` | **CREATE** — split |
| `banking/fraud/velocity_checks.py` | **CREATE** — split |
| `banking/fraud/risk_scoring.py` | **CREATE** — split |
| `src/python/utils/validation/*.py` | **CREATE** — split from validation.py |
| `src/python/events.py` | **CREATE** — internal event bus |
| `src/python/config/settings.py` | MODIFY — add missing fields |

---

## Decision Log

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| No DI framework | Overkill for project size; simple dataclass suffices | `dependency-injector`, `python-inject` |
| Protocols over ABC | Runtime structural subtyping, no inheritance required | ABC with `@abstractmethod` |
| In-process event bus | Internal coordination only; Pulsar handles external streaming | Celery, Redis pub/sub |
| `/api/v1/` prefix | Standard REST practice; enables future v2 | No versioning, header-based |
| Keep old import paths | Minimizes breakage for notebooks and external consumers | Hard cut-over |

---

*This plan should be reviewed before implementation begins. Each phase can be executed independently.*
