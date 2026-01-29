# Setup Guide

**File**: docs/SETUP.md  
**Created**: 2026-01-28T11:05:00.123  
**Author**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117

---

## Prerequisites

### System Requirements
- **Operating System**: macOS (ARM64/M-series) or Linux
- **RAM**: 8GB minimum, 16GB recommended
- **Disk Space**: 20GB minimum
- **Podman**: 4.9+ (or Docker with Compose plugin)
- **Python**: 3.11+
- **Git**: Latest version

### Install Podman
```bash
# macOS (Homebrew)
brew install podman

# Initialize machine
podman machine init --cpus 4 --memory 8192 --disk-size 50
podman machine start

# Verify
podman --version
podman machine list
```

### Install Python Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

---

## Quick Setup

### 1. Clone Repository
```bash
git clone https://github.com/davidleconte/hcd-janusgraph.git
cd hcd-janusgraph
```

### 2. Configure Environment
```bash
# Copy template
cp .env.example .env

# Edit .env
vim .env

# Update PODMAN_CONNECTION to your machine name
PODMAN_CONNECTION=podman-machine-default  # Or your machine name
```

### 3. Deploy Stack
```bash
# Using Makefile (recommended)
make deploy

# Or using scripts directly
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh
```

### 4. Verify Deployment
```bash
# Check containers
podman ps

# Run tests
make test

# Or run tests directly
bash scripts/testing/run_tests.sh
```

---

## Detailed Setup Steps

### Configure Podman Machine

**Check machine name**:
```bash
podman machine list
```

**Update .env with machine name**:
```bash
echo "PODMAN_CONNECTION=<your-machine-name>" >> .env
```

### Build Images

Build all Docker images from source:
```bash
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh
```

This will:
1. Build HCD image (Java 11 + HCD 1.2.3)
2. Build Jupyter image (Python + graph clients)
3. Pull JanusGraph official image
4. Pull monitoring images (Prometheus, Grafana)
5. Pull visualization images (Visualizer, Graphexp)

### Deploy Services

```bash
# Full stack (all services)
cd config/compose
podman-compose -f docker-compose.full.yml up -d

# Or core stack only (HCD + JanusGraph)
podman-compose -f docker-compose.yml up -d
```

### Wait for Startup

**HCD**: Takes 60-90 seconds to initialize
```bash
# Watch logs
podman logs -f hcd-server

# Check status
podman exec hcd-server nodetool status
# Should show: UN (Up/Normal)
```

**JanusGraph**: Takes 30-60 seconds after HCD is ready
```bash
# Watch logs
podman logs -f janusgraph-server

# Test connection
curl http://localhost:18182
```

---

## Initial Configuration

### Schema Initialization

Schema is auto-initialized on first start. To manually initialize:

```bash
python3 scripts/init/load_data.py
```

This creates:
- 3 vertex labels (person, company, product)
- 4 edge labels (knows, worksFor, created, uses)
- 9 properties
- 4 composite indexes

### Sample Data

Pre-loaded data includes:
- 5 people
- 3 companies
- 3 products
- 19 relationships

---

## Access Services

### Core Services
- **JanusGraph**: http://localhost:18182
- **HCD CQL**: localhost:19042
- **Jupyter Lab**: http://localhost:8888

### Monitoring & Visualization
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)
- **Visualizer**: http://localhost:3000
- **Graphexp**: http://localhost:8080

### Get Jupyter Token
```bash
podman logs jupyter-lab | grep token
```

---

## Troubleshooting Setup

### Podman Machine Not Running
```bash
podman machine start
```

### Port Conflicts
```bash
# Check what's using a port
lsof -i :18182

# Change port in .env
JANUSGRAPH_PORT=28182
```

### HCD Won't Start
```bash
# Check logs
podman logs hcd-server

# Increase heap size in .env
HCD_HEAP_SIZE=8G
```

### JanusGraph Can't Connect to HCD
```bash
# Verify HCD is ready
podman exec hcd-server nodetool status

# Restart JanusGraph
podman restart janusgraph-server
```

---

## Next Steps

1. **Read Documentation**: See docs/TESTING.md, docs/MONITORING.md
2. **Explore Notebooks**: Open http://localhost:8888
3. **Run Tests**: `make test`
4. **Setup Monitoring**: See docs/MONITORING.md
5. **Configure Backups**: See docs/BACKUP.md

---

**Signature**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
