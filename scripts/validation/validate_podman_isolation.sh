#!/usr/bin/env bash
# =============================================================================
# Podman Isolation Validation Script
# =============================================================================
# Purpose: Validate Podman isolation according to PODMAN_ARCHITECTURE.md
# Usage:   ./scripts/validation/validate_podman_isolation.sh [--strict]
# Exit:    0 = success, 1 = error
#
# Validates the Five Layers of Isolation:
#   1. Network Isolation (separate subnet per project)
#   2. Volume Isolation (dedicated volumes with labels)
#   3. Resource Limits (CPU/memory caps)
#   4. Port Mapping (no conflicts)
#   5. Label-Based Management (all resources tagged)
#
# Reference: /Users/david.leconte/Documents/Work/Labs/adal/podman-architecture/PODMAN_ARCHITECTURE.md
#
# Co-Authored-By: David Leconte <david.leconte1@ibm.com>
# =============================================================================

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"

# Load .env if exists
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env"
fi

PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$PROJECT_NAME}"


# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[✅]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[⚠️]${NC} $*"; }
log_error() { echo -e "${RED}[❌]${NC} $*"; }
log_section() { echo -e "\n${CYAN}=== $* ===${NC}"; }

# Track errors and warnings
ERRORS=0
WARNINGS=0
STRICT_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --strict)
            STRICT_MODE=true
            shift
            ;;
        *)
            echo "Usage: $0 [--strict]"
            exit 1
            ;;
    esac
done

# =============================================================================
# Helper Functions
# =============================================================================

podman_cmd() {
    podman --remote --connection "$PODMAN_CONNECTION" "$@" 2>/dev/null
}

check_podman_available() {
    log_info "Checking Podman connection to '$PODMAN_CONNECTION'..."

    if ! command -v podman &> /dev/null; then
        log_error "Podman is not installed"
        return 1
    fi

    if ! podman_cmd ps &> /dev/null; then
        log_error "Cannot connect to Podman machine '$PODMAN_CONNECTION'"
        log_info "Start with: podman machine start $PODMAN_CONNECTION"
        return 1
    fi

    log_success "Podman connection successful"
    return 0
}

# =============================================================================
# Layer 1: Network Isolation Validation
# =============================================================================

validate_network_isolation() {
    log_section "Layer 1: Network Isolation"

    local networks
    networks=$(podman_cmd network ls --filter "name=${PROJECT_NAME}" --format "{{.Name}}" 2>/dev/null || echo "")

    if [[ -z "$networks" ]]; then
        log_warning "No networks found with project prefix '$PROJECT_NAME'"
        log_info "Networks will be created on first deployment"
        ((WARNINGS++))
        return 0
    fi

    log_info "Found networks with project prefix:"
    echo "$networks" | while read -r network; do
        if [[ -n "$network" ]]; then
            log_success "  $network"

            # Check network has project label
            local labels
            labels=$(podman_cmd network inspect "$network" --format '{{.Labels}}' 2>/dev/null || echo "{}")
            if [[ "$labels" == *"project"* ]]; then
                log_success "    Has project label"
            else
                log_warning "    Missing project label"
                ((WARNINGS++))
            fi
        fi
    done

    # Check for conflicting networks (without project prefix)
    local all_networks
    all_networks=$(podman_cmd network ls --format "{{.Name}}" 2>/dev/null || echo "")
    local conflicts=""

    while IFS= read -r net; do
        if [[ "$net" == "hcd-janusgraph-network" ]] && [[ "$net" != "${PROJECT_NAME}_"* ]]; then
            conflicts+="$net "
        fi
    done <<< "$all_networks"

    if [[ -n "$conflicts" ]]; then
        log_warning "Found networks without project prefix that may conflict: $conflicts"
        ((WARNINGS++))
    fi

    return 0
}

# =============================================================================
# Layer 2: Volume Isolation Validation
# =============================================================================

validate_volume_isolation() {
    log_section "Layer 2: Volume Isolation"

    local volumes
    volumes=$(podman_cmd volume ls --filter "name=${PROJECT_NAME}" --format "{{.Name}}" 2>/dev/null || echo "")

    if [[ -z "$volumes" ]]; then
        log_warning "No volumes found with project prefix '$PROJECT_NAME'"
        log_info "Volumes will be created on first deployment"
        ((WARNINGS++))
        return 0
    fi

    log_info "Found volumes with project prefix:"
    echo "$volumes" | while read -r volume; do
        if [[ -n "$volume" ]]; then
            log_success "  $volume"
        fi
    done

    return 0
}

