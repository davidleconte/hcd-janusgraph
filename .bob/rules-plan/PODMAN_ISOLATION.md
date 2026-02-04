# Podman Container Isolation Rules

**Source:** Based on [`/Users/david.leconte/Documents/Work/Labs/Adal/podman-architecture/PODMAN_ARCHITECTURE.md`](/Users/david.leconte/Documents/Work/Labs/Adal/podman-architecture/PODMAN_ARCHITECTURE.md)  
**Date:** 2026-01-30  
**Status:** MANDATORY for all deployments

---

## Five Layers of Isolation (REQUIRED)

### 1. Network Isolation (Layer 3) - MANDATORY

**Rule:** Each project MUST have its own isolated network with unique subnet

```bash
# CORRECT - Project-specific network
podman network create \
  --subnet 10.89.X.0/24 \
  --label project=janusgraph-demo \
  janusgraph-demo-network

# WRONG - Generic network name (conflicts possible)
podman network create hcd-janusgraph-network
```

**Benefits:**
- Containers in janusgraph-demo cannot reach other projects
- Each project has its own DNS namespace
- No IP conflicts between projects
- Clean network-level separation

**Verification:**
```bash
podman network inspect janusgraph-demo-network | grep Subnet
# Should show unique subnet like 10.89.5.0/24
```

### 2. Volume Isolation (Storage Layer) - MANDATORY

**Rule:** All volumes MUST be prefixed with project name

```bash
# CORRECT - Project-prefixed volumes
janusgraph-demo-hcd-data
janusgraph-demo-janusgraph-db
janusgraph-demo-prometheus-data

# WRONG - Generic volume names (data mixing risk)
hcd-data
janusgraph-db
prometheus-data
```

**Benefits:**
- No shared volumes between projects
- Data persists independently
- Easy per-project backup
- No accidental data mixing

**Verification:**
```bash
podman volume ls --filter "label=project=janusgraph-demo"
# Should show only janusgraph-demo volumes
```

### 3. Resource Limits (CPU/Memory) - MANDATORY

**Rule:** Every pod/container MUST have explicit resource limits

```bash
# CORRECT - Explicit limits
podman pod create \
  --name janusgraph-demo-pod \
  --cpus 4 \
  --memory 10g \
  --label project=janusgraph-demo

# WRONG - No limits (can starve other projects)
podman pod create --name janusgraph-demo-pod
```

**Recommended Allocation:**
- HCD: 4GB RAM, 2 CPUs
- JanusGraph: 4GB RAM, 2 CPUs
- Monitoring: 2GB RAM, 1 CPU
- Total: 10GB RAM, 5 CPUs

**Verification:**
```bash
podman pod stats janusgraph-demo-pod
# Should show resource usage within limits
```

### 4. Port Mapping (Application Layer) - MANDATORY

**Rule:** Check for port conflicts BEFORE deployment

```bash
# CORRECT - Check ports first
netstat -an | grep -E "8182|9042|8888"
# If conflicts found, use custom ports:
HOST_JANUSGRAPH_PORT=18182 \
HOST_HCD_PORT=19042 \
HOST_JUPYTER_PORT=18888 \
./scripts/deployment/deploy_full_stack.sh

# WRONG - Deploy without checking (will fail if ports in use)
./scripts/deployment/deploy_full_stack.sh
```

**Default Ports:**
```
9042 → 9042 (HCD CQL)
8182 → 8182 (JanusGraph Gremlin)
8888 → 8888 (Jupyter)
9090 → 9090 (Prometheus)
3001 → 3000 (Grafana)
```

**Custom Ports (if conflicts):**
```
19042 → 9042 (HCD CQL)
18182 → 8182 (JanusGraph Gremlin)
18888 → 8888 (Jupyter)
19090 → 9090 (Prometheus)
13001 → 3000 (Grafana)
```

### 5. Label-Based Management - MANDATORY

**Rule:** Every resource MUST be tagged with project label

```bash
# CORRECT - All resources labeled
podman pod create \
  --name janusgraph-demo-pod \
  --label project=janusgraph-demo \
  --label environment=development

podman volume create \
  --label project=janusgraph-demo \
  janusgraph-demo-hcd-data

podman network create \
  --label project=janusgraph-demo \
  janusgraph-demo-network

# WRONG - No labels (cannot filter by project)
podman pod create --name janusgraph-demo-pod
```

