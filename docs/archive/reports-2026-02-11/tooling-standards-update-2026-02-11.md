# Tooling Standards Update

**Date:** 2026-02-11  
**Purpose:** Enforce mandatory use of `uv` and `podman` for consistency  
**Status:** MANDATORY for all development and deployment  
**Priority:** HIGH

---

## Executive Summary

This document establishes **mandatory tooling standards** for the HCD + JanusGraph Banking Compliance Platform to ensure consistency, performance, and reliability across all development and deployment environments.

### Key Changes

1. **Python Package Management:** `uv` is now **MANDATORY** (replaces pip)
2. **Container Orchestration:** `podman` and `podman-compose` are **MANDATORY** (replaces Docker/docker-compose)
3. **Documentation Updates:** AGENTS.md and bobrules updated to reflect requirements
4. **Migration Guide:** Step-by-step migration from legacy tools

---

## 1. Python Package Management: uv (MANDATORY)

### 1.1 Why uv?

**Performance Benefits:**
- **10-100x faster** than pip for package installation
- Parallel downloads and installations
- Efficient dependency resolution
- Built-in caching

**Reliability Benefits:**
- Deterministic dependency resolution
- Better conflict detection
- Consistent across environments
- Compatible with pip requirements.txt

**Current State:**
- AGENTS.md lists uv as "Option C" (optional)
- Documentation shows pip as fallback
- No enforcement mechanism

**New Standard:**
- uv is **MANDATORY** for all package operations
- pip is **DEPRECATED** (only for emergency fallback)
- All documentation must show uv first

### 1.2 Updated AGENTS.md Section

**Current (Lines 50-74):**
```markdown
### Package Management

**New environment setup** - use ONE of these methods:

```bash
# Option A: Conda (recommended for new users)
conda env create -f environment.yml
conda activate janusgraph-analysis

# Option B: pip with requirements.txt
pip install -r requirements.txt

# Option C: uv (faster than pip)
uv pip install -r requirements.txt
```

**Adding packages** - use `uv` when possible (faster than pip):

```bash
# Install packages with uv (preferred)
uv pip install package-name

# Fallback to pip if uv unavailable
pip install package-name
```
```

**Proposed Update:**
```markdown
### Package Management (MANDATORY: uv)

**CRITICAL:** This project **REQUIRES** `uv` for all Python package management operations. Do not use `pip` directly.

#### Why uv?
- **10-100x faster** than pip
- Deterministic dependency resolution
- Better conflict detection
- Fully compatible with pip requirements.txt

#### Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Verify installation
uv --version
```

#### Environment Setup (MANDATORY)

**Option A: Conda + uv (Recommended)**

```bash
# Create conda environment
conda env create -f environment.yml
conda activate janusgraph-analysis

# Install packages with uv (MANDATORY)
uv pip install -r requirements.txt

# Verify
uv pip list
```

**Option B: uv venv (Pure Python)**

```bash
# Create virtual environment with uv
uv venv --python 3.11

# Activate
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
uv pip install -r requirements.txt
```

#### Adding Packages (MANDATORY: uv)

```bash
# Install packages with uv (MANDATORY)
uv pip install package-name

# Install with version constraint
uv pip install "package-name>=1.0.0,<2.0.0"

# Install from requirements file
uv pip install -r requirements.txt

# Install development dependencies
uv pip install -e ".[dev]"
```

#### Emergency Fallback (pip)

**ONLY use pip if uv is unavailable and you cannot install it:**

```bash
# Emergency fallback (NOT RECOMMENDED)
pip install package-name

# Document why uv couldn't be used
echo "Used pip because: [reason]" >> .pip-usage-log
```

#### Verification

```bash
# Verify uv is being used
which uv  # Should show uv path, not pip

# Check installed packages
uv pip list

# Verify no pip usage
if command -v pip &> /dev/null; then
    echo "⚠️  WARNING: pip is available but should not be used"
    echo "   Use 'uv pip' instead"
fi
```
```

### 1.3 CI/CD Updates

**Update `.github/workflows/quality-gates.yml`:**

```yaml
# BEFORE
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install pytest pytest-cov pytest-asyncio
    pip install -r requirements.txt

