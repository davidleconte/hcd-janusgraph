#!/bin/bash
# Test Verification Script
# Runs coverage and determinism verification for all completed test modules
# Date: 2026-04-07

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERIFICATION_DIR="verification_reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${VERIFICATION_DIR}/verification_report_${TIMESTAMP}.md"

# Test modules
STREAMING_TESTS="banking/streaming/tests/test_*_unit.py"
AML_TESTS="banking/aml/tests/test_*_unit.py"
COMPLIANCE_TESTS="banking/compliance/tests/test_*_unit.py"
FRAUD_TESTS="banking/fraud/tests/test_fraud_detection_unit.py"
PATTERNS_TESTS="banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py"

# Coverage modules
STREAMING_COV="banking/streaming"
AML_COV="banking/aml"
COMPLIANCE_COV="banking/compliance"
FRAUD_COV="banking/fraud"
PATTERNS_COV="banking/data_generators/patterns"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check conda environment
    if [[ "$CONDA_DEFAULT_ENV" != "janusgraph-analysis" ]]; then
        print_error "Conda environment 'janusgraph-analysis' not activated"
        echo "Run: conda activate janusgraph-analysis"
        exit 1
    fi
    print_success "Conda environment: $CONDA_DEFAULT_ENV"
    
    # Check Python version
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    print_success "Python version: $PYTHON_VERSION"
    
    # Check pytest
    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found"
        echo "Run: uv pip install pytest pytest-cov"
        exit 1
    fi
    PYTEST_VERSION=$(pytest --version 2>&1 | head -1)
    print_success "$PYTEST_VERSION"
    
    # Create verification directory
    mkdir -p "$VERIFICATION_DIR"
    print_success "Verification directory: $VERIFICATION_DIR"
    
    echo ""
}

# Run coverage for a single module
run_module_coverage() {
    local module_name=$1
    local test_path=$2
    local cov_path=$3
    local output_dir="${VERIFICATION_DIR}/htmlcov_${module_name}"
    
    print_info "Running coverage for $module_name..."
    
    if pytest $test_path -v \
        --cov=$cov_path \
        --cov-report=html:$output_dir \
        --cov-report=term-missing \
        --cov-fail-under=70 > "${VERIFICATION_DIR}/${module_name}_coverage.txt" 2>&1; then
        
        # Extract coverage percentage
        local coverage=$(grep "TOTAL" "${VERIFICATION_DIR}/${module_name}_coverage.txt" | awk '{print $NF}')
        print_success "$module_name: $coverage coverage"
        echo "$coverage"
    else
        print_error "$module_name: Coverage below 70%"
        echo "FAIL"
    fi
}

# Run determinism test for a single module
run_module_determinism() {
    local module_name=$1
    local test_path=$2
    local runs=10
    
    print_info "Testing $module_name determinism ($runs runs)..."
    
    local failed=0
    for i in $(seq 1 $runs); do
        if ! pytest $test_path -v -q > /dev/null 2>&1; then
            failed=$((failed + 1))
        fi
    done
    
    if [ $failed -eq 0 ]; then
        print_success "$module_name: All $runs runs passed"
        echo "PASS"
    else
        print_error "$module_name: $failed/$runs runs failed"
        echo "FAIL"
    fi
}

