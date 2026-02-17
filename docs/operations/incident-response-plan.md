# Incident Response Plan (IRP)

**Project**: HCD + JanusGraph Stack
**Version**: 1.0
**Date**: 2026-01-28
**Classification**: CONFIDENTIAL
**Review Cycle**: Quarterly

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Incident Classification](#incident-classification)
3. [Incident Response Team](#incident-response-team)
4. [Response Procedures](#response-procedures)
5. [Communication Plan](#communication-plan)
6. [Post-Incident Activities](#post-incident-activities)
7. [Incident Types and Playbooks](#incident-types-and-playbooks)
8. [Tools and Resources](#tools-and-resources)
9. [Training and Exercises](#training-and-exercises)
10. [Appendices](#appendices)

---

## Executive Summary

This Incident Response Plan (IRP) provides structured procedures for detecting, responding to, and recovering from security incidents and operational disruptions affecting the HCD + JanusGraph stack.

### Objectives

1. **Detect** incidents quickly and accurately
2. **Contain** incidents to minimize impact
3. **Eradicate** threats completely
4. **Recover** services to normal operations
5. **Learn** from incidents to improve security

### Key Metrics

| Metric | Target | Current |
|--------|--------|---------|
| **Detection Time** | < 15 minutes | < 10 minutes |
| **Response Time** | < 30 minutes | < 20 minutes |
| **Containment Time** | < 2 hours | < 1 hour |
| **Recovery Time** | < 4 hours | < 2 hours |

---

## Incident Classification

### Severity Levels

#### P0 - Critical

**Impact**: Complete service outage or major security breach
**Response Time**: Immediate (< 15 minutes)
**Escalation**: Immediate to CTO/CISO

**Examples**:

- Complete system outage
- Active ransomware attack
- Data breach with PII exposure
- Critical vulnerability exploitation

#### P1 - High

**Impact**: Significant service degradation or security threat
**Response Time**: < 30 minutes
**Escalation**: Within 1 hour to management

**Examples**:

- Partial service outage
- DDoS attack
- Unauthorized access attempt
- Critical data corruption

#### P2 - Medium

**Impact**: Minor service degradation or security concern
**Response Time**: < 2 hours
**Escalation**: Within 4 hours if unresolved

**Examples**:

- Performance degradation
- Failed authentication spike
- Non-critical vulnerability
- Configuration error

#### P3 - Low

**Impact**: Minimal or no service impact
**Response Time**: < 8 hours
**Escalation**: Within 24 hours if unresolved

**Examples**:

- Informational security alerts
- Minor configuration issues
- Routine maintenance needs
- Documentation updates

### Incident Categories

1. **Security Incidents**
   - Unauthorized access
   - Malware/ransomware
   - Data breach
   - DDoS attack
   - Insider threat

2. **Operational Incidents**
   - Service outage
   - Performance degradation
   - Data corruption
   - Hardware failure
   - Network issues

3. **Compliance Incidents**
   - Policy violation
   - Audit finding
   - Regulatory breach
   - Data retention issue

---

## Incident Response Team

### Team Structure

```
Incident Commander
├── Technical Response Team
│   ├── Database Team
│   ├── Security Team
│   ├── Network Team
│   └── Application Team
├── Communications Team
│   ├── Internal Communications
│   └── External Communications
└── Legal/Compliance Team
    ├── Legal Counsel
    └── Compliance Officer
```

### Roles and Responsibilities

#### Incident Commander (IC)

**Primary**: John Doe (<john.doe@company.com>, +1-555-0100)
**Backup**: Jane Smith (<jane.smith@company.com>, +1-555-0101)

**Responsibilities**:

- Declare incident and severity
- Activate response team
- Coordinate response efforts
- Make critical decisions
- Communicate with stakeholders
- Declare incident resolved

#### Technical Lead

**Primary**: Bob Johnson (<bob.johnson@company.com>, +1-555-0102)

**Responsibilities**:

- Lead technical investigation
- Coordinate technical team
- Implement containment measures
- Execute recovery procedures
- Document technical findings

#### Security Lead

**Primary**: Diana Prince (<diana.prince@company.com>, +1-555-0105)

**Responsibilities**:

- Assess security implications
- Conduct forensic analysis
- Implement security controls
- Coordinate with law enforcement (if needed)
- Document security findings

#### Communications Lead

**Primary**: Eve Adams (<eve.adams@company.com>, +1-555-0106)

**Responsibilities**:

- Manage internal communications
- Coordinate external communications
- Prepare status updates
- Handle media inquiries
- Document communications

---

## Response Procedures

### Phase 1: Detection and Analysis (15-30 minutes)

#### 1.1 Incident Detection

**Automated Detection**:

```bash
# Monitoring alerts
- Prometheus alerts
- Grafana dashboards
- Log analysis (Loki)
- Security scanning
- Anomaly detection
```

**Manual Detection**:

- User reports
- Security team observation
- Vendor notification
- External notification

#### 1.2 Initial Assessment

**Actions**:

1. Verify the incident is real (not false positive)
2. Determine incident type and category
3. Assess initial severity
4. Document initial findings

**Assessment Checklist**:

- [ ] What happened?
- [ ] When did it happen?
- [ ] What systems are affected?
- [ ] What is the impact?
- [ ] Is it still ongoing?
- [ ] What is the initial severity?

#### 1.3 Incident Declaration

**Criteria for Declaration**:

- Confirmed security incident
- Service outage or degradation
- Data integrity concern
- Compliance violation

**Declaration Process**:

```bash
# 1. Notify Incident Commander
# 2. Create incident ticket
# 3. Activate response team
# 4. Start incident log
# 5. Begin status updates
```

### Phase 2: Containment (30 minutes - 2 hours)

#### 2.1 Short-term Containment

**Objective**: Stop the incident from spreading

**Actions**:

```bash
# Isolate affected systems
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo stop <affected-service>

# Block malicious IPs
iptables -A INPUT -s <malicious-ip> -j DROP

# Disable compromised accounts
./scripts/security/disable_account.sh --user <username>

# Enable enhanced monitoring
./scripts/monitoring/enable_enhanced_monitoring.sh
```

#### 2.2 Evidence Preservation

**Critical**: Preserve evidence before making changes

```bash
# Capture system state
PODMAN_CONNECTION=podman-wxd podman --remote ps -a > incident-containers.txt
PODMAN_CONNECTION=podman-wxd podman --remote logs <container> > incident-logs.txt

# Capture network state
netstat -an > incident-network.txt
iptables -L -n > incident-firewall.txt

# Capture memory dump (if needed)
PODMAN_CONNECTION=podman-wxd podman --remote exec <container> gcore <pid>

# Create forensic backup
./scripts/backup/backup_volumes_encrypted.sh --tag forensic-$(date +%Y%m%d-%H%M%S)
```

#### 2.3 Long-term Containment

**Objective**: Maintain business operations while preparing for eradication

**Actions**:

- Deploy temporary fixes
- Implement workarounds
- Enhance monitoring
- Prepare recovery plan

### Phase 3: Eradication (1-4 hours)

#### 3.1 Root Cause Analysis

**Investigation Steps**:

1. Analyze logs and forensic data
2. Identify attack vector
3. Determine scope of compromise
4. Identify all affected systems

**Tools**:

```bash
# Log analysis
PODMAN_CONNECTION=podman-wxd podman --remote logs <container> | grep -i error
loki-cli query '{job="janusgraph"}' --since 1h

# Security scanning
./scripts/security/scan_vulnerabilities.sh
./scripts/security/scan_malware.sh

# Data integrity check
./scripts/maintenance/verify_data_integrity.sh
```

#### 3.2 Threat Removal

**Actions**:

```bash
# Remove malware
./scripts/security/remove_malware.sh --scan-all

# Close vulnerabilities
./scripts/security/patch_vulnerabilities.sh

# Remove backdoors
./scripts/security/scan_backdoors.sh --remove

# Reset compromised credentials
./scripts/maintenance/rotate_secrets.sh --all --force
```

#### 3.3 System Hardening

**Actions**:

```bash
# Update security configurations
./scripts/security/harden_system.sh

# Apply security patches
./scripts/maintenance/apply_patches.sh

# Update firewall rules
./scripts/security/update_firewall.sh

# Enable additional security controls
./scripts/security/enable_enhanced_security.sh
```

### Phase 4: Recovery (2-4 hours)

#### 4.1 Service Restoration

**Actions**:

```bash
# Restore from clean backup (if needed)
./scripts/backup/restore_volumes.sh \
  --backup-file s3://bucket/clean-backup.tar.gz.gpg \
  --decrypt \
  --verify

# Restart services
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo up -d

# Verify services
./scripts/testing/run_integration_tests.sh
```

#### 4.2 Verification

**Checklist**:

- [ ] All services running
- [ ] Data integrity verified
- [ ] Security controls active
- [ ] Monitoring operational
- [ ] No signs of compromise
- [ ] Performance normal

#### 4.3 Return to Normal Operations

**Actions**:

1. Gradually restore traffic
2. Monitor closely for 24-48 hours
3. Maintain enhanced logging
4. Continue threat hunting
5. Document lessons learned

### Phase 5: Post-Incident (Ongoing)

#### 5.1 Incident Documentation

**Required Documentation**:

- Incident timeline
- Actions taken
- Evidence collected
- Root cause analysis
- Impact assessment
- Lessons learned

#### 5.2 Post-Incident Review

**Meeting Agenda**:

1. What happened?
2. What went well?
3. What could be improved?
4. What actions are needed?
5. Who is responsible?
6. What is the timeline?

#### 5.3 Improvement Actions

**Follow-up Tasks**:

- Update security controls
- Patch vulnerabilities
- Update documentation
- Conduct training
- Test improvements

---

## Communication Plan

### Internal Communications

#### Status Update Schedule

| Severity | Initial | Updates | Audience |
|----------|---------|---------|----------|
| **P0** | Immediate | Every 30 min | All stakeholders |
| **P1** | < 30 min | Every 1 hour | Management + Tech |
| **P2** | < 2 hours | Every 4 hours | Tech team |
| **P3** | < 8 hours | Daily | Tech team |

#### Communication Channels

- **Slack**: #incident-response (real-time updates)
- **Email**: <incident-team@company.com> (formal updates)
- **Phone**: Conference bridge for P0/P1 incidents
- **Status Page**: status.company.com (customer-facing)

#### Status Update Template

```
INCIDENT UPDATE #<number>
Severity: <P0/P1/P2/P3>
Status: <Investigating/Identified/Monitoring/Resolved>
Time: <timestamp>

Summary:
<Brief description of current situation>

Impact:
<What services/users are affected>

Actions Taken:
<What has been done>

Next Steps:
<What will be done next>

Next Update: <time>
```

### External Communications

#### Customer Notifications

**When to Notify**:

- P0 incidents (always)
- P1 incidents (if customer-facing)
- Data breach (always, per regulations)
- Extended outage (> 1 hour)

**Notification Template**:

```
Subject: Service Incident Notification

Dear Customer,

We are currently experiencing [brief description].

Impact: [what is affected]
Status: [current status]
ETA: [estimated resolution time]

We apologize for any inconvenience and are working to resolve this as quickly as possible.

Updates: [where to find updates]

Thank you for your patience.
```

#### Regulatory Notifications

**Requirements**:

- **Data Breach**: Notify within 72 hours (GDPR)
- **PCI Incident**: Notify immediately
- **HIPAA Breach**: Notify within 60 days

**Notification Process**:

1. Consult legal counsel
2. Prepare notification
3. Submit to regulators
4. Document submission

---

## Incident Types and Playbooks

### Playbook 1: Ransomware Attack

**Detection Indicators**:

- Files encrypted with unusual extensions
- Ransom note files
- Unusual file modifications
- Backup deletion attempts

**Response Steps**:

1. **Immediate Actions** (< 5 minutes)

   ```bash
   # Isolate infected systems
   PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo down
   iptables -A INPUT -j DROP
   iptables -A OUTPUT -j DROP

   # Preserve evidence
   ./scripts/backup/backup_volumes_encrypted.sh --tag ransomware-evidence
   ```

2. **Containment** (< 30 minutes)
   - Identify patient zero
   - Check backup integrity
   - Assess encryption scope
   - Notify law enforcement

3. **Eradication** (2-4 hours)
   - Remove malware
   - Rebuild infected systems
   - Restore from clean backups
   - Patch vulnerabilities

4. **Recovery** (4-8 hours)
   - Restore data from backups
   - Verify data integrity
   - Test all systems
   - Resume operations

**Do NOT**:

- Pay the ransom
- Delete evidence
- Restore from potentially infected backups

### Playbook 2: DDoS Attack

**Detection Indicators**:

- Sudden traffic spike
- Service degradation
- High CPU/network usage
- Rate limit violations

**Response Steps**:

1. **Immediate Actions** (< 5 minutes)

   ```bash
   # Enable rate limiting
   PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo -f PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo.nginx.yml up -d

   # Block attacking IPs
   ./scripts/security/block_ips.sh --file attacking-ips.txt
   ```

2. **Containment** (< 30 minutes)
   - Activate DDoS protection (CloudFlare, AWS Shield)
   - Implement geo-blocking if needed
   - Scale infrastructure
   - Contact ISP

3. **Monitoring** (Ongoing)
   - Track attack patterns
   - Adjust defenses
   - Document attack

4. **Recovery** (< 2 hours)
   - Gradually restore normal operations
   - Remove temporary blocks
   - Analyze attack data

### Playbook 3: Data Breach

**Detection Indicators**:

- Unauthorized data access
- Data exfiltration
- Compromised credentials
- Suspicious queries

**Response Steps**:

1. **Immediate Actions** (< 15 minutes)

   ```bash
   # Enable read-only mode
   ./scripts/maintenance/enable_readonly_mode.sh

   # Revoke all access tokens
   ./scripts/security/revoke_all_tokens.sh

   # Enable enhanced audit logging
   ./scripts/monitoring/enable_audit_logging.sh
   ```

2. **Investigation** (1-4 hours)
   - Identify compromised data
   - Determine access method
   - Assess data sensitivity
   - Check for data exfiltration

3. **Containment** (< 2 hours)
   - Disable compromised accounts
   - Rotate all credentials
   - Patch vulnerabilities
   - Enhance access controls

4. **Notification** (< 72 hours)
   - Notify affected individuals
   - Notify regulators
   - Prepare public statement
   - Offer credit monitoring (if applicable)

### Playbook 4: Insider Threat

**Detection Indicators**:

- Unusual data access patterns
- After-hours activity
- Large data downloads
- Policy violations

**Response Steps**:

1. **Immediate Actions** (< 30 minutes)

   ```bash
   # Disable suspect account
   ./scripts/security/disable_account.sh --user <username>

   # Preserve evidence
   ./scripts/security/capture_user_activity.sh --user <username>

   # Enable enhanced monitoring
   ./scripts/monitoring/monitor_user.sh --user <username>
   ```

2. **Investigation** (Confidential)
   - Review access logs
   - Analyze data access
   - Interview personnel
   - Consult legal/HR

3. **Containment** (< 4 hours)
   - Revoke all access
   - Change shared credentials
   - Review permissions
   - Secure evidence

4. **Resolution** (Varies)
   - Follow HR procedures
   - Involve law enforcement (if criminal)
   - Document findings
   - Implement controls

---

## Tools and Resources

### Incident Response Tools

```bash
# Log analysis
PODMAN_CONNECTION=podman-wxd podman --remote logs <container>
loki-cli query '{job="<service>"}'

# Security scanning
./scripts/security/scan_vulnerabilities.sh
./scripts/security/scan_malware.sh

# Forensics
./scripts/security/capture_forensics.sh
./scripts/security/analyze_logs.sh

# Recovery
./scripts/backup/restore_volumes.sh
./scripts/maintenance/verify_data_integrity.sh
```

### External Resources

- **NIST Incident Response Guide**: <https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf>
- **SANS Incident Response**: <https://www.sans.org/incident-response/>
- **MITRE ATT&CK**: <https://attack.mitre.org/>
- **CVE Database**: <https://cve.mitre.org/>

### Contact Information

**Emergency Contacts**: See [Contact Information](#contact-information) section

**Law Enforcement**:

- FBI Cyber Division: +1-855-292-3937
- Local Police: 911
- IC3 (Internet Crime Complaint Center): <https://www.ic3.gov/>

**Vendors**:

- AWS Security: +1-800-AWS-SUPPORT
- DataStax Support: +1-855-DATASTAX

---

## Training and Exercises

### Training Requirements

| Role | Training | Frequency |
|------|----------|-----------|
| **All Staff** | Security Awareness | Annual |
| **Technical Staff** | Incident Response Basics | Annual |
| **IR Team** | Advanced IR Training | Semi-annual |
| **IC/Leads** | Leadership Training | Annual |

### Exercise Schedule

| Exercise Type | Frequency | Duration | Participants |
|---------------|-----------|----------|--------------|
| **Tabletop** | Quarterly | 2 hours | IR Team |
| **Simulation** | Semi-annual | 4 hours | IR Team + Management |
| **Full Drill** | Annual | 8 hours | All Teams |

### Exercise Scenarios

1. **Ransomware Attack**
2. **Data Breach**
3. **DDoS Attack**
4. **Insider Threat**
5. **Supply Chain Attack**

---

## Appendices

### Appendix A: Incident Log Template

```
INCIDENT LOG

Incident ID: INC-<YYYYMMDD>-<number>
Severity: <P0/P1/P2/P3>
Category: <Security/Operational/Compliance>
Status: <Open/Investigating/Contained/Resolved>

Timeline:
[HH:MM] - Event description
[HH:MM] - Action taken
[HH:MM] - Status update

Affected Systems:
- System 1
- System 2

Impact:
- Impact description

Actions Taken:
- Action 1
- Action 2

Evidence Collected:
- Evidence 1
- Evidence 2

Root Cause:
- Root cause description

Resolution:
- Resolution description

Lessons Learned:
- Lesson 1
- Lesson 2
```

### Appendix B: Incident Severity Matrix

| Impact | Scope | Severity |
|--------|-------|----------|
| Critical | Widespread | P0 |
| Critical | Limited | P1 |
| High | Widespread | P1 |
| High | Limited | P2 |
| Medium | Any | P2 |
| Low | Any | P3 |

### Appendix C: Compliance Requirements

**Data Breach Notification**:

- **GDPR**: 72 hours to regulator, without undue delay to individuals
- **CCPA**: Without unreasonable delay
- **HIPAA**: 60 days
- **PCI DSS**: Immediately to card brands and acquirer

### Appendix D: Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-28 | 1.0 | Initial version | Security Team |

---

**Document Classification**: CONFIDENTIAL
**Next Review Date**: 2026-04-28
**Document Owner**: Incident Commander
**Approval**: CTO, CISO

---

*This document contains sensitive information. Distribution is restricted to authorized personnel only.*
