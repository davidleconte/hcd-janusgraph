# Bare Metal Networking Configuration
# Configures physical network infrastructure for bare metal Kubernetes cluster

# ============================================================================
# Physical Network Configuration
# ============================================================================

# Configure network interfaces on control plane nodes
resource "null_resource" "baremetal_control_plane_network" {
  count = var.cloud_provider == "baremetal" ? var.baremetal_control_plane_count : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_control_plane_hosts[count.index].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  # Configure static IP and network settings
  provisioner "remote-exec" {
    inline = [
      "# Configure network interface",
      "cat > /etc/netplan/01-netcfg.yaml <<EOF",
      "network:",
      "  version: 2",
      "  ethernets:",
      "    eth0:",
      "      addresses:",
      "        - ${var.baremetal_control_plane_hosts[count.index].ip_address}/24",
      "      gateway4: ${var.baremetal_gateway}",
      "      nameservers:",
      "        addresses: [${join(", ", var.baremetal_dns_servers)}]",
      "      dhcp4: no",
      "EOF",
      "",
      "# Apply network configuration",
      "netplan apply",
      "",
      "# Configure hostname",
      "hostnamectl set-hostname ${var.baremetal_control_plane_hosts[count.index].hostname}",
      "",
      "# Update /etc/hosts",
      "echo '${var.baremetal_control_plane_hosts[count.index].ip_address} ${var.baremetal_control_plane_hosts[count.index].hostname}' >> /etc/hosts"
    ]
  }

  depends_on = [null_resource.baremetal_control_plane]
}

# Configure network interfaces on worker nodes
resource "null_resource" "baremetal_worker_network" {
  count = var.cloud_provider == "baremetal" ? var.baremetal_worker_count : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_worker_hosts[count.index].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Configure network interface",
      "cat > /etc/netplan/01-netcfg.yaml <<EOF",
      "network:",
      "  version: 2",
      "  ethernets:",
      "    eth0:",
      "      addresses:",
      "        - ${var.baremetal_worker_hosts[count.index].ip_address}/24",
      "      gateway4: ${var.baremetal_gateway}",
      "      nameservers:",
      "        addresses: [${join(", ", var.baremetal_dns_servers)}]",
      "      dhcp4: no",
      "EOF",
      "",
      "netplan apply",
      "hostnamectl set-hostname ${var.baremetal_worker_hosts[count.index].hostname}",
      "echo '${var.baremetal_worker_hosts[count.index].ip_address} ${var.baremetal_worker_hosts[count.index].hostname}' >> /etc/hosts"
    ]
  }

  depends_on = [null_resource.baremetal_worker]
}

# Configure network interfaces on HCD nodes
resource "null_resource" "baremetal_hcd_network" {
  count = var.cloud_provider == "baremetal" ? var.baremetal_hcd_count : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_hcd_hosts[count.index].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Configure network interface",
      "cat > /etc/netplan/01-netcfg.yaml <<EOF",
      "network:",
      "  version: 2",
      "  ethernets:",
      "    eth0:",
      "      addresses:",
      "        - ${var.baremetal_hcd_hosts[count.index].ip_address}/24",
      "      gateway4: ${var.baremetal_gateway}",
      "      nameservers:",
      "        addresses: [${join(", ", var.baremetal_dns_servers)}]",
      "      dhcp4: no",
      "EOF",
      "",
      "netplan apply",
      "hostnamectl set-hostname ${var.baremetal_hcd_hosts[count.index].hostname}",
      "echo '${var.baremetal_hcd_hosts[count.index].ip_address} ${var.baremetal_hcd_hosts[count.index].hostname}' >> /etc/hosts"
    ]
  }

  depends_on = [null_resource.baremetal_hcd]
}

# ============================================================================
# Network Policies
# ============================================================================

