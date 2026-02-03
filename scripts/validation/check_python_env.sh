#!/usr/bin/env bash
# =============================================================================
# Python Environment Validation Script
# =============================================================================
# Purpose: Ensure the correct Python environment (conda + Python 3.11) is active
# Usage:   ./scripts/validation/check_python_env.sh
# Exit:    0 = success, 1 = error
#
# Requirements:
#   - Conda environment: janusgraph-analysis
#   - Python version: 3.11.x
#   - Package manager: uv (preferred) or pip
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
readonly REQUIRED_CONDA_ENV="janusgraph-analysis"
readonly REQUIRED_PYTHON_VERSION="3.11"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[✅]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[⚠️]${NC} $*"; }
log_error() { echo -e "${RED}[❌]${NC} $*"; }

# Track errors
ERRORS=0

# =============================================================================
# Validation Functions
# =============================================================================

check_conda_available() {
    log_info "Checking if conda is available..."
    if ! command -v conda &> /dev/null; then
        log_error "Conda is not installed or not in PATH"
        log_info "Install miniforge: https://github.com/conda-forge/miniforge"
        return 1
    fi
    log_success "Conda is available: $(conda --version)"
    return 0
}

check_conda_env_exists() {
    log_info "Checking if conda environment '$REQUIRED_CONDA_ENV' exists..."
    if ! conda env list | grep -q "^${REQUIRED_CONDA_ENV} "; then
        log_error "Conda environment '$REQUIRED_CONDA_ENV' does not exist"
        log_info "Create it with: conda create -n $REQUIRED_CONDA_ENV python=$REQUIRED_PYTHON_VERSION"
        return 1
    fi
    log_success "Conda environment '$REQUIRED_CONDA_ENV' exists"
    return 0
}

check_conda_env_active() {
    log_info "Checking if correct conda environment is active..."
    
    if [[ -z "${CONDA_DEFAULT_ENV:-}" ]]; then
        log_error "No conda environment is active"
        log_info "Activate with: conda activate $REQUIRED_CONDA_ENV"
        return 1
    fi
    
    if [[ "$CONDA_DEFAULT_ENV" != "$REQUIRED_CONDA_ENV" ]]; then
        log_error "Wrong conda environment active: $CONDA_DEFAULT_ENV"
        log_info "Expected: $REQUIRED_CONDA_ENV"
        log_info "Activate with: conda activate $REQUIRED_CONDA_ENV"
        return 1
    fi
    
    log_success "Correct conda environment active: $CONDA_DEFAULT_ENV"
    return 0
}

check_python_version() {
    log_info "Checking Python version..."
    
    if ! command -v python &> /dev/null; then
        log_error "Python is not available in current environment"
        return 1
    fi
    
    local python_version
    python_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    
    if [[ "$python_version" != "$REQUIRED_PYTHON_VERSION" ]]; then
        log_error "Wrong Python version: $python_version (expected: $REQUIRED_PYTHON_VERSION)"
        log_info "Ensure conda environment uses Python $REQUIRED_PYTHON_VERSION"
        return 1
    fi
    
    log_success "Correct Python version: $python_version"
    return 0
}

check_python_path() {
    log_info "Checking Python path is from conda environment..."
    
    local python_path
    python_path=$(which python)
    
    # Python should be from conda environment, not system or .venv
    if [[ "$python_path" == *".venv"* ]]; then
        log_error "Python is from .venv (should be from conda): $python_path"
        log_info "Remove .venv: rm -rf $PROJECT_ROOT/.venv"
        return 1
    fi
    
    if [[ "$python_path" != *"miniforge"* ]] && [[ "$python_path" != *"conda"* ]] && [[ "$python_path" != *"envs/$REQUIRED_CONDA_ENV"* ]]; then
        log_warning "Python path may not be from conda: $python_path"
        log_info "Expected path containing: miniforge, conda, or envs/$REQUIRED_CONDA_ENV"
    else
        log_success "Python path is correct: $python_path"
    fi
    
    return 0
}

check_no_venv() {
    log_info "Checking that .venv directory does not exist..."
    
    if [[ -d "$PROJECT_ROOT/.venv" ]]; then
        log_error ".venv directory exists at: $PROJECT_ROOT/.venv"
        log_info "This can cause Python environment conflicts"
        log_info "Remove with: rm -rf $PROJECT_ROOT/.venv"
        return 1
    fi
    
    log_success "No .venv directory found (good!)"
    return 0
}

check_uv_available() {
    log_info "Checking if uv package manager is available..."
    
    if ! command -v uv &> /dev/null; then
        log_warning "uv is not installed (optional but recommended)"
        log_info "Install with: pip install uv"
        return 0  # Warning, not error
    fi
    
    log_success "uv is available: $(uv --version)"
    return 0
}

check_critical_packages() {
    log_info "Checking critical Python packages..."
    
    local packages=("gremlinpython" "pydantic" "pytest")
    local missing=()
    
    for pkg in "${packages[@]}"; do
        if ! python -c "import $pkg" 2>/dev/null; then
            missing+=("$pkg")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_warning "Missing packages: ${missing[*]}"
        log_info "Install with: uv pip install -r requirements.txt"
        return 0  # Warning, not error - packages can be installed
    fi
    
    log_success "All critical packages available"
    return 0
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    echo ""
    echo "=========================================="
    echo "Python Environment Validation"
    echo "=========================================="
    echo "Project: $PROJECT_ROOT"
    echo "Required: conda env '$REQUIRED_CONDA_ENV' with Python $REQUIRED_PYTHON_VERSION"
    echo ""
    
    # Critical checks (fail fast)
    check_conda_available || ((ERRORS++))
    check_no_venv || ((ERRORS++))
    
    # Environment checks
    if check_conda_env_exists; then
        check_conda_env_active || ((ERRORS++))
    else
        ((ERRORS++))
    fi
    
    # Python checks
    if [[ $ERRORS -eq 0 ]]; then
        check_python_version || ((ERRORS++))
        check_python_path || ((ERRORS++))
    fi
    
    # Optional checks (warnings)
    echo ""
    log_info "Running optional checks..."
    check_uv_available
    
    if [[ $ERRORS -eq 0 ]]; then
        check_critical_packages
    fi
    
    # Summary
    echo ""
    echo "=========================================="
    if [[ $ERRORS -gt 0 ]]; then
        log_error "VALIDATION FAILED: $ERRORS error(s) found"
        echo ""
        echo "Quick fix:"
        echo "  1. rm -rf .venv  # If exists"
        echo "  2. conda activate $REQUIRED_CONDA_ENV"
        echo "  3. uv pip install -r requirements.txt"
        echo ""
        exit 1
    else
        log_success "VALIDATION PASSED: Python environment is correctly configured"
        echo ""
        echo "Current environment:"
        echo "  Conda env: ${CONDA_DEFAULT_ENV:-N/A}"
        echo "  Python:    $(python --version 2>&1)"
        echo "  Path:      $(which python)"
        echo ""
        exit 0
    fi
}

# Run main function
main "$@"
