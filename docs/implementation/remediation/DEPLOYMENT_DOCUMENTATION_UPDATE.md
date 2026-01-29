# Deployment Documentation Update

**Date**: 2026-01-29  
**Status**: Complete  
**Impact**: Critical - Prevents deployment failures

---

## Overview

Updated all deployment documentation to include the **critical requirement** that `podman-compose` must be run from the `config/compose/` directory due to relative Dockerfile paths in the compose file.

---

## Root Cause

The `docker-compose.full.yml` file uses relative paths for Dockerfiles:

```yaml
services:
  visualizer:
    build:
      context: .
      dockerfile: ../../docker/visualizer/Dockerfile  # Relative to config/compose/
```

When `podman-compose` is run from the project root, these paths resolve incorrectly, causing "Dockerfile not found" errors.

---

## Files Updated

### 1. AGENTS.md
**Section**: Podman/Docker Deployment (REQUIRED)

**Changes**:
- Added explicit requirement to run from `config/compose/` directory
- Added project name requirement for isolation
- Included verification commands
- Added reference to network isolation analysis

**Key Addition**:
```bash
# MUST run from config/compose directory
cd config/compose

# Deploy with project name for isolation
COMPOSE_PROJECT_NAME="janusgraph-demo"
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d
```

### 2. README.md
**Section**: Quick Start

**Changes**:
- Updated step 3 to show directory change requirement
- Added alternative using Makefile (which handles directory change)
- Made the requirement explicit with "MUST run from config/compose directory"

**Before**:
```bash
# 3. Deploy stack
make deploy
```

**After**:
```bash
# 3. Deploy stack (MUST run from config/compose directory)
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# Or use Makefile (handles directory change automatically)
cd ../..
make deploy
```

### 3. QUICKSTART.md
**Section**: Essential Commands & Common Tasks

**Changes Made**:
- Updated "Direct Deployment" section with directory requirement
- Updated "Deploy Stack" common task with detailed explanation
- Added project name to podman-compose commands
- Updated container name examples to show project prefix

**Before**:
```bash
# Deploy full stack
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# Or use symlink at root
podman-compose -f docker-compose.full.yml up -d
```

**After**:
```bash
# Deploy full stack (MUST run from config/compose directory)
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# Or use podman-compose directly (MUST be in config/compose directory)
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d
```

---

## Why This Matters

### 1. **Prevents Deployment Failures**
Without this documentation, users running from project root will encounter:
```
Error: Dockerfile not found: ../../docker/visualizer/Dockerfile
```

### 2. **Ensures Network Isolation**
Using project name (`-p janusgraph-demo`) ensures:
- Container names: `janusgraph-demo_hcd-server_1`
- Networks: `janusgraph-demo_hcd-janusgraph-network`
- Volumes: `janusgraph-demo_hcd-data`

This prevents conflicts with other projects on the same Podman machine.

### 3. **Consistency Across Documentation**
All three key documentation files now consistently show:
- Directory requirement
- Project name usage
- Correct container naming

---

## Verification

Users can verify correct deployment with:

```bash
# Check container names include project prefix
podman ps --format "{{.Names}}" | grep janusgraph-demo

# Expected output:
# janusgraph-demo_hcd-server_1
# janusgraph-demo_janusgraph-server_1
# janusgraph-demo_jupyter-lab_1
# etc.

# Check network isolation
podman network ls | grep janusgraph-demo

# Check volume isolation
podman volume ls | grep janusgraph-demo
```

---

## Related Documentation

- [`AGENTS.md`](../../../AGENTS.md) - Complete deployment requirements
- [`docs/implementation/remediation/NETWORK_ISOLATION_ANALYSIS.md`](NETWORK_ISOLATION_ANALYSIS.md) - Network isolation analysis
- [`docs/implementation/remediation/ORCHESTRATION_IMPROVEMENTS_COMPLETE.md`](ORCHESTRATION_IMPROVEMENTS_COMPLETE.md) - Service orchestration improvements

---

## Impact Assessment

| Category | Impact | Notes |
|----------|--------|-------|
| **User Experience** | High | Prevents common deployment error |
| **Documentation Quality** | High | Consistency across all docs |
| **Production Readiness** | Medium | Improves deployment reliability |
| **Security** | Low | Indirectly improves via isolation |

---

## Testing Recommendations

Before deploying, users should:

1. **Verify working directory**:
   ```bash
   pwd  # Should show: .../hcd-tarball-janusgraph/config/compose
   ```

2. **Check compose file exists**:
   ```bash
   ls -la docker-compose.full.yml
   ```

3. **Verify Dockerfile paths**:
   ```bash
   ls -la ../../docker/*/Dockerfile
   ```

4. **Deploy with project name**:
   ```bash
   podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d
   ```

---

## Lessons Learned

### 1. **Relative Paths in Compose Files**
Docker Compose files with relative Dockerfile paths are sensitive to execution directory. Always document the required working directory.

### 2. **Project Naming for Isolation**
Using `-p` flag with podman-compose is essential for:
- Multi-project environments
- Preventing resource conflicts
- Clear resource identification

### 3. **Documentation Consistency**
Critical requirements must be documented in:
- Quick start guides (README.md)
- Detailed guides (QUICKSTART.md)
- Agent instructions (AGENTS.md)

### 4. **User Error Prevention**
Common mistakes should be:
- Explicitly documented
- Prevented with clear instructions
- Verified with example commands

---

## Future Improvements

### Short Term
- [ ] Add pre-deployment validation script
- [ ] Create deployment wrapper that enforces directory
- [ ] Add error message if run from wrong directory

### Long Term
- [ ] Consider restructuring to allow root-level deployment
- [ ] Add automated tests for deployment from various directories
- [ ] Create deployment troubleshooting guide

---

## Conclusion

All deployment documentation has been updated to prevent the common error of running `podman-compose` from the wrong directory. This critical fix improves:

1. **User Experience** - Clear, consistent instructions
2. **Deployment Reliability** - Prevents common failure mode
3. **Resource Isolation** - Proper project naming documented
4. **Documentation Quality** - Consistency across all guides

**Status**: ✅ Complete  
**Production Ready**: Yes  
**Breaking Changes**: No (documentation only)

---

**Last Updated**: 2026-01-29  
**Author**: IBM Bob  
**Review Status**: Complete