# Event-Sourced Dual Ingestion Architecture

**Date:** 2026-02-04  
**Version:** 1.0  
**Status:** Proposed  
**Author:** David Leconte

---

## TL;DR

This document describes the recommended architecture for ensuring data consistency between JanusGraph/HCD (graph storage) and OpenSearch (vector search) using Apache Pulsar as the event streaming backbone.

**Key Design Principle**: Single event source → Multiple consumers → Same entity IDs everywhere

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Proposed Architecture](#proposed-architecture)
3. [ID Consistency Strategy](#id-consistency-strategy)
4. [Event Schema](#event-schema)
5. [Topic Organization](#topic-organization)
6. [Consumer Implementation](#consumer-implementation)
7. [Consistency Guarantees](#consistency-guarantees)
8. [Cross-System Query Pattern](#cross-system-query-pattern)
9. [Implementation Roadmap](#implementation-roadmap)

---

## Problem Statement

### Current State (Gap)

```
┌─────────────────────────────────────────────────────────────────┐
│                     CURRENT DATA FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Data Generator                                                │
│        │                                                        │
│        ├──────────────────────────┬─────────────────────────┐  │
│        │                          │                         │  │
│        ▼                          ▼                         │  │
│   JanusGraph/HCD              OpenSearch                    │  │
│   (Graph Data)               (Embeddings)                   │  │
│                                                             │  │
│   NO SYNC ←──────────────────→ NO SYNC                      │  │
│                                                             │  │
└─────────────────────────────────────────────────────────────────┘
```

**Issues:**
- No automatic synchronization mechanism
- Manual coordination required during data loading
- Risk of stale embeddings, orphaned data, duplicate entities
- No Change Data Capture (CDC)
- Entity IDs not validated across systems

---

## Proposed Architecture

### Event-Sourced Dual Ingestion

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EVENT-SOURCED ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Data Generators (Scripts / Notebooks)                                      │
│       │                                                                     │
│       │  entity_id = UUID.uuid4()  ← Single ID generated at source          │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    APACHE PULSAR                                     │   │
│  │                (Single Source of Truth)                              │   │
│  │                                                                      │   │
│  │  Topics: banking/persons/events                                      │   │
│  │          banking/accounts/events                                     │   │
│  │          banking/transactions/events                                 │   │
│  │                                                                      │   │
│  │  Partition Key: entity_id                                            │   │
│  │  Sequence ID: event_id (deduplication)                               │   │
│  └──────────────────────┬──────────────────────────────────────────────┘   │
│                         │                                                   │
│           ┌─────────────┴─────────────┐                                    │
│           │                           │                                    │
│           ▼                           ▼                                    │
│   ┌───────────────────┐       ┌───────────────────┐                       │
│   │  LEG 1: Graph     │       │  LEG 2: Vector    │                       │
│   │  Consumer Group   │       │  Consumer Group   │                       │
│   │                   │       │                   │                       │
│   │  Key_Shared       │       │  Key_Shared       │                       │
│   │  Subscription     │       │  Subscription     │                       │
│   └─────────┬─────────┘       └─────────┬─────────┘                       │
│             │                           │                                  │
│             ▼                           ▼                                  │
│   ┌───────────────────┐       ┌───────────────────┐                       │
│   │   HCD/JanusGraph  │       │   OpenSearch      │                       │
│   │                   │       │                   │                       │
│   │  entity_id: UUID  │◄─────►│  entity_id: UUID  │                       │
│   │  (vertex property)│ SAME  │  (document _id)   │                       │
│   └───────────────────┘  ID   └───────────────────┘                       │
│                                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Apache Pulsar?

| Feature | Pulsar | Kafka | Winner |
|---------|--------|-------|--------|
| Key_Shared subscription | Native | No | **Pulsar** (10x parallel with ordering) |
| Message deduplication | Built-in | Manual | **Pulsar** |
| Geo-replication | Native | External | **Pulsar** |
| Tiered storage | Native | Limited | **Pulsar** (76% cost savings) |

**Key_Shared Advantage**: Enables entity-level ordering with parallel consumers.
- All events for `entity_123` → same consumer (ordered)
- All events for `entity_456` → different consumer (parallel)

---

## ID Consistency Strategy

### ID Field Mapping

| Layer | ID Field | Purpose |
|-------|----------|---------|
| **Data Generator** | `entity_id = UUID.uuid4()` | Single ID generated at source |
| **Pulsar** | `partition_key=entity_id` | Ensures ordering per entity |
| **Pulsar** | `sequence_id=event_id` | Deduplication |
| **JanusGraph** | Vertex property `entity_id` | Graph lookup |
| **OpenSearch** | Document `_id=entity_id` | Vector lookup |

### Visual Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                      ID CONSISTENCY FLOW                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Generator:  entity_id = "550e8400-e29b-41d4-a716-446655440000" │
│                     │                                            │
│                     ▼                                            │
│   Pulsar:     partition_key = "550e8400-e29b-..."               │
│               sequence_id = "evt_001"                            │
│                     │                                            │
│        ┌────────────┴────────────┐                              │
│        ▼                         ▼                              │
│   JanusGraph:                OpenSearch:                         │
│   g.V().has('entity_id',     doc._id = "550e8400-..."           │
│     '550e8400-...')          doc.entity_id = "550e8400-..."     │
│                                                                  │
│   SAME UUID EVERYWHERE = CONSISTENCY                             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Event Schema

### EntityEvent Dataclass

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

@dataclass
class EntityEvent:
    """
    Unified event schema for all entity operations.
    Same event goes to both JanusGraph and OpenSearch consumers.
    """
    
    # Core identifiers - SAME everywhere
    entity_id: str          # UUID - links all systems
    event_id: str           # For deduplication (sequence_id)
    event_type: str         # 'create', 'update', 'delete'
    
    # Entity classification
    entity_type: str        # 'person', 'account', 'transaction', 'company'
    
    # Entity data
    payload: Dict[str, Any] # Full entity data
    
    # Embedding data (for Leg 2 - OpenSearch)
    text_for_embedding: Optional[str] = None  # Text to embed (name, description)
    
    # Metadata
    timestamp: datetime = None
    version: int = 1        # Optimistic concurrency control
    source: str = None      # 'script', 'notebook', 'api'
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())

    def to_pulsar_message(self) -> dict:
        """Convert to Pulsar message format."""
        return {
            'partition_key': self.entity_id,
            'sequence_id': self.event_id,
            'payload': {
                'entity_id': self.entity_id,
                'event_id': self.event_id,
                'event_type': self.event_type,
                'entity_type': self.entity_type,
                'payload': self.payload,
                'text_for_embedding': self.text_for_embedding,
                'timestamp': self.timestamp.isoformat(),
                'version': self.version,
                'source': self.source
            }
        }
```

### Example Events

```python
# Person creation event
person_event = EntityEvent(
    entity_id="550e8400-e29b-41d4-a716-446655440000",
    event_type="create",
    entity_type="person",
    payload={
        "name": "John Smith",
        "email": "john.smith@example.com",
        "risk_score": 0.3
    },
    text_for_embedding="John Smith",  # For vector search
    source="data_generator"
)

# Transaction event
txn_event = EntityEvent(
    entity_id="txn-12345-67890",
    event_type="create",
    entity_type="transaction",
    payload={
        "from_account": "acc-111",
        "to_account": "acc-222",
        "amount": 5000.00,
        "currency": "USD"
    },
    text_for_embedding=None,  # No embedding needed for transactions
    source="notebook"
)
```

---

## Topic Organization

### Question: One Topic per Data Generator or per Entity Type?

**Answer: One Topic per Entity Type (Recommended)**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TOPIC ORGANIZATION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Data Generators                    Pulsar Topics                          │
│   ───────────────                    ─────────────                          │
│                                                                             │
│   ┌─────────────────┐                                                       │
│   │ PersonGenerator │ ──┐                                                   │
│   └─────────────────┘   │         ┌────────────────────────────┐           │
│                         ├───────► │ banking/persons/events     │           │
│   ┌─────────────────┐   │         └────────────────────────────┘           │
│   │ NB01_Sanctions  │ ──┘                                                   │
│   └─────────────────┘                                                       │
│                                                                             │
│   ┌─────────────────┐             ┌────────────────────────────┐           │
│   │ AccountGenerator│ ──────────► │ banking/accounts/events    │           │
│   └─────────────────┘             └────────────────────────────┘           │
│                                                                             │
│   ┌─────────────────┐                                                       │
│   │ TxnGenerator    │ ──┐         ┌────────────────────────────┐           │
│   └─────────────────┘   ├───────► │ banking/transactions/events│           │
│   ┌─────────────────┐   │         └────────────────────────────┘           │
│   │ NB03_Fraud      │ ──┘                                                   │
│   └─────────────────┘                                                       │
│                                                                             │
│   ┌─────────────────┐             ┌────────────────────────────┐           │
│   │ CompanyGenerator│ ──────────► │ banking/companies/events   │           │
│   └─────────────────┘             └────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Topic Design Rationale

| Approach | Pros | Cons |
|----------|------|------|
| **Topic per Entity Type** ✅ | Schema consistency, Consumer simplicity, Better partitioning | Requires routing logic |
| Topic per Generator | Simple routing | Schema mismatches, Harder to consume |
| Single monolithic topic | Simple | Poor scalability, No isolation |

### Topic Naming Convention

```
banking/{entity_type}/events

Examples:
- banking/persons/events
- banking/accounts/events
- banking/transactions/events
- banking/companies/events
- banking/communications/events
- banking/trades/events
```

### Producer Configuration

**Each generator/notebook creates its own producer instance but publishes to shared entity topics:**

```python
class EntityProducer:
    """
    Shared producer class for all data generators and notebooks.
    Routes events to appropriate topics based on entity_type.
    """
    
    def __init__(self, pulsar_url: str = "pulsar://localhost:6650"):
        self.client = pulsar.Client(pulsar_url)
        self.producers = {}  # Lazy-loaded per topic
    
    def _get_producer(self, entity_type: str):
        topic = f"persistent://banking/{entity_type}s/events"
        if topic not in self.producers:
            self.producers[topic] = self.client.create_producer(
                topic,
                compression_type=pulsar.CompressionType.ZSTD,
                batching_enabled=True,
                batching_max_messages=1000,
                batching_max_publish_delay_ms=100
            )
        return self.producers[topic]
    
    def send(self, event: EntityEvent):
        """Route event to appropriate topic."""
        producer = self._get_producer(event.entity_type)
        msg = event.to_pulsar_message()
        
        producer.send(
            content=json.dumps(msg['payload']).encode('utf-8'),
            partition_key=msg['partition_key'],
            sequence_id=hash(msg['sequence_id']) % (2**63)  # Pulsar needs int
        )
    
    def close(self):
        for producer in self.producers.values():
            producer.close()
        self.client.close()
```

### Usage in Data Generators

```python
# In PersonGenerator
class PersonGenerator(BaseGenerator):
    def __init__(self, producer: EntityProducer, seed: int = None):
        super().__init__(seed)
        self.producer = producer
    
    def generate(self) -> Person:
        person = self._create_person()
        
        # Publish event
        event = EntityEvent(
            entity_id=person.person_id,
            event_type="create",
            entity_type="person",
            payload=person.to_dict(),
            text_for_embedding=person.name,
            source="PersonGenerator"
        )
        self.producer.send(event)
        
        return person
```

### Usage in Notebooks

```python
# In NB01_Sanctions_Screening_Demo.ipynb

# Initialize producer
producer = EntityProducer()

# Add sanctioned entity
event = EntityEvent(
    entity_id=str(uuid.uuid4()),
    event_type="create",
    entity_type="person",
    payload={"name": "Test Sanctioned Person", "list_type": "OFAC"},
    text_for_embedding="Test Sanctioned Person",
    source="NB01_Sanctions"
)
producer.send(event)
```

---

## Consumer Implementation

### Leg 1: JanusGraph/HCD Consumer

```python
from pulsar import Client, ConsumerType
from gremlin_python.process.traversal import T
import json
import logging

logger = logging.getLogger(__name__)

class GraphConsumer:
    """
    Consumer for loading entities into JanusGraph/HCD.
    Uses Key_Shared subscription for parallel processing with entity-level ordering.
    """
    
    def __init__(
        self,
        pulsar_url: str = "pulsar://localhost:6650",
        janusgraph_url: str = "ws://localhost:8182/gremlin",
        topics: list = None
    ):
        self.pulsar = Client(pulsar_url)
        self.g = self._connect_janusgraph(janusgraph_url)
        
        if topics is None:
            topics = [
                "persistent://banking/persons/events",
                "persistent://banking/accounts/events",
                "persistent://banking/transactions/events",
                "persistent://banking/companies/events"
            ]
        
        self.consumer = self.pulsar.subscribe(
            topics,
            subscription_name='graph-loaders',
            consumer_type=ConsumerType.KeyShared,  # Entity-level ordering
            receiver_queue_size=1000
        )
        
        self.batch = []
        self.batch_size = 100
    
    def process_forever(self):
        """Main processing loop."""
        while True:
            try:
                msg = self.consumer.receive(timeout_millis=100)
                event = json.loads(msg.data())
                self.batch.append((msg, event))
                
                if len(self.batch) >= self.batch_size:
                    self._flush_batch()
                    
            except pulsar.Timeout:
                if self.batch:
                    self._flush_batch()
    
    def _flush_batch(self):
        """Process batch of events in single transaction."""
        try:
            tx = self.g.tx()
            gtx = tx.begin()
            
            for msg, event in self.batch:
                self._process_event(gtx, event)
            
            tx.commit()
            
            # ACK all messages after successful commit
            for msg, _ in self.batch:
                self.consumer.acknowledge(msg)
            
            logger.info(f"Committed batch of {len(self.batch)} events")
            
        except Exception as e:
            logger.error(f"Batch failed: {e}")
            tx.rollback()
            
            # Negative ACK for retry
            for msg, _ in self.batch:
                self.consumer.negative_acknowledge(msg)
        
        finally:
            self.batch = []
    
    def _process_event(self, g, event: dict):
        """Process single event within transaction."""
        entity_id = event['entity_id']
        event_type = event['event_type']
        entity_type = event['entity_type']
        payload = event['payload']
        version = event['version']
        
        if event_type == 'create':
            # Create vertex with entity_id as lookup key
            vertex = g.addV(entity_type) \
                .property('entity_id', entity_id) \
                .property('version', version)
            
            for key, value in payload.items():
                vertex = vertex.property(key, value)
            
            vertex.next()
            
        elif event_type == 'update':
            # Optimistic concurrency: check version before update
            g.V().has(entity_type, 'entity_id', entity_id) \
                .has('version', version - 1) \
                .property('version', version)
            
            for key, value in payload.items():
                g.V().has(entity_type, 'entity_id', entity_id) \
                    .property(key, value)
            
            g.V().has(entity_type, 'entity_id', entity_id).next()
            
        elif event_type == 'delete':
            g.V().has(entity_type, 'entity_id', entity_id).drop().iterate()
```

### Leg 2: OpenSearch/Vector Consumer

```python
from pulsar import Client, ConsumerType
from opensearchpy import OpenSearch, helpers
import numpy as np
import json
import logging

logger = logging.getLogger(__name__)

class VectorConsumer:
    """
    Consumer for loading embeddings into OpenSearch.
    Generates embeddings from text_for_embedding field.
    """
    
    def __init__(
        self,
        pulsar_url: str = "pulsar://localhost:6650",
        opensearch_host: str = "localhost",
        opensearch_port: int = 9200,
        embedding_model: str = "mini",
        topics: list = None
    ):
        self.pulsar = Client(pulsar_url)
        self.opensearch = OpenSearch(
            hosts=[{'host': opensearch_host, 'port': opensearch_port}],
            use_ssl=False
        )
        self.generator = EmbeddingGenerator(model_name=embedding_model)
        
        if topics is None:
            # Only subscribe to topics that need embeddings
            topics = [
                "persistent://banking/persons/events",
                "persistent://banking/companies/events"
            ]
        
        self.consumer = self.pulsar.subscribe(
            topics,
            subscription_name='vector-loaders',
            consumer_type=ConsumerType.KeyShared
        )
        
        self.batch = []
        self.batch_size = 100
    
    def process_forever(self):
        """Main processing loop."""
        while True:
            try:
                msg = self.consumer.receive(timeout_millis=100)
                event = json.loads(msg.data())
                
                # Skip events without text_for_embedding
                if event.get('text_for_embedding'):
                    self.batch.append((msg, event))
                else:
                    self.consumer.acknowledge(msg)
                
                if len(self.batch) >= self.batch_size:
                    self._flush_batch()
                    
            except pulsar.Timeout:
                if self.batch:
                    self._flush_batch()
    
    def _flush_batch(self):
        """Process batch of events with bulk indexing."""
        try:
            # Generate embeddings for batch
            texts = [e['text_for_embedding'] for _, e in self.batch]
            embeddings = self.generator.encode(texts, batch_size=len(texts))
            
            # Prepare bulk actions
            actions = []
            for i, (msg, event) in enumerate(self.batch):
                entity_id = event['entity_id']
                event_type = event['event_type']
                
                if event_type == 'delete':
                    actions.append({
                        '_op_type': 'delete',
                        '_index': self._get_index(event['entity_type']),
                        '_id': entity_id
                    })
                else:
                    embedding = embeddings[i]
                    if isinstance(embedding, np.ndarray):
                        embedding = embedding.tolist()
                    
                    actions.append({
                        '_op_type': 'index',
                        '_index': self._get_index(event['entity_type']),
                        '_id': entity_id,  # SAME ID as JanusGraph
                        '_source': {
                            'entity_id': entity_id,
                            'embedding': embedding,
                            'version': event['version'],
                            **event['payload']
                        }
                    })
            
            # Bulk index
            success, errors = helpers.bulk(self.opensearch, actions, refresh=True)
            
            # ACK all messages
            for msg, _ in self.batch:
                self.consumer.acknowledge(msg)
            
            logger.info(f"Indexed {success} documents")
            if errors:
                logger.warning(f"Encountered {len(errors)} errors")
            
        except Exception as e:
            logger.error(f"Batch failed: {e}")
            for msg, _ in self.batch:
                self.consumer.negative_acknowledge(msg)
        
        finally:
            self.batch = []
    
    def _get_index(self, entity_type: str) -> str:
        """Map entity type to OpenSearch index."""
        return f"{entity_type}_vectors"
```

---

## Consistency Guarantees

### Summary Table

| Guarantee | Mechanism | Level |
|-----------|-----------|-------|
| **At-least-once delivery** | Pulsar ACK after successful write | Full |
| **No duplicate events** | `sequence_id` deduplication in Pulsar | Full |
| **Entity-level ordering** | `Key_Shared` subscription + partition key | Full |
| **Cross-system ID link** | Same UUID used as JanusGraph property and OpenSearch `_id` | Full |
| **Optimistic concurrency** | Version number check before update | Full |
| **Eventual consistency** | Both legs process same events, converge to same state | Eventual |

### Failure Handling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FAILURE HANDLING                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Message Received                                                          │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────┐                                                          │
│   │  Process    │                                                          │
│   │  Event      │                                                          │
│   └──────┬──────┘                                                          │
│          │                                                                  │
│          ├─────────────────────────┐                                       │
│          │                         │                                       │
│          ▼                         ▼                                       │
│   ┌─────────────┐           ┌─────────────┐                               │
│   │  Success    │           │  Failure    │                               │
│   │             │           │             │                               │
│   │  ACK()      │           │  Temporary? │                               │
│   │             │           │  │      │   │                               │
│   └─────────────┘           │  Yes   No   │                               │
│                             │  │      │   │                               │
│                             │  ▼      ▼   │                               │
│                             │ NACK() DLQ  │                               │
│                             │ (retry) │   │                               │
│                             └─────────────┘                               │
│                                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

```python
class ConsumerWithRetry:
    """Consumer with retry and dead letter queue handling."""
    
    def process(self, msg):
        try:
            event = json.loads(msg.data())
            self.handle(event)
            self.consumer.acknowledge(msg)
            
        except TemporaryError as e:
            # Negative ACK - Pulsar will redeliver after delay
            logger.warning(f"Temporary error, will retry: {e}")
            self.consumer.negative_acknowledge(msg)
            
        except PermanentError as e:
            # Send to dead letter queue, then ACK original
            logger.error(f"Permanent error, sending to DLQ: {e}")
            self.dlq_producer.send(msg.data())
            self.consumer.acknowledge(msg)
```

---

## Cross-System Query Pattern

### Enrich Vector Search with Graph Context

```python
def screen_and_enrich(customer_name: str) -> List[Dict]:
    """
    1. Vector search in OpenSearch to find similar entities
    2. Enrich with graph context from JanusGraph using SAME entity_id
    """
    
    # Step 1: Vector search in OpenSearch
    embedding = generator.encode(customer_name)
    matches = opensearch.search(
        index='person_vectors',
        body={
            'size': 10,
            'query': {
                'knn': {
                    'embedding': {
                        'vector': embedding.tolist(),
                        'k': 10
                    }
                }
            }
        }
    )
    
    # Step 2: Enrich with graph data using SAME entity_id
    enriched_results = []
    for hit in matches['hits']['hits']:
        entity_id = hit['_id']  # Same ID in both systems!
        
        # Get graph context from JanusGraph
        graph_context = g.V().has('entity_id', entity_id) \
            .project('entity', 'connections', 'transactions') \
            .by(valueMap(True)) \
            .by(both().valueMap(True).fold()) \
            .by(outE('transfer').valueMap(True).fold()) \
            .toList()
        
        enriched_results.append({
            'vector_match': hit['_source'],
            'similarity_score': hit['_score'],
            'graph_context': graph_context[0] if graph_context else None
        })
    
    return enriched_results
```

### Visual Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CROSS-SYSTEM QUERY FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   1. Vector Search (OpenSearch)                                             │
│      ───────────────────────────                                           │
│      Query: "John Smith" → embedding → k-NN search                          │
│      Result: entity_id = "550e8400-e29b-41d4-a716-446655440000"            │
│              score = 0.95                                                   │
│                                                                             │
│   2. Graph Enrichment (JanusGraph)                                          │
│      ──────────────────────────────                                        │
│      Query: g.V().has('entity_id', '550e8400-...')                         │
│                  .both().path()                                            │
│      Result: Connected accounts, transactions, associates                   │
│                                                                             │
│   3. Combined Result                                                        │
│      ───────────────────                                                   │
│      {                                                                      │
│        "entity_id": "550e8400-e29b-41d4-a716-446655440000",                │
│        "name": "John Smith",                                                │
│        "similarity_score": 0.95,                                           │
│        "accounts": [...],                                                   │
│        "transactions": [...],                                               │
│        "network_risk": 0.7                                                  │
│      }                                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: Infrastructure (Week 1)

- [ ] Add Apache Pulsar to `docker-compose.full.yml`
- [ ] Configure Pulsar topics and namespaces
- [ ] Set up Pulsar admin console

### Phase 2: Event Schema & Producers (Week 2)

- [ ] Create `EntityEvent` dataclass
- [ ] Create `EntityProducer` class
- [ ] Update data generators to use producers
- [ ] Add producer initialization to notebooks

### Phase 3: Leg 1 - Graph Consumer (Week 3)

- [ ] Implement `GraphConsumer` class
- [ ] Add batch processing and transactions
- [ ] Test with synthetic data
- [ ] Add monitoring metrics

### Phase 4: Leg 2 - Vector Consumer (Week 4)

- [ ] Implement `VectorConsumer` class
- [ ] Add embedding generation
- [ ] Test cross-system ID consistency
- [ ] Add monitoring metrics

### Phase 5: Integration & Testing (Week 5)

- [ ] End-to-end testing
- [ ] Cross-system query validation
- [ ] Performance benchmarking
- [ ] Documentation updates

### Phase 6: Production Hardening (Week 6)

- [ ] Dead letter queue implementation
- [ ] Alerting on consumer lag
- [ ] Backup and recovery procedures
- [ ] Runbook creation

---

## Appendix: Docker Compose Addition

```yaml
# Add to config/compose/docker-compose.full.yml

services:
  # ... existing services ...

  pulsar:
    image: apachepulsar/pulsar:3.2.0
    container_name: pulsar
    ports:
      - "6650:6650"   # Pulsar protocol
      - "8080:8080"   # HTTP admin
    environment:
      - PULSAR_MEM="-Xms512m -Xmx1g"
    command: bin/pulsar standalone
    volumes:
      - pulsar-data:/pulsar/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/admin/v2/clusters"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - hcd-janusgraph-network

volumes:
  pulsar-data:
```

---

**Document Status**: Proposed  
**Last Updated**: 2026-02-04  
**Next Review**: After implementation begins

Co-Authored-By: David Leconte <team@example.com>
