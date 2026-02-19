#!/bin/bash
# Deploy JanusGraph Banking Platform Helm Chart
# Usage: ./deploy-helm-chart.sh [dev|staging|prod] [site-name]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
HELM_CHART_DIR="${PROJECT_ROOT}/helm/janusgraph-banking"
NAMESPACE="janusgraph-banking"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        log_error "helm not found. Please install Helm 3.8+."
        exit 1
    fi
    
    # Check helm version
    HELM_VERSION=$(helm version --short | grep -oP 'v\K[0-9]+\.[0-9]+')
    if (( $(echo "$HELM_VERSION < 3.8" | bc -l) )); then
        log_error "Helm version 3.8+ required. Current version: $HELM_VERSION"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
        exit 1
    fi
    
    log_info "Prerequisites check passed ✓"
}

add_helm_repos() {
    log_info "Adding Helm repositories..."
    
    helm repo add datastax https://datastax.github.io/charts 2>/dev/null || true
    helm repo add opensearch https://opensearch-project.github.io/helm-charts 2>/dev/null || true
    helm repo add pulsar https://pulsar.apache.org/charts 2>/dev/null || true
    helm repo add hashicorp https://helm.releases.hashicorp.com 2>/dev/null || true
    
    log_info "Updating Helm repositories..."
    helm repo update
    
    log_info "Helm repositories configured ✓"
}

create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warn "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        log_info "Namespace created ✓"
    fi
}

create_secrets() {
    local env=$1
    
    log_info "Creating secrets for environment: $env"
    
    # Check if secrets already exist
    if kubectl get secret mission-control-secrets -n "$NAMESPACE" &> /dev/null; then
        log_warn "Secrets already exist. Skipping creation."
        log_warn "To recreate secrets, delete them first:"
        log_warn "  kubectl delete secret mission-control-secrets -n $NAMESPACE"
        return
    fi
    
    # Generate random passwords for dev/staging
    if [[ "$env" == "dev" ]] || [[ "$env" == "staging" ]]; then
        POSTGRES_PASSWORD=$(openssl rand -base64 32)
        ADMIN_PASSWORD=$(openssl rand -base64 32)
        AGENT_TOKEN=$(openssl rand -base64 32)
    else
        # Production - require manual password input
        log_warn "Production environment detected."
        log_warn "Please provide secure passwords (minimum 16 characters):"
        
        read -sp "PostgreSQL password: " POSTGRES_PASSWORD
        echo
        read -sp "Admin password: " ADMIN_PASSWORD
        echo
        read -sp "Agent token: " AGENT_TOKEN
        echo
        
        # Validate password length
        if [[ ${#POSTGRES_PASSWORD} -lt 16 ]] || [[ ${#ADMIN_PASSWORD} -lt 16 ]] || [[ ${#AGENT_TOKEN} -lt 16 ]]; then
            log_error "Passwords must be at least 16 characters long"
            exit 1
        fi
    fi
    
    # Create Mission Control secrets
    kubectl create secret generic mission-control-secrets \
        --from-literal=postgres-user=mcadmin \
        --from-literal=postgres-password="$POSTGRES_PASSWORD" \
        --from-literal=admin-user=admin \
        --from-literal=admin-password="$ADMIN_PASSWORD" \
        --from-literal=agent-token="$AGENT_TOKEN" \
        -n "$NAMESPACE"
    
    log_info "Secrets created ✓"
    
    # Save passwords to secure location (dev/staging only)
    if [[ "$env" != "prod" ]]; then
        SECRETS_FILE="${PROJECT_ROOT}/.secrets-${env}.txt"
        cat > "$SECRETS_FILE" <<EOF
# Mission Control Secrets - ${env}
# Generated: $(date)
# WARNING: Keep this file secure and do not commit to git

POSTGRES_USER=mcadmin
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
ADMIN_USER=admin
ADMIN_PASSWORD=${ADMIN_PASSWORD}
AGENT_TOKEN=${AGENT_TOKEN}
EOF
        chmod 600 "$SECRETS_FILE"
        log_info "Secrets saved to: $SECRETS_FILE"
    fi
}

update_dependencies() {
    log_info "Updating Helm chart dependencies..."
    
    cd "$HELM_CHART_DIR"
    helm dependency update
    
    log_info "Dependencies updated ✓"
}

deploy_chart() {
    local env=$1
    local site=${2:-""}
    local release_name="janusgraph-banking"
    local values_file="values.yaml"
    
    # Determine values file and release name
    if [[ "$env" == "prod" ]]; then
        values_file="values-prod.yaml"
        if [[ -n "$site" ]]; then
            release_name="janusgraph-banking-${site}"
        fi
    fi
    
    log_info "Deploying Helm chart..."
    log_info "  Environment: $env"
    log_info "  Release: $release_name"
    log_info "  Values file: $values_file"
    if [[ -n "$site" ]]; then
        log_info "  Site: $site"
    fi
    
    cd "$HELM_CHART_DIR"
    
    # Build helm install command
    HELM_CMD="helm upgrade --install $release_name . \
        --namespace $NAMESPACE \
        --values $values_file \
        --wait \
        --timeout 30m"
    
    # Add site-specific overrides for production
    if [[ "$env" == "prod" ]] && [[ -n "$site" ]]; then
        HELM_CMD="$HELM_CMD --set hcd.datacenterName=${site}-dc"
        
        # Set zone-specific configuration based on site
        case "$site" in
            paris)
                HELM_CMD="$HELM_CMD \
                    --set hcd.racks[0].zone=eu-west-3a \
                    --set hcd.racks[1].zone=eu-west-3b \
                    --set hcd.racks[2].zone=eu-west-3c"
                ;;
            london)
                HELM_CMD="$HELM_CMD \
                    --set hcd.racks[0].zone=eu-west-2a \
                    --set hcd.racks[1].zone=eu-west-2b \
                    --set hcd.racks[2].zone=eu-west-2c"
                ;;
            frankfurt)
                HELM_CMD="$HELM_CMD \
                    --set hcd.racks[0].zone=eu-central-1a \
                    --set hcd.racks[1].zone=eu-central-1b \
                    --set hcd.racks[2].zone=eu-central-1c"
                ;;
        esac
    fi
    
    # Execute deployment
    eval "$HELM_CMD"
    
    log_info "Helm chart deployed ✓"
}

