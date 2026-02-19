# Outputs for OpenShift Cluster Module

output "cluster_id" {
  description = "ID of the cluster"
  value = (
    var.cloud_provider == "aws" ? aws_eks_cluster.main[0].id :
    var.cloud_provider == "azure" ? azurerm_kubernetes_cluster.main[0].id :
    var.cloud_provider == "gcp" ? google_container_cluster.main[0].id :
    null
  )
}

output "cluster_arn" {
  description = "ARN/ID of the cluster"
  value = (
    var.cloud_provider == "aws" ? aws_eks_cluster.main[0].arn :
    var.cloud_provider == "azure" ? azurerm_kubernetes_cluster.main[0].id :
    var.cloud_provider == "gcp" ? google_container_cluster.main[0].id :
    null
  )
}

output "cluster_endpoint" {
  description = "Endpoint for cluster API"
  value = (
    var.cloud_provider == "aws" ? aws_eks_cluster.main[0].endpoint :
    var.cloud_provider == "azure" ? azurerm_kubernetes_cluster.main[0].kube_config[0].host :
    var.cloud_provider == "gcp" ? "https://${google_container_cluster.main[0].endpoint}" :
    null
  )
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = var.cloud_provider == "aws" ? aws_eks_cluster.main[0].vpc_config[0].cluster_security_group_id : null
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = var.cloud_provider == "aws" ? aws_eks_cluster.main[0].certificate_authority[0].data : null
  sensitive   = true
}

output "cluster_version" {
  description = "Kubernetes version of the cluster"
  value       = var.cloud_provider == "aws" ? aws_eks_cluster.main[0].version : null
}

output "cluster_oidc_issuer_url" {
  description = "OIDC issuer URL for the cluster"
  value       = var.cloud_provider == "aws" ? aws_eks_cluster.main[0].identity[0].oidc[0].issuer : null
}

output "node_group_id" {
  description = "ID of the EKS node group"
  value       = var.cloud_provider == "aws" ? aws_eks_node_group.main[0].id : null
}

output "node_group_arn" {
  description = "ARN of the EKS node group"
  value       = var.cloud_provider == "aws" ? aws_eks_node_group.main[0].arn : null
}

output "node_group_status" {
  description = "Status of the EKS node group"
  value       = var.cloud_provider == "aws" ? aws_eks_node_group.main[0].status : null
}

output "node_role_arn" {
  description = "ARN of the IAM role for worker nodes"
  value       = var.cloud_provider == "aws" ? aws_iam_role.node[0].arn : null
}

output "ebs_csi_role_arn" {
  description = "ARN of the IAM role for EBS CSI driver"
  value       = var.cloud_provider == "aws" && var.enable_ebs_csi ? aws_iam_role.ebs_csi[0].arn : null

# ============================================================================
# Azure-Specific Outputs
# ============================================================================

output "azure_resource_group_name" {
  description = "Azure resource group name"
  value       = var.cloud_provider == "azure" ? azurerm_resource_group.main[0].name : null
}

output "azure_cluster_identity" {
  description = "Azure AKS cluster identity"
  value       = var.cloud_provider == "azure" ? azurerm_kubernetes_cluster.main[0].identity[0].principal_id : null
}

output "azure_kubelet_identity" {
  description = "Azure AKS kubelet identity"
  value       = var.cloud_provider == "azure" ? azurerm_kubernetes_cluster.main[0].kubelet_identity[0].object_id : null
}

output "azure_log_analytics_workspace_id" {
  description = "Azure Log Analytics workspace ID"
  value       = var.cloud_provider == "azure" ? azurerm_log_analytics_workspace.main[0].id : null
}

# ============================================================================
# GCP-Specific Outputs
# ============================================================================

output "gcp_cluster_ca_certificate" {
  description = "GCP GKE cluster CA certificate"
  value       = var.cloud_provider == "gcp" ? base64decode(google_container_cluster.main[0].master_auth[0].cluster_ca_certificate) : null
  sensitive   = true
}

output "gcp_cluster_master_version" {
  description = "GCP GKE master version"
  value       = var.cloud_provider == "gcp" ? google_container_cluster.main[0].master_version : null
}

output "gcp_node_service_account" {
  description = "GCP service account email for nodes"
  value       = var.cloud_provider == "gcp" ? google_service_account.gke_nodes[0].email : null
}

# ============================================================================
# Cloud-Agnostic Outputs
# ============================================================================

output "cluster_name" {
  description = "Name of the cluster"
  value       = var.cluster_name
}

output "cloud_provider" {
  description = "Cloud provider used"
  value       = var.cloud_provider
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "kubernetes_version" {
  description = "Kubernetes version"
  value       = var.kubernetes_version
}

output "node_count" {
  description = "Number of worker nodes"
  value       = var.node_count
}
}

output "kubeconfig" {
  description = "kubectl config for cluster access"
  value = var.cloud_provider == "aws" ? templatefile("${path.module}/templates/kubeconfig.tpl", {
    cluster_name                         = aws_eks_cluster.main[0].name
    cluster_endpoint                     = aws_eks_cluster.main[0].endpoint
    cluster_certificate_authority_data   = aws_eks_cluster.main[0].certificate_authority[0].data
  }) : null
  sensitive = true
}

output "cluster_tags" {
  description = "Tags applied to the cluster"
  value       = local.common_tags
}