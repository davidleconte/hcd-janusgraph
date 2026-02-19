# ADR-016: Gate-Based Validation Framework

**Status**: Accepted  
**Date**: 2026-02-19  
**Deciders**: Platform Engineering Team, QA Team, CI/CD Team  
**Technical Story**: Architecture documentation improvement initiative

## Context

Deployment failures can occur at many stages: environment setup, service startup, configuration, data loading, and runtime execution. Without structured validation, failures are detected late, root causes are unclear, and recovery is difficult.

### Problem Statement

We need a validation framework that:
- Detects failures early (fail-fast)
- Provides clear failure context
- Enables targeted troubleshooting
- Supports automated recovery
- Works in local and CI/CD environments

### Constraints

- Must work with existing deployment scripts
- Must not significantly increase deployment time
- Must provide actionable error messages
- Must support both automated and manual troubleshooting
- Must be maintainable and extensible

### Assumptions

- Failures can be categorized into discrete stages
- Early detection reduces debugging time
- Clear failure context aids troubleshooting
- Automated validation is more reliable than manual

## Decision Drivers

- **Fail-Fast**: Detect failures as early as possible
- **Clear Context**: Know exactly what failed and why
- **Actionable**: Error messages guide recovery
- **Automation**: Enforceable in CI/CD
- **Maintainability**: Easy to add new gates

## Considered Options

### Option 1: Monolithic Validation

**Pros:**
- Simple implementation
- Single validation point
- Easy to understand

**Cons:**
- Late failure detection
- Unclear failure context
- Difficult troubleshooting
- All-or-nothing approach
- No incremental progress

### Option 2: Ad-Hoc Checks

**Pros:**
- Flexible
- Easy to add checks
- No framework overhead

**Cons:**
- Inconsistent error handling
- No standardization
- Difficult to maintain
- No clear failure taxonomy
- Hard to automate

### Option 3: Gate-Based Validation (Our Approach)

**Pros:**
- Early failure detection
- Clear failure context
- Structured troubleshooting
- Incremental validation
- Easy to extend
- Automation-friendly

**Cons:**
- Framework overhead
- More complex implementation
- Requires discipline
- Gate definitions must be maintained

## Decision

**We will implement a gate-based validation framework with 10 discrete validation gates (G0-G9) that must pass sequentially for successful deployment.**

### Rationale

1. **Fail-Fast**: Each gate validates prerequisites before proceeding, detecting failures early

2. **Clear Context**: Gate codes (G0-G9) immediately identify failure stage

3. **Structured Troubleshooting**: Each gate has specific recovery procedures

4. **Incremental Progress**: Successful gates don't need re-validation

5. **Automation**: Gates are scriptable and enforceable in CI/CD

6. **Extensibility**: New gates can be added without disrupting existing ones

## Consequences

### Positive

- **Early Detection**: Failures detected at earliest possible stage
- **Clear Diagnosis**: Gate code immediately identifies problem area
- **Faster Recovery**: Targeted troubleshooting reduces MTTR
- **Reliable Automation**: Consistent validation in CI/CD
- **Better Metrics**: Gate-level success rates provide insights
- **Incremental Progress**: Can resume from last successful gate

### Negative

- **Complexity**: More complex than simple validation
- **Maintenance**: Gate definitions must be kept current
- **Overhead**: Each gate adds validation time (~5-10s per gate)
- **Learning Curve**: Team must understand gate system

### Neutral

- **Standardization**: All deployments follow same validation path
- **Documentation**: Gates must be well-documented
- **Tooling**: Scripts must implement gate logic consistently

## Implementation

### Required Changes

1. **Gate Definitions**:
   ```bash
   # scripts/testing/run_demo_pipeline_repeatable.sh
   
   # G0: Preflight Checks
   run_cmd "Preflight Validation" \
       "scripts/validation/preflight_check.sh --strict" \
       "${REPORT_DIR}/preflight.log" \
       bash scripts/validation/preflight_check.sh --strict
   
   # G2: Connection Validation
   if ! PODMAN_CONNECTION="$(resolve_podman_connection)"; then
       echo "G2_CONNECTION" > "${FAILED_GATE_FILE}"
       exit 1
   fi
   
   # G3: State Reset
   run_cmd "Deterministic State Reset" \
       "podman-compose down -v" \
       "${REPORT_DIR}/state_reset.log" \
       bash -c "cd config/compose && podman-compose -p ${PROJECT_NAME} down -v"
   
   # ... (G5, G6, G7, G8, G9)
   ```

