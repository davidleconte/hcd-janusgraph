# Deployment Scripts Duplicate Code Audit

**Date:** 2026-02-11  
**Auditor:** Bob (AI Assistant)  
**Purpose:** Identify duplicate patterns in deployment scripts for consolidation

---

## Executive Summary

**Total Scripts Audited:** 5  
**Duplicate Patterns Found:** 8 major categories  
**Estimated Code Reduction:** 30-40% (150-200 lines)  
**Maintainability Impact:** High - Single source of truth for common operations

---

## Duplicate Patterns Identified

### 1. SCRIPT_DIR Resolution (5 occurrences)

**Pattern:**
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
```

**Found in:**
- `deploy_full_stack.sh` (lines 2-3, 11-12) - **DUPLICATE WITHIN SAME FILE**
- `stop_full_stack.sh` (lines 2-3)
- `cleanup_and_reset.sh` (lines 7-8)
- `demo_quickstart.sh` (lines 27-28)
- `setup_demo_env.sh` (lines 27-28)

**Impact:** Critical - appears in every script, duplicated in deploy_full_stack.sh

---

### 2. Environment Loading (5 occurrences)

**Pattern:**
```bash
if [ -f ".env" ]; then
    source .env
fi
# OR
source "$PROJECT_ROOT/.env" || source "$PROJECT_ROOT/.env.example"
```

**Found in:**
- `deploy_full_stack.sh` (lines 4, 16-18) - **DUPLICATE WITHIN SAME FILE**
- `stop_full_stack.sh` (lines 4, 8-10)
- `cleanup_and_reset.sh` (lines 11-13)
- `demo_quickstart.sh` (implicit via setup_demo_env.sh)
- `setup_demo_env.sh` (lines 78-87 - checks if exists)

**Impact:** High - inconsistent patterns across scripts

---

### 3. Project Name Configuration (4 occurrences)

**Pattern:**
```bash
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"
# OR
PROJECT_NAME="janusgraph-demo"
```

**Found in:**
- `deploy_full_stack.sh` (line 74)
- `cleanup_and_reset.sh` (line 16)
- `demo_quickstart.sh` (line 31)
- `setup_demo_env.sh` (line 31)

**Impact:** Medium - hardcoded default value repeated

---

### 4. Podman Connection Configuration (3 occurrences)

**Pattern:**
```bash
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"
```

**Found in:**
- `deploy_full_stack.sh` (line 21)
- `stop_full_stack.sh` (line 13)
- Implied in other scripts

**Impact:** Medium - configuration duplication

---

### 5. Port Configuration (1 major occurrence)

**Pattern:**
```bash
HCD_CQL_PORT="${HCD_CQL_PORT:-19042}"
JANUSGRAPH_GREMLIN_PORT="${JANUSGRAPH_GREMLIN_PORT:-18182}"
JANUSGRAPH_MGMT_PORT="${JANUSGRAPH_MGMT_PORT:-18184}"
JUPYTER_PORT="${JUPYTER_PORT:-8888}"
VISUALIZER_PORT="${VISUALIZER_PORT:-3000}"
GRAPHEXP_PORT="${GRAPHEXP_PORT:-8080}"
PROMETHEUS_PORT="${PROMETHEUS_PORT:-9090}"
GRAFANA_PORT="${GRAFANA_PORT:-3001}"
NETWORK_NAME="${NETWORK_NAME:-hcd-janusgraph-network}"
```

**Found in:**
- `deploy_full_stack.sh` (lines 23-31)

**Impact:** Low - only in one script, but should be centralized

---

### 6. Podman Health Checks (2 occurrences)

**Pattern:**
```bash
if ! podman --remote --connection $PODMAN_CONNECTION ps >/dev/null 2>&1; then
    echo "❌ Podman machine '$PODMAN_CONNECTION' not accessible"
    echo "   Start it with: podman machine start $PODMAN_CONNECTION"
    exit 1
