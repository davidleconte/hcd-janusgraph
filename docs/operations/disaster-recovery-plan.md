# Disaster Recovery Plan (DRP)

**Project**: HCD + JanusGraph Stack  
**Version**: 1.0  
**Date**: 2026-01-28  
**Classification**: CONFIDENTIAL  
**Review Cycle**: Quarterly

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Scope and Objectives](#scope-and-objectives)
3. [Disaster Scenarios](#disaster-scenarios)
4. [Recovery Strategies](#recovery-strategies)
5. [Backup Procedures](#backup-procedures)
6. [Recovery Procedures](#recovery-procedures)
7. [Testing and Maintenance](#testing-and-maintenance)
8. [Roles and Responsibilities](#roles-and-responsibilities)
9. [Contact Information](#contact-information)
10. [Appendices](#appendices)

---

## Executive Summary

This Disaster Recovery Plan (DRP) provides comprehensive procedures for recovering the HCD + JanusGraph graph database stack in the event of a disaster. The plan ensures business continuity with minimal data loss and downtime.

### Key Metrics

| Metric | Target | Current |
|--------|--------|---------|
| **RTO** (Recovery Time Objective) | 4 hours | 2 hours |
| **RPO** (Recovery Point Objective) | 1 hour | 15 minutes |
| **Data Loss Tolerance** | < 1 hour | < 15 minutes |
| **Availability Target** | 99.9% | 99.95% |

### Recovery Priorities

1. **Critical** (P0): HCD cluster, JanusGraph service
2. **High** (P1): Monitoring (Prometheus, Grafana)
3. **Medium** (P2): Logging (Loki, Promtail)
4. **Low** (P3): Visualization tools

---

## Scope and Objectives

### In Scope

- HCD (Cassandra) cluster
- JanusGraph graph database
- Monitoring infrastructure (Prometheus, Grafana)
- Logging infrastructure (Loki, Promtail)
- Network configuration
- Security certificates
- Application data

### Out of Scope

- Development environments
- Test data
- Personal workstations
- Third-party SaaS services

### Objectives

1. Minimize downtime and data loss
2. Ensure data integrity and consistency
3. Maintain security and compliance
4. Document all recovery procedures
5. Test recovery procedures regularly

---

## Disaster Scenarios

### Scenario 1: Single Server Failure

**Probability**: High  
**Impact**: Low  
**RTO**: 30 minutes  
**RPO**: 0 (no data loss)

**Description**: Single server hardware failure or OS crash.

**Recovery Strategy**: Automatic failover to standby node (if HA configured), or manual recovery from backup.

### Scenario 2: Data Center Outage

**Probability**: Medium  
**Impact**: High  
**RTO**: 4 hours  
**RPO**: 15 minutes

**Description**: Complete data center power loss, network failure, or natural disaster.

**Recovery Strategy**: Failover to secondary data center or cloud region.

### Scenario 3: Data Corruption

**Probability**: Low  
**Impact**: Critical  
**RTO**: 2 hours  
**RPO**: 1 hour

**Description**: Database corruption due to software bug, hardware failure, or malicious activity.

**Recovery Strategy**: Restore from last known good backup.

### Scenario 4: Ransomware Attack

**Probability**: Medium  
**Impact**: Critical  
**RTO**: 8 hours  
**RPO**: 1 hour

**Description**: Malware encrypts data and demands ransom.

**Recovery Strategy**: Isolate infected systems, restore from encrypted backups, rebuild infrastructure.

### Scenario 5: Accidental Data Deletion

**Probability**: Medium  
**Impact**: Medium  
**RTO**: 1 hour  
**RPO**: 15 minutes

**Description**: Operator error results in data deletion.

**Recovery Strategy**: Restore specific data from point-in-time backup.

---

## Recovery Strategies

### Strategy 1: High Availability (HA)

**Implementation**: Multi-node cluster with automatic failover

**Components**:
- 3+ node HCD cluster
- Load-balanced JanusGraph instances
- Replicated data (RF=3)

**Advantages**:
- Zero downtime for single node failure
- Automatic recovery
- No data loss

**Disadvantages**:
- Higher infrastructure cost
- Complex configuration

### Strategy 2: Backup and Restore

**Implementation**: Regular encrypted backups to S3

**Components**:
- Automated daily backups
- GPG encryption
- S3 storage with versioning
- 90-day retention

**Advantages**:
- Cost-effective
- Simple to implement
- Off-site storage

**Disadvantages**:
- Downtime during restore
- Potential data loss (RPO)

### Strategy 3: Hybrid Approach (Recommended)

**Implementation**: HA for critical services + backup for disaster recovery

**Components**:
- HA cluster for production
- Automated backups for DR
- Secondary site for failover

**Advantages**:
- Best of both worlds
- Minimal downtime
- Minimal data loss

**Disadvantages**:
- Higher cost
- More complex

---

## Backup Procedures

### Automated Backup Schedule

| Backup Type | Frequency | Retention | Storage |
|-------------|-----------|-----------|---------|
| **Full** | Daily (2 AM) | 30 days | S3 + Local |
| **Incremental** | Every 6 hours | 7 days | S3 |
| **Transaction Logs** | Continuous | 7 days | S3 |
| **Configuration** | On change | 90 days | Git + S3 |

### Backup Script

```bash
#!/bin/bash
# Run encrypted backup
export BACKUP_ENCRYPTION_ENABLED=true
export BACKUP_ENCRYPTION_KEY="your-gpg-key-id"
export AWS_S3_BACKUP_BUCKET="your-backup-bucket"

./scripts/backup/backup_volumes_encrypted.sh
```

### Backup Verification

1. **Automated Verification** (Daily):
   ```bash
   # Verify backup integrity
   gpg --verify backup.tar.gz.gpg.sig backup.tar.gz.gpg
   
   # Test restore to staging
   ./scripts/backup/test_restore.sh --environment staging
   ```

2. **Manual Verification** (Weekly):
   - Restore to test environment
   - Verify data integrity
   - Test application functionality
   - Document results

### Backup Monitoring

- **Alert**: Backup failure
- **Alert**: Backup older than 24 hours
- **Alert**: Backup size anomaly (>20% change)
- **Dashboard**: Backup status and history

---

## Recovery Procedures

### Procedure 1: Recover from Single Node Failure

**Prerequisites**:
- Access to backup storage
- Replacement hardware or VM
- Network connectivity

**Steps**:

1. **Assess Damage** (5 minutes)
   ```bash
   # Check node status
   docker ps -a
   nodetool status
   
   # Check logs
   docker logs hcd-server
   docker logs janusgraph-server
   ```

2. **Isolate Failed Node** (5 minutes)
   ```bash
   # Stop failed services
   docker-compose stop hcd janusgraph
   
   # Remove from cluster (if HA)
   nodetool decommission
   ```

3. **Provision Replacement** (30 minutes)
   ```bash
   # Deploy new node
   docker-compose up -d hcd janusgraph
   
   # Wait for services to start
   ./scripts/deployment/wait_for_services.sh
   ```

4. **Restore Data** (if needed) (60 minutes)
   ```bash
   # Restore from latest backup
   ./scripts/backup/restore_volumes.sh \
     --backup-file s3://bucket/latest-backup.tar.gz.gpg \
     --decrypt
   ```

5. **Verify Recovery** (15 minutes)
   ```bash
   # Run health checks
   ./scripts/testing/run_integration_tests.sh
   
   # Verify data integrity
   ./scripts/maintenance/verify_data_integrity.sh
   ```

6. **Resume Operations** (5 minutes)
   ```bash
   # Update monitoring
   # Notify stakeholders
   # Document incident
   ```

**Total Time**: ~2 hours

### Procedure 2: Recover from Data Center Outage

**Prerequisites**:
- Secondary data center or cloud region
- Recent backups in S3
- DNS/load balancer access

**Steps**:

1. **Declare Disaster** (10 minutes)
   - Assess situation
   - Activate DR team
   - Notify stakeholders

2. **Failover to Secondary Site** (30 minutes)
   ```bash
   # Update DNS to point to secondary site
   aws route53 change-resource-record-sets \
     --hosted-zone-id Z123456 \
     --change-batch file://failover-dns.json
   
   # Start services at secondary site
   ssh dr-site "cd /opt/janusgraph && docker-compose up -d"
   ```

3. **Restore Latest Data** (2 hours)
   ```bash
   # Download latest backup from S3
   aws s3 cp s3://backup-bucket/latest/ /tmp/restore/ --recursive
   
   # Decrypt and restore
   ./scripts/backup/restore_volumes.sh \
     --backup-dir /tmp/restore \
     --decrypt \
     --verify
   ```

4. **Verify Services** (30 minutes)
   ```bash
   # Run comprehensive tests
   ./scripts/testing/run_integration_tests.sh
   
   # Verify data consistency
   ./scripts/maintenance/verify_data_integrity.sh
   
   # Check monitoring
   curl https://grafana.dr-site.com/api/health
   ```

5. **Resume Operations** (30 minutes)
   - Update documentation
   - Notify users
   - Monitor closely

6. **Post-Recovery** (ongoing)
   - Investigate root cause
   - Update DR plan
   - Schedule DR drill

**Total Time**: ~4 hours

### Procedure 3: Recover from Data Corruption

**Prerequisites**:
- Point-in-time backups
- Staging environment for testing
- Data validation scripts

**Steps**:

1. **Identify Corruption** (15 minutes)
   ```bash
   # Check data integrity
   nodetool verify
   
   # Check application logs
   docker logs janusgraph-server | grep -i error
   
   # Identify affected data
   ./scripts/maintenance/identify_corruption.sh
   ```

2. **Isolate Affected Systems** (10 minutes)
   ```bash
   # Stop writes to affected keyspace
   cqlsh -e "ALTER KEYSPACE janusgraph WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 0};"
   
   # Put application in read-only mode
   ./scripts/maintenance/enable_readonly_mode.sh
   ```

3. **Determine Recovery Point** (15 minutes)
   ```bash
   # List available backups
   aws s3 ls s3://backup-bucket/ --recursive
   
   # Identify last known good backup
   ./scripts/backup/find_good_backup.sh \
     --before "2026-01-28 10:00:00"
   ```

4. **Test Restore in Staging** (60 minutes)
   ```bash
   # Restore to staging environment
   ./scripts/backup/restore_volumes.sh \
     --backup-file s3://bucket/backup-20260128-0800.tar.gz.gpg \
     --environment staging \
     --decrypt
   
   # Verify data integrity
   ./scripts/testing/run_integration_tests.sh --environment staging
   ```

5. **Restore to Production** (60 minutes)
   ```bash
   # Stop production services
   docker-compose stop
   
   # Backup current state (for forensics)
   ./scripts/backup/backup_volumes_encrypted.sh --tag corrupted
   
   # Restore from good backup
   ./scripts/backup/restore_volumes.sh \
     --backup-file s3://bucket/backup-20260128-0800.tar.gz.gpg \
     --decrypt \
     --verify
   
   # Start services
   docker-compose up -d
   ```

6. **Verify and Resume** (30 minutes)
   ```bash
   # Run full test suite
   ./scripts/testing/run_integration_tests.sh
   
   # Verify data integrity
   ./scripts/maintenance/verify_data_integrity.sh
   
   # Disable read-only mode
   ./scripts/maintenance/disable_readonly_mode.sh
   
   # Monitor closely
   ```

**Total Time**: ~3 hours

### Procedure 4: Recover from Ransomware Attack

**Prerequisites**:
- Isolated backup storage
- Clean recovery environment
- Incident response team

**Steps**:

1. **Contain the Incident** (30 minutes)
   ```bash
   # Immediately isolate infected systems
   # Disconnect from network
   # Preserve evidence
   
   # Stop all services
   docker-compose down
   
   # Block network access
   iptables -A INPUT -j DROP
   iptables -A OUTPUT -j DROP
   ```

2. **Assess Damage** (60 minutes)
   - Identify infected systems
   - Determine attack vector
   - Check backup integrity
   - Notify authorities (if required)

3. **Prepare Clean Environment** (120 minutes)
   ```bash
   # Provision new infrastructure
   # Install fresh OS
   # Apply security patches
   # Configure firewall rules
   
   # Deploy from clean images
   docker-compose -f docker-compose.yml \
     -f docker-compose.tls.yml \
     -f docker-compose.nginx.yml \
     up -d
   ```

4. **Restore from Backup** (180 minutes)
   ```bash
   # Verify backup is clean (pre-infection)
   ./scripts/security/scan_backup.sh \
     --backup-file s3://bucket/backup-pre-infection.tar.gz.gpg
   
   # Restore to clean environment
   ./scripts/backup/restore_volumes.sh \
     --backup-file s3://bucket/backup-pre-infection.tar.gz.gpg \
     --decrypt \
     --verify \
     --scan-malware
   ```

5. **Harden Security** (60 minutes)
   ```bash
   # Rotate all credentials
   ./scripts/maintenance/rotate_secrets.sh --all
   
   # Update firewall rules
   ./scripts/security/update_firewall.sh
   
   # Enable additional monitoring
   ./scripts/monitoring/enable_enhanced_monitoring.sh
   ```

6. **Verify and Resume** (60 minutes)
   - Run security scans
   - Test all functionality
   - Monitor for re-infection
   - Document incident

**Total Time**: ~8 hours

---

## Testing and Maintenance

### DR Testing Schedule

| Test Type | Frequency | Duration | Participants |
|-----------|-----------|----------|--------------|
| **Backup Verification** | Daily | 30 min | Automated |
| **Restore Test** | Weekly | 2 hours | Ops Team |
| **Partial DR Drill** | Monthly | 4 hours | DR Team |
| **Full DR Drill** | Quarterly | 8 hours | All Teams |
| **Tabletop Exercise** | Semi-annually | 4 hours | Leadership |

### DR Drill Checklist

**Pre-Drill** (1 week before):
- [ ] Schedule drill date/time
- [ ] Notify all participants
- [ ] Prepare test environment
- [ ] Review DR procedures
- [ ] Assign roles

**During Drill**:
- [ ] Simulate disaster scenario
- [ ] Execute recovery procedures
- [ ] Document all actions
- [ ] Time each step
- [ ] Identify issues

**Post-Drill** (within 1 week):
- [ ] Conduct debrief meeting
- [ ] Document lessons learned
- [ ] Update DR plan
- [ ] Address identified gaps
- [ ] Schedule next drill

### Maintenance Tasks

**Monthly**:
- Review and update contact information
- Verify backup integrity
- Test restore procedures
- Update documentation

**Quarterly**:
- Full DR drill
- Review and update RTO/RPO targets
- Audit backup retention
- Update disaster scenarios

**Annually**:
- Comprehensive DR plan review
- Update risk assessment
- Review insurance coverage
- Conduct external audit

---

## Roles and Responsibilities

### DR Team Structure

```
DR Coordinator (Primary)
├── Technical Lead
│   ├── Database Administrator
│   ├── System Administrator
│   └── Network Engineer
├── Security Lead
│   ├── Security Analyst
│   └── Compliance Officer
└── Communications Lead
    ├── Internal Communications
    └── External Communications
```

### Role Definitions

#### DR Coordinator
- **Primary**: John Doe (john.doe@company.com, +1-555-0100)
- **Backup**: Jane Smith (jane.smith@company.com, +1-555-0101)

**Responsibilities**:
- Declare disaster
- Activate DR team
- Coordinate recovery efforts
- Communicate with stakeholders
- Make critical decisions

#### Technical Lead
- **Primary**: Bob Johnson (bob.johnson@company.com, +1-555-0102)
- **Backup**: Alice Williams (alice.williams@company.com, +1-555-0103)

**Responsibilities**:
- Execute technical recovery procedures
- Coordinate technical team
- Verify system integrity
- Report progress to DR Coordinator

#### Database Administrator
- **Primary**: Charlie Brown (charlie.brown@company.com, +1-555-0104)

**Responsibilities**:
- Restore database from backup
- Verify data integrity
- Optimize database performance
- Monitor database health

#### Security Lead
- **Primary**: Diana Prince (diana.prince@company.com, +1-555-0105)

**Responsibilities**:
- Assess security implications
- Implement security measures
- Investigate security incidents
- Ensure compliance

---

## Contact Information

### Emergency Contacts

| Role | Name | Phone | Email | Availability |
|------|------|-------|-------|--------------|
| DR Coordinator | John Doe | +1-555-0100 | john.doe@company.com | 24/7 |
| Technical Lead | Bob Johnson | +1-555-0102 | bob.johnson@company.com | 24/7 |
| Security Lead | Diana Prince | +1-555-0105 | diana.prince@company.com | 24/7 |
| CTO | Executive | +1-555-0200 | cto@company.com | Business hours |

### Vendor Contacts

| Vendor | Service | Contact | Phone | Support Level |
|--------|---------|---------|-------|---------------|
| AWS | Cloud Infrastructure | aws-support@amazon.com | +1-800-AWS-SUPPORT | Premium |
| DataStax | HCD Support | support@datastax.com | +1-855-DATASTAX | Enterprise |
| JanusGraph | Community Support | janusgraph-users@googlegroups.com | N/A | Community |

### Escalation Path

1. **Level 1**: On-call engineer (15 min response)
2. **Level 2**: Technical lead (30 min response)
3. **Level 3**: DR coordinator (1 hour response)
4. **Level 4**: CTO (2 hour response)

---

## Appendices

### Appendix A: Recovery Scripts

Located in: `/scripts/backup/` and `/scripts/maintenance/`

- `backup_volumes_encrypted.sh` - Encrypted backup script
- `restore_volumes.sh` - Restore from backup
- `verify_data_integrity.sh` - Data integrity verification
- `rotate_secrets.sh` - Credential rotation

### Appendix B: Configuration Files

Located in: `/config/`

- `docker-compose.yml` - Main service configuration
- `docker-compose.tls.yml` - TLS configuration
- `.env.example` - Environment variables template

### Appendix C: Network Diagrams

See: `docs/ARCHITECTURE.md`

### Appendix D: Compliance Requirements

- **PCI DSS**: Backup retention, encryption, access controls
- **HIPAA**: Data protection, audit logging, disaster recovery
- **GDPR**: Data protection, breach notification, right to erasure
- **SOC 2**: Availability, confidentiality, processing integrity

### Appendix E: Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-28 | 1.0 | Initial version | Security Team |

---

**Document Classification**: CONFIDENTIAL  
**Next Review Date**: 2026-04-28  
**Document Owner**: DR Coordinator  
**Approval**: CTO, CISO

---

*This document contains sensitive information. Distribution is restricted to authorized personnel only.*