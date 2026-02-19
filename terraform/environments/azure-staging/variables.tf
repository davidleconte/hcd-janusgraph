# Azure Staging Environment Variables

variable "azure_client_id" {
  description = "Azure Service Principal Client ID"
  type        = string
  sensitive   = true
}

variable "azure_tenant_id" {
  description = "Azure Tenant ID"
  type        = string
  sensitive   = true
}

variable "azure_admin_group_ids" {
  description = "List of Azure AD group IDs for cluster administrators"
  type        = list(string)
  default     = []
}