# Dry-Run Validation Guide

**Date:** 2026-02-19  
**Version:** 1.0  
**Status:** Active

## Overview

This guide documents all dry-run and validation capabilities for infrastructure-as-code in the HCD + JanusGraph Banking Platform. Dry-run validation allows you to test changes without applying them, ensuring safety and correctness before deployment.

## Table of Contents

1. [Terraform Dry-Run](#terraform-dry-run)
2. [Helm Dry-Run](#helm-dry-run)
3. [Kubernetes Dry-Run](#kubernetes-dry-run)
4. [OpenShift Dry-Run](#openshift-dry-run)
5. [ArgoCD Validation](#argocd-validation)
6. [Comprehensive Validation Script](#comprehensive-validation-script)
7. [CI/CD Integration](#cicd-integration)
8. [Best Practices](#best-practices)

---

## Terraform Dry-Run

### Commands

Terraform provides three levels of validation, all safe (no changes applied):

```bash
# 1. Initialize without backend (safe, no state access)
terraform init -backend=false

# 2. Validate syntax and configuration
terraform validate

# 3. Generate execution plan (shows what would change)
terraform plan -input=false
```

### Usage Examples

**Single Environment:**

```bash
cd terraform/environments/dev
terraform init -backend=false
terraform validate
terraform plan -input=false
```

**All Environments:**

```bash
for env in terraform/environments/*/; do
    echo "Validating: $env"
    cd "$env"
    terraform init -backend=false && \
    terraform validate && \
    terraform plan -input=false
    cd -
done
```

### What Gets Validated

- ✅ HCL syntax correctness
- ✅ Variable references and types
- ✅ Resource dependencies
- ✅ Provider configuration
- ✅ Module inputs/outputs
- ✅ Data source queries
- ✅ Conditional logic
- ✅ Resource count/for_each
- ❌ Does NOT validate: actual cloud resources, credentials, quotas

### Exit Codes

- `0` - Success (valid configuration)
- `1` - Error (invalid configuration)
- `2` - Partial success (warnings)

### Supported Environments

| Environment | Path | Cloud Provider |
|-------------|------|----------------|
| dev | `terraform/environments/dev/` | AWS |
| staging | `terraform/environments/staging/` | AWS |
| azure-dev | `terraform/environments/azure-dev/` | Azure |
| azure-staging | `terraform/environments/azure-staging/` | Azure |
| azure-prod | `terraform/environments/azure-prod/` | Azure |
| gcp-dev | `terraform/environments/gcp-dev/` | GCP |
| gcp-staging | `terraform/environments/gcp-staging/` | GCP |
| gcp-prod | `terraform/environments/gcp-prod/` | GCP |
| vsphere-staging | `terraform/environments/vsphere-staging/` | vSphere |
| vsphere-prod | `terraform/environments/vsphere-prod/` | vSphere |
| baremetal-staging | `terraform/environments/baremetal-staging/` | Bare Metal |
| baremetal-prod | `terraform/environments/baremetal-prod/` | Bare Metal |

---

## Helm Dry-Run

### Commands

Helm provides three validation methods:

```bash
# 1. Lint chart (syntax and best practices)
helm lint <chart-path>

# 2. Template rendering (generate manifests without installing)
helm template <release-name> <chart-path>

# 3. Install dry-run (full validation with cluster API)
helm install <release-name> <chart-path> --dry-run --debug
```

### Usage Examples

**Lint Chart:**

```bash
helm lint helm/janusgraph-banking/
```

**Template Rendering:**

```bash
# Basic template
helm template test-release helm/janusgraph-banking/

# With custom values
helm template test-release helm/janusgraph-banking/ \
    -f helm/janusgraph-banking/values-prod.yaml

# Output to file
helm template test-release helm/janusgraph-banking/ \
    > /tmp/rendered-manifests.yaml
```

**Install Dry-Run:**

```bash
# Requires cluster connection
helm install test-release helm/janusgraph-banking/ \
    --dry-run --debug \
    --namespace janusgraph-banking \
    --create-namespace
```

### What Gets Validated

**helm lint:**
- ✅ Chart.yaml syntax
- ✅ values.yaml syntax
- ✅ Template syntax
- ✅ Best practices (icon, keywords, etc.)
- ✅ Required fields
- ❌ Does NOT validate: dependencies, cluster resources

**helm template:**
- ✅ All of helm lint
- ✅ Template rendering
- ✅ Variable substitution
- ✅ Conditional logic
- ✅ Loops and ranges
- ❌ Does NOT validate: cluster API compatibility

**helm install --dry-run:**
- ✅ All of helm template
- ✅ Cluster API compatibility
- ✅ RBAC permissions
- ✅ Resource quotas
- ✅ Admission webhooks
- ❌ Does NOT validate: actual resource creation

### Common Issues

**Missing Dependencies:**

```bash
# Error: chart directory is missing these dependencies
# Solution: Build dependencies first
helm dependency build helm/janusgraph-banking/
```

**Missing Required Values:**

```bash
# Error: Missing required value: secrets.janusgraphPassword
# Solution: Provide values file or set values
helm template test-release helm/janusgraph-banking/ \
    --set secrets.janusgraphPassword=test123
```

---

## Kubernetes Dry-Run

### Commands

kubectl provides two dry-run modes:

```bash
# 1. Client-side validation (no cluster required)
kubectl apply -f <manifest> --dry-run=client

# 2. Server-side validation (requires cluster)
kubectl apply -f <manifest> --dry-run=server
```

### Usage Examples

**Single Manifest:**

```bash
# Client-side (no cluster needed)
kubectl apply -f k8s/base/namespace.yaml --dry-run=client

# Server-side (requires cluster)
kubectl apply -f k8s/base/namespace.yaml --dry-run=server
```

**Directory of Manifests:**

```bash
# Validate all manifests in directory
kubectl apply -f k8s/base/ --dry-run=client --recursive

# With output format
kubectl apply -f k8s/base/ --dry-run=client -o yaml
```

**ArgoCD Applications:**

```bash
# Validate ArgoCD Application manifest
kubectl apply -f argocd/applications/janusgraph-banking-dev.yaml \
    --dry-run=client
```

### What Gets Validated

**--dry-run=client:**
- ✅ YAML syntax
- ✅ API version compatibility
- ✅ Required fields
- ✅ Field types
- ✅ Basic validation rules
- ❌ Does NOT validate: cluster state, admission webhooks, quotas

**--dry-run=server:**
- ✅ All of client-side validation
- ✅ Admission webhooks
- ✅ Resource quotas
- ✅ RBAC permissions
- ✅ Custom resource definitions
- ✅ Mutating webhooks
- ❌ Does NOT validate: actual resource creation

### Differences from Helm

| Feature | kubectl | Helm |
|---------|---------|------|
| Template rendering | ❌ | ✅ |
| Variable substitution | ❌ | ✅ |
| Dependency management | ❌ | ✅ |
| Release tracking | ❌ | ✅ |
| Rollback capability | ❌ | ✅ |
| Direct manifest validation | ✅ | ❌ |

---

## OpenShift Dry-Run

### Commands

OpenShift CLI (`oc`) is compatible with kubectl and supports the same dry-run modes:

```bash
# Client-side validation
oc apply -f <manifest> --dry-run=client

# Server-side validation
oc apply -f <manifest> --dry-run=server
```

### Usage Examples

**OpenShift-Specific Resources:**

```bash
# Validate Route
oc apply -f k8s/base/route.yaml --dry-run=client

# Validate DeploymentConfig
oc apply -f k8s/base/deploymentconfig.yaml --dry-run=client

# Validate ImageStream
oc apply -f k8s/base/imagestream.yaml --dry-run=client
```

**Project/Namespace:**

```bash
# Validate project creation
oc new-project janusgraph-banking --dry-run=client

# Validate with specific context
oc apply -f k8s/base/ --dry-run=server \
    --context=openshift-prod
```

### OpenShift-Specific Validations

- ✅ Security Context Constraints (SCC)
- ✅ Route configuration
- ✅ ImageStream references
- ✅ BuildConfig syntax
- ✅ DeploymentConfig triggers
- ✅ Project quotas and limits

### Compatibility Notes

- All kubectl commands work with `oc`
- OpenShift adds additional resource types (Route, ImageStream, etc.)
- SCC validation only works with server-side dry-run
- Use `oc` for OpenShift-specific features, `kubectl` for standard K8s

---

## ArgoCD Validation

### Commands

ArgoCD applications can be validated using kubectl dry-run:

```bash
# Validate Application manifest
kubectl apply -f argocd/applications/janusgraph-banking-dev.yaml \
    --dry-run=client

# Validate with ArgoCD CLI (requires cluster)
argocd app create janusgraph-banking-dev \
    --file argocd/applications/janusgraph-banking-dev.yaml \
    --dry-run
```

### Usage Examples

**All Applications:**

```bash
for app in argocd/applications/*.yaml; do
    echo "Validating: $app"
    kubectl apply -f "$app" --dry-run=client
done
```

**With ArgoCD CLI:**

```bash
# Validate application
argocd app create test-app \
    --repo https://github.com/org/repo \
    --path helm/janusgraph-banking \
    --dest-server https://kubernetes.default.svc \
    --dest-namespace janusgraph-banking \
    --dry-run

# Diff against live state
argocd app diff janusgraph-banking-dev
```

### What Gets Validated

**kubectl dry-run:**
- ✅ Application manifest syntax
- ✅ Required fields (source, destination)
- ✅ API version compatibility
- ❌ Does NOT validate: Git repository access, Helm chart validity

**argocd CLI:**
- ✅ All of kubectl validation
- ✅ Git repository access
- ✅ Helm chart validity
- ✅ Kustomize build
- ✅ Application health
- ✅ Sync status

### Supported Applications

| Application | Path | Environment |
|-------------|------|-------------|
| janusgraph-banking-dev | `argocd/applications/janusgraph-banking-dev.yaml` | Development |
| janusgraph-banking-staging | `argocd/applications/janusgraph-banking-staging.yaml` | Staging |
| janusgraph-banking-prod | `argocd/applications/janusgraph-banking-prod.yaml` | Production |

---

## Comprehensive Validation Script

### Overview

The `scripts/validation/dry_run_all_infrastructure.sh` script validates ALL infrastructure without making changes.

### Usage

```bash
# Run all validations
bash scripts/validation/dry_run_all_infrastructure.sh

# Run specific validation type
bash scripts/validation/dry_run_all_infrastructure.sh --terraform-only
bash scripts/validation/dry_run_all_infrastructure.sh --helm-only
bash scripts/validation/dry_run_all_infrastructure.sh --k8s-only
bash scripts/validation/dry_run_all_infrastructure.sh --argocd-only

# Skip specific validation type
bash scripts/validation/dry_run_all_infrastructure.sh --skip-terraform
bash scripts/validation/dry_run_all_infrastructure.sh --skip-helm

# Verbose output
bash scripts/validation/dry_run_all_infrastructure.sh --verbose
```

### What Gets Validated

1. **Terraform (12 environments)**
   - AWS: dev, staging
   - Azure: dev, staging, prod
   - GCP: dev, staging, prod
   - vSphere: staging, prod
   - Bare Metal: staging, prod

2. **Helm Charts**
   - janusgraph-banking chart
   - All templates
   - Values files (default, prod)

3. **Kubernetes Manifests**
   - Base manifests (k8s/base/)
   - Namespace, NetworkPolicy, etc.

4. **ArgoCD Applications**
   - Development application
   - Staging application
   - Production application

### Output Format

```
===========================================
Infrastructure Dry-Run Validation
===========================================

[1/4] Validating Terraform Environments...
  ✓ dev: PASSED
  ✓ staging: PASSED
  ✓ azure-dev: PASSED
  ...

[2/4] Validating Helm Charts...
  ✓ janusgraph-banking: PASSED

[3/4] Validating Kubernetes Manifests...
  ✓ k8s/base: PASSED

[4/4] Validating ArgoCD Applications...
  ✓ janusgraph-banking-dev: PASSED
  ✓ janusgraph-banking-staging: PASSED
  ✓ janusgraph-banking-prod: PASSED

===========================================
Summary
===========================================
Total Tests: 16
Passed: 16
Failed: 0
Skipped: 0
Success Rate: 100%
```

### Exit Codes

- `0` - All validations passed
- `1` - One or more validations failed
- `2` - Script error (missing dependencies, etc.)

---

## CI/CD Integration

### GitHub Actions

Add dry-run validation to CI/CD pipeline:

```yaml
name: Infrastructure Validation

on:
  pull_request:
    paths:
      - 'terraform/**'
      - 'helm/**'
      - 'k8s/**'
      - 'argocd/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.7.0
      
      - name: Setup Helm
        uses: azure/setup-helm@v3
        with:
          version: 3.14.0
      
      - name: Setup kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 1.29.0
      
      - name: Run Dry-Run Validation
        run: bash scripts/validation/dry_run_all_infrastructure.sh
      
      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: validation-results
          path: /tmp/dry-run-results.txt
```

### Pre-Commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: terraform-validate
        name: Terraform Validate
        entry: bash -c 'cd terraform/environments/dev && terraform init -backend=false && terraform validate'
        language: system
        pass_filenames: false
        files: \.tf$
      
      - id: helm-lint
        name: Helm Lint
        entry: helm lint helm/janusgraph-banking/
        language: system
        pass_filenames: false
        files: ^helm/
      
      - id: kubectl-dry-run
        name: Kubectl Dry-Run
        entry: bash -c 'kubectl apply -f k8s/base/ --dry-run=client --recursive'
        language: system
        pass_filenames: false
        files: ^k8s/
```

### Makefile Targets

Add to `Makefile`:

```makefile
.PHONY: validate-terraform validate-helm validate-k8s validate-all

validate-terraform:
	@echo "Validating Terraform..."
	@for env in terraform/environments/*/; do \
		echo "Validating: $$env"; \
		cd "$$env" && terraform init -backend=false && terraform validate && cd -; \
	done

validate-helm:
	@echo "Validating Helm charts..."
	@helm lint helm/janusgraph-banking/

validate-k8s:
	@echo "Validating Kubernetes manifests..."
	@kubectl apply -f k8s/base/ --dry-run=client --recursive

validate-all:
	@bash scripts/validation/dry_run_all_infrastructure.sh
```

---

## Best Practices

### 1. Always Validate Before Apply

```bash
# ❌ WRONG - Apply without validation
terraform apply -auto-approve

# ✅ CORRECT - Validate first
terraform validate && terraform plan && terraform apply
```

### 2. Use Client-Side Dry-Run When Possible

```bash
# ✅ PREFERRED - No cluster required
kubectl apply -f manifest.yaml --dry-run=client

# ⚠️ USE WHEN NEEDED - Requires cluster
kubectl apply -f manifest.yaml --dry-run=server
```

### 3. Validate in CI/CD Pipeline

- Run dry-run validation on every PR
- Block merge if validation fails
- Upload validation results as artifacts
- Notify team of validation failures

### 4. Test with Multiple Values Files

```bash
# Test with default values
helm template test helm/janusgraph-banking/

# Test with production values
helm template test helm/janusgraph-banking/ \
    -f helm/janusgraph-banking/values-prod.yaml

# Test with custom overrides
helm template test helm/janusgraph-banking/ \
    --set replicaCount=5 \
    --set resources.requests.memory=4Gi
```

### 5. Validate Dependencies

```bash
# Helm dependencies
helm dependency build helm/janusgraph-banking/
helm dependency update helm/janusgraph-banking/

# Terraform modules
terraform get -update
```

### 6. Use Verbose Output for Debugging

```bash
# Terraform
terraform plan -input=false -no-color > plan.txt

# Helm
helm install test helm/janusgraph-banking/ \
    --dry-run --debug > debug.txt 2>&1

# kubectl
kubectl apply -f manifest.yaml --dry-run=client -v=8
```

### 7. Validate Across Environments

```bash
# Test same chart with different values
for env in dev staging prod; do
    echo "Testing: $env"
    helm template test helm/janusgraph-banking/ \
        -f helm/janusgraph-banking/values-${env}.yaml
done
```

### 8. Document Validation Requirements

- List required tools and versions
- Document validation commands
- Provide troubleshooting guide
- Include example outputs

### 9. Automate Validation

- Add pre-commit hooks
- Run in CI/CD pipeline
- Schedule periodic validation
- Alert on validation failures

### 10. Keep Validation Fast

- Use client-side validation when possible
- Cache Terraform providers
- Parallelize validation when safe
- Skip unnecessary validations

---

## Troubleshooting

### Terraform Issues

**Issue: Provider download fails**

```bash
# Solution: Use local mirror
terraform providers mirror /tmp/terraform-providers
terraform init -plugin-dir=/tmp/terraform-providers
```

**Issue: Backend configuration error**

```bash
# Solution: Skip backend initialization
terraform init -backend=false
```

### Helm Issues

**Issue: Missing dependencies**

```bash
# Solution: Build dependencies
helm dependency build helm/janusgraph-banking/
```

**Issue: Template rendering fails**

```bash
# Solution: Check values and debug
helm template test helm/janusgraph-banking/ --debug
```

### Kubernetes Issues

**Issue: Cluster connection refused**

```bash
# Solution: Use client-side validation
kubectl apply -f manifest.yaml --dry-run=client
```

**Issue: API version not found**

```bash
# Solution: Check API versions
kubectl api-versions
kubectl api-resources
```

### OpenShift Issues

**Issue: SCC validation fails**

```bash
# Solution: Use server-side validation with proper context
oc apply -f manifest.yaml --dry-run=server \
    --context=openshift-prod
```

---

## Related Documentation

- [Terraform Multi-Cloud Architecture](../architecture/terraform-multi-cloud-architecture.md)
- [Kubernetes & Helm Architecture](../architecture/kubernetes-helm-architecture.md)
- [Deployment Guide](deployment-guide.md)
- [Operations Runbook](operations-runbook.md)

---

**Last Updated:** 2026-02-19  
**Version:** 1.0  
**Maintainer:** Platform Engineering Team