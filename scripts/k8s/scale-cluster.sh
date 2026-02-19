#!/bin/bash
# Scale JanusGraph Banking Platform Components
# Usage: ./scale-cluster.sh [component] [replicas] [namespace]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPONENT="${1:-}"
REPLICAS="${2:-}"
NAMESPACE="${3:-janusgraph-banking}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_usage() {
    cat << EOF
Usage: $0 [component] [replicas] [namespace]

Components:
  janusgraph          Scale JanusGraph StatefulSet
  hcd                 Scale HCD CassandraDatacenter
  opensearch          Scale OpenSearch cluster
  pulsar-broker       Scale Pulsar brokers
  pulsar-bookkeeper   Scale Pulsar BookKeeper
  mission-control     Scale Mission Control server

Examples:
  $0 janusgraph 5 janusgraph-banking-prod
  $0 hcd 7 janusgraph-banking-prod
  $0 opensearch 5 janusgraph-banking-prod

EOF
}

validate_inputs() {
    if [[ -z "$COMPONENT" ]] || [[ -z "$REPLICAS" ]]; then
        log_error "Missing required arguments"
        print_usage
        exit 1
    fi
    
    if ! [[ "$REPLICAS" =~ ^[0-9]+$ ]]; then
        log_error "Replicas must be a positive integer"
        exit 1
    fi
    
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace '$NAMESPACE' not found"
        exit 1
    fi
}

get_current_replicas() {
    local component=$1
    local current=0
    
    case $component in
        janusgraph)
            current=$(kubectl get statefulset janusgraph -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
            ;;
        hcd)
            current=$(kubectl get cassandradatacenters -n "$NAMESPACE" -o jsonpath='{.items[0].spec.size}' 2>/dev/null || echo "0")
            ;;
        opensearch)
            current=$(kubectl get statefulset opensearch-cluster-master -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
            ;;
        pulsar-broker)
            current=$(kubectl get statefulset pulsar-broker -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
            ;;
        pulsar-bookkeeper)
            current=$(kubectl get statefulset pulsar-bookkeeper -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
            ;;
        mission-control)
            current=$(kubectl get deployment mission-control-server -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
            ;;
        *)
            log_error "Unknown component: $component"
            exit 1
            ;;
    esac
    
    echo "$current"
}

scale_janusgraph() {
    local replicas=$1
    
    log_info "Scaling JanusGraph to $replicas replicas..."
    
    kubectl scale statefulset janusgraph -n "$NAMESPACE" --replicas="$replicas"
    
    log_info "Waiting for JanusGraph pods to be ready..."
    kubectl rollout status statefulset/janusgraph -n "$NAMESPACE" --timeout=600s
    
    log_success "JanusGraph scaled to $replicas replicas"
}

scale_hcd() {
    local replicas=$1
    
    log_info "Scaling HCD to $replicas nodes..."
    
    # Get datacenter name
    local dc_name=$(kubectl get cassandradatacenters -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -z "$dc_name" ]]; then
        log_error "No CassandraDatacenter found"
        exit 1
    fi
    
    kubectl patch cassandradatacenter "$dc_name" -n "$NAMESPACE" --type='json' \
        -p="[{'op': 'replace', 'path': '/spec/size', 'value': $replicas}]"
    
    log_info "Waiting for HCD nodes to be ready (this may take several minutes)..."
    
    # Wait for all pods to be ready
    local timeout=1800  # 30 minutes
    local elapsed=0
    local interval=10
    
    while [[ $elapsed -lt $timeout ]]; do
        local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l cassandra.datastax.com/datacenter="$dc_name" --no-headers 2>/dev/null | grep -c "Running" || echo "0")
        
        if [[ $ready_pods -eq $replicas ]]; then
            log_success "HCD scaled to $replicas nodes"
            return 0
        fi
        
        log_info "HCD scaling in progress... ($ready_pods/$replicas ready)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    log_error "Timeout waiting for HCD to scale"
    exit 1
}

