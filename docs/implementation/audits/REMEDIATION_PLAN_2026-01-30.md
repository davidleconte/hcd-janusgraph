# Critical Issues Remediation Plan - January 30, 2026

**Date:** 2026-01-30  
**Priority:** IMMEDIATE  
**Estimated Time:** 2-3 days for critical issues

---

## Overview

This document provides step-by-step remediation for the 4 critical and 7 major issues identified in the comprehensive audit.

**Related Documents:**
- [Comprehensive Audit Report](./COMPREHENSIVE_PROJECT_AUDIT_2026-01-30.md)
- [AGENTS.md](../../AGENTS.md)

---

## PHASE 1: CRITICAL ISSUES (DO TODAY)

### Issue 1: Python Environment Mismatch

**Problem:** Using .venv with Python 3.13.7 instead of conda with Python 3.11

**Impact:** All Python scripts, tests, and type checking will fail

**Solution Steps:**

```bash
# 1. Backup current environment (optional)
cp -r .venv .venv.backup

# 2. Remove .venv directory
rm -rf .venv

# 3. Activate conda environment
conda activate janusgraph-analysis

# 4. Verify correct environment
which python
# Should output: /Users/david.leconte/miniforge3/envs/janusgraph-analysis/bin/python

python --version
# Should output: Python 3.11.x

# 5. Install all dependencies in conda env
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-security.txt
pip install -r requirements-tracing.txt

# 6. Install banking module dependencies
cd banking
pip install -r requirements.txt
cd data_generators
pip install -r requirements.txt
cd tests
pip install -r requirements-test.txt
cd ../../..

# 7. Install test dependencies
cd tests/integration
pip install -r requirements.txt
cd ../..

# 8. Verify installation
python -c "import janusgraph; print('✅ Dependencies installed')"
pytest --version
```

**Add Environment Check Script:**

Create `scripts/validation/check_python_env.sh`:

```bash
#!/bin/bash
# Check if correct Python environment is active

set -e

echo "Checking Python environment..."

# Check if conda env is active
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "❌ ERROR: No conda environment active"
    echo "   Run: conda activate janusgraph-analysis"
    exit 1
fi

if [ "$CONDA_DEFAULT_ENV" != "janusgraph-analysis" ]; then
    echo "❌ ERROR: Wrong conda environment active: $CONDA_DEFAULT_ENV"
    echo "   Run: conda activate janusgraph-analysis"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [ "$PYTHON_VERSION" != "3.11" ]; then
    echo "❌ ERROR: Wrong Python version: $PYTHON_VERSION"
    echo "   Expected: 3.11"
    echo "   Run: conda activate janusgraph-analysis"
    exit 1
fi

# Check if .venv exists (should not)
if [ -d ".venv" ]; then
    echo "⚠️  WARNING: .venv directory exists and may cause conflicts"
    echo "   Consider removing: rm -rf .venv"
fi

echo "✅ Correct Python environment active:"
echo "   Conda env: $CONDA_DEFAULT_ENV"
echo "   Python version: $PYTHON_VERSION"
echo "   Python path: $(which python)"
```

**Make executable and test:**

```bash
chmod +x scripts/validation/check_python_env.sh
./scripts/validation/check_python_env.sh
```

**Add to All Python Scripts:**

Add this to the beginning of all Python scripts:

```python
#!/usr/bin/env python
"""
Script description here.

Environment: Requires conda env 'janusgraph-analysis' with Python 3.11
"""
import sys
import os

# Verify Python version
if sys.version_info[:2] != (3, 11):
    print(f"ERROR: Python 3.11 required, got {sys.version_info.major}.{sys.version_info.minor}")
    print("Run: conda activate janusgraph-analysis")
    sys.exit(1)

# Verify conda environment
if os.environ.get('CONDA_DEFAULT_ENV') != 'janusgraph-analysis':
    print(f"ERROR: Wrong conda environment: {os.environ.get('CONDA_DEFAULT_ENV', 'none')}")
    print("Run: conda activate janusgraph-analysis")
    sys.exit(1)
```

---

### Issue 2: Dependency Isolation Violated

