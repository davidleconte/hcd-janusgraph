#!/bin/bash
# =============================================================================
# Kebab-Case Validation Script
# =============================================================================
# Purpose: Validate that all documentation files follow kebab-case naming
# Usage:   ./scripts/validation/validate-kebab-case.sh
# Exit:    0 if all files comply, 1 if violations found
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
VIOLATIONS=0

# Allowed exceptions (UPPERCASE files at root level)
EXCEPTIONS=(
    "README.md"
    "LICENSE"
    "CHANGELOG.md"
    "CONTRIBUTING.md"
    "CODE_OF_CONDUCT.md"
    "SECURITY.md"
    "AGENTS.md"
    "QUICKSTART.md"
    "FAQ.md"
)

# Directories to exclude
EXCLUDE_DIRS=(
    ".venv"
    ".venv.disabled"
    "vendor"
    ".bob"
    ".git"
    "node_modules"
    ".terraform"
)

# Function to check if path should be excluded
should_exclude() {
    local path="$1"
    for exclude in "${EXCLUDE_DIRS[@]}"; do
        # Match /exclude/ anywhere in path OR exclude at start of path
        if [[ "$path" == *"/$exclude/"* ]] || [[ "$path" == "$exclude/"* ]] || [[ "$path" == "$exclude"* ]]; then
            return 0
        fi
    done
    return 1
}

# Function to check if file is an exception
is_exception() {
    local file="$1"
    local basename=$(basename "$file")
    
    for exception in "${EXCEPTIONS[@]}"; do
        if [[ "$basename" == "$exception" ]]; then
            return 0
        fi
    done
    return 1
}

# Function to check if filename follows kebab-case
is_kebab_case() {
    local filename="$1"
    
    # Remove .md extension
    local name="${filename%.md}"
    
    # Check if contains uppercase letters or underscores
    if [[ "$name" =~ [A-Z_] ]]; then
        return 1
    fi
    
    # Check if starts or ends with hyphen
    if [[ "$name" =~ ^- ]] || [[ "$name" =~ -$ ]]; then
        return 1
    fi
    
    # Check for double hyphens
    if [[ "$name" =~ -- ]]; then
        return 1
    fi
    
    return 0
}

# Function to convert to kebab-case (improved)
to_kebab_case() {
    local filename="$1"
    
    # Convert underscores to hyphens, then lowercase
    echo "$filename" | \
        sed 's/_/-/g' | \
        tr '[:upper:]' '[:lower:]'
}

echo "🔍 Validating documentation file naming conventions..."
echo ""

# Find all markdown files
while IFS= read -r -d '' file; do
    # Get relative path
    rel_path="${file#$PROJECT_ROOT/}"
    
    # Skip excluded directories
    if should_exclude "$rel_path"; then
        continue
    fi
    
    filename=$(basename "$file")
    
    # Skip if exception
    if is_exception "$rel_path"; then
        continue
    fi
    
    # Check if follows kebab-case
    if ! is_kebab_case "$filename"; then
        VIOLATIONS=$((VIOLATIONS + 1))
        suggested=$(to_kebab_case "$filename")
        
        echo -e "${RED}❌ VIOLATION${NC}: $rel_path"
        echo -e "   ${YELLOW}Suggested:${NC} $(dirname "$rel_path")/$suggested"
        echo ""
    fi
done < <(find "$PROJECT_ROOT" -name "*.md" -type f -print0)

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $VIOLATIONS -eq 0 ]; then
    echo -e "${GREEN}✅ SUCCESS${NC}: All documentation files follow kebab-case naming"
    echo ""
    exit 0
else
    echo -e "${RED}❌ FAILED${NC}: Found $VIOLATIONS file(s) violating kebab-case naming"
    echo ""
    echo "To fix automatically, run:"
    echo "  ./scripts/maintenance/rename-to-kebab-case.sh"
    echo ""
    exit 1
fi

# Made with Bob
