#!/usr/bin/env bash
# File: scripts/utils/validation.sh
# Created: 2026-01-28
# Purpose: Input validation and sanitization utilities for shell scripts
# Usage: source scripts/utils/validation.sh

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Validation error counter
VALIDATION_ERRORS=0

#######################################
# Log validation error
# Arguments:
#   $1 - Error message
#######################################
log_validation_error() {
    local message="$1"
    echo -e "${RED}[VALIDATION ERROR]${NC} ${message}" >&2
    ((VALIDATION_ERRORS++))
}

#######################################
# Log validation warning
# Arguments:
#   $1 - Warning message
#######################################
log_validation_warning() {
    local message="$1"
    echo -e "${YELLOW}[VALIDATION WARNING]${NC} ${message}" >&2
}

#######################################
# Log validation success
# Arguments:
#   $1 - Success message
#######################################
log_validation_success() {
    local message="$1"
    echo -e "${GREEN}[VALIDATION OK]${NC} ${message}"
}

#######################################
# Validate hostname or IP address
# Arguments:
#   $1 - Hostname or IP to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_hostname() {
    local hostname="$1"

    # Check if empty
    if [[ -z "${hostname}" ]]; then
        log_validation_error "Hostname cannot be empty"
        return 1
    fi

    # Check length (max 253 characters for FQDN)
    if [[ ${#hostname} -gt 253 ]]; then
        log_validation_error "Hostname too long (max 253 characters): ${hostname}"
        return 1
    fi

    # Validate hostname format (RFC 1123)
    local hostname_regex='^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
    if [[ ! "${hostname}" =~ ${hostname_regex} ]]; then
        # Try IPv4 validation
        if ! validate_ipv4 "${hostname}"; then
            log_validation_error "Invalid hostname format: ${hostname}"
            return 1
        fi
    fi

    log_validation_success "Hostname valid: ${hostname}"
    return 0
}

#######################################
# Validate IPv4 address
# Arguments:
#   $1 - IPv4 address to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_ipv4() {
    local ip="$1"
    local ipv4_regex='^([0-9]{1,3}\.){3}[0-9]{1,3}$'

    if [[ ! "${ip}" =~ ${ipv4_regex} ]]; then
        return 1
    fi

    # Check each octet is 0-255
    IFS='.' read -ra octets <<< "${ip}"
    for octet in "${octets[@]}"; do
        if ((octet < 0 || octet > 255)); then
            return 1
        fi
    done

    return 0
}

#######################################
# Validate port number
# Arguments:
#   $1 - Port number to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_port() {
    local port="$1"

    # Check if numeric
    if ! [[ "${port}" =~ ^[0-9]+$ ]]; then
        log_validation_error "Port must be numeric: ${port}"
        return 1
    fi

    # Check range (1-65535)
    if ((port < 1 || port > 65535)); then
        log_validation_error "Port out of range (1-65535): ${port}"
        return 1
    fi

    # Warn about privileged ports
    if ((port < 1024)); then
        log_validation_warning "Using privileged port: ${port}"
    fi

    log_validation_success "Port valid: ${port}"
    return 0
}

#######################################
# Validate file path (must exist)
# Arguments:
#   $1 - File path to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_file_path() {
    local filepath="$1"

    # Check if empty
    if [[ -z "${filepath}" ]]; then
        log_validation_error "File path cannot be empty"
        return 1
    fi

    # Check for path traversal attempts
    if [[ "${filepath}" =~ \.\. ]]; then
        log_validation_error "Path traversal detected: ${filepath}"
        return 1
    fi

    # Check if file exists
    if [[ ! -f "${filepath}" ]]; then
        log_validation_error "File does not exist: ${filepath}"
        return 1
    fi

    # Check if readable
    if [[ ! -r "${filepath}" ]]; then
        log_validation_error "File not readable: ${filepath}"
        return 1
    fi

    log_validation_success "File path valid: ${filepath}"
    return 0
}

#######################################
# Validate directory path (must exist)
# Arguments:
#   $1 - Directory path to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_directory_path() {
    local dirpath="$1"

    # Check if empty
    if [[ -z "${dirpath}" ]]; then
        log_validation_error "Directory path cannot be empty"
        return 1
    fi

    # Check for path traversal attempts
    if [[ "${dirpath}" =~ \.\. ]]; then
        log_validation_error "Path traversal detected: ${dirpath}"
        return 1
    fi

    # Check if directory exists
    if [[ ! -d "${dirpath}" ]]; then
        log_validation_error "Directory does not exist: ${dirpath}"
        return 1
    fi

    # Check if readable
    if [[ ! -r "${dirpath}" ]]; then
        log_validation_error "Directory not readable: ${dirpath}"
        return 1
    fi

    log_validation_success "Directory path valid: ${dirpath}"
    return 0
}

#######################################
# Sanitize string (remove special characters)
# Arguments:
#   $1 - String to sanitize
# Outputs:
#   Sanitized string
#######################################
sanitize_string() {
    local input="$1"
    # Remove all non-alphanumeric characters except dash, underscore, and dot
    echo "${input}" | tr -cd '[:alnum:]._-'
}

