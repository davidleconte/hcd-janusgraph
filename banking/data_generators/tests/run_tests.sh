#!/bin/bash
# Test Runner Script
# ==================
# 
# Comprehensive test execution script for data generators
# 
# Author: IBM Bob
# Date: 2026-01-28

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Data Generators Test Suite"
echo "=========================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found${NC}"
    echo "Please install test dependencies:"
    echo "  pip install -r tests/requirements-test.txt"
    exit 1
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"
VERBOSE="${2:-}"

echo "Test Type: $TEST_TYPE"
echo ""

# Function to run tests
run_tests() {
    local test_path=$1
    local test_name=$2
    local markers=$3
    
    echo -e "${YELLOW}Running $test_name...${NC}"
    
    if [ -n "$markers" ]; then
        if [ "$VERBOSE" = "-v" ] || [ "$VERBOSE" = "--verbose" ]; then
            pytest "$test_path" -m "$markers" -v --tb=short
        else
            pytest "$test_path" -m "$markers" --tb=short
        fi
    else
        if [ "$VERBOSE" = "-v" ] || [ "$VERBOSE" = "--verbose" ]; then
            pytest "$test_path" -v --tb=short
        else
            pytest "$test_path" --tb=short
        fi
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $test_name passed${NC}"
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        return 1
    fi
    echo ""
}

# Change to tests directory
cd "$(dirname "$0")"

case $TEST_TYPE in
    "smoke")
        echo "Running smoke tests only..."
        run_tests "." "Smoke Tests" "not slow and not integration and not benchmark"
        ;;
    
    "unit")
        echo "Running unit tests..."
        run_tests "test_core/" "Core Generator Tests" "not slow and not integration"
        run_tests "test_events/" "Event Generator Tests" "not slow and not integration"
        run_tests "test_patterns/" "Pattern Generator Tests" "not slow and not integration"
        run_tests "test_orchestration/" "Orchestration Tests" "not slow and not integration"
        ;;
    
    "integration")
        echo "Running integration tests..."
        run_tests "test_integration/" "Integration Tests" "integration"
        ;;
    
    "performance")
        echo "Running performance benchmarks..."
        run_tests "test_performance/" "Performance Benchmarks" "benchmark or slow"
        ;;
    
    "fast")
        echo "Running fast tests only (no slow, integration, or benchmark)..."
        run_tests "." "Fast Tests" "not slow and not integration and not benchmark"
        ;;
    
    "all")
        echo "Running all tests..."
        run_tests "." "All Tests" ""
        ;;
    
    "coverage")
        echo "Running tests with coverage..."
        pytest . --cov=banking.data_generators --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo ""
        echo "Usage: ./run_tests.sh [TEST_TYPE] [VERBOSE]"
        echo ""
        echo "TEST_TYPE options:"
        echo "  smoke       - Run smoke tests only (quick validation)"
        echo "  unit        - Run unit tests (default, no integration/performance)"
        echo "  integration - Run integration tests (requires services)"
        echo "  performance - Run performance benchmarks"
        echo "  fast        - Run fast tests only"
        echo "  all         - Run all tests"
        echo "  coverage    - Run tests with coverage report"
        echo ""
        echo "VERBOSE options:"
        echo "  -v, --verbose - Show detailed test output"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh smoke"
        echo "  ./run_tests.sh unit -v"
        echo "  ./run_tests.sh coverage"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo -e "${GREEN}Test execution complete!${NC}"
echo "=========================================="

# Made with Bob
