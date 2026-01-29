# System Architecture

**File**: docs/ARCHITECTURE.md  
**Created**: 2026-01-28T10:36:30.123  
**Author**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117

---

## Overview

This document describes the architecture of the HCD + JanusGraph containerized stack.

## Components

### 1. HCD (HyperConverged Database)
- Cassandra-based distributed database
- Storage backend for JanusGraph
- Provides scalability and fault tolerance

### 2. JanusGraph
- Graph database built on HCD
- Supports Gremlin query language
- Lucene-based search indexing

### 3. Jupyter Lab
- Interactive Python notebooks
- Pre-configured with graph clients
- Visualization capabilities

### 4. Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and visualization
- **Alertmanager**: Alert routing

### 5. Visualization Tools
- **Visualizer**: Web-based graph explorer
- **Graphexp**: Alternative graph UI

## Data Flow

```
Client → JanusGraph (Gremlin) → HCD (CQL) → Disk
         ↓
     Prometheus → Grafana
```

## Network Architecture

All services communicate via Docker bridge network:
- **Network name**: hcd-janusgraph-network
- **Internal DNS**: Containers resolve by service name

## Storage Architecture

### HCD Data
- Path: `/var/lib/cassandra/data`
- Persistence: Podman volume `hcd-data`

### JanusGraph Data
- Path: `/var/lib/janusgraph`
- Persistence: Podman volume `janusgraph-data`

### Backups
- Path: `/backups/janusgraph/`
- Format: tar.gz + GraphML export

## Security Architecture

### Authentication
- HCD: Native authentication (optional)
- JanusGraph: Open by default (can add auth)
- Grafana: User-based authentication

### Network Security
- Services isolated in Docker network
- Only necessary ports exposed to host
- No external access by default

## Scalability Considerations

### Vertical Scaling
- Increase heap sizes in `.env`
- Add resource limits in compose files

### Horizontal Scaling
- HCD supports multi-node clusters
- JanusGraph supports multiple instances
- Load balancing required

---

**Signature**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
