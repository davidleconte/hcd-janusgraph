# Phase 3: Validation & Testing - Quick Start Guide

**Date:** 2026-02-11  
**Version:** 1.0  
**Status:** Active

---

## Overview

This guide provides quick commands to run all Phase 3 validation and testing tools.

---

## Prerequisites

```bash
# Activate conda environment
conda activate janusgraph-analysis

# Ensure services are running
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml ps
```

---

## Security Validation

### 1. Run Full Security Audit

```bash
# Full security audit (all checks)
python scripts/security/security_audit_framework.py --full

# Quick audit (critical checks only)
python scripts/security/security_audit_framework.py --quick

# Output location
ls -lh docs/implementation/audits/security/
```

**Expected Output:**
- JSON report: `audit-YYYYMMDD-HHMMSS.json`
- Markdown report: `audit-YYYYMMDD-HHMMSS.md`

### 2. Run Automated Penetration Tests

```bash
# Full penetration test suite
./scripts/security/run_pentest.sh

# Quick penetration test
./scripts/security/run_pentest.sh --quick

# Output location
ls -lh docs/implementation/audits/security/pentest/
```

**Expected Output:**
- Markdown report: `pentest-report-YYYYMMDD-HHMMSS.md`
- Tool outputs: `nmap-*.nmap`, `trivy-*.txt`, etc.

### 3. Check Security Status

```bash
# Quick security check
python scripts/security/security_audit_framework.py --quick 2>&1 | grep -A 10 "SUMMARY"
```

---

## Performance Validation

### 1. Run Load Tests

```bash
# API load test (60 seconds, 10 concurrent users)
python tests/performance/load_testing_framework.py \
  --scenario api_load \
  --duration 60 \
  --concurrent-users 10

# Full stack load test (300 seconds, 50 concurrent users)
python tests/performance/load_testing_framework.py \
  --scenario full \
  --duration 300 \
  --concurrent-users 50

# Output location
ls -lh docs/implementation/audits/performance/
```

**Expected Output:**
- JSON report: `load-test-YYYYMMDD-HHMMSS.json`
- Markdown report: `load-test-YYYYMMDD-HHMMSS.md`

### 2. Run Specific Performance Tests

```bash
# Credential rotation performance
python tests/performance/load_testing_framework.py \
  --scenario credential_rotation \
  --duration 60

# Query sanitization performance
python tests/performance/load_testing_framework.py \
  --scenario query_sanitization \
  --duration 60 \
  --concurrent-users 20

# Vault performance
python tests/performance/load_testing_framework.py \
  --scenario vault_performance \
  --duration 60 \
  --concurrent-users 20

# Concurrent users simulation
python tests/performance/load_testing_framework.py \
  --scenario concurrent_users \
  --duration 60 \
  --concurrent-users 50
```

### 3. Check Performance Status

```bash
# Quick performance check
python tests/performance/load_testing_framework.py \
  --scenario api_load \
  --duration 30 \
  --concurrent-users 5 2>&1 | grep -A 10 "SUMMARY"
```

---

## Compliance Validation

### 1. Run Compliance Audits

```bash
# All compliance standards
python scripts/compliance/compliance_audit_framework.py --standard all

# Individual standards
python scripts/compliance/compliance_audit_framework.py --standard gdpr
python scripts/compliance/compliance_audit_framework.py --standard soc2
python scripts/compliance/compliance_audit_framework.py --standard pci-dss
python scripts/compliance/compliance_audit_framework.py --standard bsa-aml

# Output location
ls -lh docs/compliance/audits/
```

**Expected Output:**
- JSON reports: `compliance-{standard}-YYYYMMDD-HHMMSS.json`
- Markdown reports: `compliance-{standard}-YYYYMMDD-HHMMSS.md`

### 2. Check Compliance Status

```bash
# Quick compliance check
python scripts/compliance/compliance_audit_framework.py --standard all 2>&1 | grep -A 5 "COMPLIANCE AUDIT"
```

---

## Complete Validation Suite

### Run All Validations

```bash
#!/bin/bash
# Run complete Phase 3 validation suite

echo "Starting Phase 3 Validation Suite..."
echo "===================================="

# 1. Security Audit
echo "[1/3] Running security audit..."
python scripts/security/security_audit_framework.py --full
SECURITY_EXIT=$?

# 2. Load Testing
echo "[2/3] Running load tests..."
python tests/performance/load_testing_framework.py \
  --scenario full \
  --duration 300 \
  --concurrent-users 50
PERFORMANCE_EXIT=$?

# 3. Compliance Audit
echo "[3/3] Running compliance audits..."
python scripts/compliance/compliance_audit_framework.py --standard all
COMPLIANCE_EXIT=$?

# Summary
echo ""
echo "===================================="
echo "Phase 3 Validation Complete"
echo "===================================="
echo "Security Audit: $([ $SECURITY_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo "Load Testing: $([ $PERFORMANCE_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo "Compliance Audit: $([ $COMPLIANCE_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo "===================================="

# Exit with error if any validation failed
[ $SECURITY_EXIT -eq 0 ] && [ $PERFORMANCE_EXIT -eq 0 ] && [ $COMPLIANCE_EXIT -eq 0 ]
```

Save as `scripts/validation/run_phase3_validation.sh` and run:

```bash
chmod +x scripts/validation/run_phase3_validation.sh
./scripts/validation/run_phase3_validation.sh
```

