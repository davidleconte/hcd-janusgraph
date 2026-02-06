# Unified Data Flow Documentation

**Created**: 2026-02-06  
**Version**: 1.0  
**Status**: Active

---

## TL;DR

Complete data flow from synthetic generation to queryable graph and vector search:

1. **Data Generators** → Create synthetic banking entities (persons, accounts, transactions)
2. **Apache Pulsar** → Event streaming with guaranteed ordering and deduplication
3. **JanusGraph + HCD** → Graph storage with ACID properties
4. **OpenSearch** → Vector embeddings for semantic search

**Key Guarantee**: 1:1 ID mapping across all systems (Pulsar partition key = JanusGraph entity_id = OpenSearch _id)

---

## High-Level Architecture

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA GENERATION LAYER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Person    │  │   Company   │  │   Account   │  │ Transaction │        │
│  │  Generator  │  │  Generator  │  │  Generator  │  │  Generator  │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                   │                                          │
│                          ┌────────▼────────┐                                 │
│                          │ StreamingOrchestrator │                           │
│                          │   (EntityProducer)    │                           │
│                          └────────┬────────┘                                 │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│                           STREAMING LAYER (Pulsar)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  persons-   │  │  accounts-  │  │transactions-│  │  companies- │        │
│  │   events    │  │   events    │  │   events    │  │   events    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                   │                                          │
│                          Key_Shared Subscription                             │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
┌───────────────────▼───────────────┐   ┌──────────▼──────────────────────────┐
│         GRAPH STORAGE             │   │         VECTOR STORAGE               │
├───────────────────────────────────┤   ├─────────────────────────────────────┤
│  ┌─────────────────────────────┐  │   │  ┌─────────────────────────────┐    │
│  │      GraphConsumer          │  │   │  │     VectorConsumer          │    │
│  │   (Gremlin Transactions)    │  │   │  │   (Embedding Generation)    │    │
│  └──────────────┬──────────────┘  │   │  └──────────────┬──────────────┘    │
│                 │                 │   │                 │                    │
│  ┌──────────────▼──────────────┐  │   │  ┌──────────────▼──────────────┐    │
│  │        JanusGraph           │  │   │  │        OpenSearch           │    │
│  │  (Vertices, Edges, Props)   │  │   │  │  (Vectors, Metadata)        │    │
│  └──────────────┬──────────────┘  │   │  └─────────────────────────────┘    │
│                 │                 │   │                                      │
│  ┌──────────────▼──────────────┐  │   │                                      │
│  │      HCD (Cassandra)        │  │   │                                      │
│  │   (WAL, 3x Replication)     │  │   │                                      │
│  └─────────────────────────────┘  │   │                                      │
└───────────────────────────────────┘   └──────────────────────────────────────┘
```

### Mermaid Flowchart

```mermaid
flowchart TB
    subgraph Generation["Data Generation Layer"]
        PG[Person Generator]
        CG[Company Generator]
        AG[Account Generator]
        TG[Transaction Generator]
        SO[StreamingOrchestrator]
        
        PG --> SO
        CG --> SO
        AG --> SO
        TG --> SO
    end
    
    subgraph Pulsar["Apache Pulsar"]
        PT1[persons-events]
        PT2[accounts-events]
        PT3[transactions-events]
        PT4[companies-events]
        
        SO --> PT1
        SO --> PT2
        SO --> PT3
        SO --> PT4
    end
    
    subgraph GraphPath["Graph Storage Path"]
        GC[GraphConsumer]
        JG[(JanusGraph)]
        HCD[(HCD/Cassandra)]
        
        PT1 & PT2 & PT3 & PT4 --> GC
        GC --> JG
        JG --> HCD
    end
    
    subgraph VectorPath["Vector Storage Path"]
        VC[VectorConsumer]
        EMB[Embedding Model]
        OS[(OpenSearch)]
        
        PT1 & PT2 & PT3 & PT4 --> VC
        VC --> EMB
        EMB --> OS
    end
    
    style Pulsar fill:#f9f,stroke:#333
    style GraphPath fill:#bbf,stroke:#333
    style VectorPath fill:#bfb,stroke:#333
