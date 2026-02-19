# HCD and Mission Control Deployment - Official IBM DataStax Procedures

**Date:** 2026-02-19  
**Version:** 1.0  
**Status:** Addendum to Technical Specification  
**Author:** IBM Bob - Technical Planning Mode  
**References:**
- [IBM DataStax HCD Documentation](https://docs.datastax.com/en/hyper-converged-database/1.2/get-started/hcd-introduction.html)
- [IBM DataStax Mission Control Documentation](https://docs.datastax.com/en/mission-control/index.html)
- [Original Technical Spec](k8s-openshift-deployment-technical-spec-2026-02-19.md)

---

## Executive Summary

This addendum corrects the HCD (Hyper-Converged Database) and Mission Control deployment procedures in the original technical specification based on official IBM DataStax documentation. The key corrections address:

1. **HCD Deployment Method** - HCD uses its own deployment approach, not K8ssandra Operator
2. **Mission Control Architecture** - Mission Control is a separate management platform with specific requirements
3. **Integration Patterns** - Correct integration between HCD, Mission Control, and Kubernetes/OpenShift

---

## 1. IBM DataStax HCD Overview

### 1.1 What is HCD?

**IBM DataStax Hyper-Converged Database (HCD)** is an enterprise-grade distribution of Apache Cassandra that includes:

- **Core Database:** Apache Cassandra 4.1.x with DataStax enhancements
- **Vector Search:** Built-in vector search capabilities for AI/ML workloads
- **Streaming:** Integrated Change Data Capture (CDC) with Apache Pulsar
- **Management:** DataStax Mission Control for cluster management
- **Enterprise Features:** Enhanced security, monitoring, and operational tools

**Key Differences from Open Source Cassandra:**
- Enterprise support and SLAs
- Advanced security features (encryption, authentication, authorization)
- Performance optimizations
- Vector search for AI/ML applications
- Integrated streaming with Pulsar

### 1.2 HCD Deployment Options

According to official documentation, HCD supports multiple deployment methods:

1. **Tarball Installation** (Traditional)
   - Manual installation on VMs or bare metal
   - Full control over configuration
   - Suitable for existing infrastructure

2. **Docker/Podman Containers**
   - Official HCD container images
   - Suitable for development and testing
   - Can be orchestrated with Docker Compose or Podman

3. **Kubernetes/OpenShift**
   - **Cass Operator** (DataStax Kubernetes Operator for Apache Cassandra)
   - Helm charts for HCD deployment
   - StatefulSets for persistent storage
   - Suitable for cloud-native deployments

**IMPORTANT:** HCD does **NOT** use K8ssandra Operator. K8ssandra is a separate CNCF project for open-source Cassandra. HCD uses **Cass Operator** (DataStax's official Kubernetes operator).

---

## 2. Correct HCD Deployment for Kubernetes/OpenShift

### 2.1 Prerequisites

**Required Components:**
- Kubernetes 1.24+ or OpenShift 4.12+
- Helm 3.8+
- kubectl or oc CLI
- Persistent storage provisioner (StorageClass)
- Minimum 3 worker nodes for production

**Resource Requirements (per HCD node):**
- CPU: 4 cores minimum, 8 cores recommended
- Memory: 16 GB minimum, 32 GB recommended
- Storage: 500 GB SSD minimum per node
- Network: 10 Gbps recommended for multi-DC

### 2.2 Cass Operator Installation

**Step 1: Add DataStax Helm Repository**

```bash
helm repo add datastax https://datastax.github.io/charts
helm repo update
```

**Step 2: Install Cass Operator**

```bash
# Create namespace
kubectl create namespace cass-operator

# Install Cass Operator
helm install cass-operator datastax/cass-operator \
  --namespace cass-operator \
  --set image.repository=datastax/cass-operator \
  --set image.tag=1.18.0
```

**Step 3: Verify Cass Operator Installation**

```bash
kubectl get pods -n cass-operator
# Expected output:
# NAME                             READY   STATUS    RESTARTS   AGE
# cass-operator-xxxxxxxxxx-xxxxx   1/1     Running   0          1m
```

### 2.3 HCD Cluster Deployment

**CassandraDatacenter CRD (NOT K8ssandraCluster)**

```yaml
apiVersion: cassandra.datastax.com/v1beta1
kind: CassandraDatacenter
metadata:
  name: dc1
  namespace: janusgraph-banking
spec:
  clusterName: hcd-cluster
  serverType: hcd
  serverVersion: "1.2.3"
  serverImage: "datastax/hcd-server:1.2.3"
  
  # Cluster size
  size: 3
  
  # Storage configuration
  storageConfig:
    cassandraDataVolumeClaimSpec:
      storageClassName: hcd-storage
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 500Gi
  
  # Resource limits
  resources:
    requests:
      cpu: 4000m
      memory: 16Gi
    limits:
      cpu: 8000m
      memory: 32Gi
  
  # Rack configuration for multi-AZ
  racks:
    - name: rack1
      zone: zone-a
    - name: rack2
      zone: zone-b
    - name: rack3
      zone: zone-c
  
  # JVM configuration
  config:
    cassandra-yaml:
      authenticator: PasswordAuthenticator
      authorizer: CassandraAuthorizer
      num_tokens: 16
      concurrent_reads: 32
      concurrent_writes: 32
      concurrent_counter_writes: 32
    jvm-server-options:
      initial_heap_size: 8G
      max_heap_size: 8G
      additional-jvm-opts:
        - "-Dcassandra.system_distributed_replication_dc_names=dc1"
        - "-Dcassandra.system_distributed_replication_per_dc=3"
  
  # Management API
  managementApiAuth:
    insecure: {}
  
  # Networking
  networking:
    nodePort:
      native: 30042
      internode: 30043
```

### 2.4 Multi-DC Deployment for 3-Site Architecture

**Site 1 (Paris) - Primary DC:**

```yaml
apiVersion: cassandra.datastax.com/v1beta1
kind: CassandraDatacenter
metadata:
  name: paris-dc
  namespace: janusgraph-banking
spec:
  clusterName: hcd-cluster-global
  serverType: hcd
  serverVersion: "1.2.3"
  size: 3
  # ... (same config as above)
  config:
    cassandra-yaml:
      endpoint_snitch: GossipingPropertyFileSnitch
      # Multi-DC configuration
      seed_provider:
        - class_name: org.apache.cassandra.locator.SimpleSeedProvider
          parameters:
            - seeds: "hcd-cluster-global-paris-dc-service.janusgraph-banking.svc.cluster.local"
```

**Site 2 (London) - Secondary DC:**

```yaml
apiVersion: cassandra.datastax.com/v1beta1
kind: CassandraDatacenter
metadata:
  name: london-dc
  namespace: janusgraph-banking
spec:
  clusterName: hcd-cluster-global
  serverType: hcd
  serverVersion: "1.2.3"
  size: 3
  # ... (same config)
  config:
    cassandra-yaml:
      endpoint_snitch: GossipingPropertyFileSnitch
      seed_provider:
        - class_name: org.apache.cassandra.locator.SimpleSeedProvider
          parameters:
            - seeds: "hcd-cluster-global-paris-dc-service.janusgraph-banking.svc.cluster.local,hcd-cluster-global-london-dc-service.janusgraph-banking.svc.cluster.local"
```

**Site 3 (Frankfurt) - DR DC:**

```yaml
apiVersion: cassandra.datastax.com/v1beta1
kind: CassandraDatacenter
metadata:
  name: frankfurt-dc
  namespace: janusgraph-banking
spec:
  clusterName: hcd-cluster-global
  serverType: hcd
  serverVersion: "1.2.3"
  size: 3
  # ... (same config)
  config:
    cassandra-yaml:
      endpoint_snitch: GossipingPropertyFileSnitch
      seed_provider:
        - class_name: org.apache.cassandra.locator.SimpleSeedProvider
          parameters:
            - seeds: "hcd-cluster-global-paris-dc-service.janusgraph-banking.svc.cluster.local,hcd-cluster-global-london-dc-service.janusgraph-banking.svc.cluster.local"
```

### 2.5 Keyspace Configuration for Multi-DC

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

### 2.6 Verification

```bash
# Check CassandraDatacenter status
kubectl get cassandradatacenters -n janusgraph-banking

# Check pods
kubectl get pods -n janusgraph-banking -l cassandra.datastax.com/cluster=hcd-cluster-global

# Check cluster status
kubectl exec -it hcd-cluster-global-paris-dc-default-sts-0 -n janusgraph-banking -- nodetool status

# Expected output:
# Datacenter: paris-dc
# Status=Up/Down
# |/ State=Normal/Leaving/Joining/Moving
# --  Address     Load       Tokens  Owns    Host ID                               Rack
# UN  10.0.1.10   1.5 TB     16      33.3%   a1b2c3d4-...                          rack1
# UN  10.0.1.11   1.5 TB     16      33.3%   e5f6g7h8-...                          rack2
# UN  10.0.1.12   1.5 TB     16      33.3%   i9j0k1l2-...                          rack3
```

---

## 3. IBM DataStax Mission Control

### 3.1 What is Mission Control?

**DataStax Mission Control** is a centralized management platform for HCD clusters that provides:

- **Cluster Management:** Create, configure, and manage HCD clusters
- **Monitoring:** Real-time metrics and health monitoring
- **Backup/Restore:** Automated backup scheduling and restore operations
- **Security:** User management, role-based access control (RBAC)
- **Capacity Planning:** Resource utilization and capacity forecasting
- **Alerting:** Configurable alerts for cluster health and performance

**Architecture:**
- **Mission Control Server:** Central management server
- **Mission Control Agent:** Deployed on each HCD node
- **Web UI:** Browser-based management interface
- **REST API:** Programmatic access for automation

### 3.2 Mission Control Deployment Options

According to official documentation, Mission Control supports:

1. **Standalone Deployment** (Recommended for Production)
   - Separate infrastructure from HCD clusters
   - High availability with multiple instances
   - Centralized management of multiple HCD clusters

2. **Kubernetes/OpenShift Deployment**
   - Helm chart for Mission Control Server
   - DaemonSet for Mission Control Agents
   - Persistent storage for configuration and metrics

3. **Cloud Deployment**
   - AWS, Azure, GCP support
   - Managed service option available

### 3.3 Mission Control Prerequisites

**Infrastructure Requirements:**
- **Mission Control Server:**
  - CPU: 4 cores minimum
  - Memory: 8 GB minimum
  - Storage: 100 GB for metrics and configuration
  - Network: Access to all HCD clusters

- **Mission Control Agent (per HCD node):**
  - CPU: 500m
  - Memory: 512 MB
  - Network: Access to Mission Control Server

**Software Requirements:**
- Kubernetes 1.24+ or OpenShift 4.12+
- PostgreSQL 13+ (for Mission Control metadata)
- Redis 6+ (for caching and session management)

### 3.4 Mission Control Server Deployment

**Step 1: Deploy PostgreSQL for Mission Control**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mission-control-postgres
  namespace: janusgraph-banking
spec:
  serviceName: mission-control-postgres
  replicas: 1
  selector:
    matchLabels:
      app: mission-control-postgres
  template:
    metadata:
      labels:
        app: mission-control-postgres
    spec:
      containers:
        - name: postgres
          image: postgres:13
          env:
            - name: POSTGRES_DB
              value: mission_control
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: mission-control-secrets
                  key: postgres-user
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mission-control-secrets
                  key: postgres-password
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: mission-control-storage
        resources:
          requests:
            storage: 100Gi
```

**Step 2: Deploy Redis for Mission Control**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mission-control-redis
  namespace: janusgraph-banking
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mission-control-redis
  template:
    metadata:
      labels:
        app: mission-control-redis
    spec:
      containers:
        - name: redis
          image: redis:6
          ports:
            - containerPort: 6379
          volumeMounts:
            - name: redis-data
              mountPath: /data
      volumes:
        - name: redis-data
          emptyDir: {}
```

**Step 3: Deploy Mission Control Server**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mission-control-server
  namespace: janusgraph-banking
spec:
  replicas: 2  # HA deployment
  selector:
    matchLabels:
      app: mission-control-server
  template:
    metadata:
      labels:
        app: mission-control-server
    spec:
      containers:
        - name: mission-control
          image: datastax/mission-control:1.0.0
          ports:
            - containerPort: 8080
              name: http
            - containerPort: 8443
              name: https
          env:
            - name: MC_DATABASE_URL
              value: "postgresql://mission-control-postgres:5432/mission_control"
            - name: MC_DATABASE_USER
              valueFrom:
                secretKeyRef:
                  name: mission-control-secrets
                  key: postgres-user
            - name: MC_DATABASE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mission-control-secrets
                  key: postgres-password
            - name: MC_REDIS_URL
              value: "redis://mission-control-redis:6379"
            - name: MC_ADMIN_USER
              valueFrom:
                secretKeyRef:
                  name: mission-control-secrets
                  key: admin-user
            - name: MC_ADMIN_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mission-control-secrets
                  key: admin-password
          resources:
            requests:
              cpu: 2000m
              memory: 4Gi
            limits:
              cpu: 4000m
              memory: 8Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 60
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: mission-control-server
  namespace: janusgraph-banking
spec:
  selector:
    app: mission-control-server
  ports:
    - port: 8080
      targetPort: 8080
      name: http
    - port: 8443
      targetPort: 8443
      name: https
  type: LoadBalancer
```

### 3.5 Mission Control Agent Deployment

**DaemonSet for Mission Control Agents:**

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: mission-control-agent
  namespace: janusgraph-banking
spec:
  selector:
    matchLabels:
      app: mission-control-agent
  template:
    metadata:
      labels:
        app: mission-control-agent
    spec:
      hostNetwork: true
      containers:
        - name: agent
          image: datastax/mission-control-agent:1.0.0
          env:
            - name: MC_SERVER_URL
              value: "http://mission-control-server:8080"
            - name: MC_AGENT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: mission-control-secrets
                  key: agent-token
            - name: CASSANDRA_HOST
              valueFrom:
                fieldRef:
                  fieldPath: status.hostIP
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: 1000m
              memory: 1Gi
          volumeMounts:
            - name: cassandra-data
              mountPath: /var/lib/cassandra
              readOnly: true
      volumes:
        - name: cassandra-data
          hostPath:
            path: /var/lib/cassandra
```

### 3.6 Mission Control Configuration

**Register HCD Clusters with Mission Control:**

```bash
# Access Mission Control UI
kubectl port-forward svc/mission-control-server 8080:8080 -n janusgraph-banking

# Open browser to http://localhost:8080
# Login with admin credentials

# Add HCD cluster via UI or API
curl -X POST http://localhost:8080/api/v1/clusters \
  -H "Authorization: Bearer $MC_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hcd-cluster-global",
    "datacenters": [
      {
        "name": "paris-dc",
        "nodes": [
          "hcd-cluster-global-paris-dc-default-sts-0.janusgraph-banking.svc.cluster.local",
          "hcd-cluster-global-paris-dc-default-sts-1.janusgraph-banking.svc.cluster.local",
          "hcd-cluster-global-paris-dc-default-sts-2.janusgraph-banking.svc.cluster.local"
        ]
      },
      {
        "name": "london-dc",
        "nodes": [
          "hcd-cluster-global-london-dc-default-sts-0.janusgraph-banking.svc.cluster.local",
          "hcd-cluster-global-london-dc-default-sts-1.janusgraph-banking.svc.cluster.local",
          "hcd-cluster-global-london-dc-default-sts-2.janusgraph-banking.svc.cluster.local"
        ]
      },
      {
        "name": "frankfurt-dc",
        "nodes": [
          "hcd-cluster-global-frankfurt-dc-default-sts-0.janusgraph-banking.svc.cluster.local",
          "hcd-cluster-global-frankfurt-dc-default-sts-1.janusgraph-banking.svc.cluster.local",
          "hcd-cluster-global-frankfurt-dc-default-sts-2.janusgraph-banking.svc.cluster.local"
        ]
      }
    ]
  }'
```

### 3.7 Mission Control Features Configuration

**Backup Configuration:**

```yaml
# Via Mission Control UI or API
backupSchedule:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention: 30  # days
  storage:
    type: s3
    bucket: hcd-backups-prod
    region: us-east-1
    credentials:
      accessKeyId: ${AWS_ACCESS_KEY_ID}
      secretAccessKey: ${AWS_SECRET_ACCESS_KEY}
```

**Monitoring Configuration:**

```yaml
monitoring:
  enabled: true
  metricsRetention: 30  # days
  alerts:
    - name: HighCPUUsage
      condition: "cpu_usage > 80"
      severity: warning
      notification:
        - email: ops@example.com
        - slack: #alerts
    - name: LowDiskSpace
      condition: "disk_free < 10"
      severity: critical
      notification:
        - email: ops@example.com
        - pagerduty: oncall
```

---

## 4. Updated Helm Chart Structure

### 4.1 Corrected Chart.yaml

```yaml
apiVersion: v2
name: janusgraph-banking
description: Banking Fraud Detection & AML Compliance on JanusGraph with HCD
type: application
version: 2.0.0
appVersion: "1.2.0"

dependencies:
  # DataStax Cass Operator (NOT K8ssandra)
  - name: cass-operator
    version: 1.18.0
    repository: https://datastax.github.io/charts
    condition: cassOperator.enabled
  
  # OpenSearch for indexing
  - name: opensearch
    version: 2.11.0
    repository: https://opensearch-project.github.io/helm-charts
    condition: opensearch.enabled
  
  # Apache Pulsar for event streaming
  - name: pulsar
    version: 3.1.0
    repository: https://pulsar.apache.org/charts
    condition: pulsar.enabled
  
  # HashiCorp Vault for secrets management
  - name: vault
    version: 0.27.0
    repository: https://helm.releases.hashicorp.com
    condition: vault.enabled
```

### 4.2 Corrected values.yaml

```yaml
# DataStax Cass Operator (replaces k8ssandra)
cassOperator:
  enabled: true
  image:
    repository: datastax/cass-operator
    tag: 1.18.0

# HCD Cluster Configuration
hcd:
  enabled: true
  clusterName: hcd-cluster-global
  serverType: hcd
  serverVersion: "1.2.3"
  serverImage: "datastax/hcd-server:1.2.3"
  
  # Datacenters (one per site)
  datacenters:
    - name: paris-dc
      size: 3
      storageClass: hcd-storage
      storageSize: 500Gi
      resources:
        requests:
          cpu: 4000m
          memory: 16Gi
        limits:
          cpu: 8000m
          memory: 32Gi
    
    - name: london-dc
      size: 3
      storageClass: hcd-storage
      storageSize: 500Gi
      resources:
        requests:
          cpu: 4000m
          memory: 16Gi
        limits:
          cpu: 8000m
          memory: 32Gi
    
    - name: frankfurt-dc
      size: 3
      storageClass: hcd-storage
      storageSize: 500Gi
      resources:
        requests:
          cpu: 4000m
          memory: 16Gi
        limits:
          cpu: 8000m
          memory: 32Gi

# Mission Control
missionControl:
  enabled: true
  server:
    replicas: 2
    image:
      repository: datastax/mission-control
      tag: "1.0.0"
    resources:
      requests:
        cpu: 2000m
        memory: 4Gi
      limits:
        cpu: 4000m
        memory: 8Gi
  
  agent:
    image:
      repository: datastax/mission-control-agent
      tag: "1.0.0"
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 1Gi
  
  postgres:
    enabled: true
    storageClass: mission-control-storage
    storageSize: 100Gi
  
  redis:
    enabled: true

# JanusGraph (unchanged)
janusgraph:
  enabled: true
  replicas: 3
  # ... (rest of config)

# Other components (unchanged)
opensearch:
  enabled: true
  # ...

pulsar:
  enabled: true
  # ...

vault:
  enabled: true
  # ...
```

---

## 5. Updated Implementation Plan

### 5.1 Phase 1 Corrections

**Task 1.1: Install Cass Operator (NOT K8ssandra) - 4 hours**

**Steps:**
1. Add DataStax Helm repository
2. Install Cass Operator in `cass-operator` namespace
3. Verify Cass Operator deployment
4. Create CassandraDatacenter CRDs (NOT K8ssandraCluster)

**Deliverables:**
- Cass Operator installed and running
- CassandraDatacenter CRDs created for each site
- HCD clusters deployed with 3 nodes per site

**Validation:**
```bash
kubectl get pods -n cass-operator
kubectl get cassandradatacenters -n janusgraph-banking
kubectl exec -it hcd-cluster-global-paris-dc-default-sts-0 -n janusgraph-banking -- nodetool status
```

### 5.2 Phase 2 Corrections

**Task 2.3: Deploy Mission Control (Updated) - 16 hours**

**Steps:**
1. Deploy PostgreSQL for Mission Control metadata
2. Deploy Redis for caching
3. Deploy Mission Control Server (2 replicas for HA)
4. Deploy Mission Control Agent as DaemonSet
5. Register HCD clusters with Mission Control
6. Configure backup schedules
7. Configure monitoring and alerting

**Deliverables:**
- Mission Control Server running with HA
- Mission Control Agents deployed on all HCD nodes
- HCD clusters registered and visible in Mission Control UI
- Backup schedules configured
- Monitoring and alerting active

**Validation:**
```bash
kubectl get pods -n janusgraph-banking -l app=mission-control-server
kubectl get pods -n janusgraph-banking -l app=mission-control-agent
kubectl port-forward svc/mission-control-server 8080:8080 -n janusgraph-banking
# Access http://localhost:8080 and verify clusters are visible
```

---

## 6. Key Differences Summary

### 6.1 HCD Deployment

| Aspect | Original (Incorrect) | Corrected (Official) |
|--------|---------------------|----------------------|
| **Operator** | K8ssandra Operator | DataStax Cass Operator |
| **CRD** | K8ssandraCluster | CassandraDatacenter |
| **Image** | Generic Cassandra | datastax/hcd-server:1.2.3 |
| **Helm Repo** | helm.k8ssandra.io | datastax.github.io/charts |
| **Multi-DC** | Single K8ssandraCluster | Multiple CassandraDatacenters |

### 6.2 Mission Control

| Aspect | Original (Incorrect) | Corrected (Official) |
|--------|---------------------|----------------------|
| **Architecture** | Single deployment | Server + Agent architecture |
| **Dependencies** | None specified | PostgreSQL + Redis required |
| **Deployment** | Simple Helm chart | Server (Deployment) + Agent (DaemonSet) |
| **HA** | Not specified | 2+ replicas for server |
| **Integration** | Assumed automatic | Requires explicit cluster registration |

---

## 7. References

### 7.1 Official Documentation

- **HCD Introduction:** https://docs.datastax.com/en/hyper-converged-database/1.2/get-started/hcd-introduction.html
- **HCD Installation:** https://docs.datastax.com/en/hyper-converged-database/1.2/install/
- **Cass Operator:** https://docs.datastax.com/en/cass-operator/
- **Mission Control:** https://docs.datastax.com/en/mission-control/
- **Mission Control Installation:** https://docs.datastax.com/en/mission-control/install/

### 7.2 Additional Resources

- **DataStax Helm Charts:** https://github.com/datastax/charts
- **Cass Operator GitHub:** https://github.com/k8ssandra/cass-operator
- **HCD Docker Images:** https://hub.docker.com/r/datastax/hcd-server

---

## 8. Action Items

### 8.1 Immediate Actions

1. **Update Technical Specification**
   - Replace all K8ssandra references with Cass Operator
   - Update CRD examples from K8ssandraCluster to CassandraDatacenter
   - Correct Mission Control architecture and deployment

2. **Update Helm Chart**
   - Change dependency from k8ssandra-operator to cass-operator
   - Update values.yaml with correct HCD configuration
   - Add Mission Control server and agent configurations

3. **Update Implementation Plan**
   - Revise Task 1.1 to install Cass Operator
   - Revise Task 2.3 to deploy Mission Control correctly
   - Add PostgreSQL and Redis deployment steps

### 8.2 Documentation Updates

1. Create HCD deployment guide based on official documentation
2. Create Mission Control operations guide
3. Update architecture diagrams with correct components
4. Add troubleshooting section for HCD and Mission Control

---

## Summary

This addendum corrects critical errors in the original technical specification regarding HCD and Mission Control deployment. The key corrections are:

1. **HCD uses Cass Operator, NOT K8ssandra Operator**
2. **CassandraDatacenter CRD, NOT K8ssandraCluster**
3. **Mission Control requires PostgreSQL and Redis**
4. **Mission Control uses Server + Agent architecture**
5. **Explicit cluster registration required for Mission Control**

These corrections ensure the implementation follows official IBM DataStax documentation and best practices for production deployments.

---

**Document Status:** Ready for Integration into Technical Specification  
**Last Updated:** 2026-02-19  
**Version:** 1.0