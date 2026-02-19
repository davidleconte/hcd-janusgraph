/**
 * Storage Module Outputs
 * 
 * Version: 1.0
 * Date: 2026-02-19
 */

# ============================================================================
# StorageClass Outputs
# ============================================================================

output "hcd_storage_class_name" {
  description = "Name of the HCD StorageClass"
  value       = kubernetes_storage_class_v1.hcd.metadata[0].name
}

output "janusgraph_storage_class_name" {
  description = "Name of the JanusGraph StorageClass"
  value       = kubernetes_storage_class_v1.janusgraph.metadata[0].name
}

output "opensearch_storage_class_name" {
  description = "Name of the OpenSearch StorageClass"
  value       = kubernetes_storage_class_v1.opensearch.metadata[0].name
}

output "pulsar_storage_class_name" {
  description = "Name of the Pulsar StorageClass"
  value       = kubernetes_storage_class_v1.pulsar.metadata[0].name
}

output "mission_control_storage_class_name" {
  description = "Name of the Mission Control StorageClass"
  value       = kubernetes_storage_class_v1.mission_control.metadata[0].name
}

output "general_storage_class_name" {
  description = "Name of the general purpose StorageClass"
  value       = kubernetes_storage_class_v1.general.metadata[0].name
}

# ============================================================================
# S3 Bucket Outputs
# ============================================================================

output "backups_bucket_id" {
  description = "ID of the backups S3 bucket"
  value       = aws_s3_bucket.backups.id
}

output "backups_bucket_arn" {
  description = "ARN of the backups S3 bucket"
  value       = aws_s3_bucket.backups.arn
}

output "snapshots_bucket_id" {
  description = "ID of the snapshots S3 bucket"
  value       = aws_s3_bucket.snapshots.id
}

output "snapshots_bucket_arn" {
  description = "ARN of the snapshots S3 bucket"
  value       = aws_s3_bucket.snapshots.arn
}

# ============================================================================
# Backup Outputs
# ============================================================================

output "backup_vault_name" {
  description = "Name of the AWS Backup vault"
  value       = aws_backup_vault.main.name
}

output "backup_vault_arn" {
  description = "ARN of the AWS Backup vault"
  value       = aws_backup_vault.main.arn
}

output "backup_plan_id" {
  description = "ID of the AWS Backup plan"
  value       = aws_backup_plan.main.id
}

output "backup_plan_arn" {
  description = "ARN of the AWS Backup plan"
  value       = aws_backup_plan.main.arn
}

output "backup_service_role_arn" {
  description = "ARN of the backup service IAM role"
  value       = aws_iam_role.backup_service.arn
}

# ============================================================================
# DLM Outputs
# ============================================================================

output "dlm_policy_id" {
  description = "ID of the DLM lifecycle policy"
  value       = aws_dlm_lifecycle_policy.ebs_snapshots.id
}

output "dlm_policy_arn" {
  description = "ARN of the DLM lifecycle policy"
  value       = aws_dlm_lifecycle_policy.ebs_snapshots.arn
}

output "dlm_role_arn" {
  description = "ARN of the DLM IAM role"
  value       = aws_iam_role.dlm.arn
}

# ============================================================================
# Storage Configuration Summary
# ============================================================================

output "storage_summary" {
  description = "Summary of storage configuration"
  value = {
    storage_classes = {
      hcd            = kubernetes_storage_class_v1.hcd.metadata[0].name
      janusgraph     = kubernetes_storage_class_v1.janusgraph.metadata[0].name
      opensearch     = kubernetes_storage_class_v1.opensearch.metadata[0].name
      pulsar         = kubernetes_storage_class_v1.pulsar.metadata[0].name
      mission_control = kubernetes_storage_class_v1.mission_control.metadata[0].name
      general        = kubernetes_storage_class_v1.general.metadata[0].name
    }
    backup_config = {
      vault_name          = aws_backup_vault.main.name
      plan_id             = aws_backup_plan.main.id
      retention_days      = var.backup_retention_days
      transition_days     = var.backup_transition_days
    }
    snapshot_config = {
      retention_days = var.snapshot_retention_days
      dlm_policy_id  = aws_dlm_lifecycle_policy.ebs_snapshots.id
    }
    s3_buckets = {
      backups   = aws_s3_bucket.backups.id
      snapshots = aws_s3_bucket.snapshots.id
    }
  }
}