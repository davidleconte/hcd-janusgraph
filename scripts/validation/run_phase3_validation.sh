#!/bin/bash
# Phase 3 Complete Validation Suite
# Runs all security, performance, and compliance validations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Determine project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 3 Validation Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Project Root: $PROJECT_ROOT"
echo "Start Time: $(date)"
echo ""

# Initialize results
SECURITY_EXIT=0
PERFORMANCE_EXIT=0
COMPLIANCE_EXIT=0

# 1. Security Audit
echo -e "${YELLOW}[1/3] Running Security Audit...${NC}"
echo "--------------------------------------"
if python scripts/security/security_audit_framework.py --full; then
    echo -e "${GREEN}✓ Security audit completed${NC}"
    SECURITY_EXIT=0
else
    echo -e "${RED}✗ Security audit failed${NC}"
    SECURITY_EXIT=$?
fi
echo ""

# 2. Load Testing
echo -e "${YELLOW}[2/3] Running Load Tests...${NC}"
echo "--------------------------------------"
if python tests/performance/load_testing_framework.py \
    --scenario full \
    --duration 300 \
    --concurrent-users 50; then
    echo -e "${GREEN}✓ Load tests completed${NC}"
    PERFORMANCE_EXIT=0
else
    echo -e "${RED}✗ Load tests failed${NC}"
    PERFORMANCE_EXIT=$?
fi
echo ""

# 3. Compliance Audit
echo -e "${YELLOW}[3/3] Running Compliance Audits...${NC}"
echo "--------------------------------------"
if python scripts/compliance/compliance_audit_framework.py --standard all; then
    echo -e "${GREEN}✓ Compliance audits completed${NC}"
    COMPLIANCE_EXIT=0
else
    echo -e "${RED}✗ Compliance audits failed${NC}"
    COMPLIANCE_EXIT=$?
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 3 Validation Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo "End Time: $(date)"
echo ""
echo "Results:"
if [ $SECURITY_EXIT -eq 0 ]; then
    echo -e "  Security Audit:    ${GREEN}✅ PASSED${NC}"
else
    echo -e "  Security Audit:    ${RED}❌ FAILED${NC}"
fi

if [ $PERFORMANCE_EXIT -eq 0 ]; then
    echo -e "  Load Testing:      ${GREEN}✅ PASSED${NC}"
else
    echo -e "  Load Testing:      ${RED}❌ FAILED${NC}"
fi

if [ $COMPLIANCE_EXIT -eq 0 ]; then
    echo -e "  Compliance Audit:  ${GREEN}✅ PASSED${NC}"
else
    echo -e "  Compliance Audit:  ${RED}❌ FAILED${NC}"
fi

echo ""
echo "Reports Location:"
echo "  Security:    docs/implementation/audits/security/"
echo "  Performance: docs/implementation/audits/performance/"
echo "  Compliance:  docs/compliance/audits/"
echo -e "${BLUE}========================================${NC}"

# Exit with error if any validation failed
if [ $SECURITY_EXIT -eq 0 ] && [ $PERFORMANCE_EXIT -eq 0 ] && [ $COMPLIANCE_EXIT -eq 0 ]; then
    echo -e "${GREEN}Overall Status: ✅ ALL VALIDATIONS PASSED${NC}"
    exit 0
else
    echo -e "${RED}Overall Status: ❌ SOME VALIDATIONS FAILED${NC}"
    exit 1
fi

# Made with Bob
