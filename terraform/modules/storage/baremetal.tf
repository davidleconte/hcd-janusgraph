# Bare Metal Storage Configuration
# Configures Ceph distributed storage and NFS for bare metal Kubernetes cluster

# ============================================================================
# Ceph Distributed Storage
# ============================================================================

# Install Ceph on HCD nodes (used as storage nodes)
resource "null_resource" "baremetal_ceph_install" {
  count = var.cloud_provider == "baremetal" ? var.baremetal_hcd_count : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_hcd_hosts[count.index].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Install Ceph packages",
      "apt-get update",
      "apt-get install -y ceph ceph-common ceph-mds",
      "",
      "# Create Ceph directories",
      "mkdir -p /var/lib/ceph/mon /var/lib/ceph/osd /var/lib/ceph/mds",
      "mkdir -p /etc/ceph"
    ]
  }

  # Note: Assumes networking module has been applied
  # depends_on should reference networking module outputs if needed
  depends_on = []
}

# Initialize Ceph cluster on first HCD node
resource "null_resource" "baremetal_ceph_init" {
  count = var.cloud_provider == "baremetal" ? 1 : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_hcd_hosts[0].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Generate Ceph cluster UUID",
      "CLUSTER_UUID=$(uuidgen)",
      "",
      "# Create Ceph configuration",
      "cat > /etc/ceph/ceph.conf <<EOF",
      "[global]",
      "fsid = $CLUSTER_UUID",
      "mon initial members = ${join(", ", [for host in var.baremetal_hcd_hosts : host.hostname])}",
      "mon host = ${join(", ", [for host in var.baremetal_hcd_hosts : host.ip_address])}",
      "public network = ${var.baremetal_hcd_cidr}",
      "cluster network = ${var.baremetal_hcd_cidr}",
      "auth cluster required = cephx",
      "auth service required = cephx",
      "auth client required = cephx",
      "osd journal size = 1024",
      "osd pool default size = 3",
      "osd pool default min size = 2",
      "osd pool default pg num = 128",
      "osd pool default pgp num = 128",
      "osd crush chooseleaf type = 1",
      "",
      "[mon]",
      "mon allow pool delete = true",
      "",
      "[osd]",
      "osd mkfs type = xfs",
      "osd mkfs options xfs = -f -i size=2048",
      "osd mount options xfs = noatime,largeio,inode64,swalloc",
      "EOF",
      "",
      "# Create monitor keyring",
      "ceph-authtool --create-keyring /tmp/ceph.mon.keyring --gen-key -n mon. --cap mon 'allow *'",
      "",
      "# Create admin keyring",
      "ceph-authtool --create-keyring /etc/ceph/ceph.client.admin.keyring --gen-key -n client.admin --cap mon 'allow *' --cap osd 'allow *' --cap mds 'allow *' --cap mgr 'allow *'",
      "",
      "# Create bootstrap OSD keyring",
      "ceph-authtool --create-keyring /var/lib/ceph/bootstrap-osd/ceph.keyring --gen-key -n client.bootstrap-osd --cap mon 'profile bootstrap-osd' --cap mgr 'allow r'",
      "",
      "# Add keyrings to monitor keyring",
      "ceph-authtool /tmp/ceph.mon.keyring --import-keyring /etc/ceph/ceph.client.admin.keyring",
      "ceph-authtool /tmp/ceph.mon.keyring --import-keyring /var/lib/ceph/bootstrap-osd/ceph.keyring",
      "",
      "# Generate monitor map",
      "monmaptool --create --add ${var.baremetal_hcd_hosts[0].hostname} ${var.baremetal_hcd_hosts[0].ip_address} --fsid $CLUSTER_UUID /tmp/monmap",
      "",
      "# Populate monitor daemon",
      "mkdir -p /var/lib/ceph/mon/ceph-${var.baremetal_hcd_hosts[0].hostname}",
      "ceph-mon --mkfs -i ${var.baremetal_hcd_hosts[0].hostname} --monmap /tmp/monmap --keyring /tmp/ceph.mon.keyring",
      "",
      "# Start monitor",
      "systemctl enable ceph-mon@${var.baremetal_hcd_hosts[0].hostname}",
      "systemctl start ceph-mon@${var.baremetal_hcd_hosts[0].hostname}",
      "",
      "# Enable msgr2 protocol",
      "ceph mon enable-msgr2",
      "",
      "# Create manager daemon",
      "mkdir -p /var/lib/ceph/mgr/ceph-${var.baremetal_hcd_hosts[0].hostname}",
      "ceph auth get-or-create mgr.${var.baremetal_hcd_hosts[0].hostname} mon 'allow profile mgr' osd 'allow *' mds 'allow *' > /var/lib/ceph/mgr/ceph-${var.baremetal_hcd_hosts[0].hostname}/keyring",
      "",
      "# Start manager",
      "systemctl enable ceph-mgr@${var.baremetal_hcd_hosts[0].hostname}",
      "systemctl start ceph-mgr@${var.baremetal_hcd_hosts[0].hostname}"
    ]
  }

  depends_on = [null_resource.baremetal_ceph_install]
}

