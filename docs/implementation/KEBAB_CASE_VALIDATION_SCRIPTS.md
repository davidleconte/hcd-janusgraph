# Kebab-Case Validation Scripts

**Date:** 2026-02-11
**Status:** Planning
**Related:** [`KEBAB_CASE_REMEDIATION_PLAN.md`](KEBAB_CASE_REMEDIATION_PLAN.md)

---

## Overview

This document provides validation scripts and CI/CD integration for enforcing kebab-case naming conventions across all documentation files.

---

## Table of Contents

1. [Validation Script](#validation-script)
2. [Renaming Script](#renaming-script)
3. [Reference Update Script](#reference-update-script)
4. [CI/CD Integration](#cicd-integration)
5. [Pre-commit Hook](#pre-commit-hook)

---

## Validation Script

### scripts/validation/validate-kebab-case.sh

```bash
#!/bin/bash
# =============================================================================
# Kebab-Case Validation Script
# =============================================================================
# Purpose: Validate that all documentation files follow kebab-case naming
# Usage:   ./scripts/validation/validate-kebab-case.sh [--strict] [--fix]
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
WARNINGS=0

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
)

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

# Function to convert to kebab-case
to_kebab_case() {
    local filename="$1"
    
    echo "$filename" | \
        sed 's/_/-/g' | \
        sed 's/\([A-Z]\)/-\1/g' | \
        sed 's/^-//' | \
        tr '[:upper:]' '[:lower:]' | \
        sed 's/--/-/g'
}

echo "🔍 Validating documentation file naming conventions..."
echo ""

# Find all markdown files
while IFS= read -r -d '' file; do
    # Get relative path
    rel_path="${file#$PROJECT_ROOT/}"
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
```

---

## Renaming Script

### scripts/maintenance/rename-to-kebab-case.sh

```bash
#!/bin/bash
# =============================================================================
# Kebab-Case Renaming Script
# =============================================================================
# Purpose: Rename all documentation files to kebab-case format
# Usage:   ./scripts/maintenance/rename-to-kebab-case.sh [--dry-run]
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
RENAMED=0

# Allowed exceptions
EXCEPTIONS=(
    "README.md"
    "LICENSE"
    "CHANGELOG.md"
    "CONTRIBUTING.md"
    "CODE_OF_CONDUCT.md"
    "SECURITY.md"
    "AGENTS.md"
    "QUICKSTART.md"
)

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

# Function to convert to kebab-case
to_kebab_case() {
    local filename="$1"
    
    echo "$filename" | \
        sed 's/_/-/g' | \
        sed 's/\([A-Z]\)/-\1/g' | \
        sed 's/^-//' | \
        tr '[:upper:]' '[:lower:]' | \
        sed 's/--/-/g'
}

if $DRY_RUN; then
    echo -e "${YELLOW}🔍 DRY RUN MODE${NC} - No files will be renamed"
else
    echo -e "${BLUE}📝 RENAMING FILES${NC} - Git history will be preserved"
fi
echo ""

cd "$PROJECT_ROOT"

# Find and rename files
while IFS= read -r -d '' file; do
    rel_path="${file#$PROJECT_ROOT/}"
    
    # Skip exceptions
    if is_exception "$rel_path"; then
        continue
    fi
    
    filename=$(basename "$file")
    dirname=$(dirname "$file")
    
    # Check if needs renaming
    if [[ "$filename" =~ [A-Z_] ]]; then
        new_filename=$(to_kebab_case "$filename")
        new_path="$dirname/$new_filename"
        
        if [ "$file" != "$new_path" ]; then
            RENAMED=$((RENAMED + 1))
            
            if $DRY_RUN; then
                echo -e "${YELLOW}WOULD RENAME:${NC}"
                echo "  From: $rel_path"
                echo "  To:   ${new_path#$PROJECT_ROOT/}"
                echo ""
            else
                echo -e "${GREEN}RENAMING:${NC}"
                echo "  From: $rel_path"
                echo "  To:   ${new_path#$PROJECT_ROOT/}"
                
                # Use git mv to preserve history
                git mv "$file" "$new_path"
                echo ""
            fi
        fi
    fi
done < <(find "$PROJECT_ROOT" -name "*.md" -type f -print0)

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if $DRY_RUN; then
    echo -e "${YELLOW}DRY RUN COMPLETE${NC}: Would rename $RENAMED file(s)"
    echo ""
    echo "To execute renames, run without --dry-run:"
    echo "  ./scripts/maintenance/rename-to-kebab-case.sh"
else
    echo -e "${GREEN}✅ COMPLETE${NC}: Renamed $RENAMED file(s)"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./scripts/maintenance/update-doc-references.sh"
    echo "  2. Commit changes: git commit -m 'docs: rename files to kebab-case'"
fi
echo ""
```

---

## Reference Update Script

### scripts/maintenance/update-doc-references.sh

```bash
#!/bin/bash
# =============================================================================
# Documentation Reference Update Script
# =============================================================================
# Purpose: Update all references to renamed documentation files
# Usage:   ./scripts/maintenance/update-doc-references.sh [--dry-run]
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Mapping of old names to new names (generated from KEBAB_CASE_REMEDIATION_PLAN.md)
declare -A RENAMES=(
    # Root directory
    ["CODE_QUALITY_BEST_PRACTICES_REVIEW_2026-02-11.md"]="code-quality-best-practices-review-2026-02-11.md"
    ["CODE_QUALITY_IMPLEMENTATION_PLAN_2026-02-11.md"]="code-quality-implementation-plan-2026-02-11.md"
    ["CODEBASE_REVIEW_2026-02-11.md"]="codebase-review-2026-02-11.md"
    ["SECURITY_REMEDIATION_PLAN_2026-02-11.md"]="security-remediation-plan-2026-02-11.md"
    ["TOOLING_STANDARDS_UPDATE_2026-02-11.md"]="tooling-standards-update-2026-02-11.md"
    
    # docs/ directory
    ["BANKING_USE_CASES_TECHNICAL_SPEC.md"]="banking-use-cases-technical-spec.md"
    ["BANKING_USE_CASES_TECHNICAL_SPEC_COMPLETE.md"]="banking-use-cases-technical-spec-complete.md"
    ["DEMO_SETUP_GUIDE.md"]="demo-setup-guide.md"
    ["DOCS_OPTIMIZATION_PLAN.md"]="docs-optimization-plan.md"
    
    # docs/banking/
    ["ENTERPRISE_ADVANCED_PATTERNS_PLAN.md"]="enterprise-advanced-patterns-plan.md"
    ["PHASE5_IMPLEMENTATION_COMPLETE.md"]="phase-5-implementation-complete.md"
    ["PHASE5_VECTOR_AI_FOUNDATION.md"]="phase-5-vector-ai-foundation.md"
    ["USER_GUIDE.md"]="user-guide.md"
    
    # Add more mappings as needed...
)

UPDATES=0

if $DRY_RUN; then
    echo -e "${YELLOW}🔍 DRY RUN MODE${NC} - No files will be modified"
else
    echo -e "${GREEN}📝 UPDATING REFERENCES${NC}"
fi
echo ""

cd "$PROJECT_ROOT"

# Update references in all markdown files
for old_name in "${!RENAMES[@]}"; do
    new_name="${RENAMES[$old_name]}"
    
    # Escape special characters for sed
    old_escaped=$(echo "$old_name" | sed 's/[.[\*^$]/\\&/g')
    new_escaped=$(echo "$new_name" | sed 's/[.[\*^$]/\\&/g')
    
    # Find files containing the old reference
    if grep -r -l "$old_name" --include="*.md" . 2>/dev/null; then
        if $DRY_RUN; then
            echo -e "${YELLOW}WOULD UPDATE:${NC} $old_name → $new_name"
            grep -r -l "$old_name" --include="*.md" . 2>/dev/null | sed 's/^/  /'
            echo ""
        else
            echo -e "${GREEN}UPDATING:${NC} $old_name → $new_name"
            
            # Update references
            find . -name "*.md" -type f -exec sed -i '' "s/$old_escaped/$new_escaped/g" {} +
            
            UPDATES=$((UPDATES + 1))
            echo ""
        fi
    fi
done

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if $DRY_RUN; then
    echo -e "${YELLOW}DRY RUN COMPLETE${NC}: Would update references in multiple files"
else
    echo -e "${GREEN}✅ COMPLETE${NC}: Updated $UPDATES reference(s)"
    echo ""
    echo "Next steps:"
    echo "  1. Review changes: git diff"
    echo "  2. Run validation: ./scripts/validation/validate-kebab-case.sh"
    echo "  3. Commit: git commit -am 'docs: update references after kebab-case rename'"
fi
echo ""
```

---

## CI/CD Integration

### .github/workflows/validate-doc-naming.yml

```yaml
name: Validate Documentation Naming

on:
  pull_request:
    paths:
      - 'docs/**/*.md'
      - '*.md'
  push:
    branches:
      - main
    paths:
      - 'docs/**/*.md'
      - '*.md'

jobs:
  validate-kebab-case:
    name: Check Kebab-Case Naming
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Validate file naming
        run: |
          chmod +x scripts/validation/validate-kebab-case.sh
          ./scripts/validation/validate-kebab-case.sh
      
      - name: Comment on PR (if violations found)
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '❌ **Documentation Naming Violation**\n\n' +
                    'Some documentation files do not follow kebab-case naming conventions.\n\n' +
                    'Please run:\n' +
                    '```bash\n' +
                    './scripts/maintenance/rename-to-kebab-case.sh\n' +
                    './scripts/maintenance/update-doc-references.sh\n' +
                    '```\n\n' +
                    'See [documentation-standards.md](docs/documentation-standards.md) for details.'
            })
```

---

## Pre-commit Hook

### .pre-commit-config.yaml (addition)

```yaml
  - repo: local
    hooks:
      - id: validate-kebab-case
        name: Validate Kebab-Case Naming
        entry: scripts/validation/validate-kebab-case.sh
        language: script
        files: \.md$
        pass_filenames: false
```

---

## Usage Examples

### Validate Current State

```bash
# Check for violations
./scripts/validation/validate-kebab-case.sh

# Output:
# 🔍 Validating documentation file naming conventions...
# 
# ❌ VIOLATION: docs/BANKING_USE_CASES_TECHNICAL_SPEC.md
#    Suggested: docs/banking-use-cases-technical-spec.md
# 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ❌ FAILED: Found 100 file(s) violating kebab-case naming
```

### Dry Run Rename

```bash
# Preview what would be renamed
./scripts/maintenance/rename-to-kebab-case.sh --dry-run

# Output:
# 🔍 DRY RUN MODE - No files will be renamed
# 
# WOULD RENAME:
#   From: docs/BANKING_USE_CASES_TECHNICAL_SPEC.md
#   To:   docs/banking-use-cases-technical-spec.md
```

### Execute Rename

```bash
# Rename all files
./scripts/maintenance/rename-to-kebab-case.sh

# Update references
./scripts/maintenance/update-doc-references.sh

# Validate
./scripts/validation/validate-kebab-case.sh

# Commit
git commit -m "docs: enforce kebab-case naming conventions"
```

---

## Script Locations

All scripts should be created in the following locations:

```
scripts/
├── validation/
│   └── validate-kebab-case.sh          # Validation script
└── maintenance/
    ├── rename-to-kebab-case.sh         # Renaming script
    └── update-doc-references.sh        # Reference update script

.github/
└── workflows/
    └── validate-doc-naming.yml         # CI/CD workflow

.pre-commit-config.yaml                 # Pre-commit hook config
```

---

## Testing

### Test Validation Script

```bash
# Should pass (no violations)
./scripts/validation/validate-kebab-case.sh
echo $?  # Should be 0

# Create test violation
touch docs/TEST_VIOLATION.md

# Should fail
./scripts/validation/validate-kebab-case.sh
echo $?  # Should be 1

# Cleanup
rm docs/TEST_VIOLATION.md
```

### Test Renaming Script

```bash
# Create test file
mkdir -p /tmp/test-kebab
cd /tmp/test-kebab
git init
touch TEST_FILE.md
git add TEST_FILE.md
git commit -m "test"

# Test dry run
./scripts/maintenance/rename-to-kebab-case.sh --dry-run

# Test actual rename
./scripts/maintenance/rename-to-kebab-case.sh

# Verify git history preserved
git log --follow test-file.md
```

---

## Troubleshooting

### Issue: Script not executable

```bash
chmod +x scripts/validation/validate-kebab-case.sh
chmod +x scripts/maintenance/rename-to-kebab-case.sh
chmod +x scripts/maintenance/update-doc-references.sh
```

### Issue: sed command differs on macOS vs Linux

The scripts use `sed -i ''` for macOS. For Linux, change to `sed -i`.

### Issue: Git mv fails

Ensure working directory is clean:

```bash
git status
git stash  # If needed
```

---

## References

- [`KEBAB_CASE_REMEDIATION_PLAN.md`](KEBAB_CASE_REMEDIATION_PLAN.md) - Main remediation plan
- [`docs/documentation-standards.md`](../documentation-standards.md) - Naming standards
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pre-commit Framework](https://pre-commit.com/)

---

**Status:** Ready for implementation
**Next Step:** Create scripts in Code mode