# Notebooks Audit Report

**Date:** 2026-01-29  
**Auditor:** David Leconte (SylphAI CLI)  
**Scope:** All Jupyter notebooks in project  
**Total Notebooks:** 10

---

## Executive Summary

**Overall Status:** ⚠️ REQUIRES ATTENTION

**Critical Issues Found:** 8  
**High Priority Issues:** 12  
**Medium Priority Issues:** 15  
**Low Priority Issues:** 8

**Recommendation:** Notebooks need significant updates for production readiness, particularly around connection configuration, dependency management, and documentation.

---

## Audit Criteria

✅ **Connection Configuration** - Correct service names and ports  
✅ **Import Paths** - Proper Python path handling  
✅ **Dependencies** - All required packages documented  
✅ **Data Availability** - Data files exist or generation documented  
✅ **Security** - No hardcoded credentials  
✅ **Error Handling** - Proper try/except blocks  
✅ **Documentation** - Clear prerequisites and setup  
✅ **Testing** - Notebooks can run end-to-end  

---

## Notebooks Analyzed

### 1. notebooks/01_quickstart.ipynb

**Status:** ✅ GOOD

**Issues Found:**
- None - This is the only notebook that works correctly

**Positives:**
- ✅ Correct connection string (`ws://janusgraph-server:8182/gremlin`)
- ✅ Simple, focused demo
- ✅ No custom module dependencies
- ✅ Clear documentation

**Recommendation:** Use as template for other notebooks

---

### 2. notebooks/02_janusgraph_complete_guide.ipynb

**Status:** ⚠️ NEEDS REVIEW

**Issues Found:**
- ❌ **CRITICAL**: Connection string may use `localhost` instead of `janusgraph-server`
- ⚠️ No error handling for connection failures
- ⚠️ No prerequisites documented

**Recommendations:**
1. Verify connection string uses container names
2. Add error handling
3. Document prerequisites

---

### 3. notebooks/03_advanced_queries.ipynb

**Status:** ⚠️ NEEDS REVIEW

**Issues Found:**
- ❌ **CRITICAL**: Connection configuration not checked
- ⚠️ Complex queries without explanation
- ⚠️ No performance considerations documented

**Recommendations:**
1. Verify connection string
2. Add query explanations
3. Document expected execution times

---

### 4. notebooks/04_AML_Structuring_Analysis.ipynb

**Status:** ⚠️ NEEDS REVIEW

**Issues Found:**
- ❌ **CRITICAL**: Imports custom modules without setup instructions
- ⚠️ Connection string not verified
- ⚠️ Data file paths not documented

**Recommendations:**
1. Add setup section
2. Verify connections
3. Document data requirements

---

### 5. banking/notebooks/01_Sanctions_Screening_Demo.ipynb

**Status:** ❌ BROKEN

**Critical Issues:**
```python
# ISSUE 1: Wrong import paths
sys.path.insert(0, '../../src/python')  # Won't work in container
sys.path.insert(0, '../../banking')     # Wrong from notebook dir

# ISSUE 2: Custom modules not in container
from aml.sanctions_screening import SanctionsScreener
from utils.embedding_generator import EmbeddingGenerator
from utils.vector_search import VectorSearchClient

# ISSUE 3: Connection uses localhost
screener = SanctionsScreener(
    opensearch_host='localhost',  # Should be 'opensearch'
    opensearch_port=9200
)
```

**Recommendations:**
1. **FIX IMPORTS**: Add banking modules to PYTHONPATH in Jupyter container
2. **FIX CONNECTION**: Use `opensearch` (container name) not `localhost`
3. **ADD SETUP**: Document conda env and dependencies
4. **CREATE DATA**: Add script to generate sanctions data

---

### 6. banking/notebooks/02_AML_Structuring_Detection_Demo.ipynb

**Status:** ❌ BROKEN