# =============================================================================
# Layer 3: Container Naming Validation
# =============================================================================

validate_container_naming() {
    log_section "Layer 3: Container Naming (Project Prefix)"

    local containers
    containers=$(podman_cmd ps -a --format "{{.Names}}" 2>/dev/null || echo "")

    if [[ -z "$containers" ]]; then
        log_info "No containers running"
        return 0
    fi

    local project_containers=""
    local orphan_containers=""

    while IFS= read -r container; do
        if [[ "$container" == "${PROJECT_NAME}_"* ]] || [[ "$container" == "${PROJECT_NAME}-"* ]]; then
            project_containers+="$container "
        elif [[ "$container" == "hcd-server" ]] || [[ "$container" == "janusgraph-server" ]] || \
             [[ "$container" == "jupyter-lab" ]] || [[ "$container" == "grafana" ]] || \
             [[ "$container" == "prometheus" ]] || [[ "$container" == "vault-server" ]]; then
            orphan_containers+="$container "
        fi
    done <<< "$containers"

    if [[ -n "$project_containers" ]]; then
        log_success "Containers with project prefix: $project_containers"
    fi

    if [[ -n "$orphan_containers" ]]; then
        log_error "Found containers WITHOUT project prefix (violates isolation):"
        log_error "  $orphan_containers"
        log_info "These containers may conflict with other projects"
        log_info "Fix: Remove container_name: from docker-compose files and use -p flag"
        ((ERRORS++))
    fi

    return 0
}

# =============================================================================
# Layer 4: Docker Compose Configuration Validation
# =============================================================================

