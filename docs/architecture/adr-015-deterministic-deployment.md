# ADR-015: Deterministic Deployment Strategy

**Status**: Accepted  
**Date**: 2026-02-19  
**Deciders**: Platform Engineering Team, Architecture Team, QA Team  
**Technical Story**: Architecture documentation improvement initiative

## Context

The HCD + JanusGraph Banking Compliance Platform requires reproducible deployments for reliable testing, debugging, and compliance auditing. Non-deterministic deployments lead to "works on my machine" problems, difficult-to-reproduce bugs, and unreliable CI/CD pipelines.

### Problem Statement

We need a deployment strategy that ensures:
- Same inputs produce same outputs (reproducibility)
- Bugs are reproducible across environments
- Test results are reliable and consistent
- Compliance audits can be reproduced
- CI/CD pipelines are predictable

### Constraints

- Must work with existing Podman/compose infrastructure
- Must support local development and CI/CD
- Must not significantly increase deployment time
- Must be enforceable through automation
- Must support debugging and troubleshooting

### Assumptions

- Determinism is achievable with proper controls
- Some variance (timing, network) is acceptable within bounds
- Team will follow deterministic practices
- Tooling can enforce deterministic behavior

### Infrastructure Requirements

**MANDATORY Podman Machine Configuration for Deterministic Deployment:**

```bash
podman machine init \
  --cpus 12 \
  --memory 24576 \   # 24 GB
  --disk-size 250 \  # 250 GB
  --now
```

**Why this configuration is required:**
- Deterministic pipeline runs 15+ notebooks simultaneously
- All services (JanusGraph, HCD, OpenSearch, Pulsar, Grafana, etc.) must run concurrently
- Insufficient resources cause timing variations → non-deterministic results
- This is the ONLY supported configuration for deterministic deployment

## Decision Drivers

- **Reproducibility**: Same inputs → same outputs
- **Debuggability**: Reproducible bugs are easier to fix
- **Reliability**: Consistent test results build confidence
- **Compliance**: Auditable, reproducible processes
- **CI/CD**: Predictable pipeline behavior

## Considered Options

### Option 1: Best-Effort Determinism

**Pros:**
- Easy to implement
- No special tooling required
- Flexible approach

**Cons:**
- Inconsistent results
- Hard to reproduce bugs
- Unreliable tests
- No guarantees
- Difficult auditing

### Option 2: Full Determinism (Hermetic Builds)

**Pros:**
- Complete reproducibility
- Maximum reliability
- Strong guarantees

**Cons:**
- Complex implementation
- Significant overhead
- May not be achievable for all components
- Requires specialized tooling
- High maintenance burden

### Option 3: Controlled Determinism (Our Approach)

**Pros:**
- Achievable with reasonable effort
- Good reproducibility (95%+)
- Practical for real-world use
- Balances determinism with flexibility
- Enforceable through automation

**Cons:**
- Not 100% deterministic
- Requires discipline
- Some variance remains
- Needs ongoing maintenance

## Decision

**We will implement a controlled determinism strategy using seed management, state reset, bounded execution, and artifact verification.**

### Rationale

1. **Practical Achievability**: 95%+ determinism is achievable without hermetic builds

2. **Seed Management**: All randomness derived from seeds ensures reproducible data generation

3. **State Reset**: Explicit state management eliminates hidden dependencies

4. **Bounded Execution**: Timeouts prevent infinite hangs and enable fail-fast

5. **Artifact Verification**: Baseline comparison detects drift and ensures consistency

6. **Automation**: Scripts and CI/CD enforce deterministic practices

## Consequences

### Positive

- **Reproducible Deployments**: Same seed → same output
- **Reliable Testing**: Consistent test results
- **Easier Debugging**: Bugs can be reproduced reliably
- **Compliance Ready**: Auditable, reproducible processes
- **CI/CD Confidence**: Predictable pipeline behavior
- **Team Productivity**: Less time debugging "works on my machine" issues

### Negative

- **Discipline Required**: Team must follow deterministic practices
- **Longer Deployment**: State reset adds ~30 seconds
- **Maintenance Overhead**: Baselines must be maintained
- **Not 100% Deterministic**: Some variance remains (timing, network)
- **Learning Curve**: Team must understand deterministic principles

