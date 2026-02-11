# Vault Agent Configuration for Docker Compose Integration
# This configuration enables automatic secret injection into containers

pid_file = "/var/run/vault-agent.pid"

vault {
  address = "http://vault-server:8200"
  retry {
    num_retries = 5
  }
}

auto_auth {
  method {
    type = "approle"
    
    config = {
      role_id_file_path = "/vault/config/role-id"
      secret_id_file_path = "/vault/config/secret-id"
      remove_secret_id_file_after_reading = false
    }
  }

  sink {
    type = "file"
    config = {
      path = "/vault/token"
      mode = 0640
    }
  }
}

# Template for JanusGraph credentials
template {
  source      = "/vault/templates/janusgraph-credentials.tpl"
  destination = "/vault/secrets/janusgraph-credentials.properties"
  perms       = "0640"
  command     = "pkill -HUP janusgraph || true"
}

# Template for OpenSearch credentials
template {
  source      = "/vault/templates/opensearch-credentials.tpl"
  destination = "/vault/secrets/opensearch-credentials.yml"
  perms       = "0640"
  command     = "curl -X POST http://opensearch:9200/_nodes/reload_secure_settings || true"
}

# Template for Grafana credentials
template {
  source      = "/vault/templates/grafana-credentials.tpl"
  destination = "/vault/secrets/grafana-credentials.ini"
  perms       = "0640"
  command     = "pkill -HUP grafana-server || true"
}

# Template for Pulsar credentials
template {
  source      = "/vault/templates/pulsar-credentials.tpl"
  destination = "/vault/secrets/pulsar-credentials.conf"
  perms       = "0640"
  command     = "pkill -HUP pulsar || true"
}

# Template for environment variables
template {
  source      = "/vault/templates/env-vars.tpl"
  destination = "/vault/secrets/env-vars.sh"
  perms       = "0640"
}