# Configure firewall rules on all nodes
resource "null_resource" "baremetal_firewall_rules" {
  count = var.cloud_provider == "baremetal" ? (
    var.baremetal_control_plane_count + 
    var.baremetal_worker_count + 
    var.baremetal_hcd_count
  ) : 0

  connection {
    type        = "ssh"
    host        = local.baremetal_all_hosts[count.index].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Install and configure firewalld",
      "apt-get update && apt-get install -y firewalld",
      "systemctl enable firewalld",
      "systemctl start firewalld",
      "",
      "# Allow SSH",
      "firewall-cmd --permanent --add-service=ssh",
      "",
      "# Allow Kubernetes API (control plane only)",
      local.baremetal_all_hosts[count.index].role == "control-plane" ? "firewall-cmd --permanent --add-port=6443/tcp" : "# Skip API port",
      "",
      "# Allow etcd (control plane only)",
      local.baremetal_all_hosts[count.index].role == "control-plane" ? "firewall-cmd --permanent --add-port=2379-2380/tcp" : "# Skip etcd ports",
      "",
      "# Allow kubelet",
      "firewall-cmd --permanent --add-port=10250/tcp",
      "",
      "# Allow NodePort services",
      "firewall-cmd --permanent --add-port=30000-32767/tcp",
      "",
      "# Allow Calico BGP",
      "firewall-cmd --permanent --add-port=179/tcp",
      "",
      "# Allow Calico VXLAN",
      "firewall-cmd --permanent --add-port=4789/udp",
      "",
      "# Allow HCD ports (HCD nodes only)",
      local.baremetal_all_hosts[count.index].role == "hcd" ? "firewall-cmd --permanent --add-port=9042/tcp" : "# Skip HCD CQL port",
      local.baremetal_all_hosts[count.index].role == "hcd" ? "firewall-cmd --permanent --add-port=7000-7001/tcp" : "# Skip HCD gossip ports",
      local.baremetal_all_hosts[count.index].role == "hcd" ? "firewall-cmd --permanent --add-port=9160/tcp" : "# Skip HCD Thrift port",
      "",
      "# Reload firewall",
      "firewall-cmd --reload"
    ]
  }

  depends_on = [
    null_resource.baremetal_control_plane_network,
    null_resource.baremetal_worker_network,
    null_resource.baremetal_hcd_network
  ]
}

# ============================================================================
# Load Balancer Configuration (HAProxy + Keepalived)
# ============================================================================

# Install and configure HAProxy on control plane nodes for API load balancing
resource "null_resource" "baremetal_haproxy" {
  count = var.cloud_provider == "baremetal" && var.baremetal_load_balancer_ip != "" ? var.baremetal_control_plane_count : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_control_plane_hosts[count.index].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Install HAProxy",
      "apt-get update && apt-get install -y haproxy",
      "",
      "# Configure HAProxy for Kubernetes API",
      "cat > /etc/haproxy/haproxy.cfg <<EOF",
      "global",
      "    log /dev/log local0",
      "    log /dev/log local1 notice",
      "    chroot /var/lib/haproxy",
      "    stats socket /run/haproxy/admin.sock mode 660 level admin",
      "    stats timeout 30s",
      "    user haproxy",
      "    group haproxy",
      "    daemon",
      "",
      "defaults",
      "    log     global",
      "    mode    tcp",
      "    option  tcplog",
      "    option  dontlognull",
      "    timeout connect 5000",
      "    timeout client  50000",
      "    timeout server  50000",
      "",
      "frontend kubernetes-api",
      "    bind ${var.baremetal_load_balancer_ip}:6443",
      "    mode tcp",
      "    option tcplog",
      "    default_backend kubernetes-api-backend",
      "",
      "backend kubernetes-api-backend",
      "    mode tcp",
      "    option tcp-check",
      "    balance roundrobin",
      join("\n", [for i, host in var.baremetal_control_plane_hosts : 
        "    server ${host.hostname} ${host.ip_address}:6443 check fall 3 rise 2"
      ]),
      "EOF",
      "",
      "# Enable and start HAProxy",
      "systemctl enable haproxy",
      "systemctl restart haproxy"
    ]
  }

  depends_on = [null_resource.baremetal_control_plane_network]
}

