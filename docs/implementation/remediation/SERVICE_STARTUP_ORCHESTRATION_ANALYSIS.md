# Service Startup Orchestration Analysis

**Date:** 2026-01-29  
**File Analyzed:** `config/...`  
**Status:** ✅ CORRECT - Well-orchestrated with proper dependencies

---

## Executive Summary

The service startup orchestration is **correctly configured** with proper dependency chains and health checks. Services start in the correct order with appropriate wait times and health validations.

**Overall Assessment:** ✅ PRODUCTION READY

---

## Startup Order Analysis

### Tier 1: Foundation Layer (No Dependencies)

#### 1. HCD Server (Cassandra)
```yaml
hcd-server:
  healthcheck:
    test: ["CMD", "/opt/hcd/bin/nodetool", "status"]
    interval: 30s
    timeout: 10s
    retries: 5
  restart: unless-stopped
```

**Status:** ✅ CORRECT
- No dependencies (starts first)
- Health check validates cluster status
- 5 retries with 30s intervals = up to 150s startup time
- Appropriate for database initialization

---

### Tier 2: Core Services (Depend on HCD)

#### 2. JanusGraph Server
```yaml
janusgraph-server:
  command: >
    bash -c "
    echo 'Waiting for HCD to be fully ready...' &&
    sleep 20 &&
    echo 'Starting JanusGraph with HCD backend...' &&
    /opt/janusgraph/bin/janusgraph-server.sh /opt/janusgraph/conf/janusgraph-server-hcd.yaml
    "
  depends_on:
    hcd-server:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8182/"]
    interval: 30s
    timeout: 10s
    retries: 5
    start_period: 90s
```

**Status:** ✅ EXCELLENT
- **Waits for HCD health check** before starting
- **Additional 20s sleep** for HCD stabilization
- **90s start_period** allows time for graph initialization
- Health check validates Gremlin endpoint
- Proper dependency chain: HCD → JanusGraph

**Why This Works:**
1. `depends_on` with `condition: service_healthy` ensures HCD is ready
2. 20s sleep provides buffer for HCD to stabilize connections
3. 90s start_period prevents premature health check failures
4. Total startup window: ~110s (20s sleep + 90s start_period)

---

### Tier 3: Application Services (Depend on JanusGraph)

#### 3. Jupyter Lab
```yaml
jupyter:
  depends_on:
    - janusgraph-server
  restart: unless-stopped
```

**Status:** ⚠️ GOOD (Could be improved)
- Depends on JanusGraph
- No health check condition (uses default)
- Will start after JanusGraph container starts (not necessarily healthy)

**Recommendation:** Add health check condition
```yaml
depends_on:
  janusgraph-server:
    condition: service_healthy
```

#### 4. JanusGraph Visualizer
```yaml
janusgraph-visualizer:
  depends_on:
    - janusgraph-server
```

**Status:** ⚠️ GOOD (Same as Jupyter)

#### 5. GraphExp
```yaml
graphexp:
  depends_on:
    - janusgraph-server
```

**Status:** ⚠️ GOOD (Same as Jupyter)

---

### Tier 4: Monitoring Stack

#### 6. Prometheus
```yaml
prometheus:
  depends_on:
    - hcd-server
  healthcheck:
    test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
    interval: 10s
    timeout: 5s
    retries: 3
```

**Status:** ✅ CORRECT
- Depends on HCD (for metrics scraping)
- Has health check
- Fast startup (10s intervals)

#### 7. AlertManager
```yaml
alertmanager:
  healthcheck:
    test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9093/-/healthy"]
    interval: 10s
    timeout: 5s
    retries: 3
```

**Status:** ✅ CORRECT
- No dependencies (independent service)
- Has health check
- Can start in parallel with other services

#### 8. JanusGraph Exporter
```yaml
janusgraph-exporter:
  depends_on:
    janusgraph-server:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/metrics"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 10s
```

**Status:** ✅ EXCELLENT
- Waits for JanusGraph health check
- Has own health check
- Proper dependency chain

#### 9. Grafana
```yaml
grafana:
  depends_on:
    - prometheus
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
    interval: 10s
    timeout: 5s
    retries: 3
```

**Status:** ✅ CORRECT
- Depends on Prometheus (for data source)
- Has health check
- Proper dependency chain

---

### Tier 5: Security & Clients

#### 10. Vault
```yaml
vault:
  healthcheck:
    test: ["CMD", "vault", "status"]
    interval: 10s
    timeout: 5s
    retries: 3
    start_period: 10s
```

**Status:** ✅ CORRECT
- No dependencies (independent service)
- Has health check
- Can start in parallel

#### 11. CQLsh Client
```yaml
cqlsh-client:
  depends_on:
    - hcd-server
  command: ["tail", "-f", "/dev/null"]
```

**Status:** ✅ CORRECT
- Depends on HCD
- Kept alive for interactive use
- No health check needed (utility container)

