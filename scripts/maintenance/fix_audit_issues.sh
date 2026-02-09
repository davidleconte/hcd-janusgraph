#!/bin/bash
# Fix Audit Issues Script
# Addresses all critical and high-priority issues from project structure audit
# Date: 2026-01-29
# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔧 Project Structure Audit Remediation"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track what was done
CHANGES_MADE=()

# ============================================================================
# PHASE 1: SECURITY CLEANUP (CRITICAL)
# ============================================================================

echo "🔒 Phase 1: Security Cleanup"
echo "----------------------------"

# 1.1 Secure vault keys
if [ -f ".vault-keys" ] || [ -f ".vault-keys.bak" ]; then
    echo "  → Securing vault keys..."
    mkdir -p ~/secure-backups/$(basename "$PWD")
    mv .vault-keys* ~/secure-backups/$(basename "$PWD")/ 2>/dev/null || true
    CHANGES_MADE+=("Moved vault keys to ~/secure-backups/$(basename "$PWD")/")
    echo -e "  ${GREEN}✓${NC} Vault keys secured"
else
    echo -e "  ${GREEN}✓${NC} No vault keys found (already secure)"
fi

# 1.2 Move vault data
if [ -d "data/vault" ]; then
    echo "  → Moving vault data..."
    BACKUP_DIR=~/vault-data-backup-$(basename "$PWD")-$(date +%Y%m%d)
    mv data/vault "$BACKUP_DIR"
    CHANGES_MADE+=("Moved vault data to $BACKUP_DIR")
    echo -e "  ${GREEN}✓${NC} Vault data moved to $BACKUP_DIR"
else
    echo -e "  ${GREEN}✓${NC} No vault data found"
fi

# 1.3 Check for .env in git
if git ls-files | grep -q "^\.env$"; then
    echo -e "  ${RED}✗${NC} .env is tracked in git! Run: git rm --cached .env"
    CHANGES_MADE+=("WARNING: .env is in git - needs manual removal")
else
    echo -e "  ${GREEN}✓${NC} .env not tracked in git"
fi

echo ""

# ============================================================================
# PHASE 2: BUILD ARTIFACTS CLEANUP
# ============================================================================

echo "🧹 Phase 2: Build Artifacts Cleanup"
echo "-----------------------------------"

# 2.1 Remove build artifacts
ARTIFACTS=(".coverage" "coverage.xml" "htmlcov" ".pytest_cache")
for artifact in "${ARTIFACTS[@]}"; do
    if [ -e "$artifact" ]; then
        rm -rf "$artifact"
        CHANGES_MADE+=("Removed build artifact: $artifact")
        echo -e "  ${GREEN}✓${NC} Removed $artifact"
    fi
done

# 2.2 Remove from git if tracked
if git ls-files | grep -qE "\.coverage$|coverage\.xml$"; then
    git rm --cached .coverage coverage.xml 2>/dev/null || true
    CHANGES_MADE+=("Removed coverage files from git tracking")
    echo -e "  ${GREEN}✓${NC} Removed coverage files from git"
fi

echo ""

# ============================================================================
# PHASE 3: BINARY AND VENDOR CODE
# ============================================================================

echo "📦 Phase 3: Binary and Vendor Code"
echo "----------------------------------"

# 3.1 Check if binary is in git
if git ls-files | grep -qE "\.tar\.gz$|\.tar$"; then
    echo -e "  ${YELLOW}⚠${NC}  Binary files found in git history"
    echo "     Run: git filter-repo --path-glob '*.tar.gz' --invert-paths"
    CHANGES_MADE+=("WARNING: Binary files in git history - needs git-filter-repo")
else
    echo -e "  ${GREEN}✓${NC} No binaries in git"
fi

# 3.2 Move vendor code
if [ -d "hcd-1.2.3" ]; then
    echo "  → Moving vendor code..."
    mkdir -p vendor
    mv hcd-1.2.3 vendor/
    CHANGES_MADE+=("Moved hcd-1.2.3/ to vendor/")
    echo -e "  ${GREEN}✓${NC} Moved hcd-1.2.3/ to vendor/"
fi

# 3.3 Create download script if binary exists
if [ -f "hcd-1.2.3-bin.tar.gz" ]; then
    echo "  → Creating download script..."
    mkdir -p scripts/setup
    cat > scripts/setup/download_hcd.sh <<'SCRIPT'
