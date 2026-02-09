# HCD + JanusGraph Testing Guide

Complete guide to test and verify your containerized HCD + JanusGraph stack.

> **Note**: All commands below use `podman-wxd` connection by default. To use a different connection, create a `.env` file (copy from `.env.example`) and set `PODMAN_CONNECTION=your-connection-name`. The deployment scripts will automatically use your custom settings.

```bash
# 1. Verify both containers are running
podman --remote --connection podman-wxd ps | grep -E "(hcd-server|janusgraph-server)"

# Expected output:
# hcd-server        Up X minutes    19042→9042, 17000-17001→7000-7001
# janusgraph-server Up X minutes    18182→8182
```

✅ **Both containers should show "Up" status**

---

## Test 1: HCD Database (Storage Layer)

### 1.1 Check HCD Cluster Status

```bash
podman --remote --connection podman-wxd exec hcd-server /opt/hcd/bin/nodetool status
```

**Expected output:**

```
Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address    Load       Tokens  Owns    Host ID                               Rack
UN  10.89.6.6  98.03 KiB  16      100.0%  a64ee549-b842-4b7a-b200-3388b32a0992  rack1
```

✅ **Status should be "UN" (Up/Normal)**

### 1.2 Test CQL Connection

```bash
# Connect to CQL shell
podman --remote --connection podman-wxd exec -it hcd-server /opt/hcd/bin/cqlsh
```

Inside cqlsh, run:

```sql
-- List all keyspaces
DESCRIBE KEYSPACES;
-- Should include: system, system_schema, system_distributed, system_traces, janusgraph

-- Check janusgraph keyspace (created by JanusGraph)
DESCRIBE KEYSPACE janusgraph;

-- Count tables in janusgraph keyspace
SELECT table_name FROM system_schema.tables WHERE keyspace_name = 'janusgraph';

-- Exit
exit;
```

✅ **`janusgraph` keyspace should exist with multiple tables**

### 1.3 Query JanusGraph Tables

```bash
podman --remote --connection podman-wxd exec hcd-server /opt/hcd/bin/cqlsh << 'EOF'
USE janusgraph;
DESCRIBE TABLES;
SELECT COUNT(*) FROM edgestore;
SELECT COUNT(*) FROM graphindex;
EOF
```

✅ **Tables should exist, counts may be 0 if no schema loaded yet**

### 1.4 Check HCD Logs

```bash
# Last 100 lines
podman --remote --connection podman-wxd logs hcd-server | tail -100

# Follow logs in real-time
podman --remote --connection podman-wxd logs -f hcd-server
```

✅ **No ERROR messages, should see "listening on" messages**

---

## Test 2: JanusGraph Server (Graph Layer)

### 2.1 Check JanusGraph Logs

```bash
# Last 100 lines
podman --remote --connection podman-wxd logs janusgraph-server | tail -100
```

**Look for:**

```
✅ "Gremlin Server configured with worker thread pool"
✅ "Channel started at port 8182"
✅ "graphtraversalsource[standardjanusgraph[cql:[hcd-server]]"
❌ No "ERROR" or "Exception" messages
```

### 2.2 Verify Graph Configuration

```bash
podman --remote --connection podman-wxd exec janusgraph-server cat /opt/janusgraph/conf/janusgraph-cql.properties | grep -E "(storage|backend)"
```

**Expected output:**

```
gremlin.graph=org.janusgraph.core.JanusGraphFactory
storage.backend=cql
storage.hostname=hcd-server
storage.port=9042
```

✅ **Backend should be `cql` and hostname `hcd-server`**

### 2.3 Test Gremlin Console Connection

```bash
# Enter Gremlin console
podman --remote --connection podman-wxd exec -it janusgraph-server ./bin/gremlin.sh
```

Inside Gremlin console:

```groovy
// Connect to remote server
:remote connect tinkerpop.server conf/remote.yaml

// Switch to remote mode
:remote console

// Test basic query
g.V().count()

// Expected: 0 (if no data loaded yet) or positive number

// Exit
:exit
```

✅ **Query should execute without errors**

---

