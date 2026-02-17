#!/usr/bin/env bash
# =============================================================================
# Preflight Check Script - Complete Pre-Deployment Validation
# =============================================================================
# Purpose: Run all validation checks before deployment
# Usage:   ./scripts/validation/preflight_check.sh [--fix] [--strict]
# Exit:    0 = success, 1 = error
#
# Options:
#   --fix     Attempt to auto-fix common issues
#   --strict  Treat warnings as errors
#
# Checks performed:
#   1. Python environment (conda, version, packages)
#   2. Podman isolation (project name, container names, networks)
#   3. Environment configuration (.env file)
#   4. Dependencies (requirements files)
#   5. Build prerequisites (HCD tarball, Dockerfiles)
#   6. Security (placeholder passwords, certificates)
#   7. Port availability
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
readonly MAGENTA='\033[0;35m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
readonly REQUIRED_CONDA_ENV="janusgraph-analysis"
readonly REQUIRED_PYTHON_VERSION="3.11"
source "$PROJECT_ROOT/scripts/utils/podman_connection.sh"

# Load .env BEFORE setting defaults (to allow .env to override)
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    # Source .env but ignore errors for variables already set
    set +e
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env" 2>/dev/null || true
    set -e
fi

# Set defaults after .env is loaded (only if not already set)
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"
PODMAN_CONNECTION="${PODMAN_CONNECTION:-}"
PODMAN_CONNECTION="$(resolve_podman_connection "${PODMAN_CONNECTION}")"

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[✅]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[⚠️]${NC} $*"; }
log_error() { echo -e "${RED}[❌]${NC} $*"; }
log_section() { echo -e "\n${MAGENTA}━━━ $* ━━━${NC}"; }
log_subsection() { echo -e "${CYAN}--- $* ---${NC}"; }

# Track errors and warnings
ERRORS=0
WARNINGS=0
AUTO_FIX=false
STRICT_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            AUTO_FIX=true
            shift
            ;;
        --strict)
            STRICT_MODE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--fix] [--strict]"
            echo ""
            echo "Options:"
            echo "  --fix     Attempt to auto-fix common issues"
            echo "  --strict  Treat warnings as errors"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--fix] [--strict]"
            exit 1
            ;;
    esac
done

# =============================================================================
# Section 1: Python Environment
# =============================================================================

check_python_environment() {
    log_section "1. Python Environment"

    # Check .venv doesn't exist
    log_subsection "Checking for .venv directory"
    if [[ -d "$PROJECT_ROOT/.venv" ]]; then
        log_error ".venv directory exists (causes conflicts)"
        if [[ "$AUTO_FIX" == "true" ]]; then
            log_info "Auto-fixing: Removing .venv directory..."
            rm -rf "$PROJECT_ROOT/.venv"
            log_success "Removed .venv directory"
        else
            log_info "Fix: rm -rf $PROJECT_ROOT/.venv"
            ((ERRORS += 1))
        fi
    else
        log_success "No .venv directory (good!)"
    fi

    # Check conda available
    log_subsection "Checking conda"
    if ! command -v conda &> /dev/null; then
        log_error "Conda is not installed"
        ((ERRORS += 1))
        return
    fi
    log_success "Conda is available"

    # Check conda env exists
    if ! conda env list | grep -q "^${REQUIRED_CONDA_ENV} "; then
        log_error "Conda environment '$REQUIRED_CONDA_ENV' does not exist"
        log_info "Create: conda create -n $REQUIRED_CONDA_ENV python=$REQUIRED_PYTHON_VERSION"
        ((ERRORS += 1))
        return
    fi
    log_success "Conda environment exists"

    # Check conda env is active
    log_subsection "Checking conda environment activation"
    if [[ -z "${CONDA_DEFAULT_ENV:-}" ]]; then
        log_error "No conda environment is active"
        log_info "Activate: conda activate $REQUIRED_CONDA_ENV"
        ((ERRORS += 1))
    elif [[ "$CONDA_DEFAULT_ENV" != "$REQUIRED_CONDA_ENV" ]]; then
        log_error "Wrong conda environment: $CONDA_DEFAULT_ENV (expected: $REQUIRED_CONDA_ENV)"
        ((ERRORS += 1))
    else
        log_success "Correct conda environment active: $CONDA_DEFAULT_ENV"
    fi

    # Check Python version
    log_subsection "Checking Python version"
    if command -v python &> /dev/null; then
        local py_ver
        py_ver=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
        if [[ "$py_ver" == "$REQUIRED_PYTHON_VERSION" ]]; then
            log_success "Python version correct: $py_ver"
        else
            log_error "Wrong Python version: $py_ver (expected: $REQUIRED_PYTHON_VERSION)"
            ((ERRORS += 1))
        fi
    else
        log_error "Python not available"
        ((ERRORS += 1))
    fi

    # Check uv available
    log_subsection "Checking package manager (uv)"
    if command -v uv &> /dev/null; then
        log_success "uv is available: $(uv --version 2>/dev/null || echo 'unknown')"
    else
        log_warning "uv is not installed (recommended for faster package management)"
        log_info "Install: pip install uv"
        ((WARNINGS += 1))
    fi
}