# Add additional monitor nodes
resource "null_resource" "baremetal_ceph_mon_add" {
  count = var.cloud_provider == "baremetal" ? var.baremetal_hcd_count - 1 : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_hcd_hosts[count.index + 1].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Copy Ceph configuration from first node",
      "scp ${var.baremetal_ssh_user}@${var.baremetal_hcd_hosts[0].ip_address}:/etc/ceph/ceph.conf /etc/ceph/",
      "scp ${var.baremetal_ssh_user}@${var.baremetal_hcd_hosts[0].ip_address}:/etc/ceph/ceph.client.admin.keyring /etc/ceph/",
      "scp ${var.baremetal_ssh_user}@${var.baremetal_hcd_hosts[0].ip_address}:/tmp/ceph.mon.keyring /tmp/",
      "",
      "# Get monitor map",
      "ceph mon getmap -o /tmp/monmap",
      "",
      "# Populate monitor daemon",
      "mkdir -p /var/lib/ceph/mon/ceph-${var.baremetal_hcd_hosts[count.index + 1].hostname}",
      "ceph-mon --mkfs -i ${var.baremetal_hcd_hosts[count.index + 1].hostname} --monmap /tmp/monmap --keyring /tmp/ceph.mon.keyring",
      "",
      "# Start monitor",
      "systemctl enable ceph-mon@${var.baremetal_hcd_hosts[count.index + 1].hostname}",
      "systemctl start ceph-mon@${var.baremetal_hcd_hosts[count.index + 1].hostname}",
      "",
      "# Create manager daemon",
      "mkdir -p /var/lib/ceph/mgr/ceph-${var.baremetal_hcd_hosts[count.index + 1].hostname}",
      "ceph auth get-or-create mgr.${var.baremetal_hcd_hosts[count.index + 1].hostname} mon 'allow profile mgr' osd 'allow *' mds 'allow *' > /var/lib/ceph/mgr/ceph-${var.baremetal_hcd_hosts[count.index + 1].hostname}/keyring",
      "",
      "# Start manager",
      "systemctl enable ceph-mgr@${var.baremetal_hcd_hosts[count.index + 1].hostname}",
      "systemctl start ceph-mgr@${var.baremetal_hcd_hosts[count.index + 1].hostname}"
    ]
  }

  depends_on = [null_resource.baremetal_ceph_init]
}

