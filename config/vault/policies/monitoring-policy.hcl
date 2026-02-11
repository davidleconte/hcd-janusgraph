# Vault Policy for Monitoring Services (Grafana, Prometheus)
# Provides read-only access to monitoring credentials
# 
# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
# Created: 2026-02-11
# Phase: Phase 2 - Infrastructure Security

# Read Grafana credentials
path "janusgraph/data/grafana" {
  capabilities = ["read"]
}

# Read Prometheus credentials (if needed)
path "janusgraph/data/prometheus" {
  capabilities = ["read"]
}

# List secrets in janusgraph namespace
path "janusgraph/metadata/*" {
  capabilities = ["list"]
}

# Allow token renewal
path "auth/token/renew-self" {
  capabilities = ["update"]
}

# Allow token lookup
path "auth/token/lookup-self" {
  capabilities = ["read"]
}