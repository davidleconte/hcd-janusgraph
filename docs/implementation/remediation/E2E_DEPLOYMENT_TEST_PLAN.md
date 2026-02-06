# End-to-End Deployment Test Plan

**Date:** 2026-01-29  
**Purpose:** Verify all script fixes work correctly in practice  
**Scope:** Complete deployment workflow validation  
**Status:** 🔄 In Progress

---

## Test Objectives

1. ✅ Verify all fixed scripts execute without errors
2. ✅ Validate security improvements (no JMX exposure, secure credentials)
3. ✅ Confirm backup/restore workflow with new naming convention
4. ✅ Test cleanup script safety measures
5. ✅ Validate data initialization with new data_script
6. ✅ Verify Jupyter notebook environment
7. ✅ Test complete stack deployment and health

---

## Pre-Test Checklist

### Environment Requirements
- [ ] Podman/Docker installed and running
- [ ] Conda environment `janusgraph-analysis` available
- [ ] Python 3.11+ installed
- [ ] Sufficient disk space (10GB+)
- [ ] Ports available: 8182, 9042, 9200, 8200, 9090, 3001, 8888

### Backup Current State
```bash
# Backup any existing data
mkdir -p ~/backup-before-test
podman volume ls | grep janusgraph > ~/backup-before-test/volumes.txt
podman ps -a > ~/backup-before-test/containers.txt
```

---

## Test Suite

### Test 1: Cleanup Script Safety ✅

**Objective:** Verify cleanup script requires confirmation and only removes project resources

**Steps:**
```bash
# 1. Test cancellation
./scripts/utils/cleanup_podman.sh
# Type anything except "DELETE" - should cancel

# 2. Create test container outside project
podman run -d --name test-external-container alpine sleep 3600

# 3. Run cleanup with confirmation
./scripts/utils/cleanup_podman.sh
# Type "DELETE" - should only remove project containers

# 4. Verify external container still exists
podman ps | grep test-external-container
# Should still be running

# 5. Cleanup test container
podman rm -f test-external-container
```

**Expected Results:**
- ✅ Script requires "DELETE" confirmation
- ✅ Only project-prefixed resources removed
- ✅ External containers preserved
- ✅ Clear warning messages displayed

**Status:** [ ] Pass [ ] Fail [ ] Not Run

---

### Test 2: Full Stack Deployment ✅

**Objective:** Verify deployment script works without JMX port exposure

**Steps:**
```bash
# 1. Deploy full stack
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# 2. Wait for services
sleep 90

# 3. Check service status
podman ps

# 4. Verify JMX port NOT exposed
podman ps | grep hcd-server | grep 7199
# Should return nothing (no JMX port mapping)

# 5. Check JanusGraph connectivity
curl -s http://localhost:8182?gremlin=g.V().count()

# 6. Check HCD connectivity
podman exec hcd-server nodetool status
```

**Expected Results:**
- ✅ All services start successfully
- ✅ No JMX port 7199 exposed externally
- ✅ JanusGraph responds on port 8182
- ✅ HCD cluster healthy
- ✅ No deployment errors in logs

**Status:** [ ] Pass [ ] Fail [ ] Not Run

**Verification Commands:**
```bash
# Check all expected services
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected services:
# - janusgraph-server
# - hcd-server
# - opensearch-node
# - vault-server
# - prometheus
# - grafana
# - alertmanager
```

---

### Test 3: Vault Initialization with Secure Credentials ✅

**Objective:** Verify Vault credentials are logged to file, not stdout

**Steps:**
```bash
# 1. Initialize Vault
./scripts/security/init_vault.sh 2>&1 | tee /tmp/vault-init-output.txt

# 2. Check stdout does NOT contain tokens
grep -i "root token" /tmp/vault-init-output.txt
# Should show "CREDENTIALS NOT DISPLAYED"

grep -i "app token" /tmp/vault-init-output.txt
# Should show "CREDENTIALS NOT DISPLAYED"

# 3. Verify credentials file exists
ls -la .vault-credentials.log
# Should exist with 400 permissions

# 4. Verify credentials are in file
cat .vault-credentials.log | grep "Root Token"
# Should show actual token

# 5. Test Vault access
source ./scripts/security/vault_access.sh
vault kv get janusgraph/admin
```

**Expected Results:**
- ✅ No tokens/passwords in stdout
- ✅ Credentials file created with 400 permissions
- ✅ All credentials present in log file
- ✅ Vault access works with tokens from file
- ✅ Clear instructions for securing credentials

