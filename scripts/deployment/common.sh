#!/bin/bash
# ==============================================================================
# Common Deployment Functions
# ==============================================================================
#
# Shared utilities for all deployment scripts.
# Source this file at the beginning of deployment scripts:
#   source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
#
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
# Date: 2026-02-11
# Version: 1.0.0
#
# ==============================================================================

set -euo pipefail

# ==============================================================================
# 1. PATH RESOLUTION
# ==============================================================================

init_paths() {
    # Resolve script directory and project root
    # This works even when sourced from other scripts
    if [ -n "${BASH_SOURCE[0]:-}" ]; then
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    else
        SCRIPT_DIR="$(pwd)"
    fi
    
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    
    export SCRIPT_DIR PROJECT_ROOT
    
    # Change to project root for consistent behavior
    cd "$PROJECT_ROOT"
}

# ==============================================================================
# 2. ENVIRONMENT LOADING
# ==============================================================================

load_environment() {
    local env_file="$PROJECT_ROOT/.env"
    local env_example="$PROJECT_ROOT/.env.example"
    
    if [ -f "$env_file" ]; then
        # shellcheck source=/dev/null
        source "$env_file"
        echo "✅ Loaded environment from .env"
    elif [ -f "$env_example" ]; then
        echo "⚠️  .env not found, using .env.example"
        echo "   Create .env for custom configuration"
        # shellcheck source=/dev/null
        source "$env_example"
    else
        echo "⚠️  No .env or .env.example found, using defaults"
    fi
}

# ==============================================================================
# 3. CONFIGURATION DEFAULTS
# ==============================================================================

set_defaults() {
    # Project Configuration
    export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"
    
    # Podman Configuration
    export PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"
    export PODMAN_PLATFORM="${PODMAN_PLATFORM:-linux/arm64}"
    
    # Port Configuration
    export HCD_CQL_PORT="${HCD_CQL_PORT:-19042}"
    export JANUSGRAPH_GREMLIN_PORT="${JANUSGRAPH_GREMLIN_PORT:-18182}"
    export JANUSGRAPH_MGMT_PORT="${JANUSGRAPH_MGMT_PORT:-18184}"
    export JUPYTER_PORT="${JUPYTER_PORT:-8888}"
    export VISUALIZER_PORT="${VISUALIZER_PORT:-3000}"
    export GRAPHEXP_PORT="${GRAPHEXP_PORT:-8080}"
    export PROMETHEUS_PORT="${PROMETHEUS_PORT:-9090}"
    export GRAFANA_PORT="${GRAFANA_PORT:-3001}"
    export ALERTMANAGER_PORT="${ALERTMANAGER_PORT:-9093}"
    export OPENSEARCH_PORT="${OPENSEARCH_PORT:-9200}"
    export OPENSEARCH_DASHBOARDS_PORT="${OPENSEARCH_DASHBOARDS_PORT:-5601}"
    export PULSAR_PORT="${PULSAR_PORT:-6650}"
    export PULSAR_ADMIN_PORT="${PULSAR_ADMIN_PORT:-8081}"
    
    # Network Configuration
    export NETWORK_NAME="${NETWORK_NAME:-hcd-janusgraph-network}"
}

# ==============================================================================
# 4. COLOR DEFINITIONS
# ==============================================================================

init_colors() {
    # Only use colors if terminal supports it
    if [ -t 1 ]; then
        export RED='\033[0;31m'
        export GREEN='\033[0;32m'
        export YELLOW='\033[1;33m'
        export BLUE='\033[0;34m'
        export CYAN='\033[0;36m'
        export MAGENTA='\033[0;35m'
        export NC='\033[0m'  # No Color
    else
        export RED=''
        export GREEN=''
        export YELLOW=''
        export BLUE=''
        export CYAN=''
        export MAGENTA=''
        export NC=''
    fi
}

# ==============================================================================
# 5. LOGGING FUNCTIONS
# ==============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $*${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $*${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $*${NC}"
}

log_error() {
    echo -e "${RED}❌ $*${NC}" >&2
}

log_step() {
    echo -e "${CYAN}▶ $*${NC}"
}

log_header() {
    echo ""
    echo "=========================================="
    echo "$*"
    echo "=========================================="
    echo ""
}

# ==============================================================================
# 6. PODMAN VALIDATION
# ==============================================================================

