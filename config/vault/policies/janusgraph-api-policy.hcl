# Vault Policy for JanusGraph API Service
# Provides read-only access to JanusGraph and OpenSearch credentials
# 
# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
# Created: 2026-02-11
# Phase: Phase 2 - Infrastructure Security

# Read JanusGraph admin credentials
path "janusgraph/data/admin" {
  capabilities = ["read"]
}

# Read OpenSearch credentials
path "janusgraph/data/opensearch" {
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

# Allow token lookup (for validation)
path "auth/token/lookup-self" {
  capabilities = ["read"]
}