**Status:** [ ] Pass [ ] Fail [ ] Not Run

---

### Test 4: Data Initialization ✅

**Objective:** Verify initialize_graph.py works with new data_script

**Steps:**
```bash
# 1. Activate conda environment
conda activate janusgraph-analysis

# 2. Test import
python -c "from src.python.init.initialize_graph import load_sample_data; print('Import OK')"

# 3. Run initialization (if services running)
python -c "
from src.python.client import JanusGraphClient
from src.python.init.initialize_graph import initialize_schema, load_sample_data

client = JanusGraphClient('ws://localhost:8182/gremlin')
client.connect()
print('Schema init:', initialize_schema(client))
print('Data load:', load_sample_data(client))
client.close()
"

# 4. Verify data loaded
curl -s "http://localhost:8182?gremlin=g.V().count()" | jq .
# Should show vertices created
```

**Expected Results:**
- ✅ No NameError for data_script
- ✅ Schema initializes successfully
- ✅ Sample data loads without errors
- ✅ Vertices and edges created in graph

**Status:** [ ] Pass [ ] Fail [ ] Not Run

---

### Test 5: Jupyter Notebook Environment ✅

**Objective:** Verify start_jupyter.sh works with fixed paths

**Steps:**
```bash
# 1. Start Jupyter
./scripts/deployment/start_jupyter.sh

# 2. Check container status
podman ps | grep jupyter

# 3. Verify volume mounts
podman inspect jupyter-notebook | jq '.[0].Mounts'
# Should show correct PROJECT_ROOT paths

# 4. Access Jupyter
# Open browser to http://localhost:8888
# Check if notebooks directory is accessible

# 5. Test notebook execution
# Open any notebook and run first cell
```

**Expected Results:**
- ✅ No syntax errors during startup
- ✅ Container starts successfully
- ✅ Volume mounts use correct paths
- ✅ Notebooks accessible and executable
- ✅ Can import banking modules

**Status:** [ ] Pass [ ] Fail [ ] Not Run

---

### Test 6: Backup and Restore Workflow ✅

**Objective:** Verify backup/restore with aligned naming convention

**Steps:**
```bash
# 1. Create test data
curl -X POST "http://localhost:8182" \
  -H "Content-Type: application/json" \
  -d '{"gremlin":"g.addV(\"test\").property(\"name\",\"backup-test\")"}'

# 2. Run backup
./scripts/backup/backup_volumes.sh

# 3. Check backup files created
ls -lh /backups/janusgraph/
# Should show hcd_TIMESTAMP and janusgraph_TIMESTAMP.tar.gz

# 4. Get timestamp from backup
TIMESTAMP=$(ls /backups/janusgraph/ | grep hcd_ | head -1 | sed 's/hcd_//')

# 5. Test restore (in test environment)
./scripts/backup/restore_volumes.sh /backups/janusgraph $TIMESTAMP

# 6. Verify data restored
curl -s "http://localhost:8182?gremlin=g.V().has('name','backup-test').count()"
```

**Expected Results:**
- ✅ Backup creates timestamped files
- ✅ Restore accepts directory and timestamp parameters
- ✅ Restore finds correct backup files
- ✅ No manual file renaming required
- ✅ Data successfully restored

**Status:** [ ] Pass [ ] Fail [ ] Not Run

---

### Test 7: Monitoring Stack ✅

**Objective:** Verify monitoring services are healthy

**Steps:**
```bash
# 1. Check Prometheus
curl -s http://localhost:9090/-/healthy
# Should return "Prometheus is Healthy"

# 2. Check Grafana
curl -s http://localhost:3001/api/health
# Should return {"database":"ok"}

# 3. Check AlertManager
curl -s http://localhost:9093/-/healthy
# Should return "OK"

# 4. Check JanusGraph exporter
curl -s http://localhost:9091/metrics | grep janusgraph
# Should show metrics

# 5. Verify alerts loaded
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[].name'
# Should show 31 alert rules
```

**Expected Results:**
- ✅ All monitoring services healthy
- ✅ Metrics being collected
- ✅ Alert rules loaded
- ✅ Dashboards accessible

**Status:** [ ] Pass [ ] Fail [ ] Not Run

---

### Test 8: Security Validation ✅

**Objective:** Verify security improvements are in place

