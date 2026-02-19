# Kubernetes/OpenShift Deployment Guide

**Version**: 1.0  
**Date**: 2026-02-19  
**Status**: Production Ready

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation Methods](#installation-methods)
4. [Deployment Procedures](#deployment-procedures)
5. [Configuration](#configuration)
6. [Verification](#verification)
7. [Operations](#operations)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

This guide provides step-by-step instructions for deploying the JanusGraph Banking Platform on Kubernetes or OpenShift with IBM DataStax HCD and Mission Control.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Ingress / Route                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    JanusGraph StatefulSet                    │
│                    (3-5 replicas)                            │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
│  HCD Cluster     │ │ OpenSearch   │ │ Pulsar       │
│  (3-5 nodes)     │ │ (3 nodes)    │ │ (3 brokers)  │
└──────────────────┘ └──────────────┘ └──────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Mission Control                           │
│  Server (2) + Agent (DaemonSet) + PostgreSQL + Redis        │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Options

| Method | Use Case | Complexity | Time |
|--------|----------|------------|------|
| **Helm** | Quick deployment, standard config | Low | 15 min |
| **Kustomize** | Custom overlays, GitOps | Medium | 30 min |
| **ArgoCD** | GitOps, automated sync | Medium | 20 min |
| **Tekton** | Full CI/CD pipeline | High | 45 min |

---

## Prerequisites

### Required Tools

```bash
# Kubernetes CLI
kubectl version --client
# Required: v1.24+

# Helm
helm version
# Required: v3.8+

# ArgoCD CLI (optional)
argocd version --client
# Required: v2.9+

# Tekton CLI (optional)
tkn version
# Required: v0.32+
```

### Cluster Requirements

**Minimum Resources** (Development):
- **Nodes**: 3 worker nodes
- **CPU**: 12 cores total (4 per node)
- **Memory**: 48 GB total (16 GB per node)
- **Storage**: 300 GB total

**Recommended Resources** (Production):
- **Nodes**: 9 worker nodes (3 per site for multi-DC)
- **CPU**: 72 cores total (8 per node)
- **Memory**: 288 GB total (32 GB per node)
- **Storage**: 3 TB total (1 TB per site)

### Storage Classes

```bash
# Check available storage classes
kubectl get storageclasses

# Required storage classes (or create them):
# - hcd-storage (for HCD data)
# - janusgraph-storage (for JanusGraph data)
# - opensearch-storage (for OpenSearch data)
# - pulsar-storage (for Pulsar data)
# - mission-control-storage (for Mission Control PostgreSQL)
```

### Network Requirements

**Required Ports**:
- **8182**: JanusGraph Gremlin Server
- **9042**: HCD CQL (Cassandra Query Language)
- **8080**: Mission Control UI
- **9200**: OpenSearch REST API
- **6650**: Pulsar broker
- **8200**: Vault (if using)

**Network Policies**: Ensure cluster supports NetworkPolicies

---

## Installation Methods

### Method 1: Helm (Recommended)

**Quick Start**:

```bash
# 1. Add Helm repository (if using remote chart)
helm repo add janusgraph-banking https://your-org.github.io/charts
helm repo update

# 2. Create namespace
kubectl create namespace janusgraph-banking-dev

# 3. Install with default values
helm install janusgraph-banking janusgraph-banking/janusgraph-banking \
  -n janusgraph-banking-dev

# 4. Wait for deployment
kubectl wait --for=condition=Ready pods --all \
  -n janusgraph-banking-dev \
  --timeout=600s
```

**Custom Configuration**:

```bash
# 1. Create custom values file
cat > my-values.yaml <<EOF
global:
  environment: dev

janusgraph:
  replicas: 3
  resources:
    requests:
      cpu: "2"
      memory: "8Gi"

hcd:
  size: 3
  resources:
    requests:
      cpu: "4"
      memory: "16Gi"
EOF

# 2. Install with custom values
helm install janusgraph-banking ./helm/janusgraph-banking \
  -f my-values.yaml \
  -n janusgraph-banking-dev

# 3. Verify installation
helm status janusgraph-banking -n janusgraph-banking-dev
```

**Upgrade Deployment**:

```bash
# 1. Update values or chart
helm upgrade janusgraph-banking ./helm/janusgraph-banking \
  -f my-values.yaml \
  -n janusgraph-banking-dev

# 2. Rollback if needed
helm rollback janusgraph-banking -n janusgraph-banking-dev
```

### Method 2: Automated Script

**Using Deployment Script**:

```bash
# 1. Navigate to scripts directory
cd scripts/k8s

# 2. Run deployment script
./deploy-helm-chart.sh dev

# 3. Follow prompts and wait for completion
```

**Script Features**:
- Prerequisites validation
- Secret generation
- Automated deployment
- Health checks
- Rollback on failure

### Method 3: ArgoCD (GitOps)

**Setup ArgoCD**:

```bash
# 1. Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f \
  https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 2. Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s \
  deployment/argocd-server -n argocd

# 3. Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# 4. Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

**Deploy Application**:

```bash
# 1. Apply ArgoCD Application
kubectl apply -f argocd/application.yaml

# 2. Sync application
argocd app sync janusgraph-banking-dev

# 3. Monitor deployment
argocd app get janusgraph-banking-dev --watch
```

### Method 4: Tekton (CI/CD)

**Setup Tekton**:

```bash
# 1. Install Tekton Pipelines
kubectl apply -f \
  https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml

# 2. Install Tekton Triggers
kubectl apply -f \
  https://storage.googleapis.com/tekton-releases/triggers/latest/release.yaml

# 3. Install Tekton Dashboard (optional)
kubectl apply -f \
  https://storage.googleapis.com/tekton-releases/dashboard/latest/release.yaml
```

**Run Pipeline**:

```bash
# 1. Apply pipeline and tasks
kubectl apply -f tekton/pipelines/cd-pipeline.yaml
kubectl apply -f tekton/tasks/

# 2. Create PipelineRun
tkn pipeline start janusgraph-banking-cd \
  --param git-url=https://github.com/your-org/hcd-tarball-janusgraph.git \
  --param git-revision=main \
  --param target-environment=dev \
  --workspace name=source,claimName=pipeline-workspace \
  --workspace name=kubeconfig,secret=kubeconfig-secret \
  --showlog
```

---

## Deployment Procedures

### Development Environment

**1. Create Namespace**:

```bash
kubectl create namespace janusgraph-banking-dev
kubectl label namespace janusgraph-banking-dev environment=dev
```

**2. Create Secrets**:

```bash
# Mission Control credentials
kubectl create secret generic mission-control-secrets \
  -n janusgraph-banking-dev \
  --from-literal=admin-password=$(openssl rand -base64 32) \
  --from-literal=postgres-password=$(openssl rand -base64 32) \
  --from-literal=redis-password=$(openssl rand -base64 32)

# S3 backup credentials (if using)
kubectl create secret generic s3-backup-credentials \
  -n janusgraph-banking-dev \
  --from-literal=access-key-id=YOUR_ACCESS_KEY \
  --from-literal=secret-access-key=YOUR_SECRET_KEY
```

**3. Deploy with Helm**:

```bash
helm install janusgraph-banking ./helm/janusgraph-banking \
  --set global.environment=dev \
  --set janusgraph.replicas=2 \
  --set hcd.size=3 \
  -n janusgraph-banking-dev
```

**4. Verify Deployment**:

```bash
# Run validation script
./scripts/k8s/validate-deployment.sh janusgraph-banking-dev
```

### Staging Environment

**1. Create Namespace**:

```bash
kubectl create namespace janusgraph-banking-staging
kubectl label namespace janusgraph-banking-staging environment=staging
```

**2. Deploy with Custom Values**:

```bash
helm install janusgraph-banking ./helm/janusgraph-banking \
  -f helm/janusgraph-banking/values-staging.yaml \
  -n janusgraph-banking-staging
```

**3. Run Integration Tests**:

```bash
# Wait for deployment to be ready
kubectl wait --for=condition=Ready pods --all \
  -n janusgraph-banking-staging \
  --timeout=600s

# Run tests
kubectl exec -it janusgraph-0 -n janusgraph-banking-staging \
  -- /tests/run-integration-tests.sh
```

### Production Environment

**1. Review Configuration**:

```bash
# Review production values
cat helm/janusgraph-banking/values-prod.yaml

# Review multi-DC configuration
cat helm/janusgraph-banking/examples/multi-dc-3-site.yaml
```

**2. Create Namespace**:

```bash
kubectl create namespace janusgraph-banking-prod
kubectl label namespace janusgraph-banking-prod \
  environment=prod \
  criticality=high
```

**3. Deploy with GitOps (Recommended)**:

```bash
# Apply ArgoCD Application
kubectl apply -f argocd/application-prod.yaml

# Manual sync (production requires approval)
argocd app sync janusgraph-banking-prod
```

**4. Verify Production Deployment**:

```bash
# Run comprehensive validation
./scripts/k8s/validate-deployment.sh janusgraph-banking-prod

# Check HCD cluster status
kubectl exec -it hcd-paris-rack1-sts-0 \
  -n janusgraph-banking-prod \
  -- nodetool status

# Test JanusGraph connectivity
kubectl exec -it janusgraph-0 -n janusgraph-banking-prod \
  -- curl http://localhost:8182?gremlin=g.V().count()
```

---

## Configuration

### Environment-Specific Values

**Development** (`values-dev.yaml`):
```yaml
global:
  environment: dev

janusgraph:
  replicas: 2
  resources:
    requests:
      cpu: "1"
      memory: "4Gi"

hcd:
  size: 3
  resources:
    requests:
      cpu: "2"
      memory: "8Gi"
```

**Staging** (`values-staging.yaml`):
```yaml
global:
  environment: staging

janusgraph:
  replicas: 3
  resources:
    requests:
      cpu: "2"
      memory: "8Gi"

hcd:
  size: 3
  resources:
    requests:
      cpu: "4"
      memory: "16Gi"
```

**Production** (`values-prod.yaml`):
```yaml
global:
  environment: production

janusgraph:
  replicas: 5
  resources:
    requests:
      cpu: "4"
      memory: "16Gi"

hcd:
  size: 5
  resources:
    requests:
      cpu: "8"
      memory: "32Gi"

  multiDC:
    enabled: true
```

### Resource Limits

**Best Practices**:
- Set `requests` to expected usage
- Set `limits` to 2x `requests` for burstable workloads
- Use `LimitRange` to enforce defaults

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: resource-limits
  namespace: janusgraph-banking-prod
spec:
  limits:
    - max:
        cpu: "16"
        memory: "64Gi"
      min:
        cpu: "500m"
        memory: "1Gi"
      type: Container
```

### Storage Configuration

**StorageClass Example** (AWS EBS):
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: hcd-storage
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

---

## Verification

### Health Checks

**1. Pod Status**:
```bash
# Check all pods
kubectl get pods -n janusgraph-banking-prod

# Check specific component
kubectl get pods -l app=janusgraph -n janusgraph-banking-prod
```

**2. StatefulSet Status**:
```bash
# Check StatefulSets
kubectl get statefulsets -n janusgraph-banking-prod

# Check specific StatefulSet
kubectl describe statefulset janusgraph -n janusgraph-banking-prod
```

**3. Service Status**:
```bash
# Check services
kubectl get services -n janusgraph-banking-prod

# Test service connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never \
  -- curl http://janusgraph:8182?gremlin=g.V().count()
```

### Component-Specific Checks

**HCD Cluster**:
```bash
# Check CassandraDatacenter
kubectl get cassandradatacenters -n janusgraph-banking-prod

# Check cluster status
kubectl exec -it hcd-paris-rack1-sts-0 -n janusgraph-banking-prod \
  -- nodetool status

# Check keyspaces
kubectl exec -it hcd-paris-rack1-sts-0 -n janusgraph-banking-prod \
  -- cqlsh -e "DESCRIBE KEYSPACES"
```

**JanusGraph**:
```bash
# Test Gremlin server
kubectl port-forward svc/janusgraph 8182:8182 -n janusgraph-banking-prod

# In another terminal
curl http://localhost:8182?gremlin=g.V().count()
```

**Mission Control**:
```bash
# Check Mission Control pods
kubectl get pods -l app=mission-control-server -n janusgraph-banking-prod

# Access UI
kubectl port-forward svc/mission-control-server 8080:8080 \
  -n janusgraph-banking-prod

# Open http://localhost:8080
```

### Automated Validation

```bash
# Run validation script
./scripts/k8s/validate-deployment.sh janusgraph-banking-prod

# Expected output:
# ✓ Namespace exists
# ✓ HCD cluster running
# ✓ JanusGraph StatefulSet ready
# ✓ Mission Control running
# ✓ All PVCs bound
# ✓ All services available
```

---

## Operations

### Scaling

**Scale JanusGraph**:
```bash
./scripts/k8s/scale-cluster.sh janusgraph 5 janusgraph-banking-prod
```

**Scale HCD**:
```bash
./scripts/k8s/scale-cluster.sh hcd 7 janusgraph-banking-prod
```

**Scale OpenSearch**:
```bash
./scripts/k8s/scale-cluster.sh opensearch 5 janusgraph-banking-prod
```

### Backup

**Manual Backup**:
```bash
kubectl create job --from=cronjob/hcd-backup \
  hcd-backup-manual-$(date +%Y%m%d-%H%M%S) \
  -n janusgraph-banking-prod
```

**List Backups**:
```bash
aws s3 ls s3://janusgraph-banking-backups-prod/
```

### Restore

**Restore from Backup**:
```bash
# 1. Edit restore job with backup name
sed -i 's/REPLACE_WITH_BACKUP_NAME/backup-20260219-020000/g' \
  k8s/backup/restore-job.yaml

# 2. Stop cluster
kubectl scale cassandradatacenter hcd-paris --replicas=0 \
  -n janusgraph-banking-prod

# 3. Run restore
kubectl apply -f k8s/backup/restore-job.yaml

# 4. Start cluster
kubectl scale cassandradatacenter hcd-paris --replicas=5 \
  -n janusgraph-banking-prod
```

### Rollback

**Rollback Deployment**:
```bash
# Rollback to previous version
./scripts/k8s/rollback-deployment.sh prod

# Rollback to specific version
./scripts/k8s/rollback-deployment.sh prod v1.2.0
```

### Monitoring

**Access Prometheus**:
```bash
kubectl port-forward svc/prometheus-server 9090:9090 -n monitoring
# Open http://localhost:9090
```

**Access Grafana**:
```bash
kubectl port-forward svc/grafana 3000:3000 -n monitoring
# Open http://localhost:3000
# Default: admin/admin
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Pods Not Starting

**Symptoms**:
```bash
kubectl get pods -n janusgraph-banking-prod
# NAME                          READY   STATUS    RESTARTS   AGE
# janusgraph-0                  0/1     Pending   0          5m
```

**Diagnosis**:
```bash
kubectl describe pod janusgraph-0 -n janusgraph-banking-prod
# Look for events section
```

**Common Causes**:
1. **Insufficient resources**: Check node capacity
2. **PVC not bound**: Check storage class
3. **Image pull errors**: Check image name and registry access

**Solutions**:
```bash
# Check node resources
kubectl top nodes

# Check PVC status
kubectl get pvc -n janusgraph-banking-prod

# Check events
kubectl get events -n janusgraph-banking-prod --sort-by='.lastTimestamp'
```

#### Issue 2: HCD Cluster Not Forming

**Symptoms**:
```bash
kubectl exec -it hcd-paris-rack1-sts-0 -n janusgraph-banking-prod \
  -- nodetool status
# Shows nodes as DN (Down/Normal)
```

**Diagnosis**:
```bash
# Check HCD logs
kubectl logs hcd-paris-rack1-sts-0 -n janusgraph-banking-prod

# Check network connectivity
kubectl exec -it hcd-paris-rack1-sts-0 -n janusgraph-banking-prod \
  -- ping hcd-paris-rack2-sts-0.hcd-paris-service
```

**Solutions**:
```bash
# Restart pods one by one
kubectl delete pod hcd-paris-rack1-sts-0 -n janusgraph-banking-prod
kubectl wait --for=condition=Ready pod/hcd-paris-rack1-sts-0 \
  -n janusgraph-banking-prod --timeout=300s

# Check seed configuration
kubectl get cassandradatacenter hcd-paris -n janusgraph-banking-prod \
  -o jsonpath='{.spec.config.cassandra-yaml.seed_provider}'
```

#### Issue 3: JanusGraph Cannot Connect to HCD

**Symptoms**:
```bash
kubectl logs janusgraph-0 -n janusgraph-banking-prod
# ERROR: Cannot connect to Cassandra
```

**Diagnosis**:
```bash
# Check HCD service
kubectl get svc hcd-paris-service -n janusgraph-banking-prod

# Test connectivity
kubectl exec -it janusgraph-0 -n janusgraph-banking-prod \
  -- nc -zv hcd-paris-service 9042
```

**Solutions**:
```bash
# Check JanusGraph configuration
kubectl exec -it janusgraph-0 -n janusgraph-banking-prod \
  -- cat /etc/janusgraph/janusgraph-hcd.properties

# Verify HCD is accepting connections
kubectl exec -it hcd-paris-rack1-sts-0 -n janusgraph-banking-prod \
  -- cqlsh -e "SELECT * FROM system.local"
```

### Debugging Commands

**Get Logs**:
```bash
# Recent logs
kubectl logs janusgraph-0 -n janusgraph-banking-prod --tail=100

# Follow logs
kubectl logs -f janusgraph-0 -n janusgraph-banking-prod

# Previous container logs (after restart)
kubectl logs janusgraph-0 -n janusgraph-banking-prod --previous
```

**Execute Commands**:
```bash
# Interactive shell
kubectl exec -it janusgraph-0 -n janusgraph-banking-prod -- /bin/bash

# Single command
kubectl exec janusgraph-0 -n janusgraph-banking-prod \
  -- curl http://localhost:8182?gremlin=g.V().count()
```

**Check Resources**:
```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods -n janusgraph-banking-prod

# Describe pod
kubectl describe pod janusgraph-0 -n janusgraph-banking-prod
```

---

## Best Practices

### Security

1. **Use Secrets for Sensitive Data**:
   ```bash
   kubectl create secret generic db-credentials \
     --from-literal=password=$(openssl rand -base64 32)
   ```

2. **Enable Network Policies**:
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: janusgraph-network-policy
   spec:
     podSelector:
       matchLabels:
         app: janusgraph
     policyTypes:
       - Ingress
       - Egress
   ```

3. **Use RBAC**:
   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: Role
   metadata:
     name: janusgraph-operator
   rules:
     - apiGroups: [""]
       resources: ["pods", "services"]
       verbs: ["get", "list", "watch"]
   ```

### High Availability

1. **Use Pod Anti-Affinity**:
   ```yaml
   affinity:
     podAntiAffinity:
       requiredDuringSchedulingIgnoredDuringExecution:
         - labelSelector:
             matchExpressions:
               - key: app
                 operator: In
                 values:
                   - janusgraph
           topologyKey: kubernetes.io/hostname
   ```

2. **Set Pod Disruption Budgets**:
   ```yaml
   apiVersion: policy/v1
   kind: PodDisruptionBudget
   metadata:
     name: janusgraph-pdb
   spec:
     minAvailable: 2
     selector:
       matchLabels:
         app: janusgraph
   ```

3. **Use Multiple Replicas**:
   - JanusGraph: 3-5 replicas
   - HCD: 3-5 nodes
   - OpenSearch: 3 nodes minimum

### Performance

1. **Resource Requests and Limits**:
   ```yaml
   resources:
     requests:
       cpu: "4"
       memory: "16Gi"
     limits:
       cpu: "8"
       memory: "32Gi"
   ```

2. **Use Fast Storage**:
   - SSD/NVMe for HCD
   - gp3 (AWS) or Premium SSD (Azure)
   - IOPS: 3000+ for production

3. **Tune JVM Settings**:
   ```yaml
   env:
     - name: JAVA_OPTS
       value: "-Xms8g -Xmx8g -XX:+UseG1GC"
   ```

### Monitoring

1. **Enable Prometheus Metrics**:
   ```yaml
   annotations:
     prometheus.io/scrape: "true"
     prometheus.io/port: "9091"
     prometheus.io/path: "/metrics"
   ```

2. **Set Up Alerts**:
   - Pod not ready
   - High CPU/memory usage
   - Backup failures
   - Cluster health issues

3. **Use Grafana Dashboards**:
   - JanusGraph metrics
   - HCD cluster health
   - Application performance

---

## Additional Resources

- [Helm Chart README](../../helm/janusgraph-banking/README.md)
- [ArgoCD README](../../argocd/README.md)
- [Technical Specification](../implementation/k8s-openshift-deployment-technical-spec-2026-02-19.md)
- [Phase 3 Automation](../implementation/k8s-phase3-automation-complete-2026-02-19.md)
- [IBM DataStax HCD Documentation](https://docs.datastax.com/en/hcd/1.2/)
- [Mission Control Documentation](https://docs.datastax.com/en/mission-control/)

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-19  
**Maintained By**: Platform Engineering Team  
**Next Review**: 2026-03-19