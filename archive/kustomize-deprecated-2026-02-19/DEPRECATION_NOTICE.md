# Kustomize Deployment - DEPRECATED

**Date**: 2026-02-19  
**Status**: DEPRECATED - Do Not Use  
**Replacement**: Helm Chart (`helm/janusgraph-banking/`)  
**Reason**: Incomplete implementation, conflicts with Helm, redundant maintenance

---

## ⚠️ DEPRECATION NOTICE

The Kustomize-based deployment in this directory has been **DEPRECATED** as of 2026-02-19 and should **NOT** be used for any deployments.

### Why Deprecated?

1. **Incomplete Implementation** (30/100 score)
   - Missing HCD (Hyper-Converged Database) deployment
   - Missing Mission Control for HCD management
   - Missing OpenSearch, Pulsar, Vault
   - No storage classes defined
   - No multi-DC support

2. **Conflicts with Helm**
   - Uses `Deployment` for JanusGraph (wrong)
   - Helm correctly uses `StatefulSet` (correct)
   - Cannot use both simultaneously

3. **Helm is Production-Ready** (97/100 score)
   - Complete stack deployment
   - All dependencies included
   - Multi-DC support
   - Production values
   - Comprehensive documentation

4. **Maintenance Burden**
   - Maintaining two deployment methods is inefficient
   - Helm is industry standard for complex applications
   - DataStax official pattern uses Helm/Operator

### Migration Path

**Use Helm Chart Instead:**

```bash
# Install with Helm (RECOMMENDED)
cd helm/janusgraph-banking

# Development
helm install janusgraph-banking . \
  --namespace janusgraph-banking \
  --create-namespace

# Production (3-site)
helm install janusgraph-banking-paris . \
  --namespace janusgraph-banking \
  --values values-prod.yaml \
  --set hcd.datacenterName=paris-dc
```

### Migration Guide

See: [`docs/guides/kustomize-to-helm-migration-guide.md`](../../docs/guides/kustomize-to-helm-migration-guide.md)

### What Was in This Directory

**Archived Contents:**
- `k8s/base/` - Base Kustomize manifests (incomplete)
- `k8s/overlays/` - Environment overlays (dev, prod)
- `k8s/backup/` - Backup CronJob (moved to Helm)

**Key Files:**
- `base/kustomization.yml` - Base configuration
- `base/namespace.yml` - Namespace definition
- `base/rbac.yml` - RBAC and resource quotas
- `base/configmaps.yml` - ConfigMaps
- `base/janusgraph-deployment.yml` - JanusGraph Deployment (WRONG: should be StatefulSet)
- `base/api-deployment.yml` - API Deployment
- `overlays/prod/kustomization.yml` - Production overrides

### Audit Report

For complete analysis, see:
- [K8s/OpenShift/Terraform Infrastructure Audit](../../docs/implementation/audits/k8s-openshift-terraform-infrastructure-audit-2026-02-19.md)

### Questions?

Contact: Platform Engineering Team

---

**DO NOT USE THIS DIRECTORY FOR DEPLOYMENTS**

**Use Helm Chart:** `helm/janusgraph-banking/`

---

**Archived**: 2026-02-19  
**Reason**: Deprecated in favor of Helm  
**Replacement**: `helm/janusgraph-banking/`