## Test 3: Initialize Schema and Load Data

### 3.1 Copy Scripts to Container

```bash
cd /Users/david.leconte/Documents/Work/Demos/hcd-tarball-janusgraph

# Copy Groovy scripts
podman --remote --connection podman-wxd cp init_sample_schema.groovy janusgraph-server:/tmp/
podman --remote --connection podman-wxd cp load_sample_data.groovy janusgraph-server:/tmp/
```

### 3.2 Run Schema Initialization

```bash
podman --remote --connection podman-wxd exec janusgraph-server \
  ./bin/gremlin.sh -e /tmp/init_sample_schema.groovy
```

**Expected output:**

```
Creating schema...
Created vertex labels: person, company, product
Created edge labels: knows, worksFor, created, uses
Created property keys
Created composite indexes
Created mixed indexes
Schema committed successfully!
...
Graph closed. Schema initialization complete.
```

✅ **Schema creation should complete without errors**

### 3.3 Verify Schema in HCD

```bash
# Check that new tables were created
podman --remote --connection podman-wxd exec hcd-server /opt/hcd/bin/cqlsh << 'EOF'
USE janusgraph;
DESCRIBE TABLES;
SELECT COUNT(*) FROM edgestore;
SELECT COUNT(*) FROM graphindex;
EOF
```

✅ **Table counts should be > 0 now**

### 3.4 Load Sample Data

```bash
podman --remote --connection podman-wxd exec janusgraph-server \
  ./bin/gremlin.sh -e /tmp/load_sample_data.groovy
```

**Expected output:**

```
Loading sample data...
Created 5 people
Created 3 companies
Created 3 products
Created 'knows' relationships
Created 'worksFor' relationships
Created 'created' relationships
Created 'uses' relationships
Data loading complete!
```

✅ **Data loading should complete with summary**

### 3.5 Verify Data Loaded

```bash
# Enter Gremlin console
podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh << 'EOF'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().count()
g.E().count()
g.V().hasLabel('person').values('name')
EOF
```

**Expected output:**

```
==>11              // 11 vertices
==>19              // 19 edges
==>Alice Johnson
==>Bob Smith
==>Carol Williams
==>David Brown
==>Eve Davis
```

✅ **Counts should match: 11 vertices, 19 edges**

---

## Test 4: Python Test Client

### 4.1 Install Python Dependencies

```bash
# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install gremlin_python
pip install gremlinpython
```

### 4.2 Make Script Executable

```bash
cd /Users/david.leconte/Documents/Work/Demos/hcd-tarball-janusgraph
chmod +x test_janusgraph_client.py
```

### 4.3 Run Test Client

```bash
./test_janusgraph_client.py
```

**Expected output:**

```
JanusGraph Python Test Client
============================================================
✅ Connected to JanusGraph at ws://localhost:18182/gremlin

============================================================
INITIALIZATION CHECK
============================================================
✅ Graph initialized: 11 vertices, 19 edges

============================================================
BASIC QUERIES
============================================================
...
✅ All tests completed successfully!
```

✅ **All test sections should pass**

### 4.4 Test Individual Queries

Create a simple test script:

```bash
cat > quick_test.py << 'EOF'
from gremlin_python.driver import client

# Connect
gremlin_client = client.Client('ws://localhost:18182/gremlin', 'g')

# Test queries
print("People:", gremlin_client.submit("g.V().hasLabel('person').values('name')").all().result())
print("Companies:", gremlin_client.submit("g.V().hasLabel('company').values('name')").all().result())
print("Alice's friends:", gremlin_client.submit("g.V().has('person', 'name', 'Alice Johnson').out('knows').values('name')").all().result())

gremlin_client.close()
EOF

python3 quick_test.py
```

✅ **Queries should return data**

---

## Test 5: Integration Testing

### 5.1 Verify JanusGraph is Using HCD

```bash
# Query from JanusGraph
podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh << 'EOF'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.addV('test').property('name', 'TestVertex').next()
g.V().has('test', 'name', 'TestVertex').values('name')
EOF
```

Then verify in HCD:

