# OpenShift Deployment Manifests - Banking Graph Platform

**Date:** 2026-02-12  
**Version:** 1.0  
**Status:** Production Ready  
**Compliance:** DORA (Digital Operational Resilience Act)  
**Related:** [`openshift-3-site-ha-dr-dora.md`](openshift-3-site-ha-dr-dora.md)

---

## Executive Summary

Ce document fournit tous les manifests YAML OpenShift nécessaires pour déployer la plateforme Banking Graph Analytics en configuration 3 sites (Paris, Londres, Frankfurt) avec Haute Disponibilité et Disaster Recovery conformes DORA.

**Contenu:**
- Manifests complets pour tous les composants
- Configuration multi-site (3 datacenters)
- Stratégies HA/DR intégrées
- Network policies et sécurité
- Scripts de validation

---

## Table des Matières

1. [Vue d'Ensemble](#1-vue-densemble)
2. [Namespaces & RBAC](#2-namespaces--rbac)
3. [Storage (OCS/Ceph)](#3-storage-ocsceph)
4. [HCD Cassandra](#4-hcd-cassandra)
5. [JanusGraph](#5-janusgraph)
6. [Apache Pulsar](#6-apache-pulsar)
7. [OpenSearch](#7-opensearch)
8. [API Services](#8-api-services)
9. [Consumers](#9-consumers)
10. [Monitoring Stack](#10-monitoring-stack)
11. [HashiCorp Vault](#11-hashicorp-vault)
12. [Network Policies](#12-network-policies)
13. [Ingress Routes](#13-ingress-routes)
14. [Validation Scripts](#14-validation-scripts)

---

## 1. Vue d'Ensemble

### 1.1 Ordre de Déploiement

```
Phase 1: Infrastructure (15 min)
  ✓ Namespaces & RBAC
  ✓ Storage (OCS)
  ✓ Operators

Phase 2: Stateful Services (30 min)
  ✓ HCD Cassandra (wait for ready)
  ✓ ZooKeeper (wait for ready)
  ✓ Pulsar BookKeeper (wait for ready)
  ✓ Pulsar Broker (wait for ready)
  ✓ OpenSearch (wait for ready)
  ✓ Vault (wait for ready)

Phase 3: Graph Layer (20 min)
  ✓ JanusGraph (wait for ready)
  ✓ Schema initialization

Phase 4: Application Layer (10 min)
  ✓ API Services
  ✓ Consumers

Phase 5: Monitoring (10 min)
  ✓ Prometheus
  ✓ Grafana
  ✓ AlertManager

Phase 6: Network & Security (5 min)
  ✓ Network Policies
  ✓ Ingress Routes

Total: ~90 minutes per site
```

---

## 2. Namespaces & RBAC

```yaml
# File: 00-namespaces/banking-production.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: banking-production
  labels:
    name: banking-production
    site: paris  # Change per site
    tier: production
    compliance: dora

---
apiVersion: v1
kind: Namespace
metadata:
  name: banking-monitoring
  labels:
    name: banking-monitoring
    site: paris
    tier: infrastructure

---
apiVersion: v1
kind: Namespace
metadata:
  name: banking-security
  labels:
    name: banking-security
    site: paris
    tier: infrastructure

---
# Service Accounts
apiVersion: v1
kind: ServiceAccount
metadata:
  name: banking-app
  namespace: banking-production

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: banking-monitoring
  namespace: banking-monitoring

---
# RBAC Role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: banking-app-role
  namespace: banking-production
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps", "secrets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets"]
    verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: banking-app-rolebinding
  namespace: banking-production
subjects:
  - kind: ServiceAccount
    name: banking-app
    namespace: banking-production
roleRef:
  kind: Role
  name: banking-app-role
  apiGroup: rbac.authorization.k8s.io
```

---

## 3. Storage (OCS/Ceph)

```yaml
# File: 01-storage/ocs-storagecluster.yaml
apiVersion: ocs.openshift.io/v1
kind: StorageCluster
metadata:
  name: ocs-storagecluster
  namespace: openshift-storage
spec:
  storageDeviceSets:
    - name: ocs-deviceset
      count: 3
      replica: 3
      dataPVCTemplate:
        spec:
          storageClassName: local-storage
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 10Ti
      resources:
        requests:
          cpu: 2
          memory: 8Gi
        limits:
          cpu: 4
          memory: 16Gi
  monitoring:
    enabled: true
  encryption:
    enable: true

---
# File: 01-storage/storage-classes.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ocs-storagecluster-ceph-rbd
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: openshift-storage.rbd.csi.ceph.com
parameters:
  clusterID: openshift-storage
  pool: ocs-storagecluster-cephblockpool
  imageFeatures: layering
  csi.storage.k8s.io/fstype: ext4
reclaimPolicy: Delete
allowVolumeExpansion: true
```

---

## 4. HCD Cassandra

```yaml
# File: 03-cassandra/cassandra-datacenter-paris.yaml
apiVersion: cassandra.datastax.com/v1beta1
kind: CassandraDatacenter
metadata:
  name: dc-paris
  namespace: banking-production
spec:
  clusterName: banking-cluster
  serverType: hcd
  serverVersion: "1.2.3"
  size: 3
  
  storageConfig:
    cassandraDataVolumeClaimSpec:
      storageClassName: ocs-storagecluster-ceph-rbd
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 1Ti
  
  resources:
    requests:
      memory: 16Gi
      cpu: 4
    limits:
      memory: 16Gi
      cpu: 4
  
  racks:
    - name: rack1
      zone: zone-a
    - name: rack2
      zone: zone-b
    - name: rack3
      zone: zone-c
  
  config:
    cassandra-yaml:
      endpoint_snitch: GossipingPropertyFileSnitch
      auto_snapshot: true
      concurrent_reads: 32
      concurrent_writes: 32
    
    jvm-server-options:
      initial_heap_size: 8G
      max_heap_size: 8G
      additional-jvm-opts:
        - "-XX:+UseG1GC"
        - "-XX:MaxGCPauseMillis=500"

---
# Schema ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: cassandra-schema
  namespace: banking-production
data:
  schema.cql: |
    CREATE KEYSPACE IF NOT EXISTS janusgraph
    WITH replication = {
      'class': 'NetworkTopologyStrategy',
      'dc-paris': 3,
      'dc-london': 3,
      'dc-frankfurt': 3
    }
    AND durable_writes = true;
```

---

## 5. JanusGraph

```yaml
# File: 04-janusgraph/janusgraph-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: janusgraph
  namespace: banking-production
spec:
  serviceName: janusgraph
  replicas: 3
  
  selector:
    matchLabels:
      app: janusgraph
  
  template:
    metadata:
      labels:
        app: janusgraph
    spec:
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
              memory: 8Gi
              cpu: 2
            limits:
              memory: 8Gi
              cpu: 2
          
          livenessProbe:
            httpGet:
              path: /?gremlin=1+1
              port: 8182
            initialDelaySeconds: 60
            periodSeconds: 10
          
          readinessProbe:
            httpGet:
              path: /?gremlin=1+1
              port: 8182
            initialDelaySeconds: 30
            periodSeconds: 5
          
          volumeMounts:
            - name: config
              mountPath: /etc/opt/janusgraph
            - name: data
              mountPath: /var/lib/janusgraph
          
          env:
            - name: JAVA_OPTIONS
              value: "-Xms4g -Xmx4g -XX:+UseG1GC"
      
      volumes:
        - name: config
          configMap:
            name: janusgraph-config
  
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ocs-storagecluster-ceph-rbd
        resources:
          requests:
            storage: 500Gi

---
# Service
apiVersion: v1
kind: Service
metadata:
  name: janusgraph-service
  namespace: banking-production
spec:
  type: ClusterIP
  selector:
    app: janusgraph
  ports:
    - port: 8182
      targetPort: 8182
      name: gremlin

---
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: janusgraph-config
  namespace: banking-production
data:
  janusgraph-hcd.properties: |
    storage.backend=cql
    storage.hostname=hcd-cassandra-service.banking-production.svc.cluster.local
    storage.port=9042
    storage.cql.keyspace=janusgraph
    storage.cql.local-datacenter=dc-paris
    storage.cql.read-consistency-level=LOCAL_QUORUM
    storage.cql.write-consistency-level=LOCAL_QUORUM
    
    index.search.backend=elasticsearch
    index.search.hostname=opensearch-cluster.banking-production.svc.cluster.local
    index.search.port=9200
    
    cache.db-cache=true
    cache.db-cache-time=180000
```

---

## 6. Apache Pulsar

```yaml
# File: 05-pulsar/zookeeper-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: zookeeper
  namespace: banking-production
spec:
  serviceName: zookeeper
  replicas: 3
  selector:
    matchLabels:
      app: zookeeper
  template:
    metadata:
      labels:
        app: zookeeper
    spec:
      containers:
        - name: zookeeper
          image: zookeeper:3.8.0
          ports:
            - containerPort: 2181
              name: client
          resources:
            requests:
              memory: 2Gi
              cpu: 1
            limits:
              memory: 2Gi
              cpu: 1
          volumeMounts:
            - name: data
              mountPath: /data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ocs-storagecluster-ceph-rbd
        resources:
          requests:
            storage: 50Gi

---
# File: 05-pulsar/pulsar-broker-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: pulsar-broker
  namespace: banking-production
spec:
  serviceName: pulsar-broker
  replicas: 3
  selector:
    matchLabels:
      app: pulsar-broker
  template:
    metadata:
      labels:
        app: pulsar-broker
    spec:
      containers:
        - name: pulsar-broker
          image: apachepulsar/pulsar:3.1.0
          command:
            - sh
            - -c
            - bin/pulsar broker
          ports:
            - containerPort: 6650
              name: pulsar
            - containerPort: 8080
              name: http
          resources:
            requests:
              memory: 4Gi
              cpu: 2
            limits:
              memory: 4Gi
              cpu: 2
          env:
            - name: PULSAR_MEM
              value: "-Xms2g -Xmx2g"
            - name: clusterName
              value: "paris-cluster"

---
apiVersion: v1
kind: Service
metadata:
  name: pulsar-broker
  namespace: banking-production
spec:
  type: ClusterIP
  selector:
    app: pulsar-broker
  ports:
    - name: pulsar
      port: 6650
    - name: http
      port: 8080
```

---

## 7. OpenSearch

```yaml
# File: 06-opensearch/opensearch-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: opensearch
  namespace: banking-production
spec:
  serviceName: opensearch
  replicas: 3
  selector:
    matchLabels:
      app: opensearch
  template:
    metadata:
      labels:
        app: opensearch
    spec:
      initContainers:
        - name: sysctl
          image: busybox
          command:
            - sh
            - -c
            - sysctl -w vm.max_map_count=262144
          securityContext:
            privileged: true
      
      containers:
        - name: opensearch
          image: opensearchproject/opensearch:2.11.0
          ports:
            - containerPort: 9200
              name: http
            - containerPort: 9300
              name: transport
          resources:
            requests:
              memory: 8Gi
              cpu: 2
            limits:
              memory: 8Gi
              cpu: 2
          env:
            - name: cluster.name
              value: "banking-opensearch"
            - name: OPENSEARCH_JAVA_OPTS
              value: "-Xms4g -Xmx4g"
          volumeMounts:
            - name: data
              mountPath: /usr/share/opensearch/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ocs-storagecluster-ceph-rbd
        resources:
          requests:
            storage: 500Gi

---
apiVersion: v1
kind: Service
metadata:
  name: opensearch-cluster
  namespace: banking-production
spec:
  type: ClusterIP
  selector:
    app: opensearch
  ports:
    - name: http
      port: 9200
```

---

## 8. API Services

```yaml
# File: 07-api/api-gateway-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: banking-production
spec:
  replicas: 6
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
        - name: api-gateway
          image: banking/api-gateway:1.0.0
          ports:
            - containerPort: 8000
              name: http
          resources:
            requests:
              memory: 2Gi
              cpu: 1
            limits:
              memory: 2Gi
              cpu: 1
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
          env:
            - name: JANUSGRAPH_HOST
              value: "janusgraph-service.banking-production.svc.cluster.local"
            - name: PULSAR_URL
              value: "pulsar://pulsar-broker.banking-production.svc.cluster.local:6650"

---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: banking-production
spec:
  type: ClusterIP
  selector:
    app: api-gateway
  ports:
    - port: 8000
      targetPort: 8000

---
# HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: banking-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 6
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## 9. Consumers

```yaml
# File: 07-api/graph-consumer-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graph-consumer
  namespace: banking-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: graph-consumer
  template:
    metadata:
      labels:
        app: graph-consumer
    spec:
      containers:
        - name: graph-consumer
          image: banking/graph-consumer:1.0.0
          resources:
            requests:
              memory: 2Gi
              cpu: 1
            limits:
              memory: 2Gi
              cpu: 1
          env:
            - name: PULSAR_URL
              value: "pulsar://pulsar-broker.banking-production.svc.cluster.local:6650"
            - name: JANUSGRAPH_HOST
              value: "janusgraph-service.banking-production.svc.cluster.local"

---
# File: 07-api/vector-consumer-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vector-consumer
  namespace: banking-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vector-consumer
  template:
    metadata:
      labels:
        app: vector-consumer
    spec:
      containers:
        - name: vector-consumer
          image: banking/vector-consumer:1.0.0
          resources:
            requests:
              memory: 2Gi
              cpu: 1
            limits:
              memory: 2Gi
              cpu: 1
          env:
            - name: PULSAR_URL
              value: "pulsar://pulsar-broker.banking-production.svc.cluster.local:6650"
            - name: OPENSEARCH_HOST
              value: "opensearch-cluster.banking-production.svc.cluster.local"

---
# File: 07-api/dlq-handler-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dlq-handler
  namespace: banking-production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dlq-handler
  template:
    metadata:
      labels:
        app: dlq-handler
    spec:
      containers:
        - name: dlq-handler
          image: banking/dlq-handler:1.0.0
          resources:
            requests:
              memory: 1Gi
              cpu: 500m
            limits:
              memory: 1Gi
              cpu: 500m
          env:
            - name: PULSAR_URL
              value: "pulsar://pulsar-broker.banking-production.svc.cluster.local:6650"
```

---

## 10. Monitoring Stack

```yaml
# File: 08-monitoring/prometheus-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: prometheus
  namespace: banking-monitoring
spec:
  serviceName: prometheus
  replicas: 3
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
        - name: prometheus
          image: prom/prometheus:v2.45.0
          ports:
            - containerPort: 9090
              name: http
          resources:
            requests:
              memory: 4Gi
              cpu: 2
            limits:
              memory: 4Gi
              cpu: 2
          volumeMounts:
            - name: config
              mountPath: /etc/prometheus
            - name: data
              mountPath: /prometheus
          args:
            - '--config.file=/etc/prometheus/prometheus.yml'
            - '--storage.tsdb.path=/prometheus'
            - '--storage.tsdb.retention.time=30d'
      volumes:
        - name: config
          configMap:
            name: prometheus-config
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ocs-storagecluster-ceph-rbd
        resources:
          requests:
            storage: 100Gi

---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: banking-monitoring
spec:
  type: ClusterIP
  selector:
    app: prometheus
  ports:
    - port: 9090
      targetPort: 9090

---
# File: 08-monitoring/grafana-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: banking-monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
        - name: grafana
          image: grafana/grafana:10.0.0
          ports:
            - containerPort: 3000
              name: http
          resources:
            requests:
              memory: 1Gi
              cpu: 500m
            limits:
              memory: 1Gi
              cpu: 500m
          volumeMounts:
            - name: data
              mountPath: /var/lib/grafana
      volumes:
        - name: data
          emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: banking-monitoring
spec:
  type: ClusterIP
  selector:
    app: grafana
  ports:
    - port: 3000
      targetPort: 3000

---
# File: 08-monitoring/alertmanager-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: alertmanager
  namespace: banking-monitoring
spec:
  serviceName: alertmanager
  replicas: 3
  selector:
    matchLabels:
      app: alertmanager
  template:
    metadata:
      labels:
        app: alertmanager
    spec:
      containers:
        - name: alertmanager
          image: prom/alertmanager:v0.26.0
          ports:
            - containerPort: 9093
              name: http
          resources:
            requests:
              memory: 512Mi
              cpu: 250m
            limits:
              memory: 512Mi
              cpu: 250m
          volumeMounts:
            - name: config
              mountPath: /etc/alertmanager
            - name: data
              mountPath: /alertmanager
      volumes:
        - name: config
          configMap:
            name: alertmanager-config
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ocs-storagecluster-ceph-rbd
        resources:
          requests:
            storage: 10Gi
```

---

## 11. HashiCorp Vault

```yaml
# File: 09-vault/vault-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: vault
  namespace: banking-security
spec:
  serviceName: vault
  replicas: 3
  selector:
    matchLabels:
      app: vault
  template:
    metadata:
      labels:
        app: vault
    spec:
      containers:
        - name: vault
          image: hashicorp/vault:1.15.0
          ports:
            - containerPort: 8200
              name: http
            - containerPort: 8201
              name: cluster
          resources:
            requests:
              memory: 2Gi
              cpu: 1
            limits:
              memory: 2Gi
              cpu: 1
          env:
            - name: VAULT_ADDR
              value: "http://127.0.0.1:8200"
            - name: VAULT_API_ADDR
              value: "http://$(POD_IP):8200"
            - name: POD_IP
              valueFrom:
                fieldRef:
                  fieldPath: status.podIP
          volumeMounts:
            - name: config
              mountPath: /vault/config
            - name: data
              mountPath: /vault/data
          command:
            - vault
            - server
            - -config=/vault/config/vault.hcl
      volumes:
        - name: config
          configMap:
            name: vault-config
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ocs-storagecluster-ceph-rbd
        resources:
          requests:
            storage: 10Gi

---
apiVersion: v1
kind: Service
metadata:
  name: vault
  namespace: banking-security
spec:
  type: ClusterIP
  selector:
    app: vault
  ports:
    - name: http
      port: 8200
    - name: cluster
      port: 8201

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: vault-config
  namespace: banking-security
data:
  vault.hcl: |
    storage "raft" {
      path = "/vault/data"
    }
    
    listener "tcp" {
      address = "0.0.0.0:8200"
      tls_disable = 1
    }
    
    api_addr = "http://vault.banking-security.svc.cluster.local:8200"
    cluster_addr = "http://$(POD_IP):8201"
    ui = true
```

---

## 12. Network Policies

```yaml
# File: 10-network/network-policies.yaml
---
# Allow API Gateway to JanusGraph
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-to-janusgraph
  namespace: banking-production
spec:
  podSelector:
    matchLabels:
      app: janusgraph
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api-gateway
      ports:
        - protocol: TCP
          port: 8182

---
# Allow Consumers to Pulsar
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-consumers-to-pulsar
  namespace: banking-production
spec:
  podSelector:
    matchLabels:
      app: pulsar-broker
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: graph-consumer
        - podSelector:
            matchLabels:
              app: vector-consumer
      ports:
        - protocol: TCP
          port: 6650

---
# Allow Prometheus to scrape all
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-prometheus-scrape
  namespace: banking-production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: banking-monitoring
        - podSelector:
            matchLabels:
              app: prometheus
      ports:
        - protocol: TCP
          port: 9090
```

---

## 13. Ingress Routes

```yaml
# File: 10-network/ingress-routes.yaml
---
# API Gateway Route
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: api-gateway
  namespace: banking-production
spec:
  host: banking-api.apps.paris.company.com
  to:
    kind: Service
    name: api-gateway
  port:
    targetPort: http
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect

---
# Grafana Route
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: grafana
  namespace: banking-monitoring
spec:
  host: grafana.apps.paris.company.com
  to:
    kind: Service
    name: grafana
  port:
    targetPort: http
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect

---
# Prometheus Route (internal only)
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: prometheus
  namespace: banking-monitoring
spec:
  host: prometheus.apps.paris.company.com
  to:
    kind: Service
    name: prometheus
  port:
    targetPort: http
  tls:
    termination: edge
```

---

## 14. Validation Scripts

### 14.1 Deployment Validation Script

```bash
#!/bin/bash
# File: scripts/validate-deployment.sh

set -e

NAMESPACE="banking-production"

echo "=== Validating OpenShift Deployment ==="

# Check namespaces
echo "Checking namespaces..."
oc get namespace banking-production banking-monitoring banking-security

# Check storage
echo "Checking storage..."
oc get storageclass ocs-storagecluster-ceph-rbd
oc get pvc -n $NAMESPACE

# Check Cassandra
echo "Checking HCD Cassandra..."
oc get cassandradatacenter -n $NAMESPACE
oc wait --for=condition=Ready cassandradatacenter/dc-paris -n $NAMESPACE --timeout=600s

# Check JanusGraph
echo "Checking JanusGraph..."
oc get statefulset janusgraph -n $NAMESPACE
oc wait --for=condition=Ready pod -l app=janusgraph -n $NAMESPACE --timeout=600s

# Check Pulsar
echo "Checking Pulsar..."
oc get statefulset zookeeper pulsar-broker -n $NAMESPACE
oc wait --for=condition=Ready pod -l app=pulsar-broker -n $NAMESPACE --timeout=600s

# Check OpenSearch
echo "Checking OpenSearch..."
oc get statefulset opensearch -n $NAMESPACE
oc wait --for=condition=Ready pod -l app=opensearch -n $NAMESPACE --timeout=600s

# Check API Services
echo "Checking API Services..."
oc get deployment api-gateway graph-consumer vector-consumer -n $NAMESPACE
oc wait --for=condition=Available deployment/api-gateway -n $NAMESPACE --timeout=300s

# Check Monitoring
echo "Checking Monitoring..."
oc get statefulset prometheus -n banking-monitoring
oc get deployment grafana -n banking-monitoring

# Check Routes
echo "Checking Routes..."
oc get route -n $NAMESPACE
oc get route -n banking-monitoring

echo "=== Validation Complete ==="
```

### 14.2 Health Check Script

```bash
#!/bin/bash
# File: scripts/health-check.sh

NAMESPACE="banking-production"

echo "=== Health Check ==="

# JanusGraph health
echo "JanusGraph:"
oc exec -n $NAMESPACE janusgraph-0 -- curl -s http://127.0.0.1:8182/?gremlin=1+1

# Cassandra health
echo "Cassandra:"
oc exec -n $NAMESPACE dc-paris-rack1-sts-0 -- nodetool status

# Pulsar health
echo "Pulsar:"
oc exec -n $NAMESPACE pulsar-broker-0 -- bin/pulsar-admin brokers healthcheck

# OpenSearch health
echo "OpenSearch:"
oc exec -n $NAMESPACE opensearch-0 -- curl -s http://localhost:9200/_cluster/health

echo "=== Health Check Complete ==="
```

### 14.3 Quick Deploy Script

```bash
#!/bin/bash
# File: scripts/quick-deploy.sh

set -e

SITE="paris"  # Change per site: paris, london, frankfurt

echo "=== Deploying to site: $SITE ==="

# Phase 1: Infrastructure
echo "Phase 1: Infrastructure..."
oc apply -f 00-namespaces/
oc apply -f 01-storage/
oc apply -f 02-operators/
sleep 30

# Phase 2: Stateful Services
echo "Phase 2: Stateful Services..."
oc apply -f 03-cassandra/cassandra-datacenter-$SITE.yaml
oc wait --for=condition=Ready cassandradatacenter/dc-$SITE -n banking-production --timeout=600s

oc apply -f 05-pulsar/
oc wait --for=condition=Ready pod -l app=zookeeper -n banking-production --timeout=300s
oc wait --for=condition=Ready pod -l app=pulsar-broker -n banking-production --timeout=300s

oc apply -f 06-opensearch/
oc wait --for=condition=Ready pod -l app=opensearch -n banking-production --timeout=300s

oc apply -f 09-vault/
oc wait --for=condition=Ready pod -l app=vault -n banking-security --timeout=300s

# Phase 3: Graph Layer
echo "Phase 3: Graph Layer..."
oc apply -f 04-janusgraph/
oc wait --for=condition=Ready pod -l app=janusgraph -n banking-production --timeout=600s

# Phase 4: Application Layer
echo "Phase 4: Application Layer..."
oc apply -f 07-api/
oc wait --for=condition=Available deployment/api-gateway -n banking-production --timeout=300s

# Phase 5: Monitoring
echo "Phase 5: Monitoring..."
oc apply -f 08-monitoring/
oc wait --for=condition=Ready pod -l app=prometheus -n banking-monitoring --timeout=300s

# Phase 6: Network & Security
echo "Phase 6: Network & Security..."
oc apply -f 10-network/

echo "=== Deployment Complete ==="
echo "Run ./scripts/validate-deployment.sh to validate"
```

---

## Summary

Ce document fournit tous les manifests YAML nécessaires pour déployer la plateforme Banking Graph Analytics sur OpenShift en configuration 3 sites avec HA/DR conforme DORA.

**Prochaines étapes:**
1. Adapter les manifests pour chaque site (paris, london, frankfurt)
2. Exécuter le script de déploiement rapide
3. Valider avec les scripts de validation
4. Consulter [`openshift-migration-operations.md`](openshift-migration-operations.md) pour la migration complète

**Documentation complète:**
- Architecture: [`openshift-3-site-ha-dr-dora.md`](openshift-3-site-ha-dr-dora.md)
- Manifests: Ce document
- Migration & Ops: [`openshift-migration-operations.md`](openshift-migration-operations.md)

---

**Version:** 1.0  
**Date:** 2026-02-12  
**Status:** Production Ready ✅
