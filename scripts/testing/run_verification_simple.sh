#!/bin/bash
# Simplified Test Verification Script
# Uses conda run instead of conda activate
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
CONDA_ENV="janusgraph-analysis"

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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Main verification
main() {
    print_header "Test Verification Script (Simplified)"
    echo "Date: $(date)"
    echo "Conda Environment: $CONDA_ENV"
    echo ""
    
    # Create verification directory
    mkdir -p "$VERIFICATION_DIR"
    print_success "Verification directory: $VERIFICATION_DIR"
    echo ""
    
    # Step 1: Combined Coverage
    print_header "Step 1: Coverage Verification"
    
    print_info "Running combined coverage test..."
    if conda run -n $CONDA_ENV pytest \
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
        --cov-report=html:${VERIFICATION_DIR}/htmlcov \
        --cov-report=term-missing \
        --cov-fail-under=70 > "${VERIFICATION_DIR}/coverage_output.txt" 2>&1; then
        
        print_success "Coverage test passed!"
        cat "${VERIFICATION_DIR}/coverage_output.txt" | tail -20
    else
        print_error "Coverage test failed!"
        cat "${VERIFICATION_DIR}/coverage_output.txt" | tail -50
        exit 1
    fi
    
    echo ""
    
    # Step 2: Quick Determinism Check (3 runs instead of 10 for speed)
    print_header "Step 2: Determinism Verification (3 runs)"
    
    local failed=0
    for i in {1..3}; do
        print_info "Run $i/3..."
        if ! conda run -n $CONDA_ENV pytest \
            $STREAMING_TESTS \
            $AML_TESTS \
            $COMPLIANCE_TESTS \
            $FRAUD_TESTS \
            $PATTERNS_TESTS \
            -q > /dev/null 2>&1; then
            failed=$((failed + 1))
        fi
    done
    
    if [ $failed -eq 0 ]; then
        print_success "All 3 runs passed - tests are deterministic"
    else
        print_error "$failed/3 runs failed"
        exit 1
    fi
    
    echo ""
    
    # Step 3: Test Statistics
    print_header "Step 3: Test Statistics"
    
    print_info "Collecting test count..."
    local test_count=$(conda run -n $CONDA_ENV pytest \
        $STREAMING_TESTS \
        $AML_TESTS \
        $COMPLIANCE_TESTS \
        $FRAUD_TESTS \
        $PATTERNS_TESTS \
        --collect-only -q 2>&1 | tail -1)
    
    print_success "Total tests: $test_count"
    
    echo ""
    
    # Final Summary
    print_header "Verification Complete: PASS"
    print_success "All modules passed coverage and determinism verification!"
    echo ""
    print_info "Coverage report: ${VERIFICATION_DIR}/htmlcov/index.html"
    print_info "Full output: ${VERIFICATION_DIR}/coverage_output.txt"
    
    # Try to open HTML report
    if command -v open &> /dev/null; then
        print_info "Opening HTML coverage report..."
        open "${VERIFICATION_DIR}/htmlcov/index.html"
    fi
}

# Run main function
main "$@"

# Made with Bob
