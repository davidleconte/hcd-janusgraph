# David Leconte Remediation Plan - January 30, 2026

**Date:** 2026-01-30  
**Priority:** CRITICAL  
**Status:** READY FOR EXECUTION  
**Estimated Time:** 2-3 days

---

## Quick Reference

**Related Documents:**
- [Comprehensive Audit](docs/implementation/audits/COMPREHENSIVE_PROJECT_AUDIT_2026-01-30.md) - Full analysis
- [Detailed Remediation](docs/implementation/audits/REMEDIATION_PLAN_2026-01-30.md) - Complete instructions

**Issues Summary:**
- 🔴 4 Critical (Python env, dependencies, Podman isolation, notebooks)
- 🟡 7 Major (validation, scripts, documentation)
- 🟢 10 Minor (config files, hooks)

---

## ⚡ PHASE 1: CRITICAL FIXES (Today - 2-3 hours)

### ✅ Checklist

- [ ] **1. Fix Python Environment**
- [ ] **2. Create Validation Scripts**
- [ ] **3. Enforce Podman Isolation**
- [ ] **4. Reorganize Notebooks**

---

### 1️⃣ Fix Python Environment (30 minutes)

**Problem:** Using .venv with Python 3.13.7 instead of conda with Python 3.11

```bash
# Step 1: Backup (optional)
cp -r .venv .venv.backup

# Step 2: Remove .venv
rm -rf .venv

# Step 3: Activate conda environment
conda activate janusgraph-analysis

# Step 4: Verify correct environment
which python
# Expected: /Users/david.leconte/miniforge3/envs/janusgraph-analysis/bin/python

python --version
# Expected: Python 3.11.x

# Step 5: Install core dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-security.txt
pip install -r requirements-tracing.txt

# Step 6: Install banking dependencies
cd banking
pip install -r requirements.txt
cd data_generators
pip install -r requirements.txt
cd tests
pip install -r requirements-test.txt
cd ../../../

# Step 7: Install test dependencies
cd tests/integration
pip install -r requirements.txt
cd ../..

# Step 8: Verify installation
python -c "import gremlinpython; print('✅ gremlinpython OK')"
pytest --version
```

**Verification:**
```bash
# Should all pass
echo $CONDA_DEFAULT_ENV  # Should output: janusgraph-analysis
python --version  # Should output: Python 3.11.x
which python  # Should show conda path
```

---

### 2️⃣ Create Validation Scripts (15 minutes)

**Create `scripts/validation/check_python_env.sh`:**

```bash
mkdir -p scripts/validation

cat > scripts/validation/check_python_env.sh << 'VALIDATION_EOF'
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
VALIDATION_EOF

chmod +x scripts/validation/check_python_env.sh
```

**Create `scripts/validation/preflight_check.sh`:**

```bash
cat > scripts/validation/preflight_check.sh << 'PREFLIGHT_EOF'
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
echo "   ✅ Port checks complete"
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
PREFLIGHT_EOF

chmod +x scripts/validation/preflight_check.sh
```

**Test validation scripts:**

```bash
./scripts/validation/check_python_env.sh
./scripts/validation/preflight_check.sh
```

---

### 3️⃣ Enforce Podman Isolation (30 minutes)

**Create `scripts/validation/validate_podman_isolation.sh`:**

