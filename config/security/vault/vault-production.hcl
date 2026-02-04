# Vault Production Configuration
# High Availability with Auto-Unseal
#
# Author: IBM Bob
# Date: 2026-02-04
#
# WARNING: For production, use cloud-based auto-unseal (AWS KMS, Azure Key Vault, etc.)

# Listener configuration with TLS
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_disable   = false
  tls_cert_file = "/vault/certs/vault.crt"
  tls_key_file  = "/vault/certs/vault.key"
  
  # Disable client certificate verification for simplicity
  # Enable in high-security environments
  tls_require_and_verify_client_cert = false
  tls_min_version = "tls12"
}

# Storage backend - Raft for HA (recommended for production)
storage "raft" {
  path    = "/vault/data"
  node_id = "vault_node_1"
  
  # Performance tuning
  performance_multiplier = 1
}

# Cluster configuration for HA
cluster_addr = "https://vault:8201"
api_addr     = "https://vault:8200"

# Disable mlock for containerized deployments
disable_mlock = true

# Telemetry for monitoring
telemetry {
  prometheus_retention_time = "60s"
  disable_hostname          = true
}

# UI enabled for management
ui = true

# Audit logging
# Enable after first unseal with: vault audit enable file file_path=/vault/logs/audit.log
log_level = "info"
log_format = "json"

# Seal configuration - CHANGE THIS FOR PRODUCTION
# Use AWS KMS, Azure Key Vault, GCP KMS, or HSM
# Example AWS KMS auto-unseal:
# seal "awskms" {
#   region     = "us-west-2"
#   kms_key_id = "your-kms-key-id"
# }

# Example Transit auto-unseal (using another Vault):
# seal "transit" {
#   address         = "https://vault.example.com:8200"
#   token           = "vault-token"
#   disable_renewal = "false"
#   key_name        = "autounseal"
#   mount_path      = "transit/"
# }
