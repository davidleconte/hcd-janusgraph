#!/bin/bash
# Automated Rollback for JanusGraph Banking Platform
# Usage: ./rollback-deployment.sh [environment] [revision]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-}"
REVISION="${2:-}"
NAMESPACE="janusgraph-banking-${ENVIRONMENT}"
ARGOCD_APP="janusgraph-banking-${ENVIRONMENT}"

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
Usage: $0 [environment] [revision]

Rollback JanusGraph Banking Platform to a previous revision.

Arguments:
  environment    Target environment (dev/staging/prod)
  revision       Git revision to rollback to (optional - uses previous if not specified)

Examples:
  $0 dev                    # Rollback dev to previous revision
  $0 staging v1.2.0         # Rollback staging to specific tag
  $0 prod abc123            # Rollback prod to specific commit

EOF
}

validate_inputs() {
    if [[ -z "$ENVIRONMENT" ]]; then
        log_error "Missing required argument: environment"
        print_usage
        exit 1
    fi
    
    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT (must be dev, staging, or prod)"
        exit 1
    fi
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found - please install kubectl"
        exit 1
    fi
    
    # Check if argocd CLI is available
    if ! command -v argocd &> /dev/null; then
        log_error "argocd CLI not found - please install argocd CLI"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace '$NAMESPACE' not found"
        exit 1
    fi
}

get_current_revision() {
    log_info "Getting current revision..."
    
    local current_revision=$(argocd app get "$ARGOCD_APP" -o json | jq -r '.status.sync.revision')
    
    if [[ -z "$current_revision" ]] || [[ "$current_revision" == "null" ]]; then
        log_error "Could not determine current revision"
        exit 1
    fi
    
    echo "$current_revision"
}

get_previous_revision() {
    log_info "Getting previous revision from ArgoCD history..."
    
    local previous_revision=$(argocd app history "$ARGOCD_APP" -o json | jq -r '.[1].revision')
    
    if [[ -z "$previous_revision" ]] || [[ "$previous_revision" == "null" ]]; then
        log_error "Could not determine previous revision"
        exit 1
    fi
    
    echo "$previous_revision"
}

create_backup() {
    log_info "Creating backup before rollback..."
    
    local backup_name="pre-rollback-$(date +%Y%m%d-%H%M%S)"
    
    # Backup current state
    kubectl get all -n "$NAMESPACE" -o yaml > "/tmp/${backup_name}.yaml"
    
    log_success "Backup created: /tmp/${backup_name}.yaml"
}

check_health() {
    local namespace=$1
    
    log_info "Checking deployment health..."
    
    # Check if all pods are running
    local total_pods=$(kubectl get pods -n "$namespace" --no-headers 2>/dev/null | wc -l)
    local running_pods=$(kubectl get pods -n "$namespace" --no-headers 2>/dev/null | grep -c "Running" || echo "0")
    
    if [[ $running_pods -lt $total_pods ]]; then
        log_warn "Not all pods are running ($running_pods/$total_pods)"
        return 1
    fi
    
    # Check StatefulSets
    local statefulsets=$(kubectl get statefulsets -n "$namespace" --no-headers 2>/dev/null | wc -l)
    if [[ $statefulsets -gt 0 ]]; then
        local ready_statefulsets=$(kubectl get statefulsets -n "$namespace" --no-headers 2>/dev/null | awk '{if ($2==$3) print $1}' | wc -l)
        if [[ $ready_statefulsets -lt $statefulsets ]]; then
            log_warn "Not all StatefulSets are ready ($ready_statefulsets/$statefulsets)"
            return 1
        fi
    fi
    
    log_success "Deployment is healthy"
    return 0
}

perform_rollback() {
    local target_revision=$1
    
    log_info "Rolling back to revision: $target_revision"
    
    # Sync ArgoCD application to target revision
    argocd app sync "$ARGOCD_APP" \
        --revision "$target_revision" \
        --prune \
        --timeout 600
    
    # Wait for sync to complete
    log_info "Waiting for rollback to complete..."
    argocd app wait "$ARGOCD_APP" \
        --health \
        --timeout 600
    
    log_success "Rollback completed"
}

verify_rollback() {
    local target_revision=$1
    
    log_info "Verifying rollback..."
    
    # Check current revision
    local current_revision=$(get_current_revision)
    
    if [[ "$current_revision" != "$target_revision" ]]; then
        log_error "Rollback verification failed"
        log_error "Expected: $target_revision"
        log_error "Current:  $current_revision"
        return 1
    fi
    
    # Check health
    if ! check_health "$NAMESPACE"; then
        log_error "Deployment is not healthy after rollback"
        return 1
    fi
    
    log_success "Rollback verified successfully"
    return 0
}

confirm_rollback() {
    local current_rev=$1
    local target_rev=$2
    
    echo
    log_warn "Rollback Operation Summary:"
    echo "  Environment:      $ENVIRONMENT"
    echo "  Namespace:        $NAMESPACE"
    echo "  Current Revision: $current_rev"
    echo "  Target Revision:  $target_rev"
    echo
    log_warn "⚠️  WARNING: This will rollback the deployment!"
    log_warn "⚠️  Ensure you have recent backups before proceeding."
    echo
    
    read -p "Do you want to proceed with rollback? (yes/no): " -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi
}

send_notification() {
    local status=$1
    local revision=$2
    
    # Placeholder for notification integration
    # Integrate with Slack, email, PagerDuty, etc.
    
    log_info "Sending notification: Rollback $status for $ENVIRONMENT to $revision"
}

# Main execution
main() {
    log_info "JanusGraph Banking Platform - Automated Rollback"
    echo
    
    validate_inputs
    
    # Get current revision
    CURRENT_REVISION=$(get_current_revision)
    log_info "Current revision: $CURRENT_REVISION"
    
    # Determine target revision
    if [[ -z "$REVISION" ]]; then
        TARGET_REVISION=$(get_previous_revision)
        log_info "No revision specified, using previous: $TARGET_REVISION"
    else
        TARGET_REVISION="$REVISION"
        log_info "Target revision: $TARGET_REVISION"
    fi
    
    # Check if already at target revision
    if [[ "$CURRENT_REVISION" == "$TARGET_REVISION" ]]; then
        log_warn "Already at target revision: $TARGET_REVISION"
        exit 0
    fi
    
    # Confirm rollback
    confirm_rollback "$CURRENT_REVISION" "$TARGET_REVISION"
    
    # Create backup
    create_backup
    
    # Perform rollback
    if perform_rollback "$TARGET_REVISION"; then
        log_success "Rollback initiated successfully"
    else
        log_error "Rollback failed"
        send_notification "FAILED" "$TARGET_REVISION"
        exit 1
    fi
    
    # Verify rollback
    if verify_rollback "$TARGET_REVISION"; then
        log_success "Rollback completed and verified"
        send_notification "SUCCESS" "$TARGET_REVISION"
    else
        log_error "Rollback verification failed"
        send_notification "FAILED" "$TARGET_REVISION"
        exit 1
    fi
    
    # Run validation
    log_info "Running deployment validation..."
    if [[ -f "scripts/k8s/validate-deployment.sh" ]]; then
        bash scripts/k8s/validate-deployment.sh "$NAMESPACE"
    fi
    
    echo
    log_success "Rollback operation completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Monitor the deployment for any issues"
    echo "2. Check application logs:"
    echo "   kubectl logs -n $NAMESPACE -l app=janusgraph --tail=100"
    echo "3. Verify data integrity"
    echo "4. Update incident documentation"
    echo
}

# Run main function
main

# Made with Bob
