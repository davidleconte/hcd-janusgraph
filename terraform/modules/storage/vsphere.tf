# VMware vSphere Storage Configuration

# vSphere Storage Class for HCD (High Performance)
resource "kubernetes_storage_class_v1" "vsphere_hcd" {
  count = var.cloud_provider == "vsphere" ? 1 : 0

  metadata {
    name = "hcd-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner = "csi.vsphere.vmware.com"
  
  parameters = {
    datastoreurl        = var.vsphere_datastore_url
    storagepolicyname   = var.vsphere_hcd_storage_policy
    fstype              = "ext4"
  }

  reclaim_policy         = "Retain"
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"
}

# vSphere Storage Class for JanusGraph
resource "kubernetes_storage_class_v1" "vsphere_janusgraph" {
  count = var.cloud_provider == "vsphere" ? 1 : 0

  metadata {
    name = "janusgraph-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner = "csi.vsphere.vmware.com"
  
  parameters = {
    datastoreurl        = var.vsphere_datastore_url
    storagepolicyname   = var.vsphere_janusgraph_storage_policy
    fstype              = "ext4"
  }

  reclaim_policy         = "Retain"
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"
}

# vSphere Storage Class for OpenSearch
resource "kubernetes_storage_class_v1" "vsphere_opensearch" {
  count = var.cloud_provider == "vsphere" ? 1 : 0

  metadata {
    name = "opensearch-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner = "csi.vsphere.vmware.com"
  
  parameters = {
    datastoreurl        = var.vsphere_datastore_url
    storagepolicyname   = var.vsphere_opensearch_storage_policy
    fstype              = "ext4"
  }

  reclaim_policy         = "Delete"
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"
}

# vSphere Storage Class for Pulsar
resource "kubernetes_storage_class_v1" "vsphere_pulsar" {
  count = var.cloud_provider == "vsphere" ? 1 : 0

  metadata {
    name = "pulsar-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner = "csi.vsphere.vmware.com"
  
  parameters = {
    datastoreurl        = var.vsphere_datastore_url
    storagepolicyname   = var.vsphere_pulsar_storage_policy
    fstype              = "ext4"
  }

  reclaim_policy         = "Delete"
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"
}

# vSphere Storage Class for General Use (Default)
resource "kubernetes_storage_class_v1" "vsphere_general" {
  count = var.cloud_provider == "vsphere" ? 1 : 0

  metadata {
    name = "vsphere-general"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }

  storage_provisioner = "csi.vsphere.vmware.com"
  
  parameters = {
    datastoreurl        = var.vsphere_datastore_url
    storagepolicyname   = var.vsphere_general_storage_policy
    fstype              = "ext4"
  }

  reclaim_policy         = "Delete"
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"
}

# NFS Storage Class (if using NFS for shared storage)
resource "kubernetes_storage_class_v1" "vsphere_nfs" {
  count = var.cloud_provider == "vsphere" && var.vsphere_enable_nfs ? 1 : 0

  metadata {
    name = "nfs-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner = "nfs.csi.k8s.io"
  
  parameters = {
    server = var.vsphere_nfs_server
    share  = var.vsphere_nfs_share
  }

  reclaim_policy         = "Retain"
  allow_volume_expansion = true
  volume_binding_mode    = "Immediate"
  mount_options          = ["hard", "nfsvers=4.1"]
}

# vSAN Storage Class (if using vSAN)
resource "kubernetes_storage_class_v1" "vsphere_vsan" {
  count = var.cloud_provider == "vsphere" && var.vsphere_enable_vsan ? 1 : 0

  metadata {
    name = "vsan-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner = "csi.vsphere.vmware.com"
  
  parameters = {
    datastoreurl        = var.vsphere_vsan_datastore_url
    storagepolicyname   = var.vsphere_vsan_storage_policy
    fstype              = "ext4"
  }

  reclaim_policy         = "Delete"
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"
}

# Snapshot Class for vSphere
resource "kubernetes_volume_snapshot_class_v1" "vsphere_snapshot" {
  count = var.cloud_provider == "vsphere" ? 1 : 0

  metadata {
    name = "vsphere-snapshot-class"
    annotations = {
      "snapshot.storage.kubernetes.io/is-default-class" = "true"
    }
  }

  driver         = "csi.vsphere.vmware.com"
  deletion_policy = "Delete"
}

# Data Sources
data "vsphere_datacenter" "dc" {
  count = var.cloud_provider == "vsphere" ? 1 : 0
  name  = var.vsphere_datacenter
}

data "vsphere_datastore" "datastore" {
  count         = var.cloud_provider == "vsphere" ? 1 : 0
  name          = var.vsphere_datastore_name
  datacenter_id = data.vsphere_datacenter.dc[0].id
}

# Outputs
output "vsphere_hcd_storage_class" {
  description = "Storage class name for HCD"
  value       = var.cloud_provider == "vsphere" && length(kubernetes_storage_class_v1.vsphere_hcd) > 0 ? kubernetes_storage_class_v1.vsphere_hcd[0].metadata[0].name : null
}

output "vsphere_janusgraph_storage_class" {
  description = "Storage class name for JanusGraph"
  value       = var.cloud_provider == "vsphere" && length(kubernetes_storage_class_v1.vsphere_janusgraph) > 0 ? kubernetes_storage_class_v1.vsphere_janusgraph[0].metadata[0].name : null
}

output "vsphere_opensearch_storage_class" {
  description = "Storage class name for OpenSearch"
  value       = var.cloud_provider == "vsphere" && length(kubernetes_storage_class_v1.vsphere_opensearch) > 0 ? kubernetes_storage_class_v1.vsphere_opensearch[0].metadata[0].name : null
}

output "vsphere_pulsar_storage_class" {
  description = "Storage class name for Pulsar"
  value       = var.cloud_provider == "vsphere" && length(kubernetes_storage_class_v1.vsphere_pulsar) > 0 ? kubernetes_storage_class_v1.vsphere_pulsar[0].metadata[0].name : null
}

output "vsphere_general_storage_class" {
  description = "Storage class name for general use"
  value       = var.cloud_provider == "vsphere" && length(kubernetes_storage_class_v1.vsphere_general) > 0 ? kubernetes_storage_class_v1.vsphere_general[0].metadata[0].name : null
}

output "vsphere_nfs_storage_class" {
  description = "Storage class name for NFS"
  value       = var.cloud_provider == "vsphere" && var.vsphere_enable_nfs && length(kubernetes_storage_class_v1.vsphere_nfs) > 0 ? kubernetes_storage_class_v1.vsphere_nfs[0].metadata[0].name : null
}

output "vsphere_vsan_storage_class" {
  description = "Storage class name for vSAN"
  value       = var.cloud_provider == "vsphere" && var.vsphere_enable_vsan && length(kubernetes_storage_class_v1.vsphere_vsan) > 0 ? kubernetes_storage_class_v1.vsphere_vsan[0].metadata[0].name : null
}

output "vsphere_snapshot_class" {
  description = "Snapshot class name"
  value       = var.cloud_provider == "vsphere" && length(kubernetes_volume_snapshot_class_v1.vsphere_snapshot) > 0 ? kubernetes_volume_snapshot_class_v1.vsphere_snapshot[0].metadata[0].name : null
}

output "vsphere_datastore_url" {
  description = "vSphere datastore URL"
  value       = var.cloud_provider == "vsphere" && length(data.vsphere_datastore.datastore) > 0 ? data.vsphere_datastore.datastore[0].url : null
}