```

---

## Detailed Data Flow

### Sequence Diagram

```mermaid
sequenceDiagram
    participant Gen as Data Generator
    participant Orch as StreamingOrchestrator
    participant Prod as EntityProducer
    participant Pulsar as Apache Pulsar
    participant GC as GraphConsumer
    participant JG as JanusGraph
    participant HCD as HCD Storage
    participant VC as VectorConsumer
    participant EMB as Embedding Model
    participant OS as OpenSearch
    
    Gen->>Orch: Generate Entity
    Orch->>Prod: Create EntityEvent
    Note over Prod: entity_id = partition_key
    Prod->>Pulsar: Publish (topic, partition_key)
    Pulsar-->>Prod: ACK
    
    par Graph Path
        Pulsar->>GC: Deliver Message
        GC->>JG: Gremlin addV/addE
        JG->>HCD: Write WAL + Data
        HCD-->>JG: Commit ACK
        JG-->>GC: Transaction Complete
        GC->>Pulsar: Consumer ACK
    and Vector Path
        Pulsar->>VC: Deliver Message
        VC->>EMB: Generate Embedding
        EMB-->>VC: Vector (768 dims)
        VC->>OS: Index Document (_id=entity_id)
        OS-->>VC: Index ACK
        VC->>Pulsar: Consumer ACK
    end
```

---

## ID Consistency Mapping

### The Golden Rule

**Every entity maintains the same ID across all systems:**

| System | ID Field | Example |
|--------|----------|---------|
| Pulsar | `partition_key` | `person-a1b2c3d4` |
| JanusGraph | `entity_id` property | `person-a1b2c3d4` |
| OpenSearch | `_id` field | `person-a1b2c3d4` |

### ID Flow Diagram

```mermaid
flowchart LR
    subgraph Generator
        ID1[entity_id: person-a1b2c3d4]
    end
    
    subgraph Pulsar
        ID2[partition_key: person-a1b2c3d4]
    end
    
    subgraph JanusGraph
        ID3["V().has('entity_id', 'person-a1b2c3d4')"]
    end
    
    subgraph OpenSearch
        ID4["_id: person-a1b2c3d4"]
    end
    
    ID1 --> ID2
    ID2 --> ID3
    ID2 --> ID4
    
    style ID1 fill:#ffd,stroke:#333
    style ID2 fill:#f9f,stroke:#333
    style ID3 fill:#bbf,stroke:#333
    style ID4 fill:#bfb,stroke:#333
```

### Code Example

```python
# Entity creation with consistent ID
from banking.streaming import create_person_event

# ID generated once, used everywhere
entity_id = f"person-{uuid.uuid4().hex[:8]}"

event = create_person_event(
    person_id=entity_id,  # Used as partition_key in Pulsar
    name="John Smith",
    payload={
        "entity_id": entity_id,  # Stored in JanusGraph
        "name": "John Smith",
        # ... other fields
    }
)

# In GraphConsumer:
# g.addV('person').property('entity_id', entity_id)

