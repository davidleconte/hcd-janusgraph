#!/bin/bash
# Validate JanusGraph Banking Platform Deployment
# Usage: ./validate-deployment.sh [namespace]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${1:-janusgraph-banking}"
VALIDATION_PASSED=0
VALIDATION_FAILED=0
VALIDATION_WARNINGS=0

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((VALIDATION_PASSED++))
}

log_warn() {
    echo -e "${YELLOW}[⚠]${NC} $1"
    ((VALIDATION_WARNINGS++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((VALIDATION_FAILED++))
}

print_header() {
    echo
    echo "========================================"
    echo "$1"
    echo "========================================"
}

check_namespace() {
    print_header "Checking Namespace"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_success "Namespace '$NAMESPACE' exists"
    else
        log_error "Namespace '$NAMESPACE' not found"
        exit 1
    fi
}

check_hcd_cluster() {
    print_header "Checking HCD Cluster"
    
    # Check CassandraDatacenter CRD
    if kubectl get cassandradatacenters -n "$NAMESPACE" &> /dev/null; then
        local dc_count=$(kubectl get cassandradatacenters -n "$NAMESPACE" --no-headers | wc -l)
        log_success "CassandraDatacenter CRD found ($dc_count datacenters)"
        
        # List datacenters
        kubectl get cassandradatacenters -n "$NAMESPACE" -o custom-columns=NAME:.metadata.name,SIZE:.spec.size,READY:.status.cassandraOperatorProgress
    else
        log_error "No CassandraDatacenter found"
    fi
    
    # Check HCD pods
    local hcd_pods=$(kubectl get pods -n "$NAMESPACE" -l cassandra.datastax.com/cluster=hcd-cluster-global --no-headers 2>/dev/null | wc -l)
    if [[ $hcd_pods -gt 0 ]]; then
        local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l cassandra.datastax.com/cluster=hcd-cluster-global --no-headers 2>/dev/null | grep -c "Running" || echo "0")
        if [[ $ready_pods -eq $hcd_pods ]]; then
            log_success "All HCD pods running ($ready_pods/$hcd_pods)"
        else
            log_warn "Some HCD pods not ready ($ready_pods/$hcd_pods running)"
        fi
        
        # Show pod status
        kubectl get pods -n "$NAMESPACE" -l cassandra.datastax.com/cluster=hcd-cluster-global
    else
        log_error "No HCD pods found"
    fi
    
    # Check HCD cluster status via nodetool
    local hcd_pod=$(kubectl get pods -n "$NAMESPACE" -l cassandra.datastax.com/cluster=hcd-cluster-global --no-headers 2>/dev/null | head -1 | awk '{print $1}')
    if [[ -n "$hcd_pod" ]]; then
        log_info "Checking HCD cluster status..."
        if kubectl exec -it "$hcd_pod" -n "$NAMESPACE" -- nodetool status 2>/dev/null | grep -q "UN"; then
            log_success "HCD nodes are UP and NORMAL"
            kubectl exec -it "$hcd_pod" -n "$NAMESPACE" -- nodetool status 2>/dev/null || true
        else
            log_warn "HCD cluster status check failed or nodes not ready"
        fi
    fi
}

check_janusgraph() {
    print_header "Checking JanusGraph"
    
    # Check StatefulSet
    if kubectl get statefulset janusgraph -n "$NAMESPACE" &> /dev/null; then
        local desired=$(kubectl get statefulset janusgraph -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
        local ready=$(kubectl get statefulset janusgraph -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
        
        if [[ "$ready" == "$desired" ]]; then
            log_success "JanusGraph StatefulSet ready ($ready/$desired replicas)"
        else
            log_warn "JanusGraph StatefulSet not fully ready ($ready/$desired replicas)"
        fi
        
        kubectl get statefulset janusgraph -n "$NAMESPACE"
    else
        log_error "JanusGraph StatefulSet not found"
    fi
    
    # Check pods
    local jg_pods=$(kubectl get pods -n "$NAMESPACE" -l app=janusgraph --no-headers 2>/dev/null | wc -l)
    if [[ $jg_pods -gt 0 ]]; then
        local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app=janusgraph --no-headers 2>/dev/null | grep -c "Running" || echo "0")
        if [[ $ready_pods -eq $jg_pods ]]; then
            log_success "All JanusGraph pods running ($ready_pods/$jg_pods)"
        else
            log_warn "Some JanusGraph pods not ready ($ready_pods/$jg_pods running)"
        fi
        
        kubectl get pods -n "$NAMESPACE" -l app=janusgraph
    else
        log_error "No JanusGraph pods found"
    fi
    
    # Check PVCs
    local pvc_count=$(kubectl get pvc -n "$NAMESPACE" -l app=janusgraph --no-headers 2>/dev/null | wc -l)
    if [[ $pvc_count -gt 0 ]]; then
        local bound_pvcs=$(kubectl get pvc -n "$NAMESPACE" -l app=janusgraph --no-headers 2>/dev/null | grep -c "Bound" || echo "0")
        if [[ $bound_pvcs -eq $pvc_count ]]; then
            log_success "All JanusGraph PVCs bound ($bound_pvcs/$pvc_count)"
        else
            log_warn "Some JanusGraph PVCs not bound ($bound_pvcs/$pvc_count)"
        fi
    else
        log_warn "No JanusGraph PVCs found"
    fi
    
    # Test JanusGraph connectivity
    local jg_pod=$(kubectl get pods -n "$NAMESPACE" -l app=janusgraph --no-headers 2>/dev/null | head -1 | awk '{print $1}')
    if [[ -n "$jg_pod" ]]; then
        log_info "Testing JanusGraph connectivity..."
        if kubectl exec "$jg_pod" -n "$NAMESPACE" -- curl -s http://localhost:8182?gremlin=g.V().count() &> /dev/null; then
            log_success "JanusGraph Gremlin server responding"
        else
            log_warn "JanusGraph Gremlin server not responding (may still be starting)"
        fi
    fi
}

check_mission_control() {
    print_header "Checking Mission Control"
    
    # Check Mission Control Server
    local mc_server_pods=$(kubectl get pods -n "$NAMESPACE" -l app=mission-control-server --no-headers 2>/dev/null | wc -l)
    if [[ $mc_server_pods -gt 0 ]]; then
        local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app=mission-control-server --no-headers 2>/dev/null | grep -c "Running" || echo "0")
        if [[ $ready_pods -eq $mc_server_pods ]]; then
            log_success "Mission Control Server running ($ready_pods/$mc_server_pods)"
        else
            log_warn "Mission Control Server not fully ready ($ready_pods/$mc_server_pods)"
        fi
        
        kubectl get pods -n "$NAMESPACE" -l app=mission-control-server
    else
        log_error "Mission Control Server not found"
    fi
    
    # Check Mission Control Agent
    local mc_agent_pods=$(kubectl get pods -n "$NAMESPACE" -l app=mission-control-agent --no-headers 2>/dev/null | wc -l)
    if [[ $mc_agent_pods -gt 0 ]]; then
        local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app=mission-control-agent --no-headers 2>/dev/null | grep -c "Running" || echo "0")
        if [[ $ready_pods -eq $mc_agent_pods ]]; then
            log_success "Mission Control Agents running ($ready_pods/$mc_agent_pods)"
        else
            log_warn "Some Mission Control Agents not ready ($ready_pods/$mc_agent_pods)"
        fi
        
        kubectl get pods -n "$NAMESPACE" -l app=mission-control-agent
    else
        log_warn "Mission Control Agents not found"
    fi
    
    # Check PostgreSQL
    if kubectl get statefulset mission-control-postgres -n "$NAMESPACE" &> /dev/null; then
        local pg_ready=$(kubectl get statefulset mission-control-postgres -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
        if [[ "$pg_ready" == "1" ]]; then
            log_success "Mission Control PostgreSQL ready"
        else
            log_warn "Mission Control PostgreSQL not ready"
        fi
    else
        log_warn "Mission Control PostgreSQL not found"
    fi
    
    # Check Redis
    if kubectl get deployment mission-control-redis -n "$NAMESPACE" &> /dev/null; then
        local redis_ready=$(kubectl get deployment mission-control-redis -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
        if [[ "$redis_ready" == "1" ]]; then
            log_success "Mission Control Redis ready"
        else
            log_warn "Mission Control Redis not ready"
        fi
    else
        log_warn "Mission Control Redis not found"
    fi
}

check_storage() {
    print_header "Checking Storage"
    
    # Check StorageClasses
    local storage_classes=("hcd-storage" "janusgraph-storage" "opensearch-storage" "pulsar-storage" "mission-control-storage")
    for sc in "${storage_classes[@]}"; do
        if kubectl get storageclass "$sc" &> /dev/null; then
            log_success "StorageClass '$sc' exists"
        else
            log_warn "StorageClass '$sc' not found"
        fi
    done
    
    # Check all PVCs
    local total_pvcs=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
    if [[ $total_pvcs -gt 0 ]]; then
        local bound_pvcs=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | grep -c "Bound" || echo "0")
        if [[ $bound_pvcs -eq $total_pvcs ]]; then
            log_success "All PVCs bound ($bound_pvcs/$total_pvcs)"
        else
            log_warn "Some PVCs not bound ($bound_pvcs/$total_pvcs)"
        fi
        
        echo
        kubectl get pvc -n "$NAMESPACE"
    else
        log_warn "No PVCs found"
    fi
}

check_services() {
    print_header "Checking Services"
    
    local services=("janusgraph" "janusgraph-headless" "mission-control-server" "mission-control-postgres" "mission-control-redis")
    for svc in "${services[@]}"; do
        if kubectl get service "$svc" -n "$NAMESPACE" &> /dev/null; then
            log_success "Service '$svc' exists"
        else
            log_warn "Service '$svc' not found"
        fi
    done
    
    echo
    kubectl get services -n "$NAMESPACE"
}

check_secrets() {
    print_header "Checking Secrets"
    
    if kubectl get secret mission-control-secrets -n "$NAMESPACE" &> /dev/null; then
        log_success "Mission Control secrets exist"
    else
        log_error "Mission Control secrets not found"
    fi
}

print_summary() {
    print_header "Validation Summary"
    
    echo
    echo "Results:"
    echo "  ✓ Passed:   $VALIDATION_PASSED"
    echo "  ⚠ Warnings: $VALIDATION_WARNINGS"
    echo "  ✗ Failed:   $VALIDATION_FAILED"
    echo
    
    if [[ $VALIDATION_FAILED -eq 0 ]]; then
        if [[ $VALIDATION_WARNINGS -eq 0 ]]; then
            log_success "All validation checks passed!"
            return 0
        else
            log_warn "Validation passed with warnings"
            return 0
        fi
    else
        log_error "Validation failed with $VALIDATION_FAILED errors"
        return 1
    fi
}

print_access_info() {
    print_header "Access Information"
    
    echo
    echo "To access Mission Control UI:"
    echo "  kubectl port-forward svc/mission-control-server 8080:8080 -n $NAMESPACE"
    echo "  Then open: http://localhost:8080"
    echo
    echo "To access JanusGraph Gremlin Server:"
    echo "  kubectl port-forward svc/janusgraph 8182:8182 -n $NAMESPACE"
    echo "  Then test: curl http://localhost:8182?gremlin=g.V().count()"
    echo
    echo "To check HCD cluster status:"
    local hcd_pod=$(kubectl get pods -n "$NAMESPACE" -l cassandra.datastax.com/cluster=hcd-cluster-global --no-headers 2>/dev/null | head -1 | awk '{print $1}')
    if [[ -n "$hcd_pod" ]]; then
        echo "  kubectl exec -it $hcd_pod -n $NAMESPACE -- nodetool status"
    fi
    echo
}

# Main execution
main() {
    log_info "Starting validation for namespace: $NAMESPACE"
    echo
    
    check_namespace
    check_hcd_cluster
    check_janusgraph
    check_mission_control
    check_storage
    check_services
    check_secrets
    
    print_summary
    print_access_info
}

# Run main function
main

# Made with Bob
