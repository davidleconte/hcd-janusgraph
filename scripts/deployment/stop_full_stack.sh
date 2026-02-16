#!/bin/bash
# ==============================================================================
# Stop Full HCD + JanusGraph Visualization Stack
# ==============================================================================
#
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
# Date: 2026-02-11
# Version: 2.0.0 (Refactored to use common.sh)
# ==============================================================================

set -e

# Source common deployment functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
init_common

# ==============================================================================
# MAIN STOP FUNCTION
# ==============================================================================

main() {
    log_header "Stopping Services"
    
    log_info "Project: $COMPOSE_PROJECT_NAME"
    echo ""
    
    # Stop services using compose
    stop_with_compose "docker-compose.full.yml" "$COMPOSE_PROJECT_NAME"
    
    echo ""
    log_success "All services stopped"
    echo ""
    echo "To start services again:"
    echo "   cd $SCRIPT_DIR && ./deploy_full_stack.sh"
    echo ""
    echo "To completely remove containers and volumes:"
    echo "   cd $SCRIPT_DIR && ./cleanup_and_reset.sh"
    echo ""
}

# Run main function
main "$@"

# Made with Bob
