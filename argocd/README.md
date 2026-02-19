# ArgoCD GitOps Configuration

**Version**: 1.0  
**Date**: 2026-02-19  
**Status**: Active

---

## Overview

This directory contains ArgoCD Application manifests for GitOps-based deployment of the JanusGraph Banking Platform.

### Architecture

```
argocd/
├── applications/              # ArgoCD Application CRDs
│   ├── janusgraph-banking-dev.yaml      # Development environment
│   ├── janusgraph-banking-staging.yaml  # Staging environment (to be created)
│   └── janusgraph-banking-prod.yaml     # Production environment
└── README.md                  # This file
```

---

## Prerequisites

### 1. Install ArgoCD

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods to be ready
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s
```

### 2. Access ArgoCD UI

```bash
# Port-forward ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Open browser to https://localhost:8080
# Username: admin
# Password: (from above command)
```

### 3. Install ArgoCD CLI (Optional)

```bash
# macOS
brew install argocd

# Linux
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd

# Verify
argocd version
```

---

## Deployment

### Development Environment

```bash
# Apply ArgoCD Application
kubectl apply -f applications/janusgraph-banking-dev.yaml

# Check application status
kubectl get application -n argocd janusgraph-banking-dev

# Watch sync progress
kubectl get application -n argocd janusgraph-banking-dev -w
```

**Features**:
- Automated sync enabled
- Self-healing enabled
- Prune enabled
- 2 API replicas
- 3 HCD nodes

### Production Environment

```bash
# Apply ArgoCD Application
kubectl apply -f applications/janusgraph-banking-prod.yaml

# Check application status
kubectl get application -n argocd janusgraph-banking-prod

# Manual sync (production requires manual approval)
argocd app sync janusgraph-banking-prod
```

**Features**:
- Manual sync (for safety)
- 3 API replicas (HPA: 3-20)
- 3 HCD nodes per DC
- Mission Control enabled
- Tagged releases only

---

## ArgoCD CLI Usage

### Login

```bash
# Login to ArgoCD
argocd login localhost:8080 --username admin --password <password>
```

### Application Management

```bash
# List applications
argocd app list

# Get application details
argocd app get janusgraph-banking-dev

# Sync application
argocd app sync janusgraph-banking-dev

# Refresh application (check for changes)
argocd app refresh janusgraph-banking-dev

# Rollback to previous version
argocd app rollback janusgraph-banking-dev

# Delete application
argocd app delete janusgraph-banking-dev
```

### Monitoring

```bash
# Watch application sync
argocd app wait janusgraph-banking-dev --health

# Get sync status
argocd app get janusgraph-banking-dev --refresh

# View application logs
argocd app logs janusgraph-banking-dev
```

---

## Configuration

### Application Spec

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: janusgraph-banking-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/hcd-tarball-janusgraph.git
    targetRevision: main
    path: helm/janusgraph-banking
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: janusgraph-banking-dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Sync Policies

**Automated Sync** (Dev/Staging):
- Automatically syncs when Git changes detected
- Self-heals when manual changes made
- Prunes resources removed from Git

**Manual Sync** (Production):
- Requires manual approval for sync
- Safer for production environments
- Allows review before deployment

---

## Multi-Environment Strategy

### Development
- **Branch**: `main`
- **Sync**: Automated
- **Purpose**: Continuous deployment for testing

### Staging
- **Branch**: `release/*`
- **Sync**: Automated
- **Purpose**: Pre-production validation

### Production
- **Branch**: Tagged releases (`v1.2.0`)
- **Sync**: Manual
- **Purpose**: Stable production deployments

---

## Troubleshooting

### Application Out of Sync

**Symptom**: Application shows "OutOfSync" status

**Solution**:
```bash
# Check diff
argocd app diff janusgraph-banking-dev

# Sync application
argocd app sync janusgraph-banking-dev
```

### Sync Failed

**Symptom**: Sync operation fails

**Solution**:
```bash
# View sync errors
argocd app get janusgraph-banking-dev

# Check application logs
kubectl logs -n argocd deployment/argocd-application-controller

# Force sync
argocd app sync janusgraph-banking-dev --force
```

### Health Check Failed

**Symptom**: Application shows "Degraded" health

**Solution**:
```bash
# Check resource health
argocd app get janusgraph-banking-dev --show-operation

# Check pod status
kubectl get pods -n janusgraph-banking-dev

# View pod logs
kubectl logs -n janusgraph-banking-dev <pod-name>
```

---

## Best Practices

### 1. Use Projects

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: janusgraph-banking
  namespace: argocd
spec:
  description: JanusGraph Banking Platform
  sourceRepos:
    - https://github.com/your-org/hcd-tarball-janusgraph.git
  destinations:
    - namespace: janusgraph-banking-*
      server: https://kubernetes.default.svc
```

### 2. Use Sync Waves

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"  # Deploy in order
```

### 3. Use Health Checks

```yaml
spec:
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas  # Ignore HPA-managed replicas
```

### 4. Use Notifications

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: $slack-token
```

---

## Integration with Tekton

The Tekton CD pipeline includes an ArgoCD sync task:

```yaml
# tekton/tasks/argocd-sync.yaml
- name: argocd-sync
  taskRef:
    name: argocd-sync
  params:
    - name: application-name
      value: janusgraph-banking-dev
```

---

## Security

### RBAC

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.csv: |
    p, role:developer, applications, get, */*, allow
    p, role:developer, applications, sync, */dev/*, allow
    p, role:operator, applications, *, */*, allow
```

### SSO Integration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  url: https://argocd.example.com
  dex.config: |
    connectors:
      - type: oidc
        id: okta
        name: Okta
```

---

## Monitoring

### Prometheus Metrics

ArgoCD exposes metrics at:
- `http://argocd-metrics:8082/metrics`
- `http://argocd-server-metrics:8083/metrics`

### Grafana Dashboards

Import ArgoCD dashboards:
- Dashboard ID: 14584 (ArgoCD Overview)
- Dashboard ID: 14585 (ArgoCD Application)

---

## Support

### Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
- [Helm Chart](../../helm/janusgraph-banking/README.md)

### Contact

- Platform Engineering Team
- DevOps Team
- GitHub Issues

---

**Last Updated**: 2026-02-19  
**Version**: 1.0  
**Status**: Active