# Vault Security Review Checklist

**Date:** 2026-02-11  
**Version:** 1.0  
**Phase:** Phase 2 - Infrastructure Security  
**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS

---

## Overview

This checklist provides a comprehensive security review framework for the HashiCorp Vault implementation in the HCD + JanusGraph Banking Compliance Platform.

**Purpose:** Ensure Vault deployment meets enterprise security standards before production use.

---

## 1. Authentication & Authorization

### 1.1 Authentication Methods

- [ ] **Token Authentication (Development Only)**
  - [ ] Root token is NOT used in production
  - [ ] Development tokens have appropriate TTL (< 24 hours)
  - [ ] Token renewal is implemented for long-running processes
  - [ ] Tokens are stored securely (not in code or logs)

- [ ] **AppRole Authentication (Production)**
  - [ ] AppRole is configured for each service
  - [ ] Role IDs are not hardcoded
  - [ ] Secret IDs have appropriate TTL
  - [ ] Secret ID rotation is automated
  - [ ] Bind restrictions are configured (CIDR, secret ID count)

- [ ] **Alternative Methods (If Used)**
  - [ ] Kubernetes auth configured correctly
  - [ ] AWS IAM auth uses least privilege
  - [ ] LDAP/AD integration follows security policies

### 1.2 Authorization Policies

- [ ] **Policy Design**
  - [ ] Least privilege principle applied
  - [ ] Policies are granular (path-specific)
  - [ ] No wildcard policies in production
  - [ ] Policies reviewed and documented
  - [ ] Policy templates exist for common roles

- [ ] **Policy Files**
  - [ ] `config/vault/policies/admin-policy.hcl` reviewed
  - [ ] `config/vault/policies/janusgraph-api-policy.hcl` reviewed
  - [ ] `config/vault/policies/monitoring-policy.hcl` reviewed
  - [ ] All policies follow naming convention
  - [ ] Policies are version controlled

- [ ] **Policy Testing**
  - [ ] Each policy tested with actual service accounts
  - [ ] Negative tests performed (denied access verified)
  - [ ] Policy changes require approval
  - [ ] Policy audit trail maintained

---

## 2. Secret Management

### 2.1 Secret Storage

- [ ] **KV Secrets Engine**
  - [ ] KV v2 is used (versioning enabled)
  - [ ] Mount point is properly configured
  - [ ] Secret versioning is enabled
  - [ ] Version history retention configured
  - [ ] Deleted secrets can be recovered (within retention)

- [ ] **Secret Organization**
  - [ ] Secrets follow consistent path structure
  - [ ] Service-specific paths are isolated
  - [ ] No secrets in root path
  - [ ] Path naming convention documented
  - [ ] Secret metadata is used appropriately

### 2.2 Secret Lifecycle

- [ ] **Creation**
  - [ ] Secrets are never hardcoded
  - [ ] Strong password generation used
  - [ ] Initial secrets populated via secure method
  - [ ] Secret creation is logged
  - [ ] Creation requires appropriate permissions

- [ ] **Rotation**
  - [ ] Rotation schedule defined for each secret type
  - [ ] Automated rotation scripts exist
  - [ ] Zero-downtime rotation procedures documented
  - [ ] Rotation is logged and monitored
  - [ ] Failed rotations trigger alerts

- [ ] **Deletion**
  - [ ] Soft delete is used (recoverable)
  - [ ] Hard delete requires elevated permissions
  - [ ] Deletion is logged
  - [ ] Dependent services notified before deletion
  - [ ] Backup exists before deletion

### 2.3 Secret Access

- [ ] **Access Patterns**
  - [ ] Secrets accessed via VaultClient wrapper
  - [ ] Direct hvac usage is minimized
  - [ ] Secrets are not logged
  - [ ] Secrets are not cached indefinitely
  - [ ] Cache TTL is appropriate (5-15 minutes)

- [ ] **Access Logging**
  - [ ] All secret access is logged
  - [ ] Logs include: who, what, when, result
  - [ ] Failed access attempts are logged
  - [ ] Logs are sent to SIEM
  - [ ] Anomalous access triggers alerts

---

## 3. Network Security

### 3.1 Network Configuration

- [ ] **Vault Server**
  - [ ] Vault runs on dedicated network segment
  - [ ] Firewall rules restrict access to Vault port (8200)
  - [ ] Only authorized services can reach Vault
  - [ ] Network segmentation is enforced
  - [ ] DDoS protection is configured

- [ ] **TLS/SSL**
  - [ ] TLS 1.2+ is enforced
  - [ ] Valid certificates are used (not self-signed in prod)
  - [ ] Certificate expiry monitoring is active
  - [ ] Certificate rotation is automated
  - [ ] Strong cipher suites are configured

### 3.2 API Security

- [ ] **API Endpoints**
  - [ ] Health check endpoint is public (no auth)
  - [ ] All other endpoints require authentication
  - [ ] Rate limiting is configured
  - [ ] Request size limits are enforced
  - [ ] API versioning is used