# AFTER
- name: Install uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies with uv
  run: |
    uv pip install pytest pytest-cov pytest-asyncio
    uv pip install -r requirements.txt
```

---

## 2. Container Orchestration: Podman (MANDATORY)

### 2.1 Why Podman?

**Security Benefits:**
- **Rootless containers** by default (no daemon running as root)
- Better security isolation
- No single point of failure (no daemon)
- Compatible with Docker CLI

**Architecture Benefits:**
- Daemonless architecture
- Pod support (Kubernetes-compatible)
- Better resource isolation
- Native systemd integration

**Current State:**
- Documentation mentions both Docker and Podman
- Scripts use `podman-compose`
- No clear mandate on which to use

**New Standard:**
- Podman is **MANDATORY** for all container operations
- Docker is **DEPRECATED** (not supported)
- All documentation must use podman commands

### 2.2 Updated AGENTS.md Section

**Add New Section After Package Management:**

```markdown
### Container Orchestration (MANDATORY: Podman)

**CRITICAL:** This project **REQUIRES** `podman` and `podman-compose` for all container operations. Docker and docker-compose are **NOT SUPPORTED**.

#### Why Podman?

- **Rootless by default** - Better security, no daemon running as root
- **Daemonless architecture** - No single point of failure
- **Pod support** - Kubernetes-compatible pod management
- **Docker CLI compatible** - Same commands, better architecture

#### Installation

**macOS:**

```bash
# Install Podman Desktop (includes podman-compose)
brew install podman-desktop

# Or install separately
brew install podman podman-compose

# Initialize Podman machine
podman machine init --cpus 4 --memory 8192 --disk-size 50
podman machine start

# Verify
podman --version
podman-compose --version
```

**Linux:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y podman podman-compose

# RHEL/Fedora
sudo dnf install -y podman podman-compose

# Verify
podman --version
podman-compose --version
```

#### Podman Machine Configuration

**MANDATORY:** Configure Podman machine with sufficient resources:

```bash
# Check current machine
podman machine list

# Stop existing machine (if needed)
podman machine stop

# Remove existing machine (if reconfiguring)
podman machine rm

# Create new machine with proper resources
podman machine init \
  --cpus 4 \
  --memory 8192 \
  --disk-size 50 \
  --now

# Verify machine is running
podman machine list
# Should show: Running

# Test connection
podman ps
```

#### Deployment Commands (MANDATORY)

**ALWAYS use podman-compose, NEVER docker-compose:**

```bash
# Deploy full stack (CORRECT)
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d

# Check status (CORRECT)
podman ps --filter "label=project=janusgraph-demo"

# View logs (CORRECT)
podman logs janusgraph-demo_hcd-server_1

# Stop services (CORRECT)
podman-compose -p janusgraph-demo -f docker-compose.full.yml down
```

#### Docker Compatibility (DEPRECATED)

**DO NOT USE DOCKER COMMANDS:**

```bash
# ❌ WRONG - Do not use docker
docker ps
docker-compose up

# ✅ CORRECT - Use podman
podman ps
podman-compose up
```

**If you have Docker installed, create aliases to prevent accidental use:**

```bash
# Add to ~/.bashrc or ~/.zshrc
alias docker='echo "❌ Use podman instead of docker" && false'
alias docker-compose='echo "❌ Use podman-compose instead of docker-compose" && false'
```

#### Podman Isolation (MANDATORY)

**CRITICAL:** Always use project name for isolation:

```bash
# MANDATORY: Set project name
export COMPOSE_PROJECT_NAME="janusgraph-demo"

# Deploy with project name
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d

# This ensures:
# - Containers: janusgraph-demo_hcd-server_1
# - Networks: janusgraph-demo_hcd-janusgraph-network
# - Volumes: janusgraph-demo_hcd-data
```

**See:** [`PODMAN_ISOLATION.md`](.bob/rules-plan/PODMAN_ISOLATION.md) for complete isolation requirements.

#### Verification

```bash
# Verify podman is being used
which podman  # Should show podman path

# Verify no docker usage
if command -v docker &> /dev/null; then
    echo "⚠️  WARNING: Docker is installed but should not be used"
    echo "   Use 'podman' instead"
