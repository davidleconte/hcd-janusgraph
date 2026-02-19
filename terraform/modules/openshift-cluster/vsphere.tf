# VMware vSphere Cluster Configuration
# OpenShift/Kubernetes on vSphere

# vSphere Cluster
resource "vsphere_virtual_machine" "control_plane" {
  count = var.cloud_provider == "vsphere" ? var.vsphere_control_plane_count : 0

  name             = "${var.cluster_name}-control-plane-${count.index + 1}"
  resource_pool_id = data.vsphere_resource_pool.pool[0].id
  datastore_id     = data.vsphere_datastore.datastore[0].id
  folder           = var.vsphere_folder

  num_cpus = var.vsphere_control_plane_cpu
  memory   = var.vsphere_control_plane_memory
  guest_id = data.vsphere_virtual_machine.template[0].guest_id

  scsi_type = data.vsphere_virtual_machine.template[0].scsi_type

  network_interface {
    network_id   = data.vsphere_network.network[0].id
    adapter_type = data.vsphere_virtual_machine.template[0].network_interface_types[0]
  }

  disk {
    label            = "disk0"
    size             = var.vsphere_control_plane_disk_size
    thin_provisioned = true
  }

  clone {
    template_uuid = data.vsphere_virtual_machine.template[0].id

    customize {
      linux_options {
        host_name = "${var.cluster_name}-control-plane-${count.index + 1}"
        domain    = var.vsphere_domain
      }

      network_interface {
        ipv4_address = cidrhost(var.vsphere_network_cidr, 10 + count.index)
        ipv4_netmask = element(split("/", var.vsphere_network_cidr), 1)
      }

      ipv4_gateway    = var.vsphere_gateway
      dns_server_list = var.vsphere_dns_servers
    }
  }

  tags = [for k, v in var.tags : vsphere_tag.tags["${k}:${v}"].id]
}

# Worker Nodes
resource "vsphere_virtual_machine" "worker" {
  count = var.cloud_provider == "vsphere" ? var.node_count : 0

  name             = "${var.cluster_name}-worker-${count.index + 1}"
  resource_pool_id = data.vsphere_resource_pool.pool[0].id
  datastore_id     = data.vsphere_datastore.datastore[0].id
  folder           = var.vsphere_folder

  num_cpus = var.vsphere_worker_cpu
  memory   = var.vsphere_worker_memory
  guest_id = data.vsphere_virtual_machine.template[0].guest_id

  scsi_type = data.vsphere_virtual_machine.template[0].scsi_type

  network_interface {
    network_id   = data.vsphere_network.network[0].id
    adapter_type = data.vsphere_virtual_machine.template[0].network_interface_types[0]
  }

  disk {
    label            = "disk0"
    size             = var.vsphere_worker_disk_size
    thin_provisioned = true
  }

  clone {
    template_uuid = data.vsphere_virtual_machine.template[0].id

    customize {
      linux_options {
        host_name = "${var.cluster_name}-worker-${count.index + 1}"
        domain    = var.vsphere_domain
      }

      network_interface {
        ipv4_address = cidrhost(var.vsphere_network_cidr, 20 + count.index)
        ipv4_netmask = element(split("/", var.vsphere_network_cidr), 1)
      }

      ipv4_gateway    = var.vsphere_gateway
      dns_server_list = var.vsphere_dns_servers
    }
  }

  tags = [for k, v in var.tags : vsphere_tag.tags["${k}:${v}"].id]
}

# HCD Nodes (High-performance nodes for Cassandra/HCD)
resource "vsphere_virtual_machine" "hcd" {
  count = var.cloud_provider == "vsphere" ? var.vsphere_hcd_count : 0

  name             = "${var.cluster_name}-hcd-${count.index + 1}"
  resource_pool_id = data.vsphere_resource_pool.pool[0].id
  datastore_id     = data.vsphere_datastore.datastore[0].id
  folder           = var.vsphere_folder

  num_cpus = var.vsphere_hcd_cpu
  memory   = var.vsphere_hcd_memory
  guest_id = data.vsphere_virtual_machine.template[0].guest_id

  scsi_type = data.vsphere_virtual_machine.template[0].scsi_type

  network_interface {
    network_id   = data.vsphere_network.network[0].id
    adapter_type = data.vsphere_virtual_machine.template[0].network_interface_types[0]
  }

  # OS Disk
  disk {
    label            = "disk0"
    size             = var.vsphere_hcd_disk_size
    thin_provisioned = true
  }

  # Data Disk for HCD
  disk {
    label            = "disk1"
    size             = var.vsphere_hcd_data_disk_size
    thin_provisioned = false
    unit_number      = 1
  }

  clone {
    template_uuid = data.vsphere_virtual_machine.template[0].id

    customize {
      linux_options {
        host_name = "${var.cluster_name}-hcd-${count.index + 1}"
        domain    = var.vsphere_domain
      }

      network_interface {
        ipv4_address = cidrhost(var.vsphere_network_cidr, 30 + count.index)
        ipv4_netmask = element(split("/", var.vsphere_network_cidr), 1)
      }

      ipv4_gateway    = var.vsphere_gateway
      dns_server_list = var.vsphere_dns_servers
    }
  }

  tags = [for k, v in var.tags : vsphere_tag.tags["${k}:${v}"].id]
}