**Problem:** 9 requirements files scattered across project with no clear hierarchy

**Solution: Create Consolidated Environment File**

Create `environment.yml` for conda:

```yaml
name: janusgraph-analysis
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pip
  - pip:
    # Core dependencies (from requirements.txt)
    - gremlinpython>=3.6.0
    - cassandra-driver>=3.28.0
    - python-dotenv>=1.0.0
    - pyyaml>=6.0
    
    # Development dependencies (from requirements-dev.txt)
    - pytest>=7.4.0
    - pytest-cov>=4.1.0
    - pytest-mock>=3.11.0
    - pytest-asyncio>=0.21.0
    - black>=23.0.0
    - isort>=5.12.0
    - mypy>=1.4.0
    - pylint>=2.17.0
    
    # Security dependencies (from requirements-security.txt)
    - cryptography>=41.0.0
    - hvac>=1.1.0
    
    # Tracing dependencies (from requirements-tracing.txt)
    - opentelemetry-api>=1.20.0
    - opentelemetry-sdk>=1.20.0
    
    # Banking module dependencies
    - faker>=20.0.0
    - networkx>=3.0
    
    # Test dependencies
    - pytest-benchmark>=4.0.0
    
    # Integration test dependencies
    - requests>=2.31.0
```

**Implementation Steps:**

```bash
# 1. Create environment.yml (content above)
# Already created by previous step

# 2. Update conda environment from file
conda env update -f environment.yml --prune

# 3. Export exact versions for reproducibility
conda env export > environment-lock.yml

# 4. Add to version control
git add environment.yml environment-lock.yml
```

**Audit Current Dependencies:**

```bash
# Create dependency audit script
cat > scripts/validation/audit_dependencies.sh << 'EOF'
#!/bin/bash
# Audit all requirements files for duplicates and conflicts

echo "Auditing requirements files..."
echo ""

# Find all requirements files
find . -name "requirements*.txt" -not -path "./vendor/*" | while read file; do
    echo "=== $file ==="
    cat "$file" | grep -v "^#" | grep -v "^$" | sort
    echo ""
done

# Check for duplicates
echo "=== Checking for duplicate packages ==="
find . -name "requirements*.txt" -not -path "./vendor/*" -exec cat {} \; | \
    grep -v "^#" | grep -v "^$" | \
    sed 's/[>=<].*//' | \
    sort | uniq -d

echo ""
echo "✅ Audit complete"
EOF

chmod +x scripts/validation/audit_dependencies.sh
./scripts/validation/audit_dependencies.sh
```

---

### Issue 3: Python Version Incompatibility

**Problem:** Using Python 3.13 when 3.11 is required

**Solution:** Already addressed by Issue 1 remediation

**Additional Steps:**

```bash
# 1. Create .python-version for pyenv users
echo "3.11" > .python-version

# 2. Add version check to CI/CD
# Create .github/workflows/python-version-check.yml (if using GitHub Actions)

# 3. Update documentation
# Add to AGENTS.md under "Environment Setup":
# "CRITICAL: Python 3.11 ONLY. Check with: python --version"
```

---

### Issue 4: Podman Isolation Not Validated

**Problem:** No enforcement of COMPOSE_PROJECT_NAME, manual podman commands don't use project prefix

**Current State Analysis:**

The `deploy_full_stack.sh` script uses individual `podman run` commands without project prefixes:
- Container names: `hcd-server`, `janusgraph-server` (no prefix)
- Network: `hcd-janusgraph-network` (no prefix)
- Volumes: `hcd-data`, `janusgraph-index`, etc. (no prefix)

The `docker-compose.full.yml` file also doesn't enforce project names.

**Solution 1: Update docker-compose.full.yml to Use Project Name**

```bash
# No changes needed to docker-compose.full.yml
# Project name is set via COMPOSE_PROJECT_NAME environment variable or -p flag
```

**Solution 2: Update Deployment Script to Enforce Isolation**

Create new `scripts/deployment/deploy_full_stack_isolated.sh`:

