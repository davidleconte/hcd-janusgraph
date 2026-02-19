# GCP Production Environment Variables

variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "alert_email" {
  description = "Email address for critical alerts"
  type        = string
}