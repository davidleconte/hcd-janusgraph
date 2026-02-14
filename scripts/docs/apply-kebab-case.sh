#!/bin/bash
# File: scripts/docs/apply-kebab-case.sh
# Purpose: Apply kebab-case naming convention to all documentation files
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
# Date: 2026-02-12

set -euo pipefail

# Configuration
DRY_RUN=true
BACKUP_DIR=".backup-$(date +%Y%m%d-%H%M%S)"
LOG_FILE="kebab-case-remediation-$(date +%Y%m%d-%H%M%S).log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
FILES_RENAMED=0
FILES_DELETED=0
LINKS_UPDATED=0
ERRORS=0

# Initialize file mapping
declare -A FILE_MAP
FILE_MAP["docs/BANKING_USE_CASES_TECHNICAL_SPEC.md"]="docs/banking-use-cases-technical-spec.md"
FILE_MAP["docs/BANKING_USE_CASES_TECHNICAL_SPEC_COMPLETE.md"]="docs/banking-use-cases-technical-spec-complete.md"
FILE_MAP["docs/TECHNICAL_SPECIFICATIONS.md"]="docs/technical-specifications.md"
FILE_MAP["docs/DOCS_OPTIMIZATION_PLAN.md"]="docs/docs-optimization-plan.md"
FILE_MAP["docs/banking/PHASE5_VECTOR_AI_FOUNDATION.md"]="docs/banking/phase5-vector-ai-foundation.md"
FILE_MAP["docs/banking/PHASE5_IMPLEMENTATION_COMPLETE.md"]="docs/banking/phase5-implementation-complete.md"
FILE_MAP["docs/banking/ENTERPRISE_ADVANCED_PATTERNS_PLAN.md"]="docs/banking/enterprise-advanced-patterns-plan.md"
FILE_MAP["docs/implementation/EXCEPTION_HANDLING_AUDIT.md"]="docs/implementation/exception-handling-audit.md"
FILE_MAP["docs/implementation/PHASE2_WEEK2_STRUCTURE_ORGANIZATION.md"]="docs/implementation/phase2-week2-structure-organization.md"
FILE_MAP["docs/implementation/PHASE3_QUICK_START.md"]="docs/implementation/phase3-quick-start.md"
FILE_MAP["docs/implementation/PHASE3_WEEK3_STANDARDIZATION.md"]="docs/implementation/phase3-week3-standardization.md"
FILE_MAP["docs/implementation/PRODUCTION_READINESS_AUDIT_2026.md"]="docs/implementation/production-readiness-audit-2026.md"
FILE_MAP["docs/implementation/PRODUCTION_READINESS_STATUS_FINAL.md"]="docs/implementation/production-readiness-status-final.md"
FILE_MAP["docs/implementation/REVIEW_CONFRONTATION_ANALYSIS_2026-02-11.md"]="docs/implementation/review-confrontation-analysis-2026-02-11.md"
FILE_MAP["docs/implementation/WEEK1_PROGRESS_SUMMARY_2026-02-11.md"]="docs/implementation/week1-progress-summary-2026-02-11.md"
FILE_MAP["docs/implementation/WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md"]="docs/implementation/week2-days-8-12-implementation-guide.md"
FILE_MAP["docs/implementation/WEEK3_DAYS13-15_SUMMARY.md"]="docs/implementation/week3-days13-15-summary.md"
FILE_MAP["docs/implementation/WEEK3_IMPLEMENTATION_PLAN.md"]="docs/implementation/week3-implementation-plan.md"
FILE_MAP["docs/implementation/WEEK4_DAY19_IMPLEMENTATION_PLAN.md"]="docs/implementation/week4-day19-implementation-plan.md"
FILE_MAP["docs/implementation/WEEK4_DAY20_IMPLEMENTATION_PLAN.md"]="docs/implementation/week4-day20-implementation-plan.md"
FILE_MAP["docs/implementation/WEEK4_DAY20_SECURITY_AUDIT_REPORT.md"]="docs/implementation/week4-day20-security-audit-report.md"
FILE_MAP["docs/implementation/WEEK4_DAY20_SUMMARY.md"]="docs/implementation/week4-day20-summary.md"
FILE_MAP["docs/implementation/WEEK4_DAY21_IMPLEMENTATION_PLAN.md"]="docs/implementation/week4-day21-implementation-plan.md"
FILE_MAP["docs/implementation/WEEK4_DAY22_IMPLEMENTATION_PLAN.md"]="docs/implementation/week4-day22-implementation-plan.md"
FILE_MAP["docs/implementation/WEEK4_DAY22_SUMMARY.md"]="docs/implementation/week4-day22-summary.md"
FILE_MAP["docs/implementation/WEEK4_IMPLEMENTATION_PLAN.md"]="docs/implementation/week4-implementation-plan.md"
FILE_MAP["docs/implementation/WEEK5_DAY25_SUMMARY.md"]="docs/implementation/week5-day25-summary.md"
FILE_MAP["docs/implementation/WEEK5_PRODUCTION_READY_SUMMARY.md"]="docs/implementation/week5-production-ready-summary.md"
FILE_MAP["docs/implementation/WEEK6_EXECUTION_PLAN.md"]="docs/implementation/week6-execution-plan.md"
FILE_MAP["docs/implementation/audits/TECHNICAL_CONFRONTATION_ANALYSIS_2026-01-30.md"]="docs/implementation/audits/technical-confrontation-analysis-2026-01-30.md"
FILE_MAP["docs/implementation/audits/DATA_SCRIPTS_SAI_AUDIT_2026-01-30.md"]="docs/implementation/audits/data-scripts-sai-audit-2026-01-30.md"
FILE_MAP["docs/implementation/audits/REBUILD_VS_REMEDIATION_ANALYSIS_2026-01-30.md"]="docs/implementation/audits/rebuild-vs-remediation-analysis-2026-01-30.md"
FILE_MAP["docs/migrations/UV_MIGRATION_GUIDE.md"]="docs/migrations/uv-migration-guide.md"
FILE_MAP["docs/monitoring/SECURITY_MONITORING.md"]="docs/monitoring/security-monitoring.md"
FILE_MAP["CODEBASE_REVIEW_2026-02-11.md"]="codebase-review-2026-02-11.md"
FILE_MAP["SECURITY_REMEDIATION_PLAN_2026-02-11.md"]="security-remediation-plan-2026-02-11.md"
FILE_MAP["TOOLING_STANDARDS_UPDATE_2026-02-11.md"]="tooling-standards-update-2026-02-11.md"
FILE_MAP["CODE_QUALITY_IMPLEMENTATION_PLAN_2026-02-11.md"]="code-quality-implementation-plan-2026-02-11.md"
FILE_MAP["adal_graph_pipeline_explanation_2026-01-30_15-45-12-234.md"]="adal-graph-pipeline-explanation-2026-01-30-15-45-12-234.md"