- [ ] **Client Configuration**
  - [ ] Clients use TLS for all connections
  - [ ] Client certificates are validated
  - [ ] Connection timeouts are configured
  - [ ] Retry logic has exponential backoff
  - [ ] Connection pooling is used appropriately

---

## 4. High Availability & Disaster Recovery

### 4.1 High Availability

- [ ] **Cluster Configuration**
  - [ ] Vault runs in HA mode (3+ nodes)
  - [ ] Raft consensus is properly configured
  - [ ] Leader election works correctly
  - [ ] Failover is tested and documented
  - [ ] Split-brain scenarios are handled

- [ ] **Load Balancing**
  - [ ] Load balancer health checks are configured
  - [ ] Sticky sessions are NOT used
  - [ ] Load balancer logs are monitored
  - [ ] Failover is automatic
  - [ ] Performance is monitored

### 4.2 Backup & Recovery

- [ ] **Backup Strategy**
  - [ ] Automated backups are configured
  - [ ] Backup frequency is appropriate (daily minimum)
  - [ ] Backups are encrypted
  - [ ] Backups are stored off-site
  - [ ] Backup retention policy is defined

- [ ] **Recovery Procedures**
  - [ ] Recovery procedures are documented
  - [ ] Recovery is tested quarterly
  - [ ] RTO/RPO targets are defined and met
  - [ ] Recovery requires multiple approvals
  - [ ] Recovery is logged and audited

---

## 5. Monitoring & Alerting

### 5.1 Metrics Collection

- [ ] **Vault Metrics**
  - [ ] Prometheus exporter is configured
  - [ ] Key metrics are collected:
    - [ ] Request rate
    - [ ] Error rate
    - [ ] Latency (p50, p95, p99)
    - [ ] Token usage
    - [ ] Secret access patterns
  - [ ] Metrics are retained appropriately
  - [ ] Metrics dashboards exist

### 5.2 Alerting

- [ ] **Critical Alerts**
  - [ ] Vault service down
  - [ ] Seal status changed
  - [ ] High error rate (>5%)
  - [ ] Authentication failures spike
  - [ ] Certificate expiring (<30 days)
  - [ ] Backup failures
  - [ ] Unauthorized access attempts

- [ ] **Alert Configuration**
  - [ ] Alerts are sent to appropriate teams
  - [ ] Alert severity is properly classified
  - [ ] Alert fatigue is minimized
  - [ ] Runbooks exist for each alert
  - [ ] Alert response is tracked

### 5.3 Audit Logging

- [ ] **Audit Configuration**
  - [ ] Audit logging is enabled
  - [ ] Audit logs are sent to secure storage
  - [ ] Audit logs are immutable
  - [ ] Audit log retention meets compliance (7+ years)
  - [ ] Audit logs are regularly reviewed

- [ ] **Audit Content**
  - [ ] All authentication attempts logged
  - [ ] All secret access logged
  - [ ] All policy changes logged
  - [ ] All configuration changes logged
  - [ ] Failed operations logged

---

## 6. Compliance & Governance

### 6.1 Compliance Requirements

- [ ] **GDPR**
  - [ ] Data residency requirements met
  - [ ] Right to erasure implemented
  - [ ] Data processing agreements in place
  - [ ] Privacy impact assessment completed

- [ ] **SOC 2**
  - [ ] Access controls documented
  - [ ] Change management process followed
  - [ ] Incident response plan exists
  - [ ] Regular security reviews conducted

- [ ] **PCI DSS (If Applicable)**
  - [ ] Cardholder data is encrypted
  - [ ] Access to secrets is restricted
  - [ ] Audit trails are maintained
  - [ ] Quarterly vulnerability scans performed

### 6.2 Governance

- [ ] **Documentation**
  - [ ] Architecture diagrams are current
  - [ ] Runbooks are complete and tested
  - [ ] Security policies are documented
  - [ ] Change procedures are documented
  - [ ] Training materials exist

- [ ] **Access Management**
  - [ ] Access reviews are quarterly
  - [ ] Least privilege is enforced
  - [ ] Privileged access is logged
  - [ ] Access requests require approval
  - [ ] Access is revoked on termination

---

## 7. Operational Security

### 7.1 Deployment Security

- [ ] **Container Security**
  - [ ] Vault container runs as non-root
  - [ ] Container image is from trusted source
  - [ ] Image vulnerabilities are scanned
  - [ ] Image is regularly updated
  - [ ] Container resources are limited

- [ ] **Configuration Management**
  - [ ] Configuration is version controlled
  - [ ] Secrets are not in configuration files
  - [ ] Configuration changes are reviewed
  - [ ] Configuration is validated before deployment
  - [ ] Rollback procedures exist

### 7.2 Incident Response

