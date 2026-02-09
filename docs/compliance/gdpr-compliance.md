# GDPR Compliance Documentation

## Document Information

- **Document Version:** 1.0.0
- **Last Updated:** 2026-01-28
- **Owner:** Security & Compliance Team
- **Review Cycle:** Quarterly
- **Next Review:** 2026-04-28

---

## Executive Summary

This document outlines the HCD JanusGraph project's compliance with the General Data Protection Regulation (GDPR) EU 2016/679. It details the technical and organizational measures implemented to protect personal data and ensure compliance with GDPR requirements.

### Compliance Status

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Lawful Basis | ✅ Compliant | Documented consent mechanisms |
| Data Minimization | ✅ Compliant | Schema design principles |
| Purpose Limitation | ✅ Compliant | Data usage policies |
| Storage Limitation | ✅ Compliant | Retention policies implemented |
| Accuracy | ✅ Compliant | Data validation & update procedures |
| Integrity & Confidentiality | ✅ Compliant | Encryption, access controls |
| Accountability | ✅ Compliant | Audit logging, documentation |

---

## Table of Contents

1. [Scope and Applicability](#scope-and-applicability)
2. [Legal Basis for Processing](#legal-basis-for-processing)
3. [Data Protection Principles](#data-protection-principles)
4. [Data Subject Rights](#data-subject-rights)
5. [Technical Measures](#technical-measures)
6. [Organizational Measures](#organizational-measures)
7. [Data Processing Records](#data-processing-records)
8. [Data Breach Procedures](#data-breach-procedures)
9. [Privacy by Design](#privacy-by-design)
10. [Third-Party Processing](#third-party-processing)
11. [International Data Transfers](#international-data-transfers)
12. [Compliance Monitoring](#compliance-monitoring)

---

## 1. Scope and Applicability

### 1.1 Personal Data Processed

The HCD JanusGraph system processes the following categories of personal data:

**User Account Data:**

- Name
- Email address
- User ID
- Authentication credentials (hashed)
- Account creation date
- Last login timestamp

**Transaction Data (Banking Module):**

- Account numbers
- Transaction amounts
- Transaction timestamps
- IP addresses
- Device identifiers

**System Logs:**

- User activity logs
- Access logs
- Error logs
- Audit trails

### 1.2 Data Controllers and Processors

**Data Controller:** [Organization Name]

- Determines purposes and means of processing
- Responsible for GDPR compliance
- Contact: <dpo@example.com>

**Data Processors:**

- HCD JanusGraph system (internal processing)
- Cloud infrastructure providers (if applicable)
- Backup service providers

### 1.3 Geographic Scope

- **Primary Processing Location:** EU/EEA
- **Data Residency:** EU data centers
- **Cross-border Transfers:** Documented with appropriate safeguards

---

## 2. Legal Basis for Processing

### 2.1 Lawful Bases

| Processing Activity | Legal Basis | Documentation |
|---------------------|-------------|---------------|
| User account management | Consent | User registration form |
| Transaction processing | Contract performance | Terms of service |
| Security monitoring | Legitimate interest | Security policy |
| Audit logging | Legal obligation | Compliance requirements |
| Analytics | Consent | Cookie/privacy policy |

### 2.2 Consent Management

**Consent Requirements:**

- ✅ Freely given
- ✅ Specific
- ✅ Informed
- ✅ Unambiguous
- ✅ Withdrawable

**Implementation:**

```python
# Consent tracking in user profile
{
    "user_id": "user123",
    "consents": {
        "data_processing": {
            "granted": true,
            "timestamp": "2026-01-15T10:30:00Z",
            "version": "1.0",
            "ip_address": "192.168.1.100"
        },
        "marketing": {
            "granted": false,
            "timestamp": "2026-01-15T10:30:00Z",
            "version": "1.0"
        }
    }
}
```

---

## 3. Data Protection Principles

### 3.1 Lawfulness, Fairness, and Transparency

**Implementation:**

- Privacy policy published and accessible
- Clear communication about data processing
- Transparent consent mechanisms
- Regular privacy notices

**Documentation Location:** `/docs/PRIVACY_POLICY.md`

### 3.2 Purpose Limitation

**Defined Purposes:**

1. User authentication and authorization
2. Transaction processing and fraud detection
3. System security and monitoring
4. Legal compliance and audit
5. Service improvement (with consent)

**Controls:**

- Purpose documented in data processing records
- Access controls based on purpose
- Regular purpose compliance audits

### 3.3 Data Minimization

**Principles Applied:**

- Collect only necessary data fields
- No excessive data collection
- Regular data necessity reviews

**Schema Design:**

```groovy
// Minimal user schema
mgmt.makeVertexLabel('user').make()
mgmt.makePropertyKey('user_id').dataType(String.class).make()
mgmt.makePropertyKey('email').dataType(String.class).make()
mgmt.makePropertyKey('name').dataType(String.class).make()
// No unnecessary fields like SSN, full address, etc.
```

### 3.4 Accuracy

**Measures:**

- Data validation on input
- User self-service data correction
- Regular data quality checks
- Automated data verification

**Implementation:**

```python
def update_user_data(user_id, updates):
    """Update user data with validation."""
    # Validate input
    validated_data = validate_personal_data(updates)

    # Log update for audit
    log_data_update(user_id, validated_data)

    # Update graph
    g.V(user_id).property('updated_at', datetime.utcnow())
    for key, value in validated_data.items():
        g.V(user_id).property(key, value)
```

### 3.5 Storage Limitation

**Retention Periods:**

| Data Type | Retention Period | Legal Basis |
|-----------|------------------|-------------|
| User accounts (active) | Duration of service | Contract |
| User accounts (inactive) | 2 years | Legitimate interest |
| Transaction records | 7 years | Legal obligation |
| Access logs | 90 days | Security |
| Audit logs | 7 years | Legal obligation |
| Backup data | 30 days | Business continuity |

**Automated Deletion:**

```python
# Scheduled data retention job
def enforce_data_retention():
    """Delete data past retention period."""
    # Delete inactive accounts > 2 years
    cutoff_date = datetime.utcnow() - timedelta(days=730)
    g.V().hasLabel('user') \
        .has('status', 'inactive') \
        .has('last_login', lt(cutoff_date)) \
        .drop().iterate()

    # Delete old logs
    log_cutoff = datetime.utcnow() - timedelta(days=90)
    delete_logs_before(log_cutoff)
```

### 3.6 Integrity and Confidentiality

**Security Measures:**

- ✅ Encryption at rest (AES-256)
- ✅ Encryption in transit (TLS 1.3)
- ✅ Access controls (RBAC)
- ✅ Authentication (MFA)
- ✅ Audit logging
- ✅ Regular security assessments

**Reference:** See `SECURITY.md`

---

## 4. Data Subject Rights

### 4.1 Right of Access (Article 15)

**Implementation:**

```python
def export_user_data(user_id):
    """Export all personal data for a user."""
    # Collect all user data
    user_data = {
        'profile': get_user_profile(user_id),
        'transactions': get_user_transactions(user_id),
        'consents': get_user_consents(user_id),
        'access_logs': get_user_access_logs(user_id)
    }

    # Generate export file
    export_file = generate_gdpr_export(user_data)

    # Log access request
    log_gdpr_request('access', user_id)

    return export_file
```

**Response Time:** Within 30 days
**Format:** JSON, CSV, or PDF
**Delivery:** Secure download link

### 4.2 Right to Rectification (Article 16)

**Implementation:**

- Self-service user profile updates
- Admin-assisted corrections
- Validation and verification
- Audit trail of changes

**API Endpoint:**

```python
@app.route('/api/v1/users/<user_id>', methods=['PUT'])
@require_auth
def update_user(user_id):
    """Update user personal data."""
    if not user_can_modify(current_user, user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    updates = request.json
    validated = validate_updates(updates)

    # Update data
    update_user_data(user_id, validated)

    # Log rectification
    log_gdpr_request('rectification', user_id, validated)

    return jsonify({'status': 'updated'}), 200
```

### 4.3 Right to Erasure (Article 17)

**Implementation:**

```python
def delete_user_data(user_id, reason):
    """Delete user data (right to be forgotten)."""
    # Verify deletion is permissible
    if not can_delete_user(user_id):
        raise ValueError("Cannot delete: legal obligation to retain")

    # Anonymize instead of delete if required
    if must_retain_for_legal_reasons(user_id):
        anonymize_user_data(user_id)
    else:
        # Full deletion
        g.V(user_id).drop().iterate()
        delete_user_from_backups(user_id)

    # Log deletion
    log_gdpr_request('erasure', user_id, reason)

    # Notify connected systems
    notify_deletion(user_id)
```

**Exceptions:**

- Legal obligations (e.g., financial records)
- Public interest
- Legal claims

### 4.4 Right to Restriction (Article 18)

**Implementation:**

```python
def restrict_user_processing(user_id, reason):
    """Restrict processing of user data."""
    # Mark account as restricted
    g.V(user_id).property('processing_restricted', True) \
        .property('restriction_reason', reason) \
        .property('restriction_date', datetime.utcnow()) \
        .iterate()

    # Log restriction
    log_gdpr_request('restriction', user_id, reason)

    # Notify systems
    notify_restriction(user_id)
```

### 4.5 Right to Data Portability (Article 20)

**Implementation:**

```python
def export_portable_data(user_id):
    """Export data in machine-readable format."""
    data = {
        'user_profile': get_user_profile(user_id),
        'transactions': get_user_transactions(user_id),
        'preferences': get_user_preferences(user_id)
    }

    # Export in standard format (JSON)
    export = {
        'format': 'JSON',
        'version': '1.0',
        'exported_at': datetime.utcnow().isoformat(),
        'data': data
    }

    log_gdpr_request('portability', user_id)

    return json.dumps(export, indent=2)
```

### 4.6 Right to Object (Article 21)

**Implementation:**

- Opt-out mechanisms for marketing
- Objection to automated decision-making
- Objection to profiling

**Process:**

1. User submits objection
2. Review objection validity
3. Cease processing if valid
4. Notify user of outcome

### 4.7 Rights Related to Automated Decision-Making (Article 22)

**Current Status:**

- ✅ No fully automated decisions with legal effects
- ✅ Human review for critical decisions
- ✅ Transparency in algorithms used

**If Implemented:**

- Right to human intervention
- Right to explanation
- Right to contest decision

---

## 5. Technical Measures

### 5.1 Encryption

**At Rest:**

- Database: AES-256 encryption
- Backups: Encrypted with GPG
- Configuration: Encrypted secrets

**In Transit:**

- TLS 1.3 for all connections
- Certificate pinning
- Perfect forward secrecy

**Implementation:**

```yaml
# janusgraph-hcd.properties
storage.cql.ssl.enabled=true
storage.cql.ssl.truststore.location=/path/to/truststore.jks
storage.cql.ssl.client-authentication-enabled=true
```

### 5.2 Access Controls

**Role-Based Access Control (RBAC):**

```python
ROLES = {
    'admin': ['read', 'write', 'delete', 'manage_users'],
    'analyst': ['read', 'query'],
    'user': ['read_own', 'update_own'],
    'auditor': ['read', 'audit_logs']
}

def check_permission(user, action, resource):
    """Check if user has permission."""
    user_roles = get_user_roles(user)
    for role in user_roles:
        if action in ROLES.get(role, []):
            return True
    return False
```

### 5.3 Pseudonymization

**Implementation:**

```python
import hashlib
import hmac

def pseudonymize_identifier(identifier, salt):
    """Pseudonymize personal identifier."""
    return hmac.new(
        salt.encode(),
        identifier.encode(),
        hashlib.sha256
    ).hexdigest()

# Usage
user_pseudo_id = pseudonymize_identifier(email, SECRET_SALT)
```

### 5.4 Audit Logging

**Logged Events:**

- Data access
- Data modifications
- User authentication
- Permission changes
- GDPR requests
- Data exports
- Data deletions

**Log Format:**

```json
{
    "timestamp": "2026-01-28T15:30:00Z",
    "event_type": "data_access",
    "user_id": "user123",
    "resource": "user_profile",
    "action": "read",
    "ip_address": "192.168.1.100",
    "result": "success",
    "trace_id": "abc123"
}
```

### 5.5 Data Anonymization

**Techniques:**

- K-anonymity for analytics
- Differential privacy for aggregates
- Data masking for non-production

```python
def anonymize_for_analytics(data):
    """Anonymize data for analytics."""
    return {
        'age_group': get_age_group(data['age']),  # 25-34 instead of 28
        'city': data['city'],  # Keep city
        'transaction_count': data['transaction_count'],
        # Remove: name, email, exact age, account number
    }
```

---

## 6. Organizational Measures

### 6.1 Data Protection Officer (DPO)

**Contact Information:**

- Name: [DPO Name]
- Email: <dpo@example.com>
- Phone: +{PHONE-NUMBER}

**Responsibilities:**

- Monitor GDPR compliance
- Advise on data protection
- Cooperate with supervisory authority
- Act as contact point for data subjects

### 6.2 Staff Training

**Training Program:**

- GDPR fundamentals (all staff)
- Data handling procedures (technical staff)
- Incident response (security team)
- Privacy by design (developers)

**Frequency:** Annual mandatory training + updates

### 6.3 Data Protection Impact Assessment (DPIA)

**When Required:**

- New data processing activities
- High-risk processing
- Large-scale processing of special categories
- Systematic monitoring

**DPIA Template:** See DPIA Template

### 6.4 Policies and Procedures

**Documented Policies:**

- ✅ Privacy Policy
- ✅ Data Retention Policy
- ✅ Data Breach Response Plan
- ✅ Access Control Policy
- ✅ Backup and Recovery Policy
- ✅ Third-Party Processing Policy

---

## 7. Data Processing Records

### 7.1 Article 30 Records

**Processing Activity:** User Account Management

| Field | Value |
|-------|-------|
| Purpose | User authentication and authorization |
| Legal Basis | Consent, Contract |
| Categories of Data | Name, email, credentials |
| Categories of Recipients | Internal systems only |
| Retention Period | Duration of service + 2 years |
| Security Measures | Encryption, access controls, MFA |

**Processing Activity:** Transaction Processing

| Field | Value |
|-------|-------|
| Purpose | Financial transaction processing |
| Legal Basis | Contract, Legal obligation |
| Categories of Data | Account numbers, amounts, timestamps |
| Categories of Recipients | Internal systems, regulators |
| Retention Period | 7 years (legal requirement) |
| Security Measures | Encryption, audit logging, access controls |

### 7.2 Data Flow Mapping

```
[User] --> [API Gateway] --> [JanusGraph] --> [HCD Storage]
                |                                    |
                v                                    v
         [Audit Logs]                         [Encrypted Backups]
```

---

## 8. Data Breach Procedures

### 8.1 Breach Detection

**Monitoring:**

- Automated intrusion detection
- Log analysis
- Anomaly detection
- User reports

### 8.2 Breach Response (72-hour timeline)

**Hour 0-4: Detection and Containment**

1. Detect and verify breach
2. Contain the breach
3. Assess scope and impact
4. Notify incident response team

**Hour 4-24: Investigation**

1. Identify affected data
2. Determine root cause
3. Document findings
4. Assess risk to data subjects

**Hour 24-72: Notification**

1. Notify supervisory authority (if required)
2. Notify affected data subjects (if high risk)
3. Document breach in register
4. Implement remediation

**Reference:** See [Incident Response](../operations/disaster-recovery-plan.md)

### 8.3 Breach Register

**Required Information:**

- Date and time of breach
- Nature of breach
- Data affected
- Number of data subjects
- Consequences
- Measures taken
- Notifications made

---

## 9. Privacy by Design

### 9.1 Design Principles

**Data Protection by Design:**

- Minimize data collection
- Pseudonymize where possible
- Encrypt sensitive data
- Implement access controls
- Enable data portability
- Facilitate data deletion

**Data Protection by Default:**

- Strictest privacy settings by default
- Opt-in for non-essential processing
- Minimal data sharing
- Short retention periods

### 9.2 Privacy-Enhancing Technologies

**Implemented:**

- ✅ Encryption (at rest and in transit)
- ✅ Pseudonymization
- ✅ Access controls
- ✅ Audit logging
- ✅ Secure deletion

**Planned:**

- 🔄 Homomorphic encryption
- 🔄 Differential privacy
- 🔄 Zero-knowledge proofs

---

## 10. Third-Party Processing

### 10.1 Processor Requirements

**Due Diligence:**

- GDPR compliance verification
- Security assessment
- Data processing agreement
- Regular audits

### 10.2 Data Processing Agreements (DPA)

**Required Clauses:**

- Processing instructions
- Confidentiality obligations
- Security measures
- Sub-processor authorization
- Data subject rights assistance
- Deletion/return of data
- Audit rights

**Template:** See DPA Template

### 10.3 Current Processors

| Processor | Service | Data Processed | DPA Status |
|-----------|---------|----------------|------------|
| [Cloud Provider] | Infrastructure | All data | ✅ Signed |
| [Backup Service] | Backups | Encrypted backups | ✅ Signed |
| [Monitoring Service] | Logs | System logs | ✅ Signed |

---

## 11. International Data Transfers

### 11.1 Transfer Mechanisms

**Within EU/EEA:**

- No additional safeguards required
- Standard GDPR compliance

**To Third Countries:**

- ✅ Adequacy decision (if applicable)
- ✅ Standard Contractual Clauses (SCCs)
- ✅ Binding Corporate Rules (if applicable)
- ✅ Explicit consent (if applicable)

### 11.2 Transfer Impact Assessment

**Assessment Criteria:**

- Legal framework in destination country
- Access by public authorities
- Practical enforceability of rights
- Effective remedies

---

## 12. Compliance Monitoring

### 12.1 Regular Audits

**Audit Schedule:**

- Internal audit: Quarterly
- External audit: Annually
- DPO review: Monthly
- Management review: Quarterly

### 12.2 Compliance Metrics

**Key Performance Indicators:**

- Data subject request response time
- Breach notification compliance
- Training completion rate
- Policy review currency
- Audit findings closure rate

### 12.3 Continuous Improvement

**Process:**

1. Monitor compliance metrics
2. Identify gaps and risks
3. Implement improvements
4. Verify effectiveness
5. Document changes

---

## Appendices

### Appendix A: Definitions

- **Personal Data:** Any information relating to an identified or identifiable natural person
- **Processing:** Any operation performed on personal data
- **Controller:** Entity that determines purposes and means of processing
- **Processor:** Entity that processes data on behalf of controller
- **Data Subject:** Individual whose personal data is processed

### Appendix B: Contact Information

**Data Protection Officer:**

- Email: <dpo@example.com>
- Phone: +{PHONE-NUMBER}

**Supervisory Authority:**

- [National DPA Name]
- Website: [URL]
- Email: [Email]

### Appendix C: Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-28 | Security Team | Initial version |

---

## Certification

This document has been reviewed and approved by:

- **Data Protection Officer:** [Name], [Date]
- **Legal Counsel:** [Name], [Date]
- **Chief Information Security Officer:** [Name], [Date]
- **Management:** [Name], [Date]

---

**Document Classification:** Internal - Confidential
**Next Review Date:** 2026-04-28
**Document Owner:** Data Protection Officer
