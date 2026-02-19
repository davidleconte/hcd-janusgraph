# GCP Storage Implementation
# Part of multi-cloud storage module

# ============================================================================
# GCP Persistent Disk StorageClasses
# ============================================================================

# HCD (Cassandra) Storage Class - SSD Persistent Disk
resource "kubernetes_storage_class_v1" "gcp_hcd" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  metadata {
    name = "hcd-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "pd.csi.storage.gke.io"
  reclaim_policy         = var.hcd_reclaim_policy
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    type               = var.gcp_hcd_disk_type  # pd-ssd, pd-balanced, pd-extreme
    replication-type   = "regional-pd"          # Regional for HA
    disk-encryption-kms-key = var.gcp_kms_key_id
    fstype             = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.gke.io/zone"
      values = var.gcp_zones
    }
  }
}

# JanusGraph Storage Class - Balanced Persistent Disk
resource "kubernetes_storage_class_v1" "gcp_janusgraph" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  metadata {
    name = "janusgraph-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "pd.csi.storage.gke.io"
  reclaim_policy         = var.janusgraph_reclaim_policy
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    type               = var.gcp_janusgraph_disk_type
    replication-type   = "regional-pd"
    disk-encryption-kms-key = var.gcp_kms_key_id
    fstype             = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.gke.io/zone"
      values = var.gcp_zones
    }
  }
}

# OpenSearch Storage Class - Balanced Persistent Disk
resource "kubernetes_storage_class_v1" "gcp_opensearch" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  metadata {
    name = "opensearch-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "pd.csi.storage.gke.io"
  reclaim_policy         = var.opensearch_reclaim_policy
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    type               = var.gcp_opensearch_disk_type
    replication-type   = "regional-pd"
    disk-encryption-kms-key = var.gcp_kms_key_id
    fstype             = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.gke.io/zone"
      values = var.gcp_zones
    }
  }
}

# Pulsar Storage Class - SSD Persistent Disk
resource "kubernetes_storage_class_v1" "gcp_pulsar" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  metadata {
    name = "pulsar-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "pd.csi.storage.gke.io"
  reclaim_policy         = var.pulsar_reclaim_policy
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    type               = var.gcp_pulsar_disk_type
    replication-type   = "regional-pd"
    disk-encryption-kms-key = var.gcp_kms_key_id
    fstype             = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.gke.io/zone"
      values = var.gcp_zones
    }
  }
}

# Mission Control Storage Class - Balanced Persistent Disk
resource "kubernetes_storage_class_v1" "gcp_mission_control" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  metadata {
    name = "mission-control-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "pd.csi.storage.gke.io"
  reclaim_policy         = "Retain"
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    type               = "pd-balanced"
    replication-type   = "regional-pd"
    disk-encryption-kms-key = var.gcp_kms_key_id
    fstype             = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.gke.io/zone"
      values = var.gcp_zones
    }
  }
}

# General Purpose Storage Class (Default) - Balanced Persistent Disk
resource "kubernetes_storage_class_v1" "gcp_general" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  metadata {
    name = "general-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }

  storage_provisioner    = "pd.csi.storage.gke.io"
  reclaim_policy         = "Delete"
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    type               = "pd-balanced"
    replication-type   = "none"  # Zonal for general purpose
    disk-encryption-kms-key = var.gcp_kms_key_id
    fstype             = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.gke.io/zone"
      values = var.gcp_zones
    }
  }
}

# ============================================================================
# GCS Bucket - Backups
# ============================================================================

