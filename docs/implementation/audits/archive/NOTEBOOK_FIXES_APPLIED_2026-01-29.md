# Notebook Fixes Applied - 2026-01-29

**Status:** COMPLETED  
**Fixed Notebooks:** 4/6 Banking notebooks  
**Remaining Issues:** 1 notebook (JSON corruption)

---

## Fixes Applied

### 1. Infrastructure Fixes ✅

#### Jupyter Dockerfile Update
**File:** `docker/jupyter/Dockerfile`

**Change:** Added PYTHONPATH environment variable

```dockerfile
# CRITICAL: Set PYTHONPATH for banking modules (fixes notebook imports)
ENV PYTHONPATH="/workspace:/workspace/banking:/workspace/src/python:$PYTHONPATH"
```

**Impact:** Banking modules now importable from notebooks without manual path manipulation

#### Environment.yml Update
**File:** `docker/jupyter/environment.yml`

**Changes:** Added missing dependencies

```yaml
- opensearch-py>=2.7.1  # OpenSearch client (for banking demos)
- sentence-transformers>=2.2.0  # Text embeddings (for sanctions screening)
- faker>=20.0.0  # Fake data generation (for demos)
```

**Impact:** All required packages now available in Jupyter container

### 2. Notebook Fixes ✅

#### Fix Script Created
**File:** `scripts/notebooks/fix_banking_notebooks.py`

**Functionality:**
- Automatically fixes connection strings (localhost → container names)
- Fixes import paths (../../ → /workspace/)
- Creates backups before modification
- Reports changes made

#### Notebooks Fixed (4/6)

1. **01_Sanctions_Screening_Demo.ipynb** ✅
   - Fixed: Connection strings (opensearch)
   - Fixed: Import paths

2. **02_AML_Structuring_Detection_Demo.ipynb** ✅
   - Fixed: Connection strings (janusgraph-server)
   - Fixed: Import paths

3. **03_Fraud_Detection_Demo.ipynb** ✅
   - Fixed: Connection strings
   - Fixed: Import paths

4. **04_Customer_360_View_Demo.ipynb** ✅
   - Fixed: Connection strings
   - Fixed: Import paths

#### Notebooks Unchanged

5. **01_AML_Structuring_Analysis.ipynb** ℹ️
   - Already correct (no changes needed)

#### Notebooks With Errors

6. **05_Advanced_Analytics_OLAP.ipynb** ❌
   - Error: JSON corruption (line 886)
   - Action required: Manual fix or regeneration

---

## Data Generators Status ✅

### Existing Generators Found

**Location:** `banking/data/aml/`

**Files:**
- `generate_structuring_data.py` (477 lines) - Generates AML structuring patterns
- `load_structuring_data.py` (14KB) - Loads data into JanusGraph
- `load_structuring_data_v2.py` (9KB) - Updated loader

### Generated Data Files ✅

**Location:** `banking/data/aml/`

**Files:**
- `aml_data_accounts.csv` (9KB, 62 accounts)
- `aml_data_addresses.csv` (7KB, 62 addresses)
- `aml_data_persons.csv` (5KB, 62 persons)
- `aml_data_phones.csv` (3KB, 62 phone numbers)
- `aml_data_transactions.csv` (111KB, 778 transactions)
- `aml_structuring_data.json` (462KB, all data in JSON)

**Status:** All data files already generated and available

**Note:** No additional data generation needed - existing files sufficient for demos

---

## Changes Summary

### Connection String Fixes

**Before:**
```python
# WRONG - Won't work in container
opensearch_host='localhost'
janusgraph_host='localhost'
```

**After:**
```python
# CORRECT - Uses container names
opensearch_host='opensearch'
janusgraph_host='janusgraph-server'
```

### Import Path Fixes

**Before:**
```python
# WRONG - Wrong from container /workspace/notebooks
sys.path.insert(0, '../../src/python')
sys.path.insert(0, '../../banking')
```

**After:**
```python
# CORRECT - Container absolute paths
sys.path.insert(0, '/workspace/src/python')
sys.path.insert(0, '/workspace/banking')
```

