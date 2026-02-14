#!/usr/bin/env bash
# File: scripts/validation/validate_credentials.sh
# Purpose: Validate that default/placeholder credentials are not used in production
# Created: 2026-02-06
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  Credential Validation Check"
echo "=========================================="

ERRORS=0
WARNINGS=0

# Function to check for placeholder values
check_placeholder() {
    local file=$1
    local pattern=$2
    local description=$3

    if [ -f "$file" ]; then
        if grep -q "$pattern" "$file" 2>/dev/null; then
            echo -e "${RED}[ERROR]${NC} $description found in $file"
            ((ERRORS++))
            return 1
        fi
    fi
    return 0
}

# Function to check for default passwords
check_default_password() {
    local file=$1
    local var_name=$2
    local default_values=("changeit" "password" "admin" "secret" "test" "demo" "YOUR_" "CHANGE_ME" "placeholder")

    if [ -f "$file" ]; then
        for default in "${default_values[@]}"; do
            if grep -qE "^${var_name}=.*${default}" "$file" 2>/dev/null; then
                echo -e "${RED}[ERROR]${NC} Default password '${default}' found for ${var_name} in $file"
                ((ERRORS++))
                return 1
            fi
        done
    fi
    return 0
}

echo ""
echo "Checking .env file..."
echo "-------------------------------------------"

if [ -f ".env" ]; then
    # Check for placeholder patterns
    check_placeholder ".env" "YOUR_SECURE_PASSWORD" "Placeholder password"
    check_placeholder ".env" "CHANGE_THIS" "Placeholder value"
    check_placeholder ".env" "YOUR_.*_HERE" "Placeholder value"

    # Check specific variables for default values
    check_default_password ".env" "JANUSGRAPH_PASSWORD"
    check_default_password ".env" "HCD_KEYSTORE_PASSWORD"
    check_default_password ".env" "OPENSEARCH_PASSWORD"
    check_default_password ".env" "VAULT_TOKEN"
    check_default_password ".env" "GRAFANA_ADMIN_PASSWORD"
    check_default_password ".env" "POSTGRES_PASSWORD"

    # Check for empty critical variables
    CRITICAL_VARS=("JANUSGRAPH_PASSWORD" "HCD_KEYSTORE_PASSWORD")
    for var in "${CRITICAL_VARS[@]}"; do
        value=$(grep "^${var}=" .env 2>/dev/null | cut -d'=' -f2-)
        if [ -z "$value" ]; then
            echo -e "${YELLOW}[WARNING]${NC} ${var} is empty or not set"
            ((WARNINGS++))
        fi
    done
else
    echo -e "${YELLOW}[WARNING]${NC} .env file not found - using .env.example as reference"
    ((WARNINGS++))
fi

echo ""
echo "Checking docker-compose files..."
echo "-------------------------------------------"

# Check for hardcoded credentials in compose files
for compose_file in config/compose/docker-compose*.yml; do
    if [ -f "$compose_file" ]; then
        # Check for hardcoded passwords (not using environment variables)
        if grep -qE "password:\s*['\"]?(changeit|password|admin|secret)['\"]?" "$compose_file" 2>/dev/null; then
            echo -e "${RED}[ERROR]${NC} Hardcoded default password in $compose_file"
            ((ERRORS++))
        fi
    fi
done

echo ""
echo "Checking configuration files..."
echo "-------------------------------------------"

# Check JanusGraph configs
for config_file in config/janusgraph/*.properties config/janusgraph/*.yaml; do
    if [ -f "$config_file" ]; then
        if grep -qE "password\s*=\s*(changeit|password|admin)" "$config_file" 2>/dev/null; then
            echo -e "${RED}[ERROR]${NC} Default password in $config_file"
            ((ERRORS++))
        fi
    fi
done

echo ""
echo "=========================================="
echo "  Validation Summary"
echo "=========================================="

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}FAILED${NC}: $ERRORS error(s) found"
    echo ""
    echo "Please update the following before deploying to production:"
    echo "  1. Replace all placeholder passwords in .env"
    echo "  2. Use strong, unique passwords (min 16 characters)"
    echo "  3. Never use default credentials like 'changeit' or 'password'"
    echo ""
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}PASSED with warnings${NC}: $WARNINGS warning(s)"
    echo ""
    echo "Review warnings above before production deployment."
    exit 0
else
    echo -e "${GREEN}PASSED${NC}: No credential issues found"
    exit 0
fi
