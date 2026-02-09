# File: config/vault/config.hcl
# Created: 2026-01-28
# Purpose: HashiCorp Vault configuration for secrets management

# Storage backend - file-based for development
storage "file" {
  path = "/vault/file"
}

# Listener configuration
listener "tcp" {
  address = "0.0.0.0:8200"
  tls_disable = 1  # Disable TLS for internal network (enable in production with external access)

  # For production with TLS:
  # tls_disable = 0
  # tls_cert_file = "/vault/certs/vault-cert.pem"
  # tls_key_file = "/vault/certs/vault-key.pem"
}

# API address
api_addr = "http://0.0.0.0:8200"

# UI configuration
ui = true

# Telemetry for monitoring
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}

# Disable mlock for containerized environments
disable_mlock = true

# Log level
log_level = "info"

# Made with Bob
