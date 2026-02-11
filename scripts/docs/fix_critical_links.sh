#!/bin/bash
# Fix critical documentation links
# Created: 2026-02-11
# Week 5 Day 26

set -euo pipefail

echo "🔗 Fixing Critical Documentation Links"
echo "======================================"
echo ""

# Track changes
CHANGES=0

# Function to fix links in a file
fix_links() {
    local file=$1
    local pattern=$2
    local replacement=$3
    
    if [ -f "$file" ]; then
        if grep -q "$pattern" "$file" 2>/dev/null; then
            sed -i '' "s|$pattern|$replacement|g" "$file"
            echo "✅ Fixed: $file"
            CHANGES=$((CHANGES + 1))
        fi
    fi
}

# README.md fixes
echo "1️⃣  Fixing README.md..."
fix_links "README.md" "docs/banking/guides/USER_GUIDE.md" "docs/banking/USER_GUIDE.md"
fix_links "README.md" "docs/operations/OPERATIONS_RUNBOOK.md" "docs/operations/operations-runbook.md"

# QUICKSTART.md fixes
echo "2️⃣  Fixing QUICKSTART.md..."
fix_links "QUICKSTART.md" "docs/operations/OPERATIONS_RUNBOOK.md" "docs/operations/operations-runbook.md"

# AGENTS.md fixes
echo "3️⃣  Fixing AGENTS.md..."
fix_links "AGENTS.md" "SETUP.md" "QUICKSTART.md"
fix_links "AGENTS.md" "/docs/SETUP.md" "docs/guides/setup-guide.md"

# banking/aml/README.md fixes
echo "4️⃣  Fixing banking/aml/README.md..."
fix_links "banking/aml/README.md" "\.\./docs/banking/guides/USER_GUIDE.md" "../../docs/banking/USER_GUIDE.md"
fix_links "banking/aml/README.md" "\.\./docs/banking/guides/API_REFERENCE.md" "../../docs/banking/guides/api-reference.md"

# banking/fraud/README.md fixes
echo "5️⃣  Fixing banking/fraud/README.md..."
fix_links "banking/fraud/README.md" "\.\./docs/banking/guides/USER_GUIDE.md" "../../docs/banking/USER_GUIDE.md"
fix_links "banking/fraud/README.md" "\.\./docs/banking/guides/API_REFERENCE.md" "../../docs/banking/guides/api-reference.md"

# banking/notebooks/README.md fixes
echo "6️⃣  Fixing banking/notebooks/README.md..."
fix_links "banking/notebooks/README.md" "\.\./\.\./docs/TROUBLESHOOTING.md" "../../docs/guides/troubleshooting-guide.md"

echo ""
echo "======================================"
echo "✅ Fixed $CHANGES critical links"
echo "======================================"

# Made with Bob
