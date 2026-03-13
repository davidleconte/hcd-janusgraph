#!/usr/bin/env bash
# =============================================================================
# Prerequisite Check Script - User-Friendly Pre-Flight Validation
# =============================================================================
# Purpose: Check all prerequisites BEFORE running any pipeline or deployment
#          Provide clear, actionable messages to users BEFORE errors occur
#
# Usage:   source scripts/validation/check_prerequisites.sh
#          Or run directly: ./scripts/validation/check_prerequisites.sh
#
# Exit codes:
#   0 = All prerequisites met
#   1 = Missing critical prerequisite (blocking)
#   2 = Warning (non-blocking but recommended)
#
# Co-Authored-By: AdaL <adal@sylph.ai>
# =============================================================================

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
readonly REQUIRED_CONDA_ENV="janusgraph-analysis"
readonly REQUIRED_PYTHON_VERSION="3.11"

# Track status
PREREQ_ERRORS=0
PREREQ_WARNINGS=0
PREREQ_CAN_AUTO_FIX=false

# Logging functions
log_header() { echo -e "\n${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }
log_section() { echo -e "\n${CYAN}▶ $1${NC}"; }
log_success() { echo -e "  ${GREEN}✓${NC} $1"; }
log_warning() { echo -e "  ${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "  ${RED}✗${NC} $1"; }
log_info() { echo -e "  ${BLUE}ℹ${NC} $1"; }
log_hint() { echo -e "    ${YELLOW}→${NC} $1"; }

# =============================================================================
# Check Functions
# =============================================================================

check_conda_installed() {
    log_section "Checking Conda installation..."
    
    if command -v conda &> /dev/null; then
        log_success "Conda is installed"
        return 0
    else
        log_error "Conda is NOT installed"
        log_hint "Install Miniforge: brew install --cask miniforge"
        log_hint "Or download from: https://github.com/conda-forge/miniforge"
        ((PREREQ_ERRORS += 1))
        return 1
    fi
}

check_conda_env_exists() {
    log_section "Checking Conda environment '$REQUIRED_CONDA_ENV'..."
    
    if conda env list 2>/dev/null | grep -q "^${REQUIRED_CONDA_ENV} "; then
        log_success "Environment '$REQUIRED_CONDA_ENV' exists"
        return 0
    else
        log_error "Environment '$REQUIRED_CONDA_ENV' does NOT exist"
        log_hint "Create it: conda create -n $REQUIRED_CONDA_ENV python=$REQUIRED_PYTHON_VERSION"
        log_hint "Or use environment.yml: conda env create -f environment.yml"
        ((PREREQ_ERRORS += 1))
        PREREQ_CAN_AUTO_FIX=true
        return 1
    fi
}

check_conda_env_active() {
    log_section "Checking active Conda environment..."
    
    if [[ -z "${CONDA_DEFAULT_ENV:-}" ]]; then
        log_warning "No Conda environment is currently active"
        log_hint "Activate: conda activate $REQUIRED_CONDA_ENV"
        log_hint "For auto-activation, install direnv: brew install direnv && direnv allow"
        
        # Try auto-activation if possible
        if conda env list 2>/dev/null | grep -q "^${REQUIRED_CONDA_ENV} "; then
            log_info "Attempting auto-activation..."
            # shellcheck disable=SC1090
            eval "$(conda shell.bash hook 2>/dev/null)" || true
            if conda activate "$REQUIRED_CONDA_ENV" 2>/dev/null; then
                if [[ "${CONDA_DEFAULT_ENV:-}" == "$REQUIRED_CONDA_ENV" ]]; then
                    log_success "Auto-activated environment: $REQUIRED_CONDA_ENV"
                    export CONDA_DEFAULT_ENV="$REQUIRED_CONDA_ENV"
                    return 0
                fi
            fi
        fi
        
        ((PREREQ_ERRORS += 1))
        return 1
    elif [[ "$CONDA_DEFAULT_ENV" != "$REQUIRED_CONDA_ENV" ]]; then
        log_warning "Wrong environment active: $CONDA_DEFAULT_ENV"
        log_hint "Switch to: conda activate $REQUIRED_CONDA_ENV"
        ((PREREQ_WARNINGS += 1))
        return 1
    else
        log_success "Correct environment active: $CONDA_DEFAULT_ENV"
        return 0
    fi
}

check_python_version() {
    log_section "Checking Python version..."
    
    if ! command -v python &> /dev/null; then
        log_error "Python is not available in current environment"
        log_hint "Ensure conda environment is activated: conda activate $REQUIRED_CONDA_ENV"
        ((PREREQ_ERRORS += 1))
        return 1
    fi
    
    local py_ver
    py_ver=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
    
    if [[ "$py_ver" == "$REQUIRED_PYTHON_VERSION" ]]; then
        log_success "Python version: $py_ver"
        return 0
    else
        log_error "Wrong Python version: $py_ver (expected: $REQUIRED_PYTHON_VERSION)"
        log_hint "Recreate environment: conda create -n $REQUIRED_CONDA_ENV python=$REQUIRED_PYTHON_VERSION"
        ((PREREQ_ERRORS += 1))
        return 1
    fi
}

check_podman_installed() {
    log_section "Checking Podman installation..."
    
    if command -v podman &> /dev/null; then
        local podman_ver
        podman_ver=$(podman --version 2>/dev/null | head -1 || echo "unknown")
        log_success "Podman is installed: $podman_ver"
        return 0
    else
        log_error "Podman is NOT installed"
        log_hint "Install: brew install podman podman-desktop"
        log_hint "Or download from: https://podman.io/getting-started/installation"
        ((PREREQ_ERRORS += 1))
        return 1
    fi
}

check_podman_machine() {
    log_section "Checking Podman machine..."
    
    local machines
    machines=$(podman machine list 2>/dev/null || echo "")
    
    if [[ -z "$machines" ]] || echo "$machines" | grep -q "no machines"; then
        log_error "No Podman machine exists"
        log_hint "Create one: podman machine init --cpus 12 --memory 24576 --disk-size 250"
        ((PREREQ_ERRORS += 1))
        return 1
    fi
    
    # Check for running machine
    local running_machine
    running_machine=$(podman machine list 2>/dev/null | grep "Currently running" | awk '{print $1}' || true)
    
    if [[ -n "$running_machine" ]]; then
        log_success "Podman machine running: $running_machine"
        return 0
    fi
    
    # Check for stopped machine
    local stopped_machine
    stopped_machine=$(podman machine list 2>/dev/null | grep -v "NAME\|Currently running" | awk '{print $1}' | head -1 || true)
    
    if [[ -n "$stopped_machine" ]]; then
        log_warning "Podman machine '$stopped_machine' exists but is NOT running"
        log_hint "Start it: podman machine start $stopped_machine"
        ((PREREQ_WARNINGS += 1))
        return 1
    fi
    
    log_error "No Podman machine is running"
    ((PREREQ_ERRORS += 1))
    return 1
}

check_podman_compose() {
    log_section "Checking podman-compose..."
    
    if command -v podman-compose &> /dev/null; then
        log_success "podman-compose is installed"
        return 0
    else
        log_warning "podman-compose is NOT installed"
        log_hint "Install: pip install podman-compose"
        log_hint "Or: brew install podman-compose"
        ((PREREQ_WARNINGS += 1))
        return 1
    fi
}

check_uv_installed() {
    log_section "Checking uv package manager..."
    
    if command -v uv &> /dev/null; then
        local uv_ver
        uv_ver=$(uv --version 2>/dev/null || echo "unknown")
        log_success "uv is installed: $uv_ver"
        return 0
    else
        log_warning "uv is NOT installed (recommended for faster package management)"
        log_hint "Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
        log_hint "Or: brew install uv"
        ((PREREQ_WARNINGS += 1))
        return 1
    fi
}

check_env_file() {
    log_section "Checking .env configuration..."
    
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        log_success ".env file exists"
        
        # Check for COMPOSE_PROJECT_NAME
        if grep -q "^COMPOSE_PROJECT_NAME=" "$PROJECT_ROOT/.env" 2>/dev/null; then
            local proj_name
            proj_name=$(grep "^COMPOSE_PROJECT_NAME=" "$PROJECT_ROOT/.env" | cut -d'=' -f2)
            log_success "COMPOSE_PROJECT_NAME: $proj_name"
        else
            log_warning "COMPOSE_PROJECT_NAME not set in .env"
            log_hint "Add: echo 'COMPOSE_PROJECT_NAME=janusgraph-demo' >> .env"
            ((PREREQ_WARNINGS += 1))
        fi
        return 0
    else
        log_warning ".env file does NOT exist"
        if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
            log_hint "Copy example: cp .env.example .env"
        else
            log_hint "Create it with required variables"
        fi
        ((PREREQ_WARNINGS += 1))
        return 1
    fi
}

check_hcd_tarball() {
    log_section "Checking HCD tarball..."
    
    local hcd_dir="$PROJECT_ROOT/hcd-1.2.3"
    
    if [[ -d "$hcd_dir" ]] || [[ -L "$hcd_dir" ]]; then
        if [[ -f "$hcd_dir/bin/hcd" ]]; then
            log_success "HCD tarball ready: $hcd_dir"
            return 0
        else
            log_warning "HCD directory exists but incomplete"
            log_hint "Re-extract or verify vendor/hcd-1.2.3"
            ((PREREQ_WARNINGS += 1))
            return 1
        fi
    else
        log_error "HCD tarball NOT found at $hcd_dir"
        if [[ -d "$PROJECT_ROOT/vendor/hcd-1.2.3" ]]; then
            log_hint "Create symlink: ln -sf vendor/hcd-1.2.3 hcd-1.2.3"
        else
            log_hint "Run: git lfs pull"
        fi
        ((PREREQ_ERRORS += 1))
        return 1
    fi
}

# =============================================================================
# Summary and Exit
# =============================================================================

print_summary() {
    log_header
    echo -e "${BOLD}PREREQUISITE CHECK SUMMARY${NC}"
    log_header
    echo ""
    
    if [[ $PREREQ_ERRORS -gt 0 ]]; then
        echo -e "  ${RED}✗ Errors:   $PREREQ_ERRORS${NC} (blocking)"
        echo ""
        echo -e "  ${YELLOW}Fix the errors above before running the pipeline.${NC}"
        echo ""
        return 1
    elif [[ $PREREQ_WARNINGS -gt 0 ]]; then
        echo -e "  ${YELLOW}⚠ Warnings: $PREREQ_WARNINGS${NC} (non-blocking)"
        echo ""
        echo -e "  ${GREEN}Prerequisites met, but review warnings above.${NC}"
        echo ""
        return 2
    else
        echo -e "  ${GREEN}✓ All prerequisites met!${NC}"
        echo ""
        echo -e "  ${GREEN}Ready to run: bash scripts/testing/run_demo_pipeline_repeatable.sh${NC}"
        echo ""
        return 0
    fi
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    log_header
    echo -e "${BOLD}JANUSGRAPH DEMO - PREREQUISITE CHECK${NC}"
    log_header
    echo ""
    echo "Project: $PROJECT_ROOT"
    echo "Time:    $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    echo ""
    
    # Run all checks
    check_conda_installed || true
    check_conda_env_exists || true
    check_conda_env_active || true
    check_python_version || true
    check_podman_installed || true
    check_podman_machine || true
    check_podman_compose || true
    check_uv_installed || true
    check_env_file || true
    check_hcd_tarball || true
    
    # Print summary and exit
    print_summary
}

# Run if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