```bash
cat > scripts/validation/validate_podman_isolation.sh << 'PODMAN_EOF'
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
CONTAINERS=$(podman ps -a --filter "name=${PROJECT_NAME}_" --format "{{.Names}}" 2>/dev/null || echo "")
if [ -z "$CONTAINERS" ]; then
    echo "⚠️  No containers found with project prefix (may not be deployed yet)"
else
    echo "$CONTAINERS" | while read container; do
        echo "  ✅ $container"
    done
fi
echo ""

# Check networks
echo "=== Networks ==="
NETWORKS=$(podman network ls --filter "name=${PROJECT_NAME}_" --format "{{.Name}}" 2>/dev/null || echo "")
if [ -z "$NETWORKS" ]; then
    echo "⚠️  No networks found with project prefix (may not be deployed yet)"
else
    echo "$NETWORKS" | while read network; do
        echo "  ✅ $network"
    done
fi
echo ""

# Check volumes
echo "=== Volumes ==="
VOLUMES=$(podman volume ls --filter "name=${PROJECT_NAME}_" --format "{{.Name}}" 2>/dev/null || echo "")
if [ -z "$VOLUMES" ]; then
    echo "⚠️  No volumes found with project prefix (may not be deployed yet)"
else
    echo "$VOLUMES" | while read volume; do
        echo "  ✅ $volume"
    done
fi
echo ""

# Check for conflicts (resources without project prefix)
echo "=== Checking for conflicts ==="
CONFLICTING=$(podman ps -a --format "{{.Names}}" 2>/dev/null | grep -E "^(hcd-server|janusgraph-server)" | grep -v "${PROJECT_NAME}_" || true)
if [ -n "$CONFLICTING" ]; then
    echo "⚠️  WARNING: Found containers without project prefix:"
    echo "$CONFLICTING"
else
    echo "  ✅ No conflicting containers found"
fi
echo ""

echo "✅ Isolation validation complete"
PODMAN_EOF

chmod +x scripts/validation/validate_podman_isolation.sh
```

**Update deployment to use project name:**

```bash
# Edit .env to add project name (if not present)
if ! grep -q "COMPOSE_PROJECT_NAME" .env; then
    echo "" >> .env
    echo "# Podman Isolation" >> .env
    echo "COMPOSE_PROJECT_NAME=janusgraph-demo" >> .env
fi
```

**Test deployment with isolation:**

```bash
cd config/compose

# Deploy with project name
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d

# Wait for services
sleep 90

# Validate isolation
cd ../..
./scripts/validation/validate_podman_isolation.sh
```

---

### 4️⃣ Reorganize Notebooks (15 minutes)

**Problem:** 4 directories named "notebooks" causing confusion

```bash
# 1. Rename root notebooks directory
git mv notebooks notebooks-exploratory

# 2. Rename scripts/notebooks to scripts/utilities
git mv scripts/notebooks scripts/utilities

# 3. Remove empty scripts/deployment/notebooks
rmdir scripts/deployment/notebooks

# 4. Create README for notebooks-exploratory
cat > notebooks-exploratory/README.md << 'README_EOF'
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
README_EOF

git add notebooks-exploratory/README.md

# 5. Update banking/notebooks README
cat > banking/notebooks/README.md << 'BANKING_README_EOF'
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
BANKING_README_EOF

git add banking/notebooks/README.md
```

---

## 🔍 VALIDATION (10 minutes)

Run all validation scripts to confirm fixes:

```bash
# 1. Python environment check
./scripts/validation/check_python_env.sh

# 2. Preflight checks
./scripts/validation/preflight_check.sh

# 3. Podman isolation check (after deployment)
./scripts/validation/validate_podman_isolation.sh

# 4. Run quick test
pytest tests/ -v --maxfail=1
```

**Expected Results:**
- ✅ All validation scripts pass
- ✅ Python 3.11 in conda env
- ✅ Podman resources have project prefix
- ✅ Tests run successfully

---

## 💾 COMMIT PHASE 1 FIXES

```bash
# Stage Python environment fixes
git add scripts/validation/check_python_env.sh
git add scripts/validation/preflight_check.sh
git commit -m "fix: Add Python environment validation scripts

- Add check_python_env.sh to enforce Python 3.11 + conda
- Add preflight_check.sh for deployment readiness
- Remove .venv directory (use conda only)

Resolves critical Python environment mismatch.

Co-Authored-By: David Leconte <david.leconte1@ibm.com>"

# Stage Podman isolation fixes
git add scripts/validation/validate_podman_isolation.sh
git add .env
git commit -m "fix: Enforce Podman project isolation

- Add validate_podman_isolation.sh
- Add COMPOSE_PROJECT_NAME to .env
- Ensure container/network/volume isolation

Resolves critical Podman isolation issue.

Co-Authored-By: David Leconte <david.leconte1@ibm.com>"

# Stage notebooks reorganization
git add notebooks-exploratory/
git add scripts/utilities/
git add banking/notebooks/README.md
git commit -m "refactor: Reorganize notebooks directories

- Rename notebooks/ → notebooks-exploratory/
- Rename scripts/notebooks/ → scripts/utilities/
- Add README.md to notebooks directories
- Remove empty scripts/deployment/notebooks/

Resolves confusion from multiple 'notebooks' directories.

Co-Authored-By: David Leconte <david.leconte1@ibm.com>"
```