# Files to delete (duplicates)
FILES_TO_DELETE=("docs/banking/USER_GUIDE.md")

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $*" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $*" | tee -a "$LOG_FILE"
    ((ERRORS++))
}

# Show help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Apply kebab-case naming convention to all documentation files.

OPTIONS:
    --execute       Execute the renaming (default is dry-run)
    --rollback      Rollback to previous state from backup
    --help          Show this help message

EXAMPLES:
    $0                    # Dry-run mode (default)
    $0 --execute          # Execute renaming
    $0 --rollback         # Rollback changes

EOF
}

# Validate environment
validate_environment() {
    log "Validating environment..."
    
    # Check if in project root
    if [ ! -f "README.md" ] || [ ! -d "docs" ]; then
        log_error "Must run from project root directory"
        exit 1
    fi
    
    # Check git status
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not a git repository"
        exit 1
    fi
    
    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        log_warning "Git repository has uncommitted changes"
        if [ "$DRY_RUN" = false ]; then
            read -p "Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
    
    log_success "Environment validation passed"
}

# Create backup
create_backup() {
    if [ "$DRY_RUN" = true ]; then
        log "Would create backup in: $BACKUP_DIR"
        return
    fi
    
    log "Creating backup in: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    
    # Backup all files that will be renamed
    for old_file in "${!FILE_MAP[@]}"; do
        if [ -f "$old_file" ]; then
            backup_path="$BACKUP_DIR/$old_file"
            mkdir -p "$(dirname "$backup_path")"
            cp "$old_file" "$backup_path"
        fi
    done
    
    # Backup files to be deleted
    for file in "${FILES_TO_DELETE[@]}"; do
        if [ -f "$file" ]; then
            backup_path="$BACKUP_DIR/$file"
            mkdir -p "$(dirname "$backup_path")"
            cp "$file" "$backup_path"
        fi
    done
    
    log_success "Backup created: $BACKUP_DIR"
}