fi

# Check podman machine status
podman machine list
# Should show: Running

# Test podman connection
podman ps
```
```

### 2.3 Script Updates

**Update `scripts/deployment/deploy_full_stack.sh`:**

```bash
# Add validation at start of script
echo "Validating tooling requirements..."

# Check podman is installed
if ! command -v podman &> /dev/null; then
    echo "❌ ERROR: podman is required but not installed"
    echo "   Install: brew install podman"
    exit 1
fi

# Check podman-compose is installed
if ! command -v podman-compose &> /dev/null; then
    echo "❌ ERROR: podman-compose is required but not installed"
    echo "   Install: brew install podman-compose"
    exit 1
fi

# Check podman machine is running
if ! podman machine list | grep -q "Running"; then
    echo "❌ ERROR: Podman machine is not running"
    echo "   Start: podman machine start"
    exit 1
fi

echo "✅ Tooling validation passed"
```

---

## 3. Bob Rules Configuration Updates

### 3.1 Create New Rule File

**File:** `.bob/rules-plan/TOOLING_STANDARDS.md`

```markdown
# Tooling Standards (MANDATORY)

## Python Package Management

**RULE:** All Python package operations MUST use `uv`

```bash
# ✅ CORRECT
uv pip install package-name
uv pip install -r requirements.txt

# ❌ WRONG
pip install package-name
pip install -r requirements.txt
```

**Enforcement:**
- CI/CD workflows must use uv
- Local development must use uv
- Documentation must show uv commands first
- pip is only for emergency fallback (must be documented)

**Rationale:**
- 10-100x faster than pip
- Deterministic dependency resolution
- Better conflict detection
- Consistent across environments

## Container Orchestration

**RULE:** All container operations MUST use `podman` and `podman-compose`

```bash
# ✅ CORRECT
podman ps
podman-compose up -d

# ❌ WRONG
docker ps
docker-compose up -d
```

**Enforcement:**
- All scripts must use podman commands
- Documentation must use podman examples
- Docker commands are deprecated
- CI/CD must use podman

**Rationale:**
- Rootless containers (better security)
- Daemonless architecture (no single point of failure)
- Pod support (Kubernetes-compatible)
- Better resource isolation

## Project Isolation

**RULE:** All podman deployments MUST use project name

```bash
# ✅ CORRECT
export COMPOSE_PROJECT_NAME="janusgraph-demo"
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d

# ❌ WRONG
podman-compose -f docker-compose.full.yml up -d  # No project name
```

**Enforcement:**
- All deployment scripts must set COMPOSE_PROJECT_NAME
- All containers must have project prefix
- All networks must have project prefix
- All volumes must have project prefix

**Rationale:**
- Prevents conflicts with other projects
- Enables multiple projects on same machine
- Clear resource ownership
- Easy cleanup per project

## Validation Scripts

**RULE:** All deployment scripts must validate tooling before proceeding

```bash
# Required checks:
1. uv is installed
2. podman is installed
3. podman-compose is installed
4. podman machine is running
5. COMPOSE_PROJECT_NAME is set
```

**Example:**

```bash
#!/bin/bash
# Validate tooling requirements

# Check uv
if ! command -v uv &> /dev/null; then
    echo "❌ ERROR: uv is required"
    exit 1
fi

# Check podman
if ! command -v podman &> /dev/null; then
    echo "❌ ERROR: podman is required"
    exit 1
fi

# Check podman-compose
if ! command -v podman-compose &> /dev/null; then
    echo "❌ ERROR: podman-compose is required"
    exit 1
fi

# Check podman machine
if ! podman machine list | grep -q "Running"; then
    echo "❌ ERROR: Podman machine not running"
    exit 1
fi

# Check project name
if [ -z "$COMPOSE_PROJECT_NAME" ]; then
    echo "❌ ERROR: COMPOSE_PROJECT_NAME not set"
    exit 1
fi

echo "✅ Tooling validation passed"
```
```

### 3.2 Update Existing Rules

**File:** `.bob/rules-plan/AGENTS.md`

**Add Section After "Docker Compose Architecture":**