**Benefits:**
- Easy to list resources per project
- Bulk operations per project (start/stop all)
- No accidental cross-project operations
- Clear resource ownership

**Verification:**
```bash
# List all janusgraph-demo resources
podman ps --filter "label=project=janusgraph-demo"
podman volume ls --filter "label=project=janusgraph-demo"
podman network ls --filter "label=project=janusgraph-demo"
```

---

## Deployment Script Requirements

### MUST Use Project Name

```bash
# CORRECT - Use COMPOSE_PROJECT_NAME
COMPOSE_PROJECT_NAME="janusgraph-demo"
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d

# This automatically prefixes:
# - Containers: janusgraph-demo_hcd-server_1
# - Networks: janusgraph-demo_hcd-janusgraph-network
# - Volumes: janusgraph-demo_hcd-data

# WRONG - No project name (conflicts inevitable)
podman-compose -f docker-compose.full.yml up -d
```

### MUST Check Isolation After Deployment

```bash
# Verify isolation
./scripts/deployment/verify_isolation.sh

# Should check:
# 1. All containers have project prefix
# 2. All volumes have project prefix
# 3. All networks have project prefix
# 4. No port conflicts
# 5. Resource limits applied
```

---

## Docker Compose File Requirements

### Network Configuration

```yaml
# CORRECT - Project-specific network
networks:
  janusgraph-demo-network:
    driver: bridge
    labels:
      project: janusgraph-demo

# WRONG - Generic network name
networks:
  hcd-janusgraph-network:
    driver: bridge
```

### Volume Configuration

```yaml
# CORRECT - Project-prefixed volumes
volumes:
  janusgraph-demo-hcd-data:
    driver: local
    labels:
      project: janusgraph-demo
  janusgraph-demo-janusgraph-db:
    driver: local
    labels:
      project: janusgraph-demo

# WRONG - Generic volume names
volumes:
  hcd-data:
    driver: local
  janusgraph-db:
    driver: local
```

### Service Configuration

```yaml
# CORRECT - Labels and resource limits
services:
  hcd-server:
    container_name: janusgraph-demo-hcd-server
    labels:
      project: janusgraph-demo
      component: database
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
    networks:
      - janusgraph-demo-network
    volumes:
      - janusgraph-demo-hcd-data:/var/lib/hcd/data

# WRONG - No labels, no limits, generic names
services:
  hcd-server:
    container_name: hcd-server
    networks:
      - hcd-janusgraph-network
    volumes:
      - hcd-data:/var/lib/hcd/data
```

---

## Management Operations

### Per-Project Operations

```bash
# Start all janusgraph-demo containers
podman ps -a --filter "label=project=janusgraph-demo" --format "{{.Names}}" | \
  xargs -I {} podman start {}

# Stop all janusgraph-demo containers
podman ps --filter "label=project=janusgraph-demo" --format "{{.Names}}" | \
  xargs -I {} podman stop {}

# Remove all janusgraph-demo resources (keeps volumes)
podman ps -a --filter "label=project=janusgraph-demo" --format "{{.Names}}" | \
  xargs -I {} podman rm -f {}

# Full cleanup (including volumes)
podman volume ls --filter "label=project=janusgraph-demo" --format "{{.Name}}" | \
  xargs -I {} podman volume rm {}
```

### Multi-Project Overview

```bash
# List all projects on machine
podman ps --format "{{.Labels}}" | grep -o 'project=[^,]*' | sort -u

# Show resource usage by project
podman stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
  --filter "label=project=janusgraph-demo"
```

---

## Port Conflict Detection

### Pre-Deployment Check

```bash
#!/bin/bash
# Check if ports are available

REQUIRED_PORTS=(8182 9042 8888 9090 3001 8080 8200)

echo "Checking port availability..."
for port in "${REQUIRED_PORTS[@]}"; do
  if netstat -an | grep -q ":$port.*LISTEN"; then
    echo "❌ Port $port is already in use"
    netstat -an | grep ":$port.*LISTEN"
    exit 1
  else
    echo "✅ Port $port is available"
  fi
done

echo "All ports available for deployment"
```

### Port Conflict Resolution

```bash
# If conflicts found, use custom ports
export HOST_JANUSGRAPH_PORT=18182
export HOST_HCD_PORT=19042
export HOST_JUPYTER_PORT=18888
export HOST_PROMETHEUS_PORT=19090
export HOST_GRAFANA_PORT=13001

# Update docker-compose.yml to use these ports
# Then deploy
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d
```