# Rename a single file
rename_file() {
    local old_file="$1"
    local new_file="$2"
    
    if [ ! -f "$old_file" ]; then
        log_warning "File not found: $old_file"
        return 1
    fi
    
    if [ -f "$new_file" ]; then
        log_warning "Target file already exists: $new_file"
        return 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log "Would rename: $old_file → $new_file"
    else
        # Use git mv to preserve history
        if git ls-files --error-unmatch "$old_file" > /dev/null 2>&1; then
            git mv "$old_file" "$new_file"
            log_success "Renamed (git): $old_file → $new_file"
        else
            mv "$old_file" "$new_file"
            log_success "Renamed: $old_file → $new_file"
        fi
    fi
    
    ((FILES_RENAMED++))
    return 0
}

# Delete a file
delete_file() {
    local file="$1"
    
    if [ ! -f "$file" ]; then
        log_warning "File not found: $file"
        return 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log "Would delete: $file (duplicate)"
    else
        if git ls-files --error-unmatch "$file" > /dev/null 2>&1; then
            git rm "$file"
            log_success "Deleted (git): $file"
        else
            rm "$file"
            log_success "Deleted: $file"
        fi
    fi
    
    ((FILES_DELETED++))
    return 0
}

# Update links in a file
update_links_in_file() {
    local md_file="$1"
    local changes=0
    
    if [ ! -f "$md_file" ]; then
        return 0
    fi
    
    # Create temp file for changes
    local temp_file="${md_file}.tmp"
    cp "$md_file" "$temp_file"
    
    # Update links for each renamed file
    for old_file in "${!FILE_MAP[@]}"; do
        local new_file="${FILE_MAP[$old_file]}"
        local old_basename=$(basename "$old_file")
        local new_basename=$(basename "$new_file")
        
        # Skip if this is the file being renamed
        [ "$md_file" = "$old_file" ] && continue
        
        # Update markdown links: [text](OLD.md) → [text](NEW.md)
        if grep -q "]($old_basename)" "$temp_file" 2>/dev/null; then
            sed -i.bak "s|]($old_basename)|]($new_basename)|g" "$temp_file"
            ((changes++))
        fi
        
        # Update full path links
        if grep -q "]($old_file)" "$temp_file" 2>/dev/null; then
            sed -i.bak "s|]($old_file)|]($new_file)|g" "$temp_file"
            ((changes++))
        fi
        
        # Update inline code references: `OLD.md` → `NEW.md`
        if grep -q "\`$old_basename\`" "$temp_file" 2>/dev/null; then
            sed -i.bak "s|\`$old_basename\`|\`$new_basename\`|g" "$temp_file"
            ((changes++))
        fi
    done
    
    # Clean up backup files
    rm -f "${temp_file}.bak"
    
    if [ $changes -gt 0 ]; then
        if [ "$DRY_RUN" = true ]; then
            log "Would update $changes link(s) in: $md_file"
            rm "$temp_file"
        else
            mv "$temp_file" "$md_file"
            log_success "Updated $changes link(s) in: $md_file"
        fi
        ((LINKS_UPDATED += changes))
    else
        rm "$temp_file"
    fi
}

# Update all links
update_all_links() {
    log "Updating links in markdown files..."
    
    # Find all markdown files
    while IFS= read -r -d '' md_file; do
        update_links_in_file "$md_file"
    done < <(find . -name "*.md" -type f -print0)
    
    log_success "Link update complete"
}

