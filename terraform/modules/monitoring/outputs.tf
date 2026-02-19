/**
 * Monitoring Module Outputs
 * 
 * Version: 1.0
 * Date: 2026-02-19
 */

# ============================================================================
# Namespace Outputs
# ============================================================================

output "monitoring_namespace" {
  description = "Name of the monitoring namespace"
  value       = kubernetes_namespace_v1.monitoring.metadata[0].name
}

# ============================================================================
# Prometheus Outputs
# ============================================================================

output "prometheus_service_name" {
  description = "Name of the Prometheus service"
  value       = "kube-prometheus-stack-prometheus"
}

output "prometheus_service_port" {
  description = "Port of the Prometheus service"
  value       = 9090
}

output "prometheus_url" {
  description = "Internal URL for Prometheus"
  value       = "http://kube-prometheus-stack-prometheus.${kubernetes_namespace_v1.monitoring.metadata[0].name}.svc.cluster.local:9090"
}

output "prometheus_hostname" {
  description = "External hostname for Prometheus (if ingress enabled)"
  value       = var.enable_ingress ? var.prometheus_hostname : null
}

# ============================================================================
# Grafana Outputs
# ============================================================================

output "grafana_service_name" {
  description = "Name of the Grafana service"
  value       = "kube-prometheus-stack-grafana"
}

output "grafana_service_port" {
  description = "Port of the Grafana service"
  value       = 3000
}

output "grafana_url" {
  description = "Internal URL for Grafana"
  value       = "http://kube-prometheus-stack-grafana.${kubernetes_namespace_v1.monitoring.metadata[0].name}.svc.cluster.local:3000"
}

output "grafana_hostname" {
  description = "External hostname for Grafana (if ingress enabled)"
  value       = var.enable_ingress ? var.grafana_hostname : null
}

# ============================================================================
# AlertManager Outputs
# ============================================================================

output "alertmanager_service_name" {
  description = "Name of the AlertManager service"
  value       = "kube-prometheus-stack-alertmanager"
}

output "alertmanager_service_port" {
  description = "Port of the AlertManager service"
  value       = 9093
}

output "alertmanager_url" {
  description = "Internal URL for AlertManager"
  value       = "http://kube-prometheus-stack-alertmanager.${kubernetes_namespace_v1.monitoring.metadata[0].name}.svc.cluster.local:9093"
}

output "alertmanager_hostname" {
  description = "External hostname for AlertManager (if ingress enabled)"
  value       = var.enable_ingress ? var.alertmanager_hostname : null
}

# ============================================================================
# Loki Outputs
# ============================================================================

output "loki_service_name" {
  description = "Name of the Loki service"
  value       = var.enable_loki ? "loki" : null
}

output "loki_service_port" {
  description = "Port of the Loki service"
  value       = var.enable_loki ? 3100 : null
}

output "loki_url" {
  description = "Internal URL for Loki"
  value       = var.enable_loki ? "http://loki.${kubernetes_namespace_v1.monitoring.metadata[0].name}.svc.cluster.local:3100" : null
}

# ============================================================================
# Jaeger Outputs
# ============================================================================

output "jaeger_service_name" {
  description = "Name of the Jaeger service"
  value       = var.enable_jaeger ? "jaeger-query" : null
}

output "jaeger_service_port" {
  description = "Port of the Jaeger service"
  value       = var.enable_jaeger ? 16686 : null
}

output "jaeger_url" {
  description = "Internal URL for Jaeger"
  value       = var.enable_jaeger ? "http://jaeger-query.${kubernetes_namespace_v1.monitoring.metadata[0].name}.svc.cluster.local:16686" : null
}

output "jaeger_hostname" {
  description = "External hostname for Jaeger (if ingress enabled)"
  value       = var.enable_ingress && var.enable_jaeger ? var.jaeger_hostname : null
}

output "jaeger_collector_url" {
  description = "Internal URL for Jaeger collector"
  value       = var.enable_jaeger ? "http://jaeger-collector.${kubernetes_namespace_v1.monitoring.metadata[0].name}.svc.cluster.local:14268" : null
}

# ============================================================================
# Monitoring Stack Summary
# ============================================================================

output "monitoring_summary" {
  description = "Summary of monitoring stack configuration"
  value = {
    namespace = kubernetes_namespace_v1.monitoring.metadata[0].name
    prometheus = {
      service_name = "kube-prometheus-stack-prometheus"
      port         = 9090
      url          = "http://kube-prometheus-stack-prometheus.${kubernetes_namespace_v1.monitoring.metadata[0].name}.svc.cluster.local:9090"
      hostname     = var.enable_ingress ? var.prometheus_hostname : null
    }
    grafana = {
      service_name = "kube-prometheus-stack-grafana"
      port         = 3000
      url          = "http://kube-prometheus-stack-grafana.${kubernetes_namespace_v1.monitoring.metadata[0].name}.svc.cluster.local:3000"
      hostname     = var.enable_ingress ? var.grafana_hostname : null
    }
    alertmanager = {
      service_name = "kube-prometheus-stack-alertmanager"
      port         = 9093
      url          = "http://kube-prometheus-stack-alertmanager.${kubernetes_namespace_v1.monitoring.metadata[0].name}.svc.cluster.local:9093"
      hostname     = var.enable_ingress ? var.alertmanager_hostname : null
    }
    loki = var.enable_loki ? {
      service_name = "loki"
      port         = 3100
      url          = "http://loki.${kubernetes_namespace_v1.monitoring.metadata[0].name}.svc.cluster.local:3100"
    } : null
    jaeger = var.enable_jaeger ? {
      service_name = "jaeger-query"
      port         = 16686
      url          = "http://jaeger-query.${kubernetes_namespace_v1.monitoring.metadata[0].name}.svc.cluster.local:16686"
      hostname     = var.enable_ingress ? var.jaeger_hostname : null
    } : null
    ingress_enabled = var.enable_ingress
  }
}

# ============================================================================
# Access Instructions
# ============================================================================

output "access_instructions" {
  description = "Instructions for accessing monitoring services"
  value = var.enable_ingress ? {
    prometheus   = "https://${var.prometheus_hostname}"
    grafana      = "https://${var.grafana_hostname}"
    alertmanager = "https://${var.alertmanager_hostname}"
    jaeger       = var.enable_jaeger ? "https://${var.jaeger_hostname}" : null
  } : {
    prometheus   = "kubectl port-forward -n ${kubernetes_namespace_v1.monitoring.metadata[0].name} svc/kube-prometheus-stack-prometheus 9090:9090"
    grafana      = "kubectl port-forward -n ${kubernetes_namespace_v1.monitoring.metadata[0].name} svc/kube-prometheus-stack-grafana 3000:3000"
    alertmanager = "kubectl port-forward -n ${kubernetes_namespace_v1.monitoring.metadata[0].name} svc/kube-prometheus-stack-alertmanager 9093:9093"
    jaeger       = var.enable_jaeger ? "kubectl port-forward -n ${kubernetes_namespace_v1.monitoring.metadata[0].name} svc/jaeger-query 16686:16686" : null
  }
}