# =============================================================================
# Section 2: Environment Configuration
# =============================================================================

check_environment_config() {
    log_section "2. Environment Configuration"

    local env_file="$PROJECT_ROOT/.env"

    # Check .env exists
    log_subsection "Checking .env file"
    if [[ ! -f "$env_file" ]]; then
        log_error ".env file not found"
        if [[ "$AUTO_FIX" == "true" ]] && [[ -f "$PROJECT_ROOT/.env.example" ]]; then
            log_info "Auto-fixing: Copying .env.example to .env..."
            cp "$PROJECT_ROOT/.env.example" "$env_file"
            log_success "Created .env from .env.example"
        else
            log_info "Fix: cp $PROJECT_ROOT/.env.example $env_file"
            ((ERRORS += 1))
        fi
        return
    fi
    log_success ".env file exists"

    # Check COMPOSE_PROJECT_NAME
    log_subsection "Checking COMPOSE_PROJECT_NAME"
    if grep -q "^COMPOSE_PROJECT_NAME=" "$env_file" 2>/dev/null; then
        local proj_name
        proj_name=$(grep "^COMPOSE_PROJECT_NAME=" "$env_file" | cut -d'=' -f2)
        log_success "COMPOSE_PROJECT_NAME is set: $proj_name"
    else
        log_error "COMPOSE_PROJECT_NAME is NOT set"
        if [[ "$AUTO_FIX" == "true" ]]; then
            log_info "Auto-fixing: Adding COMPOSE_PROJECT_NAME=janusgraph-demo..."
            echo "" >> "$env_file"
            echo "# Podman Isolation (REQUIRED)" >> "$env_file"
            echo "COMPOSE_PROJECT_NAME=janusgraph-demo" >> "$env_file"
            log_success "Added COMPOSE_PROJECT_NAME"
        else
            log_info "Fix: Add 'COMPOSE_PROJECT_NAME=janusgraph-demo' to .env"
            ((ERRORS += 1))
        fi
    fi

    # Check PODMAN_CONNECTION
    log_subsection "Checking PODMAN_CONNECTION"
    if grep -q "^PODMAN_CONNECTION=" "$env_file" 2>/dev/null; then
        local conn
        conn=$(grep "^PODMAN_CONNECTION=" "$env_file" | cut -d'=' -f2)
        log_success "PODMAN_CONNECTION is set: $conn"
    else
        log_warning "PODMAN_CONNECTION not set (using default: $PODMAN_CONNECTION)"
        if [[ "$AUTO_FIX" == "true" ]]; then
            echo "PODMAN_CONNECTION=${PODMAN_CONNECTION}" >> "$env_file"
            log_success "Added PODMAN_CONNECTION"
        else
            ((WARNINGS += 1))
        fi
    fi

    # Check for placeholder passwords
    log_subsection "Checking for placeholder passwords"
    local placeholder_count=0
    if grep -q "CHANGE_ME" "$env_file" 2>/dev/null; then
        placeholder_count=$((placeholder_count + 1))
    fi
    if grep -q "changeit" "$env_file" 2>/dev/null; then
        placeholder_count=$((placeholder_count + 1))
    fi

    if [[ $placeholder_count -gt 0 ]]; then
        log_warning "Found placeholder passwords in .env (OK for development)"
        log_info "Update passwords before production deployment"
        ((WARNINGS += 1))
    else
        log_success "No placeholder passwords found"
    fi
}

# =============================================================================
# Section 3: Podman Configuration
# =============================================================================

