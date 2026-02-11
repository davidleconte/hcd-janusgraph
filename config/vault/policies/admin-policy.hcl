# Vault Policy for Administrative Operations
# Provides full access to janusgraph namespace for credential rotation and management
# 
# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
# Created: 2026-02-11
# Phase: Phase 2 - Infrastructure Security

# Full access to janusgraph secrets
path "janusgraph/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Full access to janusgraph metadata
path "janusgraph/metadata/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Allow token management
path "auth/token/create" {
  capabilities = ["create", "update"]
}

path "auth/token/renew-self" {
  capabilities = ["update"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}

path "auth/token/revoke-self" {
  capabilities = ["update"]
}

# Allow policy management
path "sys/policies/acl/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Allow audit log access
path "sys/audit" {
  capabilities = ["read", "list"]
}

# Allow health checks
path "sys/health" {
  capabilities = ["read"]
}