# Install and configure Keepalived for VIP management
resource "null_resource" "baremetal_keepalived" {
  count = var.cloud_provider == "baremetal" && var.baremetal_load_balancer_ip != "" ? var.baremetal_control_plane_count : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_control_plane_hosts[count.index].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Install Keepalived",
      "apt-get update && apt-get install -y keepalived",
      "",
      "# Configure Keepalived",
      "cat > /etc/keepalived/keepalived.conf <<EOF",
      "vrrp_script check_haproxy {",
      "    script \"/usr/bin/killall -0 haproxy\"",
      "    interval 2",
      "    weight 2",
      "}",
      "",
      "vrrp_instance VI_1 {",
      "    state ${count.index == 0 ? "MASTER" : "BACKUP"}",
      "    interface eth0",
      "    virtual_router_id 51",
      "    priority ${100 - count.index * 10}",
      "    advert_int 1",
      "    authentication {",
      "        auth_type PASS",
      "        auth_pass ${random_password.keepalived_password.result}",
      "    }",
      "    virtual_ipaddress {",
      "        ${var.baremetal_load_balancer_ip}",
      "    }",
      "    track_script {",
      "        check_haproxy",
      "    }",
      "}",
      "EOF",
      "",
      "# Enable and start Keepalived",
      "systemctl enable keepalived",
      "systemctl restart keepalived"
    ]
  }

  depends_on = [null_resource.baremetal_haproxy]
}

# Generate random password for Keepalived authentication
resource "random_password" "keepalived_password" {
  count   = var.cloud_provider == "baremetal" && var.baremetal_load_balancer_ip != "" ? 1 : 0
  length  = 16
  special = false
}

# ============================================================================
# DNS Configuration
# ============================================================================

# Configure local DNS entries on all nodes
resource "null_resource" "baremetal_dns_config" {
  count = var.cloud_provider == "baremetal" ? (
    var.baremetal_control_plane_count + 
    var.baremetal_worker_count + 
    var.baremetal_hcd_count
  ) : 0

  connection {
    type        = "ssh"
    host        = local.baremetal_all_hosts[count.index].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Add all cluster nodes to /etc/hosts",
      join("\n", concat(
        [for host in var.baremetal_control_plane_hosts : 
          "echo '${host.ip_address} ${host.hostname}.${var.baremetal_domain} ${host.hostname}' >> /etc/hosts"
        ],
        [for host in var.baremetal_worker_hosts : 
          "echo '${host.ip_address} ${host.hostname}.${var.baremetal_domain} ${host.hostname}' >> /etc/hosts"
        ],
        [for host in var.baremetal_hcd_hosts : 
          "echo '${host.ip_address} ${host.hostname}.${var.baremetal_domain} ${host.hostname}' >> /etc/hosts"
        ]
      )),
      "",
      "# Add load balancer VIP if configured",
      var.baremetal_load_balancer_ip != "" ? "echo '${var.baremetal_load_balancer_ip} kubernetes-api.${var.baremetal_domain} kubernetes-api' >> /etc/hosts" : "# No load balancer VIP"
    ]
  }

  depends_on = [
    null_resource.baremetal_control_plane_network,
    null_resource.baremetal_worker_network,
    null_resource.baremetal_hcd_network
  ]
}

# ============================================================================
# Local Variables
# ============================================================================

locals {
  # Combine all hosts for iteration
  baremetal_all_hosts = var.cloud_provider == "baremetal" ? concat(
    [for i, host in var.baremetal_control_plane_hosts : merge(host, { role = "control-plane" })],
    [for i, host in var.baremetal_worker_hosts : merge(host, { role = "worker" })],
    [for i, host in var.baremetal_hcd_hosts : merge(host, { role = "hcd" })]
  ) : []
}

# ============================================================================
# Outputs
# ============================================================================

output "control_plane_ips" {
  description = "IP addresses of control plane nodes"
  value       = var.cloud_provider == "baremetal" ? [for host in var.baremetal_control_plane_hosts : host.ip_address] : []
}

output "worker_ips" {
  description = "IP addresses of worker nodes"
  value       = var.cloud_provider == "baremetal" ? [for host in var.baremetal_worker_hosts : host.ip_address] : []
}

output "hcd_ips" {
  description = "IP addresses of HCD nodes"
  value       = var.cloud_provider == "baremetal" ? [for host in var.baremetal_hcd_hosts : host.ip_address] : []
}

output "load_balancer_ip" {
  description = "Load balancer virtual IP"
  value       = var.cloud_provider == "baremetal" && var.baremetal_load_balancer_ip != "" ? var.baremetal_load_balancer_ip : null
}

output "api_endpoint" {
  description = "Kubernetes API endpoint"
  value       = var.cloud_provider == "baremetal" ? (
    var.baremetal_load_balancer_ip != "" ? 
    "https://${var.baremetal_load_balancer_ip}:6443" : 
    "https://${var.baremetal_control_plane_hosts[0].ip_address}:6443"
  ) : null
}