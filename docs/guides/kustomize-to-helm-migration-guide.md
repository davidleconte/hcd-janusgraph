# Kustomize to Helm Migration Guide

**Date**: 2026-02-19  
**Version**: 1.0  
**Status**: Active  
**Audience**: DevOps Engineers, Platform Teams

---

## Executive Summary

This guide provides step-by-step instructions for migrating from the deprecated Kustomize deployment to the production-ready Helm chart for the JanusGraph Banking Platform.

**Why Migrate?**
- Kustomize deployment is incomplete (30/100) and deprecated
- Helm chart is production-ready (97/100) with full stack support
- Helm includes HCD, Mission Control, and all dependencies
- Helm is the official DataStax deployment pattern

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Pre-Migration Checklist](#2-pre-migration-checklist)
3. [Migration Steps](#3-migration-steps)
4. [Configuration Mapping](#4-configuration-mapping)
5. [Verification](#5-verification)
6. [Rollback Procedure](#6-rollback-procedure)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Prerequisites

### Required Tools

```bash
# Helm 3.8+
helm version

# kubectl or oc CLI
kubectl version

# Access to Kubernetes/OpenShift cluster
kubectl cluster-info
```

### Required Permissions

- Cluster admin or namespace admin
- Ability to create CRDs (for Cass Operator)
- Ability to create PersistentVolumes

---

## 2. Pre-Migration Checklist

### 2.1 Backup Current Deployment

```bash
# Export current Kustomize resources
kubectl get all -n janusgraph-banking -o yaml > backup-kustomize-$(date +%Y%m%d).yaml

# Backup ConfigMaps and Secrets
kubectl get configmaps,secrets -n janusgraph-banking -o yaml >> backup-kustomize-$(date +%Y%m%d).yaml

# Backup PVCs (if any)
kubectl get pvc -n janusgraph-banking -o yaml >> backup-kustomize-$(date +%Y%m%d).yaml
```

### 2.2 Document Current Configuration

```bash
# List current resources
kubectl get all -n janusgraph-banking

# Note current resource quotas
kubectl get resourcequota -n janusgraph-banking

# Note current limit ranges
kubectl get limitrange -n janusgraph-banking
```

### 2.3 Plan Downtime Window

**Estimated Downtime**: 15-30 minutes

**Recommended Window**: Off-peak hours

---

## 3. Migration Steps

### Step 1: Uninstall Kustomize Deployment

```bash
# Delete Kustomize resources
kubectl delete -k archive/kustomize-deprecated-2026-02-19/k8s/overlays/prod

# Or delete namespace (if dedicated)
kubectl delete namespace janusgraph-banking

# Verify deletion
kubectl get all -n janusgraph-banking
```

**⚠️ WARNING**: This will delete all running pods. Ensure backups are complete.

### Step 2: Preserve Data (if applicable)

If you have persistent data:

```bash
# List PVCs
kubectl get pvc -n janusgraph-banking

# Change reclaim policy to Retain (prevents deletion)
kubectl patch pv <pv-name> -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'
```

### Step 3: Add Helm Repositories

```bash
# Add required Helm repositories
helm repo add datastax https://datastax.github.io/charts
helm repo add opensearch https://opensearch-project.github.io/helm-charts
helm repo add pulsar https://pulsar.apache.org/charts
helm repo add hashicorp https://helm.releases.hashicorp.com

# Update repositories
helm repo update
```

### Step 4: Create Namespace (if deleted)

```bash
kubectl create namespace janusgraph-banking
```

### Step 5: Create Secrets

```bash
# Create Mission Control secrets
kubectl create secret generic mission-control-secrets \
  --from-literal=postgres-user=mcadmin \
  --from-literal=postgres-password=CHANGE_ME \
  --from-literal=admin-user=admin \
  --from-literal=admin-password=CHANGE_ME \
  --from-literal=agent-token=CHANGE_ME \
  -n janusgraph-banking

# Create JanusGraph secrets
kubectl create secret generic janusgraph-secrets \
  --from-literal=password=CHANGE_ME \
  -n janusgraph-banking

# Create OpenSearch secrets
kubectl create secret generic opensearch-secrets \
  --from-literal=password=CHANGE_ME \
  -n janusgraph-banking
```

### Step 6: Update Helm Dependencies

```bash
cd helm/janusgraph-banking

# Update dependencies
helm dependency update

# Verify dependencies downloaded
ls charts/
```

### Step 7: Install Helm Chart

**Development:**

```bash
helm install janusgraph-banking . \
  --namespace janusgraph-banking \
  --wait \
  --timeout 30m
```

**Production:**

```bash
helm install janusgraph-banking . \
  --namespace janusgraph-banking \
  --values values-prod.yaml \
  --wait \
  --timeout 30m
```

### Step 8: Verify Deployment

```bash
# Check Helm release
helm list -n janusgraph-banking

# Check pods
kubectl get pods -n janusgraph-banking

# Check services
kubectl get svc -n janusgraph-banking

# Check PVCs
kubectl get pvc -n janusgraph-banking
```

---

## 4. Configuration Mapping

### 4.1 Kustomize → Helm Value Mapping

| Kustomize Config | Helm Value | Notes |
|------------------|------------|-------|
| `base/namespace.yml` | `global.namespace` | Namespace name |
| `base/rbac.yml` (ResourceQuota) | Not needed | Helm creates automatically |
| `base/rbac.yml` (LimitRange) | Not needed | Helm creates automatically |
| `base/configmaps.yml` (janusgraph-config) | `janusgraph.storage.*` | Templated in Helm |
| `base/configmaps.yml` (banking-config) | `api.env.*` | Templated in Helm |
| `base/janusgraph-deployment.yml` (replicas) | `janusgraph.replicas` | Default: 3 |
| `base/janusgraph-deployment.yml` (resources) | `janusgraph.resources` | CPU/Memory limits |
| `base/api-deployment.yml` (replicas) | `api.replicas` | Default: 3 |
| `base/api-deployment.yml` (resources) | `api.resources` | CPU/Memory limits |
| `overlays/prod/kustomization.yml` (patches) | `values-prod.yaml` | Production overrides |

### 4.2 Example Value Mappings

**Kustomize ConfigMap:**
```yaml
# base/configmaps.yml
data:
  janusgraph-use-ssl: "false"
  cors-origins: "http://localhost:3000"
```

**Helm Values:**
```yaml
# values.yaml
api:
  env:
    useSSL: "false"
    corsOrigins: "http://localhost:3000"
```

**Kustomize Resource Patch:**
```yaml
# overlays/prod/kustomization.yml
patches:
  - target:
      kind: Deployment
      name: banking-api
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 3
```

**Helm Values:**
```yaml
# values-prod.yaml
api:
  replicas: 3
```

---

## 5. Verification

### 5.1 Health Checks

```bash
# Check HCD cluster status
kubectl get cassandradatacenters -n janusgraph-banking

# Check HCD pods
kubectl get pods -n janusgraph-banking -l cassandra.datastax.com/cluster=hcd-cluster-global

# Exec into HCD pod and check cluster
kubectl exec -it hcd-cluster-global-dc1-default-sts-0 -n janusgraph-banking -- nodetool status
```

### 5.2 JanusGraph Connectivity

```bash
# Port-forward JanusGraph
kubectl port-forward svc/janusgraph 8182:8182 -n janusgraph-banking

# Test query
curl http://localhost:8182?gremlin=g.V().count()
```

### 5.3 Mission Control Access

```bash
# Port-forward Mission Control
kubectl port-forward svc/mission-control-server 8080:8080 -n janusgraph-banking

# Open browser to http://localhost:8080
```

### 5.4 API Health

```bash
# Port-forward API
kubectl port-forward svc/banking-api 8001:8001 -n janusgraph-banking

# Test health endpoint
curl http://localhost:8001/health
```

---

## 6. Rollback Procedure

If migration fails, rollback to Kustomize:

```bash
# Uninstall Helm release
helm uninstall janusgraph-banking -n janusgraph-banking

# Restore Kustomize deployment
kubectl apply -k archive/kustomize-deprecated-2026-02-19/k8s/overlays/prod

# Verify rollback
kubectl get all -n janusgraph-banking
```

**⚠️ Note**: Rollback to Kustomize is NOT recommended as it's deprecated. Fix Helm issues instead.

---

## 7. Troubleshooting

### Issue 1: Helm Dependencies Not Downloaded

**Symptom**: `Error: found in Chart.yaml, but missing in charts/ directory`

**Solution**:
```bash
cd helm/janusgraph-banking
helm dependency update
```

### Issue 2: HCD Pods Not Starting

**Symptom**: `CassandraDatacenter` stuck in `Pending`

**Solution**:
```bash
# Check Cass Operator logs
kubectl logs -n janusgraph-banking -l name=cass-operator

# Check storage class
kubectl get storageclass

# Check PVC status
kubectl get pvc -n janusgraph-banking
```

### Issue 3: Mission Control Cannot Connect to HCD

**Symptom**: Mission Control shows no clusters

**Solution**:
```bash
# Check Mission Control agent logs
kubectl logs -n janusgraph-banking -l app=mission-control-agent

# Verify HCD service
kubectl get svc -n janusgraph-banking | grep hcd

# Check network policies
kubectl get networkpolicies -n janusgraph-banking
```

### Issue 4: Insufficient Resources

**Symptom**: Pods stuck in `Pending` with `Insufficient cpu/memory`

**Solution**:
```bash
# Check node resources
kubectl top nodes

# Reduce resource requests in values.yaml
helm upgrade janusgraph-banking . \
  --namespace janusgraph-banking \
  --set hcd.resources.requests.cpu=2000m \
  --set hcd.resources.requests.memory=8Gi
```

---

## 8. Post-Migration Tasks

### 8.1 Update CI/CD Pipelines

Update deployment scripts to use Helm:

```bash
# Old (Kustomize)
kubectl apply -k k8s/overlays/prod

# New (Helm)
helm upgrade --install janusgraph-banking helm/janusgraph-banking \
  --namespace janusgraph-banking \
  --values helm/janusgraph-banking/values-prod.yaml
```

### 8.2 Update Documentation

- Update deployment guides
- Update runbooks
- Update disaster recovery procedures

### 8.3 Train Team

- Helm basics
- Chart structure
- Values hierarchy
- Upgrade procedures

---

## 9. Benefits After Migration

### What You Gain

1. **Complete Stack** - HCD, Mission Control, OpenSearch, Pulsar, Vault
2. **Dependency Management** - Automatic subchart installation
3. **Multi-DC Support** - Easy 3-site deployment
4. **Production Values** - Pre-configured production settings
5. **Release Management** - Versioning, rollback, upgrade
6. **Better Documentation** - 441-line README with examples

### What You Lose

Nothing! Kustomize was incomplete and conflicted with Helm.

---

## 10. Support

### Resources

- [Helm Chart README](../../helm/janusgraph-banking/README.md)
- [K8s/OpenShift Audit Report](../implementation/audits/k8s-openshift-terraform-infrastructure-audit-2026-02-19.md)
- [DataStax HCD Documentation](https://docs.datastax.com/en/hyper-converged-database/1.2/)
- [Mission Control Documentation](https://docs.datastax.com/en/mission-control/)

### Contact

- Platform Engineering Team
- DevOps Team
- GitHub Issues: https://github.com/your-org/janusgraph-banking/issues

---

**Migration Complete!** 🎉

You are now using the production-ready Helm chart with full HCD and Mission Control support.

---

**Last Updated**: 2026-02-19  
**Version**: 1.0  
**Status**: Active