2. **Gate Failure Handling**:
   ```bash
   run_cmd() {
       local step="$1"
       local cmd_desc="$2"
       local log_file="$3"
       shift 3
       
       if ! "$@" >"${log_file}" 2>&1; then
           case "${step}" in
               "Preflight Validation"|"Podman Isolation Validation")
                   echo "G0_PRECHECK" > "${FAILED_GATE_FILE}"
                   ;;
               "Deterministic State Reset")
                   echo "G3_RESET" > "${FAILED_GATE_FILE}"
                   ;;
               # ... other gates
           esac
           echo "❌ ${step} failed"
           return 1
       fi
       echo "✅ ${step} complete"
   }
   ```

3. **Status Reporting**:
   ```bash
   # Write status report
   cat > "${STATUS_REPORT}" <<EOF
   {
     "timestamp_utc": "${RUN_TIMESTAMP}",
     "exit_code": ${EXIT_CODE},
     "failed_gate": "$(cat ${FAILED_GATE_FILE} 2>/dev/null || echo 'none')"
   }
   EOF
   ```

4. **CI/CD Integration**:
   ```yaml
   # .github/workflows/deterministic-proof.yml
   - name: Run Deterministic Deployment
     run: |
       bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
         --status-report exports/deterministic-status.json
   
   - name: Check Gate Status
     if: failure()
     run: |
       FAILED_GATE=$(jq -r '.failed_gate' exports/deterministic-status.json)
       echo "::error::Deployment failed at gate: $FAILED_GATE"
   ```

### Migration Path

**Phase 1: Implement Gates (Week 1)**
1. Define gate structure
2. Implement gate validation logic
3. Add gate failure handling
4. Document gate definitions

**Phase 2: Integrate Gates (Week 2)**
1. Update deployment scripts
2. Add status reporting
3. Integrate with CI/CD
4. Create troubleshooting guides

**Phase 3: Optimize Gates (Week 3-4)**
1. Tune gate timeouts
2. Add gate-specific recovery
3. Improve error messages
4. Add gate metrics

### Rollback Strategy

If gate-based validation causes issues:

1. **Disable Gate Checks**:
   ```bash
   # Skip all gates
   bash scripts/deployment/deploy_full_stack.sh --no-validation
   ```

2. **Bypass Specific Gate**:
   ```bash
   # Skip preflight
   bash scripts/testing/run_demo_pipeline_repeatable.sh --skip-preflight
   ```

3. **Remove Gate Logic**:
   ```bash
   # Revert to simple validation
   git revert <gate-commit>
   ```

**Rollback Trigger**: If gates cause excessive false positives or deployment delays.

## Compliance

- [x] Security review completed (no security impact)
- [x] Performance impact assessed (acceptable overhead)
- [x] Documentation updated (comprehensive gate guide)
- [x] Team notified (training on gate system)

## References

- [Deterministic Deployment Architecture](deterministic-deployment-architecture.md)
- [Deployment Architecture](deployment-architecture.md)
- [Non-Determinism Analysis](non-determinism-analysis.md)

## Notes

### Gate Definitions

| Gate | Name | Purpose | Typical Duration |
|------|------|---------|------------------|
| **G0** | Preflight Checks | Validate environment | 5-10s |
| **G2** | Connection | Verify Podman reachable | 1-2s |
| **G3** | State Reset | Clean slate | 10-30s |
| **G5** | Deploy + Vault | Services up and healthy | 90-180s |
| **G6** | Runtime Contract | Validate runtime | 10-20s |
| **G7** | Graph Seed | Load demo data | 30-60s |
| **G8** | Notebooks | Execute notebooks | 300-600s |
| **G9** | Determinism | Verify artifacts | 5-10s |

### Gate Flow

```
START
  ↓
G0: Preflight ──FAIL──> Exit(G0_PRECHECK)
  ↓ PASS
G2: Connection ──FAIL──> Exit(G2_CONNECTION)
  ↓ PASS
G3: Reset ──FAIL──> Exit(G3_RESET)
  ↓ PASS
G5: Deploy ──FAIL──> Exit(G5_DEPLOY_VAULT)
  ↓ PASS
G6: Runtime ──FAIL──> Exit(G6_RUNTIME_CONTRACT)
  ↓ PASS
G7: Seed ──FAIL──> Exit(G7_SEED)
  ↓ PASS
G8: Notebooks ──FAIL──> Exit(G8_NOTEBOOKS)
  ↓ PASS
G9: Determinism ──FAIL──> Exit(G9_DETERMINISM)
  ↓ PASS
SUCCESS
```

