#!/bin/bash
# Fix remaining broken documentation links
# Created: 2026-02-11
# Week 5 Day 26

set -euo pipefail

echo "🔗 Fixing Remaining Documentation Links"
echo "========================================"
echo ""

# Track changes
CHANGES=0

# Function to fix links in a file
fix_link() {
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

# README.md - Update remediation links to current implementation docs
echo "1️⃣  Fixing README.md remediation links..."
fix_link "README.md" "docs/implementation/remediation/PRODUCTION_READINESS_ROADMAP.md" "docs/implementation/PRODUCTION_READINESS_AUDIT_2026.md"
fix_link "README.md" "docs/implementation/remediation/WEEK1_FINAL_REPORT.md" "docs/implementation/WEEK1_COMPLETE_SUMMARY_2026-02-11.md"
fix_link "README.md" "docs/implementation/remediation/WEEK2_COMPLETE.md" "docs/implementation/WEEK2_DAY12_COMPLETE_SUMMARY.md"
fix_link "README.md" "docs/implementation/remediation/WEEK3-4_QUICKSTART.md" "docs/implementation/WEEK3_COMPLETE_SUMMARY.md"

# QUICKSTART.md - Update remediation links
echo "2️⃣  Fixing QUICKSTART.md remediation links..."
fix_link "QUICKSTART.md" "docs/implementation/remediation/WEEK1_FINAL_REPORT.md" "docs/implementation/WEEK1_COMPLETE_SUMMARY_2026-02-11.md"
fix_link "QUICKSTART.md" "docs/implementation/remediation/WEEK2_COMPLETE.md" "docs/implementation/WEEK2_DAY12_COMPLETE_SUMMARY.md"
fix_link "QUICKSTART.md" "docs/implementation/remediation/WEEK3-4_QUICKSTART.md" "docs/implementation/WEEK3_COMPLETE_SUMMARY.md"
fix_link "QUICKSTART.md" "docs/implementation/remediation/PRODUCTION_READINESS_ROADMAP.md" "docs/implementation/PRODUCTION_READINESS_AUDIT_2026.md"

# AGENTS.md - Remove network-isolation-analysis reference (deprecated)
echo "3️⃣  Fixing AGENTS.md..."
fix_link "AGENTS.md" "docs/implementation/remediation/network-isolation-analysis.md" "config/compose/docker-compose.full.yml"

# banking/aml/README.md - Remove setup guide references (deprecated)
echo "4️⃣  Fixing banking/aml/README.md..."
if [ -f "banking/aml/README.md" ]; then
    if grep -q "\.\./docs/banking/setup/01_AML_PHASE1_SETUP.md" "banking/aml/README.md" 2>/dev/null; then
        # Remove the entire line referencing the deprecated setup guide
        sed -i '' '/01_AML_PHASE1_SETUP.md/d' "banking/aml/README.md"
        echo "✅ Removed deprecated setup reference from banking/aml/README.md"
        CHANGES=$((CHANGES + 1))
    fi
fi

# banking/notebooks/README.md - Remove deprecated references
echo "5️⃣  Fixing banking/notebooks/README.md..."
if [ -f "banking/notebooks/README.md" ]; then
    # Remove PRODUCTION_SYSTEM_VERIFICATION references
    if grep -q "PRODUCTION_SYSTEM_VERIFICATION.md" "banking/notebooks/README.md" 2>/dev/null; then
        sed -i '' '/PRODUCTION_SYSTEM_VERIFICATION.md/d' "banking/notebooks/README.md"
        echo "✅ Removed deprecated verification references from banking/notebooks/README.md"
        CHANGES=$((CHANGES + 1))
    fi
    
    # Remove PRODUCTION_DEPLOYMENT_GUIDE references
    if grep -q "PRODUCTION_DEPLOYMENT_GUIDE.md" "banking/notebooks/README.md" 2>/dev/null; then
        sed -i '' '/PRODUCTION_DEPLOYMENT_GUIDE.md/d' "banking/notebooks/README.md"
        echo "✅ Removed deprecated deployment guide references from banking/notebooks/README.md"
        CHANGES=$((CHANGES + 1))
    fi
fi

# banking/streaming/README.md - Remove deprecated references
echo "6️⃣  Fixing banking/streaming/README.md..."
if [ -f "banking/streaming/README.md" ]; then
    if grep -q "docs/archive/streaming_summary.md" "banking/streaming/README.md" 2>/dev/null; then
        sed -i '' '/docs\/archive\/streaming_summary.md/d' "banking/streaming/README.md"
        echo "✅ Removed deprecated streaming summary reference"
        CHANGES=$((CHANGES + 1))
    fi
    
    if grep -q "src/python/client/README.md" "banking/streaming/README.md" 2>/dev/null; then
        sed -i '' '/src\/python\/client\/README.md/d' "banking/streaming/README.md"
        echo "✅ Removed deprecated client README reference"
        CHANGES=$((CHANGES + 1))
    fi
fi

echo ""
echo "======================================"
echo "✅ Fixed $CHANGES remaining links"
echo "======================================"

# Made with Bob