```markdown
## Tooling Requirements (MANDATORY)

**Python Package Management MUST use uv** - pip is deprecated:

```bash
# CORRECT - Use uv for all package operations
uv pip install package-name
uv pip install -r requirements.txt
uv pip install -e ".[dev]"

# WRONG - Do not use pip directly
pip install package-name  # ❌ DEPRECATED
```

**Container Orchestration MUST use podman** - Docker is not supported:

```bash
# CORRECT - Use podman and podman-compose
podman ps
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d

# WRONG - Do not use docker
docker ps  # ❌ NOT SUPPORTED
docker-compose up  # ❌ NOT SUPPORTED
```

**Project Isolation MUST be enforced** - Always use project name:

```bash
# CORRECT - Project name ensures isolation
export COMPOSE_PROJECT_NAME="janusgraph-demo"
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d

# WRONG - No project name causes conflicts
podman-compose -f docker-compose.full.yml up -d  # ❌ MISSING PROJECT NAME
```

**Rationale:**
- **uv:** 10-100x faster, deterministic resolution, better conflict detection
- **podman:** Rootless security, daemonless architecture, Kubernetes-compatible
- **Project isolation:** Prevents conflicts, enables multi-project deployments
```

---

## 4. Migration Guide

### 4.1 For Developers Currently Using pip

**Step 1: Install uv**

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Verify
uv --version
```

**Step 2: Migrate existing environment**

```bash
# Activate your conda environment
conda activate janusgraph-analysis

# Export current packages
pip freeze > requirements-backup.txt

# Install with uv
uv pip install -r requirements.txt

# Verify
uv pip list
```

**Step 3: Update your workflow**

```bash
# OLD workflow (deprecated)
pip install package-name
pip install -r requirements.txt

# NEW workflow (mandatory)
uv pip install package-name
uv pip install -r requirements.txt
```

### 4.2 For Developers Currently Using Docker

**Step 1: Install Podman**

```bash
# macOS
brew install podman podman-compose

# Initialize machine
podman machine init --cpus 4 --memory 8192 --disk-size 50
podman machine start

# Verify
podman --version
podman-compose --version
```

**Step 2: Stop Docker services**

```bash
# Stop any running Docker containers
docker-compose down

# Optional: Remove Docker Desktop
# (Keep if you need it for other projects)
```

**Step 3: Deploy with Podman**

```bash
# Set project name
export COMPOSE_PROJECT_NAME="janusgraph-demo"

# Deploy
cd config/compose
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d

# Verify
podman ps --filter "label=project=janusgraph-demo"
```

**Step 4: Update your aliases**

```bash
# Add to ~/.bashrc or ~/.zshrc
alias docker='echo "❌ Use podman instead" && false'
alias docker-compose='echo "❌ Use podman-compose instead" && false'

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

---

## 5. Validation & Enforcement

### 5.1 Pre-commit Hooks

**Create `.pre-commit-config.yaml` entry:**

```yaml
repos:
  - repo: local
    hooks:
      - id: check-tooling
        name: Check tooling requirements
        entry: bash -c 'command -v uv >/dev/null 2>&1 || (echo "❌ uv is required" && exit 1)'
        language: system
        pass_filenames: false
      
      - id: check-podman
        name: Check podman requirements
        entry: bash -c 'command -v podman >/dev/null 2>&1 || (echo "❌ podman is required" && exit 1)'
        language: system
        pass_filenames: false
      
      - id: no-pip-usage
        name: Prevent direct pip usage
        entry: bash -c 'git diff --cached --name-only | xargs grep -l "pip install" && echo "❌ Use uv pip instead of pip" && exit 1 || exit 0'
        language: system
        pass_filenames: false
      
      - id: no-docker-usage
        name: Prevent docker usage
        entry: bash -c 'git diff --cached --name-only | xargs grep -l "docker-compose\|docker run" && echo "❌ Use podman-compose instead of docker-compose" && exit 1 || exit 0'
        language: system
        pass_filenames: false
```

### 5.2 CI/CD Validation

**Update all GitHub Actions workflows:**