fi
```

**Found in:**
- `deploy_full_stack.sh` (lines 44-48)
- Implied need in other scripts

**Impact:** High - critical validation missing from other scripts

---

### 7. Color Definitions (2 occurrences)

**Pattern:**
```bash
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
```

**Found in:**
- `demo_quickstart.sh` (lines 19-24)
- `setup_demo_env.sh` (lines 20-24)

**Impact:** Low - cosmetic, but should be centralized

---

### 8. Service Status Checks (2 occurrences)

**Pattern:**
```bash
if ! podman ps --filter "label=project=$PROJECT_NAME" | grep -q "hcd-server"; then
    echo "Warning: HCD server may not be running"
fi
```

**Found in:**
- `demo_quickstart.sh` (lines 119-122, 124-127)
- Needed in other scripts

**Impact:** Medium - useful validation pattern

---

## Critical Issues Found

### Issue 1: Duplicate SCRIPT_DIR in deploy_full_stack.sh

**Lines 2-3:**
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/.env" || source "$PROJECT_ROOT/.env.example"
```

**Lines 11-13:**
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
```

**Impact:** CRITICAL - Same code duplicated within the same file!

---

### Issue 2: Inconsistent Environment Loading

**Three different patterns:**

1. **Pattern A** (deploy_full_stack.sh line 4):
   ```bash
   source "$PROJECT_ROOT/.env" || source "$PROJECT_ROOT/.env.example"
   ```

2. **Pattern B** (deploy_full_stack.sh lines 16-18):
   ```bash
   if [ -f ".env" ]; then
       source .env
   fi
   ```

3. **Pattern C** (cleanup_and_reset.sh lines 11-13):
   ```bash
   if [ -f "$PROJECT_ROOT/.env" ]; then
       source "$PROJECT_ROOT/.env"
   fi
   ```

**Impact:** HIGH - Inconsistent behavior across scripts

---

### Issue 3: Missing Validation

**Scripts lacking podman health checks:**
- `stop_full_stack.sh` - No check before stopping
- `cleanup_and_reset.sh` - No check before cleanup
- `demo_quickstart.sh` - No check before deployment
- `setup_demo_env.sh` - N/A (doesn't use podman)

**Impact:** MEDIUM - Could fail silently

---

## Proposed Common Functions

### common.sh Structure

```bash
#!/bin/bash
# ==============================================================================
# Common Deployment Functions
# ==============================================================================

# 1. Path Resolution
init_paths() {
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    export SCRIPT_DIR PROJECT_ROOT
}

# 2. Environment Loading
load_environment() {
    if [ -f "$PROJECT_ROOT/.env" ]; then
        source "$PROJECT_ROOT/.env"
    elif [ -f "$PROJECT_ROOT/.env.example" ]; then
        echo "⚠️  Using .env.example (create .env for custom config)"
        source "$PROJECT_ROOT/.env.example"
    fi
}

# 3. Configuration Defaults
set_defaults() {
    export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"
    export PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"
    export PODMAN_PLATFORM="${PODMAN_PLATFORM:-linux/arm64}"
    
    # Ports
    export HCD_CQL_PORT="${HCD_CQL_PORT:-19042}"
    export JANUSGRAPH_GREMLIN_PORT="${JANUSGRAPH_GREMLIN_PORT:-18182}"
    export JANUSGRAPH_MGMT_PORT="${JANUSGRAPH_MGMT_PORT:-18184}"
    export JUPYTER_PORT="${JUPYTER_PORT:-8888}"
    export VISUALIZER_PORT="${VISUALIZER_PORT:-3000}"
    export GRAPHEXP_PORT="${GRAPHEXP_PORT:-8080}"
    export PROMETHEUS_PORT="${PROMETHEUS_PORT:-9090}"
    export GRAFANA_PORT="${GRAFANA_PORT:-3001}"
    export NETWORK_NAME="${NETWORK_NAME:-hcd-janusgraph-network}"
}