- [ ] **Incident Procedures**
  - [ ] Incident response plan exists
  - [ ] Incident severity levels defined
  - [ ] Escalation paths documented
  - [ ] Communication templates prepared
  - [ ] Post-incident reviews conducted

- [ ] **Security Incidents**
  - [ ] Unauthorized access attempts
  - [ ] Credential compromise
  - [ ] Service disruption
  - [ ] Data breach
  - [ ] Policy violations

---

## 8. Client Implementation

### 8.1 VaultClient Wrapper

- [ ] **Code Quality**
  - [ ] Code follows security best practices
  - [ ] No hardcoded credentials
  - [ ] Error handling is comprehensive
  - [ ] Logging does not expose secrets
  - [ ] Type hints are complete

- [ ] **Testing**
  - [ ] Unit tests cover all methods
  - [ ] Integration tests with real Vault
  - [ ] Performance benchmarks exist
  - [ ] Error scenarios are tested
  - [ ] Concurrent access is tested

### 8.2 Caching

- [ ] **Cache Configuration**
  - [ ] Cache TTL is appropriate (5-15 minutes)
  - [ ] Cache invalidation works correctly
  - [ ] Cache size is limited
  - [ ] Cache is thread-safe
  - [ ] Cache metrics are collected

- [ ] **Cache Security**
  - [ ] Cached secrets are in memory only
  - [ ] Cache is cleared on shutdown
  - [ ] Cache is not persisted to disk
  - [ ] Cache access is logged
  - [ ] Cache poisoning is prevented

### 8.3 Retry Logic

- [ ] **Retry Configuration**
  - [ ] Max retries is reasonable (3-5)
  - [ ] Exponential backoff is used
  - [ ] Retry delay is appropriate
  - [ ] Retries are logged
  - [ ] Circuit breaker pattern considered

---

## 9. Integration Points

### 9.1 Service Integration

- [ ] **JanusGraph**
  - [ ] Credentials retrieved from Vault
  - [ ] Connection string uses Vault secrets
  - [ ] Credentials are rotated regularly
  - [ ] Failed auth triggers alert

- [ ] **OpenSearch**
  - [ ] Admin credentials in Vault
  - [ ] API keys in Vault
  - [ ] TLS certificates in Vault
  - [ ] Rotation is automated

- [ ] **HCD/Cassandra**
  - [ ] Superuser credentials in Vault
  - [ ] Application credentials in Vault
  - [ ] JMX credentials in Vault
  - [ ] Keystore passwords in Vault

- [ ] **Monitoring Stack**
  - [ ] Grafana credentials in Vault
  - [ ] Prometheus credentials in Vault
  - [ ] AlertManager credentials in Vault

### 9.2 CI/CD Integration

- [ ] **Pipeline Security**
  - [ ] Vault access in CI/CD is restricted
  - [ ] Short-lived tokens are used
  - [ ] Secrets are not in pipeline logs
  - [ ] Pipeline runs are audited
  - [ ] Failed deployments are investigated

---

## 10. Pre-Production Checklist

### 10.1 Security Testing

- [ ] **Penetration Testing**
  - [ ] External penetration test completed
  - [ ] Internal penetration test completed
  - [ ] Findings remediated
  - [ ] Re-test performed
  - [ ] Report archived

- [ ] **Vulnerability Scanning**
  - [ ] Vault server scanned
  - [ ] Client libraries scanned
  - [ ] Dependencies scanned
  - [ ] Critical vulnerabilities fixed
  - [ ] Scan results documented

### 10.2 Performance Testing

- [ ] **Load Testing**
  - [ ] Expected load tested
  - [ ] Peak load tested (2x expected)
  - [ ] Sustained load tested (24+ hours)
  - [ ] Performance metrics meet SLA
  - [ ] Bottlenecks identified and resolved

### 10.3 Final Review

- [ ] **Documentation Review**
  - [ ] All documentation is current
  - [ ] Runbooks are tested
  - [ ] Training is complete
  - [ ] Handoff to operations complete

- [ ] **Sign-off**
  - [ ] Security team approval
  - [ ] Operations team approval
  - [ ] Compliance team approval
  - [ ] Management approval
  - [ ] Go-live date confirmed

---

## Review History

| Date | Reviewer | Status | Notes |
|------|----------|--------|-------|
| 2026-02-11 | David Leconte | Initial | Checklist created |
| | | | |
| | | | |

---

## References

- [Vault Security Model](https://www.vaultproject.io/docs/internals/security)
- [Vault Production Hardening](https://learn.hashicorp.com/tutorials/vault/production-hardening)
- [SECURITY_REMEDIATION_PLAN_2026-02-11.md](../../SECURITY_REMEDIATION_PLAN_2026-02-11.md)
- [vault_client.py](../../src/python/utils/vault_client.py)

---

**Last Updated:** 2026-02-11  
**Next Review:** 2026-03-11  
**Status:** Active

<!-- Made with Bob -->