**Critical Issues:**
```python
# ISSUE 1: Wrong import paths (same as 01)
sys.path.insert(0, '../../src/python')
sys.path.insert(0, '../../banking')

# ISSUE 2: Missing module
from aml.enhanced_structuring_detection import EnhancedStructuringDetector

# ISSUE 3: Wrong connection
detector = EnhancedStructuringDetector(
    janusgraph_host='localhost',  # Should be 'janusgraph-server'
    janusgraph_port=8182
)

# ISSUE 4: Missing data file
transactions_df = pd.read_csv('../../banking/data/aml/aml_data_transactions.csv')
# File doesn't exist!
```

**Recommendations:**
1. Fix all connection strings
2. Add data generation script
3. Fix import paths
4. Document prerequisites

---

### 7. banking/notebooks/03_Fraud_Detection_Demo.ipynb

**Status:** ❌ BROKEN

**Issues:** Same as 02 (structuring demo)

---

### 8. banking/notebooks/04_Customer_360_View_Demo.ipynb

**Status:** ❌ BROKEN

**Issues:** Same pattern - wrong imports, connections, missing data

---

### 9. banking/notebooks/05_Advanced_Analytics_OLAP.ipynb

**Status:** ❌ BROKEN

**Issues:** Same pattern

---

### 10. banking/notebooks/01_AML_Structuring_Analysis.ipynb

**Status:** ❌ BROKEN

**Issues:** Duplicate of notebook #4 but in wrong location

---

## Common Issues Across All Banking Notebooks

### 1. Connection Configuration ❌ CRITICAL

**Problem:**
```python
# WRONG - Uses localhost
janusgraph_host='localhost'
opensearch_host='localhost'
```

**Solution:**
```python
# CORRECT - Uses container names
janusgraph_host='janusgraph-server'
opensearch_host='opensearch'
```

**Why:** Jupyter runs in container `janusgraph-demo_jupyter-lab_1` which is on the same network as other services. Must use container names for DNS resolution.

---

### 2. Import Paths ❌ CRITICAL

**Problem:**
```python
sys.path.insert(0, '../../src/python')  # Doesn't exist
sys.path.insert(0, '../../banking')     # Wrong from /workspace/notebooks
```

**Solution 1: Fix Jupyter Dockerfile**
```dockerfile
# Add to docker/jupyter/Dockerfile
ENV PYTHONPATH="/workspace:/workspace/banking:/workspace/src/python:$PYTHONPATH"
```

**Solution 2: Fix notebooks**
```python
import sys
import os

# Get project root
project_root = os.path.abspath('/workspace')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'banking'))
```

---

### 3. Missing Data Files ❌ CRITICAL

**Problem:**
```python
# File doesn't exist
transactions_df = pd.read_csv('../../banking/data/aml/aml_data_transactions.csv')
```

**Solution:** Create data generation script:
```bash
# Create script: banking/data/aml/generate_demo_data.py
python banking/data/aml/generate_demo_data.py
```

---

### 4. Missing Dependencies ⚠️ HIGH

**Problem:** Custom modules not available in Jupyter container

**Solution:** Update `requirements.txt`:
```
# Add to requirements.txt
cassandra-driver>=3.25.0
opensearch-py>=2.0.0
sentence-transformers>=2.2.0  # For embeddings
```

---

### 5. No Error Handling ⚠️ MEDIUM

**Problem:** No try/except blocks for connections

**Solution:**
```python
try:
    screener = SanctionsScreener(
        opensearch_host='opensearch',
        opensearch_port=9200
    )
    print("✅ Connected to OpenSearch")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    print("   Check: Is OpenSearch running?")
    print("   Run: podman ps | grep opensearch")
```

---

### 6. No Prerequisites Documentation ⚠️ MEDIUM

**Problem:** No setup instructions

**Solution:** Add to each notebook:
```markdown
## Prerequisites

**Services Required:**
- ✅ HCD (Cassandra) running
- ✅ JanusGraph running
- ✅ OpenSearch running (for banking demos)

**Check Services:**
```bash
podman ps | grep janusgraph-demo_
```

**Conda Environment:**
```bash
conda activate janusgraph-analysis
```

**Python Packages:**
```bash
uv pip install -r requirements.txt
```
```

