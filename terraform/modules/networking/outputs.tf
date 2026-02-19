/**
 * Networking Module Outputs
 * 
 * Cloud-agnostic outputs that work across AWS, Azure, and GCP
 * 
 * Version: 1.0
 * Date: 2026-02-19
 */

# ============================================================================
# VPC/Network Outputs
# ============================================================================

output "vpc_id" {
  description = "ID of the VPC/VNet/Network"
  value = var.cloud_provider == "aws" ? (
    length(aws_vpc.main) > 0 ? aws_vpc.main[0].id : null
  ) : var.cloud_provider == "azure" ? (
    length(azurerm_virtual_network.main) > 0 ? azurerm_virtual_network.main[0].id : null
  ) : var.cloud_provider == "gcp" ? (
    length(google_compute_network.main) > 0 ? google_compute_network.main[0].id : null
  ) : null
}

output "vpc_cidr" {
  description = "CIDR block of the VPC/VNet"
  value       = var.vpc_cidr
}

# ============================================================================
# Subnet Outputs
# ============================================================================

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value = var.cloud_provider == "aws" ? (
    aws_subnet.public[*].id
  ) : var.cloud_provider == "azure" ? (
    azurerm_subnet.public[*].id
  ) : var.cloud_provider == "gcp" ? (
    google_compute_subnetwork.public[*].id
  ) : []
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value = var.cloud_provider == "aws" ? (
    aws_subnet.private[*].id
  ) : var.cloud_provider == "azure" ? (
    azurerm_subnet.private[*].id
  ) : var.cloud_provider == "gcp" ? (
    google_compute_subnetwork.private[*].id
  ) : []
}

output "public_subnet_cidrs" {
  description = "List of public subnet CIDR blocks"
  value = var.cloud_provider == "aws" ? (
    aws_subnet.public[*].cidr_block
  ) : var.cloud_provider == "azure" ? (
    azurerm_subnet.public[*].address_prefixes
  ) : var.cloud_provider == "gcp" ? (
    google_compute_subnetwork.public[*].ip_cidr_range
  ) : []
}

output "private_subnet_cidrs" {
  description = "List of private subnet CIDR blocks"
  value = var.cloud_provider == "aws" ? (
    aws_subnet.private[*].cidr_block
  ) : var.cloud_provider == "azure" ? (
    azurerm_subnet.private[*].address_prefixes
  ) : var.cloud_provider == "gcp" ? (
    google_compute_subnetwork.private[*].ip_cidr_range
  ) : []
}

# ============================================================================
# NAT Gateway Outputs
# ============================================================================

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value = var.cloud_provider == "aws" ? (
    aws_nat_gateway.main[*].id
  ) : var.cloud_provider == "azure" ? (
    azurerm_nat_gateway.main[*].id
  ) : var.cloud_provider == "gcp" ? (
    google_compute_router_nat.main[*].name
  ) : []
}

output "nat_gateway_public_ips" {
  description = "List of NAT Gateway public IPs"
  value = var.cloud_provider == "aws" ? (
    aws_eip.nat[*].public_ip
  ) : var.cloud_provider == "azure" ? (
    azurerm_public_ip.nat[*].ip_address
  ) : var.cloud_provider == "gcp" ? (
    [] # GCP Cloud NAT uses auto-allocated IPs
  ) : []
}

# ============================================================================
# Security Group Outputs (AWS/Azure)
# ============================================================================

output "load_balancer_security_group_id" {
  description = "Security group ID for load balancers (AWS/Azure only)"
  value = var.cloud_provider == "aws" ? (
    length(aws_security_group.load_balancer) > 0 ? aws_security_group.load_balancer[0].id : null
  ) : var.cloud_provider == "azure" ? (
    length(azurerm_network_security_group.public) > 0 ? azurerm_network_security_group.public[0].id : null
  ) : null
}

output "vpc_endpoints_security_group_id" {
  description = "Security group ID for VPC endpoints (AWS only)"
  value = var.cloud_provider == "aws" && var.enable_vpc_endpoints ? (
    length(aws_security_group.vpc_endpoints) > 0 ? aws_security_group.vpc_endpoints[0].id : null
  ) : null
}