**Note:** With PYTHONPATH fix in Dockerfile, these explicit inserts are now optional

---

## Next Steps

### Immediate Actions (Required)

1. **Rebuild Jupyter Container**
   ```bash
   cd config/compose
   podman-compose -p janusgraph-demo build jupyter
   podman-compose -p janusgraph-demo restart jupyter
   ```

   **Why:** Apply PYTHONPATH and dependency changes

2. **Fix Corrupted Notebook**
   ```bash
   # Check JSON error
   python3 -m json.tool banking/notebooks/05_Advanced_Analytics_OLAP.ipynb > /dev/null
   
   # If unfixable, consider:
   # - Manual edit to fix JSON
   # - Restore from git history
   # - Regenerate from template
   ```

### Testing (After Rebuild)

1. **Test Fixed Notebooks**
   - Open Jupyter Lab: http://localhost:8888
   - Test each banking notebook
   - Verify imports work
   - Verify connections work

2. **Verify Services Running**
   ```bash
   podman ps | grep janusgraph-demo_
   
   # Should show:
   # - janusgraph-demo_jupyter-lab_1
   # - janusgraph-demo_janusgraph-server_1
   # - janusgraph-demo_opensearch_1
   # - etc.
   ```

3. **Test Data Availability**
   ```python
   # In Jupyter
   import pandas as pd
   df = pd.read_csv('/workspace/banking/data/aml/aml_data_transactions.csv')
   print(f"Loaded {len(df)} transactions")
   ```

### Optional Improvements

1. **Add Prerequisites Cell**
   - Template available in audit report
   - Checks service connectivity
   - Validates dependencies

2. **Add Error Handling**
   - Wrap connections in try/except
   - Provide helpful error messages

3. **Update Documentation**
   - Add setup instructions to each notebook
   - Document prerequisites

---

## Verification Checklist

After rebuilding Jupyter container:

- [ ] Jupyter container running
- [ ] Banking notebooks load without import errors
- [ ] OpenSearch connection works (for sanctions screening)
- [ ] JanusGraph connection works (for AML structuring)
- [ ] Data files accessible from notebooks
- [ ] All dependencies available (`sentence-transformers`, `faker`, etc.)

---

## Files Modified

1. **Infrastructure:**
   - `docker/jupyter/Dockerfile` - Added PYTHONPATH
   - `docker/jupyter/environment.yml` - Added dependencies

2. **Scripts:**
   - `scripts/notebooks/fix_banking_notebooks.py` - Created (157 lines)

3. **Notebooks (with backups):**
   - `banking/notebooks/01_Sanctions_Screening_Demo.ipynb`
   - `banking/notebooks/02_AML_Structuring_Detection_Demo.ipynb`
   - `banking/notebooks/03_Fraud_Detection_Demo.ipynb`
   - `banking/notebooks/04_Customer_360_View_Demo.ipynb`

4. **Documentation:**
   - `docs/implementation/audits/NOTEBOOKS_AUDIT_2026-01-29.md` - Created
   - `docs/implementation/audits/NOTEBOOK_FIXES_APPLIED_2026-01-29.md` - This file

---

## Related Documentation

- [Full Audit Report](NOTEBOOKS_AUDIT_2026-01-29.md)
- `docker/jupyter/Dockerfile`
- `docker/jupyter/environment.yml`
- `banking/data/aml/`

---

## Success Metrics

**Before Fixes:**
- Working notebooks: 1/10 (10%)
- Broken notebooks: 6/10 (60%)

**After Fixes:**
- Working notebooks: 5/10 (50%) - after rebuild
- Broken notebooks: 1/10 (10%)
- Ready for testing: 4/10 (40%)

**Target (After Testing):**
- Working notebooks: 9/10 (90%)
- Broken notebooks: 0/10 (0%)

---

**Fix Status:** APPLIED (awaiting container rebuild)  
**Testing Status:** PENDING  
**Production Ready:** After successful testing