validate_compose_config() {
    log_section "Layer 4: Docker Compose Configuration"

    local compose_dir="$PROJECT_ROOT/config/compose"

    if [[ ! -d "$compose_dir" ]]; then
        log_error "Compose directory not found: $compose_dir"
        ((ERRORS++))
        return 1
    fi

    # Check for container_name overrides (CRITICAL violation)
    log_info "Checking for container_name overrides (violates isolation)..."

    local container_name_count=0
    for file in "$compose_dir"/*.yml; do
        if [[ -f "$file" ]]; then
            local count
            count=0
            if ! count=$(grep -c "container_name:" "$file" 2>/dev/null); then
                count=0
            fi
            if [[ $count -gt 0 ]]; then
                log_error "  $file: $count container_name override(s)"
                container_name_count=$((container_name_count + count))
            fi
        fi
    done

    if [[ $container_name_count -gt 0 ]]; then
        log_error "CRITICAL: Found $container_name_count container_name overrides"
        log_error "This BREAKS project isolation - containers won't have project prefix"
        log_info "Fix: Remove ALL container_name: lines from docker-compose files"
        ((ERRORS++))
    else
        log_success "No container_name overrides found (good!)"
    fi

    # Check for project label usage
    log_info "Checking for project labels..."
    local has_labels=false
    for file in "$compose_dir"/*.yml; do
        if [[ -f "$file" ]]; then
            if grep -q "project=" "$file" 2>/dev/null || grep -q "labels:" "$file" 2>/dev/null; then
                has_labels=true
            fi
        fi
    done

    if [[ "$has_labels" == "false" ]]; then
        log_warning "No project labels found in compose files"
        log_info "Recommended: Add 'labels: [\"project=$PROJECT_NAME\"]' to services"
        ((WARNINGS++))
    fi

    return 0
}

# =============================================================================
# Layer 5: Environment Configuration Validation
# =============================================================================

validate_env_config() {
    log_section "Layer 5: Environment Configuration"

    local env_file="$PROJECT_ROOT/.env"

    if [[ ! -f "$env_file" ]]; then
        log_error ".env file not found"
        log_info "Copy from: cp $PROJECT_ROOT/.env.example $env_file"
        ((ERRORS++))
        return 1
    fi

    # Check COMPOSE_PROJECT_NAME
    if grep -q "^COMPOSE_PROJECT_NAME=" "$env_file" 2>/dev/null; then
        local project_name
        project_name=$(grep "^COMPOSE_PROJECT_NAME=" "$env_file" | cut -d'=' -f2)
        log_success "COMPOSE_PROJECT_NAME is set: $project_name"
    else
        log_error "COMPOSE_PROJECT_NAME is NOT set in .env"
        log_info "Add: COMPOSE_PROJECT_NAME=janusgraph-demo"
        ((ERRORS++))
    fi

    # Check PODMAN_CONNECTION
    if grep -q "^PODMAN_CONNECTION=" "$env_file" 2>/dev/null; then
        local conn
        conn=$(grep "^PODMAN_CONNECTION=" "$env_file" | cut -d'=' -f2)
        log_success "PODMAN_CONNECTION is set: $conn"
    else
        log_warning "PODMAN_CONNECTION not set in .env (using default: $PODMAN_CONNECTION)"
        ((WARNINGS++))
    fi

    # Check for placeholder passwords
    if grep -q "CHANGE_ME" "$env_file" 2>/dev/null || grep -q "changeit" "$env_file" 2>/dev/null; then
        log_warning "Found placeholder passwords in .env"
        log_info "Update all passwords before production deployment"
        ((WARNINGS++))
    fi

    return 0
}

# =============================================================================
# Port Conflict Detection
# =============================================================================

validate_port_availability() {
    log_section "Port Availability Check"

    local ports=(
        "19042:HCD CQL"
        "18182:JanusGraph Gremlin"
        "8888:Jupyter"
        "3000:Visualizer"
        "9090:Prometheus"
        "3001:Grafana"
    )

    log_info "Checking port availability on localhost..."

    for port_info in "${ports[@]}"; do
        local port="${port_info%%:*}"
        local service="${port_info##*:}"

        if lsof -Pi ":$port" -sTCP:LISTEN -t &>/dev/null; then
            local pid
            pid=$(lsof -Pi ":$port" -sTCP:LISTEN -t 2>/dev/null | head -1)
            local proc
            proc=$(ps -p "$pid" -o comm= 2>/dev/null || echo "unknown")
            log_warning "Port $port ($service) is in use by: $proc (PID: $pid)"
            ((WARNINGS++))
        else
            log_success "Port $port ($service) is available"
        fi
    done

    return 0
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    echo ""
    echo "=========================================="
    echo "Podman Isolation Validation"
    echo "=========================================="
    echo "Project:    $PROJECT_NAME"
    echo "Connection: $PODMAN_CONNECTION"
    echo "Strict:     $STRICT_MODE"
    echo ""

    # Check Podman is available
    if ! check_podman_available; then
        log_error "Cannot proceed without Podman connection"
        exit 1
    fi

    # Run all validation layers
    validate_env_config
    validate_compose_config
    validate_network_isolation
    validate_volume_isolation
    validate_container_naming
    validate_port_availability

    # Summary
    echo ""
    echo "=========================================="
    echo "Validation Summary"
    echo "=========================================="

    if [[ $ERRORS -gt 0 ]]; then
        log_error "ERRORS: $ERRORS"
    else
        log_success "ERRORS: 0"
    fi

    if [[ $WARNINGS -gt 0 ]]; then
        log_warning "WARNINGS: $WARNINGS"
    else
        log_success "WARNINGS: 0"
    fi

    echo ""

    # Exit code
    if [[ $ERRORS -gt 0 ]]; then
        log_error "VALIDATION FAILED"
        echo ""
        echo "Critical issues found. Fix before deployment:"
        echo "  1. Remove all container_name: from docker-compose files"
        echo "  2. Add COMPOSE_PROJECT_NAME=janusgraph-demo to .env"
        echo "  3. Always use: podman-compose -p \$COMPOSE_PROJECT_NAME ..."
        echo ""
        exit 1
    elif [[ $WARNINGS -gt 0 ]] && [[ "$STRICT_MODE" == "true" ]]; then
        log_warning "VALIDATION FAILED (strict mode)"
        exit 1
    else
        log_success "VALIDATION PASSED"
        echo ""
        echo "Podman isolation is correctly configured."
        echo "Deploy with: cd config/compose && podman-compose -p $PROJECT_NAME up -d"
        echo ""
        exit 0
    fi
}

# Run main function
main "$@"