# Data Sources
data "vsphere_datacenter" "dc" {
  count = var.cloud_provider == "vsphere" ? 1 : 0
  name  = var.vsphere_datacenter
}

data "vsphere_datastore" "datastore" {
  count         = var.cloud_provider == "vsphere" ? 1 : 0
  name          = var.vsphere_datastore
  datacenter_id = data.vsphere_datacenter.dc[0].id
}

data "vsphere_resource_pool" "pool" {
  count         = var.cloud_provider == "vsphere" ? 1 : 0
  name          = var.vsphere_resource_pool
  datacenter_id = data.vsphere_datacenter.dc[0].id
}

data "vsphere_network" "network" {
  count         = var.cloud_provider == "vsphere" ? 1 : 0
  name          = var.vsphere_network
  datacenter_id = data.vsphere_datacenter.dc[0].id
}

data "vsphere_virtual_machine" "template" {
  count         = var.cloud_provider == "vsphere" ? 1 : 0
  name          = var.vsphere_template
  datacenter_id = data.vsphere_datacenter.dc[0].id
}

# Tags
resource "vsphere_tag_category" "category" {
  count = var.cloud_provider == "vsphere" ? 1 : 0

  name        = "${var.cluster_name}-category"
  cardinality = "MULTIPLE"
  description = "Tags for ${var.cluster_name}"

  associable_types = [
    "VirtualMachine",
  ]
}

resource "vsphere_tag" "tags" {
  for_each = var.cloud_provider == "vsphere" ? var.tags : {}

  name        = "${each.key}:${each.value}"
  category_id = vsphere_tag_category.category[0].id
  description = "Tag ${each.key}=${each.value}"
}

# Load Balancer VM (HAProxy)
resource "vsphere_virtual_machine" "load_balancer" {
  count = var.cloud_provider == "vsphere" ? 1 : 0

  name             = "${var.cluster_name}-lb"
  resource_pool_id = data.vsphere_resource_pool.pool[0].id
  datastore_id     = data.vsphere_datastore.datastore[0].id
  folder           = var.vsphere_folder

  num_cpus = 2
  memory   = 4096
  guest_id = data.vsphere_virtual_machine.template[0].guest_id

  scsi_type = data.vsphere_virtual_machine.template[0].scsi_type

  network_interface {
    network_id   = data.vsphere_network.network[0].id
    adapter_type = data.vsphere_virtual_machine.template[0].network_interface_types[0]
  }

  disk {
    label            = "disk0"
    size             = 50
    thin_provisioned = true
  }

  clone {
    template_uuid = data.vsphere_virtual_machine.template[0].id

    customize {
      linux_options {
        host_name = "${var.cluster_name}-lb"
        domain    = var.vsphere_domain
      }

      network_interface {
        ipv4_address = cidrhost(var.vsphere_network_cidr, 5)
        ipv4_netmask = element(split("/", var.vsphere_network_cidr), 1)
      }

      ipv4_gateway    = var.vsphere_gateway
      dns_server_list = var.vsphere_dns_servers
    }
  }

  tags = [for k, v in var.tags : vsphere_tag.tags["${k}:${v}"].id]
}

# Outputs
output "vsphere_control_plane_ips" {
  description = "IP addresses of control plane nodes"
  value = var.cloud_provider == "vsphere" ? [
    for vm in vsphere_virtual_machine.control_plane : vm.default_ip_address
  ] : []
}

output "vsphere_worker_ips" {
  description = "IP addresses of worker nodes"
  value = var.cloud_provider == "vsphere" ? [
    for vm in vsphere_virtual_machine.worker : vm.default_ip_address
  ] : []
}

output "vsphere_hcd_ips" {
  description = "IP addresses of HCD nodes"
  value = var.cloud_provider == "vsphere" ? [
    for vm in vsphere_virtual_machine.hcd : vm.default_ip_address
  ] : []
}

output "vsphere_load_balancer_ip" {
  description = "IP address of load balancer"
  value       = var.cloud_provider == "vsphere" && length(vsphere_virtual_machine.load_balancer) > 0 ? vsphere_virtual_machine.load_balancer[0].default_ip_address : null
}