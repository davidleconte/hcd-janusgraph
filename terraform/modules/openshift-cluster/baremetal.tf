# Bare Metal Cluster Module
# Purpose: Deploy Kubernetes/OpenShift on physical bare metal servers
# Features: PXE boot, IPMI management, node provisioning

# Bare Metal Host Configuration
resource "null_resource" "baremetal_control_plane" {
  count = var.cloud_provider == "baremetal" ? var.baremetal_control_plane_count : 0
  
  triggers = {
    host_id = var.baremetal_control_plane_hosts[count.index].id
  }
  
  # Power on host via IPMI
  provisioner "local-exec" {
    command = <<-EOT
      ipmitool -I lanplus \
        -H ${var.baremetal_control_plane_hosts[count.index].ipmi_address} \
        -U ${var.baremetal_ipmi_user} \
        -P ${var.baremetal_ipmi_password} \
        power on
    EOT
  }
  
  # Wait for PXE boot
  provisioner "local-exec" {
    command = "sleep 60"
  }
  
  # Set boot device to network (PXE)
  provisioner "local-exec" {
    command = <<-EOT
      ipmitool -I lanplus \
        -H ${var.baremetal_control_plane_hosts[count.index].ipmi_address} \
        -U ${var.baremetal_ipmi_user} \
        -P ${var.baremetal_ipmi_password} \
        chassis bootdev pxe options=persistent
    EOT
  }
}

resource "null_resource" "baremetal_worker" {
  count = var.cloud_provider == "baremetal" ? var.baremetal_worker_count : 0
  
  triggers = {
    host_id = var.baremetal_worker_hosts[count.index].id
  }
  
  # Power on host via IPMI
  provisioner "local-exec" {
    command = <<-EOT
      ipmitool -I lanplus \
        -H ${var.baremetal_worker_hosts[count.index].ipmi_address} \
        -U ${var.baremetal_ipmi_user} \
        -P ${var.baremetal_ipmi_password} \
        power on
    EOT
  }
  
  # Wait for PXE boot
  provisioner "local-exec" {
    command = "sleep 60"
  }
  
  # Set boot device to network (PXE)
  provisioner "local-exec" {
    command = <<-EOT
      ipmitool -I lanplus \
        -H ${var.baremetal_worker_hosts[count.index].ipmi_address} \
        -U ${var.baremetal_ipmi_user} \
        -P ${var.baremetal_ipmi_password} \
        chassis bootdev pxe options=persistent
    EOT
  }
}

resource "null_resource" "baremetal_hcd" {
  count = var.cloud_provider == "baremetal" ? var.baremetal_hcd_count : 0
  
  triggers = {
    host_id = var.baremetal_hcd_hosts[count.index].id
  }
  
  # Power on host via IPMI
  provisioner "local-exec" {
    command = <<-EOT
      ipmitool -I lanplus \
        -H ${var.baremetal_hcd_hosts[count.index].ipmi_address} \
        -U ${var.baremetal_ipmi_user} \
        -P ${var.baremetal_ipmi_password} \
        power on
    EOT
  }
  
  # Wait for PXE boot
  provisioner "local-exec" {
    command = "sleep 60"
  }
  
  # Set boot device to network (PXE)
  provisioner "local-exec" {
    command = <<-EOT
      ipmitool -I lanplus \
        -H ${var.baremetal_hcd_hosts[count.index].ipmi_address} \
        -U ${var.baremetal_ipmi_user} \
        -P ${var.baremetal_ipmi_password} \
        chassis bootdev pxe options=persistent
    EOT
  }
}

# Kubernetes Installation (kubeadm)
resource "null_resource" "kubernetes_init" {
  count = var.cloud_provider == "baremetal" ? 1 : 0
  
  depends_on = [
    null_resource.baremetal_control_plane,
    null_resource.baremetal_worker,
    null_resource.baremetal_hcd
  ]
  
  # Wait for all nodes to boot
  provisioner "local-exec" {
    command = "sleep 300"
  }
  
  # Initialize Kubernetes on first control plane node
  provisioner "local-exec" {
    command = <<-EOT
      set -e
      set -o pipefail
      
      ssh -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=30 \
        ${var.baremetal_ssh_user}@${var.baremetal_control_plane_hosts[0].ip_address} \
        'sudo kubeadm init \
          --pod-network-cidr=${var.baremetal_pod_network_cidr} \
          --service-cidr=${var.baremetal_service_cidr} \
          --apiserver-advertise-address=${var.baremetal_control_plane_hosts[0].ip_address}' || {
        echo "ERROR: Failed to initialize Kubernetes cluster"
        exit 1
      }
    EOT
  }
  
  # Copy kubeconfig
  provisioner "local-exec" {
    command = <<-EOT
      set -e
      set -o pipefail
      
      ssh -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=30 \
        ${var.baremetal_ssh_user}@${var.baremetal_control_plane_hosts[0].ip_address} \
        'mkdir -p $HOME/.kube && \
         sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config && \
         sudo chown $(id -u):$(id -g) $HOME/.kube/config' || {
        echo "ERROR: Failed to copy kubeconfig"
        exit 1
      }
    EOT
  }
  
  # Install CNI (Calico)
  provisioner "local-exec" {
    command = <<-EOT
      set -e
      set -o pipefail
      
      CALICO_VERSION="v3.26.1"
      ssh -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=30 \
        ${var.baremetal_ssh_user}@${var.baremetal_control_plane_hosts[0].ip_address} \
        "kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/$CALICO_VERSION/manifests/calico.yaml" || {
        echo "ERROR: Failed to install Calico CNI"
        exit 1
      }
    EOT
  }
}

