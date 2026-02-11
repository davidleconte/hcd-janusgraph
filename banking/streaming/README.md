# Banking Streaming Module

Event-sourced streaming architecture for real-time data ingestion into JanusGraph and OpenSearch.

**Created**: 2026-02-04 (6-Week Implementation)
**Status**: Production Ready ✅

---

## Overview

This module provides Apache Pulsar-based event streaming that enables:

- **Real-time ingestion**: Entities published to Pulsar as events
- **Dual-leg consumption**: Parallel writes to JanusGraph (graph) and OpenSearch (vector)
- **ID consistency**: Same UUID across Pulsar, JanusGraph, and OpenSearch
- **Fault tolerance**: Dead Letter Queue (DLQ) for failed messages

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Data Generators │────▶│  Apache Pulsar  │────▶│   Consumers     │
└─────────────────┘     │  (Event Bus)    │     │                 │
                        └────────┬────────┘     │  ┌───────────┐  │
                                 │              │  │ GraphCons │──┼──▶ JanusGraph
                                 │              │  └───────────┘  │
                                 │              │                 │
                                 │              │  ┌───────────┐  │
                                 └──────────────┼──│VectorCons │──┼──▶ OpenSearch
                                                │  └───────────┘  │
                                                └─────────────────┘
```

---

## Pulsar CLI Access

For debugging and administration, use the `pulsar-cli` container:

```bash
# List topics
podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin topics list public/banking

# Check topic stats
podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin topics stats persistent://public/banking/persons-events

# Consume messages (debugging)
podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-client consume -s debug-sub persistent://public/banking/persons-events -n 5

# Peek at messages without consuming
podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin topics peek-messages persistent://public/banking/persons-events -n 5 -s my-subscription
```

---

## Components

| Component | File | Description |
|-----------|------|-------------|
| **EntityEvent** | `events.py` | Event schema with entity_id, type, payload, metadata |
| **EntityProducer** | `producer.py` | Publishes events to Pulsar topics |
| **GraphConsumer** | `graph_consumer.py` | Leg 1: Writes to JanusGraph |
| **VectorConsumer** | `vector_consumer.py` | Leg 2: Writes to OpenSearch |
| **StreamingOrchestrator** | `streaming_orchestrator.py` | Integrates generators with streaming |
| **DLQHandler** | `dlq_handler.py` | Handles failed messages with retry/archive |
| **StreamingMetrics** | `metrics.py` | Prometheus metrics for monitoring |
| **EntityConverter** | `entity_converter.py` | Converts generated entities to events |

---

## Topics

All topics use persistent storage with the `public/banking` namespace:

| Topic | Entity Type | Partition Key |
|-------|-------------|---------------|
| `persons-events` | Person | `entity_id` |
| `accounts-events` | Account | `entity_id` |
| `transactions-events` | Transaction | `entity_id` |
| `companies-events` | Company | `entity_id` |
| `communications-events` | Communication | `entity_id` |
| `dlq-events` | Failed events | Original `entity_id` |

---

## Quick Start

### 1. Basic Event Publishing

```python
from banking.streaming import EntityProducer, create_person_event

# Create producer
producer = EntityProducer(pulsar_url="pulsar://localhost:6650")

# Create and publish event
event = create_person_event(
    person_id="person-123",
    name="John Doe",
    payload={"first_name": "John", "last_name": "Doe", "email": "john@example.com"},
    source="DataGenerator"
)

producer.send(event)
producer.flush()
producer.close()
```

### 2. Using StreamingOrchestrator

```python
from banking.streaming import StreamingOrchestrator, StreamingConfig
from pathlib import Path

config = StreamingConfig(
    seed=42,
    person_count=100,
    company_count=20,
    account_count=200,
    transaction_count=500,
    communication_count=100,
    pulsar_url="pulsar://localhost:6650",
    output_dir=Path("./output")
)

with StreamingOrchestrator(config) as orchestrator:
    stats = orchestrator.generate_all()
    print(f"Published {stats.events_published} events")
```

### 3. Converting Existing Entities

```python
from banking.streaming import convert_entity_to_event
from banking.data_generators import PersonGenerator

# Generate entity
generator = PersonGenerator(seed=42)
person = generator.generate()

# Convert to event
event = convert_entity_to_event(person, source="MyApp")
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PULSAR_URL` | `pulsar://localhost:6650` | Pulsar broker URL |
| `OPENSEARCH_USE_SSL` | `true` | Enable SSL for OpenSearch |
| `JANUSGRAPH_PORT` | `8182` | JanusGraph Gremlin port |

### StreamingConfig Options

```python
StreamingConfig(
    # Generation counts
    person_count=100,
    company_count=20,
    account_count=200,
    transaction_count=500,
    communication_count=100,

    # Streaming options
    pulsar_url="pulsar://localhost:6650",
    use_mock_producer=False,  # True for testing
    streaming_enabled=True,

    # Output
    output_dir=Path("./output"),
    seed=42  # For reproducibility
)
```