### Neutral

- **Explicit Configuration**: All configuration must be explicit (no implicit defaults)
- **Bounded Variance**: Acceptable variance within defined bounds
- **Continuous Improvement**: Determinism improves over time

## Implementation

### Required Changes

1. **Seed Management**:
   ```python
   # banking/data_generators/core/base_generator.py
   class BaseGenerator:
       def __init__(self, seed: Optional[int] = None):
           self.seed = seed
           if seed is not None:
               random.seed(seed)
               Faker.seed(seed)
   ```

2. **Reference Timestamps**:
   ```python
   # Use fixed reference instead of datetime.now()
   REFERENCE_TIMESTAMP = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
   ```

3. **State Reset**:
   ```bash
   # scripts/testing/run_demo_pipeline_repeatable.sh
   if [[ "$DEMO_RESET_STATE" == "1" ]]; then
       podman-compose -p $PROJECT_NAME down -v
   fi
   ```

4. **Bounded Execution**:
   ```bash
   # Timeouts for all operations
   export DEMO_NOTEBOOK_TOTAL_TIMEOUT=420  # 7 minutes
   export DEMO_NOTEBOOK_CELL_TIMEOUT=180   # 3 minutes
   export MAX_HEALTH_WAIT_SEC=300          # 5 minutes
   ```

5. **Artifact Verification**:
   ```bash
   # Compare against baseline
   diff baseline_fingerprint.txt runtime_fingerprint.txt
   ```

6. **Environment Control**:
   ```bash
   # Fix Python hash seed
   export PYTHONHASHSEED=0
   
   # Set demo seed
   export DEMO_SEED=42
   ```

### Migration Path

**Phase 1: Enable Determinism (Week 1)**
1. Add seed management to generators
2. Implement reference timestamps
3. Add state reset to deployment scripts
4. Document deterministic practices

**Phase 2: Enforce Determinism (Week 2)**
1. Add bounded execution timeouts
2. Implement artifact verification
3. Create baseline artifacts
4. Add validation to CI/CD

**Phase 3: Optimize Determinism (Week 3-4)**
1. Identify remaining variance sources
2. Implement additional mitigations
3. Tune timeouts and thresholds
4. Document exceptions

### Rollback Strategy

If determinism causes issues:

1. **Disable State Reset**:
   ```bash
   export DEMO_RESET_STATE=0
   ```

2. **Disable Artifact Verification**:
   ```bash
   export DEMO_DETERMINISTIC_MODE=0
   ```

3. **Use Random Seeds**:
   ```bash
   unset DEMO_SEED
   ```

4. **Remove Timeouts**:
   ```bash
   unset DEMO_NOTEBOOK_TOTAL_TIMEOUT
   unset DEMO_NOTEBOOK_CELL_TIMEOUT
   ```

**Rollback Trigger**: If determinism prevents critical work or causes excessive delays.

## Compliance

- [x] Security review completed (no security impact)
- [x] Performance impact assessed (acceptable overhead)
- [x] Documentation updated (comprehensive guides)
- [x] Team notified (training on deterministic practices)

## References

