# Tooling Standards (MANDATORY)

This file defines mandatory tooling requirements for the HCD + JanusGraph Banking Compliance Platform.

---

## Python Package Management

**RULE:** All Python package operations MUST use `uv`

```bash
# ✅ CORRECT
uv pip install package-name
uv pip install -r requirements.txt
uv pip install -e ".[dev]"

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

---

## Container Orchestration

**RULE:** All container operations MUST use `podman` and `podman-compose`

```bash
# ✅ CORRECT
podman ps
podman-compose -p janusgraph-demo up -d

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

---

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

---

## Validation Requirements

**RULE:** All deployment scripts must validate tooling before proceeding

Required checks:
1. uv is installed
2. podman is installed
3. podman-compose is installed
4. podman machine is running
5. COMPOSE_PROJECT_NAME is set

**Example validation script:**

```bash
#!/bin/bash
# Validate tooling requirements

echo "Validating tooling requirements..."

# Check uv
if ! command -v uv &> /dev/null; then
    echo "❌ ERROR: uv is required but not installed"
    echo "   Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check podman
if ! command -v podman &> /dev/null; then
    echo "❌ ERROR: podman is required but not installed"
    echo "   Install: brew install podman"
    exit 1
fi

# Check podman-compose
if ! command -v podman-compose &> /dev/null; then
    echo "❌ ERROR: podman-compose is required but not installed"
    echo "   Install: brew install podman-compose"
    exit 1
fi

# Check podman machine
if ! podman machine list | grep -q "Running"; then
    echo "❌ ERROR: Podman machine is not running"
    echo "   Start: podman machine start"
    exit 1
fi

# Check project name
if [ -z "$COMPOSE_PROJECT_NAME" ]; then
    echo "❌ ERROR: COMPOSE_PROJECT_NAME environment variable not set"
    echo "   Set: export COMPOSE_PROJECT_NAME=janusgraph-demo"
    exit 1
fi

echo "✅ Tooling validation passed"
```

---

## Emergency Fallback Procedures

### When uv is unavailable

**ONLY use pip if:**
1. uv cannot be installed (restricted environment)
2. Critical production issue requires immediate fix
3. Documented in `.pip-usage-log`

```bash
# Emergency fallback
pip install package-name

# MUST document usage
echo "$(date): Used pip for package-name because: [reason]" >> .pip-usage-log
```

### When podman is unavailable

**ONLY use docker if:**
1. podman cannot be installed (restricted environment)
2. Critical production issue requires immediate fix
3. Documented in `.docker-usage-log`

```bash
# Emergency fallback
docker-compose up -d

# MUST document usage
echo "$(date): Used docker-compose because: [reason]" >> .docker-usage-log
```

---

## Migration Guide

### From pip to uv

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Verify installation
uv --version

# 3. Migrate existing environment
conda activate janusgraph-analysis
uv pip install -r requirements.txt

# 4. Verify
uv pip list
```

### From docker to podman

```bash
# 1. Install podman
brew install podman podman-compose

# 2. Initialize machine
podman machine init --cpus 4 --memory 8192 --disk-size 50
podman machine start

# 3. Stop docker services
docker-compose down

# 4. Deploy with podman
export COMPOSE_PROJECT_NAME="janusgraph-demo"
cd config/compose
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d

# 5. Verify
podman ps --filter "label=project=janusgraph-demo"
```

---

## Enforcement Mechanisms

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: check-uv
        name: Check uv is installed
        entry: bash -c 'command -v uv >/dev/null 2>&1 || (echo "❌ uv is required" && exit 1)'
        language: system
        pass_filenames: false
      
      - id: check-podman
        name: Check podman is installed
        entry: bash -c 'command -v podman >/dev/null 2>&1 || (echo "❌ podman is required" && exit 1)'
        language: system
        pass_filenames: false
      
      - id: no-pip-usage
        name: Prevent direct pip usage
        entry: bash -c 'git diff --cached --name-only | xargs grep -l "^pip install" && echo "❌ Use uv pip instead" && exit 1 || exit 0'
        language: system
        pass_filenames: false
      
      - id: no-docker-usage
        name: Prevent docker usage
        entry: bash -c 'git diff --cached --name-only | xargs grep -l "docker-compose\|docker run" && echo "❌ Use podman instead" && exit 1 || exit 0'
        language: system
        pass_filenames: false
```

### CI/CD Validation

Add to GitHub Actions workflows:

```yaml
jobs:
  validate-tooling:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Verify uv installation
        run: uv --version
      
      - name: Check for pip usage in scripts
        run: |
          if grep -r "^pip install" --include="*.sh" scripts/; then
            echo "❌ Found pip usage - use uv pip instead"
            exit 1
          fi
      
      - name: Check for docker usage in scripts
        run: |
          if grep -r "docker-compose\|docker run" --include="*.sh" scripts/; then
            echo "❌ Found docker usage - use podman instead"
            exit 1
          fi
```

---

## Exceptions

### Approved Exceptions

The following are approved exceptions to tooling standards:

1. **CI/CD Runners:** GitHub Actions runners may use docker if podman is unavailable
2. **Legacy Scripts:** Scripts in `scripts/archive/` may use old tooling (deprecated)
3. **Documentation Examples:** Historical examples may reference old tooling (must be marked as deprecated)

### Requesting Exceptions

To request an exception:

1. Create GitHub issue with `tooling-exception` label
2. Provide detailed justification
3. Propose alternative approach
4. Get approval from 2+ maintainers

---

## Compliance Checklist

Before merging any PR, verify:

- [ ] All Python package operations use `uv pip`
- [ ] All container operations use `podman`/`podman-compose`
- [ ] All deployments set `COMPOSE_PROJECT_NAME`
- [ ] All scripts include tooling validation
- [ ] Documentation uses correct tooling
- [ ] No direct `pip install` commands
- [ ] No `docker`/`docker-compose` commands
- [ ] Pre-commit hooks pass
- [ ] CI/CD validation passes

---

**Last Updated:** 2026-02-11  
**Version:** 1.0  
**Status:** MANDATORY