**Steps:**
```bash
# 1. Verify no JMX port exposure
netstat -an | grep 7199
# Should show nothing or only localhost binding

# 2. Check SSL/TLS certificates exist
ls -la config/ssl/
# Should show certificates

# 3. Verify Vault sealed status
podman exec vault-server vault status
# Should show "Sealed: false"

# 4. Check audit logging enabled
ls -la logs/audit/
# Should show audit log files

# 5. Verify no default passwords in running config
podman exec janusgraph-server env | grep PASSWORD
# Should show environment variables (check if changed from defaults)
```

**Expected Results:**
- ✅ JMX not accessible externally
- ✅ SSL certificates present
- ✅ Vault unsealed and accessible
- ✅ Audit logging active
- ⚠️ Default passwords still present (known issue)

**Status:** [ ] Pass [ ] Fail [ ] Not Run

---

### Test 9: Integration Tests ✅

**Objective:** Run automated test suite

**Steps:**
```bash
# 1. Activate conda environment
conda activate janusgraph-analysis

# 2. Run data generator tests
cd banking/data_generators/tests
./run_tests.sh smoke

# 3. Run unit tests
cd ../../..
pytest tests/unit/ -v

# 4. Run integration tests (if services running)
pytest tests/integration/ -v

# 5. Check coverage
pytest --cov=src --cov=banking --cov-report=term-missing
```

**Expected Results:**
- ✅ Smoke tests pass
- ✅ Unit tests pass (170+ tests)
- ✅ Integration tests pass
- ✅ Coverage ≥82%

**Status:** [ ] Pass [ ] Fail [ ] Not Run

---

### Test 10: End-to-End Workflow ✅

**Objective:** Complete workflow from deployment to query

**Steps:**
```bash
# 1. Clean environment
./scripts/utils/cleanup_podman.sh
# Type "DELETE"

# 2. Deploy full stack
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# 3. Wait for services
sleep 90

# 4. Initialize Vault
cd ../..
./scripts/security/init_vault.sh

# 5. Initialize graph
conda activate janusgraph-analysis
python -c "
from src.python.client import JanusGraphClient
from src.python.init.initialize_graph import initialize_schema, load_sample_data
client = JanusGraphClient('ws://localhost:8182/gremlin')
client.connect()
initialize_schema(client)
load_sample_data(client)
client.close()
"

# 6. Run sample query
curl -X POST "http://localhost:8182" \
  -H "Content-Type: application/json" \
  -d '{"gremlin":"g.V().hasLabel(\"person\").values(\"name\")"}'

# 7. Check monitoring
curl -s http://localhost:9090/api/v1/query?query=janusgraph_vertices_total

# 8. Create backup
./scripts/backup/backup_volumes.sh
```

**Expected Results:**
- ✅ Complete workflow executes without errors
- ✅ All services healthy
- ✅ Data queryable
- ✅ Monitoring active
- ✅ Backup successful

**Status:** [ ] Pass [ ] Fail [ ] Not Run

---

## Test Results Summary

| Test | Status | Duration | Issues |
|------|--------|----------|--------|
| 1. Cleanup Safety | [ ] | - | - |
| 2. Full Deployment | [ ] | - | - |
| 3. Vault Security | [ ] | - | - |
| 4. Data Init | [ ] | - | - |
| 5. Jupyter | [ ] | - | - |
| 6. Backup/Restore | [ ] | - | - |
| 7. Monitoring | [ ] | - | - |
| 8. Security | [ ] | - | - |
| 9. Integration Tests | [ ] | - | - |
| 10. E2E Workflow | [ ] | - | - |

**Overall Status:** [ ] Pass [ ] Fail [ ] In Progress

---

## Known Issues to Verify

1. **Default Passwords** - Confirm still present (expected, documented blocker)
2. **MFA Incomplete** - Verify TODO markers still exist (expected)
3. **Script Fixes** - All 7 fixes should be working

---

## Post-Test Actions

### If All Tests Pass ✅
1. Update production readiness status to "VERIFIED"
2. Document test results
3. Proceed with default password replacement
4. Schedule external security audit

### If Tests Fail ❌
1. Document failure details
2. Identify root cause
3. Apply fixes
4. Re-run failed tests
5. Update remediation plan

---

## Test Execution Log

```
Test execution will be logged here...
```

---

**Test Plan Created:** 2026-01-29T04:07:00Z  
**Tester:** David Leconte (Advanced Mode)  
**Status:** 📋 Ready for Execution