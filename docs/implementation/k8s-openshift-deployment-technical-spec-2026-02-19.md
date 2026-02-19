# Kubernetes/OpenShift Deployment Technical Specification & Implementation Plan

**Date:** 2026-02-19  
**Version:** 1.0  
**Status:** Technical Specification - Ready for Implementation  
**Author:** IBM Bob - Technical Planning Mode  
**Related Documents:**
- [`docs/architecture/openshift-3-site-ha-dr-dora.md`](../architecture/openshift-3-site-ha-dr-dora.md)
- [`docs/architecture/ha-dr-resilient-architecture.md`](../architecture/ha-dr-resilient-architecture.md)
- [`helm/janusgraph-banking/Chart.yaml`](../../helm/janusgraph-banking/Chart.yaml)
- [`k8s/base/kustomization.yml`](../../k8s/base/kustomization.yml)

---

## Executive Summary

This document provides a comprehensive technical specification and phased implementation plan for deploying the Banking Graph Analytics Platform on Kubernetes/OpenShift with enterprise-grade High Availability (HA) and Disaster Recovery (DR) capabilities.

### Key Objectives

1. **Deploy IBM DataStax HCD** using K8ssandra Operator for production-grade Cassandra
2. **Complete Helm Chart** with all dependencies (HCD, OpenSearch, Pulsar, Vault)
3. **Implement Infrastructure as Code** with Terraform for reproducible deployments
4. **Integrate Mission Control** for centralized HCD cluster management
5. **Enable GitOps** with ArgoCD for continuous deployment
6. **Update Documentation** to English and align with implementation

### Current State vs Target State

| Component | Current State | Target State | Priority | Effort |
|-----------|---------------|--------------|----------|--------|
| **HCD Deployment** | ❌ Missing | ✅ K8ssandra Operator, 3 replicas, RF=3 | P0 | 16h |
| **Resource Types** | ❌ Deployment (wrong) | ✅ StatefulSet (correct) | P0 | 8h |
| **Storage** | ❌ No PVCs | ✅ PersistentVolumeClaims, StorageClasses | P0 | 12h |
| **Helm Chart** | ⚠️ Incomplete (76 lines) | ✅ Complete with dependencies | P0 | 20h |
| **Terraform IaC** | ❌ Missing | ✅ Complete modules for 3-site | P1 | 40h |
| **Mission Control** | ❌ Missing | ✅ Deployed and configured | P1 | 24h |
| **GitOps (ArgoCD)** | ❌ No CD | ✅ ArgoCD with auto-sync | P1 | 16h |
| **Tekton CD** | ⚠️ CI only | ✅ Complete CI/CD pipeline | P1 | 24h |
| **Documentation** | ⚠️ French, gaps | ✅ English, complete | P2 | 24h |
| **OpenShift Optimizations** | ❌ Generic K8s | ✅ Routes, SCC, monitoring | P2 | 16h |

**Total Estimated Effort:** 200 hours (25 working days, ~5 weeks)

### Implementation Timeline

- **Phase 1 (Weeks 1-2):** Foundation - HCD, StatefulSets, Storage, Terraform
- **Phase 2 (Weeks 3-4):** Complete Stack - Helm dependencies, Mission Control, Multi-DC
- **Phase 3 (Weeks 5-6):** Automation - ArgoCD, Tekton CD, Backup/Restore
- **Phase 4 (Weeks 7-8):** Documentation & Testing - Guides, DR testing, Performance tuning

---

## Table of Contents