```yaml
# Add to all workflow files
jobs:
  validate-tooling:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Verify uv installation
        run: uv --version
      
      - name: Check for pip usage
        run: |
          if grep -r "pip install" --include="*.sh" --include="*.yml" .; then
            echo "❌ Found pip usage - use uv pip instead"
            exit 1
          fi
      
      - name: Check for docker usage
        run: |
          if grep -r "docker-compose\|docker run" --include="*.sh" --include="*.yml" .; then
            echo "❌ Found docker usage - use podman instead"
            exit 1
          fi
```

### 5.3 Documentation Validation

**Create `scripts/validation/check_tooling_docs.sh`:**

```bash
#!/bin/bash
# Validate documentation uses correct tooling

echo "Checking documentation for tooling compliance..."

# Check for pip usage in docs
if grep -r "pip install" --include="*.md" docs/ README.md AGENTS.md | grep -v "uv pip"; then
    echo "❌ Found pip usage in documentation - use 'uv pip' instead"
    exit 1
fi

# Check for docker usage in docs
if grep -r "docker-compose\|docker run" --include="*.md" docs/ README.md AGENTS.md | grep -v "podman"; then
    echo "❌ Found docker usage in documentation - use 'podman' instead"
    exit 1
fi

echo "✅ Documentation tooling compliance check passed"
```

---

## 6. Implementation Timeline

### Week 1: Documentation Updates
- **Day 1:** Update AGENTS.md with mandatory uv/podman sections
- **Day 2:** Create TOOLING_STANDARDS.md in .bob/rules-plan/
- **Day 3:** Update all README files and guides
- **Day 4:** Update CI/CD workflows
- **Day 5:** Review and testing

### Week 2: Script Updates
- **Day 1:** Update deployment scripts with validation
- **Day 2:** Update testing scripts
- **Day 3:** Create migration guides
- **Day 4:** Add pre-commit hooks
- **Day 5:** Testing and validation

### Week 3: Enforcement
- **Day 1:** Enable pre-commit hooks
- **Day 2:** Update CI/CD with enforcement
- **Day 3:** Team training and migration support
- **Day 4:** Monitor and fix issues
- **Day 5:** Final validation

---

## 7. Success Criteria

| Criterion | Validation Method | Status |
|-----------|-------------------|--------|
| AGENTS.md updated | Manual review | ⏳ Pending |
| Bob rules updated | Manual review | ⏳ Pending |
| All scripts use uv | `grep -r "pip install" scripts/` returns nothing | ⏳ Pending |
| All scripts use podman | `grep -r "docker-compose" scripts/` returns nothing | ⏳ Pending |
| CI/CD uses uv | Check workflow files | ⏳ Pending |
| CI/CD uses podman | Check workflow files | ⏳ Pending |
| Pre-commit hooks active | `pre-commit run --all-files` passes | ⏳ Pending |
| Documentation updated | All docs use uv/podman | ⏳ Pending |

---

## 8. Rollback Plan

If issues arise during migration:

1. **Immediate Rollback:**
   ```bash
   # Revert to pip
   pip install -r requirements.txt
   
   # Revert to docker
   docker-compose up -d
   ```

2. **Document Issues:**
   - Create GitHub issue with details
   - Tag as `tooling-migration`
   - Include error messages and context

3. **Gradual Migration:**
   - Allow both tools temporarily
   - Migrate team by team
   - Full enforcement after 4 weeks

---

## Conclusion

This tooling standards update establishes **mandatory requirements** for:

1. **uv** for Python package management (10-100x faster than pip)
2. **podman** for container orchestration (rootless, daemonless, secure)
3. **Project isolation** for multi-project deployments

**Benefits:**
- ✅ Faster development (uv performance)
- ✅ Better security (podman rootless)
- ✅ Consistent environments
- ✅ Clear project isolation
- ✅ Kubernetes-compatible architecture

**Next Steps:**
1. Review and approve this document
2. Update AGENTS.md and bob rules
3. Begin Week 1 documentation updates
4. Schedule team training
5. Enable enforcement in Week 3

---

**Prepared by:** IBM Bob (Plan Mode)  
**Date:** 2026-02-11  
**Status:** READY FOR IMPLEMENTATION  
**Approval Required:** Development Team, DevOps Team