resource "google_storage_bucket" "backups" {
  count         = var.cloud_provider == "gcp" ? 1 : 0
  name          = "${var.cluster_name}-backups"
  project       = var.gcp_project_id
  location      = var.gcp_region
  storage_class = "STANDARD"
  
  # Versioning
  versioning {
    enabled = true
  }
  
  # Encryption
  encryption {
    default_kms_key_name = var.gcp_kms_key_id
  }
  
  # Lifecycle rules
  lifecycle_rule {
    condition {
      age = var.backup_transition_days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
  
  lifecycle_rule {
    condition {
      age = var.backup_retention_days
    }
    action {
      type = "Delete"
    }
  }
  
  lifecycle_rule {
    condition {
      num_newer_versions = 3
    }
    action {
      type = "Delete"
    }
  }
  
  # Security
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  
  labels = merge(
    var.tags,
    {
      name    = "${var.cluster_name}-backups"
      purpose = "backup-storage"
    }
  )
}

# ============================================================================
# GCS Bucket - Snapshots
# ============================================================================

resource "google_storage_bucket" "snapshots" {
  count         = var.cloud_provider == "gcp" ? 1 : 0
  name          = "${var.cluster_name}-snapshots"
  project       = var.gcp_project_id
  location      = var.gcp_region
  storage_class = "STANDARD"
  
  # Versioning
  versioning {
    enabled = true
  }
  
  # Encryption
  encryption {
    default_kms_key_name = var.gcp_kms_key_id
  }
  
  # Lifecycle rules
  lifecycle_rule {
    condition {
      age = var.snapshot_retention_days
    }
    action {
      type = "Delete"
    }
  }
  
  lifecycle_rule {
    condition {
      num_newer_versions = 2
    }
    action {
      type = "Delete"
    }
  }
  
  # Security
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  
  labels = merge(
    var.tags,
    {
      name    = "${var.cluster_name}-snapshots"
      purpose = "snapshot-storage"
    }
  )
}

# ============================================================================
# Persistent Disk Snapshot Schedule
# ============================================================================

resource "google_compute_resource_policy" "snapshot_schedule" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  name    = "${var.cluster_name}-snapshot-schedule"
  project = var.gcp_project_id
  region  = var.gcp_region

  snapshot_schedule_policy {
    schedule {
      daily_schedule {
        days_in_cycle = 1
        start_time    = "03:00"  # 3 AM UTC
      }
    }

    retention_policy {
      max_retention_days    = var.snapshot_retention_days
      on_source_disk_delete = "KEEP_AUTO_SNAPSHOTS"
    }

    snapshot_properties {
      labels = merge(
        var.tags,
        {
          snapshot-type = "automated"
        }
      )
      storage_locations = [var.gcp_region]
      guest_flush       = false
    }
  }
}

# ============================================================================
# IAM Service Account for Backups
# ============================================================================

resource "google_service_account" "backup" {
  count        = var.cloud_provider == "gcp" ? 1 : 0
  account_id   = "${var.cluster_name}-backup"
  display_name = "Service Account for ${var.cluster_name} backups"
  project      = var.gcp_project_id
}

# Grant backup service account access to GCS buckets
resource "google_storage_bucket_iam_member" "backup_backups" {
  count  = var.cloud_provider == "gcp" ? 1 : 0
  bucket = google_storage_bucket.backups[0].name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backup[0].email}"
}

resource "google_storage_bucket_iam_member" "backup_snapshots" {
  count  = var.cloud_provider == "gcp" ? 1 : 0
  bucket = google_storage_bucket.snapshots[0].name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backup[0].email}"
}

# Grant backup service account snapshot permissions
resource "google_project_iam_member" "backup_snapshot_creator" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  project = var.gcp_project_id
  role    = "roles/compute.storageAdmin"
  member  = "serviceAccount:${google_service_account.backup[0].email}"
}

# ============================================================================
# Cloud Scheduler for Backup Jobs
# ============================================================================

resource "google_cloud_scheduler_job" "daily_backup" {
  count       = var.cloud_provider == "gcp" ? 1 : 0
  name        = "${var.cluster_name}-daily-backup"
  project     = var.gcp_project_id
  region      = var.gcp_region
  description = "Daily backup job for ${var.cluster_name}"
  schedule    = "0 2 * * *"  # 2 AM UTC daily
  time_zone   = "UTC"

  http_target {
    http_method = "POST"
    uri         = "https://backup.googleapis.com/v1/projects/${var.gcp_project_id}/locations/${var.gcp_region}/backupPlans/${var.cluster_name}-backup-plan:run"
    
    oauth_token {
      service_account_email = google_service_account.backup[0].email
    }
  }
}

resource "google_cloud_scheduler_job" "weekly_backup" {
  count       = var.cloud_provider == "gcp" ? 1 : 0
  name        = "${var.cluster_name}-weekly-backup"
  project     = var.gcp_project_id
  region      = var.gcp_region
  description = "Weekly backup job for ${var.cluster_name}"
  schedule    = "0 3 * * 0"  # 3 AM UTC on Sundays
  time_zone   = "UTC"

  http_target {
    http_method = "POST"
    uri         = "https://backup.googleapis.com/v1/projects/${var.gcp_project_id}/locations/${var.gcp_region}/backupPlans/${var.cluster_name}-backup-plan:run"
    
    oauth_token {
      service_account_email = google_service_account.backup[0].email
    }
  }
}