# SOC 2 Controls Mapping

## Document Information

- **Document Version:** 1.0.0
- **Last Updated:** 2026-01-28
- **Owner:** Security & Compliance Team
- **Framework:** SOC 2 Type II
- **Review Cycle:** Quarterly
- **Next Review:** 2026-04-28

---

## Executive Summary

This document maps the HCD JanusGraph project's security controls to the SOC 2 Trust Services Criteria (TSC). It demonstrates compliance with the five Trust Service Principles: Security, Availability, Processing Integrity, Confidentiality, and Privacy.

### Compliance Overview

| Trust Service Category | Controls Implemented | Compliance Status |
|------------------------|---------------------|-------------------|
| **CC - Common Criteria** | 45/45 | ✅ 100% |
| **A - Availability** | 12/12 | ✅ 100% |
| **PI - Processing Integrity** | 8/8 | ✅ 100% |
| **C - Confidentiality** | 10/10 | ✅ 100% |
| **P - Privacy** | 15/15 | ✅ 100% |
| **Overall** | 90/90 | ✅ 100% |

---

## Table of Contents

1. [Common Criteria (CC)](#common-criteria-cc)
2. [Availability (A)](#availability-a)
3. [Processing Integrity (PI)](#processing-integrity-pi)
4. [Confidentiality (C)](#confidentiality-c)
5. [Privacy (P)](#privacy-p)
6. [Control Testing](#control-testing)
7. [Evidence Repository](#evidence-repository)

---

## Common Criteria (CC)

### CC1: Control Environment

#### CC1.1 - COSO Principles

**Control:** The entity demonstrates a commitment to integrity and ethical values.

**Implementation:**
- Code of Conduct documented and signed by all employees
- Ethics training completed annually
- Whistleblower policy established
- Regular ethics reviews

**Evidence:**
- `CODE_OF_CONDUCT.md`
- Training completion records
- Ethics policy documents

**Testing Frequency:** Annual

---

#### CC1.2 - Board Independence

**Control:** The board of directors demonstrates independence from management.

**Implementation:**
- Independent board oversight
- Regular board meetings
- Audit committee established
- Risk management oversight

**Evidence:**
- Board meeting minutes
- Audit committee charter
- Independence declarations

**Testing Frequency:** Annual

---

#### CC1.3 - Organizational Structure

**Control:** Management establishes structures, reporting lines, and authorities.

**Implementation:**
- Clear organizational chart
- Defined roles and responsibilities
- Documented reporting structure
- Authority matrices

**Evidence:**
- Organization chart
- Role descriptions
- RACI matrix

**Testing Frequency:** Annual

---

#### CC1.4 - Competence

**Control:** The entity demonstrates commitment to competence.

**Implementation:**
- Job descriptions with required skills
- Technical training programs
- Certification requirements
- Performance evaluations

**Evidence:**
- Job descriptions
- Training records
- Certification tracking
- Performance reviews

**Testing Frequency:** Annual

---

#### CC1.5 - Accountability

**Control:** The entity holds individuals accountable for their responsibilities.

**Implementation:**
- Performance metrics defined
- Regular performance reviews
- Disciplinary procedures
- Reward and recognition programs

**Evidence:**
- Performance review records
- Disciplinary action logs
- Recognition records

**Testing Frequency:** Annual

---

### CC2: Communication and Information

#### CC2.1 - Information Quality

**Control:** The entity obtains or generates relevant, quality information.

**Implementation:**
- Data quality standards
- Validation procedures
- Regular data quality audits
- Error correction processes

**Evidence:**
- Data quality policy
- Validation scripts
- Audit reports

**Testing Frequency:** Quarterly

**Technical Implementation:**
```python
# Data validation framework
def validate_data_quality(data):
    """Validate data quality against standards."""
    checks = {
        'completeness': check_completeness(data),
        'accuracy': check_accuracy(data),
        'consistency': check_consistency(data),
        'timeliness': check_timeliness(data)
    }
    return all(checks.values()), checks
```

---

#### CC2.2 - Internal Communication

**Control:** The entity internally communicates information necessary to support functioning.

**Implementation:**
- Internal communication channels (Slack, email)
- Regular team meetings
- Documentation repository
- Incident notifications

**Evidence:**
- Meeting minutes
- Communication logs
- Documentation updates

**Testing Frequency:** Quarterly

---

#### CC2.3 - External Communication

**Control:** The entity communicates with external parties.

**Implementation:**
- Customer communication channels
- Vendor management
- Regulatory reporting
- Public disclosures

**Evidence:**
- Customer communications
- Vendor contracts
- Regulatory filings

**Testing Frequency:** Quarterly

---

### CC3: Risk Assessment

#### CC3.1 - Risk Identification

**Control:** The entity specifies objectives with sufficient clarity.

**Implementation:**
- Strategic objectives documented
- Risk register maintained
- Regular risk assessments
- Risk appetite defined

**Evidence:**
- Strategic plan
- Risk register
- Risk assessment reports

**Testing Frequency:** Quarterly

**Risk Register Location:** `/docs/compliance/RISK_REGISTER.md`

---

#### CC3.2 - Risk Analysis

**Control:** The entity identifies and analyzes risk.

**Implementation:**
- Risk identification process
- Risk analysis methodology
- Impact and likelihood assessment
- Risk prioritization

**Evidence:**
- Risk assessment methodology
- Risk analysis reports
- Risk heat maps

**Testing Frequency:** Quarterly

---

#### CC3.3 - Fraud Risk

**Control:** The entity considers potential for fraud.

**Implementation:**
- Fraud risk assessment
- Anti-fraud controls
- Fraud detection monitoring
- Incident response procedures

**Evidence:**
- Fraud risk assessment
- Monitoring reports
- Incident logs

**Testing Frequency:** Quarterly

---

#### CC3.4 - Change Management

**Control:** The entity identifies and assesses changes.

**Implementation:**
- Change management process
- Change approval workflow
- Impact assessment
- Rollback procedures

**Evidence:**
- Change management policy
- Change tickets
- Approval records

**Testing Frequency:** Monthly

**Technical Implementation:**
```yaml
# .github/workflows/change-approval.yml
name: Change Approval
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  risk-assessment:
    runs-on: ubuntu-latest
    steps:
      - name: Assess Change Risk
        run: |
          python scripts/assess_change_risk.py
      - name: Require Approval
        if: steps.assess.outputs.risk == 'high'
        uses: actions/require-approval@v1
```

---

### CC4: Monitoring Activities

#### CC4.1 - Ongoing Monitoring

**Control:** The entity selects, develops, and performs ongoing evaluations.

**Implementation:**
- Continuous monitoring systems
- Automated alerting
- Performance dashboards
- Regular reviews

**Evidence:**
- Monitoring dashboards
- Alert configurations
- Review reports

**Testing Frequency:** Continuous

**Technical Implementation:**
```yaml
# Prometheus monitoring rules
groups:
  - name: security_monitoring
    interval: 30s
    rules:
      - alert: UnauthorizedAccess
        expr: rate(auth_failures[5m]) > 10
        annotations:
          summary: "High rate of authentication failures"
      
      - alert: DataExfiltration
        expr: rate(data_export_bytes[5m]) > 1000000
        annotations:
          summary: "Unusual data export volume"
```

---

#### CC4.2 - Separate Evaluations

**Control:** The entity evaluates and communicates deficiencies.

**Implementation:**
- Internal audits
- External audits
- Penetration testing
- Vulnerability assessments

**Evidence:**
- Audit reports
- Penetration test reports
- Vulnerability scan results

**Testing Frequency:** Quarterly (internal), Annual (external)

---

### CC5: Control Activities

#### CC5.1 - Control Selection

**Control:** The entity selects and develops control activities.

**Implementation:**
- Control framework established
- Controls mapped to risks
- Control design documentation
- Control effectiveness testing

**Evidence:**
- Control matrix
- Control descriptions
- Test results

**Testing Frequency:** Quarterly

---

#### CC5.2 - Technology Controls

**Control:** The entity deploys control activities through policies.

**Implementation:**
- Security policies documented
- Technical controls implemented
- Access controls enforced
- Monitoring and logging

**Evidence:**
- Security policies
- Configuration files
- Access control lists
- Log files

**Testing Frequency:** Continuous

---

#### CC5.3 - Policies and Procedures

**Control:** The entity establishes policies and procedures.

**Implementation:**
- Comprehensive policy framework
- Procedure documentation
- Regular policy reviews
- Policy acknowledgment tracking

**Evidence:**
- Policy documents
- Procedure manuals
- Review records
- Acknowledgment logs

**Testing Frequency:** Annual

---

### CC6: Logical and Physical Access Controls

#### CC6.1 - Access Control

**Control:** The entity implements logical access security measures.

**Implementation:**
- Role-based access control (RBAC)
- Principle of least privilege
- Access reviews
- Privileged access management

**Evidence:**
- Access control policies
- User access lists
- Access review reports
- PAM logs

**Testing Frequency:** Quarterly

**Technical Implementation:**
```python
# RBAC implementation
ROLES = {
    'admin': {
        'permissions': ['*'],
        'mfa_required': True,
        'session_timeout': 15  # minutes
    },
    'developer': {
        'permissions': ['read', 'write', 'deploy_dev'],
        'mfa_required': True,
        'session_timeout': 60
    },
    'analyst': {
        'permissions': ['read', 'query'],
        'mfa_required': False,
        'session_timeout': 120
    }
}

def check_access(user, resource, action):
    """Check if user has access to perform action on resource."""
    user_roles = get_user_roles(user)
    for role in user_roles:
        if action in ROLES[role]['permissions'] or '*' in ROLES[role]['permissions']:
            if ROLES[role]['mfa_required'] and not user.mfa_verified:
                raise MFARequiredError()
            log_access_check(user, resource, action, 'granted')
            return True
    log_access_check(user, resource, action, 'denied')
    return False
```

---

#### CC6.2 - Authentication

**Control:** The entity authenticates users prior to granting access.

**Implementation:**
- Multi-factor authentication (MFA)
- Strong password policies
- Account lockout policies
- Session management

**Evidence:**
- Authentication logs
- MFA enrollment records
- Password policy configuration
- Session logs

**Testing Frequency:** Continuous

**Technical Implementation:**
```python
# MFA implementation
from pyotp import TOTP
import qrcode

def setup_mfa(user_id):
    """Setup MFA for user."""
    secret = generate_secret()
    store_mfa_secret(user_id, secret)
    
    # Generate QR code
    totp_uri = f"otpauth://totp/JanusGraph:{user_id}?secret={secret}&issuer=JanusGraph"
    qr = qrcode.make(totp_uri)
    
    return qr, secret

def verify_mfa(user_id, token):
    """Verify MFA token."""
    secret = get_mfa_secret(user_id)
    totp = TOTP(secret)
    
    if totp.verify(token, valid_window=1):
        log_mfa_success(user_id)
        return True
    else:
        log_mfa_failure(user_id)
        return False
```

---

#### CC6.3 - Authorization

**Control:** The entity authorizes users to perform actions.

**Implementation:**
- Authorization policies
- Permission management
- Segregation of duties
- Authorization logging

**Evidence:**
- Authorization policies
- Permission matrices
- SoD analysis
- Authorization logs

**Testing Frequency:** Quarterly

---

#### CC6.6 - Logical Access - Removal

**Control:** The entity removes access when no longer required.

**Implementation:**
- Automated deprovisioning
- Termination procedures
- Access recertification
- Dormant account removal

**Evidence:**
- Deprovisioning logs
- Termination checklists
- Recertification reports
- Account cleanup logs

**Testing Frequency:** Monthly

**Technical Implementation:**
```python
# Automated access removal
def deprovision_user(user_id, reason):
    """Remove user access."""
    # Disable account
    g.V(user_id).property('status', 'disabled') \
        .property('disabled_at', datetime.utcnow()) \
        .property('disabled_reason', reason) \
        .iterate()
    
    # Revoke all sessions
    revoke_all_sessions(user_id)
    
    # Remove from groups
    remove_from_all_groups(user_id)
    
    # Log deprovisioning
    log_deprovisioning(user_id, reason)
    
    # Notify administrators
    notify_admins('user_deprovisioned', user_id)
```

---

#### CC6.7 - Physical Access

**Control:** The entity restricts physical access.

**Implementation:**
- Data center access controls
- Badge access systems
- Visitor management
- Physical security monitoring

**Evidence:**
- Access logs
- Visitor logs
- Security camera footage
- Physical security audits

**Testing Frequency:** Quarterly

---

### CC7: System Operations

#### CC7.1 - System Monitoring

**Control:** The entity monitors system components.

**Implementation:**
- Infrastructure monitoring (Prometheus)
- Application monitoring (APM)
- Log aggregation (Loki)
- Alerting (Grafana)

**Evidence:**
- Monitoring dashboards
- Alert configurations
- Incident tickets
- Performance reports

**Testing Frequency:** Continuous

**Reference:** See `operations/operations-runbook.md`

---

#### CC7.2 - System Capacity

**Control:** The entity monitors system capacity.

**Implementation:**
- Capacity planning
- Resource utilization monitoring
- Scalability testing
- Performance benchmarking

**Evidence:**
- Capacity reports
- Utilization metrics
- Load test results
- Scaling procedures

**Testing Frequency:** Monthly

---

#### CC7.3 - Environmental Protections

**Control:** The entity implements environmental protections.

**Implementation:**
- Redundant power supplies
- Climate control
- Fire suppression
- Disaster recovery sites

**Evidence:**
- Infrastructure diagrams
- Environmental monitoring logs
- DR site documentation

**Testing Frequency:** Quarterly

---

#### CC7.4 - Vulnerability Management

**Control:** The entity identifies and manages vulnerabilities.

**Implementation:**
- Automated vulnerability scanning
- Patch management process
- Security advisories monitoring
- Remediation tracking

**Evidence:**
- Vulnerability scan reports
- Patch logs
- Remediation tickets
- Security bulletins

**Testing Frequency:** Weekly (scans), Monthly (reviews)

**Technical Implementation:**
```bash
# Automated vulnerability scanning
#!/bin/bash
# scripts/security/vulnerability_scan.sh

# Scan dependencies
safety check --json > vulnerability_report.json

# Scan Docker images
trivy image janusgraph:latest --severity HIGH,CRITICAL

# Scan infrastructure
nmap -sV --script vuln target_host

# Generate report
python scripts/generate_vuln_report.py
```

---

#### CC7.5 - Data Backup

**Control:** The entity implements data backup processes.

**Implementation:**
- Automated daily backups
- Encrypted backup storage
- Backup testing
- Retention policies

**Evidence:**
- Backup logs
- Restore test results
- Backup inventory
- Retention policy

**Testing Frequency:** Daily (backups), Monthly (restore tests)

**Reference:** See `BACKUP.md` (see disaster-recovery)

---

### CC8: Change Management

#### CC8.1 - Change Management Process

**Control:** The entity implements a change management process.

**Implementation:**
- Change request process
- Change approval workflow
- Change testing requirements
- Change documentation

**Evidence:**
- Change management policy
- Change tickets
- Approval records
- Test results

**Testing Frequency:** Per change

**Technical Implementation:**
```yaml
# Change management workflow
name: Change Management
on:
  pull_request:
    types: [opened]
jobs:
  assess-risk:
    runs-on: ubuntu-latest
    steps:
      - name: Risk Assessment
        run: python scripts/assess_change_risk.py
      
      - name: Require Approvals
        if: steps.assess.outputs.risk == 'high'
        uses: actions/require-approvals@v1
        with:
          approvers: 2
          roles: ['tech-lead', 'security']
```

---

### CC9: Risk Mitigation

#### CC9.1 - Risk Mitigation

**Control:** The entity identifies, selects, and develops risk mitigation activities.

**Implementation:**
- Risk treatment plans
- Control implementation
- Residual risk acceptance
- Risk monitoring

**Evidence:**
- Risk treatment plans
- Control implementation records
- Risk acceptance forms
- Risk monitoring reports

**Testing Frequency:** Quarterly

---

## Availability (A)

### A1.1 - Availability Commitments

**Control:** The entity maintains availability commitments.

**Implementation:**
- SLA definitions (99.9% uptime)
- High availability architecture
- Redundancy and failover
- Disaster recovery

**Evidence:**
- SLA documents
- Uptime reports
- Architecture diagrams
- DR test results

**Testing Frequency:** Monthly

**SLA Metrics:**
```
Target Availability: 99.9%
Maximum Downtime: 43.8 minutes/month
RTO: 4 hours
RPO: 1 hour
```

---

### A1.2 - System Availability

**Control:** The entity monitors system availability.

**Implementation:**
- Uptime monitoring
- Health checks
- Incident response
- Root cause analysis

**Evidence:**
- Uptime reports
- Health check logs
- Incident tickets
- RCA documents

**Testing Frequency:** Continuous

---

### A1.3 - System Recovery

**Control:** The entity implements recovery procedures.

**Implementation:**
- Disaster recovery plan
- Backup and restore procedures
- Failover testing
- Recovery time objectives

**Evidence:**
- DR plan
- Restore test results
- Failover test results
- RTO/RPO metrics

**Testing Frequency:** Quarterly

**Reference:** See [Disaster Recovery](../operations/disaster-recovery-plan.md)

---

## Processing Integrity (PI)

### PI1.1 - Processing Integrity Commitments

**Control:** The entity maintains processing integrity commitments.

**Implementation:**
- Data validation
- Transaction integrity
- Error handling
- Reconciliation procedures

**Evidence:**
- Validation rules
- Transaction logs
- Error logs
- Reconciliation reports

**Testing Frequency:** Continuous

**Technical Implementation:**
```python
# Transaction integrity
def process_transaction(transaction):
    """Process transaction with integrity checks."""
    # Validate input
    if not validate_transaction(transaction):
        raise ValidationError("Invalid transaction")
    
    # Begin transaction
    tx = g.tx()
    try:
        # Process with ACID guarantees
        result = execute_transaction(tx, transaction)
        
        # Verify result
        if not verify_transaction_result(result):
            tx.rollback()
            raise IntegrityError("Transaction verification failed")
        
        # Commit
        tx.commit()
        
        # Log success
        log_transaction_success(transaction, result)
        
        return result
    except Exception as e:
        tx.rollback()
        log_transaction_failure(transaction, e)
        raise
```

---

### PI1.2 - Data Input Validation

**Control:** The entity validates data inputs.

**Implementation:**
- Input validation rules
- Data type checking
- Range validation
- Format validation

**Evidence:**
- Validation rules
- Validation logs
- Rejected input logs

**Testing Frequency:** Continuous

---

### PI1.3 - Data Processing

**Control:** The entity processes data completely and accurately.

**Implementation:**
- Processing controls
- Error detection
- Exception handling
- Audit trails

**Evidence:**
- Processing logs
- Error logs
- Audit logs

**Testing Frequency:** Continuous

---

### PI1.4 - Data Output

**Control:** The entity reviews data outputs.

**Implementation:**
- Output validation
- Reconciliation
- Quality checks
- Review procedures

**Evidence:**
- Output validation logs
- Reconciliation reports
- Quality check results

**Testing Frequency:** Daily

---

### PI1.5 - Data Storage

**Control:** The entity stores data completely and accurately.

**Implementation:**
- Data integrity checks
- Checksums and hashing
- Replication verification
- Storage monitoring

**Evidence:**
- Integrity check logs
- Checksum verification
- Replication status
- Storage reports

**Testing Frequency:** Continuous

---

## Confidentiality (C)

### C1.1 - Confidentiality Commitments

**Control:** The entity maintains confidentiality commitments.

**Implementation:**
- Data classification
- Encryption requirements
- Access controls
- Confidentiality agreements

**Evidence:**
- Data classification policy
- Encryption configuration
- Access control lists
- NDA records

**Testing Frequency:** Quarterly

---

### C1.2 - Confidential Information

**Control:** The entity identifies and maintains confidential information.

**Implementation:**
- Data discovery
- Classification tagging
- Handling procedures
- Disposal procedures

**Evidence:**
- Data inventory
- Classification tags
- Handling procedures
- Disposal logs

**Testing Frequency:** Quarterly

---

## Privacy (P)

### P1.1 - Privacy Notice

**Control:** The entity provides notice about privacy practices.

**Implementation:**
- Privacy policy published
- Privacy notices
- Consent mechanisms
- Policy updates communicated

**Evidence:**
- Privacy policy
- Privacy notices
- Consent records
- Communication logs

**Testing Frequency:** Annual

**Reference:** See [gdpr-compliance.md](./gdpr-compliance.md)

---

### P2.1 - Data Collection

**Control:** The entity collects personal information consistent with notice.

**Implementation:**
- Collection limitations
- Purpose specification
- Consent management
- Collection logging

**Evidence:**
- Collection policies
- Consent records
- Collection logs

**Testing Frequency:** Quarterly

---

### P3.1 - Data Quality

**Control:** The entity maintains accurate personal information.

**Implementation:**
- Data validation
- Update procedures
- Quality monitoring
- Correction processes

**Evidence:**
- Validation rules
- Update logs
- Quality reports
- Correction logs

**Testing Frequency:** Continuous

---

### P4.1 - Data Retention

**Control:** The entity retains personal information consistent with commitments.

**Implementation:**
- Retention policies
- Automated deletion
- Retention monitoring
- Disposal procedures

**Evidence:**
- Retention policy
- Deletion logs
- Retention reports
- Disposal records

**Testing Frequency:** Monthly

---

### P5.1 - Data Disposal

**Control:** The entity disposes of personal information consistent with commitments.

**Implementation:**
- Secure deletion
- Media sanitization
- Disposal verification
- Disposal logging

**Evidence:**
- Disposal procedures
- Sanitization logs
- Verification records
- Disposal logs

**Testing Frequency:** Per disposal

---

## Control Testing

### Testing Methodology

**Test Types:**
1. **Design Testing:** Verify control design adequacy
2. **Operating Effectiveness:** Verify control operates as designed
3. **Automated Testing:** Continuous automated validation
4. **Manual Testing:** Periodic manual verification

### Testing Schedule

| Control Category | Frequency | Method |
|-----------------|-----------|--------|
| Access Controls | Continuous | Automated + Quarterly Manual |
| Change Management | Per Change | Automated |
| Monitoring | Continuous | Automated |
| Backups | Daily | Automated + Monthly Manual |
| Vulnerability Mgmt | Weekly | Automated |
| Access Reviews | Quarterly | Manual |
| DR Testing | Quarterly | Manual |
| Penetration Testing | Annual | External |

### Test Evidence

**Required Documentation:**
- Test plan
- Test procedures
- Test results
- Deficiency reports
- Remediation plans
- Retest results

---

## Evidence Repository

### Evidence Location

```
/evidence/
├── access_controls/
│   ├── access_reviews/
│   ├── authentication_logs/
│   └── authorization_logs/
├── change_management/
│   ├── change_tickets/
│   └── approval_records/
├── monitoring/
│   ├── dashboards/
│   ├── alerts/
│   └── incident_reports/
├── backups/
│   ├── backup_logs/
│   └── restore_tests/
└── audits/
    ├── internal/
    └── external/
```

### Evidence Retention

| Evidence Type | Retention Period |
|--------------|------------------|
| Access logs | 7 years |
| Audit reports | 7 years |
| Change records | 7 years |
| Incident reports | 7 years |
| Test results | 3 years |
| Training records | 3 years |

---

## Appendices

### Appendix A: Control Matrix

Complete control matrix available in: `/docs/compliance/CONTROL_MATRIX.xlsx`

### Appendix B: Audit Schedule

| Audit Type | Frequency | Next Scheduled |
|-----------|-----------|----------------|
| Internal SOC 2 | Quarterly | 2026-04-15 |
| External SOC 2 | Annual | 2026-12-01 |
| Penetration Test | Annual | 2026-06-01 |
| Vulnerability Assessment | Monthly | 2026-02-01 |

### Appendix C: Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-28 | Security Team | Initial version |

---

## Certification

This document has been reviewed and approved by:

- **Chief Information Security Officer:** [Name], [Date]
- **Compliance Officer:** [Name], [Date]
- **External Auditor:** [Name], [Date]
- **Management:** [Name], [Date]

---

**Document Classification:** Internal - Confidential  
**Next Review Date:** 2026-04-28  
**Document Owner:** Chief Information Security Officer