#!/bin/bash
# Download HCD on-demand instead of storing in repo
VERSION="${1:-1.2.3}"
URL="https://downloads.datastax.com/hcd/${VERSION}/hcd-${VERSION}-bin.tar.gz"

echo "Downloading HCD ${VERSION}..."
if command -v wget &> /dev/null; then
    wget "$URL" -O "hcd-${VERSION}-bin.tar.gz"
elif command -v curl &> /dev/null; then
    curl -L "$URL" -o "hcd-${VERSION}-bin.tar.gz"
else
    echo "Error: Neither wget nor curl found"
    exit 1
fi

echo "Extracting..."
tar xzf "hcd-${VERSION}-bin.tar.gz"
echo "✓ HCD extracted to hcd-${VERSION}/"
SCRIPT
    chmod +x scripts/setup/download_hcd.sh
    CHANGES_MADE+=("Created scripts/setup/download_hcd.sh")
    echo -e "  ${GREEN}✓${NC} Created download script"

    # Move binary to vendor
    mkdir -p vendor
    mv hcd-1.2.3-bin.tar.gz vendor/ 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} Moved binary to vendor/"
fi

echo ""

# ============================================================================
# PHASE 4: DOCKER COMPOSE CONSOLIDATION
# ============================================================================

echo "🐳 Phase 4: Docker Compose Consolidation"
echo "----------------------------------------"

# 4.1 Move root-level compose files to config/compose
COMPOSE_FILES=(
    "docker-compose.logging.yml"
    "docker-compose.nginx.yml"
    "docker-compose.opensearch.yml"
    "docker-compose.tls.yml"
    "docker-compose.tracing.yml"
)

for file in "${COMPOSE_FILES[@]}"; do
    if [ -f "$file" ] && [ ! -L "$file" ]; then
        echo "  → Moving $file to config/compose/"
        mv "$file" config/compose/
        CHANGES_MADE+=("Moved $file to config/compose/")
        echo -e "  ${GREEN}✓${NC} Moved $file"
    fi
done

echo ""

# ============================================================================
# PHASE 5: DIRECTORY CLEANUP
# ============================================================================

echo "📁 Phase 5: Directory Cleanup"
echo "-----------------------------"

# 5.1 Remove empty/duplicate directories
DIRS_TO_CHECK=("exports" "notebooks")
for dir in "${DIRS_TO_CHECK[@]}"; do
    if [ -d "$dir" ] && [ -z "$(ls -A $dir 2>/dev/null)" ]; then
        echo "  → Removing empty directory: $dir/"
        rmdir "$dir"
        CHANGES_MADE+=("Removed empty directory: $dir/")
        echo -e "  ${GREEN}✓${NC} Removed empty $dir/"
    elif [ -d "$dir" ]; then
        echo -e "  ${YELLOW}⚠${NC}  $dir/ not empty - manual review needed"
    fi
done

echo ""

# ============================================================================
# PHASE 6: FIX REMAINING BUILD CONTEXT
# ============================================================================

echo "🔧 Phase 6: Fix Remaining Build Contexts"
echo "----------------------------------------"

# Fix docker-compose.yml if it has wrong context
if grep -q "context: \." config/compose/docker-compose.yml 2>/dev/null; then
    echo "  → Fixing build context in docker-compose.yml..."
    sed -i.bak 's/context: \./context: ..\/../' config/compose/docker-compose.yml
    rm config/compose/docker-compose.yml.bak
    CHANGES_MADE+=("Fixed build context in config/compose/docker-compose.yml")
    echo -e "  ${GREEN}✓${NC} Fixed build context"
else
    echo -e "  ${GREEN}✓${NC} Build contexts already correct"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "📊 Summary"
echo "=========="
echo ""

if [ ${#CHANGES_MADE[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ No changes needed - project already clean!${NC}"
else
    echo "Changes made:"
    for change in "${CHANGES_MADE[@]}"; do
        echo "  • $change"
    done
fi

echo ""
echo "📋 Next Steps:"
echo "  1. Review changes: git status"
echo "  2. Test deployment: cd config/compose && podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d"
echo "  3. Commit changes: git add -A && git commit -m 'fix: audit remediation - security and structure cleanup'"
echo ""
echo -e "${GREEN}✓ Audit remediation complete!${NC}"

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
