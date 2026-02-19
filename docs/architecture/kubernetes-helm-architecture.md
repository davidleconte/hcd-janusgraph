# Kubernetes & Helm Architecture

**Date:** 2026-02-19  
**Version:** 1.0  
**Status:** Active  
**Last Updated:** 2026-02-19

---

## Executive Summary

This document describes the Kubernetes and Helm-based deployment architecture for the HCD + JanusGraph Banking Platform. The platform uses **Helm charts** for package management and **ArgoCD** for GitOps-based continuous deployment.

**Key Features:**
- ✅ **Helm Charts**: Templated Kubernetes manifests
- ✅ **ArgoCD GitOps**: Automated deployment from Git
- ✅ **Multi-Environment**: Dev, staging, production configs
- ✅ **Kustomize Deprecated**: Migrated to Helm + ArgoCD
- ✅ **Production Ready**: Health checks, resource limits, security

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Helm Chart Structure](#2-helm-chart-structure)
3. [Kubernetes Resources](#3-kubernetes-resources)
4. [ArgoCD GitOps](#4-argocd-gitops)
5. [Multi-Environment Strategy](#5-multi-environment-strategy)
6. [Security Architecture](#6-security-architecture)
7. [Deployment Workflows](#7-deployment-workflows)
8. [Migration from Kustomize](#8-migration-from-kustomize)

---

## 1. Architecture Overview

### 1.1 Deployment Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Git Repository                        │
│              (Source of Truth)                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Git Sync
                     ▼
┌─────────────────────────────────────────────────────────┐
│                      ArgoCD                              │
│              (GitOps Controller)                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Apply Manifests
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 Kubernetes Cluster                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Helm Release                         │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │  Banking Platform Pods                      │  │  │
│  │  │  - HCD (Cassandra)                          │  │  │
│  │  │  - JanusGraph                               │  │  │
│  │  │  - API Services                             │  │  │
│  │  │  - Consumers                                │  │  │
│  │  │  - Monitoring                               │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Key Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Helm** | Package manager for Kubernetes | Helm 3.x |
| **ArgoCD** | GitOps continuous deployment | ArgoCD 2.x |
| **Kubernetes** | Container orchestration | K8s 1.28+ |
| **Helm Charts** | Templated manifests | YAML + Go templates |
| **Values Files** | Environment-specific configs | YAML |

### 1.3 Design Principles

- **GitOps**: Git as single source of truth
- **Declarative**: Desired state in Git
- **Automated**: ArgoCD syncs automatically
- **Auditable**: All changes tracked in Git
- **Rollback**: Easy rollback via Git revert

---

## 2. Helm Chart Structure

### 2.1 Chart Organization

```
helm/janusgraph-banking/
├── Chart.yaml                 # Chart metadata
├── values.yaml                # Default values
├── values-dev.yaml            # Dev overrides
├── values-staging.yaml        # Staging overrides
├── values-prod.yaml           # Production overrides
├── templates/                 # Kubernetes manifests
│   ├── _helpers.tpl          # Template helpers
│   ├── namespace.yaml        # Namespace
│   ├── hcd-statefulset.yaml  # HCD StatefulSet
│   ├── janusgraph-deployment.yaml  # JanusGraph
│   ├── api-deployment.yaml   # API services
│   ├── consumers-deployment.yaml   # Consumers
│   ├── services.yaml         # Services
│   ├── ingress.yaml          # Ingress/Routes
│   ├── configmaps.yaml       # ConfigMaps
│   ├── secrets.yaml          # Secrets
│   ├── pvc.yaml              # PersistentVolumeClaims
│   ├── network-policy.yaml   # NetworkPolicies
│   └── route.yaml            # OpenShift Routes
└── README.md                  # Chart documentation
```

### 2.2 Chart.yaml

```yaml
apiVersion: v2
name: janusgraph-banking
description: HCD + JanusGraph Banking Compliance Platform
type: application
version: 1.4.0
appVersion: "1.4.0"

keywords:
  - janusgraph
  - cassandra
  - graph-database
  - banking
  - compliance

maintainers:
  - name: David LECONTE
    email: david.leconte@ibm.com

dependencies: []

annotations:
  category: Database
  licenses: MIT
```

### 2.3 Values Structure

**Default values.yaml:**

```yaml
# Global settings
global:
  namespace: banking
  environment: production
  
# HCD (Cassandra)
hcd:
  enabled: true
  replicas: 3
  image:
    repository: hcd-server
    tag: "1.2.3"
    pullPolicy: IfNotPresent
  
  resources:
    requests:
      memory: "4Gi"
      cpu: "2"
    limits:
      memory: "8Gi"
      cpu: "4"
  
  storage:
    size: 100Gi
    storageClass: "fast-ssd"
  
  jvmOptions: "-Xms4G -Xmx4G"

# JanusGraph
janusgraph:
  enabled: true
  replicas: 2
  image:
    repository: janusgraph/janusgraph
    tag: "1.0.0"
    pullPolicy: IfNotPresent
  
  resources:
    requests:
      memory: "2Gi"
      cpu: "1"
    limits:
      memory: "4Gi"
      cpu: "2"
  
  storage:
    backend: "hcd"
    index: "opensearch"

# API Services
api:
  enabled: true
  replicas: 3
  image:
    repository: banking-api
    tag: "1.4.0"
    pullPolicy: IfNotPresent
  
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "1Gi"
      cpu: "1"
  
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

# Consumers
consumers:
  graph:
    enabled: true
    replicas: 2
  vector:
    enabled: true
    replicas: 2

# Monitoring
monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true

# Security
security:
  tls:
    enabled: true
  networkPolicies:
    enabled: true
```

**Environment-specific overrides (values-prod.yaml):**

```yaml
global:
  environment: production

hcd:
  replicas: 5
  resources:
    requests:
      memory: "8Gi"
      cpu: "4"
    limits:
      memory: "16Gi"
      cpu: "8"
  storage:
    size: 500Gi

janusgraph:
  replicas: 3
  resources:
    requests:
      memory: "4Gi"
      cpu: "2"
    limits:
      memory: "8Gi"
      cpu: "4"

api:
  replicas: 5
  autoscaling:
    minReplicas: 5
    maxReplicas: 20

security:
  tls:
    enabled: true
  networkPolicies:
    enabled: true
```

---

## 3. Kubernetes Resources

### 3.1 Resource Types

| Resource Type | Purpose | Count |
|---------------|---------|-------|
| **Namespace** | Logical isolation | 1 |
| **StatefulSet** | HCD (stateful storage) | 1 |
| **Deployment** | Stateless services | 6 |
| **Service** | Service discovery | 8 |
| **Ingress/Route** | External access | 3 |
| **ConfigMap** | Configuration | 5 |
| **Secret** | Sensitive data | 4 |
| **PVC** | Persistent storage | 3 |
| **NetworkPolicy** | Network isolation | 4 |
| **HPA** | Horizontal autoscaling | 2 |

### 3.2 StatefulSet (HCD)

**Purpose**: Manage HCD Cassandra cluster with stable network identities

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: hcd-server
  namespace: {{ .Values.global.namespace }}
spec:
  serviceName: hcd-service
  replicas: {{ .Values.hcd.replicas }}
  selector:
    matchLabels:
      app: hcd-server
  template:
    metadata:
      labels:
        app: hcd-server
    spec:
      containers:
      - name: hcd
        image: {{ .Values.hcd.image.repository }}:{{ .Values.hcd.image.tag }}
        ports:
        - containerPort: 9042
          name: cql
        - containerPort: 7000
          name: intra-node
        - containerPort: 7001
          name: tls-intra-node
        env:
        - name: CASSANDRA_CLUSTER_NAME
          value: "banking-cluster"
        - name: CASSANDRA_DC
          value: "dc1"
        - name: CASSANDRA_RACK
          value: "rack1"
        - name: CASSANDRA_SEEDS
          value: "hcd-server-0.hcd-service,hcd-server-1.hcd-service"
        resources:
          {{- toYaml .Values.hcd.resources | nindent 10 }}
        volumeMounts:
        - name: data
          mountPath: /var/lib/cassandra
        livenessProbe:
          exec:
            command:
            - /bin/bash
            - -c
            - nodetool status
          initialDelaySeconds: 90
          periodSeconds: 30
        readinessProbe:
          exec:
            command:
            - /bin/bash
            - -c
            - nodetool status | grep -E "^UN"
          initialDelaySeconds: 60
          periodSeconds: 10
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: {{ .Values.hcd.storage.storageClass }}
      resources:
        requests:
          storage: {{ .Values.hcd.storage.size }}
```

### 3.3 Deployment (JanusGraph)

**Purpose**: Manage JanusGraph graph database instances

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: janusgraph
  namespace: {{ .Values.global.namespace }}
spec:
  replicas: {{ .Values.janusgraph.replicas }}
  selector:
    matchLabels:
      app: janusgraph
  template:
    metadata:
      labels:
        app: janusgraph
    spec:
      containers:
      - name: janusgraph
        image: {{ .Values.janusgraph.image.repository }}:{{ .Values.janusgraph.image.tag }}
        ports:
        - containerPort: 8182
          name: gremlin
        env:
        - name: JANUSGRAPH_STORAGE_BACKEND
          value: {{ .Values.janusgraph.storage.backend }}
        - name: JANUSGRAPH_STORAGE_HOSTNAME
          value: "hcd-service"
        - name: JANUSGRAPH_INDEX_BACKEND
          value: {{ .Values.janusgraph.storage.index }}
        - name: JANUSGRAPH_INDEX_HOSTNAME
          value: "opensearch"
        resources:
          {{- toYaml .Values.janusgraph.resources | nindent 10 }}
        livenessProbe:
          httpGet:
            path: /
            port: 8182
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 8182
          initialDelaySeconds: 30
          periodSeconds: 10
```

### 3.4 Service (ClusterIP)

**Purpose**: Internal service discovery

```yaml
apiVersion: v1
kind: Service
metadata:
  name: janusgraph-service
  namespace: {{ .Values.global.namespace }}
spec:
  type: ClusterIP
  selector:
    app: janusgraph
  ports:
  - name: gremlin
    port: 8182
    targetPort: 8182
    protocol: TCP
```

### 3.5 Ingress (Standard Kubernetes)

**Purpose**: External HTTP/HTTPS access

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: banking-api-ingress
  namespace: {{ .Values.global.namespace }}
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.banking.example.com
    secretName: banking-api-tls
  rules:
  - host: api.banking.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8001
```

### 3.6 Route (OpenShift)

**Purpose**: OpenShift-specific external access

```yaml
{{- if .Values.openshift.enabled }}
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: banking-api-route
  namespace: {{ .Values.global.namespace }}
spec:
  host: api.banking.apps.openshift.example.com
  to:
    kind: Service
    name: api-service
    weight: 100
  port:
    targetPort: 8001
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
  wildcardPolicy: None
{{- end }}
```

### 3.7 HorizontalPodAutoscaler

**Purpose**: Automatic scaling based on metrics

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: {{ .Values.global.namespace }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-deployment
  minReplicas: {{ .Values.api.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.api.autoscaling.maxReplicas }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.api.autoscaling.targetCPUUtilizationPercentage }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 3.8 NetworkPolicy

**Purpose**: Network isolation and security

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: hcd-network-policy
  namespace: {{ .Values.global.namespace }}
spec:
  podSelector:
    matchLabels:
      app: hcd-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow from JanusGraph
  - from:
    - podSelector:
        matchLabels:
          app: janusgraph
    ports:
    - protocol: TCP
      port: 9042
  # Allow inter-node communication
  - from:
    - podSelector:
        matchLabels:
          app: hcd-server
    ports:
    - protocol: TCP
      port: 7000
    - protocol: TCP
      port: 7001
  egress:
  # Allow to other HCD nodes
  - to:
    - podSelector:
        matchLabels:
          app: hcd-server
    ports:
    - protocol: TCP
      port: 7000
    - protocol: TCP
      port: 7001
  # Allow DNS
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: UDP
      port: 53
```

---

## 4. ArgoCD GitOps

### 4.1 ArgoCD Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Git Repository                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  argocd/applications/                             │  │
│  │  ├── banking-dev.yaml                             │  │
│  │  ├── banking-staging.yaml                         │  │
│  │  └── banking-prod.yaml                            │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Git Sync (every 3 minutes)
                     ▼
┌─────────────────────────────────────────────────────────┐
│              ArgoCD Server                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Application Controller                           │  │
│  │  - Monitors Git repository                        │  │
│  │  - Compares desired vs actual state              │  │
│  │  - Syncs differences                              │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Apply/Update
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Kubernetes Cluster                             │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Banking Platform Resources                       │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 4.2 ArgoCD Application (Production)

**File:** `argocd/applications/banking-prod.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: banking-prod
  namespace: argocd
spec:
  project: default
  
  source:
    repoURL: https://github.com/davidleconte/hcd-janusgraph.git
    targetRevision: main
    path: helm/janusgraph-banking
    helm:
      valueFiles:
        - values.yaml
        - values-prod.yaml
      parameters:
        - name: global.environment
          value: production
  
  destination:
    server: https://kubernetes.default.svc
    namespace: banking
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  
  revisionHistoryLimit: 10
```

### 4.3 ArgoCD Sync Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Manual** | Requires manual sync | Production (with approval) |
| **Automated** | Auto-sync on Git changes | Dev, Staging |
| **Self-Heal** | Auto-correct drift | All environments |
| **Prune** | Delete removed resources | All environments |

### 4.4 ArgoCD CLI Commands

```bash
# Login to ArgoCD
argocd login argocd.example.com

# List applications
argocd app list

# Get application details
argocd app get banking-prod

# Sync application
argocd app sync banking-prod

# Rollback to previous version
argocd app rollback banking-prod

# View sync history
argocd app history banking-prod

# Set sync policy
argocd app set banking-prod --sync-policy automated

# View application logs
argocd app logs banking-prod

# Delete application
argocd app delete banking-prod
```

---

## 5. Multi-Environment Strategy

### 5.1 Environment Matrix

| Environment | Namespace | Values File | ArgoCD App | Sync Policy |
|-------------|-----------|-------------|------------|-------------|
| **Development** | banking-dev | values-dev.yaml | banking-dev.yaml | Automated |
| **Staging** | banking-staging | values-staging.yaml | banking-staging.yaml | Automated |
| **Production** | banking | values-prod.yaml | banking-prod.yaml | Manual |

### 5.2 Environment Differences

**Development:**
- Minimal resources (1 replica)
- No autoscaling
- No TLS
- No network policies
- Fast iteration

**Staging:**
- Production-like resources (3 replicas)
- Autoscaling enabled
- TLS enabled
- Network policies enabled
- Pre-production testing

**Production:**
- Full resources (5+ replicas)
- Autoscaling enabled
- TLS required
- Network policies enforced
- High availability

### 5.3 Promotion Workflow

```
┌──────────┐      ┌──────────┐      ┌──────────┐
│   Dev    │─────▶│ Staging  │─────▶│   Prod   │
└──────────┘      └──────────┘      └──────────┘
     │                 │                  │
     │                 │                  │
  Auto-sync        Auto-sync         Manual sync
  (immediate)      (immediate)       (with approval)
```

**Promotion Steps:**

1. **Dev → Staging**
   ```bash
   # Merge feature branch to staging
   git checkout staging
   git merge feature/new-feature
   git push origin staging
   
   # ArgoCD auto-syncs staging
   ```

2. **Staging → Production**
   ```bash
   # Create release tag
   git tag -a v1.4.0 -m "Release 1.4.0"
   git push origin v1.4.0
   
   # Update production ArgoCD app
   argocd app set banking-prod --revision v1.4.0
   
   # Manual sync with approval
   argocd app sync banking-prod
   ```

---

## 6. Security Architecture

### 6.1 Security Layers

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Network Policies (Pod-to-Pod)                 │
├─────────────────────────────────────────────────────────┤
│  Layer 2: RBAC (User/ServiceAccount Permissions)        │
├─────────────────────────────────────────────────────────┤
│  Layer 3: Pod Security Standards (PSS)                  │
├─────────────────────────────────────────────────────────┤
│  Layer 4: Secrets Management (Vault/Sealed Secrets)     │
├─────────────────────────────────────────────────────────┤
│  Layer 5: TLS/mTLS (Encrypted Communication)            │
└─────────────────────────────────────────────────────────┘
```

### 6.2 RBAC Configuration

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: banking-api
  namespace: banking
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: banking-api-role
  namespace: banking
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: banking-api-rolebinding
  namespace: banking
subjects:
- kind: ServiceAccount
  name: banking-api
  namespace: banking
roleRef:
  kind: Role
  name: banking-api-role
  apiGroup: rbac.authorization.k8s.io
```

### 6.3 Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: banking
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 6.4 Secrets Management

**Option 1: Kubernetes Secrets (Base64)**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: hcd-credentials
  namespace: banking
type: Opaque
data:
  username: YWRtaW4=  # base64 encoded
  password: c2VjdXJlcGFzc3dvcmQ=
```

**Option 2: Sealed Secrets (Encrypted)**
```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: hcd-credentials
  namespace: banking
spec:
  encryptedData:
    username: AgBx...encrypted...
    password: AgBy...encrypted...
```

**Option 3: External Secrets (Vault)**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: hcd-credentials
  namespace: banking
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: hcd-credentials
  data:
  - secretKey: username
    remoteRef:
      key: banking/hcd
      property: username
  - secretKey: password
    remoteRef:
      key: banking/hcd
      property: password
```

---

## 7. Deployment Workflows

### 7.1 Initial Deployment

```bash
# 1. Install Helm chart manually (first time)
helm install banking-prod ./helm/janusgraph-banking \
  --namespace banking \
  --create-namespace \
  --values helm/janusgraph-banking/values-prod.yaml

# 2. Verify deployment
kubectl get pods -n banking
kubectl get svc -n banking

# 3. Create ArgoCD application
kubectl apply -f argocd/applications/banking-prod.yaml

# 4. Verify ArgoCD sync
argocd app get banking-prod
```

### 7.2 Update Deployment

```bash
# 1. Update values or templates in Git
vim helm/janusgraph-banking/values-prod.yaml
git add .
git commit -m "Update production replicas to 5"
git push origin main

# 2. ArgoCD detects change and syncs (if automated)
# Or manually sync:
argocd app sync banking-prod

# 3. Monitor rollout
kubectl rollout status deployment/api-deployment -n banking
```

### 7.3 Rollback Deployment

```bash
# Option 1: ArgoCD rollback
argocd app rollback banking-prod

# Option 2: Helm rollback
helm rollback banking-prod -n banking

# Option 3: Git revert
git revert HEAD
git push origin main
# ArgoCD will sync the reverted state
```

---

## 8. Migration from Kustomize

### 8.1 Migration Status

**Status:** ✅ COMPLETE

**Timeline:**
- Kustomize deprecated: 2026-02-11
- Helm charts created: 2026-02-12
- ArgoCD configured: 2026-02-13
- Migration complete: 2026-02-14

### 8.2 Migration Rationale

| Aspect | Kustomize | Helm | Winner |
|--------|-----------|------|--------|
| **Templating** | Limited (patches) | Full (Go templates) | Helm |
| **Package Management** | No | Yes (charts) | Helm |
| **Versioning** | Manual | Built-in | Helm |
| **Rollback** | Manual | One command | Helm |
| **Reusability** | Low | High | Helm |
| **Community** | Good | Excellent | Helm |

### 8.3 Migration Steps Taken

1. **Created Helm chart structure**
   - Chart.yaml with metadata
   - values.yaml with defaults
   - templates/ with manifests

2. **Converted Kustomize overlays to values files**
   - dev → values-dev.yaml
   - staging → values-staging.yaml
   - prod → values-prod.yaml

3. **Templated all manifests**
   - Added Go template syntax
   - Created _helpers.tpl for common functions
   - Added conditional logic

4. **Configured ArgoCD**
   - Created Application manifests
   - Set up sync policies
   - Configured automated sync for dev/staging

5. **Archived Kustomize**
   - Moved to k8s/archive/kustomize/
   - Created migration guide
   - Updated documentation

### 8.4 Migration Guide

**See:** `docs/migrations/kustomize-to-helm-migration.md`

---

## 9. References

### 9.1 Internal Documentation

- [Deployment Architecture](deployment-architecture.md)
- [Terraform Multi-Cloud Architecture](terraform-multi-cloud-architecture.md)
- [Horizontal Scaling Guide](../operations/horizontal-scaling-guide.md)
- [Kustomize Migration Guide](../migrations/kustomize-to-helm-migration.md)

### 9.2 Helm Chart

- Chart: `helm/janusgraph-banking/`
- README: `helm/janusgraph-banking/README.md`
- Values: `helm/janusgraph-banking/values*.yaml`

### 9.3 ArgoCD Applications

- Applications: `argocd/applications/`
- Dev: `argocd/applications/banking-dev.yaml`
- Staging: `argocd/applications/banking-staging.yaml`
- Production: `argocd/applications/banking-prod.yaml`

### 9.4 External Resources

- [Helm Documentation](https://helm.sh/docs/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-19  
**Status:** Active  
**Next Review:** 2026-03-19