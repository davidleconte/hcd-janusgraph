# Architecture Overview

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
**Contact:**

## System Architecture

```mermaid
flowchart TB
    subgraph Data Sources
        DG[Data Generators]
        EXT[External Systems]
    end

    subgraph Streaming Layer
        P[Apache Pulsar]
        DLQ[Dead Letter Queue]
    end

    subgraph Storage Layer
        JG[JanusGraph]
        HCD[HCD/Cassandra]
        OS[OpenSearch]
    end

    subgraph Application Layer
        API[REST API]
        NB[Notebooks]
    end

    DG --> P
    EXT --> P
    P --> JG
    P --> OS
    P -.-> DLQ
    JG --> HCD
    API --> JG
    API --> OS
    NB --> JG
    NB --> OS
```

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| Data Generators | Synthetic data | Python |
| Apache Pulsar | Event streaming | Pulsar 3.x |
| JanusGraph | Graph database | JanusGraph 1.x |
| HCD | Graph storage | Cassandra 4.x |
| OpenSearch | Vector search | OpenSearch 2.x |
| REST API | External access | FastAPI |

## Data Flow

See [Unified Data Flow](data-flow-unified.md) for detailed data pipeline documentation.

## Key Design Decisions

1. **Event-Driven Architecture**: Pulsar enables decoupled, scalable data ingestion
2. **Dual Storage**: Graph (JanusGraph) + Vector (OpenSearch) for different query patterns
3. **Consistent IDs**: Entity IDs consistent across all systems