# Main verification
main() {
    print_header "Test Verification Script"
    echo "Date: $(date)"
    echo "Report: $REPORT_FILE"
    echo ""
    
    check_prerequisites
    
    # Initialize report
    cat > "$REPORT_FILE" << EOF
# Test Verification Report

**Date:** $(date +%Y-%m-%d)
**Time:** $(date +%H:%M:%S)
**Verified By:** Automated Script
**Status:** In Progress

---

## Coverage Results

| Module | Coverage | Target | Status |
|--------|----------|--------|--------|
EOF
    
    # Step 1: Coverage Verification
    print_header "Step 1: Coverage Verification"
    
    declare -A coverage_results
    
    # Streaming
    coverage_results[Streaming]=$(run_module_coverage "streaming" "$STREAMING_TESTS" "$STREAMING_COV")
    
    # AML
    coverage_results[AML]=$(run_module_coverage "aml" "$AML_TESTS" "$AML_COV")
    
    # Compliance
    coverage_results[Compliance]=$(run_module_coverage "compliance" "$COMPLIANCE_TESTS" "$COMPLIANCE_COV")
    
    # Fraud
    coverage_results[Fraud]=$(run_module_coverage "fraud" "$FRAUD_TESTS" "$FRAUD_COV")
    
    # Patterns
    coverage_results[Patterns]=$(run_module_coverage "patterns" "$PATTERNS_TESTS" "$PATTERNS_COV")
    
    echo ""
    
    # Update report with coverage results
    for module in Streaming AML Compliance Fraud Patterns; do
        local result="${coverage_results[$module]}"
        if [[ "$result" == "FAIL" ]]; then
            echo "| $module | FAIL | 70%+ | ❌ FAIL |" >> "$REPORT_FILE"
        else
            echo "| $module | $result | 70%+ | ✅ PASS |" >> "$REPORT_FILE"
        fi
    done
    
    cat >> "$REPORT_FILE" << EOF

---

## Determinism Results

| Module | Runs | Failures | Status |
|--------|------|----------|--------|
EOF
    
    # Step 2: Determinism Verification
    print_header "Step 2: Determinism Verification"
    
    declare -A determinism_results
    
    # Streaming
    determinism_results[Streaming]=$(run_module_determinism "Streaming" "$STREAMING_TESTS")
    
    # AML
    determinism_results[AML]=$(run_module_determinism "AML" "$AML_TESTS")
    
    # Compliance
    determinism_results[Compliance]=$(run_module_determinism "Compliance" "$COMPLIANCE_TESTS")
    
    # Fraud
    determinism_results[Fraud]=$(run_module_determinism "Fraud" "$FRAUD_TESTS")
    
    # Patterns
    determinism_results[Patterns]=$(run_module_determinism "Patterns" "$PATTERNS_TESTS")
    
    echo ""
    
    # Update report with determinism results
    for module in Streaming AML Compliance Fraud Patterns; do
        local result="${determinism_results[$module]}"
        if [[ "$result" == "PASS" ]]; then
            echo "| $module | 10 | 0 | ✅ PASS |" >> "$REPORT_FILE"
        else
            echo "| $module | 10 | >0 | ❌ FAIL |" >> "$REPORT_FILE"
        fi
    done
    
    # Step 3: Combined Coverage
    print_header "Step 3: Combined Coverage Report"
    
    print_info "Running combined coverage..."
    pytest \
        $STREAMING_TESTS \
        $AML_TESTS \
        $COMPLIANCE_TESTS \
        $FRAUD_TESTS \
        $PATTERNS_TESTS \
        --cov=$STREAMING_COV \
        --cov=$AML_COV \
        --cov=$COMPLIANCE_COV \
        --cov=$FRAUD_COV \
        --cov=$PATTERNS_COV \
        --cov-report=html:${VERIFICATION_DIR}/htmlcov_combined \
        --cov-report=json:${VERIFICATION_DIR}/coverage.json \
        --cov-report=term > "${VERIFICATION_DIR}/combined_coverage.txt" 2>&1
    
    local combined_coverage=$(grep "TOTAL" "${VERIFICATION_DIR}/combined_coverage.txt" | awk '{print $NF}')
    print_success "Combined coverage: $combined_coverage"
    
    echo ""
    
    # Step 4: Test Statistics
    print_header "Step 4: Test Statistics"
    
    print_info "Collecting test statistics..."
    local test_count=$(pytest \
        $STREAMING_TESTS \
        $AML_TESTS \
        $COMPLIANCE_TESTS \
        $FRAUD_TESTS \
        $PATTERNS_TESTS \
        --collect-only -q 2>&1 | tail -1)
    
    print_success "Total tests: $test_count"
    
    # Measure execution time
    print_info "Measuring execution time..."
    local start_time=$(date +%s)
    pytest \
        $STREAMING_TESTS \
        $AML_TESTS \
        $COMPLIANCE_TESTS \
        $FRAUD_TESTS \
        $PATTERNS_TESTS \
        -v > /dev/null 2>&1
    local end_time=$(date +%s)
    local execution_time=$((end_time - start_time))
    
    print_success "Execution time: ${execution_time}s"
    
    echo ""
    
    # Update report with statistics
    cat >> "$REPORT_FILE" << EOF

---

## Test Statistics

- **Total Tests:** $test_count
- **Combined Coverage:** $combined_coverage
- **Total Execution Time:** ${execution_time}s
- **Average Test Time:** $((execution_time * 1000 / ${test_count%% *}))ms

---

## Coverage Reports

- Combined: \`${VERIFICATION_DIR}/htmlcov_combined/index.html\`
- Streaming: \`${VERIFICATION_DIR}/htmlcov_streaming/index.html\`
- AML: \`${VERIFICATION_DIR}/htmlcov_aml/index.html\`
- Compliance: \`${VERIFICATION_DIR}/htmlcov_compliance/index.html\`
- Fraud: \`${VERIFICATION_DIR}/htmlcov_fraud/index.html\`
- Patterns: \`${VERIFICATION_DIR}/htmlcov_patterns/index.html\`

---

## Summary

EOF
    
    # Determine overall status
    local all_passed=true
    for module in Streaming AML Compliance Fraud Patterns; do
        if [[ "${coverage_results[$module]}" == "FAIL" ]] || [[ "${determinism_results[$module]}" == "FAIL" ]]; then
            all_passed=false
            break
        fi
    done
    
    if $all_passed; then
        echo "**Overall Status:** ✅ PASS" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        echo "All modules passed coverage and determinism verification." >> "$REPORT_FILE"
        print_header "Verification Complete: PASS"
        print_success "All modules passed!"
    else
        echo "**Overall Status:** ❌ FAIL" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        echo "Some modules failed verification. See details above." >> "$REPORT_FILE"
        print_header "Verification Complete: FAIL"
        print_error "Some modules failed. Check report for details."
    fi
    
    echo ""
    print_info "Full report: $REPORT_FILE"
    print_info "HTML coverage: ${VERIFICATION_DIR}/htmlcov_combined/index.html"
    
    # Open HTML report (optional)
    if command -v open &> /dev/null; then
        print_info "Opening HTML coverage report..."
        open "${VERIFICATION_DIR}/htmlcov_combined/index.html"
    fi
}

# Run main function
main "$@"

# Made with Bob
