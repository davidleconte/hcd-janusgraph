# OpenSearch + JVector Remediation Checklist

**Date:** 2026-02-03
**Status:** MOSTLY COMPLETE (Updated 2026-02-03 22:30)
**Priority:** CRITICAL

---

## Current State Assessment

| Component | Current State | Target State |
|-----------|--------------|--------------|
| docker-compose.full.yml | ❌ Elasticsearch 8.11.0 (lines 61-90) | OpenSearch 3.x with JVector |
| janusgraph-hcd.properties | ⚠️ backend=elasticsearch, hostname=opensearch | backend=elasticsearch (OK for OpenSearch) |
| janusgraph-index volume | ❌ Corrupted (Elasticsearch data) | Clean OpenSearch data |
| JanusGraph health | ❌ Unhealthy (index backend unavailable) | Healthy |
| JVector plugin | ❌ Not installed | Installed via Maven |

### Container Status

```
janusgraph-demo_elasticsearch_1   Exited (143) - FAILING
janusgraph-demo_janusgraph-server_1  Unhealthy - CAUSED BY ABOVE
```

---

## Remediation Checklist (Ordered)

### Phase 1: Stop & Clean (5 min)

- [x] **1.1** Stop all containers ✅ DONE
- [x] **1.2** Remove corrupted `janusgraph-index` volume ✅ DONE
- [x] **1.3** Verify clean state ✅ DONE

### Phase 2: Fix docker-compose.full.yml (10 min)

- [x] **2.1** Replace Elasticsearch service with OpenSearch service ✅ DONE
- [x] **2.2** Update service name from `elasticsearch` to `opensearch` ✅ DONE
- [x] **2.3** Add JVector installation script mount (Replaced by Custom Dockerfile) ✅ DONE
- [x] **2.4** Update JanusGraph `depends_on` to use `opensearch` ✅ DONE
- [x] **2.5** Update volume name from `janusgraph-index` to `opensearch-data` ✅ DONE

### Phase 3: Update JanusGraph Configuration (5 min)

- [x] **3.1** Verify `index.search.backend=elasticsearch` (correct for OpenSearch) ✅ DONE
- [x] **3.2** Verify `index.search.hostname=opensearch` ✅ DONE
- [x] **3.3** Ensure REST_CLIENT interface is used ✅ DONE

### Phase 4: Deploy & Install JVector (15 min)

- [x] **4.1** Start HCD, Vault, OpenSearch ✅ DONE
- [x] **4.2** Wait for OpenSearch healthy ✅ DONE
- [x] **4.3** Create Custom Dockerfile with JVector (Maven) ✅ DONE
- [ ] **4.4** Build and Deploy Full Stack ⏳ PENDING
- [ ] **4.5** Verify Plugin Installation ⏳ PENDING

### Phase 5: Verify (10 min)

- [ ] **5.1** JanusGraph health check passes ⏳ PENDING (Fix applied in Compose)
- [x] **5.2** Gremlin query works: `g.V().count()` ✅ DONE (660 vertices)
- [x] **5.3** OpenSearch responds: `curl localhost:9200` ✅ DONE
- [x] **4.3** Create Custom Dockerfile with JVector (Maven) ✅ DONE
- [x] **4.4** Build and Deploy Full Stack ✅ DONE
- [x] **4.5** Verify Plugin Installation ✅ DONE

### Phase 5: Verify (10 min)

- [x] **5.1** JanusGraph health check passes ✅ DONE (Healthy)
- [x] **5.2** Gremlin query works: `g.V().count()` ✅ DONE (660 vertices)
- [x] **5.3** OpenSearch responds: `curl localhost:9200` ✅ DONE
- [x] **5.4** JVector plugin loaded (check OpenSearch plugins) ✅ DONE
  hostname: opensearch
  networks:
  - hcd-janusgraph-network
  ports:
  - "9200:9200"      # REST API
  - "9600:9600"      # Performance Analyzer
  environment:
  - cluster.name=opensearch-cluster
  - node.name=opensearch-node1
  - discovery.type=single-node
  - bootstrap.memory_lock=true
  - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
  - plugins.security.disabled=true  # Dev mode - enable in production
  ulimits:
    memlock:
      soft: -1
      hard: -1
    nofile:
      soft: 65536
      hard: 65536
  volumes:
  - opensearch-data:/usr/share/opensearch/data
  - ../../config/opensearch/jvector-install.sh:/tmp/jvector-install.sh:ro
  healthcheck:
    test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health | grep -qE '\"status\":\"(green|yellow)\"'"]
    interval: 30s
    timeout: 10s
    retries: 5
    start_period: 60s
  restart: unless-stopped

```

### JanusGraph Properties (already correct)
```properties
index.search.backend=elasticsearch  # Works with OpenSearch
index.search.hostname=opensearch
index.search.port=9200
index.search.elasticsearch.interface=REST_CLIENT
```

### JVector Installation

```bash
# Inside OpenSearch container:
podman exec janusgraph-demo_opensearch_1 bash /tmp/jvector-install.sh
podman restart janusgraph-demo_opensearch_1
```

---

## Commands Reference

### Stop & Clean

```bash
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml down -v
podman volume rm janusgraph-demo_janusgraph-index 2>/dev/null || true
```

### Deploy

```bash
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d
```

### Verify

```bash
podman ps --filter "name=janusgraph-demo"
curl -s http://localhost:9200/_cluster/health | jq
curl -s http://localhost:18182/
```

---

**Executor:** David Leconte
**Co-Authored-By:** David Leconte <team@example.com>