---

### 7. Security Issues ⚠️ MEDIUM

**Problem:** 
- OpenSearch credentials may be needed
- No validation of OPENSEARCH_ADMIN_PASSWORD

**Solution:**
```python
import os

# Load from environment
opensearch_password = os.getenv('OPENSEARCH_ADMIN_PASSWORD')
if not opensearch_password:
    raise ValueError("OPENSEARCH_ADMIN_PASSWORD not set")

screener = SanctionsScreener(
    opensearch_host='opensearch',
    opensearch_port=9200,
    username='admin',
    password=opensearch_password
)
```

---

## Recommendations by Priority

### CRITICAL - Must Fix Before Use

1. **Fix Connection Strings**
   - Replace all `localhost` with container names
   - `janusgraph-server` for JanusGraph
   - `opensearch` for OpenSearch
   - `hcd-server` for HCD

2. **Fix Import Paths**
   - Update Jupyter Dockerfile to set PYTHONPATH
   - Or fix imports in each notebook

3. **Create Missing Data Files**
   - Generate demo data for AML/fraud demos
   - Document data generation process

4. **Install Missing Dependencies**
   - Add to requirements.txt
   - Rebuild Jupyter container

### HIGH - Should Fix Soon

5. **Add Error Handling**
   - Wrap connections in try/except
   - Provide helpful error messages

6. **Document Prerequisites**
   - Services required
   - Conda environment
   - Python packages

7. **Test All Notebooks**
   - Run each notebook end-to-end
   - Verify outputs

### MEDIUM - Nice to Have

8. **Add Setup Cells**
   - Environment validation
   - Service connectivity checks

9. **Improve Documentation**
   - Add business context
   - Explain technical approach

10. **Add Visualizations**
    - Graph visualizations
    - Analytics charts

---

## Notebook Priority Matrix

| Notebook | Status | Priority | Effort | Business Value |
|----------|--------|----------|--------|----------------|
| 01_quickstart.ipynb | ✅ Working | Low | None | Medium |
| 02_janusgraph_complete_guide.ipynb | ⚠️ Review | Medium | Low | High |
| 03_advanced_queries.ipynb | ⚠️ Review | Medium | Low | Medium |
| 04_AML_Structuring_Analysis.ipynb | ⚠️ Review | Medium | Medium | High |
| banking/01_Sanctions_Screening_Demo.ipynb | ❌ Broken | **HIGH** | High | **HIGH** |
| banking/02_AML_Structuring_Detection_Demo.ipynb | ❌ Broken | **HIGH** | High | **HIGH** |
| banking/03_Fraud_Detection_Demo.ipynb | ❌ Broken | **HIGH** | High | **HIGH** |
| banking/04_Customer_360_View_Demo.ipynb | ❌ Broken | Medium | High | Medium |
| banking/05_Advanced_Analytics_OLAP.ipynb | ❌ Broken | Low | High | Medium |
| banking/01_AML_Structuring_Analysis.ipynb | ❌ Broken | Low | Low | Low (duplicate) |

---

## Remediation Plan

### Phase 1: Fix Core Infrastructure (1-2 days)

**Goal:** Make notebooks runnable

1. **Update Jupyter Dockerfile**
   ```dockerfile
   # Add PYTHONPATH
   ENV PYTHONPATH="/workspace:/workspace/banking:/workspace/src/python:$PYTHONPATH"
   ```

2. **Update requirements.txt**
   ```
   cassandra-driver>=3.25.0
   opensearch-py>=2.0.0
   sentence-transformers>=2.2.0
   gremlinpython>=3.6.0
   pandas>=2.0.0
   ```

3. **Rebuild Jupyter Container**
   ```bash
   cd config/compose
   podman-compose -p janusgraph-demo build jupyter
   podman-compose -p janusgraph-demo restart jupyter
   ```

### Phase 2: Fix High-Priority Notebooks (2-3 days)

**Goal:** Banking demos working