scale_opensearch() {
    local replicas=$1
    
    log_info "Scaling OpenSearch to $replicas nodes..."
    
    kubectl scale statefulset opensearch-cluster-master -n "$NAMESPACE" --replicas="$replicas"
    
    log_info "Waiting for OpenSearch pods to be ready..."
    kubectl rollout status statefulset/opensearch-cluster-master -n "$NAMESPACE" --timeout=600s
    
    log_success "OpenSearch scaled to $replicas nodes"
}

scale_pulsar_broker() {
    local replicas=$1
    
    log_info "Scaling Pulsar brokers to $replicas replicas..."
    
    kubectl scale statefulset pulsar-broker -n "$NAMESPACE" --replicas="$replicas"
    
    log_info "Waiting for Pulsar broker pods to be ready..."
    kubectl rollout status statefulset/pulsar-broker -n "$NAMESPACE" --timeout=600s
    
    log_success "Pulsar brokers scaled to $replicas replicas"
}

scale_pulsar_bookkeeper() {
    local replicas=$1
    
    log_info "Scaling Pulsar BookKeeper to $replicas replicas..."
    
    kubectl scale statefulset pulsar-bookkeeper -n "$NAMESPACE" --replicas="$replicas"
    
    log_info "Waiting for BookKeeper pods to be ready..."
    kubectl rollout status statefulset/pulsar-bookkeeper -n "$NAMESPACE" --timeout=600s
    
    log_success "Pulsar BookKeeper scaled to $replicas replicas"
}

scale_mission_control() {
    local replicas=$1
    
    log_info "Scaling Mission Control server to $replicas replicas..."
    
    kubectl scale deployment mission-control-server -n "$NAMESPACE" --replicas="$replicas"
    
    log_info "Waiting for Mission Control pods to be ready..."
    kubectl rollout status deployment/mission-control-server -n "$NAMESPACE" --timeout=300s
    
    log_success "Mission Control server scaled to $replicas replicas"
}

confirm_scaling() {
    local component=$1
    local current=$2
    local target=$3
    
    echo
    log_warn "Scaling Operation Summary:"
    echo "  Component: $component"
    echo "  Current:   $current replicas"
    echo "  Target:    $target replicas"
    echo "  Namespace: $NAMESPACE"
    echo
    
    if [[ $target -lt $current ]]; then
        log_warn "⚠️  WARNING: Scaling DOWN may cause data loss or service disruption!"
        log_warn "⚠️  Ensure you have recent backups before proceeding."
    fi
    
    read -p "Do you want to proceed? (yes/no): " -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Scaling operation cancelled"
        exit 0
    fi
}

# Main execution
main() {
    log_info "JanusGraph Banking Platform - Scaling Tool"
    echo
    
    validate_inputs
    
    local current_replicas=$(get_current_replicas "$COMPONENT")
    
    if [[ "$current_replicas" == "0" ]]; then
        log_error "Component '$COMPONENT' not found in namespace '$NAMESPACE'"
        exit 1
    fi
    
    if [[ "$current_replicas" == "$REPLICAS" ]]; then
        log_info "Component '$COMPONENT' is already at $REPLICAS replicas"
        exit 0
    fi
    
    confirm_scaling "$COMPONENT" "$current_replicas" "$REPLICAS"
    
    case $COMPONENT in
        janusgraph)
            scale_janusgraph "$REPLICAS"
            ;;
        hcd)
            scale_hcd "$REPLICAS"
            ;;
        opensearch)
            scale_opensearch "$REPLICAS"
            ;;
        pulsar-broker)
            scale_pulsar_broker "$REPLICAS"
            ;;
        pulsar-bookkeeper)
            scale_pulsar_bookkeeper "$REPLICAS"
            ;;
        mission-control)
            scale_mission_control "$REPLICAS"
            ;;
    esac
    
    echo
    log_success "Scaling operation completed successfully!"
    log_info "Run './validate-deployment.sh $NAMESPACE' to verify cluster health"
}

# Run main function
main

# Made with Bob