1. [Gap Analysis](#1-gap-analysis)
2. [Technical Specifications](#2-technical-specifications)
3. [Implementation Plan - Phase 1](#3-implementation-plan---phase-1-foundation)
4. [Implementation Plan - Phase 2](#4-implementation-plan---phase-2-complete-stack)
5. [Implementation Plan - Phase 3](#5-implementation-plan---phase-3-automation)
6. [Implementation Plan - Phase 4](#6-implementation-plan---phase-4-documentation--testing)
7. [Validation & Testing](#7-validation--testing)
8. [Documentation Updates](#8-documentation-updates)
9. [Risk Assessment](#9-risk-assessment)
10. [Appendices](#10-appendices)

---

## 1. Gap Analysis

### 1.1 Critical Gaps (P0 - Blocks Production)

#### Gap 1.1: Missing HCD Deployment

**Current State:**
- No HCD/Cassandra deployment in Helm chart or Kustomize
- JanusGraph configured to use HCD but HCD not deployed
- No K8ssandra Operator installed

**Impact:** JanusGraph cannot function without storage backend

**Required Changes:**
1. Install K8ssandra Operator via Helm dependency
2. Create K8ssandraCluster CRD for HCD deployment
3. Configure NetworkTopologyStrategy with RF=3
4. Set up multi-DC replication across 3 sites
5. Configure persistent storage with StorageClass

**Estimated Effort:** 16 hours

#### Gap 1.2: Wrong Resource Type (Deployment vs StatefulSet)

**Current State:**
- JanusGraph uses `Deployment` (line 2 in `k8s/base/janusgraph-deployment.yml`)
- No persistent storage configured
- No stable network identity

**Impact:** Data loss on pod restart, cannot maintain stable connections

**Required Changes:**
1. Convert JanusGraph from Deployment to StatefulSet
2. Add PersistentVolumeClaim template
3. Create headless service for stable network identity
4. Configure podManagementPolicy: OrderedReady
5. Add pod anti-affinity rules

**Estimated Effort:** 8 hours

#### Gap 1.3: Missing Persistent Storage

**Current State:**
- No PersistentVolumeClaims defined
- No StorageClass configuration
- ConfigMap-only storage (ephemeral)

**Impact:** All data lost on pod restart, cannot meet RPO requirements

**Required Changes:**
1. Define StorageClass for each component (HCD, JanusGraph, Pulsar, OpenSearch)
2. Add PVC templates to StatefulSets
3. Configure volume mount paths
4. Set up backup policies

**Estimated Effort:** 12 hours

#### Gap 1.4: Incomplete Helm Chart

**Current State:**
- Helm chart only has JanusGraph and API (76 lines in `helm/janusgraph-banking/values.yaml`)
- No dependencies defined in Chart.yaml
- Missing HCD, OpenSearch, Pulsar, Vault subcharts

**Impact:** Cannot deploy complete stack with single Helm command

**Required Changes:**
1. Add Helm dependencies in Chart.yaml (k8ssandra-operator, opensearch, pulsar, vault)
2. Create values overrides for each dependency
3. Add Mission Control subchart
4. Configure inter-service dependencies

**Estimated Effort:** 20 hours

**Total P0 Effort:** 56 hours

### 1.2 High Priority Gaps (P1 - Limits Operations)

#### Gap 1.5: No Terraform Infrastructure as Code

**Current State:** No Terraform modules for OpenShift provisioning

**Impact:** Inconsistent environments, slow disaster recovery

**Estimated Effort:** 40 hours

#### Gap 1.6: No Mission Control Integration

**Current State:** No DataStax Mission Control deployment

**Impact:** Difficult cluster operations, no visual monitoring

**Estimated Effort:** 24 hours

#### Gap 1.7: No GitOps with ArgoCD

**Current State:** Manual kubectl/helm deployments

**Impact:** Slow deployments, configuration drift, no audit trail

**Estimated Effort:** 16 hours

#### Gap 1.8: No Continuous Deployment Pipeline

**Current State:** Tekton only has CI pipeline

**Impact:** Manual promotion between environments

**Estimated Effort:** 24 hours

**Total P1 Effort:** 104 hours

### 1.3 Medium Priority Gaps (P2 - Nice to Have)

#### Gap 1.9: Documentation in French

**Current State:** `docs/architecture/openshift-3-site-ha-dr-dora.md` is in French

**Impact:** Reduced accessibility for international teams

**Estimated Effort:** 8 hours

#### Gap 1.10: Missing OpenShift-Specific Optimizations

**Current State:** Generic Kubernetes manifests

**Impact:** Not leveraging OpenShift features

**Estimated Effort:** 16 hours

**Total P2 Effort:** 24 hours

### 1.4 Gap Summary

| Priority | Gaps | Total Effort | Impact |
|----------|------|--------------|--------|
| **P0 Critical** | 4 gaps | 56 hours | Blocks production deployment |
| **P1 High** | 4 gaps | 104 hours | Limits operational efficiency |
| **P2 Medium** | 2 gaps | 24 hours | Reduces usability |
| **Total** | 10 gaps | 184 hours | 23 working days |

---

## 2. Technical Specifications

### 2.1 HCD Cassandra Deployment Specification

#### 2.1.1 K8ssandraCluster CRD

```yaml
apiVersion: k8ssandra.io/v1alpha1
kind: K8ssandraCluster
metadata:
  name: hcd-cluster
  namespace: janusgraph-banking
spec:
  cassandra:
    serverVersion: "4.1.3"  # HCD 1.2.3 is based on Cassandra 4.1.3
    serverImage: "datastax/hcd:1.2.3"
    datacenters:
      - metadata:
          name: dc1
        size: 3
        storageConfig:
          cassandraDataVolumeClaimSpec:
            storageClassName: hcd-storage
            accessModes:
              - ReadWriteOnce
            resources:
              requests:
                storage: 500Gi
        config:
          jvmOptions:
            heapSize: 8Gi
            heapNewGenSize: 2Gi
        resources:
          requests:
            cpu: 4
            memory: 16Gi
          limits:
            cpu: 8
            memory: 32Gi
        racks:
          - name: rack1
            affinityLabels:
              topology.kubernetes.io/zone: zone-a
          - name: rack2
            affinityLabels:
              topology.kubernetes.io/zone: zone-b
          - name: rack3
            affinityLabels:
              topology.kubernetes.io/zone: zone-c
    networking:
      hostNetwork: false
    mgmtAPIHeap: 256Mi
  stargate:
    size: 1
    heapSize: 512Mi
  reaper:
    enabled: true
  medusa:
    enabled: true
    storageProperties:
      storageProvider: s3
      bucketName: hcd-backups
```

#### 2.1.2 Multi-DC Configuration for 3-Site Deployment

**Keyspace Configuration:**
```cql
CREATE KEYSPACE janusgraph
WITH replication = {
  'class': 'NetworkTopologyStrategy',
  'paris-dc': 3,
  'london-dc': 3,
  'frankfurt-dc': 3
}
AND durable_writes = true;
```

### 2.2 JanusGraph StatefulSet Specification

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: janusgraph
  namespace: janusgraph-banking
spec:
  serviceName: janusgraph-headless
  replicas: 3
  selector:
    matchLabels:
      app: janusgraph
  template:
    metadata:
      labels:
        app: janusgraph
    spec:
      serviceAccountName: janusgraph-sa
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
      containers:
        - name: janusgraph
          image: janusgraph/janusgraph:1.0.0
          ports:
            - containerPort: 8182
              name: gremlin
          resources:
            requests:
              cpu: 2
              memory: 4Gi
            limits:
              cpu: 4
              memory: 8Gi
          env:
            - name: JAVA_OPTIONS
              value: "-Xms2g -Xmx6g"
            - name: JANUSGRAPH_STORAGE_BACKEND
              value: "cql"
            - name: JANUSGRAPH_STORAGE_HOSTNAME
              value: "hcd-cluster-dc1-service.janusgraph-banking.svc.cluster.local"
          volumeMounts:
            - name: data
              mountPath: /opt/janusgraph/data
            - name: config
              mountPath: /opt/janusgraph/conf
          readinessProbe:
            httpGet:
              path: /health
              port: 8182
            initialDelaySeconds: 60
            periodSeconds: 10
      volumes:
        - name: config
          configMap:
            name: janusgraph-config
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: janusgraph-storage
        resources:
          requests:
            storage: 100Gi
```

### 2.3 Complete Helm Chart Structure

```
helm/janusgraph-banking/
├── Chart.yaml                    # Chart metadata with dependencies
├── values.yaml                   # Default values
├── values-dev.yaml              # Development overrides
├── values-staging.yaml          # Staging overrides
├── values-prod.yaml             # Production overrides (3-site)
├── templates/
│   ├── _helpers.tpl             # Template helpers
│   ├── namespace.yaml           # Namespace
│   ├── rbac.yaml                # ServiceAccount, Role, RoleBinding
│   ├── configmaps.yaml          # Configuration
│   ├── secrets.yaml             # Secrets (from Vault)
│   ├── hcd-cluster.yaml         # K8ssandraCluster CRD
│   ├── janusgraph-statefulset.yaml  # JanusGraph StatefulSet
│   ├── api-deployment.yaml      # API Deployment
│   ├── network-policy.yaml      # NetworkPolicies
│   ├── pdb.yaml                 # PodDisruptionBudgets
│   ├── hpa.yaml                 # HorizontalPodAutoscalers
│   ├── route.yaml               # OpenShift Routes
│   └── monitoring/
│       ├── servicemonitor.yaml  # Prometheus ServiceMonitor
│       └── prometheusrule.yaml  # Alert rules
└── charts/                      # Dependency charts (downloaded)
```

#### Enhanced Chart.yaml with Dependencies

```yaml
apiVersion: v2
name: janusgraph-banking
description: Banking Fraud Detection & AML Compliance on JanusGraph with HCD
type: application
version: 2.0.0
appVersion: "1.2.0"

dependencies:
  - name: k8ssandra-operator
    version: 1.14.0
    repository: https://helm.k8ssandra.io/stable
    condition: k8ssandra.enabled
  - name: opensearch
    version: 2.11.0
    repository: https://opensearch-project.github.io/helm-charts
    condition: opensearch.enabled
  - name: pulsar
    version: 3.1.0
    repository: https://pulsar.apache.org/charts
    condition: pulsar.enabled
  - name: vault
    version: 0.27.0
    repository: https://helm.releases.hashicorp.com
    condition: vault.enabled
```

### 2.4 Terraform Module Structure

```
terraform/
├── modules/
│   ├── openshift-cluster/       # Cluster provisioning
│   ├── networking/              # VPC, subnets, load balancers
│   ├── storage/                 # StorageClasses, PV provisioning
│   └── monitoring/              # Prometheus, Grafana
└── environments/
    ├── dev/                     # Dev environment
    ├── staging/                 # Staging environment
    └── prod/                    # Production 3-site
```

### 2.5 ArgoCD Application Specification

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: janusgraph-banking-prod
  namespace: argocd
spec:
  project: banking
  source:
    repoURL: https://github.com/your-org/janusgraph-banking
    targetRevision: main
    path: helm/janusgraph-banking
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: janusgraph-banking
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

---

## 3. Implementation Plan - Phase 1: Foundation

**Duration:** Weeks 1-2  
**Objective:** Deploy HCD with K8ssandra, convert to StatefulSets, implement storage, create Terraform modules

### Week 1: HCD and StatefulSets

#### Task 1.1: Install K8ssandra Operator (4 hours)

**Steps:**
1. Add K8ssandra Operator to Helm dependencies in `Chart.yaml`
2. Create `templates/hcd-cluster.yaml` with K8ssandraCluster CRD
3. Configure 3-node cluster with RF=3
4. Deploy and verify HCD cluster health

**Deliverables:**
- `helm/janusgraph-banking/Chart.yaml` updated
- `helm/janusgraph-banking/templates/hcd-cluster.yaml` created
- HCD cluster running with 3 nodes

**Validation:**
```bash
kubectl get k8ssandraclusters -n janusgraph-banking
kubectl exec -it hcd-cluster-dc1-default-sts-0 -n janusgraph-banking -- nodetool status
```

**Success Criteria:**
- K8ssandraCluster CRD deployed
- 3 HCD pods running
- `nodetool status` shows UN (Up/Normal) for all nodes

#### Task 1.2: Convert JanusGraph to StatefulSet (8 hours)

**Steps:**
1. Create `templates/janusgraph-statefulset.yaml` replacing Deployment
2. Add volumeClaimTemplates for data persistence
3. Create headless service for stable network identity
4. Configure podManagementPolicy: OrderedReady
5. Add pod anti-affinity rules
6. Update `k8s/base/janusgraph-deployment.yml` to StatefulSet

**Deliverables:**
- `helm/janusgraph-banking/templates/janusgraph-statefulset.yaml` created
- `k8s/base/janusgraph-deployment.yml` converted
- Headless service created

**Validation:**
```bash
kubectl get statefulsets -n janusgraph-banking
kubectl get pvc -n janusgraph-banking
kubectl get pods -n janusgraph-banking -o wide
```

**Success Criteria:**
- StatefulSet deployed with 3 replicas
- PVCs created for each pod
- Pods distributed across nodes (anti-affinity working)

#### Task 1.3: Implement Persistent Storage (4 hours)

**Steps:**
1. Create `templates/storage-classes.yaml` with StorageClass definitions
2. Add PVC templates to StatefulSets
3. Configure volume mount paths
4. Set up backup policies

**Deliverables:**
- `helm/janusgraph-banking/templates/storage-classes.yaml` created
- PVCs configured for HCD, JanusGraph, Pulsar, OpenSearch
- Backup policies defined

**Validation:**
```bash
kubectl get storageclasses
kubectl get pvc -n janusgraph-banking
kubectl describe pvc janusgraph-data-janusgraph-0 -n janusgraph-banking
```

**Success Criteria:**
- StorageClasses created for all components
- PVCs bound to PVs
- Data persists across pod restarts

### Week 2: Terraform Infrastructure

#### Task 1.4: Create Terraform Modules (24 hours)

**Steps:**
1. Create `terraform/modules/openshift-cluster/` for cluster provisioning
2. Create `terraform/modules/networking/` for VPC, subnets, load balancers
3. Create `terraform/modules/storage/` for StorageClasses
4. Create `terraform/modules/monitoring/` for Prometheus, Grafana

**Deliverables:**
- `terraform/modules/openshift-cluster/` complete with main.tf, variables.tf, outputs.tf
- `terraform/modules/networking/` complete
- `terraform/modules/storage/` complete
- `terraform/modules/monitoring/` complete

**Validation:**
```bash
cd terraform/modules/openshift-cluster
terraform init
terraform validate
terraform plan
```

**Success Criteria:**
- All modules pass `terraform validate`
- `terraform plan` shows expected resources
- Modules are reusable across environments

#### Task 1.5: Create Environment Configurations (16 hours)

**Steps:**
1. Create `terraform/environments/dev/` configuration
2. Create `terraform/environments/staging/` configuration
3. Create `terraform/environments/prod/` configuration (3-site)
4. Configure remote state backend (S3 + DynamoDB)

**Deliverables:**
- `terraform/environments/dev/` complete
- `terraform/environments/staging/` complete
- `terraform/environments/prod/` complete
- Remote state backend configured

**Validation:**
```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply  # Deploy dev environment
```

**Success Criteria:**
- Dev environment deploys successfully
- State stored in remote backend
- Infrastructure matches specifications

### Phase 1 Milestones

- ✅ HCD cluster running with 3 nodes
- ✅ JanusGraph StatefulSet with persistent storage
- ✅ Terraform modules for infrastructure provisioning
- ✅ Dev environment deployed via Terraform

**Phase 1 Total Effort:** 56 hours (7 working days)

---

## 4. Implementation Plan - Phase 2: Complete Stack

**Duration:** Weeks 3-4  
**Objective:** Complete Helm chart with all dependencies, deploy Mission Control, configure multi-DC

### Week 3: Helm Chart Completion

#### Task 2.1: Add Helm Dependencies (12 hours)

**Steps:**
1. Update `Chart.yaml` with all dependencies (opensearch, pulsar, vault)
2. Create values overrides for each dependency
3. Configure inter-service dependencies
4. Test dependency resolution

**Deliverables:**
- `Chart.yaml` with complete dependencies
- `values.yaml` with dependency configurations
- Dependency charts downloaded to `charts/`

**Validation:**
```bash
helm dependency update helm/janusgraph-banking
helm lint helm/janusgraph-banking
helm template janusgraph-banking helm/janusgraph-banking --debug
```

**Success Criteria:**
- All dependencies resolve successfully
- Helm lint passes
- Template renders without errors

#### Task 2.2: Create Complete values.yaml (8 hours)

**Steps:**
1. Expand `values.yaml` to include all components
2. Create `values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml`
3. Configure resource limits for each component
4. Set up monitoring and observability

**Deliverables:**
- Enhanced `values.yaml` (300+ lines)
- Environment-specific value files
- Resource limits configured

**Validation:**
```bash
helm install janusgraph-banking helm/janusgraph-banking \
  -f helm/janusgraph-banking/values-dev.yaml \
  --dry-run --debug
```

**Success Criteria:**
- All components configured
- Resource limits appropriate for environment
- Dry-run succeeds

### Week 4: Mission Control and Multi-DC

#### Task 2.3: Deploy Mission Control (12 hours)

**Steps:**
1. Create `templates/mission-control.yaml`
2. Configure Mission Control to manage HCD clusters
3. Set up authentication with Vault
4. Configure backup schedules
5. Create custom dashboards

**Deliverables:**
- `templates/mission-control.yaml` created
- Mission Control deployed and accessible
- Backup schedules configured

**Validation:**
```bash
kubectl get pods -n janusgraph-banking -l app=mission-control
kubectl port-forward svc/mission-control 8080:8080 -n janusgraph-banking
# Access http://localhost:8080
```

**Success Criteria:**
- Mission Control UI accessible
- HCD clusters visible in UI
- Backup schedules active

#### Task 2.4: Configure Multi-DC Replication (12 hours)

**Steps:**
1. Create K8ssandraCluster CRDs for each site (Paris, London, Frankfurt)
2. Configure NetworkTopologyStrategy keyspaces
3. Set up cross-site replication
4. Test failover scenarios

**Deliverables:**
- K8ssandraCluster CRDs for 3 sites
- Keyspaces with multi-DC replication
- Failover procedures documented

**Validation:**
```bash
# On each site
kubectl exec -it hcd-cluster-dc1-default-sts-0 -n janusgraph-banking -- \
  cqlsh -e "DESCRIBE KEYSPACE janusgraph"
```

**Success Criteria:**
- All 3 sites have HCD clusters
- Keyspaces replicated across sites
- Failover tested successfully

### Phase 2 Milestones

- ✅ Complete Helm chart with all dependencies
- ✅ Mission Control deployed and managing HCD
- ✅ Multi-DC replication configured and tested
- ✅ All components deployed in dev environment

**Phase 2 Total Effort:** 44 hours (5.5 working days)

---

## 5. Implementation Plan - Phase 3: Automation

**Duration:** Weeks 5-6  
**Objective:** Enable GitOps with ArgoCD, complete CI/CD pipeline, implement backup/restore

### Week 5: GitOps with ArgoCD

#### Task 3.1: Install ArgoCD (8 hours)

**Steps:**
1. Install ArgoCD Operator
2. Create ArgoCD instance
3. Configure RBAC and authentication
4. Set up notifications (Slack, email)

**Deliverables:**
- ArgoCD Operator installed
- ArgoCD instance running
- RBAC configured

**Validation:**
```bash
kubectl get pods -n argocd
kubectl port-forward svc/argocd-server 8080:443 -n argocd
# Access https://localhost:8080
```

**Success Criteria:**
- ArgoCD UI accessible
- Authentication working
- Notifications configured

#### Task 3.2: Create ArgoCD Applications (8 hours)

**Steps:**
1. Create Application manifests for each environment
2. Configure sync policies (auto-sync, prune, self-heal)
3. Set up ApplicationSets for multi-cluster deployment
4. Test deployment and rollback

**Deliverables:**
- `argocd/applications/` directory with Application manifests
- Sync policies configured
- ApplicationSets for multi-cluster

**Validation:**
```bash
kubectl apply -f argocd/applications/janusgraph-banking-dev.yaml
argocd app get janusgraph-banking-dev
argocd app sync janusgraph-banking-dev
```

**Success Criteria:**
- Applications deploy successfully
- Auto-sync working
- Rollback tested

### Week 6: CI/CD and Backup

#### Task 3.3: Complete Tekton CD Pipeline (12 hours)

**Steps:**
1. Create Tekton CD pipeline tasks
2. Integrate with ArgoCD for deployment
3. Add automated rollback on failure
4. Configure deployment notifications

**Deliverables:**
- `tekton/pipelines/cd-pipeline.yaml` created
- Integration with ArgoCD
- Rollback automation

**Validation:**
```bash
kubectl apply -f tekton/pipelines/cd-pipeline.yaml
tkn pipeline start cd-pipeline --showlog
```

**Success Criteria:**
- CD pipeline runs successfully
- Deploys to dev, promotes to staging
- Rollback on failure working

#### Task 3.4: Implement Backup/Restore (12 hours)

**Steps:**
1. Configure Medusa for HCD backups
2. Set up backup schedules
3. Test restore procedures
4. Document backup/restore runbook

**Deliverables:**
- Medusa configured for S3 backups
- Backup schedules active
- Restore procedures tested

**Validation:**
```bash
# Trigger backup
kubectl exec -it hcd-cluster-dc1-default-sts-0 -n janusgraph-banking -- \
  medusa backup --backup-name test-backup

# Test restore
kubectl exec -it hcd-cluster-dc1-default-sts-0 -n janusgraph-banking -- \
  medusa restore --backup-name test-backup
```

**Success Criteria:**
- Backups running on schedule
- Restore tested successfully
- RPO < 5 minutes achieved

### Phase 3 Milestones

- ✅ ArgoCD managing all deployments
- ✅ Complete CI/CD pipeline operational
- ✅ Backup/restore tested and documented
- ✅ Automated rollback working

**Phase 3 Total Effort:** 40 hours (5 working days)

---

## 6. Implementation Plan - Phase 4: Documentation & Testing

**Duration:** Weeks 7-8  
**Objective:** Update documentation, perform DR testing, optimize performance

### Week 7: Documentation Updates

#### Task 4.1: Translate OpenShift Architecture Doc (8 hours)

**Steps:**
1. Translate `docs/architecture/openshift-3-site-ha-dr-dora.md` to English
2. Maintain French version as `openshift-3-site-ha-dr-dora.fr.md`
3. Update all cross-references
4. Add language indicator to all docs

**Deliverables:**
- English version of OpenShift architecture doc
- French version preserved
- Cross-references updated

**Success Criteria:**
- English doc complete and accurate
- All links working
- Consistent terminology

#### Task 4.2: Create K8s/OpenShift Deployment Guide (8 hours)

**Steps:**
1. Create `docs/guides/k8s-openshift-deployment-guide.md`
2. Document deployment procedures
3. Add troubleshooting section
4. Include examples and screenshots

**Deliverables:**
- Complete deployment guide
- Troubleshooting section
- Examples and screenshots

**Success Criteria:**
- Guide covers all deployment scenarios
- Troubleshooting section comprehensive
- Examples tested

#### Task 4.3: Document HCD Operations (8 hours)

**Steps:**
1. Create `docs/operations/hcd-operations-runbook.md`
2. Document backup/restore procedures
3. Document scaling procedures
4. Document upgrade procedures

**Deliverables:**
- HCD operations runbook
- Backup/restore procedures
- Scaling and upgrade procedures

**Success Criteria:**
- Runbook covers all operations
- Procedures tested
- Clear and actionable

### Week 8: DR Testing and Performance

#### Task 4.4: Disaster Recovery Testing (12 hours)

**Steps:**
1. Test site failover (Paris → London)
2. Test data recovery from backups
3. Measure RTO and RPO
4. Document DR procedures

**Deliverables:**
- DR test results
- RTO/RPO measurements
- DR procedures documented

**Validation:**
```bash
# Simulate site failure
kubectl scale statefulset hcd-cluster-dc1-default-sts --replicas=0 -n janusgraph-banking

# Verify failover to London
kubectl get pods -n janusgraph-banking --context=london-cluster

# Measure recovery time
```

**Success Criteria:**
- RTO < 30 minutes
- RPO < 5 minutes
- DR procedures validated

#### Task 4.5: Performance Tuning (12 hours)

**Steps:**
1. Run performance benchmarks
2. Tune JVM settings for JanusGraph
3. Optimize HCD configuration
4. Document performance baselines

**Deliverables:**
- Performance benchmark results
- Tuned configurations
- Performance baselines documented

**Validation:**
```bash
# Run benchmarks
kubectl apply -f tests/performance/benchmark-job.yaml
kubectl logs -f job/benchmark-job -n janusgraph-banking
```

**Success Criteria:**
- Query latency < 100ms (P95)
- Throughput > 1000 TPS
- Resource utilization optimized

### Phase 4 Milestones

- ✅ All documentation updated and in English
- ✅ DR testing complete with RTO/RPO validated
- ✅ Performance tuned and baselined
- ✅ Production-ready deployment

**Phase 4 Total Effort:** 48 hours (6 working days)

---

## 7. Validation & Testing

### 7.1 Validation Checklist

**Infrastructure:**
- [ ] OpenShift clusters deployed in 3 sites
- [ ] Networking configured (VPC, subnets, load balancers)
- [ ] Storage classes created and working
- [ ] Monitoring stack deployed (Prometheus, Grafana)

**HCD Deployment:**
- [ ] K8ssandra Operator installed
- [ ] HCD clusters running in all 3 sites
- [ ] Multi-DC replication configured
- [ ] Keyspaces created with NetworkTopologyStrategy
- [ ] Medusa backups configured and tested

**JanusGraph:**
- [ ] StatefulSets deployed with 3 replicas per site
- [ ] Persistent storage configured
- [ ] Connected to HCD backend
- [ ] Connected to OpenSearch for indexing
- [ ] Health checks passing

**Supporting Services:**
- [ ] OpenSearch deployed and indexed
- [ ] Pulsar deployed with geo-replication
- [ ] Vault deployed for secrets management
- [ ] Mission Control deployed and managing HCD

**Automation:**
- [ ] ArgoCD managing all deployments
- [ ] Tekton CI/CD pipeline operational
- [ ] Automated backups running
- [ ] Automated rollback tested

**Documentation:**
- [ ] All docs translated to English
- [ ] Deployment guide complete
- [ ] Operations runbook complete
- [ ] DR procedures documented

### 7.2 Testing Strategy

**Unit Tests:**
- Helm chart linting
- Terraform validation
- YAML syntax validation

**Integration Tests:**
- Deploy to dev environment
- Verify all services healthy
- Test inter-service communication

**Performance Tests:**
- Load testing with 1000 TPS
- Latency testing (P95 < 100ms)
- Resource utilization monitoring

**DR Tests:**
- Site failover testing
- Backup/restore testing
- RTO/RPO validation

### 7.3 Success Criteria

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| **RTO** | < 30 minutes | DR failover test |
| **RPO** | < 5 minutes | Backup frequency check |
| **Availability** | 99.99% | Uptime monitoring |
| **Query Latency (P95)** | < 100ms | Performance benchmarks |
| **Throughput** | > 1000 TPS | Load testing |
| **Deployment Time** | < 30 minutes | ArgoCD sync time |
| **Rollback Time** | < 5 minutes | Automated rollback test |

---

## 8. Documentation Updates

### 8.1 New Documentation Required

1. **K8s/OpenShift Deployment Guide** (`docs/guides/k8s-openshift-deployment-guide.md`)
   - Prerequisites
   - Installation steps
   - Configuration
   - Troubleshooting

2. **HCD Operations Runbook** (`docs/operations/hcd-operations-runbook.md`)
   - Daily operations
   - Backup/restore procedures
   - Scaling procedures
   - Upgrade procedures

3. **Terraform Usage Guide** (`terraform/README.md`)
   - Module documentation
   - Environment setup
   - Deployment procedures
   - State management

4. **ArgoCD Configuration Guide** (`argocd/README.md`)
   - Application setup
   - Sync policies
   - Multi-cluster management
   - Troubleshooting

### 8.2 Documentation Updates Required

1. **OpenShift Architecture Doc** (`docs/architecture/openshift-3-site-ha-dr-dora.md`)
   - Translate to English
   - Update with actual implementation details
   - Add cross-references to new docs

2. **HA/DR Architecture Doc** (`docs/architecture/ha-dr-resilient-architecture.md`)
   - Add K8s/OpenShift section
   - Update with multi-DC configuration
   - Add Mission Control integration

3. **README.md**
   - Add K8s/OpenShift deployment instructions
   - Update architecture diagram
   - Add links to new documentation

### 8.3 Documentation Standards

All documentation must follow:
- Kebab-case naming convention
- Markdown format
- Clear section headers
- Code examples with syntax highlighting
- Cross-references to related docs
- Metadata (date, version, status)

---

## 9. Risk Assessment

### 9.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **HCD cluster instability** | Medium | High | Thorough testing in dev, gradual rollout |
| **Data loss during migration** | Low | Critical | Comprehensive backup before migration |
| **Performance degradation** | Medium | Medium | Performance testing, tuning, monitoring |
| **Network latency issues** | Low | Medium | Network optimization, caching strategies |
| **Storage capacity issues** | Low | High | Capacity planning, monitoring, alerts |

### 9.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Insufficient training** | Medium | Medium | Comprehensive documentation, training sessions |
| **Complex troubleshooting** | Medium | Medium | Detailed runbooks, escalation procedures |
| **Backup failures** | Low | High | Automated monitoring, regular testing |
| **DR test failures** | Medium | High | Regular DR drills, documented procedures |

### 9.3 Project Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Timeline delays** | Medium | Medium | Phased approach, buffer time |
| **Resource constraints** | Low | Medium | Clear task assignments, parallel work |
| **Scope creep** | Medium | Medium | Strict change control, prioritization |

---

## 10. Appendices

### 10.1 Glossary

- **HCD:** Hyper-Converged Database (IBM DataStax Cassandra distribution)
- **K8ssandra:** Kubernetes operator for Cassandra lifecycle management
- **StatefulSet:** Kubernetes resource for stateful applications
- **PVC:** PersistentVolumeClaim
- **RF:** Replication Factor
- **NetworkTopologyStrategy:** Cassandra replication strategy for multi-DC
- **RTO:** Recovery Time Objective
- **RPO:** Recovery Point Objective

### 10.2 References

- [K8ssandra Documentation](https://docs.k8ssandra.io/)
- [OpenShift Documentation](https://docs.openshift.com/)
- [JanusGraph Documentation](https://docs.janusgraph.org/)
- [Helm Documentation](https://helm.sh/docs/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Terraform Documentation](https://www.terraform.io/docs/)

### 10.3 Related Documents

- [`docs/architecture/openshift-3-site-ha-dr-dora.md`](../architecture/openshift-3-site-ha-dr-dora.md)
- [`docs/architecture/ha-dr-resilient-architecture.md`](../architecture/ha-dr-resilient-architecture.md)
- [`docs/operations/operations-runbook.md`](../operations/operations-runbook.md)
- [`AGENTS.md`](../../AGENTS.md)

---

## Summary

This technical specification provides a comprehensive, phased approach to deploying the Banking Graph Analytics Platform on Kubernetes/OpenShift with enterprise-grade HA/DR capabilities.

### Key Deliverables

1. **HCD Deployment** with K8ssandra Operator and multi-DC replication
2. **Complete Helm Chart** with all dependencies
3. **Terraform IaC** for reproducible infrastructure
4. **Mission Control** for centralized HCD management
5. **GitOps with ArgoCD** for continuous deployment
6. **Complete Documentation** in English

### Implementation Timeline

- **Phase 1 (Weeks 1-2):** Foundation - 56 hours
- **Phase 2 (Weeks 3-4):** Complete Stack - 44 hours
- **Phase 3 (Weeks 5-6):** Automation - 40 hours
- **Phase 4 (Weeks 7-8):** Documentation & Testing - 48 hours

**Total Effort:** 188 hours (~24 working days, ~5 weeks)

### Next Steps

1. Review and approve this technical specification
2. Allocate resources for implementation
3. Begin Phase 1: Foundation (HCD, StatefulSets, Storage, Terraform)
4. Schedule regular progress reviews
5. Plan production deployment after Phase 4 completion

---

**Document Status:** Ready for Review and Approval  
**Last Updated:** 2026-02-19  
**Version:** 1.0
