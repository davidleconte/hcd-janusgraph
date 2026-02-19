/**
 * Monitoring Module
 * 
 * Deploys Prometheus, Grafana, AlertManager, and related monitoring infrastructure
 * for JanusGraph Banking Platform using Helm charts.
 * 
 * Version: 1.0
 * Date: 2026-02-19
 */

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
}

# ============================================================================
# Monitoring Namespace
# ============================================================================

resource "kubernetes_namespace_v1" "monitoring" {
  metadata {
    name = var.monitoring_namespace

    labels = {
      name        = var.monitoring_namespace
      environment = var.environment
    }
  }
}

# ============================================================================
# Prometheus Operator (kube-prometheus-stack)
# ============================================================================

resource "helm_release" "kube_prometheus_stack" {
  name       = "kube-prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = var.prometheus_stack_version
  namespace  = kubernetes_namespace_v1.monitoring.metadata[0].name

  values = [
    yamlencode({
      # Prometheus Configuration
      prometheus = {
        enabled = true
        prometheusSpec = {
          retention          = var.prometheus_retention
          retentionSize      = var.prometheus_retention_size
          storageSpec = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = var.storage_class_name
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = var.prometheus_storage_size
                  }
                }
              }
            }
          }
          resources = {
            requests = {
              cpu    = var.prometheus_cpu_request
              memory = var.prometheus_memory_request
            }
            limits = {
              cpu    = var.prometheus_cpu_limit
              memory = var.prometheus_memory_limit
            }
          }
          serviceMonitorSelectorNilUsesHelmValues = false
          podMonitorSelectorNilUsesHelmValues     = false
          ruleSelectorNilUsesHelmValues           = false
          additionalScrapeConfigs = [
            {
              job_name = "janusgraph-exporter"
              static_configs = [
                {
                  targets = ["janusgraph-exporter:9091"]
                }
              ]
            }
          ]
        }
        service = {
          type = var.prometheus_service_type
          port = 9090
        }
        ingress = {
          enabled = var.enable_ingress
          annotations = {
            "kubernetes.io/ingress.class"                = "nginx"
            "cert-manager.io/cluster-issuer"             = "letsencrypt-prod"
            "nginx.ingress.kubernetes.io/auth-type"      = "basic"
            "nginx.ingress.kubernetes.io/auth-secret"    = "prometheus-basic-auth"
            "nginx.ingress.kubernetes.io/auth-realm"     = "Authentication Required"
          }
          hosts = [
            {
              host = var.prometheus_hostname
              paths = [
                {
                  path     = "/"
                  pathType = "Prefix"
                }
              ]
            }
          ]
          tls = [
            {
              secretName = "prometheus-tls"
              hosts      = [var.prometheus_hostname]
            }
          ]
        }
      }

      # Grafana Configuration
      grafana = {
        enabled = true
        adminPassword = var.grafana_admin_password
        persistence = {
          enabled          = true
          storageClassName = var.storage_class_name
          size             = var.grafana_storage_size
        }
        resources = {
          requests = {
            cpu    = var.grafana_cpu_request
            memory = var.grafana_memory_request
          }
          limits = {
            cpu    = var.grafana_cpu_limit
            memory = var.grafana_memory_limit
          }
        }
        service = {
          type = var.grafana_service_type
          port = 3000
        }
        ingress = {
          enabled = var.enable_ingress
          annotations = {
            "kubernetes.io/ingress.class"        = "nginx"
            "cert-manager.io/cluster-issuer"     = "letsencrypt-prod"
          }
          hosts = [var.grafana_hostname]
          tls = [
            {
              secretName = "grafana-tls"
              hosts      = [var.grafana_hostname]
            }
          ]
        }
        datasources = {
          "datasources.yaml" = {
            apiVersion = 1
            datasources = [
              {
                name      = "Prometheus"
                type      = "prometheus"
                url       = "http://kube-prometheus-stack-prometheus:9090"
                access    = "proxy"
                isDefault = true
              },
              {
                name   = "Loki"
                type   = "loki"
                url    = "http://loki:3100"
                access = "proxy"
              }
            ]
          }
        }
        dashboardProviders = {
          "dashboardproviders.yaml" = {
            apiVersion = 1
            providers = [
              {
                name            = "default"
                orgId           = 1
                folder          = ""
                type            = "file"
                disableDeletion = false
                editable        = true
                options = {
                  path = "/var/lib/grafana/dashboards/default"
                }
              }
            ]
          }
        }
        dashboards = {
          default = {
            janusgraph = {
              gnetId    = 14584
              revision  = 1
              datasource = "Prometheus"
            }
            kubernetes-cluster = {
              gnetId    = 7249
              revision  = 1
              datasource = "Prometheus"
            }
            cassandra = {
              gnetId    = 11863
              revision  = 1
              datasource = "Prometheus"
            }
          }
        }
      }

      # AlertManager Configuration
      alertmanager = {
        enabled = true
        alertmanagerSpec = {
          storage = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = var.storage_class_name
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = var.alertmanager_storage_size
                  }
                }
              }
            }
          }
          resources = {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu    = "200m"
              memory = "256Mi"
            }
          }
        }
        service = {
          type = var.alertmanager_service_type
          port = 9093
        }
        ingress = {
          enabled = var.enable_ingress
          annotations = {
            "kubernetes.io/ingress.class"                = "nginx"
            "cert-manager.io/cluster-issuer"             = "letsencrypt-prod"
            "nginx.ingress.kubernetes.io/auth-type"      = "basic"
            "nginx.ingress.kubernetes.io/auth-secret"    = "alertmanager-basic-auth"
            "nginx.ingress.kubernetes.io/auth-realm"     = "Authentication Required"
          }
          hosts = [
            {
              host = var.alertmanager_hostname
              paths = [
                {
                  path     = "/"
                  pathType = "Prefix"
                }
              ]
            }
          ]
          tls = [
            {
              secretName = "alertmanager-tls"
              hosts      = [var.alertmanager_hostname]
            }
          ]
        }
        config = {
          global = {
            resolve_timeout = "5m"
          }
          route = {
            group_by        = ["alertname", "cluster", "service"]
            group_wait      = "10s"
            group_interval  = "10s"
            repeat_interval = "12h"
            receiver        = "default"
            routes = [
              {
                match = {
                  alertname = "Watchdog"
                }
                receiver = "null"
              },
              {
                match = {
                  severity = "critical"
                }
                receiver = "critical"
              }
            ]
          }
          receivers = [
            {
              name = "null"
            },
            {
              name = "default"
              slack_configs = var.slack_webhook_url != "" ? [
                {
                  api_url   = var.slack_webhook_url
                  channel   = var.slack_channel
                  title     = "{{ .GroupLabels.alertname }}"
                  text      = "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
                }
              ] : []
            },
            {
              name = "critical"
              slack_configs = var.slack_webhook_url != "" ? [
                {
                  api_url   = var.slack_webhook_url
                  channel   = var.slack_channel
                  title     = "🚨 CRITICAL: {{ .GroupLabels.alertname }}"
                  text      = "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
                }
              ] : []
              pagerduty_configs = var.pagerduty_service_key != "" ? [
                {
                  service_key = var.pagerduty_service_key
                }
              ] : []
            }
          ]
        }
      }

      # Node Exporter
      nodeExporter = {
        enabled = true
      }

      # Kube State Metrics
      kubeStateMetrics = {
        enabled = true
      }
    })
  ]

  depends_on = [kubernetes_namespace_v1.monitoring]
}