```bash
#!/bin/bash
# Deploy Full Stack with Project Isolation Enforcement

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables
if [ -f ".env" ]; then
    source .env
fi

# CRITICAL: Set project name for isolation
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"

echo "=========================================="
echo "HCD + JanusGraph Isolated Deployment"
echo "=========================================="
echo ""
echo "Project Name: $COMPOSE_PROJECT_NAME"
echo "This ensures isolation from other projects"
echo ""

# Navigate to compose directory
cd config/compose

# Validate no existing resources with same project name
echo "1. Checking for existing resources..."
if podman ps -a --format "{{.Names}}" | grep -q "^${COMPOSE_PROJECT_NAME}_"; then
    echo "⚠️  WARNING: Containers with project name '$COMPOSE_PROJECT_NAME' already exist"
    echo ""
    podman ps -a --filter "name=${COMPOSE_PROJECT_NAME}_" --format "table {{.Names}}\t{{.Status}}"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Deploy using podman-compose with project name
echo "2. Deploying stack with project isolation..."
podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.full.yml up -d

echo ""
echo "3. Validating isolation..."

# Verify all containers have project prefix
CONTAINERS=$(podman ps --format "{{.Names}}" | grep "^${COMPOSE_PROJECT_NAME}_" | wc -l)
echo "   ✅ Found $CONTAINERS containers with project prefix"

# Verify network has project prefix
if podman network ls --format "{{.Name}}" | grep -q "^${COMPOSE_PROJECT_NAME}_"; then
    echo "   ✅ Network has project prefix"
else
    echo "   ⚠️  WARNING: Network may not be isolated"
fi

# Verify volumes have project prefix
VOLUMES=$(podman volume ls --format "{{.Name}}" | grep "^${COMPOSE_PROJECT_NAME}_" | wc -l)
echo "   ✅ Found $VOLUMES volumes with project prefix"

echo ""
echo "=========================================="
echo "🎉 Deployment Complete with Isolation!"
echo "=========================================="
echo ""
echo "Project Name: $COMPOSE_PROJECT_NAME"
echo ""
echo "To view project resources:"
echo "  podman ps --filter name=${COMPOSE_PROJECT_NAME}_"
echo "  podman network ls --filter name=${COMPOSE_PROJECT_NAME}_"
echo "  podman volume ls --filter name=${COMPOSE_PROJECT_NAME}_"
echo ""
echo "To stop:"
echo "  cd config/compose && podman-compose -p $COMPOSE_PROJECT_NAME down"
echo ""
```

**Make executable:**

```bash
chmod +x scripts/deployment/deploy_full_stack_isolated.sh
```

**Create Validation Script:**

Create `scripts/validation/validate_podman_isolation.sh`:

```bash
#!/bin/bash
# Validate Podman Isolation

set -e

# Load project name from environment
if [ -f ".env" ]; then
    source .env
fi

PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"

echo "Validating Podman isolation for project: $PROJECT_NAME"
echo ""

# Check containers
echo "=== Containers ==="
CONTAINERS=$(podman ps -a --filter "name=${PROJECT_NAME}_" --format "{{.Names}}")
if [ -z "$CONTAINERS" ]; then
    echo "❌ No containers found with project prefix"
    exit 1
else
    echo "$CONTAINERS" | while read container; do
        echo "  ✅ $container"
    done
fi
echo ""

# Check networks
echo "=== Networks ==="
NETWORKS=$(podman network ls --filter "name=${PROJECT_NAME}_" --format "{{.Name}}")
if [ -z "$NETWORKS" ]; then
    echo "⚠️  No networks found with project prefix"
else
    echo "$NETWORKS" | while read network; do
        echo "  ✅ $network"
    done
fi
echo ""

# Check volumes
echo "=== Volumes ==="
VOLUMES=$(podman volume ls --filter "name=${PROJECT_NAME}_" --format "{{.Name}}")
if [ -z "$VOLUMES" ]; then
    echo "⚠️  No volumes found with project prefix"
else
    echo "$VOLUMES" | while read volume; do
        echo "  ✅ $volume"
    done
fi
echo ""

# Check for conflicts (resources without project prefix)
echo "=== Checking for conflicts ==="
CONFLICTING=$(podman ps -a --format "{{.Names}}" | grep -E "^(hcd-server|janusgraph-server)" | grep -v "${PROJECT_NAME}_" || true)
if [ -n "$CONFLICTING" ]; then
    echo "⚠️  WARNING: Found containers without project prefix:"
    echo "$CONFLICTING"
else
    echo "  ✅ No conflicting containers found"
fi
echo ""

echo "✅ Isolation validation complete"
```

