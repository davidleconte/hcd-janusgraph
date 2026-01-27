# HCD + JanusGraph Containerized Stack

Complete containerized deployment of DataStax HCD 1.2.3 with JanusGraph on Podman.

## Architecture

```
podman-wxd machine
├── hcd-server (container)
│   └── HCD 1.2.3 (Cassandra-based storage)
│       - Port 9042: CQL
│       - Port 7000-7001: Inter-node
│       - Port 7199: JMX
│
└── janusgraph-server (container)
    └── JanusGraph (graph database)
        - Port 8182: Gremlin WebSocket
        - Port 8184: Management
        - Backend: HCD via CQL
```

## Prerequisites

- Podman machine `podman-wxd` running (✓ verified)
- Podman Compose installed
- HCD tarball extracted to `hcd-1.2.3/` directory

## Files Overview

**Core Configuration:**
1. **Dockerfile.hcd** - Builds HCD container image (Java 11)
2. **janusgraph-hcd.properties** - JanusGraph configuration for HCD backend
3. **.env.example** - Configuration template (copy to `.env` for customization)

**Deployment:**
4. **deploy_full_stack.sh** - Complete stack deployment with visualization tools
5. **podman-compose.yml** - Basic 2-container stack (HCD + JanusGraph)
6. **podman-compose-full.yml** - Full stack with monitoring and visualization

**Initialization:**
7. **init_and_load.py** / **simple_load.py** - Python scripts for schema and data

**Documentation:**
8. **README.md** - This file (quick start)
9. **IMPROVEMENTS.md** - Detailed list of fixes applied
10. **TESTING_GUIDE.md** - Comprehensive testing procedures

## Deployment Steps

### 1. Build HCD Image

```bash
cd /Users/david.leconte/Documents/Work/Demos/hcd-tarball-janusgraph

# Build using podman-wxd connection
podman --remote --connection podman-wxd build \
  -t localhost/hcd:1.2.3 \
  -f Dockerfile.hcd .
```

### 2. Deploy Stack

```bash
# Deploy using podman-compose
podman-compose --podman-run-args="--connection podman-wxd" up -d
```

Or manually with podman:

```bash
# Create network
podman --remote --connection podman-wxd network create hcd-janusgraph-network

# Create volumes
podman --remote --connection podman-wxd volume create hcd-data
podman --remote --connection podman-wxd volume create hcd-commitlog
podman --remote --connection podman-wxd volume create janusgraph-index

# Start HCD
podman --remote --connection podman-wxd run -d \
  --name hcd-server \
  --network hcd-janusgraph-network \
  -p 9042:9042 -p 7000:7000 -p 7199:7199 \
  -v hcd-data:/var/lib/hcd/data \
  -v hcd-commitlog:/var/lib/hcd/commitlog \
  -e MAX_HEAP_SIZE=4G \
  localhost/hcd:1.2.3

# Wait for HCD to be ready (2-3 minutes)
podman --remote --connection podman-wxd exec hcd-server /opt/hcd/bin/nodetool status

# Start JanusGraph
podman --remote --connection podman-wxd run -d \
  --name janusgraph-server \
  --network hcd-janusgraph-network \
  -p 8182:8182 -p 8184:8184 \
  -v $(pwd)/janusgraph.properties:/etc/opt/janusgraph/janusgraph.properties:ro \
  -v janusgraph-index:/var/lib/janusgraph/index \
  -e janusgraph.storage.hostname=hcd-server \
  docker.io/janusgraph/janusgraph:latest
```

### 3. Verify Deployment

```bash
# Check HCD status
podman --remote --connection podman-wxd exec hcd-server /opt/hcd/bin/nodetool status

# Check JanusGraph logs
podman --remote --connection podman-wxd logs janusgraph-server

# Test Gremlin connection (from host)
curl http://localhost:8182?gremlin=g.V().count()
```

### 4. Connect to Services

**CQL (HCD):**
```bash
podman --remote --connection podman-wxd exec -it hcd-server /opt/hcd/bin/cqlsh
```

