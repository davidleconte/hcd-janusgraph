# Variables for Azure Development Environment

variable "azure_client_id" {
  description = "Azure AD application client ID for authentication"
  type        = string
  sensitive   = true
}

variable "azure_tenant_id" {
  description = "Azure AD tenant ID"
  type        = string
  sensitive   = true
}

variable "azure_admin_group_ids" {
  description = "Azure AD group IDs for cluster administrators"
  type        = list(string)
  default     = []
}