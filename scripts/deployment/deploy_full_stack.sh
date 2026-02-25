#!/bin/bash
# ==============================================================================
# Deploy Full HCD + JanusGraph Visualization Stack
# ==============================================================================
# Platform: macOS M3 Pro (Sequoia 26.2)
# Podman machine: configurable via .env
#
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
# Date: 2026-02-11
# Version: 2.1.0 (Deterministic - builds images and initializes Vault)
# ==============================================================================

set -e

# Source common deployment functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "$SCRIPT_DIR/common.sh"
init_common

# ==============================================================================
# DETERMINISTIC IMAGE BUILDING
# ==============================================================================

build_local_images() {
    log_step "Building Local Docker Images"
    echo ""
    
    local docker_dir="$PROJECT_ROOT/docker"
    
    # Build all local images needed for the stack
    # Format: "image_name:dockerfile_dir"
    local images=(
        "hcd:1.2.3:docker/hcd"
        "opensearch-jvector:1.0.0:docker/opensearch"
        "jupyter-janusgraph:1.0.0:docker/jupyter"
        "janusgraph-visualizer:1.0.0:docker/visualizer"
        "graphexp:1.0.0:docker/graphexp"
        "cqlsh-client:1.0.0:docker/cqlsh"
        "janusgraph-exporter:1.0.0:docker"
        "analytics-api:1.0.0:docker/api"
        "graph-consumer:1.0.0:docker/consumers"
        "vector-consumer:1.0.0:docker/consumers"
    )
    
    for image_spec in "${images[@]}"; do
        local image_name="${image_spec%%:*}"
        local dockerfile_dir="${image_spec##*:}"
        local dockerfile_path="$PROJECT_ROOT/$dockerfile_dir/Dockerfile"
        
        # Determine Dockerfile name (some have different names)
        local actual_dockerfile="$dockerfile_path"
        if [[ "$image_name" == "janusgraph-exporter" ]] && [[ ! -f "$dockerfile_path" ]]; then
            actual_dockerfile="$docker_file_dir/Dockerfile.exporter"
        fi
        
        if [[ -f "$actual_dockerfile" ]]; then
            log_info "Building localhost/$image_name from $dockerfile_dir..."
            podman --remote --connection "$PODMAN_CONNECTION" build \
                -f "$actual_dockerfile" \
                -t "localhost/$image_name" \
                "$PROJECT_ROOT" 2>&1 | tail -3
            log_success "Built localhost/$image_name"
        else
            log_warn "Dockerfile not found: $actual_dockerfile for $image_name"
        fi
    done
    
    log_success "All local images built"
    echo ""
}

# ==============================================================================
# DETERMINISTIC VAULT INITIALIZATION
# ==============================================================================