**Gremlin Console (JanusGraph):**
```bash
podman --remote --connection podman-wxd exec -it janusgraph-server ./bin/gremlin.sh
```

Then in Gremlin console:
```groovy
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().count()
```

## Management Commands

**View logs:**
```bash
podman --remote --connection podman-wxd logs -f hcd-server
podman --remote --connection podman-wxd logs -f janusgraph-server
```

**Stop stack:**
```bash
podman-compose --podman-run-args="--connection podman-wxd" down
```

**Restart services:**
```bash
podman-compose --podman-run-args="--connection podman-wxd" restart
```

**Remove volumes (CAUTION - deletes data):**
```bash
podman --remote --connection podman-wxd volume rm hcd-data hcd-commitlog janusgraph-index
```

## Configuration

### HCD Configuration
Main config: `/opt/hcd/resources/cassandra/conf/cassandra.yaml` (inside container)

Key settings pre-configured:
- Data directory: `/var/lib/hcd/data`
- Commitlog: `/var/lib/hcd/commitlog`
- Heap: 4GB (adjustable via `MAX_HEAP_SIZE` env var)
- Network: Listening on all interfaces

### JanusGraph Configuration
Config file: `janusgraph-hcd.properties` (mounted read-only)

Backend settings:
- Storage backend: CQL (Cassandra-compatible)
- Hostname: `hcd-server` (container name)
- Port: 9042
- Keyspace: `janusgraph`
- Index backend: Lucene (for mixed indexes)
- Vertex ID: Auto-generated (graph.set-vertex-id=false)

### Customization via .env
Create `.env` file from `.env.example` to customize:
- Podman connection name
- Port mappings
- Network names
- Resource limits

All deployment scripts automatically load `.env` if present.

## Troubleshooting

**HCD not starting:**
- Check logs: `podman --remote --connection podman-wxd logs hcd-server`
- Verify heap settings (requires 4GB+ free memory)
- Ensure ports 9042, 7000 not already in use

**JanusGraph can't connect to HCD:**
- Verify HCD is healthy: `podman --remote --connection podman-wxd exec hcd-server /opt/hcd/bin/nodetool status`
- Check network: Both containers must be on `hcd-janusgraph-network`
- Wait for HCD initialization (can take 2-3 minutes)

**Port conflicts:**
- Check existing containers: `podman --remote --connection podman-wxd ps -a`
- Modify port mappings in `podman-compose.yml` if needed

## Production Considerations

1. **Resource Allocation**: Increase heap size for HCD (`MAX_HEAP_SIZE`)
2. **Replication**: Configure multi-node HCD cluster
3. **Backups**: Set up automated snapshots of volumes
4. **Monitoring**: Add Prometheus/Grafana for metrics
5. **Security**: Enable authentication, TLS for inter-node communication
6. **Performance**: Tune JVM settings, adjust cache sizes

## What's Included

**Graph is pre-initialized!** Schema and sample data are already loaded:
- **11 vertices**: 5 people, 3 companies, 3 products
- **19 edges**: Social network (knows, worksFor, created, uses)
- **Indexes**: Composite indexes on name, email fields

**Query Examples:**
```python
# Using Python gremlinpython client
from gremlin_python.driver import client
gc = client.Client('ws://localhost:18182/gremlin', 'g')

# Alice's friends
gc.submit("g.V().has('person','name','Alice Johnson').out('knows').values('name')").all().result()
# Returns: ['Bob Smith', 'Carol Williams', 'David Brown']

# DataStax employees
gc.submit("g.V().has('company','name','DataStax').in('worksFor').values('name')").all().result()
# Returns: ['Alice Johnson', 'Carol Williams', 'David Brown']
```

## Next Steps

1. **Explore the data**: Use Jupyter Lab (http://localhost:8888) or visualizers
2. **Custom schema**: Modify `init_and_load.py` for your domain model
3. **Production data**: Replace sample data with real data
4. **Set up backups**: Create snapshot scripts for HCD volumes
5. **Add monitoring**: Configure Prometheus alerts and Grafana dashboards
6. **Security**: Enable authentication and TLS