# Create OSDs on data disks
resource "null_resource" "baremetal_ceph_osd" {
  count = var.cloud_provider == "baremetal" ? var.baremetal_hcd_count : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_hcd_hosts[count.index].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "set -e",  # Exit on error
      "set -o pipefail",  # Catch errors in pipes
      "",
      "# Prepare data disk with idempotency checks",
      "DISK_DEVICE='${var.baremetal_hcd_data_disk}'",
      "PARTITION=\"$${DISK_DEVICE}1\"",
      "",
      "# Check if disk is already partitioned",
      "if ! parted $DISK_DEVICE print 2>/dev/null | grep -q 'Partition Table: gpt'; then",
      "  echo 'Creating GPT partition table on $DISK_DEVICE...'",
      "  parted -s $DISK_DEVICE mklabel gpt || { echo 'ERROR: Failed to create partition table'; exit 1; }",
      "  parted -s $DISK_DEVICE mkpart primary xfs 0% 100% || { echo 'ERROR: Failed to create partition'; exit 1; }",
      "  ",
      "  # Wait for partition to be recognized",
      "  sleep 2",
      "  partprobe $DISK_DEVICE",
      "  sleep 2",
      "  ",
      "  # Format partition",
      "  mkfs.xfs -f $PARTITION || { echo 'ERROR: Failed to format partition'; exit 1; }",
      "else",
      "  echo 'Disk $DISK_DEVICE already partitioned, skipping...'",
      "fi",
      "",
      "# Create OSD with idempotency",
      "OSD_ID=$(ceph osd create) || { echo 'ERROR: Failed to create OSD'; exit 1; }",
      "OSD_DIR=\"/var/lib/ceph/osd/ceph-$OSD_ID\"",
      "",
      "# Check if OSD directory already exists and is mounted",
      "if ! mountpoint -q $OSD_DIR; then",
      "  mkdir -p $OSD_DIR",
      "  mount $PARTITION $OSD_DIR || { echo 'ERROR: Failed to mount OSD'; exit 1; }",
      "  ",
      "  # Initialize OSD",
      "  ceph-osd -i $OSD_ID --mkfs --mkkey || { echo 'ERROR: Failed to initialize OSD'; exit 1; }",
      "  ",
      "  # Register OSD",
      "  ceph auth add osd.$OSD_ID osd 'allow *' mon 'allow profile osd' -i $OSD_DIR/keyring || { echo 'ERROR: Failed to register OSD'; exit 1; }",
      "  ",
      "  # Add to CRUSH map (idempotent)",
      "  if ! ceph osd crush dump | grep -q '\"name\": \"${var.baremetal_hcd_hosts[count.index].hostname}\"'; then",
      "    ceph osd crush add-bucket ${var.baremetal_hcd_hosts[count.index].hostname} host || true",
      "  fi",
      "  ceph osd crush move ${var.baremetal_hcd_hosts[count.index].hostname} root=default || true",
      "  ceph osd crush add osd.$OSD_ID 1.0 host=${var.baremetal_hcd_hosts[count.index].hostname} || { echo 'ERROR: Failed to add OSD to CRUSH map'; exit 1; }",
      "  ",
      "  # Add to fstab if not already present",
      "  if ! grep -q \"$PARTITION\" /etc/fstab; then",
      "    echo \"$PARTITION $OSD_DIR xfs defaults 0 0\" >> /etc/fstab",
      "  fi",
      "  ",
      "  # Start OSD",
      "  systemctl enable ceph-osd@$OSD_ID || { echo 'ERROR: Failed to enable OSD service'; exit 1; }",
      "  systemctl start ceph-osd@$OSD_ID || { echo 'ERROR: Failed to start OSD service'; exit 1; }",
      "else",
      "  echo 'OSD $OSD_ID already mounted and running, skipping...'",
      "fi"
    ]
  }

  depends_on = [null_resource.baremetal_ceph_mon_add]
}