```bash
podman --remote --connection podman-wxd exec hcd-server /opt/hcd/bin/cqlsh << 'EOF'
USE janusgraph;
SELECT COUNT(*) FROM edgestore WHERE key = textAsBlob('test');
EOF
```

✅ **Data added via JanusGraph should be visible in HCD**

### 5.2 Test Data Persistence

```bash
# Add vertex via JanusGraph
podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh << 'EOF'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.addV('person').property('name', 'TestUser').property('age', 99).next()
g.V().has('person', 'name', 'TestUser').elementMap()
EOF

# Restart JanusGraph
podman --remote --connection podman-wxd restart janusgraph-server

# Wait 60 seconds
sleep 60

# Verify data persisted
podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh << 'EOF'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().has('person', 'name', 'TestUser').elementMap()
EOF
```

✅ **Data should survive JanusGraph restart**

### 5.3 Test Concurrent Writes

Create `concurrent_test.py`:

```python
from gremlin_python.driver import client
from concurrent.futures import ThreadPoolExecutor
import time

def add_person(name):
    gremlin_client = client.Client('ws://localhost:18182/gremlin', 'g')
    try:
        query = f"g.addV('person').property('name', '{name}').property('age', 30).next()"
        result = gremlin_client.submit(query).all().result()
        print(f"Added: {name}")
        return True
    except Exception as e:
        print(f"Failed: {name} - {e}")
        return False
    finally:
        gremlin_client.close()

# Add 10 people concurrently
with ThreadPoolExecutor(max_workers=5) as executor:
    names = [f"ConcurrentUser{i}" for i in range(10)]
    results = executor.map(add_person, names)

print(f"Success: {sum(results)}/10")
```

```bash
python3 concurrent_test.py
```

✅ **All 10 should succeed**

---

## Test 6: Performance Testing

### 6.1 Bulk Insert Test

```bash
podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh << 'EOF'
:remote connect tinkerpop.server conf/remote.yaml
:remote console

// Add 100 vertices
(1..100).each { i ->
    g.addV('person').property('name', "User${i}").property('age', 20 + (i % 50)).next()
}

// Commit transaction
graph.tx().commit()

// Verify count
g.V().hasLabel('person').count()
EOF
```

✅ **Should complete in < 30 seconds**

### 6.2 Query Performance

```bash
time podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh << 'EOF'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().hasLabel('person').has('age', gte(25)).has('age', lte(35)).count()
EOF
```

✅ **Query should complete in < 5 seconds**

### 6.3 Traversal Performance

```bash
time podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh << 'EOF'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().has('person', 'name', 'Alice Johnson')
  .out('knows').out('knows').out('knows')
  .dedup().count()
EOF
```

✅ **Multi-hop traversal should complete in < 10 seconds**

---

## Test 7: Failure Testing

### 7.1 Test HCD Restart

```bash
# Restart HCD
podman --remote --connection podman-wxd restart hcd-server

# Wait for HCD to come up (2-3 minutes)
sleep 180

# Check HCD status
podman --remote --connection podman-wxd exec hcd-server /opt/hcd/bin/nodetool status

# Verify JanusGraph still works
podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh << 'EOF'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().count()
EOF
```

✅ **JanusGraph should reconnect automatically**

### 7.2 Test JanusGraph Restart

```bash
# Restart JanusGraph
podman --remote --connection podman-wxd restart janusgraph-server

# Wait for startup (60 seconds)
sleep 60

# Verify data persisted
podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh << 'EOF'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().count()
EOF
```

✅ **Data should be intact**

---

## Common Issues and Solutions

### Issue: Python client connection timeout

**Symptom**: `ConnectionRefusedError` or timeout

**Solution**:

```bash
# 1. Check JanusGraph is running
podman --remote --connection podman-wxd ps | grep janusgraph

# 2. Check port mapping
podman --remote --connection podman-wxd port janusgraph-server

# 3. Test WebSocket manually
nc -zv localhost 18182

# 4. Check JanusGraph logs
podman --remote --connection podman-wxd logs janusgraph-server | tail -50
```