# Validate changes
validate_changes() {
    log "Validating changes..."
    local validation_errors=0
    
    if [ "$DRY_RUN" = true ]; then
        log "Skipping validation in dry-run mode"
        return
    fi
    
    # Check all files were renamed
    for old_file in "${!FILE_MAP[@]}"; do
        if [ -f "$old_file" ]; then
            log_error "File still exists: $old_file"
            ((validation_errors++))
        fi
    done
    
    for new_file in "${FILE_MAP[@]}"; do
        if [ ! -f "$new_file" ]; then
            log_error "File not created: $new_file"
            ((validation_errors++))
        fi
    done
    
    # Check for broken links (basic check)
    log "Checking for potential broken links..."
    local broken_links=0
    while IFS= read -r -d '' md_file; do
        # Look for UPPERCASE patterns in links
        if grep -E '\[.*\]\(.*[A-Z_]{2,}.*\.md\)' "$md_file" > /dev/null 2>&1; then
            log_warning "Potential broken link in: $md_file"
            ((broken_links++))
        fi
    done < <(find docs -name "*.md" -type f -print0 2>/dev/null)
    
    if [ $broken_links -gt 0 ]; then
        log_warning "Found $broken_links file(s) with potential broken links"
    fi
    
    if [ $validation_errors -eq 0 ]; then
        log_success "Validation passed"
    else
        log_error "Validation failed with $validation_errors error(s)"
    fi
}

# Generate report
generate_report() {
    echo ""
    echo "================================================================="
    echo "KEBAB-CASE REMEDIATION REPORT"
    echo "================================================================="
    echo ""
    echo "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY-RUN' || echo 'EXECUTE')"
    echo "Date: $(date +'%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "Summary:"
    echo "  Files renamed: $FILES_RENAMED"
    echo "  Files deleted: $FILES_DELETED"
    echo "  Links updated: $LINKS_UPDATED"
    echo "  Errors: $ERRORS"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        echo "This was a DRY-RUN. No changes were made."
        echo "To execute: $0 --execute"
    else
        echo "Changes have been applied."
        echo "Backup location: $BACKUP_DIR"
        echo "To rollback: $0 --rollback"
    fi
    
    echo ""
    echo "Log file: $LOG_FILE"
    echo "================================================================="
}

# Rollback changes
rollback() {
    log "Starting rollback..."
    
    # Find most recent backup
    local latest_backup=$(ls -dt .backup-* 2>/dev/null | head -1)
    
    if [ -z "$latest_backup" ]; then
        log_error "No backup found"
        exit 1
    fi
    
    log "Restoring from: $latest_backup"
    
    # Restore all files
    cp -r "$latest_backup"/* .
    
    log_success "Rollback complete"
    log "Backup preserved at: $latest_backup"
}

# Main execution
main() {
    cd "$PROJECT_ROOT"
    
    echo "================================================================="
    echo "KEBAB-CASE REMEDIATION"
    echo "================================================================="
    echo ""
    
    log "Starting kebab-case remediation"
    log "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY-RUN' || echo 'EXECUTE')"
    echo ""
    
    # Step 1: Validate environment
    validate_environment
    echo ""
    
    # Step 2: Create backup
    create_backup
    echo ""
    
    # Step 3: Delete duplicate files
    log "Deleting duplicate files..."
    for file in "${FILES_TO_DELETE[@]}"; do
        delete_file "$file"
    done
    echo ""
    
    # Step 4: Rename files
    log "Renaming files..."
    for old_file in "${!FILE_MAP[@]}"; do
        new_file="${FILE_MAP[$old_file]}"
        rename_file "$old_file" "$new_file"
    done
    echo ""
    
    # Step 5: Update links
    update_all_links
    echo ""
    
    # Step 6: Validate
    validate_changes
    echo ""
    
    # Step 7: Generate report
    generate_report
    
    # Exit with error code if there were errors
    [ $ERRORS -gt 0 ] && exit 1
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --execute)
            DRY_RUN=false
            shift
            ;;
        --rollback)
            rollback
            exit 0
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main
main

# Made with Bob
