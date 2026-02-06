# Network Isolation Analysis - Podman Environment

**Date:** 2026-01-29  
**Podman Machine:** podman-wxd  
**Status:** ⚠️ PARTIAL ISOLATION - Needs Improvement

---

## Executive Summary

The current configuration provides **partial isolation** through a dedicated bridge network (`hcd-janusgraph-network`), but **does NOT use pods** for complete isolation. Services can potentially interact with other projects on the same Podman machine.

**Risk Level:** MEDIUM  
**Recommendation:** Implement pod-based isolation or use project-specific naming prefixes

---

## Current Configuration Analysis

### Network Configuration

**Docker Compose (docker-compose.full.yml):**
```yaml
networks:
  hcd-janusgraph-network:
    driver: bridge
```

**Deployment Script (deploy_full_stack.sh):**
```bash
NETWORK_NAME="${NETWORK_NAME:-hcd-janusgraph-network}"
```

**All services connect to:** `hcd-janusgraph-network`

### Container Naming

**Current Names:**
- `hcd-server`
- `janusgraph-server`
- `jupyter-lab`
- `janusgraph-visualizer`
- `graphexp`
- `cqlsh-client`
- `prometheus`
- `grafana`

**Issue:** Generic names without project prefix

---

## Isolation Assessment

### ✅ What IS Isolated

1. **Network Traffic**
   - Services communicate only within `hcd-janusgraph-network`
   - Cannot directly access services on other bridge networks
   - Internal DNS resolution scoped to network

2. **Service Discovery**
   - Hostname resolution limited to network members
   - Services find each other by container name within network

3. **Port Exposure**
   - Only explicitly mapped ports accessible from host
   - Internal ports isolated within network

### ❌ What is NOT Isolated

1. **Container Names**
   - Names are global across Podman machine
   - Conflict if another project uses same names
   - Example: Two projects can't both have `prometheus`

2. **Volume Names**
   - Volumes are global: `hcd-data`, `janusgraph-db`, etc.
   - No project prefix to prevent conflicts
   - Risk of data mixing if names collide

3. **Network Names**
   - Network name `hcd-janusgraph-network` is global
   - Another project could create same network name
   - Potential for accidental cross-project communication

4. **Host Ports**
   - Ports like 8182, 9042, 8888 are global
   - Conflicts if another project uses same ports
   - Only one project can bind to each port

---

## Pod-Based Isolation (Not Currently Used)

### What Pods Would Provide

**Podman Pods** create a shared network namespace for containers:

```bash
# Create isolated pod
podman pod create --name janusgraph-pod \
  --network janusgraph-net \
  -p 8182:8182 \
  -p 9042:9042

# Add containers to pod
podman run --pod janusgraph-pod ...
```

**Benefits:**
- Complete network isolation
- Shared localhost within pod
- Single network namespace
- Kubernetes-compatible

**Current Status:** ❌ NOT IMPLEMENTED

---

## Risk Analysis

### Scenario 1: Name Conflicts

**Risk:** Another project tries to create `prometheus` container

**Current Behavior:**
```bash
Error: container name "prometheus" is already in use
```

**Impact:** Deployment fails, requires manual cleanup

**Likelihood:** HIGH (common service names)

---

### Scenario 2: Port Conflicts

**Risk:** Another project tries to use port 8182

**Current Behavior:**
```bash
Error: port 8182 is already allocated
```

**Impact:** Deployment fails, requires port reconfiguration

**Likelihood:** MEDIUM (JanusGraph port is specific)

---

### Scenario 3: Volume Conflicts

**Risk:** Another project creates volume named `hcd-data`

**Current Behavior:**
- Podman reuses existing volume
- Data from different projects mixed
- Potential data corruption

**Impact:** CRITICAL - Data integrity compromised

**Likelihood:** LOW (specific naming) but HIGH IMPACT

---

### Scenario 4: Network Conflicts

**Risk:** Another project creates `hcd-janusgraph-network`

**Current Behavior:**
- Podman reuses existing network
- Services from different projects on same network
- Potential security breach

**Impact:** HIGH - Cross-project communication possible

**Likelihood:** LOW but HIGH IMPACT