# ============================================================================
# Route Table Outputs
# ============================================================================

output "public_route_table_ids" {
  description = "List of public route table IDs"
  value = var.cloud_provider == "aws" ? (
    [aws_route_table.public[0].id]
  ) : var.cloud_provider == "azure" ? (
    [azurerm_route_table.public[0].id]
  ) : var.cloud_provider == "gcp" ? (
    [] # GCP uses implicit routing
  ) : []
}

output "private_route_table_ids" {
  description = "List of private route table IDs"
  value = var.cloud_provider == "aws" ? (
    aws_route_table.private[*].id
  ) : var.cloud_provider == "azure" ? (
    azurerm_route_table.private[*].id
  ) : var.cloud_provider == "gcp" ? (
    [] # GCP uses implicit routing
  ) : []
}

# ============================================================================
# Load Balancer Outputs
# ============================================================================

output "load_balancer_public_ip" {
  description = "Public IP address of the load balancer"
  value = var.cloud_provider == "aws" ? (
    null # AWS ELB IPs are dynamic
  ) : var.cloud_provider == "azure" ? (
    length(azurerm_public_ip.lb) > 0 ? azurerm_public_ip.lb[0].ip_address : null
  ) : var.cloud_provider == "gcp" ? (
    length(google_compute_global_address.lb) > 0 ? google_compute_global_address.lb[0].address : null
  ) : null
}

# ============================================================================
# DNS Outputs
# ============================================================================

output "private_dns_zone_id" {
  description = "ID of the private DNS zone"
  value = var.cloud_provider == "aws" ? (
    null # AWS uses Route53 (not in this module)
  ) : var.cloud_provider == "azure" ? (
    length(azurerm_private_dns_zone.main) > 0 ? azurerm_private_dns_zone.main[0].id : null
  ) : var.cloud_provider == "gcp" ? (
    length(google_dns_managed_zone.private) > 0 ? google_dns_managed_zone.private[0].id : null
  ) : null
}

# ============================================================================
# Flow Logs Outputs
# ============================================================================

output "flow_logs_enabled" {
  description = "Whether VPC flow logs are enabled"
  value       = var.enable_flow_logs
}

output "flow_logs_log_group" {
  description = "CloudWatch log group for flow logs (AWS only)"
  value = var.cloud_provider == "aws" && var.enable_flow_logs ? (
    length(aws_cloudwatch_log_group.flow_logs) > 0 ? aws_cloudwatch_log_group.flow_logs[0].name : null
  ) : null
}

# ============================================================================
# Cloud-Specific Outputs
# ============================================================================

# AWS-specific outputs
output "aws_vpc_id" {
  description = "AWS VPC ID (AWS only)"
  value       = var.cloud_provider == "aws" && length(aws_vpc.main) > 0 ? aws_vpc.main[0].id : null
}

output "aws_internet_gateway_id" {
  description = "AWS Internet Gateway ID (AWS only)"
  value       = var.cloud_provider == "aws" && length(aws_internet_gateway.main) > 0 ? aws_internet_gateway.main[0].id : null
}

# Azure-specific outputs
output "azure_vnet_id" {
  description = "Azure VNet ID (Azure only)"
  value       = var.cloud_provider == "azure" && length(azurerm_virtual_network.main) > 0 ? azurerm_virtual_network.main[0].id : null
}

output "azure_resource_group_name" {
  description = "Azure resource group name (Azure only)"
  value       = var.cloud_provider == "azure" ? var.azure_resource_group_name : null
}

# GCP-specific outputs
output "gcp_network_name" {
  description = "GCP VPC network name (GCP only)"
  value       = var.cloud_provider == "gcp" && length(google_compute_network.main) > 0 ? google_compute_network.main[0].name : null
}

output "gcp_network_self_link" {
  description = "GCP VPC network self link (GCP only)"
  value       = var.cloud_provider == "gcp" && length(google_compute_network.main) > 0 ? google_compute_network.main[0].self_link : null
}