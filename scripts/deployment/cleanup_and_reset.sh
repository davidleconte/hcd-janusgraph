#!/bin/bash
# ==============================================================================
# Cleanup and Reset Script
# ==============================================================================
# Removes all containers, networks, and volumes for the project.
# Use this when you need to completely reset the stack.
#
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
# Date: 2026-02-11
# Version: 2.0.0 (Refactored to use common.sh)
# ==============================================================================

set -e

# Source common deployment functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# ==============================================================================
# MAIN CLEANUP FUNCTION
# ==============================================================================

main() {
    log_header "Cleanup and Reset"
    
    log_warning "This will remove:"
    echo "  • All containers for project: $COMPOSE_PROJECT_NAME"
    echo "  • All volumes (DATA WILL BE LOST)"
    echo "  • All networks"
    echo ""
    
    # Stop services first
    log_step "Stopping services"
    cd "$PROJECT_ROOT/config/compose"
    podman-compose -p "$COMPOSE_PROJECT_NAME" -f docker-compose.full.yml down -v 2>/dev/null || true
    
    # Cleanup containers
    cleanup_containers "$COMPOSE_PROJECT_NAME"
    
    # Cleanup networks
    cleanup_networks
    
    # Cleanup volumes (with confirmation)
    cleanup_volumes "$COMPOSE_PROJECT_NAME"
    
    echo ""
    log_success "Cleanup complete"
    echo ""
    echo "To deploy fresh stack:"
    echo "   cd $SCRIPT_DIR && ./deploy_full_stack.sh"
    echo ""
}

# Run main function
main "$@"

# Made with Bob