init_vault_deterministic() {
    log_step "Initializing Vault (Deterministic)"
    echo ""
    
    local vault_container="${COMPOSE_PROJECT_NAME}_vault_1"
    
    # Check if Vault container is running
    if ! podman --remote --connection "$PODMAN_CONNECTION" ps | grep -q "vault_1"; then
        log_warn "Vault container not running, skipping initialization"
        return 0
    fi
    
    # Check if Vault is already initialized and unsealed
    local vault_status
    vault_status=$(podman --remote --connection "$PODMAN_CONNECTION" exec "$vault_container" vault status 2>&1 || true)
    
    if echo "$vault_status" | grep -q "Sealed.*false"; then
        log_info "Vault already unsealed"
        return 0
    fi
    
    if echo "$vault_status" | grep -q "Initialized.*true"; then
        log_info "Vault initialized but sealed, unsealing..."
        
        # Unseal with stored keys (3 of 5)
        podman --remote --connection "$PODMAN_CONNECTION" exec "$vault_container" \
            vault operator unseal "BZCM/BxZ79JWMnb+fbQHIhWOgvjNLdImq2EFmInANsiv" >/dev/null 2>&1 || true
        podman --remote --connection "$PODMAN_CONNECTION" exec "$vault_container" \
            vault operator unseal "cTSJkHANFF6/ZpOoViV1hn2CxClBOoIZlD1IewM9lsLC" >/dev/null 2>&1 || true
        podman --remote --connection "$PODMAN_CONNECTION" exec "$vault_container" \
            vault operator unseal "GK6GwkIb579aa6ORck/z5gv8gOjCQw50PAbFIcsZLMb6" >/dev/null 2>&1 || true
        
        log_success "Vault unsealed"
        return 0
    fi
    
    # Initialize Vault
    log_info "Initializing Vault..."
    
    local vault_init
    vault_init=$(podman --remote --connection "$PODMAN_CONNECTION" exec -e "VAULT_ADDR=http://vault:8200" "$vault_container" \
        vault operator init -key-shares=5 -key-threshold=3 -format=json 2>&1)
    
    # Extract and apply unseal keys
    local key1=$(echo "$vault_init" | python3 -c "import sys,json; print(json.load(sys.stdin)['unseal_keys_b64'][0])" 2>/dev/null || echo "")
    local key2=$(echo "$vault_init" | python3 -c "import sys,json; print(json.load(sys.stdin)['unseal_keys_b64'][1])" 2>/dev/null || echo "")
    local key3=$(echo "$vault_init" | python3 -c "import sys,json; print(json.load(sys.stdin)['unseal_keys_b64'][2])" 2>/dev/null || echo "")
    
    if [[ -n "$key1" ]] && [[ -n "$key2" ]] && [[ -n "$key3" ]]; then
        podman --remote --connection "$PODMAN_CONNECTION" exec -e "VAULT_ADDR=http://vault:8200" "$vault_container" \
            vault operator unseal "$key1" >/dev/null 2>&1 || true
        podman --remote --connection "$PODMAN_CONNECTION" exec -e "VAULT_ADDR=http://vault:8200" "$vault_container" \
            vault operator unseal "$key2" >/dev/null 2>&1 || true
        podman --remote --connection "$PODMAN_CONNECTION" exec -e "VAULT_ADDR=http://vault:8200" "$vault_container" \
            vault operator unseal "$key3" >/dev/null 2>&1 || true
        
        log_success "Vault initialized and unsealed"
    else
        log_warn "Could not extract Vault keys - manual intervention may be needed"
    fi
    
    echo ""
}

# ==============================================================================
# MAIN DEPLOYMENT
# ==============================================================================

main() {
    CORE_SERVICES_WAIT_SEC="${CORE_SERVICES_WAIT_SEC:-90}"
    RUN_NOTEBOOK_PREREQ_BOOTSTRAP="${RUN_NOTEBOOK_PREREQ_BOOTSTRAP:-1}"

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
    
    # Build local images first (deterministic)
    build_local_images
    
    # Deploy stack
    log_step "Deploying Full Stack via Podman Compose"
    log_info "This will start all services with dependencies managed."
    echo ""
    
    deploy_with_compose "docker-compose.full.yml" "$COMPOSE_PROJECT_NAME" || exit 1
    
    # Wait for core services
    log_info "Waiting ${CORE_SERVICES_WAIT_SEC} seconds for core services..."
    sleep "${CORE_SERVICES_WAIT_SEC}"
    log_success "Core services should be ready"
    echo ""

    # Initialize Vault deterministically
    init_vault_deterministic

    if [[ "${RUN_NOTEBOOK_PREREQ_BOOTSTRAP}" == "1" ]]; then
        log_step "Deterministic Notebook Prerequisite Bootstrap"
        log_info "Seeding baseline graph data and validating HCD/JanusGraph/OpenSearch readiness."
        echo ""

        bash "${PROJECT_ROOT}/scripts/testing/seed_demo_graph.sh"
        bash "${PROJECT_ROOT}/scripts/testing/prove_notebook_prerequisites.sh" \
            --report "${PROJECT_ROOT}/exports/notebook-prereq-proof-latest.json"

        log_success "Notebook prerequisite bootstrap complete"
        echo ""
    else
        log_info "Notebook prerequisite bootstrap skipped (RUN_NOTEBOOK_PREREQ_BOOTSTRAP=0)"
        echo ""
    fi
    
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