# 4. Color Definitions
init_colors() {
    export RED='\033[0;31m'
    export GREEN='\033[0;32m'
    export YELLOW='\033[1;33m'
    export BLUE='\033[0;34m'
    export CYAN='\033[0;36m'
    export NC='\033[0m'
}

# 5. Podman Health Check
check_podman() {
    local connection="${1:-$PODMAN_CONNECTION}"
    
    if ! podman --remote --connection "$connection" ps >/dev/null 2>&1; then
        echo -e "${RED}❌ Podman machine '$connection' not accessible${NC}"
        echo "   Start it with: podman machine start $connection"
        return 1
    fi
    
    echo -e "${GREEN}✅ Podman machine accessible${NC}"
    return 0
}

# 6. Port Availability Check
check_port() {
    local port=$1
    local service=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port $port already in use ($service)${NC}"
        return 1
    fi
    return 0
}

# 7. Service Health Check
check_service() {
    local service_name=$1
    local project="${2:-$COMPOSE_PROJECT_NAME}"
    
    if podman ps --filter "label=project=$project" | grep -q "$service_name"; then
        echo -e "${GREEN}✅ $service_name is running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $service_name is not running${NC}"
        return 1
    fi
}

# 8. Wait for Service
wait_for_service() {
    local service_name=$1
    local timeout=${2:-120}
    local interval=${3:-5}
    
    echo "⏳ Waiting for $service_name (timeout: ${timeout}s)..."
    
    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if check_service "$service_name" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready${NC}"
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    echo -e "${RED}❌ Timeout waiting for $service_name${NC}"
    return 1
}

# 9. Initialize All
init_common() {
    init_paths
    load_environment
    set_defaults
    init_colors
}
```

---

## Refactoring Strategy

### Phase 1: Create common.sh (Day 2)
1. Create `scripts/deployment/common.sh` with all common functions
2. Add comprehensive error handling
3. Add logging functions
4. Add validation functions

### Phase 2: Refactor deploy_full_stack.sh (Day 3)
1. Remove duplicate SCRIPT_DIR definitions
2. Source common.sh
3. Replace duplicated code with function calls
4. Add missing validations

### Phase 3: Refactor Other Scripts (Day 4)
1. Update stop_full_stack.sh
2. Update cleanup_and_reset.sh
3. Update demo_quickstart.sh
4. Update setup_demo_env.sh

### Phase 4: Create GitHub Action (Day 4)
1. Create `.github/actions/deploy-common/action.yml`
2. Reuse common.sh functions
3. Add GitHub-specific features

---

## Expected Benefits

### Code Reduction
- **Before:** ~500 lines across 5 scripts
- **After:** ~350 lines (common.sh + refactored scripts)
- **Reduction:** 30% (150 lines)

### Maintainability
- Single source of truth for common operations
- Consistent error handling
- Consistent validation
- Easier to add new features

### Reliability
- Comprehensive validation in all scripts
- Consistent environment loading
- Better error messages
- Fail-fast behavior

---

## Migration Checklist

- [ ] Create scripts/deployment/common.sh
- [ ] Add comprehensive tests for common.sh
- [ ] Refactor deploy_full_stack.sh
- [ ] Refactor stop_full_stack.sh
- [ ] Refactor cleanup_and_reset.sh
- [ ] Refactor demo_quickstart.sh
- [ ] Refactor setup_demo_env.sh
- [ ] Create GitHub composite action
- [ ] Update documentation
- [ ] Test all scripts
- [ ] Measure code reduction

---

## Next Steps

1. ✅ **Day 1:** Complete audit (this document)
2. **Day 2:** Create common.sh with all functions
3. **Day 3:** Refactor deploy_full_stack.sh (highest priority)
4. **Day 4:** Refactor remaining scripts + GitHub action
5. **Day 5:** Validate, test, document

---

**Audit Status:** ✅ COMPLETE  
**Ready for Implementation:** YES  
**Estimated Implementation Time:** 3-4 days  
**Risk Level:** LOW (backward compatible approach)