check_podman() {
    local connection="${1:-$PODMAN_CONNECTION}"
    
    log_step "Checking Podman machine: $connection"
    
    if ! command -v podman &> /dev/null; then
        log_error "Podman is not installed"
        log_info "Install: brew install podman"
        return 1
    fi
    
    if ! podman --remote --connection "$connection" ps >/dev/null 2>&1; then
        log_error "Podman machine '$connection' not accessible"
        log_info "Start it with: podman machine start $connection"
        return 1
    fi
    
    log_success "Podman machine accessible"
    return 0
}

# Wrapper to route podman commands through configured remote connection.
podman_cmd() {
    podman --remote --connection "$PODMAN_CONNECTION" "$@"
}

check_podman_compose() {
    log_step "Checking podman-compose"
    
    if ! command -v podman-compose &> /dev/null; then
        log_error "podman-compose is not installed"
        log_info "Install: brew install podman-compose"
        return 1
    fi
    
    log_success "podman-compose available"
    return 0
}

# ==============================================================================
# 7. PORT AVAILABILITY CHECKS
# ==============================================================================

check_port() {
    local port=$1
    local service=${2:-"service"}
    
    if command -v lsof &> /dev/null; then
        if lsof -Pi ":$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_warning "Port $port already in use ($service)"
            return 1
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -an | grep -q ":$port.*LISTEN"; then
            log_warning "Port $port already in use ($service)"
            return 1
        fi
    else
        log_warning "Cannot check port $port (lsof/netstat not available)"
        return 0  # Assume available if we can't check
    fi
    
    return 0
}

check_all_ports() {
    log_step "Checking port availability"
    
    local ports_ok=true
    
    check_port "$HCD_CQL_PORT" "HCD CQL" || ports_ok=false
    check_port "$JANUSGRAPH_GREMLIN_PORT" "JanusGraph Gremlin" || ports_ok=false
    check_port "$JUPYTER_PORT" "Jupyter" || ports_ok=false
    check_port "$GRAFANA_PORT" "Grafana" || ports_ok=false
    check_port "$PROMETHEUS_PORT" "Prometheus" || ports_ok=false
    
    if [ "$ports_ok" = true ]; then
        log_success "All ports available"
        return 0
    else
        log_warning "Some ports are in use (may cause conflicts)"
        return 1
    fi
}

# ==============================================================================
# 8. SERVICE HEALTH CHECKS
# ==============================================================================

check_service() {
    local service_name=$1
    local project="${2:-$COMPOSE_PROJECT_NAME}"
    
    if podman_cmd ps --filter "label=project=$project" --format "{{.Names}}" | grep -q "$service_name"; then
        return 0
    else
        return 1
    fi
}

wait_for_service() {
    local service_name=$1
    local timeout=${2:-120}
    local interval=${3:-5}
    
    log_step "Waiting for $service_name (timeout: ${timeout}s)"
    
    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if check_service "$service_name" >/dev/null 2>&1; then
            log_success "$service_name is ready"
            return 0
        fi
        sleep "$interval"
        elapsed=$((elapsed + interval))
        echo -n "."
    done
    
    echo ""
    log_error "Timeout waiting for $service_name"
    return 1
}

check_all_services() {
    local project="${1:-$COMPOSE_PROJECT_NAME}"
    
    log_step "Checking service status"
    
    local services=("hcd-server" "janusgraph" "opensearch" "pulsar")
    local all_running=true
    
    for service in "${services[@]}"; do
        if check_service "$service" "$project"; then
            log_success "$service is running"
        else
            log_warning "$service is not running"
            all_running=false
        fi
    done
    
    if [ "$all_running" = true ]; then
        return 0
    else
        return 1
    fi
}

# ==============================================================================
# 9. DIRECTORY MANAGEMENT
# ==============================================================================

