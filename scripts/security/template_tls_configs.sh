#!/usr/bin/env bash
# =============================================================================
# TLS Config Templating Script
# =============================================================================
# Replaces placeholder passwords in JanusGraph and Cassandra TLS config files
# with values from environment variables (or .env file).
#
# Usage:
#   source .env  # or export variables manually
#   ./scripts/security/template_tls_configs.sh
#
# Required environment variables:
#   JANUSGRAPH_KEYSTORE_PASSWORD
#   JANUSGRAPH_TRUSTSTORE_PASSWORD
#   HCD_KEYSTORE_PASSWORD
#   HCD_TRUSTSTORE_PASSWORD
#
# The script writes to config/janusgraph/*.yaml IN PLACE.
# Back up originals before running if needed.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

JANUSGRAPH_TLS_YAML="$PROJECT_ROOT/config/janusgraph/janusgraph-server-tls.yaml"
CASSANDRA_TLS_YAML="$PROJECT_ROOT/config/janusgraph/cassandra-tls.yaml"

WEAK_PATTERNS="^changeit$|^password$|^admin$|^12345|^YOUR_|^CHANGE_ME|^PLACEHOLDER"

validate_password() {
    local name="$1" value="$2"
    if [[ -z "$value" ]]; then
        log_error "$name is not set"
        return 1
    fi
    if echo "$value" | grep -qEi "$WEAK_PATTERNS"; then
        log_error "$name still contains a weak/placeholder value: '$value'"
        return 1
    fi
    if [[ ${#value} -lt 12 ]]; then
        log_warn "$name is shorter than 12 characters (${#value} chars)"
    fi
    return 0
}

errors=0

for var in JANUSGRAPH_KEYSTORE_PASSWORD JANUSGRAPH_TRUSTSTORE_PASSWORD \
           HCD_KEYSTORE_PASSWORD HCD_TRUSTSTORE_PASSWORD; do
    if ! validate_password "$var" "${!var:-}"; then
        ((errors++))
    fi
done

if [[ $errors -gt 0 ]]; then
    log_error "$errors required password variable(s) missing or weak. Aborting."
    echo ""
    echo "Set them via:"
    echo "  export JANUSGRAPH_KEYSTORE_PASSWORD=\$(openssl rand -base64 24)"
    echo "  export JANUSGRAPH_TRUSTSTORE_PASSWORD=\$(openssl rand -base64 24)"
    echo "  export HCD_KEYSTORE_PASSWORD=\$(openssl rand -base64 24)"
    echo "  export HCD_TRUSTSTORE_PASSWORD=\$(openssl rand -base64 24)"
    exit 1
fi

template_file() {
    local file="$1"
    shift
    if [[ ! -f "$file" ]]; then
        log_warn "Config file not found, skipping: $file"
        return
    fi

    local tmp
    tmp="$(mktemp)"
    cp "$file" "$tmp"

    while [[ $# -ge 2 ]]; do
        local pattern="$1" replacement="$2"
        shift 2
        sed -i.bak "s|${pattern}|${replacement}|g" "$tmp"
        rm -f "$tmp.bak"
    done

    if diff -q "$file" "$tmp" > /dev/null 2>&1; then
        log_info "No changes needed: $file"
    else
        cp "$tmp" "$file"
        log_info "Templated: $file"
    fi
    rm -f "$tmp"
}

log_info "Templating JanusGraph server TLS config..."
template_file "$JANUSGRAPH_TLS_YAML" \
    "keyStorePassword: changeit" "keyStorePassword: ${JANUSGRAPH_KEYSTORE_PASSWORD}" \
    "trustStorePassword: changeit" "trustStorePassword: ${JANUSGRAPH_TRUSTSTORE_PASSWORD}"

log_info "Templating Cassandra TLS config..."
template_file "$CASSANDRA_TLS_YAML" \
    "keystore_password: changeit" "keystore_password: ${HCD_KEYSTORE_PASSWORD}" \
    "truststore_password: changeit" "truststore_password: ${HCD_TRUSTSTORE_PASSWORD}"

log_info "TLS config templating complete."

remaining=$(grep -c 'changeit' "$JANUSGRAPH_TLS_YAML" "$CASSANDRA_TLS_YAML" 2>/dev/null | tail -1 || true)
if [[ "$remaining" =~ [1-9] ]]; then
    log_warn "Some 'changeit' values may remain in commented sections — review manually."
fi

echo ""
log_info "Done. Verify with:"
echo "  grep -n 'changeit' config/janusgraph/*.yaml"