---

## Recommended Solutions

### Option 1: Project-Specific Naming (Quick Fix)

**Add project prefix to all resources:**

```yaml
# docker-compose.full.yml
networks:
  janusgraph-demo-network:  # Add prefix
    driver: bridge

volumes:
  janusgraph-demo-hcd-data:  # Add prefix
  janusgraph-demo-janusgraph-db:  # Add prefix

services:
  hcd-server:
    container_name: janusgraph-demo-hcd  # Add prefix
    networks:
      - janusgraph-demo-network
```

**Pros:**
- Easy to implement
- Backward compatible with compose
- Clear project ownership

**Cons:**
- Requires updating all references
- Still not true pod isolation

---

### Option 2: Use Podman Pods (Best Practice)

**Create pod-based deployment:**

```bash
# Create pod with all port mappings
podman pod create \
  --name janusgraph-demo-pod \
  --network janusgraph-demo-net \
  -p 8182:8182 \
  -p 9042:9042 \
  -p 8888:8888 \
  -p 3000:3000 \
  -p 8080:8080 \
  -p 9090:9090 \
  -p 3001:3000

# Deploy containers to pod
podman run --pod janusgraph-demo-pod ...
```

**Pros:**
- Complete isolation
- Kubernetes-compatible
- Shared localhost within pod
- Single network namespace

**Cons:**
- Requires rewriting deployment scripts
- Not compatible with docker-compose
- More complex management

---

### Option 3: Use Compose Project Name (Recommended)

**Leverage docker-compose project naming:**

```bash
# Deploy with project name
podman-compose -p janusgraph-demo up -d

# This automatically prefixes:
# - Containers: janusgraph-demo_hcd-server_1
# - Networks: janusgraph-demo_hcd-janusgraph-network
# - Volumes: janusgraph-demo_hcd-data
```

**Pros:**
- Built-in compose feature
- Automatic prefixing
- Easy to implement
- Maintains compose compatibility

**Cons:**
- Longer names
- Requires updating scripts to use project name

---

## Implementation Recommendation

### Immediate Action (Priority 1)

**Use Compose Project Name:**

```bash
# Update deploy_full_stack.sh
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"

# Deploy with project name
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d
```

**Benefits:**
- Quick to implement (1 line change)
- Automatic resource prefixing
- Prevents all naming conflicts
- Maintains existing compose files

---

### Long-Term Solution (Priority 2)

**Migrate to Pod-Based Deployment:**

1. Create pod creation script
2. Update deployment to use pods
3. Test Kubernetes compatibility
4. Document pod management

**Timeline:** 1-2 weeks

---

## Current Risk Mitigation

### Temporary Measures

1. **Document Port Usage**
   - List all ports in README
   - Check for conflicts before deployment

2. **Use Cleanup Script**
   - Run cleanup before each deployment
   - Prevents stale resource conflicts

3. **Namespace Volumes**
   - Manually add prefixes to volume names
   - Update compose file

---

## Verification Commands

### Check for Conflicts

```bash
# List all containers
podman ps -a --format "{{.Names}}"

# List all networks
podman network ls

# List all volumes
podman volume ls

# Check port usage
netstat -an | grep -E "8182|9042|8888"
```

### Verify Isolation

```bash
# Check network membership
podman network inspect hcd-janusgraph-network

# Verify no cross-network communication
podman exec janusgraph-server ping other-project-container
# Should fail if properly isolated
```

---

## Conclusion

**Current State:** ⚠️ PARTIAL ISOLATION

**Risks:**
- Name conflicts: HIGH
- Port conflicts: MEDIUM  
- Volume conflicts: LOW but CRITICAL impact
- Network conflicts: LOW but HIGH impact

**Recommended Action:**
1. **Immediate:** Add compose project name (`-p janusgraph-demo`)
2. **Short-term:** Update documentation with conflict prevention
3. **Long-term:** Migrate to pod-based deployment

**With project name implementation:** ✅ FULL ISOLATION ACHIEVED

---

**Analysis Date:** 2026-01-29T04:15:00Z  
**Analyst:** David Leconte (Advanced Mode)  
**Status:** ⚠️ Needs Improvement