# Create Ceph pools for different workloads
resource "null_resource" "baremetal_ceph_pools" {
  count = var.cloud_provider == "baremetal" ? 1 : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_hcd_hosts[0].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Wait for OSDs to be up",
      "sleep 30",
      "",
      "# Create RBD pool for block storage",
      "ceph osd pool create rbd 128 128",
      "ceph osd pool application enable rbd rbd",
      "rbd pool init rbd",
      "",
      "# Create CephFS pools",
      "ceph osd pool create cephfs_data 128 128",
      "ceph osd pool create cephfs_metadata 64 64",
      "ceph fs new cephfs cephfs_metadata cephfs_data",
      "",
      "# Create pool for HCD data",
      "ceph osd pool create hcd-data 256 256",
      "ceph osd pool application enable hcd-data rbd",
      "",
      "# Create pool for JanusGraph data",
      "ceph osd pool create janusgraph-data 128 128",
      "ceph osd pool application enable janusgraph-data rbd",
      "",
      "# Create pool for OpenSearch data",
      "ceph osd pool create opensearch-data 128 128",
      "ceph osd pool application enable opensearch-data rbd",
      "",
      "# Create pool for Pulsar data",
      "ceph osd pool create pulsar-data 128 128",
      "ceph osd pool application enable pulsar-data rbd",
      "",
      "# Create pool for general workloads",
      "ceph osd pool create general 64 64",
      "ceph osd pool application enable general rbd"
    ]
  }

  depends_on = [null_resource.baremetal_ceph_osd]
}

# ============================================================================
# Rook-Ceph Operator for Kubernetes Integration
# ============================================================================

# Deploy Rook-Ceph operator
resource "null_resource" "baremetal_rook_operator" {
  count = var.cloud_provider == "baremetal" ? 1 : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_control_plane_hosts[0].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Install Rook-Ceph operator",
      "kubectl create -f https://raw.githubusercontent.com/rook/rook/release-1.12/deploy/examples/crds.yaml",
      "kubectl create -f https://raw.githubusercontent.com/rook/rook/release-1.12/deploy/examples/common.yaml",
      "kubectl create -f https://raw.githubusercontent.com/rook/rook/release-1.12/deploy/examples/operator.yaml",
      "",
      "# Wait for operator to be ready",
      "kubectl wait --for=condition=ready pod -l app=rook-ceph-operator -n rook-ceph --timeout=300s"
    ]
  }

  # Note: Kubernetes init is in cluster module
  # This should be coordinated at environment level
  depends_on = [
    null_resource.baremetal_ceph_pools
  ]
}

# Create Rook-Ceph cluster configuration
resource "null_resource" "baremetal_rook_cluster" {
  count = var.cloud_provider == "baremetal" ? 1 : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_control_plane_hosts[0].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Create Rook-Ceph cluster manifest",
      "cat > /tmp/rook-cluster.yaml <<EOF",
      "apiVersion: ceph.rook.io/v1",
      "kind: CephCluster",
      "metadata:",
      "  name: rook-ceph",
      "  namespace: rook-ceph",
      "spec:",
      "  cephVersion:",
      "    image: quay.io/ceph/ceph:v17.2.6",
      "  dataDirHostPath: /var/lib/rook",
      "  mon:",
      "    count: ${var.baremetal_hcd_count}",
      "    allowMultiplePerNode: false",
      "  mgr:",
      "    count: 2",
      "    allowMultiplePerNode: false",
      "  dashboard:",
      "    enabled: true",
      "    ssl: true",
      "  storage:",
      "    useAllNodes: false",
      "    useAllDevices: false",
      "    nodes:",
      join("\n", [for host in var.baremetal_hcd_hosts : <<-EOT
      "    - name: ${host.hostname}",
      "      devices:",
      "      - name: sdb",
      EOT
      ]),
      "EOF",
      "",
      "# Apply cluster configuration",
      "kubectl apply -f /tmp/rook-cluster.yaml",
      "",
      "# Wait for cluster to be ready",
      "kubectl wait --for=condition=ready cephcluster/rook-ceph -n rook-ceph --timeout=600s"
    ]
  }

  depends_on = [null_resource.baremetal_rook_operator]
}

# ============================================================================
# Storage Classes
# ============================================================================

