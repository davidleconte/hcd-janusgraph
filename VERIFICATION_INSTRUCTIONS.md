# Test Verification Instructions

**Date:** 2026-04-07  
**Status:** Ready for Verification  
**Modules:** Streaming, AML, Compliance, Fraud, Patterns (5/6 complete)

---

## Overview

This document provides step-by-step instructions for verifying test coverage and deterministic behavior for all completed test modules.

---

## Prerequisites

```bash
# 1. Activate conda environment (REQUIRED)
conda activate janusgraph-analysis

# 2. Verify environment
which python  # Should show conda env path
python --version  # Should show Python 3.11+

# 3. Verify pytest is installed
pytest --version
```

---

## Step 1: Coverage Verification

### 1.1 Individual Module Coverage

**Streaming Module:**
```bash
pytest banking/streaming/tests/test_*_unit.py -v \
  --cov=banking/streaming \
  --cov-report=html:htmlcov/streaming \
  --cov-report=term-missing \
  --cov-fail-under=70
```

**AML Module:**
```bash
pytest banking/aml/tests/test_*_unit.py -v \
  --cov=banking/aml \
  --cov-report=html:htmlcov/aml \
  --cov-report=term-missing \
  --cov-fail-under=70
```

**Compliance Module:**
```bash
pytest banking/compliance/tests/test_*_unit.py -v \
  --cov=banking/compliance \
  --cov-report=html:htmlcov/compliance \
  --cov-report=term-missing \
  --cov-fail-under=70
```

**Fraud Module:**
```bash
pytest banking/fraud/tests/test_fraud_detection_unit.py -v \
  --cov=banking/fraud \
  --cov-report=html:htmlcov/fraud \
  --cov-report=term-missing \
  --cov-fail-under=70
```

**Patterns Module:**
```bash
pytest banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py -v \
  --cov=banking/data_generators/patterns \
  --cov-report=html:htmlcov/patterns \
  --cov-report=term-missing \
  --cov-fail-under=70
```

### 1.2 Combined Coverage Report

**All Completed Modules:**
```bash
pytest \
  banking/streaming/tests/test_*_unit.py \
  banking/aml/tests/test_*_unit.py \
  banking/compliance/tests/test_*_unit.py \
  banking/fraud/tests/test_fraud_detection_unit.py \
  banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py \
  -v \
  --cov=banking/streaming \
  --cov=banking/aml \
  --cov=banking/compliance \
  --cov=banking/fraud \
  --cov=banking/data_generators/patterns \
  --cov-report=html:htmlcov/combined \
  --cov-report=term-missing \
  --cov-fail-under=70
```

### 1.3 View Coverage Reports

```bash
# Open HTML coverage reports in browser
open htmlcov/combined/index.html  # macOS
xdg-open htmlcov/combined/index.html  # Linux
start htmlcov/combined/index.html  # Windows
```

### 1.4 Expected Coverage Results

| Module | Current | Target | Expected | Pass Criteria |
|--------|---------|--------|----------|---------------|
| Streaming | 28% | 70%+ | 83%+ | ✅ Should pass |
| AML | 25% | 70%+ | 82%+ | ✅ Should pass |
| Compliance | 25% | 70%+ | 85%+ | ✅ Should pass |
| Fraud | 23% | 70%+ | 75%+ | ✅ Should pass |
| Patterns | 13% | 70%+ | 72%+ | ✅ Should pass |

---

## Step 2: Deterministic Behavior Verification

### 2.1 Individual Module Determinism Tests

**Streaming Module (10 runs):**
```bash
echo "Testing Streaming Module Determinism..."
for i in {1..10}; do 
  echo "Run $i/10..."
  pytest banking/streaming/tests/test_*_unit.py -v -q || exit 1
done
echo "✅ Streaming: All 10 runs passed - tests are deterministic"
```

**AML Module (10 runs):**
```bash
echo "Testing AML Module Determinism..."
for i in {1..10}; do 
  echo "Run $i/10..."
  pytest banking/aml/tests/test_*_unit.py -v -q || exit 1
done
echo "✅ AML: All 10 runs passed - tests are deterministic"
```

**Compliance Module (10 runs):**
```bash
echo "Testing Compliance Module Determinism..."
for i in {1..10}; do 
  echo "Run $i/10..."
  pytest banking/compliance/tests/test_*_unit.py -v -q || exit 1
done
echo "✅ Compliance: All 10 runs passed - tests are deterministic"
```

**Fraud Module (10 runs):**
```bash
echo "Testing Fraud Module Determinism..."
for i in {1..10}; do 
  echo "Run $i/10..."
  pytest banking/fraud/tests/test_fraud_detection_unit.py -v -q || exit 1
done
echo "✅ Fraud: All 10 runs passed - tests are deterministic"
```

**Patterns Module (10 runs):**
```bash
echo "Testing Patterns Module Determinism..."
for i in {1..10}; do 
  echo "Run $i/10..."
  pytest banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py -v -q || exit 1
done
echo "✅ Patterns: All 10 runs passed - tests are deterministic"
```

### 2.2 Combined Determinism Test

**All Modules (10 runs):**
```bash
echo "Testing All Modules Determinism..."
for i in {1..10}; do 
  echo "Run $i/10..."
  pytest \
    banking/streaming/tests/test_*_unit.py \
    banking/aml/tests/test_*_unit.py \
    banking/compliance/tests/test_*_unit.py \
    banking/fraud/tests/test_fraud_detection_unit.py \
    banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py \
    -v -q || exit 1
done
echo "✅ All modules: All 10 runs passed - tests are deterministic"
```