# Join Worker Nodes
resource "null_resource" "kubernetes_join_workers" {
  count = var.cloud_provider == "baremetal" ? var.baremetal_worker_count : 0
  
  depends_on = [null_resource.kubernetes_init]
  
  # Get join command
  provisioner "local-exec" {
    command = <<-EOT
      set -e
      set -o pipefail
      
      JOIN_CMD=$(ssh -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=30 \
        ${var.baremetal_ssh_user}@${var.baremetal_control_plane_hosts[0].ip_address} \
        'kubeadm token create --print-join-command') || {
        echo "ERROR: Failed to create join command"
        exit 1
      }
      
      ssh -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=30 \
        ${var.baremetal_ssh_user}@${var.baremetal_worker_hosts[count.index].ip_address} \
        "sudo $JOIN_CMD" || {
        echo "ERROR: Failed to join worker node ${var.baremetal_worker_hosts[count.index].hostname}"
        exit 1
      }
    EOT
  }
}

# Join HCD Nodes
resource "null_resource" "kubernetes_join_hcd" {
  count = var.cloud_provider == "baremetal" ? var.baremetal_hcd_count : 0
  
  depends_on = [null_resource.kubernetes_init]
  
  # Get join command
  provisioner "local-exec" {
    command = <<-EOT
      set -e
      set -o pipefail
      
      JOIN_CMD=$(ssh -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=30 \
        ${var.baremetal_ssh_user}@${var.baremetal_control_plane_hosts[0].ip_address} \
        'kubeadm token create --print-join-command') || {
        echo "ERROR: Failed to create join command"
        exit 1
      }
      
      ssh -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=30 \
        ${var.baremetal_ssh_user}@${var.baremetal_hcd_hosts[count.index].ip_address} \
        "sudo $JOIN_CMD" || {
        echo "ERROR: Failed to join HCD node ${var.baremetal_hcd_hosts[count.index].hostname}"
        exit 1
      }
    EOT
  }
  
  # Label HCD nodes
  provisioner "local-exec" {
    command = <<-EOT
      set -e
      set -o pipefail
      
      ssh -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=30 \
        ${var.baremetal_ssh_user}@${var.baremetal_control_plane_hosts[0].ip_address} \
        "kubectl label node ${var.baremetal_hcd_hosts[count.index].hostname} \
          node-role.kubernetes.io/hcd=true \
          workload=hcd" || {
        echo "ERROR: Failed to label HCD node ${var.baremetal_hcd_hosts[count.index].hostname}"
        exit 1
      }
    EOT
  }
}

# MetalLB Load Balancer
resource "null_resource" "metallb_install" {
  count = var.cloud_provider == "baremetal" ? 1 : 0
  
  depends_on = [
    null_resource.kubernetes_join_workers,
    null_resource.kubernetes_join_hcd
  ]
  
  # Install MetalLB
  provisioner "local-exec" {
    command = <<-EOT
      set -e
      set -o pipefail
      
      METALLB_VERSION="v0.13.12"
      ssh -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=30 \
        ${var.baremetal_ssh_user}@${var.baremetal_control_plane_hosts[0].ip_address} \
        "kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/$METALLB_VERSION/config/manifests/metallb-native.yaml" || {
        echo "ERROR: Failed to install MetalLB"
        exit 1
      }
    EOT
  }
  
  # Wait for MetalLB to be ready
  provisioner "local-exec" {
    command = <<-EOT
      set -e
      set -o pipefail
      
      ssh -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=30 \
        ${var.baremetal_ssh_user}@${var.baremetal_control_plane_hosts[0].ip_address} \
        'kubectl wait --namespace metallb-system \
          --for=condition=ready pod \
          --selector=app=metallb \
          --timeout=90s' || {
        echo "ERROR: MetalLB pods did not become ready"
        exit 1
      }
    EOT
  }
}

# MetalLB IP Address Pool
resource "null_resource" "metallb_config" {
  count = var.cloud_provider == "baremetal" ? 1 : 0
  
  depends_on = [null_resource.metallb_install]
  
  # Create IP address pool configuration
  provisioner "local-exec" {
    command = <<-EOT
      set -e
      set -o pipefail
      
      ssh -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=30 \
        ${var.baremetal_ssh_user}@${var.baremetal_control_plane_hosts[0].ip_address} \
        'cat <<EOF | kubectl apply -f - || { echo "ERROR: Failed to configure MetalLB"; exit 1; }
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
  - ${var.baremetal_metallb_ip_range}
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default
  namespace: metallb-system
spec:
  ipAddressPools:
  - default-pool
EOF'
    EOT
  }
}

# Outputs
output "baremetal_control_plane_ips" {
  description = "Control plane node IP addresses"
  value = var.cloud_provider == "baremetal" ? [
    for host in var.baremetal_control_plane_hosts : host.ip_address
  ] : []
}

output "baremetal_worker_ips" {
  description = "Worker node IP addresses"
  value = var.cloud_provider == "baremetal" ? [
    for host in var.baremetal_worker_hosts : host.ip_address
  ] : []
}

output "baremetal_hcd_ips" {
  description = "HCD node IP addresses"
  value = var.cloud_provider == "baremetal" ? [
    for host in var.baremetal_hcd_hosts : host.ip_address
  ] : []
}

output "baremetal_api_endpoint" {
  description = "Kubernetes API endpoint"
  value = var.cloud_provider == "baremetal" ? "https://${var.baremetal_control_plane_hosts[0].ip_address}:6443" : null
}