---

## Metrics

Prometheus metrics available at `/metrics`:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `streaming_events_published_total` | Counter | entity_type, source | Events published |
| `streaming_events_publish_failed_total` | Counter | entity_type, error_type | Failed publishes |
| `streaming_publish_latency_seconds` | Histogram | entity_type | Publish latency |
| `streaming_events_consumed_total` | Counter | entity_type, consumer_type | Events consumed |
| `streaming_dlq_messages_total` | Counter | entity_type, failure_reason | DLQ messages |

### Get Metrics Output

```python
from banking.streaming import get_metrics_output

# Get Prometheus format
metrics_text = get_metrics_output()
print(metrics_text)
```

---

## Testing

### Run All Streaming Tests

```bash
# Activate conda environment
conda activate janusgraph-analysis

# Run unit tests
PYTHONPATH=. pytest banking/streaming/tests/ -v

# Run E2E tests (requires services running)
PYTHONPATH=. OPENSEARCH_USE_SSL=false pytest tests/integration/test_e2e_streaming.py -v
```

### Test Coverage

| Module | Coverage | Tests |
|--------|----------|-------|
| events.py | 95% | 20 |
| producer.py | 90% | 14 |
| entity_converter.py | 92% | 35 |
| streaming_orchestrator.py | 88% | 15 |
| dlq_handler.py | 85% | 10 |
| **Total** | **90%** | **94** |

---

## ID Consistency Guarantee

The architecture guarantees that the same UUID is used across all systems:

```
EntityEvent.entity_id  ─┬─▶ Pulsar partition_key
                        ├─▶ JanusGraph vertex.entity_id property
                        └─▶ OpenSearch document._id
```

This enables:

- Cross-system joins by ID
- Deduplication at each layer
- Consistent audit trails

---

## Error Handling

### Dead Letter Queue (DLQ)

Failed messages are automatically routed to DLQ with retry logic:

```python
from banking.streaming import DLQHandler

dlq = DLQHandler(
    pulsar_url="pulsar://localhost:6650",
    max_retries=3,
    retry_delay_seconds=60
)

# Process DLQ with custom handler
dlq.process_with_retry(
    handler_func=my_custom_handler,
    batch_size=100
)
```

### Retry Policy

| Attempt | Delay | Action |
|---------|-------|--------|
| 1 | 60s | Retry immediately |
| 2 | 120s | Retry with backoff |
| 3 | 300s | Final retry |
| 4+ | - | Archive to cold storage |

---

## Troubleshooting

### Pulsar Connection Issues on macOS (Apple Silicon)

**Symptom**: Pulsar tests fail with `TimeOut` or `No route to host` errors after container restarts.

**Root Cause**: Pulsar standalone mode resolves `advertisedAddress` via hostname lookup, which can return stale container IPs on macOS.

**Solution**: The `docker-compose.full.yml` has been configured with:

```yaml
environment:
  - _JAVA_OPTIONS=-XX:UseSVE=0  # Apple Silicon JVM fix (JDK-8345296)
command: bin/pulsar standalone --advertised-address localhost
```

If issues persist:

```bash
# Stop and remove Pulsar container
podman stop janusgraph-demo_pulsar_1
podman rm janusgraph-demo_pulsar_1

# Remove stale data volume
podman volume rm janusgraph-demo_pulsar-data

# Restart Pulsar
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d pulsar
```

**References**:

- [GitHub Issue #15401](https://github.com/apache/pulsar/issues/15401)
- [GitHub Issue #23891](https://github.com/apache/pulsar/issues/23891)

### OpenSearch SSL Configuration

**Symptom**: OpenSearch integration tests skip or fail with SSL errors.

**Configuration**: OpenSearch runs with security disabled in dev mode:

```yaml
environment:
  - plugins.security.disabled=true  # Dev mode - no SSL
```

**Environment Variable**: Tests require `OPENSEARCH_USE_SSL=false`:

```bash
# Add to conda environment
conda env config vars set OPENSEARCH_USE_SSL=false
conda deactivate && conda activate janusgraph-analysis

# Or set per-command
OPENSEARCH_USE_SSL=false pytest tests/integration/test_e2e_streaming.py -v
```

**Verification**:

```bash
curl http://localhost:9200  # Should return cluster info (no https)
```

---

## Related Documentation

- [Data Generators](../data_generators/README.md)

---

## Changelog

### Week 1-4: Foundation

- EntityEvent schema
- EntityProducer with topic routing
- Entity converter
- StreamingOrchestrator

### Week 5: E2E Testing

- Integration test harness
- JanusGraph/OpenSearch connectivity tests
- Cross-system consistency tests

### Week 6: Monitoring & DLQ

- Prometheus metrics
- DLQHandler with retry/archive
- Metrics dashboard integration