### Gate Exit Codes

All gates use exit code `1` on failure, but write specific gate code to `failed_gate.txt`:

| Gate Code | Meaning | Recovery |
|-----------|---------|----------|
| `G0_PRECHECK` | Environment/isolation check failed | Fix environment, free ports |
| `G2_CONNECTION` | Podman unreachable | Start podman machine |
| `G3_RESET` | State reset failed | Force remove resources |
| `G5_DEPLOY_VAULT` | Deployment/health failed | Check logs, restart services |
| `G6_RUNTIME_CONTRACT` | Runtime contract violation | Fix secrets, packages |
| `G7_SEED` | Graph seeding failed | Check graph connection |
| `G8_NOTEBOOKS` | Notebook execution failed | Debug notebook, increase timeout |
| `G9_DETERMINISM` | Artifact mismatch | Update baseline or fix drift |

### Troubleshooting by Gate

**G0 Failure**:
```bash
# Read preflight log
cat exports/<RUN_ID>/preflight.log

# Common fixes
conda activate janusgraph-analysis
lsof -ti:18182 | xargs kill -9
```

**G2 Failure**:
```bash
# Check Podman machine
podman machine list
podman machine start
```

**G5 Failure**:
```bash
# Check service logs
podman logs janusgraph-demo_hcd-server_1
podman logs janusgraph-demo_janusgraph-server_1

# Check health
podman ps --filter "health=unhealthy"
```

**G8 Failure**:
```bash
# Read notebook report
cat exports/<RUN_ID>/notebook_run_report.tsv

# Find failed notebook
grep FAIL exports/<RUN_ID>/notebook_run_report.tsv

# Run manually
jupyter nbconvert --execute <notebook>.ipynb
```

### Gate Metrics

**Success Rates** (Target):
- G0: 98% (environment issues rare)
- G2: 99% (connection usually stable)
- G3: 99% (reset rarely fails)
- G5: 95% (services occasionally timeout)
- G6: 98% (runtime usually correct)
- G7: 97% (graph seed usually works)
- G8: 90% (notebooks most variable)
- G9: 95% (determinism usually maintained)

**Overall Success Rate**: 85% (all gates pass)

### Best Practices

1. **Always Check Gate Status**:
   ```bash
   if [ -f exports/<RUN_ID>/failed_gate.txt ]; then
       FAILED_GATE=$(cat exports/<RUN_ID>/failed_gate.txt)
       echo "Failed at gate: $FAILED_GATE"
   fi
   ```

2. **Use Gate-Specific Recovery**:
   ```bash
   case "$FAILED_GATE" in
       G0_PRECHECK)
           # Fix environment
           ;;
       G5_DEPLOY_VAULT)
           # Restart services
           ;;
   esac
   ```

3. **Log Gate Progress**:
   ```bash
   echo "[$(date)] Starting gate G0: Preflight"
   echo "[$(date)] Gate G0: PASS"
   ```

4. **Monitor Gate Metrics**:
   ```bash
   # Track gate success rates
   grep "Gate.*PASS" logs/*.log | wc -l
   grep "Gate.*FAIL" logs/*.log | wc -l
   ```

5. **Document Gate Changes**:
   ```bash
   # When adding new gate
   # 1. Update gate definitions
   # 2. Update troubleshooting guide
   # 3. Update CI/CD workflows
   # 4. Update documentation
   ```

### Future Enhancements

- **Gate Retry**: Automatic retry for transient failures
- **Gate Skip**: Allow skipping specific gates with justification
- **Gate Metrics**: Dashboard showing gate success rates
- **Gate Alerts**: Alert on repeated gate failures
- **Gate Optimization**: Parallel gate execution where possible

### Example Usage

**Full Deployment**:
```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

**Skip Preflight** (for already-running stack):
```bash
bash scripts/testing/run_demo_pipeline_repeatable.sh --skip-preflight
```

**Skip Notebooks** (for services-only testing):
```bash
bash scripts/testing/run_demo_pipeline_repeatable.sh --skip-notebooks
```

**Dry Run** (show execution plan):
```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --dry-run
```

---

**Last Updated**: 2026-02-19  
**Next Review**: 2026-05-19 (3 months)  
**Owner**: Platform Engineering Team