---

## 📋 PHASE 2: MAJOR FIXES (Next 1-2 days)

### Quick Reference

- [ ] **5. Add Dependency Version Locking**
- [ ] **6. Update AGENTS.md Documentation**
- [ ] **7. Fix Test Execution Scripts**
- [ ] **8. Update Deployment Scripts**

**See [Detailed Remediation Plan](docs/implementation/audits/REMEDIATION_PLAN_2026-01-30.md) for complete instructions.**

---

## 📋 PHASE 3: MINOR IMPROVEMENTS (Next week)

```bash
# Quick wins - run all at once
echo "3.11" > .python-version

cat > .envrc << 'ENVRC_EOF'
source_up
layout anaconda janusgraph-analysis
ENVRC_EOF

cat > .editorconfig << 'EDITOR_EOF'
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
EDITOR_EOF

cat > .gitattributes << 'GITATTR_EOF'
* text=auto eol=lf
*.py text eol=lf
*.sh text eol=lf
*.md text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.json text eol=lf
GITATTR_EOF

# Commit all together
git add .python-version .envrc .editorconfig .gitattributes
git commit -m "chore: Add development environment config files

- Add .python-version for pyenv
- Add .envrc for direnv auto-activation
- Add .editorconfig for consistent formatting
- Add .gitattributes for line ending consistency

Co-Authored-By: David Leconte <david.leconte1@ibm.com>"
```

---

## 🎯 SUCCESS CRITERIA

Phase 1 is complete when:

- ✅ `./scripts/validation/check_python_env.sh` passes
- ✅ `./scripts/validation/preflight_check.sh` passes
- ✅ `./scripts/validation/validate_podman_isolation.sh` shows project prefixes
- ✅ `pytest tests/ -v` runs successfully
- ✅ No .venv directory exists
- ✅ Notebooks directories renamed
- ✅ All changes committed to git

---

## ⚠️ TROUBLESHOOTING

### Python Environment Issues

```bash
# If conda environment doesn't exist
conda create -n janusgraph-analysis python=3.11
conda activate janusgraph-analysis

# If dependencies fail to install
pip install --upgrade pip
pip cache purge
pip install -r requirements.txt
```

### Podman Issues

```bash
# If podman-compose not found
pip install podman-compose

# If containers fail to start
podman system prune -a -f
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml down -v
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d
```

### Git Issues

```bash
# If git mv fails (files modified)
git stash
git mv notebooks notebooks-exploratory
git mv scripts/notebooks scripts/utilities
git stash pop
```

---

## 📞 NEED HELP?

- **Full Audit Report**: [docs/implementation/audits/COMPREHENSIVE_PROJECT_AUDIT_2026-01-30.md](docs/implementation/audits/COMPREHENSIVE_PROJECT_AUDIT_2026-01-30.md)
- **Detailed Instructions**: [docs/implementation/audits/REMEDIATION_PLAN_2026-01-30.md](docs/implementation/audits/REMEDIATION_PLAN_2026-01-30.md)
- **AGENTS.md**: Project guidance (needs updates after Phase 1)

---

## ⏱️ TIME ESTIMATES

- **Phase 1 (Critical)**: 2-3 hours
- **Phase 2 (Major)**: 1-2 days
- **Phase 3 (Minor)**: 2-3 hours
- **Total**: 2-3 days for production-ready state

---

**Status:** Ready to execute Phase 1 immediately ✅
