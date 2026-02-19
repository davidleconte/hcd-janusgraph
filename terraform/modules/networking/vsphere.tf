# VMware vSphere Networking Configuration

# Note: vSphere networking is typically pre-configured at the infrastructure level
# This file provides configuration for network-related resources that can be managed via Terraform

# vSphere Distributed Port Group (if using vDS)
resource "vsphere_distributed_port_group" "pg" {
  count                           = var.cloud_provider == "vsphere" && var.vsphere_use_distributed_switch ? 1 : 0
  name                            = "${var.cluster_name}-pg"
  distributed_virtual_switch_uuid = data.vsphere_distributed_virtual_switch.dvs[0].id

  vlan_id = var.vsphere_vlan_id

  active_uplinks  = ["uplink1", "uplink2"]
  standby_uplinks = []

  tags = [for k, v in var.tags : vsphere_tag.tags["${k}:${v}"].id]
}

# Data Sources
data "vsphere_datacenter" "dc" {
  count = var.cloud_provider == "vsphere" ? 1 : 0
  name  = var.vsphere_datacenter
}

data "vsphere_distributed_virtual_switch" "dvs" {
  count         = var.cloud_provider == "vsphere" && var.vsphere_use_distributed_switch ? 1 : 0
  name          = var.vsphere_dvs_name
  datacenter_id = data.vsphere_datacenter.dc[0].id
}

data "vsphere_network" "network" {
  count         = var.cloud_provider == "vsphere" ? 1 : 0
  name          = var.vsphere_network_name
  datacenter_id = data.vsphere_datacenter.dc[0].id
}

# Tags for vSphere resources
resource "vsphere_tag_category" "category" {
  count = var.cloud_provider == "vsphere" ? 1 : 0

  name        = "${var.cluster_name}-network-category"
  cardinality = "MULTIPLE"
  description = "Network tags for ${var.cluster_name}"

  associable_types = [
    "Network",
    "DistributedVirtualPortgroup",
  ]
}

resource "vsphere_tag" "tags" {
  for_each = var.cloud_provider == "vsphere" ? var.tags : {}

  name        = "${each.key}:${each.value}"
  category_id = vsphere_tag_category.category[0].id
  description = "Tag ${each.key}=${each.value}"
}

# Outputs
output "vsphere_network_id" {
  description = "vSphere network ID"
  value       = var.cloud_provider == "vsphere" && length(data.vsphere_network.network) > 0 ? data.vsphere_network.network[0].id : null
}

output "vsphere_network_name" {
  description = "vSphere network name"
  value       = var.cloud_provider == "vsphere" ? var.vsphere_network_name : null
}

output "vsphere_port_group_id" {
  description = "vSphere distributed port group ID"
  value       = var.cloud_provider == "vsphere" && var.vsphere_use_distributed_switch && length(vsphere_distributed_port_group.pg) > 0 ? vsphere_distributed_port_group.pg[0].id : null
}

output "vsphere_datacenter_id" {
  description = "vSphere datacenter ID"
  value       = var.cloud_provider == "vsphere" && length(data.vsphere_datacenter.dc) > 0 ? data.vsphere_datacenter.dc[0].id : null
}