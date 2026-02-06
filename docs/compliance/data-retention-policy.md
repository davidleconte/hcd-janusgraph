# Data Retention and Disposal Policy

## Document Information

- **Document Version:** 1.0.0
- **Last Updated:** 2026-01-28
- **Owner:** Data Protection Officer
- **Review Cycle:** Annual
- **Next Review:** 2027-01-28
- **Effective Date:** 2026-02-01

---

## Executive Summary

This Data Retention and Disposal Policy establishes guidelines for the retention, archival, and secure disposal of data within the HCD JanusGraph system. The policy ensures compliance with legal requirements, regulatory obligations, and business needs while protecting data privacy and security.

### Policy Objectives

1. Comply with legal and regulatory retention requirements
2. Minimize data storage costs and security risks
3. Protect data subject privacy rights
4. Support business operations and analytics
5. Enable efficient data discovery and retrieval

---

## Table of Contents

1. [Scope and Applicability](#scope-and-applicability)
2. [Retention Schedules](#retention-schedules)
3. [Data Classification](#data-classification)
4. [Retention Procedures](#retention-procedures)
5. [Archival Procedures](#archival-procedures)
6. [Disposal Procedures](#disposal-procedures)
7. [Legal Holds](#legal-holds)
8. [Roles and Responsibilities](#roles-and-responsibilities)
9. [Compliance Monitoring](#compliance-monitoring)
10. [Exceptions](#exceptions)

---

## 1. Scope and Applicability

### 1.1 Scope

This policy applies to all data stored, processed, or transmitted by the HCD JanusGraph system, including:

- **Structured Data:** Graph database records, relational data
- **Unstructured Data:** Documents, logs, backups
- **System Data:** Configuration files, metadata, audit trails
- **Personal Data:** User information, transaction records

### 1.2 Applicability

This policy applies to:
- All employees and contractors
- All systems and applications
- All data storage locations (on-premise and cloud)
- All data formats (electronic and physical)

### 1.3 Regulatory Framework

This policy complies with:
- **GDPR** (EU General Data Protection Regulation)
- **SOX** (Sarbanes-Oxley Act) - Financial records
- **PCI DSS** (Payment Card Industry Data Security Standard)
- **Local Data Protection Laws**
- **Industry-Specific Regulations**

---

## 2. Retention Schedules

### 2.1 User Account Data

| Data Type | Active Retention | Inactive Retention | Total Retention | Legal Basis |
|-----------|------------------|-------------------|-----------------|-------------|
| User Profile | Duration of service | 2 years | Service + 2 years | Contract, Legitimate Interest |
| Authentication Logs | 90 days | N/A | 90 days | Security |
| Consent Records | Duration of service | 7 years | Service + 7 years | Legal Obligation |
| Account Closure Records | N/A | 7 years | 7 years | Legal Obligation |

**Retention Triggers:**
- **Active:** Account is in use
- **Inactive:** No login for 12 months
- **Closed:** User-requested deletion or termination

**Implementation:**
```python
# Automated inactive account cleanup
def cleanup_inactive_accounts():
    """Delete accounts inactive for > 2 years."""
    cutoff_date = datetime.utcnow() - timedelta(days=730)
    
    inactive_users = g.V().hasLabel('user') \
        .has('status', 'inactive') \
        .has('last_login', P.lt(cutoff_date)) \
        .toList()
    
    for user in inactive_users:
        # Check for legal holds
        if not has_legal_hold(user.id):
            # Anonymize or delete
            if must_retain_anonymized(user.id):
                anonymize_user(user.id)
            else:
                delete_user(user.id)
            
            log_retention_action('user_cleanup', user.id)
```

---

### 2.2 Transaction Data

| Data Type | Retention Period | Legal Basis | Disposal Method |
|-----------|-----------------|-------------|-----------------|
| Financial Transactions | 7 years | SOX, Tax Law | Secure Deletion |
| Transaction Metadata | 7 years | Legal Obligation | Secure Deletion |
| Payment Card Data | 90 days | PCI DSS | Secure Deletion |
| Fraud Investigation Data | 10 years | Legal Obligation | Secure Deletion |

**Special Considerations:**
- Financial records: 7 years from end of fiscal year
- Tax-related records: Per local tax authority requirements
- Disputed transactions: Retain until resolution + 7 years

---

### 2.3 System Logs

| Log Type | Retention Period | Purpose | Storage Location |
|----------|-----------------|---------|------------------|
| Application Logs | 90 days | Troubleshooting | Loki |
| Access Logs | 90 days | Security Monitoring | Loki |
| Audit Logs | 7 years | Compliance | Archive Storage |
| Security Event Logs | 1 year | Incident Response | SIEM |
| Performance Metrics | 13 months | Capacity Planning | Prometheus |

**Log Rotation Schedule:**
```yaml
# Loki retention configuration
retention_period: 90d
retention_stream:
  - selector: '{job="janusgraph"}'
    priority: 1
    min_age: 90d
  - selector: '{level="error"}'
    priority: 2
    min_age: 180d  # Keep errors longer
```

---

### 2.4 Backup Data

| Backup Type | Retention Period | Frequency | Storage Location |
|-------------|-----------------|-----------|------------------|
| Full Backup | 30 days | Weekly | Encrypted Cloud Storage |
| Incremental Backup | 7 days | Daily | Encrypted Cloud Storage |
| Archive Backup | 7 years | Annual | Cold Storage |
| Disaster Recovery | 90 days | Daily | DR Site |

**Backup Retention Implementation:**
```bash
#!/bin/bash
# scripts/backup/enforce_backup_retention.sh

# Delete backups older than 30 days
find /backups/full -type f -mtime +30 -delete

# Delete incremental backups older than 7 days
find /backups/incremental -type f -mtime +7 -delete

# Archive annual backups to cold storage
find /backups/annual -type f -mtime +365 -exec \
  aws s3 cp {} s3://archive-bucket/ --storage-class GLACIER \;

# Log retention actions
echo "$(date): Backup retention enforced" >> /var/log/backup_retention.log
```

---

### 2.5 Documentation

| Document Type | Retention Period | Review Cycle | Owner |
|--------------|-----------------|--------------|-------|
| Technical Documentation | Current + 3 versions | Quarterly | Engineering |
| Policy Documents | 7 years | Annual | Compliance |
| Audit Reports | 7 years | N/A | Audit |
| Incident Reports | 7 years | N/A | Security |
| Training Materials | 3 years | Annual | HR |
| Contracts | Duration + 7 years | N/A | Legal |

---

## 3. Data Classification

### 3.1 Classification Levels

| Level | Description | Retention Impact | Examples |
|-------|-------------|------------------|----------|
| **Public** | Publicly available | Standard retention | Marketing materials |
| **Internal** | Internal use only | Standard retention | Internal docs |
| **Confidential** | Sensitive business data | Extended retention | Financial data |
| **Restricted** | Highly sensitive | Maximum retention | PII, PHI, PCI |

### 3.2 Classification Criteria

**Restricted Data:**
- Personal Identifiable Information (PII)
- Payment Card Information (PCI)
- Authentication credentials
- Encryption keys
- Trade secrets

**Confidential Data:**
- Financial records
- Business strategies
- Customer lists
- Proprietary algorithms

**Internal Data:**
- Internal communications
- Project documentation
- System configurations

**Public Data:**
- Published documentation
- Marketing materials
- Public announcements

---

## 4. Retention Procedures

### 4.1 Data Lifecycle Management

```
[Creation] → [Active Use] → [Inactive] → [Archive] → [Disposal]
     ↓            ↓            ↓            ↓           ↓
  Classify    Monitor      Review       Secure      Verify
              Access       Retention    Storage     Deletion
```

### 4.2 Automated Retention Enforcement

**Daily Jobs:**
```python
# Daily retention enforcement
def daily_retention_job():
    """Execute daily retention tasks."""
    # Clean up expired sessions
    cleanup_expired_sessions()
    
    # Rotate logs
    rotate_application_logs()
    
    # Clean up temporary data
    cleanup_temp_data()
    
    # Generate retention report
    generate_retention_report()
```

**Weekly Jobs:**
```python
# Weekly retention enforcement
def weekly_retention_job():
    """Execute weekly retention tasks."""
    # Review inactive accounts
    review_inactive_accounts()
    
    # Clean up old backups
    cleanup_old_backups()
    
    # Archive old data
    archive_old_data()
    
    # Update retention metrics
    update_retention_metrics()
```

**Monthly Jobs:**
```python
# Monthly retention enforcement
def monthly_retention_job():
    """Execute monthly retention tasks."""
    # Delete expired data
    delete_expired_data()
    
    # Verify archival integrity
    verify_archive_integrity()
    
    # Generate compliance report
    generate_compliance_report()
    
    # Review retention policy
    review_retention_policy()
```

### 4.3 Manual Review Process

**Quarterly Reviews:**
1. Review retention schedules
2. Identify data for disposal
3. Check for legal holds
4. Approve disposal requests
5. Verify disposal completion

**Annual Reviews:**
1. Review entire retention policy
2. Update retention schedules
3. Assess compliance
4. Update procedures
5. Train staff

---

## 5. Archival Procedures

### 5.1 Archival Criteria

Data should be archived when:
- No longer actively used
- Required for compliance
- Historical value
- Legal obligation

### 5.2 Archival Process

```python
def archive_data(data_id, reason):
    """Archive data to long-term storage."""
    # Validate archival eligibility
    if not can_archive(data_id):
        raise ValueError("Data cannot be archived")
    
    # Extract data
    data = extract_data(data_id)
    
    # Compress data
    compressed = compress_data(data)
    
    # Encrypt data
    encrypted = encrypt_data(compressed)
    
    # Store in archive
    archive_id = store_in_archive(encrypted)
    
    # Update metadata
    update_archive_metadata(data_id, archive_id, reason)
    
    # Remove from active storage
    remove_from_active_storage(data_id)
    
    # Log archival
    log_archival(data_id, archive_id, reason)
    
    return archive_id
```

### 5.3 Archive Storage

**Storage Tiers:**
- **Hot Storage:** Frequently accessed (< 30 days)
- **Warm Storage:** Occasionally accessed (30-365 days)
- **Cold Storage:** Rarely accessed (> 365 days)
- **Glacier:** Long-term archive (> 7 years)

**Implementation:**
```yaml
# AWS S3 Lifecycle Policy
lifecycle_rules:
  - id: archive-transition
    status: Enabled
    transitions:
      - days: 30
        storage_class: STANDARD_IA
      - days: 90
        storage_class: GLACIER
      - days: 2555  # 7 years
        storage_class: DEEP_ARCHIVE
    expiration:
      days: 2920  # 8 years (7 + 1 buffer)
```

---

## 6. Disposal Procedures

### 6.1 Disposal Methods

| Data Type | Disposal Method | Verification |
|-----------|----------------|--------------|
| Database Records | Secure deletion + overwrite | Deletion log |
| Log Files | Secure deletion | Deletion log |
| Backups | Cryptographic erasure | Certificate |
| Physical Media | Degaussing or shredding | Certificate of Destruction |
| Cloud Storage | Cryptographic erasure | API confirmation |

### 6.2 Secure Deletion Process

```python
def secure_delete(data_id, reason):
    """Securely delete data."""
    # Check for legal holds
    if has_legal_hold(data_id):
        raise LegalHoldError("Cannot delete: legal hold active")
    
    # Verify retention period expired
    if not retention_expired(data_id):
        raise RetentionError("Cannot delete: retention period not expired")
    
    # Get approval
    if not has_deletion_approval(data_id):
        raise ApprovalError("Cannot delete: approval required")
    
    # Delete from primary storage
    delete_from_database(data_id)
    
    # Delete from backups
    delete_from_backups(data_id)
    
    # Delete from archives
    delete_from_archives(data_id)
    
    # Verify deletion
    if verify_deletion(data_id):
        # Log deletion
        log_secure_deletion(data_id, reason)
        
        # Generate certificate
        generate_deletion_certificate(data_id)
    else:
        raise DeletionError("Deletion verification failed")
```

### 6.3 Cryptographic Erasure

For encrypted data, cryptographic erasure (key destruction) is acceptable:

```python
def cryptographic_erasure(data_id):
    """Erase data by destroying encryption keys."""
    # Get encryption key ID
    key_id = get_encryption_key_id(data_id)
    
    # Destroy key in KMS
    destroy_kms_key(key_id)
    
    # Verify key destruction
    if not verify_key_destroyed(key_id):
        raise KeyDestructionError("Key destruction failed")
    
    # Log erasure
    log_cryptographic_erasure(data_id, key_id)
    
    # Data is now unrecoverable
    return True
```

### 6.4 Disposal Verification

**Verification Steps:**
1. Confirm data no longer accessible
2. Verify deletion from all systems
3. Check backup deletion
4. Generate disposal certificate
5. Update disposal register

**Disposal Certificate:**
```json
{
  "certificate_id": "CERT-2026-001",
  "data_id": "user_12345",
  "data_type": "user_account",
  "disposal_date": "2026-01-28T15:00:00Z",
  "disposal_method": "secure_deletion",
  "retention_period_end": "2026-01-15",
  "approved_by": "dpo@example.com",
  "executed_by": "system_admin",
  "verification_status": "verified",
  "verification_date": "2026-01-28T15:30:00Z"
}
```

---

## 7. Legal Holds

### 7.1 Legal Hold Process

When litigation, investigation, or audit is anticipated:

1. **Initiate Hold:** Legal counsel issues hold notice
2. **Identify Data:** Determine scope of hold
3. **Preserve Data:** Suspend normal retention/disposal
4. **Notify Custodians:** Inform data owners
5. **Monitor Compliance:** Ensure hold is maintained
6. **Release Hold:** Legal counsel authorizes release

### 7.2 Legal Hold Implementation

```python
def apply_legal_hold(data_id, case_id, reason):
    """Apply legal hold to data."""
    # Create hold record
    hold = {
        'hold_id': generate_hold_id(),
        'data_id': data_id,
        'case_id': case_id,
        'reason': reason,
        'applied_date': datetime.utcnow(),
        'applied_by': get_current_user(),
        'status': 'active'
    }
    
    # Mark data with hold
    g.V(data_id).property('legal_hold', True) \
        .property('hold_id', hold['hold_id']) \
        .iterate()
    
    # Prevent deletion
    add_to_hold_list(data_id)
    
    # Notify custodians
    notify_legal_hold(data_id, hold)
    
    # Log hold
    log_legal_hold('applied', hold)
    
    return hold['hold_id']

def release_legal_hold(hold_id, reason):
    """Release legal hold."""
    # Verify authorization
    if not authorized_to_release(hold_id):
        raise AuthorizationError("Not authorized to release hold")
    
    # Get hold details
    hold = get_hold_details(hold_id)
    
    # Remove hold from data
    g.V(hold['data_id']).property('legal_hold', False) \
        .property('hold_id', None) \
        .iterate()
    
    # Remove from hold list
    remove_from_hold_list(hold['data_id'])
    
    # Update hold record
    update_hold_status(hold_id, 'released', reason)
    
    # Notify custodians
    notify_hold_release(hold)
    
    # Log release
    log_legal_hold('released', hold)
    
    # Resume normal retention
    resume_retention_schedule(hold['data_id'])
```

---

## 8. Roles and Responsibilities

### 8.1 Data Protection Officer (DPO)

**Responsibilities:**
- Oversee retention policy
- Approve retention schedules
- Monitor compliance
- Handle data subject requests
- Coordinate with legal

### 8.2 Data Owners

**Responsibilities:**
- Classify data
- Define retention requirements
- Approve disposal
- Maintain data inventory
- Ensure compliance

### 8.3 System Administrators

**Responsibilities:**
- Implement retention controls
- Execute disposal procedures
- Maintain audit logs
- Monitor automated jobs
- Report issues

### 8.4 Legal Counsel

**Responsibilities:**
- Advise on legal requirements
- Issue legal holds
- Review retention schedules
- Approve exceptions
- Handle litigation

### 8.5 Compliance Team

**Responsibilities:**
- Monitor compliance
- Conduct audits
- Report violations
- Update policies
- Train staff

---

## 9. Compliance Monitoring

### 9.1 Monitoring Activities

**Continuous Monitoring:**
- Automated retention enforcement
- Disposal verification
- Legal hold compliance
- Access to retained data

**Periodic Reviews:**
- Quarterly retention audits
- Annual policy review
- Data inventory updates
- Compliance assessments

### 9.2 Compliance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Retention Compliance | 100% | % data within retention period |
| Disposal Timeliness | 95% | % disposed within 30 days of expiration |
| Legal Hold Compliance | 100% | % holds properly maintained |
| Audit Findings | 0 | Number of critical findings |

### 9.3 Reporting

**Monthly Reports:**
- Retention statistics
- Disposal activities
- Legal holds
- Compliance issues

**Quarterly Reports:**
- Compliance assessment
- Audit results
- Policy updates
- Training completion

**Annual Reports:**
- Comprehensive review
- Regulatory compliance
- Policy effectiveness
- Recommendations

---

## 10. Exceptions

### 10.1 Exception Process

Exceptions to this policy require:
1. Written justification
2. Risk assessment
3. Compensating controls
4. DPO approval
5. Documentation

### 10.2 Exception Types

**Temporary Exceptions:**
- Business need (< 90 days)
- Technical limitation
- Pending system upgrade

**Permanent Exceptions:**
- Legal requirement
- Regulatory mandate
- Contractual obligation

### 10.3 Exception Tracking

```python
def request_retention_exception(data_id, reason, duration):
    """Request exception to retention policy."""
    exception = {
        'exception_id': generate_exception_id(),
        'data_id': data_id,
        'reason': reason,
        'requested_by': get_current_user(),
        'requested_date': datetime.utcnow(),
        'duration': duration,
        'status': 'pending'
    }
    
    # Submit for approval
    submit_for_approval(exception)
    
    # Log request
    log_exception_request(exception)
    
    return exception['exception_id']
```

---

## Appendices

### Appendix A: Retention Schedule Summary

Complete retention schedule matrix available in: `/docs/compliance/RETENTION_SCHEDULE.xlsx`

### Appendix B: Disposal Checklist

1. ☐ Verify retention period expired
2. ☐ Check for legal holds
3. ☐ Obtain disposal approval
4. ☐ Execute secure deletion
5. ☐ Verify deletion complete
6. ☐ Generate disposal certificate
7. ☐ Update disposal register
8. ☐ Notify stakeholders

### Appendix C: Legal Hold Template

Template available in: `/docs/compliance/LEGAL_HOLD_TEMPLATE.md`

### Appendix D: Glossary

- **Retention Period:** Time data must be kept
- **Archival:** Moving data to long-term storage
- **Disposal:** Permanent deletion of data
- **Legal Hold:** Suspension of normal retention
- **Cryptographic Erasure:** Deletion by key destruction

### Appendix E: Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-28 | DPO | Initial version |

---

## Policy Approval

This policy has been reviewed and approved by:

- **Data Protection Officer:** [Name], [Date]
- **Legal Counsel:** [Name], [Date]
- **Chief Information Security Officer:** [Name], [Date]
- **Chief Executive Officer:** [Name], [Date]

---

**Document Classification:** Internal - Confidential  
**Next Review Date:** 2027-01-28  
**Document Owner:** Data Protection Officer  
**Policy Effective Date:** 2026-02-01