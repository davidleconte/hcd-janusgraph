/**
 * Monitoring Module Variables
 * 
 * Version: 1.0
 * Date: 2026-02-19
 */

# ============================================================================
# Required Variables
# ============================================================================

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "storage_class_name" {
  description = "StorageClass name for persistent volumes"
  type        = string
  default     = "general-storage"
}

# ============================================================================
# Namespace Configuration
# ============================================================================

variable "monitoring_namespace" {
  description = "Kubernetes namespace for monitoring stack"
  type        = string
  default     = "monitoring"
}

# ============================================================================
# Helm Chart Versions
# ============================================================================

variable "prometheus_stack_version" {
  description = "Version of kube-prometheus-stack Helm chart"
  type        = string
  default     = "55.0.0"
}

variable "loki_version" {
  description = "Version of loki-stack Helm chart"
  type        = string
  default     = "2.9.0"
}

variable "jaeger_version" {
  description = "Version of jaeger Helm chart"
  type        = string
  default     = "0.71.0"
}

# ============================================================================
# Prometheus Configuration
# ============================================================================

variable "prometheus_retention" {
  description = "Prometheus data retention period"
  type        = string
  default     = "30d"
}

variable "prometheus_retention_size" {
  description = "Prometheus data retention size"
  type        = string
  default     = "50GB"
}

variable "prometheus_storage_size" {
  description = "Prometheus persistent volume size"
  type        = string
  default     = "100Gi"
}

variable "prometheus_cpu_request" {
  description = "Prometheus CPU request"
  type        = string
  default     = "500m"
}

variable "prometheus_memory_request" {
  description = "Prometheus memory request"
  type        = string
  default     = "2Gi"
}

variable "prometheus_cpu_limit" {
  description = "Prometheus CPU limit"
  type        = string
  default     = "2000m"
}

variable "prometheus_memory_limit" {
  description = "Prometheus memory limit"
  type        = string
  default     = "8Gi"
}

variable "prometheus_service_type" {
  description = "Prometheus service type (ClusterIP, LoadBalancer, NodePort)"
  type        = string
  default     = "ClusterIP"

  validation {
    condition     = contains(["ClusterIP", "LoadBalancer", "NodePort"], var.prometheus_service_type)
    error_message = "Service type must be ClusterIP, LoadBalancer, or NodePort."
  }
}

variable "prometheus_hostname" {
  description = "Hostname for Prometheus ingress"
  type        = string
  default     = "prometheus.example.com"
}

# ============================================================================
# Grafana Configuration
# ============================================================================

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
}

variable "grafana_storage_size" {
  description = "Grafana persistent volume size"
  type        = string
  default     = "10Gi"
}

variable "grafana_cpu_request" {
  description = "Grafana CPU request"
  type        = string
  default     = "100m"
}

variable "grafana_memory_request" {
  description = "Grafana memory request"
  type        = string
  default     = "256Mi"
}

variable "grafana_cpu_limit" {
  description = "Grafana CPU limit"
  type        = string
  default     = "500m"
}

variable "grafana_memory_limit" {
  description = "Grafana memory limit"
  type        = string
  default     = "1Gi"
}

variable "grafana_service_type" {
  description = "Grafana service type (ClusterIP, LoadBalancer, NodePort)"
  type        = string
  default     = "ClusterIP"

  validation {
    condition     = contains(["ClusterIP", "LoadBalancer", "NodePort"], var.grafana_service_type)
    error_message = "Service type must be ClusterIP, LoadBalancer, or NodePort."
  }
}

variable "grafana_hostname" {
  description = "Hostname for Grafana ingress"
  type        = string
  default     = "grafana.example.com"
}

# ============================================================================
# AlertManager Configuration
# ============================================================================

variable "alertmanager_storage_size" {
  description = "AlertManager persistent volume size"
  type        = string
  default     = "10Gi"
}

variable "alertmanager_service_type" {
  description = "AlertManager service type (ClusterIP, LoadBalancer, NodePort)"
  type        = string
  default     = "ClusterIP"

  validation {
    condition     = contains(["ClusterIP", "LoadBalancer", "NodePort"], var.alertmanager_service_type)
    error_message = "Service type must be ClusterIP, LoadBalancer, or NodePort."
  }
}

variable "alertmanager_hostname" {
  description = "Hostname for AlertManager ingress"
  type        = string
  default     = "alertmanager.example.com"
}

# ============================================================================
# Alert Notification Configuration
# ============================================================================

variable "slack_webhook_url" {
  description = "Slack webhook URL for alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "slack_channel" {
  description = "Slack channel for alerts"
  type        = string
  default     = "#alerts"
}

variable "pagerduty_service_key" {
  description = "PagerDuty service key for critical alerts"
  type        = string
  default     = ""
  sensitive   = true
}

# ============================================================================
# Loki Configuration
# ============================================================================

variable "enable_loki" {
  description = "Enable Loki log aggregation"
  type        = bool
  default     = true
}

variable "loki_storage_size" {
  description = "Loki persistent volume size"
  type        = string
  default     = "50Gi"
}

variable "loki_retention_period" {
  description = "Loki log retention period"
  type        = string
  default     = "168h" # 7 days
}

# ============================================================================
# Jaeger Configuration
# ============================================================================

variable "enable_jaeger" {
  description = "Enable Jaeger distributed tracing"
  type        = bool
  default     = true
}

variable "jaeger_hostname" {
  description = "Hostname for Jaeger ingress"
  type        = string
  default     = "jaeger.example.com"
}

# ============================================================================
# Ingress Configuration
# ============================================================================

variable "enable_ingress" {
  description = "Enable ingress for monitoring services"
  type        = bool
  default     = false
}