check_podman_config() {
    log_section "3. Podman Configuration"

    # Check podman available
    log_subsection "Checking Podman"
    if ! command -v podman &> /dev/null; then
        log_error "Podman is not installed"
        ((ERRORS += 1))
        return
    fi
    log_success "Podman is installed"

    # Check podman-compose available
    if ! command -v podman-compose &> /dev/null; then
        log_warning "podman-compose is not installed"
        log_info "Install: pip install podman-compose"
        ((WARNINGS += 1))
    else
        log_success "podman-compose is available"
    fi

    # Check podman machine connection
    log_subsection "Checking Podman machine connection"
    if podman --remote --connection "$PODMAN_CONNECTION" ps &>/dev/null; then
        log_success "Podman machine '$PODMAN_CONNECTION' is accessible"
    else
        log_warning "Cannot connect to Podman machine '$PODMAN_CONNECTION'"
        log_info "Start with: podman machine start $PODMAN_CONNECTION"
        ((WARNINGS += 1))
    fi

    # Check for container_name overrides in compose files
    log_subsection "Checking docker-compose files for container_name overrides"
    local compose_dir="$PROJECT_ROOT/config/compose"
    if [[ -d "$compose_dir" ]]; then
        local total_overrides=0
        for file in "$compose_dir"/*.yml; do
            if [[ -f "$file" ]]; then
                local count
                count=0
                if ! count=$(grep -c "container_name:" "$file" 2>/dev/null); then
                    count=0
                fi
                if [[ $count -gt 0 ]]; then
                    log_error "  $(basename "$file"): $count container_name override(s)"
                    total_overrides=$((total_overrides + count))
                fi
            fi
        done

        if [[ $total_overrides -gt 0 ]]; then
            log_error "CRITICAL: $total_overrides container_name overrides found"
            log_info "This BREAKS project isolation. Remove all container_name: lines."
            ((ERRORS += 1))
        else
            log_success "No container_name overrides found (good!)"
        fi
    fi
}

# =============================================================================
# Section 4: Build Prerequisites
# =============================================================================

check_build_prerequisites() {
    log_section "4. Build Prerequisites"

    # Check HCD tarball exists
    log_subsection "Checking HCD tarball"
    local hcd_dir="$PROJECT_ROOT/hcd-1.2.3"

    if [[ -d "$hcd_dir" ]] || [[ -L "$hcd_dir" ]]; then
        # Verify key files exist (follow symlinks)
        if [[ -f "$hcd_dir/bin/hcd" ]]; then
            log_success "HCD directory exists with correct structure"
        else
            log_error "HCD directory exists but missing bin/hcd"
            log_info "Verify vendor/hcd-1.2.3 is complete or re-extract"
            ((ERRORS += 1))
        fi
    else
        # Check if vendor has HCD
        if [[ -d "$PROJECT_ROOT/vendor/hcd-1.2.3" ]]; then
            log_error "HCD not found at project root"
            log_info "Create symlink: ln -sf vendor/hcd-1.2.3 hcd-1.2.3"
            ((ERRORS += 1))
        else
            log_error "HCD not found in vendor/ directory"
            log_info "Run: git lfs pull"
            log_info "Then: ln -sf vendor/hcd-1.2.3 hcd-1.2.3"
            ((ERRORS += 1))
        fi
    fi

    # Check Dockerfiles exist
    log_subsection "Checking Dockerfiles"
    local dockerfiles=(
        "docker/hcd/Dockerfile"
        "docker/api/Dockerfile"
        "docker/consumers/Dockerfile"
        "docker/jupyter/Dockerfile"
        "docker/opensearch/Dockerfile"
    )

    for df in "${dockerfiles[@]}"; do
        if [[ -f "$PROJECT_ROOT/$df" ]]; then
            log_success "$df exists"
        else
            log_error "$df MISSING"
            ((ERRORS += 1))
        fi
    done
}

# =============================================================================
# Section 5: Dependencies
# =============================================================================

check_dependencies() {
    log_section "5. Dependencies"

    # Check deterministic dependency files exist
    log_subsection "Checking dependency lock files"
    local req_files=(
        "pyproject.toml"
        "uv.lock"
        "requirements.txt"
        "requirements-dev.txt"
        "requirements-security.txt"
        "requirements-tracing.txt"
    )

    for req in "${req_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$req" ]]; then
            log_success "$req exists"
        else
            log_warning "$req not found"
            ((WARNINGS += 1))
        fi
    done

    # Check critical packages (only if Python is available)
    if command -v python &> /dev/null && [[ "${CONDA_DEFAULT_ENV:-}" == "$REQUIRED_CONDA_ENV" ]]; then
        log_subsection "Checking critical Python packages"
        local packages=("gremlinpython" "pydantic" "pytest")

        for pkg in "${packages[@]}"; do
            if python -c "import $pkg" 2>/dev/null; then
                log_success "$pkg is installed"
            else
                log_warning "$pkg is not installed"
                ((WARNINGS += 1))
            fi
        done
    fi
}

# =============================================================================
# Section 6: Security
# =============================================================================

check_security() {
    log_section "6. Security"

    # Check SSL certificates
    log_subsection "Checking SSL certificates"
    local cert_dir="$PROJECT_ROOT/config/certs/ca"
    if [[ -f "$cert_dir/ca-cert.pem" ]]; then
        log_success "CA certificate exists"

        # Check certificate validity
        if command -v openssl &> /dev/null; then
            local expiry
            expiry=$(openssl x509 -enddate -noout -in "$cert_dir/ca-cert.pem" 2>/dev/null | cut -d= -f2)
            if [[ -n "$expiry" ]]; then
                log_info "Certificate expires: $expiry"
            fi
        fi
    else
        log_warning "SSL certificates not found"
        log_info "Generate with: ./scripts/security/generate_certificates.sh"
        ((WARNINGS += 1))
    fi

    # Check .gitignore for sensitive files
    log_subsection "Checking .gitignore"
    local gitignore="$PROJECT_ROOT/.gitignore"
    if [[ -f "$gitignore" ]]; then
        local patterns=(".env" "*.pem" "*.key" ".vault-keys")
        for pattern in "${patterns[@]}"; do
            if grep -q "^$pattern" "$gitignore" 2>/dev/null || grep -q "^\\*$pattern" "$gitignore" 2>/dev/null; then
                log_success ".gitignore includes: $pattern"
            else
                log_warning ".gitignore may be missing: $pattern"
                ((WARNINGS += 1))
            fi
        done
    fi
}

# =============================================================================
# Section 7: Port Availability
# =============================================================================

check_ports() {
    log_section "7. Port Availability"

    local ports=(
        "19042:HCD CQL"
        "18182:JanusGraph"
        "8888:Jupyter"
        "3000:Visualizer"
        "9090:Prometheus"
        "3001:Grafana"
    )

    for port_info in "${ports[@]}"; do
        local port="${port_info%%:*}"
        local service="${port_info##*:}"

        if lsof -Pi ":$port" -sTCP:LISTEN -t &>/dev/null; then
            local pid
            pid=$(lsof -Pi ":$port" -sTCP:LISTEN -t 2>/dev/null | head -1)
            log_warning "Port $port ($service) is in use (PID: $pid)"
            ((WARNINGS += 1))
        else
            log_success "Port $port ($service) is available"
        fi
    done
}

# =============================================================================
# Summary
# =============================================================================

print_summary() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "            PREFLIGHT CHECK SUMMARY"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    if [[ $ERRORS -gt 0 ]]; then
        log_error "ERRORS:   $ERRORS"
    else
        log_success "ERRORS:   0"
    fi

    if [[ $WARNINGS -gt 0 ]]; then
        log_warning "WARNINGS: $WARNINGS"
    else
        log_success "WARNINGS: 0"
    fi

    echo ""

    # Exit decision
    if [[ $ERRORS -gt 0 ]]; then
        log_error "PREFLIGHT CHECK FAILED"
        echo ""
        echo "Fix the errors above before deploying."
        echo "Run with --fix to auto-fix common issues."
        echo ""
        return 1
    elif [[ $WARNINGS -gt 0 ]] && [[ "$STRICT_MODE" == "true" ]]; then
        log_warning "PREFLIGHT CHECK FAILED (strict mode)"
        echo ""
        return 1
    else
        log_success "PREFLIGHT CHECK PASSED"
        echo ""
        echo "Ready to deploy with:"
        echo "  cd config/compose"
        echo "  podman-compose -p $PROJECT_NAME -f docker-compose.full.yml up -d"
        echo ""
        return 0
    fi
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "           PREFLIGHT CHECKS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Project:    $PROJECT_NAME"
    echo "Root:       $PROJECT_ROOT"
    echo "Auto-fix:   $AUTO_FIX"
    echo "Strict:     $STRICT_MODE"
    echo ""

    # Run all checks
    check_python_environment
    check_environment_config
    check_podman_config
    check_build_prerequisites
    check_dependencies
    check_security
    check_ports

    # Print summary and exit
    if print_summary; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