# In VectorConsumer:
# opensearch.index(index='persons', id=entity_id, body={...})
```

---

## Topic Structure

### Pulsar Topics

| Topic | Entity Type | Partition Key | Consumer Groups |
|-------|-------------|---------------|-----------------|
| `persons-events` | Person | `person_id` | graph-loaders, vector-loaders |
| `accounts-events` | Account | `account_id` | graph-loaders, vector-loaders |
| `transactions-events` | Transaction | `from_account_id` | graph-loaders, vector-loaders |
| `companies-events` | Company | `company_id` | graph-loaders, vector-loaders |
| `communications-events` | Communication | `from_person_id` | graph-loaders, vector-loaders |
| `trades-events` | Trade | `account_id` | graph-loaders, vector-loaders |

### Topic Flow Diagram

```mermaid
flowchart TB
    subgraph Topics["Pulsar Topics"]
        P[persons-events]
        A[accounts-events]
        T[transactions-events]
        C[companies-events]
        COM[communications-events]
        TR[trades-events]
    end
    
    subgraph GraphLoaders["graph-loaders subscription"]
        GL1[GraphConsumer 1]
        GL2[GraphConsumer 2]
        GLN[GraphConsumer N]
    end
    
    subgraph VectorLoaders["vector-loaders subscription"]
        VL1[VectorConsumer 1]
        VL2[VectorConsumer 2]
        VLN[VectorConsumer N]
    end
    
    Topics --> GraphLoaders
    Topics --> VectorLoaders
```

---

## Error Handling & DLQ

### Dead Letter Queue Flow

```mermaid
flowchart TB
    subgraph Normal["Normal Flow"]
        P[Pulsar Topic]
        C[Consumer]
        S[(Storage)]
        
        P --> C
        C --> S
    end
    
    subgraph Error["Error Flow"]
        E[Processing Error]
        R{Retry Count}
        DLQ[Dead Letter Queue]
        Alert[Alert System]
        
        C --> E
        E --> R
        R -->|< 3 retries| C
        R -->|>= 3 retries| DLQ
        DLQ --> Alert
    end
    
    style DLQ fill:#fbb,stroke:#333
```

### DLQ Topics

| Original Topic | DLQ Topic | Purpose |
|---------------|-----------|---------|
| `persons-events` | `persons-events-dlq` | Failed person processing |
| `transactions-events` | `transactions-events-dlq` | Failed transaction processing |
| (all topics) | `*-events-dlq` | Pattern for all entity types |

---

## Consistency Guarantees

### ACID Properties

| Property | Mechanism | Guarantee |
|----------|-----------|-----------|
| **Atomicity** | JanusGraph Txn + Pulsar ACK | All-or-nothing per batch |
| **Consistency** | Schema validation | Valid state transitions |
| **Isolation** | MVCC | Read Committed level |
| **Durability** | WAL + 3x replication | No data loss |

### Consistency Flow

```mermaid
stateDiagram-v2
    [*] --> EventReceived
    EventReceived --> Processing
    Processing --> GraphWrite
    GraphWrite --> WALWrite
    WALWrite --> Replication
    Replication --> ConsumerACK
    ConsumerACK --> [*]
    
    Processing --> DLQ: Error (3 retries)
    GraphWrite --> NegativeACK: Txn Failed
    NegativeACK --> EventReceived: Redelivery
```

---

## Performance Characteristics

### Latency Breakdown

| Stage | Latency | Notes |
|-------|---------|-------|
| Producer → Pulsar | 5ms p99 | With batching |
| Pulsar → Consumer | 2ms p99 | Key_Shared routing |
| Consumer batch | 10ms | 1000 msgs or timeout |
| Graph write | 100ms | Atomic transaction |
| Vector indexing | 50ms | Embedding + index |
| **Total (Graph)** | ~115ms | Event to queryable |
| **Total (Vector)** | ~65ms | Event to searchable |

### Throughput

| Component | Throughput | Scale Factor |
|-----------|------------|--------------|
| Pulsar | 3M msg/sec | Per topic |
| Graph Loader | 1K vertices/sec | Per worker |
| Vector Loader | 2K docs/sec | Per worker |
| **System** | 100K writes/sec | With 100 workers |

---

## Related Documentation

- [Streaming Architecture](streaming-architecture.md) - Detailed streaming design
- [System Architecture](system-architecture.md) - Overall system design
- [banking/streaming/README.md](`banking/streaming/README.md`) - Implementation guide

---

**Document Status**: Active  
**Last Updated**: 2026-02-06  
**Version**: 1.0