### 2.3 Determinism Verification Checklist

After running the tests, verify:

- [ ] All 10 runs completed without failures
- [ ] No random test failures
- [ ] No timing-dependent failures
- [ ] Same test results across all runs
- [ ] No flaky tests detected

---

## Step 3: Test Statistics Collection

### 3.1 Count Tests

```bash
# Count tests per module
echo "Streaming Tests:"
pytest banking/streaming/tests/test_*_unit.py --collect-only -q | tail -1

echo "AML Tests:"
pytest banking/aml/tests/test_*_unit.py --collect-only -q | tail -1

echo "Compliance Tests:"
pytest banking/compliance/tests/test_*_unit.py --collect-only -q | tail -1

echo "Fraud Tests:"
pytest banking/fraud/tests/test_fraud_detection_unit.py --collect-only -q | tail -1

echo "Patterns Tests:"
pytest banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py --collect-only -q | tail -1

echo "Total Tests:"
pytest \
  banking/streaming/tests/test_*_unit.py \
  banking/aml/tests/test_*_unit.py \
  banking/compliance/tests/test_*_unit.py \
  banking/fraud/tests/test_fraud_detection_unit.py \
  banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py \
  --collect-only -q | tail -1
```

### 3.2 Test Execution Time

```bash
# Measure execution time
time pytest \
  banking/streaming/tests/test_*_unit.py \
  banking/aml/tests/test_*_unit.py \
  banking/compliance/tests/test_*_unit.py \
  banking/fraud/tests/test_fraud_detection_unit.py \
  banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py \
  -v
```

---

## Step 4: Results Documentation

### 4.1 Create Verification Report

After running all tests, create a verification report:

```bash
# Create verification report directory
mkdir -p verification_reports

# Generate coverage report
pytest \
  banking/streaming/tests/test_*_unit.py \
  banking/aml/tests/test_*_unit.py \
  banking/compliance/tests/test_*_unit.py \
  banking/fraud/tests/test_fraud_detection_unit.py \
  banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py \
  --cov=banking/streaming \
  --cov=banking/aml \
  --cov=banking/compliance \
  --cov=banking/fraud \
  --cov=banking/data_generators/patterns \
  --cov-report=json:verification_reports/coverage.json \
  --cov-report=html:verification_reports/htmlcov \
  --cov-report=term > verification_reports/coverage_report.txt
```

### 4.2 Verification Report Template

Create `verification_reports/VERIFICATION_REPORT.md`:

```markdown
# Test Verification Report

**Date:** YYYY-MM-DD
**Verified By:** [Your Name]
**Status:** [PASS/FAIL]

## Coverage Results

| Module | Coverage | Target | Status |
|--------|----------|--------|--------|
| Streaming | X% | 70%+ | [PASS/FAIL] |
| AML | X% | 70%+ | [PASS/FAIL] |
| Compliance | X% | 70%+ | [PASS/FAIL] |
| Fraud | X% | 70%+ | [PASS/FAIL] |
| Patterns | X% | 70%+ | [PASS/FAIL] |

## Determinism Results

| Module | Runs | Failures | Status |
|--------|------|----------|--------|
| Streaming | 10 | 0 | [PASS/FAIL] |
| AML | 10 | 0 | [PASS/FAIL] |
| Compliance | 10 | 0 | [PASS/FAIL] |
| Fraud | 10 | 0 | [PASS/FAIL] |
| Patterns | 10 | 0 | [PASS/FAIL] |

## Test Statistics

- Total Tests: XXX
- Total Execution Time: XX seconds
- Average Test Time: XX ms

## Issues Found

[List any issues or failures]

## Recommendations

[List any recommendations]
```

---

## Troubleshooting

### Issue: Tests Fail

**Solution:**
```bash
# Run with verbose output to see failures
pytest [test_path] -vv

# Run specific failing test
pytest [test_path]::[test_name] -vv
```

### Issue: Coverage Below Target

**Solution:**
```bash
# See which lines are not covered
pytest [test_path] --cov=[module] --cov-report=term-missing

# View HTML report for detailed analysis
open htmlcov/index.html
```

### Issue: Import Errors

**Solution:**
```bash
# Verify conda environment is activated
conda activate janusgraph-analysis

# Verify PYTHONPATH
echo $PYTHONPATH

# Install missing dependencies
uv pip install pytest pytest-cov pytest-mock
```

### Issue: Flaky Tests

**Solution:**
```bash
# Run test multiple times to identify flakiness
pytest [test_path] --count=10

# Check for timing dependencies
pytest [test_path] -vv --tb=short
```

---

## Success Criteria

### Coverage Verification ✅
- [ ] All modules achieve 70%+ coverage
- [ ] Coverage reports generated successfully
- [ ] No critical gaps in coverage

### Determinism Verification ✅
- [ ] All modules pass 10 consecutive runs
- [ ] No flaky tests detected
- [ ] Consistent results across runs

### Documentation ✅
- [ ] Verification report created
- [ ] Results documented
- [ ] Issues logged (if any)

---

## Next Steps After Verification

1. **If All Tests Pass:**
   - Update coverage baselines
   - Proceed to Phase 6 (Analytics Module)
   - Update CI configuration

2. **If Tests Fail:**
   - Document failures
   - Fix failing tests
   - Re-run verification
   - Update test implementation

3. **If Coverage Below Target:**
   - Identify uncovered code
   - Add additional tests
   - Re-run coverage verification

---

**Last Updated:** 2026-04-07  
**Author:** Bob (AI Assistant)  
**Status:** Ready for Verification