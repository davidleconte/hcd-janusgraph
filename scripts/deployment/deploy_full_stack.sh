#!/bin/bash
# ==============================================================================
# Deploy Full HCD + JanusGraph Visualization Stack
# ==============================================================================
# Platform: macOS M3 Pro (Sequoia 26.2)
# Podman machine: configurable via .env
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
# MAIN DEPLOYMENT
# ==============================================================================

main() {
    CORE_SERVICES_WAIT_SEC="${CORE_SERVICES_WAIT_SEC:-90}"

    log_header "HCD + JanusGraph Full Stack Deployment"
    
    # Display configuration
    echo "Configuration:"
    echo "  Project Name:      $COMPOSE_PROJECT_NAME"
    echo "  Podman Connection: $PODMAN_CONNECTION"
    echo "  Platform:          $PODMAN_PLATFORM"
    echo ""
    
    # Validate environment
    validate_environment || exit 1
    
    # Create required directories
    create_directories
    
    # Deploy stack
    log_step "Deploying Full Stack via Podman Compose"
    log_info "This will build custom images (OpenSearch w/ JVector, Visualization tools)"
    log_info "and start all services with dependencies managed."
    echo ""
    
    deploy_with_compose "docker-compose.full.yml" "$COMPOSE_PROJECT_NAME" || exit 1
    
    # Wait for core services
    log_info "Total Expected: 90-270 seconds (1.5-4.5 minutes)"
    log_info "Current wait: ${CORE_SERVICES_WAIT_SEC} seconds for core services..."
    log_info "(Services continue initializing in background)"
    echo ""
    sleep "${CORE_SERVICES_WAIT_SEC}"
    log_success "Core services should be ready (check health with: podman --remote --connection $PODMAN_CONNECTION ps)"
    echo ""
    
    # Display access information
    display_access_info "$COMPOSE_PROJECT_NAME"
    
    echo "📖 See FULL_STACK_ACCESS.md for detailed documentation"
    echo ""
    echo "To stop all services:"
    echo "   cd $SCRIPT_DIR && ./stop_full_stack.sh"
    echo ""
}

# Run main function
main "$@"

# Made with Bob
