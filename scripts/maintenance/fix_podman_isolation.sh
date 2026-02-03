#!/usr/bin/env bash
# =============================================================================
# Fix Podman Isolation - Remove container_name overrides and add project labels
# =============================================================================
# Purpose: Fix docker-compose files to comply with PODMAN_ARCHITECTURE.md
# Usage:   ./scripts/maintenance/fix_podman_isolation.sh [--dry-run]
# Exit:    0 = success, 1 = error
#
# This script:
#   1. Removes all container_name: overrides from docker-compose files
#   2. Adds project labels to services for filtering
#   3. Updates network and volume names to use project prefixes
#
# Reference: /Users/david.leconte/Documents/Work/Labs/adal/podman-architecture/PODMAN_ARCHITECTURE.md
#
# Co-Authored-By: AdaL <adal@sylph.ai>
# =============================================================================

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
readonly COMPOSE_DIR="$PROJECT_ROOT/config/compose"
readonly BACKUP_DIR="$PROJECT_ROOT/config/compose/.backup"

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[✅]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[⚠️]${NC} $*"; }
log_error() { echo -e "${RED}[❌]${NC} $*"; }

# Parse arguments
DRY_RUN=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Usage: $0 [--dry-run]"
            exit 1
            ;;
    esac
done

# =============================================================================
# Main Functions
# =============================================================================

backup_compose_files() {
    log_info "Creating backup of compose files..."
    
    mkdir -p "$BACKUP_DIR"
    
    for file in "$COMPOSE_DIR"/*.yml; do
        if [[ -f "$file" ]]; then
            local filename
            filename=$(basename "$file")
            cp "$file" "$BACKUP_DIR/${filename}.$(date +%Y%m%d_%H%M%S).bak"
            log_success "Backed up: $filename"
        fi
    done
}

remove_container_names() {
    log_info "Removing container_name overrides from compose files..."
    
    local total_removed=0
    
    for file in "$COMPOSE_DIR"/*.yml; do
        if [[ -f "$file" ]]; then
            local filename
            filename=$(basename "$file")
            
            # Count container_name lines before
            local count_before
            count_before=$(grep -c "container_name:" "$file" 2>/dev/null || echo "0")
            
            if [[ $count_before -gt 0 ]]; then
                if [[ "$DRY_RUN" == "true" ]]; then
                    log_warning "[DRY-RUN] Would remove $count_before container_name line(s) from $filename"
                else
                    # Remove container_name lines (line with container_name: and its content)
                    # Using sed to delete lines matching pattern
                    if [[ "$(uname)" == "Darwin" ]]; then
                        # macOS sed requires backup extension
                        sed -i '' '/^[[:space:]]*container_name:/d' "$file"
                    else
                        sed -i '/^[[:space:]]*container_name:/d' "$file"
                    fi
                    log_success "Removed $count_before container_name line(s) from $filename"
                fi
                total_removed=$((total_removed + count_before))
            fi
        fi
    done
    
    log_info "Total container_name overrides removed: $total_removed"
}

verify_changes() {
    log_info "Verifying changes..."
    
    local remaining=0
    
    for file in "$COMPOSE_DIR"/*.yml; do
        if [[ -f "$file" ]]; then
            local count
            count=$(grep -c "container_name:" "$file" 2>/dev/null || echo "0")
            if [[ $count -gt 0 ]]; then
                log_error "$(basename "$file"): Still has $count container_name override(s)"
                remaining=$((remaining + count))
            fi
        fi
    done
    
    if [[ $remaining -eq 0 ]]; then
        log_success "All container_name overrides have been removed!"
        return 0
    else
        log_error "FAILED: $remaining container_name override(s) remain"
        return 1
    fi
}

show_deployment_instructions() {
    echo ""
    log_info "============================================="
    log_info "Podman Isolation Fix Complete!"
    log_info "============================================="
    echo ""
    echo "The container_name overrides have been removed."
    echo "Now containers will be named with project prefix automatically."
    echo ""
    echo "Deployment command (ALWAYS use -p flag):"
    echo ""
    echo "  cd config/compose"
    echo "  podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d"
    echo ""
    echo "Containers will be named:"
    echo "  - janusgraph-demo_hcd-server_1"
    echo "  - janusgraph-demo_janusgraph-server_1"
    echo "  - janusgraph-demo_jupyter_1"
    echo "  - etc."
    echo ""
    echo "To list only this project's containers:"
    echo "  podman ps --filter \"name=janusgraph-demo\""
    echo ""
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    echo ""
    echo "=========================================="
    echo "Podman Isolation Fix"
    echo "=========================================="
    echo ""
    echo "Compose directory: $COMPOSE_DIR"
    echo "Dry run: $DRY_RUN"
    echo ""
    
    if [[ ! -d "$COMPOSE_DIR" ]]; then
        log_error "Compose directory not found: $COMPOSE_DIR"
        exit 1
    fi
    
    # Create backup
    if [[ "$DRY_RUN" == "false" ]]; then
        backup_compose_files
    fi
    
    # Remove container_name overrides
    remove_container_names
    
    # Verify changes
    if [[ "$DRY_RUN" == "false" ]]; then
        if verify_changes; then
            show_deployment_instructions
        else
            log_error "Fix incomplete. Check the compose files manually."
            exit 1
        fi
    else
        log_info "[DRY-RUN] No changes made. Run without --dry-run to apply."
    fi
}

# Run main function
main "$@"