verify_deployment() {
    local release_name=$1
    
    log_info "Verifying deployment..."
    
    # Wait for pods to be ready
    log_info "Waiting for pods to be ready (this may take several minutes)..."
    kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/instance="$release_name" \
        -n "$NAMESPACE" \
        --timeout=600s || true
    
    # Check HCD pods
    log_info "Checking HCD pods..."
    kubectl get pods -n "$NAMESPACE" -l cassandra.datastax.com/cluster=hcd-cluster-global
    
    # Check JanusGraph pods
    log_info "Checking JanusGraph pods..."
    kubectl get pods -n "$NAMESPACE" -l app=janusgraph
    
    # Check Mission Control pods
    log_info "Checking Mission Control pods..."
    kubectl get pods -n "$NAMESPACE" -l app=mission-control-server
    kubectl get pods -n "$NAMESPACE" -l app=mission-control-agent
    
    # Check PVCs
    log_info "Checking PersistentVolumeClaims..."
    kubectl get pvc -n "$NAMESPACE"
    
    log_info "Deployment verification complete ✓"
}

print_access_info() {
    local env=$1
    
    log_info "==================================="
    log_info "Deployment Complete!"
    log_info "==================================="
    echo
    log_info "Access Information:"
    echo
    log_info "Mission Control UI:"
    log_info "  kubectl port-forward svc/mission-control-server 8080:8080 -n $NAMESPACE"
    log_info "  Then open: http://localhost:8080"
    echo
    log_info "JanusGraph Gremlin Server:"
    log_info "  kubectl port-forward svc/janusgraph 8182:8182 -n $NAMESPACE"
    log_info "  Then test: curl http://localhost:8182?gremlin=g.V().count()"
    echo
    log_info "Check HCD cluster status:"
    log_info "  kubectl exec -it hcd-cluster-global-dc1-default-sts-0 -n $NAMESPACE -- nodetool status"
    echo
    
    if [[ "$env" != "prod" ]]; then
        log_info "Secrets file: ${PROJECT_ROOT}/.secrets-${env}.txt"
    fi
    
    log_info "==================================="
}

# Main execution
main() {
    local env=${1:-"dev"}
    local site=${2:-""}
    
    # Validate environment
    if [[ ! "$env" =~ ^(dev|staging|prod)$ ]]; then
        log_error "Invalid environment: $env"
        log_error "Usage: $0 [dev|staging|prod] [site-name]"
        exit 1
    fi
    
    # Validate site for production
    if [[ "$env" == "prod" ]] && [[ -z "$site" ]]; then
        log_error "Site name required for production deployment"
        log_error "Usage: $0 prod [paris|london|frankfurt]"
        exit 1
    fi
    
    log_info "Starting deployment for environment: $env"
    if [[ -n "$site" ]]; then
        log_info "Site: $site"
    fi
    echo
    
    # Execute deployment steps
    check_prerequisites
    add_helm_repos
    create_namespace
    create_secrets "$env"
    update_dependencies
    
    # Determine release name
    local release_name="janusgraph-banking"
    if [[ "$env" == "prod" ]] && [[ -n "$site" ]]; then
        release_name="janusgraph-banking-${site}"
    fi
    
    deploy_chart "$env" "$site"
    verify_deployment "$release_name"
    print_access_info "$env"
}

# Run main function
main "$@"

# Made with Bob