# Create Kubernetes storage classes
resource "null_resource" "baremetal_storage_classes" {
  count = var.cloud_provider == "baremetal" ? 1 : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_control_plane_hosts[0].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Create storage class manifest",
      "cat > /tmp/storage-classes.yaml <<'EOF'",
      "---",
      "# HCD Storage Class (High Performance)",
      "apiVersion: storage.k8s.io/v1",
      "kind: StorageClass",
      "metadata:",
      "  name: hcd-storage",
      "provisioner: rook-ceph.rbd.csi.ceph.com",
      "parameters:",
      "  clusterID: rook-ceph",
      "  pool: hcd-data",
      "  imageFormat: \"2\"",
      "  imageFeatures: layering",
      "  csi.storage.k8s.io/provisioner-secret-name: rook-csi-rbd-provisioner",
      "  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/controller-expand-secret-name: rook-csi-rbd-provisioner",
      "  csi.storage.k8s.io/controller-expand-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/node-stage-secret-name: rook-csi-rbd-node",
      "  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/fstype: xfs",
      "allowVolumeExpansion: true",
      "reclaimPolicy: Retain",
      "---",
      "# JanusGraph Storage Class",
      "apiVersion: storage.k8s.io/v1",
      "kind: StorageClass",
      "metadata:",
      "  name: janusgraph-storage",
      "provisioner: rook-ceph.rbd.csi.ceph.com",
      "parameters:",
      "  clusterID: rook-ceph",
      "  pool: janusgraph-data",
      "  imageFormat: \"2\"",
      "  imageFeatures: layering",
      "  csi.storage.k8s.io/provisioner-secret-name: rook-csi-rbd-provisioner",
      "  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/controller-expand-secret-name: rook-csi-rbd-provisioner",
      "  csi.storage.k8s.io/controller-expand-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/node-stage-secret-name: rook-csi-rbd-node",
      "  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/fstype: xfs",
      "allowVolumeExpansion: true",
      "reclaimPolicy: Delete",
      "---",
      "# OpenSearch Storage Class",
      "apiVersion: storage.k8s.io/v1",
      "kind: StorageClass",
      "metadata:",
      "  name: opensearch-storage",
      "provisioner: rook-ceph.rbd.csi.ceph.com",
      "parameters:",
      "  clusterID: rook-ceph",
      "  pool: opensearch-data",
      "  imageFormat: \"2\"",
      "  imageFeatures: layering",
      "  csi.storage.k8s.io/provisioner-secret-name: rook-csi-rbd-provisioner",
      "  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/controller-expand-secret-name: rook-csi-rbd-provisioner",
      "  csi.storage.k8s.io/controller-expand-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/node-stage-secret-name: rook-csi-rbd-node",
      "  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/fstype: xfs",
      "allowVolumeExpansion: true",
      "reclaimPolicy: Delete",
      "---",
      "# Pulsar Storage Class",
      "apiVersion: storage.k8s.io/v1",
      "kind: StorageClass",
      "metadata:",
      "  name: pulsar-storage",
      "provisioner: rook-ceph.rbd.csi.ceph.com",
      "parameters:",
      "  clusterID: rook-ceph",
      "  pool: pulsar-data",
      "  imageFormat: \"2\"",
      "  imageFeatures: layering",
      "  csi.storage.k8s.io/provisioner-secret-name: rook-csi-rbd-provisioner",
      "  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/controller-expand-secret-name: rook-csi-rbd-provisioner",
      "  csi.storage.k8s.io/controller-expand-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/node-stage-secret-name: rook-csi-rbd-node",
      "  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/fstype: xfs",
      "allowVolumeExpansion: true",
      "reclaimPolicy: Delete",
      "---",
      "# General Storage Class",
      "apiVersion: storage.k8s.io/v1",
      "kind: StorageClass",
      "metadata:",
      "  name: general-storage",
      "  annotations:",
      "    storageclass.kubernetes.io/is-default-class: \"true\"",
      "provisioner: rook-ceph.rbd.csi.ceph.com",
      "parameters:",
      "  clusterID: rook-ceph",
      "  pool: general",
      "  imageFormat: \"2\"",
      "  imageFeatures: layering",
      "  csi.storage.k8s.io/provisioner-secret-name: rook-csi-rbd-provisioner",
      "  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/controller-expand-secret-name: rook-csi-rbd-provisioner",
      "  csi.storage.k8s.io/controller-expand-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/node-stage-secret-name: rook-csi-rbd-node",
      "  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/fstype: ext4",
      "allowVolumeExpansion: true",
      "reclaimPolicy: Delete",
      "---",
      "# CephFS Storage Class (Shared Filesystem)",
      "apiVersion: storage.k8s.io/v1",
      "kind: StorageClass",
      "metadata:",
      "  name: cephfs-storage",
      "provisioner: rook-ceph.cephfs.csi.ceph.com",
      "parameters:",
      "  clusterID: rook-ceph",
      "  fsName: cephfs",
      "  pool: cephfs_data",
      "  csi.storage.k8s.io/provisioner-secret-name: rook-csi-cephfs-provisioner",
      "  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/controller-expand-secret-name: rook-csi-cephfs-provisioner",
      "  csi.storage.k8s.io/controller-expand-secret-namespace: rook-ceph",
      "  csi.storage.k8s.io/node-stage-secret-name: rook-csi-cephfs-node",
      "  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph",
      "allowVolumeExpansion: true",
      "reclaimPolicy: Delete",
      "EOF",
      "",
      "# Apply storage classes",
      "kubectl apply -f /tmp/storage-classes.yaml"
    ]
  }

  depends_on = [null_resource.baremetal_rook_cluster]
}