---

## Interpreting Results

### Security Audit Results

**Exit Codes:**
- `0` - All checks passed
- `1` - Critical findings detected
- `2` - High severity findings detected

**Status Indicators:**
- ✅ `COMPLIANT` - No issues
- ⚠️ `NEEDS_ATTENTION` - Minor issues
- ❌ `NON_COMPLIANT` - Critical issues

### Load Test Results

**SLA Requirements:**
- Average Response Time: < 200ms
- P95 Response Time: < 500ms
- P99 Response Time: < 1000ms
- Success Rate: > 99.5%
- Requests/Second: > 100

**Exit Codes:**
- `0` - All SLA requirements met
- `1` - SLA violations detected

### Compliance Audit Results

**Compliance Scores:**
- 95-100%: ✅ COMPLIANT
- 70-94%: ⚠️ PARTIAL
- <70%: ❌ NON_COMPLIANT

**Standards:**
- GDPR: Target 95%+
- SOC 2: Target 95%+
- PCI DSS: Target 100%
- BSA/AML: Target 100%

---

## Troubleshooting

### Security Audit Issues

**Issue:** "nmap not installed"
```bash
# macOS
brew install nmap

# Linux
sudo apt-get install nmap
```

**Issue:** "testssl.sh not found"
```bash
# Install testssl.sh
git clone https://github.com/drwetter/testssl.sh.git
sudo ln -s $(pwd)/testssl.sh/testssl.sh /usr/local/bin/testssl.sh
```

**Issue:** "trivy not installed"
```bash
# macOS
brew install trivy

# Linux
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy
```

### Load Test Issues

**Issue:** "Connection refused"
```bash
# Check if services are running
cd config/compose
podman-compose -p janusgraph-demo ps

# Start services if needed
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d

# Wait for services to be ready
sleep 90
```

**Issue:** "Import error: requests"
```bash
# Install required packages
conda activate janusgraph-analysis
uv pip install requests
```

### Compliance Audit Issues

**Issue:** "Module not found"
```bash
# Ensure you're in project root
cd /path/to/hcd-tarball-janusgraph

# Activate conda environment
conda activate janusgraph-analysis

# Install dependencies
uv pip install -r requirements.txt
```

---

## Report Locations

### Security Reports

```
docs/implementation/audits/security/
├── audit-YYYYMMDD-HHMMSS.json          # Security audit JSON
├── audit-YYYYMMDD-HHMMSS.md            # Security audit report
└── pentest/
    ├── pentest-report-YYYYMMDD-HHMMSS.md
    ├── nmap-YYYYMMDD-HHMMSS.nmap
    ├── testssl-YYYYMMDD-HHMMSS.txt
    ├── trivy-*.txt
    ├── bandit-YYYYMMDD-HHMMSS.json
    └── secrets-scan-YYYYMMDD-HHMMSS.txt
```

### Performance Reports

```
docs/implementation/audits/performance/
├── load-test-YYYYMMDD-HHMMSS.json      # Load test JSON
└── load-test-YYYYMMDD-HHMMSS.md        # Load test report
```

### Compliance Reports

```
docs/compliance/audits/
├── compliance-gdpr-YYYYMMDD-HHMMSS.json
├── compliance-gdpr-YYYYMMDD-HHMMSS.md
├── compliance-soc-2-type-ii-YYYYMMDD-HHMMSS.json
├── compliance-soc-2-type-ii-YYYYMMDD-HHMMSS.md
├── compliance-pci-dss-YYYYMMDD-HHMMSS.json
├── compliance-pci-dss-YYYYMMDD-HHMMSS.md
├── compliance-bsa-aml-YYYYMMDD-HHMMSS.json
└── compliance-bsa-aml-YYYYMMDD-HHMMSS.md
```

---

## Continuous Validation

### Daily Checks

```bash
# Quick daily validation (5 minutes)
python scripts/security/security_audit_framework.py --quick
python tests/performance/load_testing_framework.py --scenario api_load --duration 30
```

### Weekly Checks

```bash
# Weekly validation (30 minutes)
./scripts/security/run_pentest.sh
python tests/performance/load_testing_framework.py --scenario full --duration 300
```

### Monthly Checks

```bash
# Monthly validation (1 hour)
python scripts/security/security_audit_framework.py --full
python tests/performance/load_testing_framework.py --scenario full --duration 600 --concurrent-users 100
python scripts/compliance/compliance_audit_framework.py --standard all
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Phase 3 Validation

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  security-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Security Audit
        run: |
          python scripts/security/security_audit_framework.py --quick
      
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Load Tests
        run: |
          python tests/performance/load_testing_framework.py \
            --scenario api_load --duration 60
      
  compliance-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Compliance Audit
        run: |
          python scripts/compliance/compliance_audit_framework.py --standard all
```

---

## Next Steps

After running Phase 3 validation:

1. **Review Reports**
   - Check all generated reports
   - Identify any failures or warnings
   - Prioritize remediation

2. **Address Findings**
   - Fix critical security issues immediately
   - Plan remediation for high/medium issues
   - Document all changes

3. **Re-validate**
   - Run validation again after fixes
   - Verify all issues resolved
   - Update documentation

4. **Production Readiness**
   - Ensure all validations pass
   - Complete external audits
   - Get stakeholder approval

---

**Last Updated:** 2026-02-11  
**Version:** 1.0  
**Status:** Active