### Issue: "Graph is empty" after loading data

**Symptom**: Python client or queries return 0 vertices

**Solution**:

```bash
# 1. Check if data was actually loaded
podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh << 'EOF'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().count()
g.E().count()
EOF

# 2. Re-run data loading script
podman --remote --connection podman-wxd exec janusgraph-server \
  ./bin/gremlin.sh -e /tmp/load_sample_data.groovy
```

### Issue: "Schema already exists" error

**Symptom**: Error when re-running schema initialization

**Solution**:

```bash
# Option 1: Drop keyspace and recreate
podman --remote --connection podman-wxd exec hcd-server /opt/hcd/bin/cqlsh << 'EOF'
DROP KEYSPACE IF EXISTS janusgraph;
EOF

# Restart JanusGraph (will recreate keyspace)
podman --remote --connection podman-wxd restart janusgraph-server
sleep 60

# Re-run schema init
podman --remote --connection podman-wxd exec janusgraph-server \
  ./bin/gremlin.sh -e /tmp/init_sample_schema.groovy

# Option 2: Clear graph (keeps schema)
podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh << 'EOF'
:remote connect tinkerpop.server conf/remote.yaml
:remote console
g.V().drop().iterate()
graph.tx().commit()
EOF
```

### Issue: HCD "Unable to gossip" error

**Symptom**: HCD container exits with gossip error

**Solution**:

```bash
# This is expected for single-node setup
# Verify auto_bootstrap is disabled in Dockerfile

# Check configuration
podman --remote --connection podman-wxd exec hcd-server \
  grep -E "(auto_bootstrap|seeds)" /opt/hcd/resources/cassandra/conf/cassandra.yaml

# Should show:
# - seeds: "hcd-server"
# auto_bootstrap: false
```

---

## Test Checklist

Use this checklist to verify complete functionality:

- [ ] Both containers running (hcd-server, janusgraph-server)
- [ ] HCD cluster status: UN (Up/Normal)
- [ ] HCD CQL shell accessible
- [ ] JanusGraph keyspace exists in HCD
- [ ] JanusGraph logs show no errors
- [ ] Gremlin console connects successfully
- [ ] Schema initialization completes
- [ ] Sample data loads successfully
- [ ] Vertex count: 11, Edge count: 19
- [ ] Python client connects successfully
- [ ] Python test client passes all tests
- [ ] Data persists after JanusGraph restart
- [ ] JanusGraph reconnects after HCD restart
- [ ] Queries return expected results
- [ ] Concurrent writes succeed
- [ ] Performance meets expectations

---

## Monitoring Commands

### Continuous Monitoring

```bash
# Watch container status
watch -n 5 'podman --remote --connection podman-wxd ps | grep -E "(hcd|janusgraph)"'

# Watch HCD cluster
watch -n 10 'podman --remote --connection podman-wxd exec hcd-server /opt/hcd/bin/nodetool status'

# Follow JanusGraph logs
podman --remote --connection podman-wxd logs -f janusgraph-server

# Follow HCD logs
podman --remote --connection podman-wxd logs -f hcd-server

# Monitor vertex count
watch -n 5 'podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh -e ":remote connect tinkerpop.server conf/remote.yaml; :remote console; g.V().count()"'
```

### Resource Usage

```bash
# Container stats
podman --remote --connection podman-wxd stats hcd-server janusgraph-server

# Volume usage
podman --remote --connection podman-wxd volume ls
podman --remote --connection podman-wxd volume inspect hcd-data
```

---

## Next Steps After Testing

Once all tests pass:

1. **Customize Schema**: Modify `init_sample_schema.groovy` for your domain
2. **Load Real Data**: Replace sample data with production data
3. **Set Up Backups**: Create snapshot scripts for HCD volumes
4. **Add Monitoring**: Integrate Prometheus/Grafana
5. **Production Config**: Adjust heap sizes, replication factor
6. **Security**: Enable authentication, TLS
7. **Scale**: Add more HCD nodes, configure load balancing

---

**All tests successful? Your HCD + JanusGraph stack is ready! 🚀**
