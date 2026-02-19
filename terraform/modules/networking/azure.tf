# Azure Networking Implementation
# Part of multi-cloud networking module

# ============================================================================
# Azure Virtual Network
# ============================================================================

resource "azurerm_virtual_network" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${var.cluster_name}-vnet"
  location            = var.azure_region
  resource_group_name = var.azure_resource_group_name
  address_space       = [var.vpc_cidr]

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-vnet"
    }
  )
}

# ============================================================================
# Public Subnets
# ============================================================================

resource "azurerm_subnet" "public" {
  count                = var.cloud_provider == "azure" ? length(var.availability_zones) : 0
  name                 = "${var.cluster_name}-public-${count.index}"
  resource_group_name  = var.azure_resource_group_name
  virtual_network_name = azurerm_virtual_network.main[0].name
  address_prefixes     = [cidrsubnet(var.vpc_cidr, 4, count.index)]

  # Service endpoints for Azure services
  service_endpoints = [
    "Microsoft.Storage",
    "Microsoft.KeyVault",
    "Microsoft.ContainerRegistry"
  ]
}

# ============================================================================
# Private Subnets
# ============================================================================

resource "azurerm_subnet" "private" {
  count                = var.cloud_provider == "azure" ? length(var.availability_zones) : 0
  name                 = "${var.cluster_name}-private-${count.index}"
  resource_group_name  = var.azure_resource_group_name
  virtual_network_name = azurerm_virtual_network.main[0].name
  address_prefixes     = [cidrsubnet(var.vpc_cidr, 4, count.index + length(var.availability_zones))]

  # Service endpoints for Azure services
  service_endpoints = [
    "Microsoft.Storage",
    "Microsoft.KeyVault",
    "Microsoft.ContainerRegistry",
    "Microsoft.Sql"
  ]

  # Delegation for AKS
  delegation {
    name = "aks-delegation"

    service_delegation {
      name = "Microsoft.ContainerService/managedClusters"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action"
      ]
    }
  }
}

# ============================================================================
# Public IP for NAT Gateway
# ============================================================================

resource "azurerm_public_ip" "nat" {
  count               = var.cloud_provider == "azure" && var.enable_nat_gateway ? length(var.availability_zones) : 0
  name                = "${var.cluster_name}-nat-ip-${count.index}"
  location            = var.azure_region
  resource_group_name = var.azure_resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = [var.availability_zones[count.index]]

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-nat-ip-${count.index}"
    }
  )
}

# ============================================================================
# NAT Gateway
# ============================================================================

resource "azurerm_nat_gateway" "main" {
  count                   = var.cloud_provider == "azure" && var.enable_nat_gateway ? length(var.availability_zones) : 0
  name                    = "${var.cluster_name}-nat-${count.index}"
  location                = var.azure_region
  resource_group_name     = var.azure_resource_group_name
  sku_name                = "Standard"
  idle_timeout_in_minutes = 10
  zones                   = [var.availability_zones[count.index]]

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-nat-${count.index}"
    }
  )
}

# Associate Public IP with NAT Gateway
resource "azurerm_nat_gateway_public_ip_association" "main" {
  count                = var.cloud_provider == "azure" && var.enable_nat_gateway ? length(var.availability_zones) : 0
  nat_gateway_id       = azurerm_nat_gateway.main[count.index].id
  public_ip_address_id = azurerm_public_ip.nat[count.index].id
}

# Associate NAT Gateway with Private Subnets
resource "azurerm_subnet_nat_gateway_association" "private" {
  count          = var.cloud_provider == "azure" && var.enable_nat_gateway ? length(var.availability_zones) : 0
  subnet_id      = azurerm_subnet.private[count.index].id
  nat_gateway_id = azurerm_nat_gateway.main[count.index].id
}

# ============================================================================
# Network Security Groups
# ============================================================================

# Public Subnet NSG
resource "azurerm_network_security_group" "public" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${var.cluster_name}-public-nsg"
  location            = var.azure_region
  resource_group_name = var.azure_resource_group_name

  # Allow HTTP
  security_rule {
    name                       = "AllowHTTP"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Allow HTTPS
  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-public-nsg"
    }
  )
}