# ============================================================================
# Loki (Log Aggregation)
# ============================================================================

resource "helm_release" "loki" {
  count = var.enable_loki ? 1 : 0

  name       = "loki"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki-stack"
  version    = var.loki_version
  namespace  = kubernetes_namespace_v1.monitoring.metadata[0].name

  values = [
    yamlencode({
      loki = {
        enabled = true
        persistence = {
          enabled          = true
          storageClassName = var.storage_class_name
          size             = var.loki_storage_size
        }
        config = {
          auth_enabled = false
          ingester = {
            chunk_idle_period   = "3m"
            chunk_block_size    = 262144
            chunk_retain_period = "1m"
            max_transfer_retries = 0
            lifecycler = {
              ring = {
                kvstore = {
                  store = "inmemory"
                }
                replication_factor = 1
              }
            }
          }
          limits_config = {
            enforce_metric_name      = false
            reject_old_samples       = true
            reject_old_samples_max_age = "168h"
          }
          schema_config = {
            configs = [
              {
                from         = "2020-10-24"
                store        = "boltdb-shipper"
                object_store = "filesystem"
                schema       = "v11"
                index = {
                  prefix = "index_"
                  period = "24h"
                }
              }
            ]
          }
          server = {
            http_listen_port = 3100
          }
          storage_config = {
            boltdb_shipper = {
              active_index_directory = "/data/loki/boltdb-shipper-active"
              cache_location         = "/data/loki/boltdb-shipper-cache"
              cache_ttl              = "24h"
              shared_store           = "filesystem"
            }
            filesystem = {
              directory = "/data/loki/chunks"
            }
          }
          chunk_store_config = {
            max_look_back_period = "0s"
          }
          table_manager = {
            retention_deletes_enabled = true
            retention_period          = var.loki_retention_period
          }
        }
      }
      promtail = {
        enabled = true
        config = {
          clients = [
            {
              url = "http://loki:3100/loki/api/v1/push"
            }
          ]
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace_v1.monitoring]
}

# ============================================================================
# Jaeger (Distributed Tracing)
# ============================================================================

resource "helm_release" "jaeger" {
  count = var.enable_jaeger ? 1 : 0

  name       = "jaeger"
  repository = "https://jaegertracing.github.io/helm-charts"
  chart      = "jaeger"
  version    = var.jaeger_version
  namespace  = kubernetes_namespace_v1.monitoring.metadata[0].name

  values = [
    yamlencode({
      provisionDataStore = {
        cassandra = false
      }
      allInOne = {
        enabled = true
        ingress = {
          enabled = var.enable_ingress
          annotations = {
            "kubernetes.io/ingress.class" = "nginx"
          }
          hosts = [var.jaeger_hostname]
        }
      }
      storage = {
        type = "memory"
      }
      agent = {
        enabled = true
      }
      collector = {
        enabled = true
        service = {
          type = "ClusterIP"
        }
      }
      query = {
        enabled = true
        service = {
          type = "ClusterIP"
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace_v1.monitoring]
}

# ============================================================================
# ServiceMonitor for JanusGraph
# ============================================================================

resource "kubernetes_manifest" "janusgraph_service_monitor" {
  manifest = {
    apiVersion = "monitoring.coreos.com/v1"
    kind       = "ServiceMonitor"
    metadata = {
      name      = "janusgraph-exporter"
      namespace = kubernetes_namespace_v1.monitoring.metadata[0].name
      labels = {
        app = "janusgraph-exporter"
      }
    }
    spec = {
      selector = {
        matchLabels = {
          app = "janusgraph-exporter"
        }
      }
      endpoints = [
        {
          port     = "metrics"
          interval = "30s"
          path     = "/metrics"
        }
      ]
    }
  }

  depends_on = [helm_release.kube_prometheus_stack]
}

# ============================================================================
# PrometheusRule for JanusGraph Alerts
# ============================================================================

resource "kubernetes_manifest" "janusgraph_prometheus_rule" {
  manifest = {
    apiVersion = "monitoring.coreos.com/v1"
    kind       = "PrometheusRule"
    metadata = {
      name      = "janusgraph-alerts"
      namespace = kubernetes_namespace_v1.monitoring.metadata[0].name
      labels = {
        prometheus = "kube-prometheus"
      }
    }
    spec = {
      groups = [
        {
          name = "janusgraph"
          interval = "30s"
          rules = [
            {
              alert = "JanusGraphHighQueryLatency"
              expr  = "histogram_quantile(0.95, rate(janusgraph_query_duration_seconds_bucket[5m])) > 1"
              for   = "5m"
              labels = {
                severity = "warning"
              }
              annotations = {
                summary     = "JanusGraph high query latency"
                description = "JanusGraph P95 query latency is above 1 second"
              }
            },
            {
              alert = "JanusGraphHighErrorRate"
              expr  = "rate(janusgraph_errors_total[5m]) > 0.05"
              for   = "5m"
              labels = {
                severity = "critical"
              }
              annotations = {
                summary     = "JanusGraph high error rate"
                description = "JanusGraph error rate is above 5%"
              }
            },
            {
              alert = "JanusGraphDown"
              expr  = "up{job=\"janusgraph-exporter\"} == 0"
              for   = "2m"
              labels = {
                severity = "critical"
              }
              annotations = {
                summary     = "JanusGraph is down"
                description = "JanusGraph exporter is not reachable"
              }
            }
          ]
        }
      ]
    }
  }

  depends_on = [helm_release.kube_prometheus_stack]
}