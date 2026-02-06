#!/usr/bin/env bash
# File: run_integration_tests.sh
# Created: 2026-01-28
# Purpose: Run integration tests for HCD + JanusGraph stack

set -euo pipefail

# Color codes
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Configuration
TESTS_DIR="${PROJECT_ROOT}/tests/integration"
REPORTS_DIR="${PROJECT_ROOT}/test-reports"
VENV_DIR="${PROJECT_ROOT}/.venv-integration"

# Test configuration
PYTEST_ARGS="${PYTEST_ARGS:---verbose --tb=short --color=yes}"
COVERAGE_THRESHOLD="${COVERAGE_THRESHOLD:-80}"
TIMEOUT="${TIMEOUT:-300}"

#######################################
# Print colored message
# Arguments:
#   $1 - Color code
#   $2 - Message
#######################################
print_message() {
    local color="$1"
    local message="$2"
    echo -e "${color}${message}${NC}"
}

#######################################
# Print section header
# Arguments:
#   $1 - Section name
#######################################
print_header() {
    local section="$1"
    echo ""
    print_message "${BLUE}" "=========================================="
    print_message "${BLUE}" "  ${section}"
    print_message "${BLUE}" "=========================================="
    echo ""
}

#######################################
# Check if services are running
#######################################
check_services() {
    print_header "Checking Services"
    
    local services=("hcd-server:9042" "janusgraph-server:8182" "grafana:3001" "prometheus:9090")
    local all_running=true
    
    for service in "${services[@]}"; do
        IFS=':' read -ra parts <<< "${service}"
        local name="${parts[0]}"
        local port="${parts[1]}"
        
        if nc -z localhost "${port}" 2>/dev/null; then
            print_message "${GREEN}" "✓ ${name} is running on port ${port}"
        else
            print_message "${RED}" "✗ ${name} is NOT running on port ${port}"
            all_running=false
        fi
    done
    
    if [[ "${all_running}" == "false" ]]; then
        print_message "${RED}" "ERROR: Not all services are running"
        print_message "${YELLOW}" "Start services with: docker-compose up -d"
        exit 1
    fi
    
    print_message "${GREEN}" "All services are running"
}

#######################################
# Setup Python virtual environment
#######################################
setup_venv() {
    print_header "Setting Up Python Environment"
    
    if [[ ! -d "${VENV_DIR}" ]]; then
        print_message "${YELLOW}" "Creating virtual environment..."
        python3 -m venv "${VENV_DIR}"
    fi
    
    # Activate virtual environment
    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate"
    
    # Upgrade pip
    print_message "${YELLOW}" "Upgrading pip..."
    pip install --quiet --upgrade pip
    
    # Install requirements
    print_message "${YELLOW}" "Installing test requirements..."
    pip install --quiet -r "${TESTS_DIR}/requirements.txt"
    
    print_message "${GREEN}" "Python environment ready"
}

#######################################
# Create reports directory
#######################################
setup_reports() {
    print_header "Setting Up Reports Directory"
    
    mkdir -p "${REPORTS_DIR}"
    
    print_message "${GREEN}" "Reports directory: ${REPORTS_DIR}"
}

#######################################
# Run integration tests
#######################################
run_tests() {
    print_header "Running Integration Tests"
    
    cd "${PROJECT_ROOT}"
    
    # Run pytest with coverage
    print_message "${YELLOW}" "Executing tests..."
    
    # shellcheck disable=SC2086
    pytest ${PYTEST_ARGS} \
        --cov="${PROJECT_ROOT}/src" \
        --cov-report=html:"${REPORTS_DIR}/coverage" \
        --cov-report=term-missing \
        --cov-report=xml:"${REPORTS_DIR}/coverage.xml" \
        --junit-xml="${REPORTS_DIR}/junit.xml" \
        --timeout="${TIMEOUT}" \
        "${TESTS_DIR}/test_full_stack.py" \
        || {
            print_message "${RED}" "Tests failed!"
            return 1
        }
    
    print_message "${GREEN}" "Tests completed successfully"
}

#######################################
# Generate test report
#######################################
generate_report() {
    print_header "Generating Test Report"
    
    local report_file="${REPORTS_DIR}/test_summary.txt"
    
    {
        echo "Integration Test Report"
        echo "======================="
        echo ""
        echo "Date: $(date)"
        echo "Project: HCD + JanusGraph"
        echo ""
        echo "Test Results:"
        echo "-------------"
        
        if [[ -f "${REPORTS_DIR}/junit.xml" ]]; then
            # Parse JUnit XML for summary
            local tests=$(grep -o 'tests="[0-9]*"' "${REPORTS_DIR}/junit.xml" | head -1 | grep -o '[0-9]*')
            local failures=$(grep -o 'failures="[0-9]*"' "${REPORTS_DIR}/junit.xml" | head -1 | grep -o '[0-9]*')
            local errors=$(grep -o 'errors="[0-9]*"' "${REPORTS_DIR}/junit.xml" | head -1 | grep -o '[0-9]*')
            
            echo "Total Tests: ${tests:-0}"
            echo "Failures: ${failures:-0}"
            echo "Errors: ${errors:-0}"
            echo "Passed: $((tests - failures - errors))"
        fi
        
        echo ""
        echo "Coverage Report: ${REPORTS_DIR}/coverage/index.html"
        echo "JUnit Report: ${REPORTS_DIR}/junit.xml"
        
    } > "${report_file}"
    
    cat "${report_file}"
    
    print_message "${GREEN}" "Report saved to: ${report_file}"
}

#######################################
# Cleanup
#######################################
cleanup() {
    print_header "Cleanup"
    
    # Deactivate virtual environment if active
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        deactivate 2>/dev/null || true
    fi
    
    print_message "${GREEN}" "Cleanup complete"
}

#######################################
# Main execution
#######################################
main() {
    print_message "${BLUE}" "Integration Test Runner"
    print_message "${BLUE}" "======================="
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    # Check prerequisites
    if ! command -v python3 &> /dev/null; then
        print_message "${RED}" "ERROR: python3 is not installed"
        exit 1
    fi
    
    if ! command -v nc &> /dev/null; then
        print_message "${YELLOW}" "WARNING: netcat (nc) is not installed, skipping service checks"
    else
        check_services
    fi
    
    # Setup environment
    setup_venv
    setup_reports
    
    # Run tests
    if run_tests; then
        generate_report
        print_message "${GREEN}" "✓ All integration tests passed!"
        exit 0
    else
        print_message "${RED}" "✗ Integration tests failed"
        exit 1
    fi
}

# Run main function
main "$@"

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