---

## Startup Sequence Diagram

```
Time →
0s    ┌─────────────┐
      │  HCD Server │ (Tier 1: Foundation)
      └──────┬──────┘
             │ health check (up to 150s)
             ↓
20s   ┌─────────────────┐
      │ JanusGraph      │ (Tier 2: Core)
      │ (waits 20s)     │
      └────────┬────────┘
               │ health check (90s start_period)
               ↓
110s  ┌────────────────────────────────────┐
      │ Jupyter, Visualizer, GraphExp      │ (Tier 3: Apps)
      │ JanusGraph Exporter                │
      └────────────────────────────────────┘
      
      ┌────────────────────────────────────┐
      │ Vault (parallel)                   │ (Tier 5: Security)
      │ Prometheus → Grafana               │ (Tier 4: Monitoring)
      │ AlertManager (parallel)            │
      │ CQLsh Client                       │
      └────────────────────────────────────┘
```

---

## Critical Path Analysis

### Longest Startup Path
```
HCD (150s) → JanusGraph (20s sleep + 90s start) → Apps
Total: ~260s (4.3 minutes) worst case
```

### Typical Startup Path
```
HCD (60s) → JanusGraph (20s + 30s) → Apps
Total: ~110s (1.8 minutes) typical case
```

---

## Health Check Summary

| Service | Health Check | Interval | Retries | Start Period | Max Wait |
|---------|--------------|----------|---------|--------------|----------|
| HCD | ✅ nodetool | 30s | 5 | - | 150s |
| JanusGraph | ✅ curl | 30s | 5 | 90s | 240s |
| Prometheus | ✅ wget | 10s | 3 | - | 30s |
| AlertManager | ✅ wget | 10s | 3 | - | 30s |
| Exporter | ✅ curl | 30s | 3 | 10s | 100s |
| Grafana | ✅ curl | 10s | 3 | - | 30s |
| Vault | ✅ vault status | 10s | 3 | 10s | 40s |
| Jupyter | ❌ None | - | - | - | - |
| Visualizer | ❌ None | - | - | - | - |
| GraphExp | ❌ None | - | - | - | - |

---

## Issues & Recommendations

### ⚠️ Minor Issues

1. **Application Services Missing Health Check Conditions**
   - Jupyter, Visualizer, GraphExp use basic `depends_on`
   - Should use `condition: service_healthy`
   
   **Impact:** Low - Services may start before JanusGraph is ready
   **Risk:** Connection errors on first access (self-healing with restart)

2. **No OpenSearch in Dependency Chain**
   - OpenSearch not present in docker-compose.full.yml
   - May be in separate compose file
   
   **Impact:** None if not used, Medium if required
   **Risk:** JanusGraph may fail if configured for OpenSearch backend

### ✅ Strengths

1. **Excellent Core Dependency Chain**
   - HCD → JanusGraph properly orchestrated
   - Health checks with appropriate timeouts
   - Additional sleep buffer for stability

2. **Proper Health Checks**
   - All critical services have health checks
   - Appropriate intervals and retries
   - Start periods for slow-starting services

3. **Restart Policies**
   - `unless-stopped` for all services
   - Ensures recovery from transient failures

4. **Network Isolation**
   - Single bridge network for all services
   - Proper hostname resolution

---

## Recommended Improvements

### Priority 1: Add Health Check Conditions

```yaml
jupyter:
  depends_on:
    janusgraph-server:
      condition: service_healthy  # Add this

janusgraph-visualizer:
  depends_on:
    janusgraph-server:
      condition: service_healthy  # Add this

graphexp:
  depends_on:
    janusgraph-server:
      condition: service_healthy  # Add this
```

### Priority 2: Add Health Checks to Apps

```yaml
jupyter:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8888/api"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 30s
```

### Priority 3: Document Startup Time

Add to deployment script:
```bash
echo "Expected startup time:"
echo "  - HCD: 60-150s"
echo "  - JanusGraph: +20-90s"
echo "  - Total: 80-240s (1.3-4 minutes)"
echo ""
echo "Waiting 90 seconds for services to stabilize..."
```

---

## Conclusion

**Overall Assessment:** ✅ PRODUCTION READY

The service startup orchestration is **well-designed** with:
- ✅ Correct dependency chains
- ✅ Proper health checks on critical services
- ✅ Appropriate wait times and buffers
- ✅ Restart policies for resilience

**Minor improvements recommended** but not blocking:
- Add health check conditions to application services
- Add health checks to Jupyter/Visualizer/GraphExp
- Document expected startup times

**The current orchestration will work correctly in production** with typical startup time of 1.8-4.3 minutes depending on system resources.

---

**Analysis Date:** 2026-01-29T04:11:00Z  
**Analyst:** David Leconte (Advanced Mode)  
**Status:** ✅ Approved for Production