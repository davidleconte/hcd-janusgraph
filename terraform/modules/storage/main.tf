/**
 * Storage Module
 * 
 * Creates StorageClasses, PersistentVolumes, and backup storage for JanusGraph Banking Platform.
 * Supports EBS CSI driver with encryption, snapshots, and backup policies.
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
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

# ============================================================================
# AWS StorageClass - HCD (Cassandra)
# ============================================================================

resource "kubernetes_storage_class_v1" "hcd" {
  count = var.cloud_provider == "aws" ? 1 : 0

  metadata {
    name = "hcd-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = var.hcd_reclaim_policy
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    type      = var.hcd_volume_type
    iops      = var.hcd_volume_type == "io2" ? tostring(var.hcd_iops) : null
    encrypted = "true"
    kmsKeyId  = var.kms_key_id
    fsType    = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.ebs.csi.aws.com/zone"
      values = var.availability_zones
    }
  }
}

# ============================================================================
# AWS StorageClass - JanusGraph
# ============================================================================

resource "kubernetes_storage_class_v1" "janusgraph" {
  count = var.cloud_provider == "aws" ? 1 : 0

  metadata {
    name = "janusgraph-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = var.janusgraph_reclaim_policy
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    type      = var.janusgraph_volume_type
    iops      = var.janusgraph_volume_type == "io2" ? tostring(var.janusgraph_iops) : null
    encrypted = "true"
    kmsKeyId  = var.kms_key_id
    fsType    = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.ebs.csi.aws.com/zone"
      values = var.availability_zones
    }
  }
}

# ============================================================================
# AWS StorageClass - OpenSearch
# ============================================================================

resource "kubernetes_storage_class_v1" "opensearch" {
  count = var.cloud_provider == "aws" ? 1 : 0

  metadata {
    name = "opensearch-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = var.opensearch_reclaim_policy
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    type      = var.opensearch_volume_type
    iops      = var.opensearch_volume_type == "io2" ? tostring(var.opensearch_iops) : null
    encrypted = "true"
    kmsKeyId  = var.kms_key_id
    fsType    = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.ebs.csi.aws.com/zone"
      values = var.availability_zones
    }
  }
}

# ============================================================================
# AWS StorageClass - Pulsar
# ============================================================================

resource "kubernetes_storage_class_v1" "pulsar" {
  count = var.cloud_provider == "aws" ? 1 : 0

  metadata {
    name = "pulsar-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = var.pulsar_reclaim_policy
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    type      = var.pulsar_volume_type
    iops      = var.pulsar_volume_type == "io2" ? tostring(var.pulsar_iops) : null
    encrypted = "true"
    kmsKeyId  = var.kms_key_id
    fsType    = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.ebs.csi.aws.com/zone"
      values = var.availability_zones
    }
  }
}

# ============================================================================
# AWS StorageClass - Mission Control (PostgreSQL)
# ============================================================================

resource "kubernetes_storage_class_v1" "mission_control" {
  count = var.cloud_provider == "aws" ? 1 : 0

  metadata {
    name = "mission-control-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = "Retain"
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    type      = "gp3"
    encrypted = "true"
    kmsKeyId  = var.kms_key_id
    fsType    = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.ebs.csi.aws.com/zone"
      values = var.availability_zones
    }
  }
}

# ============================================================================
# AWS StorageClass - General Purpose (Default)
# ============================================================================

resource "kubernetes_storage_class_v1" "general" {
  count = var.cloud_provider == "aws" ? 1 : 0

  metadata {
    name = "general-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = "Delete"
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    type      = "gp3"
    encrypted = "true"
    kmsKeyId  = var.kms_key_id
    fsType    = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.ebs.csi.aws.com/zone"
      values = var.availability_zones
    }
  }
}

# ============================================================================
# AWS S3 Bucket - Backups
# ============================================================================

resource "aws_s3_bucket" "backups" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = "${var.cluster_name}-backups"

  tags = merge(
    var.tags,
    {
      Name    = "${var.cluster_name}-backups"
      Purpose = "Backup storage for JanusGraph Banking Platform"
    }
  )
}

resource "aws_s3_bucket_versioning" "backups" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = aws_s3_bucket.backups[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = aws_s3_bucket.backups[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_id
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = aws_s3_bucket.backups[0].id

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    transition {
      days          = var.backup_transition_days
      storage_class = "GLACIER"
    }

    expiration {
      days = var.backup_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_s3_bucket_public_access_block" "backups" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = aws_s3_bucket.backups[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# AWS S3 Bucket - Snapshots
# ============================================================================

resource "aws_s3_bucket" "snapshots" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = "${var.cluster_name}-snapshots"

  tags = merge(
    var.tags,
    {
      Name    = "${var.cluster_name}-snapshots"
      Purpose = "EBS snapshot storage"
    }
  )
}

resource "aws_s3_bucket_versioning" "snapshots" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = aws_s3_bucket.snapshots[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "snapshots" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = aws_s3_bucket.snapshots[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_id
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "snapshots" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = aws_s3_bucket.snapshots[0].id

  rule {
    id     = "expire-old-snapshots"
    status = "Enabled"

    expiration {
      days = var.snapshot_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

resource "aws_s3_bucket_public_access_block" "snapshots" {
  count = var.cloud_provider == "aws" ? 1 : 0

  bucket = aws_s3_bucket.snapshots[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# AWS IAM Role - Backup Service
# ============================================================================

resource "aws_iam_role" "backup_service" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name_prefix = "${var.cluster_name}-backup-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "backup_service" {
  count = var.cloud_provider == "aws" ? 1 : 0

  role       = aws_iam_role.backup_service[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "backup_restore" {
  count = var.cloud_provider == "aws" ? 1 : 0

  role       = aws_iam_role.backup_service[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

# ============================================================================
# AWS Backup Vault
# ============================================================================

resource "aws_backup_vault" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name        = "${var.cluster_name}-backup-vault"
  kms_key_arn = var.kms_key_arn

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-backup-vault"
    }
  )
}

# ============================================================================
# AWS Backup Plan
# ============================================================================

resource "aws_backup_plan" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name = "${var.cluster_name}-backup-plan"

  # Daily backups
  rule {
    rule_name         = "daily-backups"
    target_vault_name = aws_backup_vault.main[0].name
    schedule          = "cron(0 2 * * ? *)" # 2 AM UTC daily

    lifecycle {
      delete_after = var.backup_retention_days
    }

    recovery_point_tags = merge(
      var.tags,
      {
        Type = "Daily"
      }
    )
  }

  # Weekly backups
  rule {
    rule_name         = "weekly-backups"
    target_vault_name = aws_backup_vault.main[0].name
    schedule          = "cron(0 3 ? * SUN *)" # 3 AM UTC on Sundays

    lifecycle {
      delete_after = var.backup_retention_days * 4 # Keep for 4x daily retention
    }

    recovery_point_tags = merge(
      var.tags,
      {
        Type = "Weekly"
      }
    )
  }

  tags = var.tags
}

# ============================================================================
# AWS Backup Selection
# ============================================================================

resource "aws_backup_selection" "ebs_volumes" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name         = "${var.cluster_name}-ebs-volumes"
  plan_id      = aws_backup_plan.main[0].id
  iam_role_arn = aws_iam_role.backup_service[0].arn

  selection_tag {
    type  = "STRINGEQUALS"
    key   = "kubernetes.io/cluster/${var.cluster_name}"
    value = "owned"
  }

  selection_tag {
    type  = "STRINGEQUALS"
    key   = "backup"
    value = "true"
  }
}

# ============================================================================
# AWS DLM (Data Lifecycle Manager) Policy for EBS Snapshots
# ============================================================================

resource "aws_iam_role" "dlm" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name_prefix = "${var.cluster_name}-dlm-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "dlm.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "dlm" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name_prefix = "${var.cluster_name}-dlm-"
  role        = aws_iam_role.dlm[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateSnapshot",
          "ec2:CreateSnapshots",
          "ec2:DeleteSnapshot",
          "ec2:DescribeInstances",
          "ec2:DescribeVolumes",
          "ec2:DescribeSnapshots",
          "ec2:EnableFastSnapshotRestores",
          "ec2:DescribeFastSnapshotRestores",
          "ec2:DisableFastSnapshotRestores",
          "ec2:CopySnapshot",
          "ec2:ModifySnapshotAttribute",
          "ec2:DescribeSnapshotAttribute"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateTags"
        ]
        Resource = "arn:aws:ec2:*::snapshot/*"
      }
    ]
  })
}

resource "aws_dlm_lifecycle_policy" "ebs_snapshots" {
  count = var.cloud_provider == "aws" ? 1 : 0

  description        = "EBS snapshot lifecycle policy for ${var.cluster_name}"
  execution_role_arn = aws_iam_role.dlm[0].arn
  state              = "ENABLED"

  policy_details {
    resource_types = ["VOLUME"]

    schedule {
      name = "Daily snapshots"

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = ["03:00"]
      }

      retain_rule {
        count = var.snapshot_retention_days
      }

      tags_to_add = merge(
        var.tags,
        {
          SnapshotType = "DLM"
        }
      )

      copy_tags = true
    }

    target_tags = {
      "kubernetes.io/cluster/${var.cluster_name}" = "owned"
      "snapshot"                                   = "true"
    }
  }

  tags = var.tags
}