# ============================================================================
# NFS Server (Optional - for legacy workloads)
# ============================================================================

# Install NFS server on first control plane node
resource "null_resource" "baremetal_nfs_server" {
  count = var.cloud_provider == "baremetal" && var.baremetal_enable_nfs ? 1 : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_control_plane_hosts[0].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Install NFS server",
      "apt-get update && apt-get install -y nfs-kernel-server",
      "",
      "# Create NFS export directory",
      "mkdir -p /srv/nfs/kubernetes",
      "chown nobody:nogroup /srv/nfs/kubernetes",
      "chmod 777 /srv/nfs/kubernetes",
      "",
      "# Configure NFS exports",
      "cat > /etc/exports <<EOF",
      "/srv/nfs/kubernetes ${var.baremetal_worker_cidr}(rw,sync,no_subtree_check,no_root_squash)",
      "/srv/nfs/kubernetes ${var.baremetal_hcd_cidr}(rw,sync,no_subtree_check,no_root_squash)",
      "EOF",
      "",
      "# Export NFS shares",
      "exportfs -a",
      "",
      "# Enable and start NFS server",
      "systemctl enable nfs-kernel-server",
      "systemctl restart nfs-kernel-server"
    ]
  }

  depends_on = [null_resource.baremetal_control_plane_network]
}

# Deploy NFS provisioner for Kubernetes
resource "null_resource" "baremetal_nfs_provisioner" {
  count = var.cloud_provider == "baremetal" && var.baremetal_enable_nfs ? 1 : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_control_plane_hosts[0].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Install NFS provisioner",
      "helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/",
      "helm repo update",
      "",
      "helm install nfs-provisioner nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \\",
      "  --set nfs.server=${var.baremetal_control_plane_hosts[0].ip_address} \\",
      "  --set nfs.path=/srv/nfs/kubernetes \\",
      "  --set storageClass.name=nfs-storage \\",
      "  --set storageClass.defaultClass=false"
    ]
  }

  # Note: Kubernetes init is in cluster module
  # This should be coordinated at environment level
  depends_on = [
    null_resource.baremetal_nfs_server
  ]
}

# ============================================================================
# Outputs
# ============================================================================

output "ceph_dashboard_url" {
  description = "Ceph dashboard URL"
  value       = var.cloud_provider == "baremetal" ? "https://${var.baremetal_hcd_hosts[0].ip_address}:8443" : null
}

output "storage_classes" {
  description = "Available storage classes"
  value = var.cloud_provider == "baremetal" ? [
    "hcd-storage",
    "janusgraph-storage",
    "opensearch-storage",
    "pulsar-storage",
    "general-storage",
    "cephfs-storage",
    var.baremetal_enable_nfs ? "nfs-storage" : null
  ] : []
}

output "nfs_server" {
  description = "NFS server address"
  value       = var.cloud_provider == "baremetal" && var.baremetal_enable_nfs ? var.baremetal_control_plane_hosts[0].ip_address : null
}