# Incident Response Procedures

**Version:** 1.0  
**Date:** 2026-02-11  
**Status:** Active  
**Owner:** Security & Operations Team

---

## Table of Contents

1. [Overview](#overview)
2. [Incident Classification](#incident-classification)
3. [Response Team](#response-team)
4. [Incident Response Process](#incident-response-process)
5. [Incident Types](#incident-types)
6. [Communication Protocols](#communication-protocols)
7. [Post-Incident Activities](#post-incident-activities)
8. [Compliance Requirements](#compliance-requirements)

---

## Overview

This document defines incident response procedures for the HCD + JanusGraph Banking Compliance Platform. It ensures rapid, coordinated response to security incidents, data breaches, and operational disruptions.

### Objectives

- **Minimize Impact:** Reduce damage and recovery time
- **Preserve Evidence:** Maintain forensic integrity
- **Ensure Compliance:** Meet regulatory requirements (GDPR, SOC 2, PCI DSS, BSA/AML)
- **Continuous Improvement:** Learn from incidents

### Scope

This procedure covers:
- Security incidents (breaches, attacks, unauthorized access)
- Data incidents (loss, corruption, unauthorized disclosure)
- Operational incidents (outages, performance degradation)
- Compliance incidents (regulatory violations)

---

## Incident Classification

### Severity Levels

| Level | Description | Response Time | Escalation |
|-------|-------------|---------------|------------|
| **P1 - Critical** | Production down, data breach, active attack | Immediate (15 min) | Executive team |
| **P2 - High** | Significant degradation, potential breach | 1 hour | Management |
| **P3 - Medium** | Partial degradation, security concern | 4 hours | Team lead |
| **P4 - Low** | Minor issue, no immediate impact | 24 hours | Standard |

### Incident Categories

1. **Security Incidents**
   - Unauthorized access
   - Malware/ransomware
   - DDoS attacks
   - Credential compromise
   - Insider threats

2. **Data Incidents**
   - Data breach
   - Data loss
   - Data corruption
   - Unauthorized disclosure
   - Privacy violations

3. **Operational Incidents**
   - Service outages
   - Performance degradation
   - Infrastructure failures
   - Configuration errors

4. **Compliance Incidents**
   - Regulatory violations
   - Audit findings
   - Policy breaches
   - Reporting failures

---

## Response Team

### Incident Response Team (IRT)

| Role | Responsibilities | Contact |
|------|------------------|---------|
| **Incident Commander** | Overall coordination, decision-making | On-call rotation |
| **Security Lead** | Security analysis, containment | security@example.com |
| **Operations Lead** | System recovery, infrastructure | ops@example.com |
| **Compliance Officer** | Regulatory requirements, notifications | compliance@example.com |
| **Communications Lead** | Internal/external communications | comms@example.com |
| **Legal Counsel** | Legal implications, liability | legal@example.com |

### On-Call Schedule

- **Primary:** 24/7 on-call rotation
- **Secondary:** Backup responder
- **Escalation:** Management chain

### Contact Information

```
Emergency Hotline: +1-XXX-XXX-XXXX
Incident Email: incidents@example.com
Slack Channel: #incident-response
PagerDuty: https://example.pagerduty.com
```

---

## Incident Response Process

### Phase 1: Detection & Reporting (0-15 minutes)

**Objectives:**
- Identify potential incident
- Initial assessment
- Activate response team

**Actions:**

1. **Detect Incident**
   - Monitoring alerts (Prometheus, Grafana)
   - User reports
   - Security scans
   - Audit log analysis

2. **Report Incident**
   ```bash
   # Report via Slack
   /incident create severity=P1 title="Data breach detected"
   
   # Or via email
   To: incidents@example.com
   Subject: [P1] Data breach detected in production
   ```

3. **Initial Assessment**
   - Verify incident is real (not false positive)
   - Determine severity level
   - Identify affected systems
   - Estimate impact

4. **Activate Response Team**
   - Page on-call responder
   - Notify Incident Commander
   - Assemble response team based on severity

**Checklist:**
- [ ] Incident detected and verified
- [ ] Severity level assigned
- [ ] Response team notified
- [ ] Incident ticket created
- [ ] Initial timeline started

### Phase 2: Containment (15 minutes - 2 hours)

**Objectives:**
- Stop incident from spreading
- Preserve evidence
- Minimize damage

**Actions:**

1. **Short-term Containment**
   ```bash
   # Isolate affected systems
   podman stop <compromised-container>
   
   # Block malicious IPs
   iptables -A INPUT -s <malicious-ip> -j DROP
   
   # Disable compromised accounts
   vault write auth/userpass/users/<user>/password password=DISABLED
   
   # Enable enhanced logging
   kubectl logs -f <pod> --tail=1000 > incident-logs.txt
   ```

2. **Evidence Preservation**
   ```bash
   # Capture system state
   podman inspect <container> > container-state.json
   
   # Backup logs
   tar -czf incident-logs-$(date +%Y%m%d-%H%M%S).tar.gz /var/log/
   
   # Memory dump (if needed)
   gcore <pid>
   
   # Network capture
   tcpdump -i any -w incident-capture.pcap
   ```

3. **Impact Assessment**
   - Identify affected data
   - Count affected users
   - Assess data sensitivity
   - Determine breach scope

4. **Long-term Containment**
   - Patch vulnerabilities
   - Update firewall rules
   - Rotate credentials
   - Deploy security updates

**Checklist:**
- [ ] Incident contained
- [ ] Evidence preserved
- [ ] Impact assessed
- [ ] Affected systems identified
- [ ] Stakeholders notified

### Phase 3: Eradication (2-24 hours)

**Objectives:**
- Remove threat completely
- Fix vulnerabilities
- Prevent recurrence

**Actions:**

1. **Root Cause Analysis**
   - Analyze logs and evidence
   - Identify attack vector
   - Determine vulnerability exploited
   - Timeline reconstruction

2. **Remove Threat**
   ```bash
   # Remove malware
   podman rm -f <compromised-container>
   
   # Clean infected files
   find /data -name "*.malware" -delete
   
   # Rebuild from clean images
   podman pull <image>:latest
   podman run -d <image>:latest
   ```

3. **Fix Vulnerabilities**
   ```bash
   # Apply security patches
   uv pip install --upgrade <vulnerable-package>
   
   # Update configurations
   vim config/security.yaml
   
   # Regenerate certificates
   ./scripts/security/generate_certificates.sh
   ```

4. **Verify Eradication**
   - Scan for remaining threats
   - Verify patches applied
   - Test security controls
   - Confirm no backdoors

**Checklist:**
- [ ] Root cause identified
- [ ] Threat removed
- [ ] Vulnerabilities patched
- [ ] Systems verified clean
- [ ] Security controls tested

### Phase 4: Recovery (4-48 hours)

**Objectives:**
- Restore normal operations
- Verify system integrity
- Monitor for recurrence

**Actions:**

1. **Restore Services**
   ```bash
   # Restore from backup
   ./scripts/backup/restore_volumes.sh
   
   # Restart services
   cd config/compose
   podman-compose -p janusgraph-demo up -d
   
   # Verify health
   ./scripts/hcd/health_check.sh
   ```

2. **Verify Integrity**
   ```bash
   # Check data integrity
   python scripts/validation/verify_data_integrity.py
   
   # Verify configurations
   diff config/production.yaml config/backup.yaml
   
   # Test functionality
   pytest tests/integration/ -v
   ```

3. **Enhanced Monitoring**
   ```bash
   # Enable detailed logging
   export LOG_LEVEL=DEBUG
   
   # Monitor for anomalies
   tail -f /var/log/audit.log | grep -i "suspicious"
   
   # Watch metrics
   watch -n 5 'curl -s http://localhost:9090/api/v1/query?query=up'
   ```

4. **Gradual Restoration**
   - Restore non-critical services first
   - Monitor each restoration
   - Verify no issues before proceeding
   - Full restoration only when confident

**Checklist:**
- [ ] Services restored
- [ ] Data integrity verified
- [ ] Functionality tested
- [ ] Enhanced monitoring active
- [ ] Users notified of restoration

### Phase 5: Post-Incident (1-7 days)

**Objectives:**
- Document lessons learned
- Improve defenses
- Meet compliance requirements

**Actions:**

1. **Post-Incident Review**
   - Schedule review meeting (within 48 hours)
   - Review timeline and actions
   - Identify what went well
   - Identify areas for improvement

2. **Documentation**
   ```markdown
   # Incident Report Template
   
   ## Incident Summary
   - **Incident ID:** INC-2026-001
   - **Date/Time:** 2026-02-11 10:30 UTC
   - **Severity:** P1
   - **Duration:** 4 hours
   - **Status:** Resolved
   
   ## Timeline
   - 10:30 - Incident detected
   - 10:35 - Response team activated
   - 10:45 - Containment achieved
   - 12:00 - Threat eradicated
   - 14:30 - Services restored
   
   ## Root Cause
   [Detailed analysis]
   
   ## Impact
   - Affected systems: [list]
   - Affected users: [count]
   - Data compromised: [details]
   
   ## Actions Taken
   [Detailed actions]
   
   ## Lessons Learned
   [What we learned]
   
   ## Recommendations
   [Improvements needed]
   ```

3. **Compliance Notifications**
   
   **GDPR (Article 33):**
   - Notify supervisory authority within 72 hours
   - Include nature of breach, affected data, likely consequences
   - Describe measures taken
   
   **GDPR (Article 34):**
   - Notify affected individuals if high risk
   - Provide clear information about breach
   - Advise on protective measures
   
   **PCI DSS:**
   - Notify payment brands immediately
   - Notify acquiring bank
   - Forensic investigation required
   
   **SOC 2:**
   - Notify customers per contract
   - Update SOC 2 report
   - Document in audit trail

4. **Improvement Actions**
   - Update security controls
   - Enhance monitoring
   - Improve procedures
   - Conduct training
   - Schedule follow-up review

**Checklist:**
- [ ] Post-incident review completed
- [ ] Incident report documented
- [ ] Compliance notifications sent
- [ ] Improvements implemented
- [ ] Team debriefed

---

## Incident Types

### Data Breach

**Definition:** Unauthorized access to or disclosure of personal/sensitive data

**Immediate Actions:**
1. Isolate affected systems
2. Identify compromised data
3. Assess breach scope
4. Preserve evidence
5. Notify legal/compliance

**Compliance Requirements:**
- GDPR: 72-hour notification to supervisory authority
- State laws: Varies by jurisdiction
- PCI DSS: Immediate notification to payment brands

**Example Response:**
```bash
# 1. Isolate database
podman stop janusgraph-demo_hcd-server_1

# 2. Capture evidence
podman logs janusgraph-demo_hcd-server_1 > breach-logs.txt

# 3. Identify affected records
python scripts/incident/identify_affected_records.py

# 4. Generate breach report
python scripts/compliance/generate_breach_report.py
```

### Ransomware Attack

**Definition:** Malware that encrypts data and demands ransom

**Immediate Actions:**
1. Isolate infected systems immediately
2. Do NOT pay ransom
3. Identify ransomware variant
4. Restore from backups
5. Report to law enforcement

**Example Response:**
```bash
# 1. Immediate isolation
podman stop $(podman ps -q)

# 2. Identify variant
sha256sum /path/to/ransomware > ransomware-hash.txt

# 3. Check backups
./scripts/backup/verify_backups.sh

# 4. Restore from clean backup
./scripts/backup/restore_volumes.sh --date 2026-02-10
```

### DDoS Attack

**Definition:** Distributed Denial of Service attack

**Immediate Actions:**
1. Activate DDoS mitigation (CloudFlare, AWS Shield)
2. Implement rate limiting
3. Block malicious IPs
4. Scale infrastructure if needed
5. Monitor attack patterns

**Example Response:**
```bash
# 1. Enable rate limiting
kubectl apply -f config/rate-limiting.yaml

# 2. Block attack sources
iptables -A INPUT -s <attack-ip> -j DROP

# 3. Scale up
kubectl scale deployment api --replicas=10
```

### Insider Threat

**Definition:** Malicious or negligent actions by authorized users

**Immediate Actions:**
1. Disable user access immediately
2. Preserve audit logs
3. Review user activity
4. Assess data accessed
5. Involve HR/Legal

**Example Response:**
```bash
# 1. Disable access
vault write auth/userpass/users/<user>/password password=DISABLED

# 2. Review activity
grep "<user>" /var/log/audit.log > insider-activity.txt

# 3. Identify accessed data
python scripts/audit/user_activity_report.py --user <user>
```

---

## Communication Protocols

### Internal Communications

**Incident Channel:** #incident-response (Slack)

**Status Updates:**
- Every 30 minutes during active incident
- Include: current status, actions taken, next steps
- Tag relevant stakeholders

**Template:**
```
🚨 INCIDENT UPDATE - [Severity] - [Time]

Status: [Investigating/Contained/Resolved]
Impact: [Description]
Actions Taken: [List]
Next Steps: [List]
ETA: [Estimate]

Incident Commander: @user
```

### External Communications

**Customer Notifications:**
- Coordinate with Communications Lead
- Approved by Legal
- Clear, honest, actionable
- Multiple channels (email, status page, social media)

**Template:**
```
Subject: Service Incident Notification

Dear Customer,

We are writing to inform you of a service incident that occurred on [date].

What Happened:
[Brief description]

Impact:
[What was affected]

Actions Taken:
[What we did]

Your Action Required:
[If any]

We apologize for any inconvenience and are committed to preventing future incidents.

For questions, contact: support@example.com
```

**Regulatory Notifications:**
- Use official templates
- Include all required information
- Submit within required timeframes
- Maintain proof of notification

---

## Post-Incident Activities

### Incident Report

**Required Sections:**
1. Executive Summary
2. Incident Timeline
3. Root Cause Analysis
4. Impact Assessment
5. Response Actions
6. Lessons Learned
7. Recommendations
8. Appendices (logs, evidence)

### Lessons Learned Meeting

**Agenda:**
1. Incident overview (10 min)
2. Timeline review (15 min)
3. What went well (15 min)
4. What could improve (20 min)
5. Action items (10 min)
6. Follow-up plan (10 min)

**Participants:**
- Incident Response Team
- Management
- Affected teams
- External experts (if applicable)

### Improvement Actions

**Categories:**
1. **Technical:** Security controls, monitoring, automation
2. **Process:** Procedures, documentation, training
3. **People:** Skills, staffing, communication
4. **Tools:** Software, hardware, services

**Tracking:**
- Create tickets for each action
- Assign owners and deadlines
- Regular status reviews
- Verify completion

---

## Compliance Requirements

### GDPR

**Article 33 - Breach Notification:**
- Notify supervisory authority within 72 hours
- Include: nature, categories, approximate numbers
- Describe likely consequences and measures taken

**Article 34 - Individual Notification:**
- Notify individuals if high risk to rights and freedoms
- Clear and plain language
- Describe nature of breach and protective measures

### SOC 2

**CC7.3 - Incident Response:**
- Documented incident response plan
- Regular testing and updates
- Incident logging and tracking
- Post-incident reviews

### PCI DSS

**Requirement 12.10 - Incident Response:**
- Incident response plan
- Roles and responsibilities
- Communication procedures
- Forensic investigation procedures
- Annual testing

### BSA/AML

**Suspicious Activity Reporting:**
- File SAR within 30 days of detection
- Maintain confidentiality
- Document investigation
- Preserve records for 5 years

---

## Appendices

### A. Contact Lists

[Maintain current contact information]

### B. Incident Response Tools

```bash
# Forensics
- Volatility (memory analysis)
- Autopsy (disk analysis)
- Wireshark (network analysis)

# Monitoring
- Prometheus
- Grafana
- ELK Stack

# Communication
- Slack
- PagerDuty
- Email
```

### C. Compliance Notification Templates

[Maintain templates for each regulation]

### D. Incident Response Checklist

[Quick reference checklist for responders]

---

**Last Updated:** 2026-02-11  
**Next Review:** 2026-05-11  
**Version:** 1.0  
**Owner:** Security Team