create_directories() {
    log_step "Creating required directories"
    
    local dirs=(
        "exports"
        "notebooks"
        "data/samples"
        "logs"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$PROJECT_ROOT/$dir" ]; then
            mkdir -p "$PROJECT_ROOT/$dir"
            log_success "Created: $dir"
        fi
    done
}

# ==============================================================================
# 10. CLEANUP FUNCTIONS
# ==============================================================================

cleanup_containers() {
    local project="${1:-$COMPOSE_PROJECT_NAME}"
    
    log_step "Cleaning up containers for project: $project"
    
    # Stop containers
    podman_cmd stop $(podman_cmd ps -q --filter "label=project=$project") 2>/dev/null || true
    
    # Remove containers
    podman_cmd rm $(podman_cmd ps -aq --filter "label=project=$project") 2>/dev/null || true
    
    log_success "Containers cleaned up"
}

cleanup_networks() {
    log_step "Cleaning up networks"
    
    podman_cmd network prune -f 2>/dev/null || true
    
    log_success "Networks cleaned up"
}

cleanup_volumes() {
    local project="${1:-$COMPOSE_PROJECT_NAME}"
    
    log_warning "This will DELETE ALL DATA for project: $project"
    read -p "Continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "Aborted"
        return 1
    fi

    log_step "Cleaning up volumes"
    
    podman_cmd volume rm $(podman_cmd volume ls -q --filter "label=project=$project") 2>/dev/null || true
    
    log_success "Volumes cleaned up"
}

# ==============================================================================
# 11. DEPLOYMENT HELPERS
# ==============================================================================

deploy_with_compose() {
    local compose_file="${1:-docker-compose.full.yml}"
    local project="${2:-$COMPOSE_PROJECT_NAME}"
    
    log_step "Deploying with podman-compose"
    log_info "Project: $project"
    log_info "Compose file: $compose_file"
    
    cd "$PROJECT_ROOT/config/compose"
    
    podman-compose -p "$project" -f "$compose_file" up -d --build
    
    if [ $? -eq 0 ]; then
        log_success "Deployment successful"
        return 0
    else
        log_error "Deployment failed"
        return 1
    fi
}

stop_with_compose() {
    local compose_file="${1:-docker-compose.full.yml}"
    local project="${2:-$COMPOSE_PROJECT_NAME}"
    
    log_step "Stopping services"
    
    cd "$PROJECT_ROOT/config/compose"
    
    podman-compose -p "$project" -f "$compose_file" down
    
    log_success "Services stopped"
}

# ==============================================================================
# 12. VALIDATION FUNCTIONS
# ==============================================================================

validate_environment() {
    log_header "Environment Validation"
    
    local validation_ok=true
    
    # Check Podman
    if ! check_podman; then
        validation_ok=false
    fi
    
    # Check podman-compose
    if ! check_podman_compose; then
        validation_ok=false
    fi
    
    # Check ports (non-fatal)
    check_all_ports || true
    
    if [ "$validation_ok" = true ]; then
        log_success "Environment validation passed"
        return 0
    else
        log_error "Environment validation failed"
        return 1
    fi
}

# ==============================================================================
# 13. INITIALIZATION
# ==============================================================================

init_common() {
    # Initialize all common components
    init_paths
    load_environment
    set_defaults
    init_colors
}

# ==============================================================================
# 14. DISPLAY FUNCTIONS
# ==============================================================================

display_access_info() {
    local project="${1:-$COMPOSE_PROJECT_NAME}"
    
    log_header "🎉 Deployment Complete!"
    
    echo "📊 WEB INTERFACES:"
    echo "   Jupyter Lab:          http://localhost:$JUPYTER_PORT"
    echo "   JanusGraph Visualizer: http://localhost:$VISUALIZER_PORT"
    echo "   Graphexp:             http://localhost:$GRAPHEXP_PORT"
    echo "   Grafana:              http://localhost:$GRAFANA_PORT (admin/admin)"
    echo "   Prometheus:           http://localhost:$PROMETHEUS_PORT"
    echo "   OpenSearch Dashboards: http://localhost:$OPENSEARCH_DASHBOARDS_PORT"
    echo ""
    echo "🔌 API ENDPOINTS:"
    echo "   JanusGraph Gremlin:   ws://localhost:$JANUSGRAPH_GREMLIN_PORT/gremlin"
    echo "   HCD CQL:              localhost:$HCD_CQL_PORT"
    echo "   OpenSearch:           http://localhost:$OPENSEARCH_PORT"
    echo "   Pulsar:               pulsar://localhost:$PULSAR_PORT"
    echo ""
    echo "💻 CLI ACCESS:"
    echo "   Gremlin Console:"
    echo "     podman exec -it ${project}_gremlin-console_1 bin/gremlin.sh"
    echo ""
    echo "   CQL Shell:"
    echo "     podman exec -it ${project}_cqlsh-client_1 cqlsh hcd-server"
    echo ""
    echo "📁 SHARED DIRECTORIES:"
    echo "   Notebooks: $PROJECT_ROOT/notebooks"
    echo "   Exports:   $PROJECT_ROOT/exports"
    echo ""
}

# ==============================================================================
# AUTO-INITIALIZATION
# ==============================================================================

# Automatically initialize when sourced (unless SKIP_INIT is set)
if [ -z "${SKIP_INIT:-}" ]; then
    init_common
fi

# ==============================================================================
# END OF COMMON.SH
# ==============================================================================

# Made with Bob