#######################################
# Validate connection name (alphanumeric, dash, underscore)
# Arguments:
#   $1 - Connection name to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_connection_name() {
    local name="$1"

    # Check if empty
    if [[ -z "${name}" ]]; then
        log_validation_error "Connection name cannot be empty"
        return 1
    fi

    # Check length (max 64 characters)
    if [[ ${#name} -gt 64 ]]; then
        log_validation_error "Connection name too long (max 64 characters): ${name}"
        return 1
    fi

    # Validate format (alphanumeric, dash, underscore only)
    local name_regex='^[a-zA-Z0-9_-]+$'
    if [[ ! "${name}" =~ ${name_regex} ]]; then
        log_validation_error "Invalid connection name format (use alphanumeric, dash, underscore): ${name}"
        return 1
    fi

    log_validation_success "Connection name valid: ${name}"
    return 0
}

#######################################
# Validate environment variable name
# Arguments:
#   $1 - Variable name to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_env_var_name() {
    local varname="$1"

    # Check if empty
    if [[ -z "${varname}" ]]; then
        log_validation_error "Environment variable name cannot be empty"
        return 1
    fi

    # Validate format (uppercase letters, numbers, underscore)
    local varname_regex='^[A-Z_][A-Z0-9_]*$'
    if [[ ! "${varname}" =~ ${varname_regex} ]]; then
        log_validation_error "Invalid environment variable name: ${varname}"
        return 1
    fi

    log_validation_success "Environment variable name valid: ${varname}"
    return 0
}

#######################################
# Validate password strength
# Arguments:
#   $1 - Password to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_password_strength() {
    local password="$1"
    local min_length=12

    # Check minimum length
    if [[ ${#password} -lt ${min_length} ]]; then
        log_validation_error "Password too short (minimum ${min_length} characters)"
        return 1
    fi

    # Check for uppercase
    if [[ ! "${password}" =~ [A-Z] ]]; then
        log_validation_error "Password must contain at least one uppercase letter"
        return 1
    fi

    # Check for lowercase
    if [[ ! "${password}" =~ [a-z] ]]; then
        log_validation_error "Password must contain at least one lowercase letter"
        return 1
    fi

    # Check for digit
    if [[ ! "${password}" =~ [0-9] ]]; then
        log_validation_error "Password must contain at least one digit"
        return 1
    fi

    # Check for special character
    if [[ ! "${password}" =~ [^a-zA-Z0-9] ]]; then
        log_validation_error "Password must contain at least one special character"
        return 1
    fi

    log_validation_success "Password meets strength requirements"
    return 0
}

#######################################
# Validate URL format
# Arguments:
#   $1 - URL to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_url() {
    local url="$1"

    # Check if empty
    if [[ -z "${url}" ]]; then
        log_validation_error "URL cannot be empty"
        return 1
    fi

    # Validate URL format
    local url_regex='^(https?|wss?)://[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*(:[0-9]{1,5})?(/.*)?$'
    if [[ ! "${url}" =~ ${url_regex} ]]; then
        log_validation_error "Invalid URL format: ${url}"
        return 1
    fi

    log_validation_success "URL valid: ${url}"
    return 0
}

#######################################
# Validate email address
# Arguments:
#   $1 - Email to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_email() {
    local email="$1"

    # Check if empty
    if [[ -z "${email}" ]]; then
        log_validation_error "Email cannot be empty"
        return 1
    fi

    # Validate email format (basic)
    local email_regex='^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if [[ ! "${email}" =~ ${email_regex} ]]; then
        log_validation_error "Invalid email format: ${email}"
        return 1
    fi

    log_validation_success "Email valid: ${email}"
    return 0
}

#######################################
# Validate numeric value
# Arguments:
#   $1 - Value to validate
#   $2 - Minimum value (optional)
#   $3 - Maximum value (optional)
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_numeric() {
    local value="$1"
    local min="${2:-}"
    local max="${3:-}"

    # Check if numeric
    if ! [[ "${value}" =~ ^-?[0-9]+(\.[0-9]+)?$ ]]; then
        log_validation_error "Value must be numeric: ${value}"
        return 1
    fi

    # Check minimum
    if [[ -n "${min}" ]] && (( $(echo "${value} < ${min}" | bc -l) )); then
        log_validation_error "Value below minimum (${min}): ${value}"
        return 1
    fi

    # Check maximum
    if [[ -n "${max}" ]] && (( $(echo "${value} > ${max}" | bc -l) )); then
        log_validation_error "Value above maximum (${max}): ${value}"
        return 1
    fi

    log_validation_success "Numeric value valid: ${value}"
    return 0
}

#######################################
# Validate boolean value
# Arguments:
#   $1 - Value to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_boolean() {
    local value="$1"

    # Convert to lowercase
    value=$(echo "${value}" | tr '[:upper:]' '[:lower:]')

    # Check if valid boolean
    if [[ ! "${value}" =~ ^(true|false|yes|no|1|0|on|off)$ ]]; then
        log_validation_error "Invalid boolean value: ${value}"
        return 1
    fi

    log_validation_success "Boolean value valid: ${value}"
    return 0
}

#######################################
# Check if validation errors occurred
# Returns:
#   Number of validation errors
#######################################
get_validation_error_count() {
    echo "${VALIDATION_ERRORS}"
}

#######################################
# Reset validation error counter
#######################################
reset_validation_errors() {
    VALIDATION_ERRORS=0
}

#######################################
# Exit if validation errors occurred
# Arguments:
#   $1 - Exit code (default: 1)
#######################################
exit_on_validation_errors() {
    local exit_code="${1:-1}"

    if ((VALIDATION_ERRORS > 0)); then
        echo -e "${RED}Validation failed with ${VALIDATION_ERRORS} error(s)${NC}" >&2
        exit "${exit_code}"
    fi
}

# Export functions
export -f log_validation_error
export -f log_validation_warning
export -f log_validation_success
export -f validate_hostname
export -f validate_ipv4
export -f validate_port
export -f validate_file_path
export -f validate_directory_path
export -f sanitize_string
export -f validate_connection_name
export -f validate_env_var_name
export -f validate_password_strength
export -f validate_url
export -f validate_email
export -f validate_numeric
export -f validate_boolean
export -f get_validation_error_count
export -f reset_validation_errors
export -f exit_on_validation_errors

# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