---

## Validation Checklist

Before considering deployment successful, verify:

- [ ] All containers have `janusgraph-demo` prefix
- [ ] All volumes have `janusgraph-demo` prefix
- [ ] All networks have `janusgraph-demo` prefix
- [ ] All resources have `project=janusgraph-demo` label
- [ ] No port conflicts on host
- [ ] Resource limits applied to all containers
- [ ] Containers can communicate within project network
- [ ] Containers CANNOT communicate with other projects
- [ ] Volumes are isolated (no cross-project access)

**Verification Script:**
```bash
#!/bin/bash
# scripts/deployment/verify_isolation.sh

PROJECT_NAME="janusgraph-demo"

echo "Verifying isolation for project: $PROJECT_NAME"

# Check containers
echo "1. Checking containers..."
CONTAINERS=$(podman ps --filter "label=project=$PROJECT_NAME" --format "{{.Names}}")
if [ -z "$CONTAINERS" ]; then
  echo "❌ No containers found with project label"
  exit 1
fi
echo "✅ Found containers: $CONTAINERS"

# Check volumes
echo "2. Checking volumes..."
VOLUMES=$(podman volume ls --filter "label=project=$PROJECT_NAME" --format "{{.Name}}")
if [ -z "$VOLUMES" ]; then
  echo "❌ No volumes found with project label"
  exit 1
fi
echo "✅ Found volumes: $VOLUMES"

# Check networks
echo "3. Checking networks..."
NETWORKS=$(podman network ls --filter "label=project=$PROJECT_NAME" --format "{{.Name}}")
if [ -z "$NETWORKS" ]; then
  echo "❌ No networks found with project label"
  exit 1
fi
echo "✅ Found networks: $NETWORKS"

# Check resource limits
echo "4. Checking resource limits..."
podman pod inspect janusgraph-demo-pod 2>/dev/null | grep -q "CPUQuota"
if [ $? -eq 0 ]; then
  echo "✅ Resource limits configured"
else
  echo "⚠️  No resource limits found"
fi

echo "Isolation verification complete"
```

---

## Common Mistakes to Avoid

### ❌ WRONG: Generic Names

```bash
# These will conflict with other projects
podman pod create --name janusgraph-pod
podman volume create hcd-data
podman network create janusgraph-network
```

### ✅ CORRECT: Project-Prefixed Names

```bash
# These are isolated per project
podman pod create --name janusgraph-demo-pod --label project=janusgraph-demo
podman volume create janusgraph-demo-hcd-data --label project=janusgraph-demo
podman network create janusgraph-demo-network --label project=janusgraph-demo
```

### ❌ WRONG: No Resource Limits

```bash
# Can starve other projects
podman run -d --name hcd-server localhost/hcd:1.2.3
```

### ✅ CORRECT: Explicit Limits

```bash
# Guaranteed resources, cannot starve others
podman run -d \
  --name janusgraph-demo-hcd-server \
  --cpus 2 \
  --memory 4g \
  --label project=janusgraph-demo \
  localhost/hcd:1.2.3
```

### ❌ WRONG: Shared Volumes

```bash
# Risk of data mixing
volumes:
  - hcd-data:/var/lib/hcd/data
```

### ✅ CORRECT: Project-Specific Volumes

```bash
# Isolated data storage
volumes:
  - janusgraph-demo-hcd-data:/var/lib/hcd/data
```

---

## References

- **Source Architecture:** [`/Users/david.leconte/Documents/Work/Labs/Adal/podman-architecture/PODMAN_ARCHITECTURE.md`](/Users/david.leconte/Documents/Work/Labs/Adal/podman-architecture/PODMAN_ARCHITECTURE.md)
- **Podman Commands:** [`/Users/david.leconte/Documents/Work/Labs/Adal/podman-architecture/PODMAN_COMMANDS.md`](/Users/david.leconte/Documents/Work/Labs/Adal/podman-architecture/PODMAN_COMMANDS.md)
- **Network Isolation Analysis:** [`docs/implementation/remediation/NETWORK_ISOLATION_ANALYSIS.md`](../../docs/implementation/remediation/NETWORK_ISOLATION_ANALYSIS.md)

---

**Last Updated:** 2026-01-30  
**Status:** MANDATORY - Must be followed for all deployments  
**Enforcement:** Automated validation required before production