# Private Subnet NSG
resource "azurerm_network_security_group" "private" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${var.cluster_name}-private-nsg"
  location            = var.azure_region
  resource_group_name = var.azure_resource_group_name

  # Allow internal traffic
  security_rule {
    name                       = "AllowVnetInbound"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }

  # Allow Azure Load Balancer
  security_rule {
    name                       = "AllowAzureLoadBalancer"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "AzureLoadBalancer"
    destination_address_prefix = "*"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-private-nsg"
    }
  )
}

# Associate NSG with Public Subnets
resource "azurerm_subnet_network_security_group_association" "public" {
  count                     = var.cloud_provider == "azure" ? length(var.availability_zones) : 0
  subnet_id                 = azurerm_subnet.public[count.index].id
  network_security_group_id = azurerm_network_security_group.public[0].id
}

# Associate NSG with Private Subnets
resource "azurerm_subnet_network_security_group_association" "private" {
  count                     = var.cloud_provider == "azure" ? length(var.availability_zones) : 0
  subnet_id                 = azurerm_subnet.private[count.index].id
  network_security_group_id = azurerm_network_security_group.private[0].id
}

# ============================================================================
# Route Tables
# ============================================================================

# Public Route Table
resource "azurerm_route_table" "public" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${var.cluster_name}-public-rt"
  location            = var.azure_region
  resource_group_name = var.azure_resource_group_name

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-public-rt"
    }
  )
}

# Private Route Table
resource "azurerm_route_table" "private" {
  count               = var.cloud_provider == "azure" ? length(var.availability_zones) : 0
  name                = "${var.cluster_name}-private-rt-${count.index}"
  location            = var.azure_region
  resource_group_name = var.azure_resource_group_name

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-private-rt-${count.index}"
    }
  )
}

# Associate Route Tables with Subnets
resource "azurerm_subnet_route_table_association" "public" {
  count          = var.cloud_provider == "azure" ? length(var.availability_zones) : 0
  subnet_id      = azurerm_subnet.public[count.index].id
  route_table_id = azurerm_route_table.public[0].id
}

resource "azurerm_subnet_route_table_association" "private" {
  count          = var.cloud_provider == "azure" ? length(var.availability_zones) : 0
  subnet_id      = azurerm_subnet.private[count.index].id
  route_table_id = azurerm_route_table.private[count.index].id
}

# ============================================================================
# Load Balancer (for public services)
# ============================================================================

# Public IP for Load Balancer
resource "azurerm_public_ip" "lb" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${var.cluster_name}-lb-ip"
  location            = var.azure_region
  resource_group_name = var.azure_resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-lb-ip"
    }
  )
}

# Load Balancer
resource "azurerm_lb" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${var.cluster_name}-lb"
  location            = var.azure_region
  resource_group_name = var.azure_resource_group_name
  sku                 = "Standard"

  frontend_ip_configuration {
    name                 = "PublicIPAddress"
    public_ip_address_id = azurerm_public_ip.lb[0].id
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-lb"
    }
  )
}

# ============================================================================
# Network Watcher (for flow logs)
# ============================================================================

resource "azurerm_network_watcher_flow_log" "main" {
  count                = var.cloud_provider == "azure" && var.enable_flow_logs ? 1 : 0
  name                 = "${var.cluster_name}-flow-log"
  network_watcher_name = var.azure_network_watcher_name
  resource_group_name  = var.azure_network_watcher_rg
  network_security_group_id = azurerm_network_security_group.private[0].id
  storage_account_id   = var.azure_flow_logs_storage_account_id
  enabled              = true

  retention_policy {
    enabled = true
    days    = var.flow_logs_retention_days
  }

  traffic_analytics {
    enabled               = true
    workspace_id          = var.azure_log_analytics_workspace_id
    workspace_region      = var.azure_region
    workspace_resource_id = var.azure_log_analytics_workspace_resource_id
    interval_in_minutes   = 10
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-flow-log"
    }
  )
}

# ============================================================================
# Private DNS Zone (for private endpoints)
# ============================================================================

resource "azurerm_private_dns_zone" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "privatelink.${var.azure_region}.azmk8s.io"
  resource_group_name = var.azure_resource_group_name

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-private-dns"
    }
  )
}

resource "azurerm_private_dns_zone_virtual_network_link" "main" {
  count                 = var.cloud_provider == "azure" ? 1 : 0
  name                  = "${var.cluster_name}-dns-link"
  resource_group_name   = var.azure_resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.main[0].name
  virtual_network_id    = azurerm_virtual_network.main[0].id

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-dns-link"
    }
  )
}