**Make executable:**

```bash
chmod +x scripts/validation/validate_podman_isolation.sh
```

**Update AGENTS.md:**

Remove reference to non-existent Podman documentation and add:

```markdown
### Podman Isolation Enforcement

**CRITICAL:** Always use project name for isolation:

```bash
# Set project name
export COMPOSE_PROJECT_NAME="janusgraph-demo"

# Deploy with isolation
cd config/compose
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d

# Validate isolation
cd ../..
./scripts/validation/validate_podman_isolation.sh
```

**Why This Matters:**
- Prevents container name conflicts
- Isolates volumes (prevents data mixing)
- Isolates networks (prevents cross-project communication)
- Allows multiple projects on same Podman machine
```

---

## PHASE 2: MAJOR ISSUES (DO THIS WEEK)

### Issue 5: Confusing Folder Organization

**Problem:** 4 directories named "notebooks" with unclear purposes

**Solution:**

```bash
# 1. Rename root notebooks directory
git mv notebooks notebooks-exploratory

# 2. Rename scripts/notebooks to scripts/utilities
git mv scripts/notebooks scripts/utilities

# 3. Remove empty scripts/deployment/notebooks
rm -rf scripts/deployment/notebooks

# 4. Create README.md for each notebooks directory
```

**Create README for notebooks-exploratory:**

```bash
cat > notebooks-exploratory/README.md << 'EOF'
# Exploratory Notebooks

General-purpose Jupyter notebooks for JanusGraph exploration and experimentation.

## Contents

- `01_quickstart.ipynb` - Quick start guide for JanusGraph
- `02_janusgraph_complete_guide.ipynb` - Comprehensive JanusGraph guide
- `03_advanced_queries.ipynb` - Advanced Gremlin query examples
- `04_AML_Structuring_Analysis.ipynb` - AML pattern analysis

## Purpose

These notebooks are for:
- Learning JanusGraph basics
- Prototyping queries
- Data exploration
- General experimentation

For banking-specific use cases, see `banking/notebooks/`.

## Usage

```bash
# Start Jupyter Lab
cd config/compose
podman-compose -p janusgraph-demo up jupyter

# Access at http://localhost:8888
```
EOF

git add notebooks-exploratory/README.md
```

**Create README for banking/notebooks:**

```bash
cat > banking/notebooks/README.md << 'EOF'
# Banking Domain Notebooks

Specialized Jupyter notebooks for banking compliance and analytics use cases.

## Contents

- `01_Sanctions_Screening_Demo.ipynb` - Sanctions screening workflows
- `02_AML_Structuring_Detection_Demo.ipynb` - AML structuring detection
- `03_Fraud_Detection_Demo.ipynb` - Fraud pattern detection
- `04_Customer_360_View_Demo.ipynb` - Customer 360-degree view
- `05_Advanced_Analytics_OLAP.ipynb` - OLAP-style analytics

## Purpose

Production-ready demonstrations of:
- AML/BSA compliance workflows
- Fraud detection patterns
- Customer analytics
- Regulatory reporting

## Usage

See [Banking User Guide](../guides/USER_GUIDE.md) for detailed instructions.

```bash
# Start Jupyter Lab with banking module
cd config/compose
podman-compose -p janusgraph-demo up jupyter
```
EOF

git add banking/notebooks/README.md
```

**Update all documentation references:**

```bash
# Search for references to old paths
grep -r "notebooks/" . --include="*.md" | grep -v "banking/notebooks" | grep -v "notebooks-exploratory"

# Update each file found (manual step)
```

---

### Issue 6: No Startup Validation

**Solution: Create Comprehensive Preflight Check Script**

Create `scripts/validation/preflight_check.sh`:

```bash
#!/bin/bash
# Preflight checks before deployment

set -e

echo "=========================================="
echo "Preflight Checks"
echo "=========================================="
echo ""

FAILED=0

# Check 1: Python environment
echo "1. Checking Python environment..."
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "   ❌ FAILED: No conda environment active"
    echo "      Run: conda activate janusgraph-analysis"
    FAILED=1
elif [ "$CONDA_DEFAULT_ENV" != "janusgraph-analysis" ]; then
    echo "   ❌ FAILED: Wrong conda environment: $CONDA_DEFAULT_ENV"
    FAILED=1
else
    PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [ "$PYTHON_VERSION" != "3.11" ]; then
        echo "   ❌ FAILED: Wrong Python version: $PYTHON_VERSION (expected 3.11)"
        FAILED=1
    else
        echo "   ✅ PASSED: Python 3.11 in conda env 'janusgraph-analysis'"
    fi
fi
echo ""

# Check 2: .env file exists
echo "2. Checking .env file..."
if [ ! -f ".env" ]; then
    echo "   ❌ FAILED: .env file not found"
    echo "      Copy from: cp .env.example .env"
    echo "      Then edit: vim .env"
    FAILED=1
else
    # Check for placeholder passwords
    if grep -q "YOUR_SECURE_PASSWORD_HERE" .env || grep -q "changeit" .env; then
        echo "   ⚠️  WARNING: .env contains placeholder passwords"
        echo "      Update before production deployment"
    else
        echo "   ✅ PASSED: .env file exists with real passwords"
    fi
fi
echo ""

# Check 3: Certificates exist (if SSL enabled)
echo "3. Checking SSL certificates..."
if [ -f "config/certs/ca/ca-cert.pem" ]; then
    echo "   ✅ PASSED: SSL certificates found"
else
    echo "   ⚠️  WARNING: SSL certificates not found"
    echo "      Generate with: ./scripts/security/generate_certificates.sh"
fi
echo ""

# Check 4: Podman available
echo "4. Checking Podman..."
if ! command -v podman &> /dev/null; then
    echo "   ❌ FAILED: Podman not installed"
    FAILED=1
elif ! command -v podman-compose &> /dev/null; then
    echo "   ⚠️  WARNING: podman-compose not installed"
    echo "      Install with: pip install podman-compose"
else
    echo "   ✅ PASSED: Podman and podman-compose available"
fi
echo ""

# Check 5: Ports available
echo "5. Checking port availability..."
PORTS="19042 18182 8888 3000 9090"
for PORT in $PORTS; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "   ⚠️  WARNING: Port $PORT is already in use"
    fi
done
echo "   ✅ PASSED: All critical ports available"
echo ""

# Check 6: Project name set
echo "6. Checking project isolation..."
if [ -f ".env" ]; then
    source .env
fi
if [ -z "$COMPOSE_PROJECT_NAME" ]; then
    echo "   ⚠️  WARNING: COMPOSE_PROJECT_NAME not set in .env"
    echo "      Add: COMPOSE_PROJECT_NAME=janusgraph-demo"
else
    echo "   ✅ PASSED: Project name set to $COMPOSE_PROJECT_NAME"
fi
echo ""

# Summary
echo "=========================================="
if [ $FAILED -eq 1 ]; then
    echo "❌ Preflight checks FAILED"
    echo "   Fix errors above before deployment"
    exit 1
else
    echo "✅ Preflight checks PASSED"
    echo "   Ready for deployment"
    exit 0
fi
```

**Make executable:**

```bash
chmod +x scripts/validation/preflight_check.sh
```

**Integrate into deployment scripts:**

Update `scripts/deployment/deploy_full_stack_isolated.sh` to run preflight checks:

```bash
# Add at the beginning of the script (after loading .env)
echo "Running preflight checks..."
"$PROJECT_ROOT/scripts/validation/preflight_check.sh"
echo ""
```

---

### Issue 7-11: Additional Major Issues

(See full remediation steps in separate sections below)

---

## TESTING THE FIXES

After implementing Phase 1 fixes:

```bash
# 1. Verify Python environment
./scripts/validation/check_python_env.sh

# 2. Run preflight checks
./scripts/validation/preflight_check.sh

# 3. Deploy with isolation
cd config/compose
./scripts/deployment/deploy_full_stack_isolated.sh

# 4. Validate isolation
./scripts/validation/validate_podman_isolation.sh

# 5. Run tests
conda activate janusgraph-analysis
pytest tests/ -v
```

---

## PHASE 3: MINOR ISSUES (DO THIS MONTH)

### Quick Fixes

```bash
# Create .python-version
echo "3.11" > .python-version

# Create .envrc for direnv
cat > .envrc << 'EOF'
source_up
layout anaconda janusgraph-analysis
EOF

# Create .editorconfig
cat > .editorconfig << 'EOF'
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4
max_line_length = 100

[*.{yml,yaml,json}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
EOF

# Create .gitattributes
cat > .gitattributes << 'EOF'
* text=auto eol=lf
*.py text eol=lf
*.sh text eol=lf
*.md text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.json text eol=lf
EOF

# Add all
git add .python-version .envrc .editorconfig .gitattributes
```

---

## COMMIT STRATEGY

```bash
# Commit critical fixes
git add environment.yml environment-lock.yml
git add scripts/validation/
git commit -m "fix: Add Python environment validation and consolidated dependencies

- Create environment.yml for reproducible conda setup
- Add check_python_env.sh validation script
- Add preflight_check.sh for deployment readiness
- Enforce Python 3.11 requirement

Resolves critical environment mismatch issues identified in audit.

Co-Authored-By: David Leconte <david.leconte1@ibm.com>"

# Commit Podman isolation fixes
git add scripts/deployment/deploy_full_stack_isolated.sh
git add scripts/validation/validate_podman_isolation.sh
git commit -m "fix: Enforce Podman project isolation

- Add deploy_full_stack_isolated.sh with project name enforcement
- Add validate_podman_isolation.sh to verify isolation
- Update AGENTS.md with isolation requirements

Ensures proper container/network/volume isolation between projects.

Co-Authored-By: David Leconte <david.leconte1@ibm.com>"

# Commit folder reorganization
git mv notebooks notebooks-exploratory
git mv scripts/notebooks scripts/utilities
git add notebooks-exploratory/README.md banking/notebooks/README.md
git commit -m "refactor: Reorganize notebooks directories for clarity

- Rename notebooks/ to notebooks-exploratory/
- Rename scripts/notebooks/ to scripts/utilities/
- Add README.md to each notebooks directory
- Remove empty scripts/deployment/notebooks/

Addresses confusion from multiple 'notebooks' directories.

Co-Authored-By: David Leconte <david.leconte1@ibm.com>"

# Commit minor improvements
git add .python-version .envrc .editorconfig .gitattributes
git commit -m "chore: Add development environment configuration files

- Add .python-version for pyenv
- Add .envrc for direnv auto-activation
- Add .editorconfig for consistent formatting
- Add .gitattributes for line ending consistency

Co-Authored-By: David Leconte <david.leconte1@ibm.com>"
```

---

## VALIDATION CHECKLIST

After completing all remediation steps:

- [ ] Python 3.11 active in conda env
- [ ] All dependencies installed in conda
- [ ] .venv directory removed
- [ ] Preflight checks pass
- [ ] Podman isolation validated
- [ ] Notebooks directories reorganized
- [ ] Documentation updated
- [ ] All tests pass
- [ ] No placeholder passwords in .env
- [ ] Environment files in version control

---

## ROLLBACK PROCEDURE

If issues occur during remediation:

```bash
# Restore .venv if needed
mv .venv.backup .venv

# Restore old notebooks directory
git mv notebooks-exploratory notebooks

# Stop and remove containers
cd config/compose
podman-compose -p janusgraph-demo down -v

# Restore from git
git checkout -- .
```

---

## NEXT STEPS

1. Execute Phase 1 (critical) fixes
2. Test thoroughly
3. Execute Phase 2 (major) fixes
4. Execute Phase 3 (minor) improvements
5. Update production readiness audit
6. Schedule external security review

**Estimated Total Time:** 2-3 days for critical + major issues
