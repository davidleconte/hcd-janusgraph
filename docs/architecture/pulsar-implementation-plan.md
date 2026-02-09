# Pulsar Implementation Plan

**Date:** 2026-02-04
**Version:** 1.0
**Status:** Planning
**Reference:** Event Sourced Ingestion Architecture

---

## TL;DR

| Question | Answer |
|----------|--------|
| **Is this idempotent?** | ✅ Yes - via `entity_id` as OpenSearch `_id` and Pulsar `sequence_id` deduplication |
| **Update = delete + recreate vector?** | ❌ No - OpenSearch `_id` upsert semantics; only regenerate embedding if text changed |
| **Is CDC mandatory?** | ❌ No (if all writes go through Pulsar); ✅ Yes (if direct JanusGraph writes exist) |

---

## Table of Contents

1. [Architectural Decisions](#architectural-decisions)
2. [Idempotency Analysis](#idempotency-analysis)
3. [Update Semantics for Vectors](#update-semantics-for-vectors)
4. [CDC Requirements](#cdc-requirements)
5. [Implementation Plan](#implementation-plan)
6. [Task Breakdown](#task-breakdown)
7. [Dependencies & Prerequisites](#dependencies--prerequisites)
8. [Risk Assessment](#risk-assessment)

---

## Architectural Decisions

### Decision 1: Idempotency Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IDEMPOTENCY MECHANISMS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Layer              Mechanism                 Behavior                     │
│   ─────────────────────────────────────────────────────────────────────────│
│   Pulsar             sequence_id               Deduplicates retried msgs    │
│   │                                                                         │
│   │                                                                         │
│   ▼                                                                         │
│   JanusGraph         fold().coalesce()         Create if not exists         │
│   │                  or has('entity_id')       Update if exists             │
│   │                                                                         │
│   ▼                                                                         │
│   OpenSearch         _id = entity_id           PUT = upsert                 │
│                      (same ID overwrites)      (idempotent by default)      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Result**: Same event processed multiple times → same final state (idempotent)

### Decision 2: Update Strategy for Vectors

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     UPDATE DECISION FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Incoming Event (event_type = 'update')                                    │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────┐                                  │
│   │  Did text_for_embedding change?      │                                  │
│   └──────────────┬──────────────────────┘                                  │
│                  │                                                          │
│         ┌───────┴───────┐                                                  │
│         │               │                                                  │
│         ▼               ▼                                                  │
│      YES              NO                                                    │
│         │               │                                                  │
│         ▼               ▼                                                  │
│   ┌───────────┐   ┌───────────────────┐                                    │
│   │ Regenerate│   │ Partial Update    │                                    │
│   │ Embedding │   │ (metadata only)   │                                    │
│   │           │   │                   │                                    │
│   │ Full doc  │   │ POST /_update     │                                    │
│   │ replace   │   │ { "doc": {...} }  │                                    │
│   └───────────┘   └───────────────────┘                                    │
│                                                                             │
│   BOTH use same _id = entity_id (NO delete required!)                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Insight**: OpenSearch does NOT require delete + recreate. Using the same `_id`:

- `PUT /index/_doc/{id}` → full document replacement (upsert)
- `POST /index/_update/{id}` → partial update (merge)

**Recommendation**:

- **Simple approach**: Always regenerate embedding on update (wasteful but simple)
- **Optimized approach**: Check if `text_for_embedding` changed; if not, partial update

### Decision 3: CDC Requirement

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CDC DECISION MATRIX                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Write Source                    CDC Needed?    Reason                     │
│   ─────────────────────────────────────────────────────────────────────────│
│                                                                             │
│   Data Generators → Pulsar        ❌ No          Pulsar IS the source       │
│   Notebooks → Pulsar              ❌ No          Pulsar IS the source       │
│   API → Pulsar                    ❌ No          Pulsar IS the source       │
│                                                                             │
│   ──────────────────────── vs ────────────────────────────────────────────│
│                                                                             │
│   Direct Gremlin to JanusGraph    ✅ Yes         Bypasses Pulsar            │
│   Legacy system imports           ✅ Yes         External writes            │
│   Admin/maintenance scripts       ✅ Yes         Manual changes             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**For This Project**:

- If ALL writes go through Pulsar → **CDC NOT required**
- If notebooks/scripts write directly to JanusGraph → **CDC IS required**

**Recommendation**:

1. **Phase 1**: Enforce all writes through Pulsar (no CDC needed)
2. **Phase 2 (optional)**: Add CDC if direct JanusGraph access is needed

---

## Idempotency Analysis

### Pulsar Level

```python
# Producer sends with sequence_id for deduplication
producer.send(
    content=json.dumps(event).encode(),
    partition_key=entity_id,
    sequence_id=hash(event_id)  # Enables deduplication
)

# If producer retries (network issue), Pulsar drops duplicate
# ✅ Same event_id = processed once
```

### JanusGraph Level

```python
# Idempotent create/update pattern
def process_event(g, event):
    entity_id = event['entity_id']

    # fold().coalesce() pattern - idempotent
    g.V().has('entity_id', entity_id) \
        .fold() \
        .coalesce(
            unfold(),  # If exists, use it
            addV(event['entity_type'])  # Else create
        ) \
        .property('entity_id', entity_id) \
        .property('version', event['version']) \
        .next()

# ✅ Same event processed twice = same result
```

### OpenSearch Level

```python
# Index operation with explicit _id is idempotent
actions.append({
    '_op_type': 'index',  # This is an upsert!
    '_index': 'person_vectors',
    '_id': entity_id,  # Same ID = overwrite
    '_source': {
        'entity_id': entity_id,
        'embedding': embedding,
        **metadata
    }
})

# ✅ Same document indexed twice = same result
```

### End-to-End Idempotency Guarantee

| Scenario | Behavior | Result |
|----------|----------|--------|
| Network retry (producer) | Pulsar dedup drops duplicate | ✅ Idempotent |
| Consumer crash mid-batch | NACK → redeliver → reprocess | ✅ Idempotent |
| OpenSearch index twice | Same `_id` = overwrite | ✅ Idempotent |
| JanusGraph process twice | fold().coalesce() | ✅ Idempotent |

---

## Update Semantics for Vectors

### Scenario Analysis

| Scenario | Action | Embedding | Metadata |
|----------|--------|-----------|----------|
| Create new entity | Full index | Generate | Store |
| Update text field | Full replace | **Regenerate** | Update |
| Update metadata only | Partial update | **Keep existing** | Update |
| Delete entity | Delete doc | Remove | Remove |

### Implementation Options

#### Option A: Always Regenerate (Simple)

```python
def process_update(event):
    """Always regenerate embedding on any update."""
    if event.get('text_for_embedding'):
        embedding = generator.encode(event['text_for_embedding'])
    else:
        embedding = [0.0] * 384  # Or fetch existing

    # Full document replace
    opensearch.index(
        index='person_vectors',
        id=event['entity_id'],
        body={
            'embedding': embedding,
            **event['payload']
        }
    )
```

**Pros**: Simple, no state tracking
**Cons**: Wasteful if only metadata changed

#### Option B: Smart Update (Optimized)

```python
def process_update(event):
    """Regenerate embedding only if text changed."""

    # Get existing document
    existing = opensearch.get(
        index='person_vectors',
        id=event['entity_id'],
        ignore=[404]
    )

    if existing and event.get('text_for_embedding'):
        old_text = existing.get('_source', {}).get('text_for_embedding')
        new_text = event['text_for_embedding']

        if old_text != new_text:
            # Text changed - regenerate embedding
            embedding = generator.encode(new_text)
            mode = 'full_replace'
        else:
            # Text unchanged - partial update
            mode = 'partial_update'
    else:
        embedding = generator.encode(event['text_for_embedding'])
        mode = 'full_replace'

    if mode == 'full_replace':
        opensearch.index(
            index='person_vectors',
            id=event['entity_id'],
            body={'embedding': embedding, **event['payload']}
        )
    else:
        opensearch.update(
            index='person_vectors',
            id=event['entity_id'],
            body={'doc': event['payload']}
        )
```

**Pros**: Efficient, saves compute
**Cons**: More complex, requires fetching existing doc

#### Recommendation

**Start with Option A** (simple), optimize to Option B later if:

- High update volume
- Embedding generation is slow/expensive
- Most updates are metadata-only

---

## CDC Requirements

### When CDC is NOT Needed

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PULSAR AS SOLE WRITE PATH                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│   │ Generator   │────►│   PULSAR    │────►│ JanusGraph  │                  │
│   └─────────────┘     │ (Source of  │     └─────────────┘                  │
│                       │  Truth)     │                                       │
│   ┌─────────────┐     │             │     ┌─────────────┐                  │
│   │ Notebook    │────►│             │────►│ OpenSearch  │                  │
│   └─────────────┘     └─────────────┘     └─────────────┘                  │
│                                                                             │
│   ALL WRITES GO THROUGH PULSAR = NO CDC NEEDED                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### When CDC IS Needed

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DIRECT WRITES EXIST                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│   │ Generator   │────►│   PULSAR    │────►│ OpenSearch  │                  │
│   └─────────────┘     └─────────────┘     └─────────────┘                  │
│                                                                             │
│   ┌─────────────┐                         ┌─────────────┐                  │
│   │ Admin Script│─────────────────────────►│ JanusGraph  │                  │
│   └─────────────┘     DIRECT WRITE!       └──────┬──────┘                  │
│                                                   │                         │
│   OpenSearch doesn't know about this change! ←────┘                         │
│                                                                             │
│   SOLUTION: CDC captures JanusGraph changes → Pulsar → OpenSearch          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CDC Implementation (If Needed)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CDC ARCHITECTURE (OPTIONAL)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   JanusGraph/HCD                                                            │
│        │                                                                    │
│        │  Cassandra WAL                                                     │
│        ▼                                                                    │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│   │  Debezium   │────►│   Pulsar    │────►│ OpenSearch  │                  │
│   │  Connector  │     │ (CDC Topic) │     │  Consumer   │                  │
│   └─────────────┘     └─────────────┘     └─────────────┘                  │
│                                                                             │
│   banking/cdc/janusgraph-changes                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**CDC Tools**:

- **Debezium**: Industry standard, supports Cassandra (HCD backend)
- **Pulsar IO Connector**: Native Pulsar integration

### Project Recommendation

| Phase | Approach | Rationale |
|-------|----------|-----------|
| Phase 1 | **No CDC** | Enforce all writes through Pulsar producers |
| Phase 2 | **Optional CDC** | Add if direct JanusGraph access needed |

---

## Implementation Plan

### High-Level Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION TIMELINE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Week 1          Week 2          Week 3          Week 4          Week 5   │
│   ────────────────────────────────────────────────────────────────────────│
│   │               │               │               │               │        │
│   ▼               ▼               ▼               ▼               ▼        │
│   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌─────┐ │
│   │Pulsar     │   │Event      │   │Graph      │   │Vector     │   │E2E  │ │
│   │Infra      │   │Schema &   │   │Consumer   │   │Consumer   │   │Test │ │
│   │           │   │Producers  │   │(Leg 1)    │   │(Leg 2)    │   │     │ │
│   └───────────┘   └───────────┘   └───────────┘   └───────────┘   └─────┘ │
│                                                                             │
│   Week 6                                                                    │
│   ────────────────                                                         │
│   │                                                                         │
│   ▼                                                                         │
│   ┌───────────────────────────────────────┐                                │
│   │Production Hardening & Documentation   │                                │
│   └───────────────────────────────────────┘                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Task Breakdown

### Week 1: Pulsar Infrastructure

| ID | Task | Est. | Deps | Owner |
|----|------|------|------|-------|
| 1.1 | Add Pulsar to docker-compose.full.yml | 2h | - | DevOps |
| 1.2 | Configure Pulsar standalone mode | 1h | 1.1 | DevOps |
| 1.3 | Create namespace: `banking` | 0.5h | 1.2 | DevOps |
| 1.4 | Create topics: persons, accounts, transactions, companies | 1h | 1.3 | DevOps |
| 1.5 | Enable message deduplication | 1h | 1.4 | DevOps |
| 1.6 | Set up Pulsar admin console access | 1h | 1.2 | DevOps |
| 1.7 | Write health check script | 1h | 1.6 | DevOps |
| 1.8 | Update deployment documentation | 2h | 1.7 | Docs |

**Week 1 Deliverables:**

- [ ] Pulsar running in docker-compose
- [ ] Topics created and accessible
- [ ] Admin console at <http://localhost:8080>
- [ ] Deduplication enabled

### Week 2: Event Schema & Producers

| ID | Task | Est. | Deps | Owner |
|----|------|------|------|-------|
| 2.1 | Create `EntityEvent` dataclass | 2h | - | Dev |
| 2.2 | Create `EntityProducer` class | 4h | 2.1 | Dev |
| 2.3 | Add pulsar-client to requirements.txt | 0.5h | - | Dev |
| 2.4 | Update PersonGenerator to use producer | 3h | 2.2 | Dev |
| 2.5 | Update AccountGenerator to use producer | 2h | 2.2 | Dev |
| 2.6 | Update TransactionGenerator to use producer | 2h | 2.2 | Dev |
| 2.7 | Update CompanyGenerator to use producer | 2h | 2.2 | Dev |
| 2.8 | Add producer initialization to notebooks | 4h | 2.2 | Dev |
| 2.9 | Write unit tests for EntityEvent | 2h | 2.1 | QA |
| 2.10 | Write unit tests for EntityProducer | 3h | 2.2 | QA |

**Week 2 Deliverables:**

- [ ] `banking/streaming/events.py` - EntityEvent
- [ ] `banking/streaming/producer.py` - EntityProducer
- [ ] Generators updated with producer injection
- [ ] Unit tests passing

### Week 3: Graph Consumer (Leg 1)

| ID | Task | Est. | Deps | Owner |
|----|------|------|------|-------|
| 3.1 | Create `GraphConsumer` class | 6h | 2.2 | Dev |
| 3.2 | Implement batch processing (100 events) | 3h | 3.1 | Dev |
| 3.3 | Implement transaction handling | 4h | 3.2 | Dev |
| 3.4 | Implement idempotent create/update | 4h | 3.3 | Dev |
| 3.5 | Implement delete handling | 2h | 3.3 | Dev |
| 3.6 | Add error handling (NACK, DLQ) | 3h | 3.5 | Dev |
| 3.7 | Add Prometheus metrics | 3h | 3.6 | Dev |
| 3.8 | Write integration tests | 4h | 3.6 | QA |
| 3.9 | Performance benchmarking | 3h | 3.8 | QA |

**Week 3 Deliverables:**

- [ ] `banking/streaming/graph_consumer.py`
- [ ] Integration tests passing
- [ ] Metrics exposed at /metrics
- [ ] Benchmark: X events/sec

### Week 4: Vector Consumer (Leg 2)

| ID | Task | Est. | Deps | Owner |
|----|------|------|------|-------|
| 4.1 | Create `VectorConsumer` class | 6h | 3.1 | Dev |
| 4.2 | Implement batch embedding generation | 4h | 4.1 | Dev |
| 4.3 | Implement bulk indexing | 3h | 4.2 | Dev |
| 4.4 | Implement update semantics (Option A) | 3h | 4.3 | Dev |
| 4.5 | Implement delete handling | 2h | 4.3 | Dev |
| 4.6 | Add error handling (NACK, DLQ) | 3h | 4.5 | Dev |
| 4.7 | Add Prometheus metrics | 3h | 4.6 | Dev |
| 4.8 | Write integration tests | 4h | 4.6 | QA |
| 4.9 | Test cross-system ID consistency | 4h | 4.8, 3.8 | QA |

**Week 4 Deliverables:**

- [ ] `banking/streaming/vector_consumer.py`
- [ ] Same entity_id in JanusGraph and OpenSearch
- [ ] Integration tests passing
- [ ] Metrics exposed at /metrics

### Week 5: End-to-End Testing

| ID | Task | Est. | Deps | Owner |
|----|------|------|------|-------|
| 5.1 | Create E2E test harness | 4h | 4.9 | QA |
| 5.2 | Test: Create flow (Generator→Pulsar→Both) | 3h | 5.1 | QA |
| 5.3 | Test: Update flow (both consumers) | 3h | 5.2 | QA |
| 5.4 | Test: Delete flow (both consumers) | 2h | 5.3 | QA |
| 5.5 | Test: Idempotency (retry scenarios) | 4h | 5.4 | QA |
| 5.6 | Test: Cross-system query | 4h | 5.5 | QA |
| 5.7 | Test: Consumer failure recovery | 4h | 5.6 | QA |
| 5.8 | Load testing (1000 events/sec) | 4h | 5.7 | QA |
| 5.9 | Document test results | 3h | 5.8 | Docs |

**Week 5 Deliverables:**

- [ ] E2E test suite in `tests/integration/test_streaming.py`
- [ ] All scenarios passing
- [ ] Load test report
- [ ] Test documentation

### Week 6: Production Hardening

| ID | Task | Est. | Deps | Owner |
|----|------|------|------|-------|
| 6.1 | Implement Dead Letter Queue topic | 4h | 5.9 | Dev |
| 6.2 | Add DLQ consumer for monitoring | 3h | 6.1 | Dev |
| 6.3 | Add Grafana dashboard for consumers | 4h | 5.9 | DevOps |
| 6.4 | Add AlertManager rules (lag, errors) | 3h | 6.3 | DevOps |
| 6.5 | Write operations runbook | 4h | 6.4 | Docs |
| 6.6 | Update disaster recovery plan | 3h | 6.5 | Docs |
| 6.7 | Security review (auth, encryption) | 4h | 6.2 | Security |
| 6.8 | Final documentation review | 3h | 6.6 | Docs |

**Week 6 Deliverables:**

- [ ] DLQ topic and monitoring
- [ ] Grafana dashboard
- [ ] Alert rules
- [ ] Operations runbook
- [ ] Updated DR plan

---

## Dependencies & Prerequisites

### Software Dependencies

| Component | Version | Purpose |
|-----------|---------|---------|
| Apache Pulsar | 3.2.0+ | Event streaming |
| pulsar-client (Python) | 3.4.0+ | Producer/Consumer |
| opensearch-py | 2.4.0+ | OpenSearch client |
| sentence-transformers | 2.2.0+ | Embedding generation |

### Infrastructure Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| Pulsar memory | 512MB | 2GB |
| Pulsar disk | 5GB | 20GB |
| Consumer instances | 1 | 3+ |

### Pre-requisites Checklist

- [ ] Docker/Podman with compose support
- [ ] Python 3.11+ with conda environment
- [ ] JanusGraph running and accessible
- [ ] OpenSearch running and accessible
- [ ] Network connectivity between services

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Pulsar complexity | Medium | High | Start with standalone mode |
| Consumer lag | Medium | Medium | Auto-scaling, backpressure |
| ID mismatch | Low | High | Automated consistency checks |
| Embedding latency | Medium | Medium | Batch processing, GPU |
| Data loss | Low | High | Pulsar persistence, DLQ |

---

## Open Questions

1. **GPU for embeddings?** - Consider GPU container for faster embedding generation
2. **Scaling consumers?** - Kubernetes HPA or manual scaling?
3. **Retention policy?** - How long to keep events in Pulsar?
4. **Schema evolution?** - How to handle event schema changes?

---

## Appendix: File Structure

```
banking/
└── streaming/               # NEW DIRECTORY
    ├── __init__.py
    ├── events.py           # EntityEvent dataclass
    ├── producer.py         # EntityProducer class
    ├── graph_consumer.py   # Leg 1 consumer
    ├── vector_consumer.py  # Leg 2 consumer
    └── dlq_handler.py      # Dead letter queue handler

config/
└── compose/
    └── docker-compose.full.yml  # Updated with Pulsar

tests/
└── integration/
    └── test_streaming.py   # E2E streaming tests
```

---

**Document Status**: Planning
**Last Updated**: 2026-02-04
**Next Steps**: Review and approve Week 1 tasks

Co-Authored-By: David Leconte <team@example.com>