- [Deterministic Deployment Architecture](deterministic-deployment-architecture.md)
- [Non-Determinism Analysis](non-determinism-analysis.md)
- [Deployment Architecture](deployment-architecture.md)
- [Martin Fowler: Eradicating Non-Determinism in Tests](https://martinfowler.com/articles/nonDeterminism.html)

## Notes

### Deterministic Principles

**1. Seed Management**
- All random values derived from seeds
- Seeds documented and version-controlled
- Different seeds for different purposes

**2. Reference Timestamps**
- Fixed reference timestamp for data generation
- Relative offsets instead of absolute times
- UTC everywhere

**3. State Reset**
- Explicit state management
- Complete reset before deployment
- Verification of clean state

**4. Bounded Execution**
- All operations have timeouts
- Fail-fast on timeout
- Predictable pipeline duration

**5. Artifact Verification**
- Baseline capture on first success
- Comparison on subsequent runs
- Investigation of differences

### Determinism Levels

| Level | Description | Achievement |
|-------|-------------|-------------|
| **Data Generation** | Seeded randomness | 100% |
| **Deployment** | State reset + health checks | 95% |
| **Notebook Execution** | Seeded + bounded | 90% |
| **Test Results** | Controlled environment | 95% |
| **CI/CD Pipelines** | Automated enforcement | 90% |

### Acceptable Variance

**Timing Variance**: ±30 seconds for service startup  
**Network Variance**: ±100ms for API calls  
**CI/CD Variance**: ±2 minutes for pipeline duration

**Rationale**: These variances are within acceptable bounds and don't affect functional correctness.

### Canonical Command

```bash
# Full deterministic deployment
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
  --status-report exports/deterministic-status.json
```

**What it does**:
1. Validates environment (G0)
2. Checks Podman connection (G2)
3. Resets state (G3)
4. Deploys services (G5)
5. Validates runtime contracts (G6)
6. Seeds graph (G7)
7. Executes notebooks (G8)
8. Verifies determinism (G9)

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DEMO_SEED` | `42` | Random seed |
| `DEMO_RESET_STATE` | `1` | Enable state reset |
| `DEMO_DETERMINISTIC_MODE` | `1` | Enable determinism checks |
| `PYTHONHASHSEED` | `0` | Fix Python hash seed |
| `DEMO_NOTEBOOK_TOTAL_TIMEOUT` | `420` | Notebook timeout (s) |
| `DEMO_NOTEBOOK_CELL_TIMEOUT` | `180` | Cell timeout (s) |
| `MAX_HEALTH_WAIT_SEC` | `300` | Health check timeout |

### Testing Determinism

**Test 1: Data Generation**
```bash
DEMO_SEED=42 python generate_data.py > output1.json
DEMO_SEED=42 python generate_data.py > output2.json
diff output1.json output2.json  # Should be identical
```

**Test 2: Deployment**
```bash
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh
# Compare artifacts - should be identical (except timestamps)
```

**Test 3: Notebooks**
```bash
DEMO_SEED=42 jupyter nbconvert --execute notebook.ipynb --to notebook --output run1.ipynb
DEMO_SEED=42 jupyter nbconvert --execute notebook.ipynb --to notebook --output run2.ipynb
# Compare outputs - should be identical (except execution metadata)
```

### Troubleshooting Non-Determinism

**Issue**: Different outputs with same seed

**Checklist**:
1. ✅ Seed set correctly?
2. ✅ PYTHONHASHSEED=0?
3. ✅ Reference timestamp used?
4. ✅ State reset before run?
5. ✅ No datetime.now() calls?
6. ✅ No unseeded random calls?
7. ✅ Sorted iteration (sets, dicts)?

**Debug**:
```bash
# Enable debug logging
export DEBUG=1

# Run with verbose output
bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh 2>&1 | tee debug.log

# Compare debug logs
diff debug1.log debug2.log
```

### Best Practices

1. **Always Use Seeds**:
   ```python
   # ✅ CORRECT
   generator = PersonGenerator(seed=42)
   
   # ❌ WRONG
   generator = PersonGenerator()
   ```

2. **Use Reference Timestamps**:
   ```python
   # ✅ CORRECT
   timestamp = REFERENCE_TIMESTAMP + timedelta(days=-30)
   
   # ❌ WRONG
   timestamp = datetime.now()
   ```

3. **Reset State**:
   ```bash
   # ✅ CORRECT
   podman-compose -p janusgraph-demo down -v
   podman-compose -p janusgraph-demo up -d
   
   # ❌ WRONG
   podman-compose restart
   ```

4. **Use Timeouts**:
   ```python
   # ✅ CORRECT
   response = requests.get(url, timeout=10)
   
   # ❌ WRONG
   response = requests.get(url)
   ```

5. **Verify Artifacts**:
   ```bash
   # ✅ CORRECT
   diff baseline.txt current.txt
   
   # ❌ WRONG
   # No verification
   ```

### Future Improvements

- **Hermetic Builds**: Explore fully hermetic builds for critical components
- **Snapshot Testing**: Implement snapshot testing for UI components
- **Chaos Engineering**: Test determinism under failure conditions
- **Performance**: Optimize state reset and verification
- **Monitoring**: Add determinism metrics to dashboards

---

**Last Updated**: 2026-02-19  
**Next Review**: 2026-05-19 (3 months)  
**Owner**: Platform Engineering Team