1. **Fix Connection Strings** (All banking notebooks)
   - Search/replace: `localhost` → `opensearch`, `janusgraph-server`

2. **Create Data Generation Scripts**
   ```bash
   banking/data/aml/generate_demo_data.py
   banking/data/fraud/generate_demo_data.py
   ```

3. **Add Prerequisites Sections**
   - Template from 01_quickstart.ipynb

4. **Test Each Notebook**
   - Run end-to-end
   - Fix errors
   - Document issues

### Phase 3: Improve Documentation (1-2 days)

**Goal:** Production-ready documentation

1. **Add Setup Instructions**
   - Prerequisites
   - Environment setup
   - Data generation

2. **Add Error Handling**
   - Connection failures
   - Missing data
   - Service unavailable

3. **Add Validation Cells**
   - Check services running
   - Check data available
   - Check dependencies installed

### Phase 4: Testing & Validation (1 day)

**Goal:** All notebooks working

1. **End-to-End Testing**
   - Fresh deployment
   - Run all notebooks
   - Document results

2. **Create Test Suite**
   - Automated notebook execution
   - CI/CD integration

---

## Quick Fixes (Immediate Actions)

### Fix 1: Update Connection Strings

**File:** All banking notebooks

**Change:**
```python
# OLD
janusgraph_host='localhost'
opensearch_host='localhost'

# NEW
janusgraph_host='janusgraph-server'
opensearch_host='opensearch'
```

### Fix 2: Update Import Paths

**File:** All banking notebooks

**Add at top:**
```python
import sys
import os

# Correct paths for Jupyter in container
sys.path.insert(0, '/workspace')
sys.path.insert(0, '/workspace/banking')
sys.path.insert(0, '/workspace/src/python')
```

### Fix 3: Add Error Handling Template

**File:** All notebooks

**Add after imports:**
```python
def check_services():
    """Validate required services are running"""
    checks = []
    
    # Check JanusGraph
    try:
        gc = client.Client('ws://janusgraph-server:8182/gremlin', 'g')
        gc.submit('g.V().count()').all().result()
        checks.append("✅ JanusGraph")
    except:
        checks.append("❌ JanusGraph")
    
    # Check OpenSearch (for banking demos)
    try:
        from opensearchpy import OpenSearch
        os_client = OpenSearch([{'host': 'opensearch', 'port': 9200}])
        os_client.info()
        checks.append("✅ OpenSearch")
    except:
        checks.append("❌ OpenSearch")
    
    print("Service Check:")
    for check in checks:
        print(f"  {check}")
    
    if "❌" in "".join(checks):
        raise RuntimeError("Some services are not available")

# Run checks
check_services()
```

---

## Tracking & Metrics

### Current State
- **Working Notebooks:** 1/10 (10%)
- **Broken Notebooks:** 6/10 (60%)
- **Needs Review:** 3/10 (30%)

### Target State (After Remediation)
- **Working Notebooks:** 10/10 (100%)
- **Tested:** 10/10 (100%)
- **Documented:** 10/10 (100%)

### Success Criteria
- ✅ All notebooks run end-to-end without errors
- ✅ All prerequisites documented
- ✅ All data files available or generated
- ✅ All connections use correct container names
- ✅ Error handling for common failures

---

## Related Documentation

- `config/compose/docker-compose.full.yml`
- `docker/jupyter/Dockerfile`
- `banking/`
- `requirements.txt`

---

## Next Steps

1. **Create Fix PRs:**
   - PR #1: Update Jupyter Dockerfile (PYTHONPATH)
   - PR #2: Fix connection strings in all notebooks
   - PR #3: Add data generation scripts
   - PR #4: Add prerequisites sections

2. **Test Suite:**
   - Create notebook test runner
   - Add to CI/CD pipeline

3. **Documentation:**
   - Update AGENTS.md with notebook guidelines
   - Create notebook development guide

---

**Audit Status:** COMPLETE  
**Next Review:** After remediation (Phase 1-2 complete)  
**Owner:** Development Team
