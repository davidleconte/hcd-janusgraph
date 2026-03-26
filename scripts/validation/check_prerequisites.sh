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
# Author: David LECONTE, IBM WW | Tiger Team - Watsonx.Data, Global Product Specialist
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
readonly DETERMINISTIC_MIN_CPUS=12
readonly DETERMINISTIC_MIN_MEMORY_GIB=24
readonly DETERMINISTIC_MIN_DISK_GIB=250

# Track status
PREREQ_ERRORS=0
PREREQ_WARNINGS=0
PREREQ_CAN_AUTO_FIX=false
CURRENT_PODMAN_MACHINE=""
readonly RUN_TS="$(date -u +"%Y%m%dT%H%M%SZ")"
readonly LOG_DIR="${PROJECT_ROOT}/exports/prereq-checks"
readonly LOG_FILE="${LOG_DIR}/prereq-check-${RUN_TS}.log"
readonly SUMMARY_FILE="${LOG_DIR}/prereq-check-${RUN_TS}.summary"
readonly LATEST_POINTER="${LOG_DIR}/latest.log"

# Logging functions
log_header() { echo -e "\n${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }
log_section() { echo -e "\n${CYAN}▶ $1${NC}"; }
log_success() { echo -e "  ${GREEN}✓${NC} $1"; }
log_warning() { echo -e "  ${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "  ${RED}✗${NC} $1"; }
log_info() { echo -e "  ${BLUE}ℹ${NC} $1"; }
log_hint() { echo -e "    ${YELLOW}→${NC} $1"; }

increment_error() {
    ((PREREQ_ERRORS += 1))
}

increment_warning() {
    ((PREREQ_WARNINGS += 1))
}

# =============================================================================
# Check Functions
# =============================================================================

init_logging() {
    mkdir -p "${LOG_DIR}"
    # Duplicate all output to logfile for post-mortem analysis.
    exec > >(tee -a "${LOG_FILE}") 2>&1
    ln -snf "$(basename "${LOG_FILE}")" "${LATEST_POINTER}"
}

check_conda_installed() {
    log_section "Checking Conda installation..."

    if command -v conda &> /dev/null; then
        log_success "Conda is installed"
        return 0
    else
        log_error "Conda is NOT installed"
        log_hint "Install Miniforge: brew install --cask miniforge"
        log_hint "Or download from: https://github.com/conda-forge/miniforge"
        increment_error
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
        increment_error
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

        increment_error
        return 1
    elif [[ "$CONDA_DEFAULT_ENV" != "$REQUIRED_CONDA_ENV" ]]; then
        log_warning "Wrong environment active: $CONDA_DEFAULT_ENV"
        log_hint "Switch to: conda activate $REQUIRED_CONDA_ENV"

        # This is blocking for deterministic behavior.
        increment_error
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
        increment_error
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
        increment_error
        return 1
    fi
}

check_podman_installed() {
    log_section "Checking Podman installation..."

    if command -v podman &> /dev/null; then
        local podman_ver
        podman_ver=$(podman --version 2>/dev/null || echo "unknown")
        log_success "Podman is installed: $podman_ver"
        return 0
    else
        log_error "Podman is NOT installed"
        log_hint "Install: brew install podman podman-desktop"
        log_hint "Or download from: https://podman.io/getting-started/installation"
        increment_error
        return 1
    fi
}

check_podman_connection() {
    log_section "Checking Podman connection health..."

    if podman info >/dev/null 2>&1; then
        log_success "Podman connection is reachable"
        return 0
    else
        log_error "Podman connection is NOT reachable"
        log_hint "Start machine: podman machine start"
        log_hint "Verify: podman machine list"
        increment_error
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
        increment_error
        return 1
    fi

    # Check for running machine
    local running_machine
    running_machine=$(podman machine list 2>/dev/null | grep "Currently running" | awk '{print $1}' | sed 's/\*$//' || true)

    if [[ -n "$running_machine" ]]; then
        CURRENT_PODMAN_MACHINE="$running_machine"
        log_success "Podman machine running: $running_machine"
        return 0
    fi

    # Check for stopped machine
    local stopped_machine
    stopped_machine=$(podman machine list 2>/dev/null | grep -v "NAME\|Currently running" | awk '{print $1}' | sed 's/\*$//' | head -1 || true)

    if [[ -n "$stopped_machine" ]]; then
        log_error "Podman machine '$stopped_machine' exists but is NOT running"
        log_hint "Start it: podman machine start $stopped_machine"
        increment_error
        return 1
    fi

    log_error "No Podman machine is running"
    increment_error
    return 1
}

check_podman_machine_resources() {
    log_section "Checking deterministic Podman machine resources..."

    local running_line
    running_line="$(podman machine list 2>/dev/null | grep "Currently running" || true)"

    if [[ -z "${running_line}" ]]; then
        log_error "Cannot validate resources: no running Podman machine"
        increment_error
        return 1
    fi

    local cpus memory_str disk_str
    cpus="$(echo "${running_line}" | awk '{print $(NF-2)}' || true)"
    memory_str="$(echo "${running_line}" | awk '{print $(NF-1)}' || true)"
    disk_str="$(echo "${running_line}" | awk '{print $NF}' || true)"

    local memory_num disk_num
    memory_num="$(echo "${memory_str}" | sed -E 's/[^0-9].*$//' || true)"
    disk_num="$(echo "${disk_str}" | sed -E 's/[^0-9].*$//' || true)"

    if [[ -z "${cpus}" || -z "${memory_num}" || -z "${disk_num}" ]]; then
        log_warning "Could not parse machine resource values from podman output"
        log_hint "Observed line: ${running_line}"
        increment_warning
        return 1
    fi

    log_info "Detected resources -> CPU: ${cpus}, Memory: ${memory_str}, Disk: ${disk_str}"

    local local_error=0
    if (( cpus < DETERMINISTIC_MIN_CPUS )); then
        log_error "CPU too low for deterministic profile: ${cpus} < ${DETERMINISTIC_MIN_CPUS}"
        local_error=1
    fi
    if (( memory_num < DETERMINISTIC_MIN_MEMORY_GIB )); then
        log_error "Memory too low for deterministic profile: ${memory_str} < ${DETERMINISTIC_MIN_MEMORY_GIB}GiB"
        local_error=1
    fi
    if (( disk_num < DETERMINISTIC_MIN_DISK_GIB )); then
        log_error "Disk too low for deterministic profile: ${disk_str} < ${DETERMINISTIC_MIN_DISK_GIB}GiB"
        local_error=1
    fi

    if (( local_error == 1 )); then
        log_hint "Recreate machine with: podman machine init --cpus 12 --memory 24576 --disk-size 250 --now"
        increment_error
        return 1
    fi

    log_success "Podman resource profile satisfies deterministic requirements"
    return 0
}

check_podman_compose() {
    log_section "Checking podman-compose..."

    if command -v podman-compose &> /dev/null; then
        log_success "podman-compose is installed"
        return 0
    else
        log_error "podman-compose is NOT installed (required for deployment scripts)"
        log_hint "Install: brew install podman-compose"
        increment_error
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
        increment_warning
        return 1
    fi
}

check_repo_runtime_files() {
    log_section "Checking required runtime scripts/files..."

    local missing=0
    local required_paths=(
        "scripts/testing/run_demo_pipeline_repeatable.sh"
        "scripts/deployment/deterministic_setup_and_proof_wrapper.sh"
        "scripts/deployment/deploy_full_stack.sh"
        "scripts/validation/preflight_check.sh"
        "scripts/validation/validate_podman_isolation.sh"
        "config/compose/docker-compose.full.yml"
    )

    local rel_path
    for rel_path in "${required_paths[@]}"; do
        if [[ -e "${PROJECT_ROOT}/${rel_path}" ]]; then
            log_success "Found: ${rel_path}"
        else
            log_error "Missing required file: ${rel_path}"
            missing=1
        fi
    done

    if [[ "${missing}" -eq 1 ]]; then
        log_hint "Repository appears incomplete; verify checkout and branch state."
        increment_error
        return 1
    fi

    return 0
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
            increment_warning
        fi
        return 0
    else
        log_warning ".env file does NOT exist"
        if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
            log_hint "Copy example: cp .env.example .env"
        else
            log_hint "Create it with required variables"
        fi
        increment_warning
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
            increment_warning
            return 1
        fi
    else
        log_error "HCD tarball NOT found at $hcd_dir"
        if [[ -d "$PROJECT_ROOT/vendor/hcd-1.2.3" ]]; then
            log_hint "Create symlink: ln -sf vendor/hcd-1.2.3 hcd-1.2.3"
        else
            log_hint "Run: git lfs pull"
        fi
        increment_error
        return 1
    fi
}

check_existing_stack_health() {
    log_section "Checking existing stack health (fail-fast bad states)..."

    local project_name
    project_name="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"

    local podman_out
    podman_out="$(podman ps -a --format '{{.Names}}\t{{.Status}}' 2>/dev/null | grep "^${project_name}_" || true)"

    if [[ -z "${podman_out}" ]]; then
        log_info "No existing '${project_name}' containers detected (clean state before deploy)"
        return 0
    fi

    log_info "Detected existing '${project_name}' containers. Validating statuses..."

    local bad_states=0
    local unhealthy=0
    local created_states=0
    while IFS= read -r line; do
        [[ -z "${line}" ]] && continue
        local cname cstatus
        cname="$(echo "${line}" | awk -F'\t' '{print $1}')"
        cstatus="$(echo "${line}" | awk -F'\t' '{print $2}')"

        if echo "${cstatus}" | grep -Eiq 'unhealthy'; then
            log_error "${cname}: ${cstatus}"
            unhealthy=1
            continue
        fi

        if echo "${cstatus}" | grep -Eiq 'Dead|Error'; then
            log_error "${cname}: ${cstatus}"
            bad_states=1
            continue
        fi

        if echo "${cstatus}" | grep -Eiq 'Exited'; then
            log_warning "${cname}: ${cstatus} (stopped from previous run)"
            created_states=1
            continue
        fi

        if echo "${cstatus}" | grep -Eiq 'Created'; then
            log_warning "${cname}: ${cstatus} (transitional state)"
            created_states=1
            continue
        fi

        log_success "${cname}: ${cstatus}"
    done <<< "${podman_out}"

    if [[ "${bad_states}" -eq 1 || "${unhealthy}" -eq 1 ]]; then
        log_hint "Detected unhealthy/exited/failed containers. Run deterministic reset before pipeline:"
        log_hint "cd config/compose && bash ../../scripts/deployment/stop_full_stack.sh"
        log_hint "Then rerun prerequisite check."
        increment_error
        return 1
    fi

    if [[ "${created_states}" -eq 1 ]]; then
        log_warning "Some containers are in 'Created' transitional state; pipeline can continue and will enforce health gates."
        increment_warning
    fi

    log_success "Existing container stack state is healthy enough to proceed"
    return 0
}

# =============================================================================
# Summary and Exit
# =============================================================================

write_summary_artifact() {
    local final_code="$1"

    cat > "${SUMMARY_FILE}" <<EOF
timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
project_root=${PROJECT_ROOT}
log_file=${LOG_FILE}
errors=${PREREQ_ERRORS}
warnings=${PREREQ_WARNINGS}
final_exit_code=${final_code}
podman_machine=${CURRENT_PODMAN_MACHINE}
required_conda_env=${REQUIRED_CONDA_ENV}
required_python=${REQUIRED_PYTHON_VERSION}
deterministic_min_cpus=${DETERMINISTIC_MIN_CPUS}
deterministic_min_memory_gib=${DETERMINISTIC_MIN_MEMORY_GIB}
deterministic_min_disk_gib=${DETERMINISTIC_MIN_DISK_GIB}
EOF
}

print_summary() {
    log_header
    echo -e "${BOLD}PREREQUISITE CHECK SUMMARY${NC}"
    log_header
    echo ""

    local exit_code=0
    if [[ $PREREQ_ERRORS -gt 0 ]]; then
        echo -e "  ${RED}✗ Errors:   $PREREQ_ERRORS${NC} (blocking)"
        if [[ $PREREQ_WARNINGS -gt 0 ]]; then
            echo -e "  ${YELLOW}⚠ Warnings: $PREREQ_WARNINGS${NC} (non-blocking)"
        fi
        echo ""
        echo -e "  ${YELLOW}Fix the errors above before running the pipeline.${NC}"
        echo ""
        exit_code=1
    elif [[ $PREREQ_WARNINGS -gt 0 ]]; then
        echo -e "  ${YELLOW}⚠ Warnings: $PREREQ_WARNINGS${NC} (non-blocking)"
        echo ""
        echo -e "  ${GREEN}Prerequisites met, but review warnings above.${NC}"
        echo ""
        exit_code=2
    else
        echo -e "  ${GREEN}✓ All prerequisites met!${NC}"
        echo ""
        echo -e "  ${GREEN}Ready to run: bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh --status-report exports/deterministic-status.json${NC}"
        echo ""
        exit_code=0
    fi

    log_info "Detailed log: ${LOG_FILE}"
    log_info "Summary artifact: ${SUMMARY_FILE}"
    write_summary_artifact "${exit_code}"

    return "${exit_code}"
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    init_logging

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
    check_podman_connection || true
    check_podman_machine || true
    check_podman_machine_resources || true
    check_podman_compose || true
    check_uv_installed || true
    check_repo_runtime_files || true
    check_env_file || true
    check_hcd_tarball || true
    check_existing_stack_health || true

    # Print summary and exit
    print_summary
}

# Run if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
