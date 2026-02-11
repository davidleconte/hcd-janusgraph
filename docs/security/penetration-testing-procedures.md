# Penetration Testing Procedures

**Version:** 1.0  
**Date:** 2026-02-11  
**Status:** Active

## Overview

This document outlines penetration testing procedures for the HCD + JanusGraph Banking Compliance Platform. These procedures ensure comprehensive security validation before production deployment.

---

## Table of Contents

1. [Pre-Testing Requirements](#pre-testing-requirements)
2. [Testing Scope](#testing-scope)
3. [Testing Methodology](#testing-methodology)
4. [Test Scenarios](#test-scenarios)
5. [Reporting Requirements](#reporting-requirements)
6. [Remediation Process](#remediation-process)

---

## Pre-Testing Requirements

### Authorization

- [ ] Written authorization from system owner
- [ ] Defined testing window and scope
- [ ] Emergency contact information documented
- [ ] Rollback procedures prepared

### Environment Setup

- [ ] Isolated testing environment deployed
- [ ] Production data NOT used (synthetic data only)
- [ ] Monitoring and logging enabled
- [ ] Backup completed before testing

### Tools Required

- **Network Scanning:** nmap, masscan
- **Vulnerability Scanning:** OpenVAS, Nessus, or equivalent
- **Web Application Testing:** OWASP ZAP, Burp Suite
- **Database Testing:** sqlmap (for injection testing)
- **SSL/TLS Testing:** testssl.sh, sslyze
- **Container Security:** trivy, grype
- **Credential Testing:** hydra, medusa (authorized use only)

---

## Testing Scope

### In-Scope Components

1. **API Endpoints**
   - FastAPI REST endpoints
   - GraphQL endpoints (if applicable)
   - Authentication/authorization mechanisms

2. **Network Services**
   - JanusGraph Gremlin Server (port 8182)
   - HCD/Cassandra (port 9042)
   - OpenSearch (ports 9200, 9300)
   - Pulsar (ports 6650, 8080)
   - HashiCorp Vault (port 8200)

3. **Web Interfaces**
   - OpenSearch Dashboards (port 5601)
   - Grafana (port 3001)
   - Prometheus (port 9090)

4. **Container Infrastructure**
   - Docker/Podman containers
   - Container images
   - Network isolation

### Out-of-Scope

- Physical security testing
- Social engineering attacks
- Denial of Service (DoS) attacks
- Testing against production systems
- Third-party services (AWS, cloud providers)

---

## Testing Methodology

### Phase 1: Reconnaissance (Passive)

**Objective:** Gather information without active scanning

**Activities:**
1. Review public documentation
2. Analyze configuration files (from authorized access)
3. Review source code (if available)
4. Identify technology stack
5. Map network architecture

**Tools:**
- Manual review
- Documentation analysis
- Architecture diagrams

**Duration:** 1-2 days

### Phase 2: Scanning (Active)

**Objective:** Identify potential vulnerabilities

**Activities:**
1. Port scanning
2. Service enumeration
3. Vulnerability scanning
4. SSL/TLS configuration testing
5. Container image scanning

**Commands:**

```bash
# Port scanning
nmap -sV -sC -p- <target-ip> -oA nmap-full-scan

# SSL/TLS testing
testssl.sh --full <target-url>

# Container scanning
trivy image <image-name>
grype <image-name>

# Vulnerability scanning (requires OpenVAS/Nessus)
# Configure and run through GUI
```

**Duration:** 2-3 days

### Phase 3: Exploitation (Controlled)

**Objective:** Validate identified vulnerabilities

**Activities:**
1. Authentication bypass attempts
2. Authorization testing
3. Injection attacks (SQL, NoSQL, Gremlin)
4. Cross-Site Scripting (XSS) testing
5. Cross-Site Request Forgery (CSRF) testing
6. API abuse testing
7. Credential stuffing (with test credentials)

**Test Cases:** See [Test Scenarios](#test-scenarios) section

**Duration:** 3-5 days

### Phase 4: Post-Exploitation

**Objective:** Assess impact of successful exploits

**Activities:**
1. Privilege escalation attempts
2. Lateral movement testing
3. Data exfiltration simulation
4. Persistence mechanism testing

**Duration:** 2-3 days

### Phase 5: Reporting

**Objective:** Document findings and recommendations

**Activities:**
1. Compile findings
2. Assess risk levels
3. Provide remediation guidance
4. Create executive summary

**Duration:** 2-3 days

---

## Test Scenarios

### 1. Authentication & Authorization

#### Test 1.1: Brute Force Protection

**Objective:** Verify account lockout mechanisms

**Procedure:**
```bash
# Attempt multiple failed logins
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"wrong'$i'"}'
done

# Verify account is locked after threshold
```

**Expected Result:** Account locked after 5 failed attempts

**Risk if Failed:** HIGH - Brute force attacks possible

#### Test 1.2: JWT Token Security

**Objective:** Verify JWT token implementation

**Procedure:**
```bash
# Obtain valid token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' | jq -r '.access_token')

# Test token manipulation
# 1. Modify payload
# 2. Change signature
# 3. Use expired token
# 4. Use token with different user

# Decode and analyze token
echo $TOKEN | cut -d. -f2 | base64 -d | jq
```

**Expected Result:** All manipulated tokens rejected

**Risk if Failed:** CRITICAL - Authentication bypass

#### Test 1.3: Role-Based Access Control (RBAC)

**Objective:** Verify authorization enforcement

**Procedure:**
```bash
# Login as regular user
USER_TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"userpass"}' | jq -r '.access_token')

# Attempt admin-only operations
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"hacker","role":"admin"}'
```

**Expected Result:** 403 Forbidden

**Risk if Failed:** CRITICAL - Privilege escalation

### 2. Injection Attacks

#### Test 2.1: Gremlin Injection

**Objective:** Verify query sanitization

**Procedure:**
```bash
# Test Gremlin injection in search
curl -X GET "http://localhost:8000/api/v1/persons/search?name=test');g.V().drop();g.V('test" \
  -H "Authorization: Bearer $TOKEN"

# Test in graph traversal
curl -X POST http://localhost:8000/api/v1/graph/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"g.V().has(\"name\", \"test\");g.V().drop();"}'
```

**Expected Result:** Query rejected or sanitized

**Risk if Failed:** CRITICAL - Data manipulation/deletion

#### Test 2.2: NoSQL Injection (OpenSearch)

**Objective:** Verify OpenSearch query sanitization

**Procedure:**
```bash
# Test injection in search
curl -X POST http://localhost:9200/persons/_search \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "query_string": {
        "query": "name:test OR 1=1"
      }
    }
  }'
```

**Expected Result:** Query sanitized or rejected

**Risk if Failed:** HIGH - Unauthorized data access

#### Test 2.3: Command Injection

**Objective:** Verify input validation in system commands

**Procedure:**
```bash
# Test in file upload/processing endpoints
curl -X POST http://localhost:8000/api/v1/import \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.csv; cat /etc/passwd"
```

**Expected Result:** Command rejected

**Risk if Failed:** CRITICAL - Remote code execution

### 3. Cryptography & SSL/TLS

#### Test 3.1: SSL/TLS Configuration

**Objective:** Verify strong encryption

**Procedure:**
```bash
# Test SSL/TLS configuration
testssl.sh --full https://localhost:8182

# Check for:
# - TLS 1.2+ only
# - Strong cipher suites
# - Valid certificates
# - No SSL/TLS vulnerabilities (POODLE, BEAST, etc.)
```

**Expected Result:** A+ rating, no vulnerabilities

**Risk if Failed:** HIGH - Man-in-the-middle attacks

#### Test 3.2: Certificate Validation

**Objective:** Verify certificate validation

**Procedure:**
```bash
# Test with self-signed certificate
curl -k https://localhost:8182  # Should fail without -k

# Test with expired certificate
# Test with wrong hostname
```

**Expected Result:** Connections rejected without valid cert

**Risk if Failed:** MEDIUM - MITM attacks possible

### 4. Secrets Management

#### Test 4.1: Vault Access Control

**Objective:** Verify Vault security

**Procedure:**
```bash
# Attempt to access Vault without token
curl http://localhost:8200/v1/secret/data/janusgraph/admin

# Attempt to access with invalid token
curl -H "X-Vault-Token: invalid" \
  http://localhost:8200/v1/secret/data/janusgraph/admin

# Attempt to access secrets outside policy scope
```

**Expected Result:** All unauthorized access denied

**Risk if Failed:** CRITICAL - Credential exposure

#### Test 4.2: Credential Exposure

**Objective:** Verify no hardcoded credentials

**Procedure:**
```bash
# Search for hardcoded credentials
grep -r -i "password\s*=\s*['\"]" src/ banking/
grep -r -i "api_key\s*=\s*['\"]" src/ banking/
grep -r -i "secret\s*=\s*['\"]" src/ banking/

# Check environment files
cat .env | grep -i "changeit\|password\|YOUR_"
```

**Expected Result:** No hardcoded credentials found

**Risk if Failed:** CRITICAL - Credential exposure

### 5. Network Security

#### Test 5.1: Network Isolation

**Objective:** Verify container network isolation

**Procedure:**
```bash
# Test cross-network access
podman exec janusgraph-container curl http://vault-container:8200

# Test external access to internal services
curl http://localhost:9042  # Cassandra (should not be exposed)
curl http://localhost:7199  # JMX (should not be exposed)
```

**Expected Result:** Unauthorized access blocked

**Risk if Failed:** HIGH - Lateral movement possible

#### Test 5.2: Port Exposure

**Objective:** Verify only necessary ports exposed

**Procedure:**
```bash
# Scan exposed ports
nmap -p- localhost

# Verify only expected ports open:
# - 8182 (JanusGraph)
# - 9200 (OpenSearch)
# - 8000 (API)
# - 3001 (Grafana)
# - 5601 (Dashboards)
```

**Expected Result:** Only necessary ports exposed

**Risk if Failed:** MEDIUM - Increased attack surface

### 6. API Security

#### Test 6.1: Rate Limiting

**Objective:** Verify rate limiting implementation

**Procedure:**
```bash
# Send rapid requests
for i in {1..100}; do
  curl -X GET http://localhost:8000/api/v1/persons \
    -H "Authorization: Bearer $TOKEN" &
done
wait

# Check for rate limit responses (429)
```

**Expected Result:** Rate limiting enforced

**Risk if Failed:** MEDIUM - API abuse possible

#### Test 6.2: Input Validation

**Objective:** Verify input validation

**Procedure:**
```bash
# Test with oversized input
curl -X POST http://localhost:8000/api/v1/persons \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"'$(python -c 'print("A"*10000)')'"}'

# Test with invalid data types
curl -X POST http://localhost:8000/api/v1/persons \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":12345,"age":"not_a_number"}'
```

**Expected Result:** Invalid input rejected

**Risk if Failed:** MEDIUM - Data corruption possible

### 7. Container Security

#### Test 7.1: Container Escape

**Objective:** Verify container isolation

**Procedure:**
```bash
# Attempt to access host filesystem
podman exec janusgraph-container ls /host

# Attempt privileged operations
podman exec janusgraph-container mount

# Check for privileged containers
podman inspect janusgraph-container | grep -i privileged
```

**Expected Result:** Container escape prevented

**Risk if Failed:** CRITICAL - Host compromise

#### Test 7.2: Image Vulnerabilities

**Objective:** Verify container images are secure

**Procedure:**
```bash
# Scan all images
for image in $(podman images --format "{{.Repository}}:{{.Tag}}"); do
  echo "Scanning $image..."
  trivy image --severity HIGH,CRITICAL $image
done
```

**Expected Result:** No HIGH/CRITICAL vulnerabilities

**Risk if Failed:** HIGH - Exploitable vulnerabilities

---

## Reporting Requirements

### Report Structure

1. **Executive Summary**
   - Overall security posture
   - Critical findings count
   - Risk assessment
   - Recommendations

2. **Methodology**
   - Testing approach
   - Tools used
   - Scope and limitations

3. **Findings**
   - For each finding:
     - Title
     - Severity (Critical/High/Medium/Low)
     - Description
     - Proof of Concept
     - Impact
     - Remediation steps
     - CVSS score (if applicable)

4. **Appendices**
   - Detailed test results
   - Screenshots
   - Log excerpts
   - Tool outputs

### Severity Classification

| Severity | Criteria | Response Time |
|----------|----------|---------------|
| **Critical** | Remote code execution, authentication bypass, data breach | Immediate (24h) |
| **High** | Privilege escalation, sensitive data exposure | 7 days |
| **Medium** | Information disclosure, DoS | 30 days |
| **Low** | Minor configuration issues | 90 days |

---

## Remediation Process

### 1. Triage (Day 1)

- Review all findings
- Validate findings
- Assign severity
- Prioritize remediation

### 2. Remediation Planning (Days 2-3)

- Create remediation tickets
- Assign owners
- Set deadlines based on severity
- Allocate resources

### 3. Implementation (Days 4-14)

- Fix critical findings immediately
- Address high findings within 7 days
- Plan medium/low findings

### 4. Verification (Days 15-21)

- Re-test all fixed findings
- Verify no regression
- Update documentation

### 5. Re-Testing (Days 22-30)

- Full penetration test re-run
- Verify all findings resolved
- Generate final report

---

## Automated Testing Script

Save as `scripts/security/run_pentest.sh`:

```bash
#!/bin/bash
# Automated Penetration Testing Script

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/docs/implementation/audits/security/pentest"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

mkdir -p "$REPORT_DIR"

echo "Starting automated penetration testing..."
echo "Report directory: $REPORT_DIR"

# 1. Port Scanning
echo "[1/7] Running port scan..."
nmap -sV -sC -p- localhost -oA "$REPORT_DIR/nmap-$TIMESTAMP" || true

# 2. SSL/TLS Testing
echo "[2/7] Testing SSL/TLS configuration..."
testssl.sh --full https://localhost:8182 > "$REPORT_DIR/testssl-$TIMESTAMP.txt" || true

# 3. Container Scanning
echo "[3/7] Scanning container images..."
for image in $(podman images --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>"); do
    echo "  Scanning $image..."
    trivy image --severity HIGH,CRITICAL "$image" > "$REPORT_DIR/trivy-$(echo $image | tr '/:' '-')-$TIMESTAMP.txt" || true
done

# 4. Dependency Scanning
echo "[4/7] Scanning dependencies..."
cd "$PROJECT_ROOT"
uv tool run pip-audit -r requirements.txt > "$REPORT_DIR/pip-audit-$TIMESTAMP.txt" || true

# 5. Code Security Scan
echo "[5/7] Running code security scan..."
uv tool run bandit -r src/ banking/ -f json -o "$REPORT_DIR/bandit-$TIMESTAMP.json" || true

# 6. Secrets Scanning
echo "[6/7] Scanning for secrets..."
detect-secrets scan --all-files > "$REPORT_DIR/secrets-$TIMESTAMP.json" || true

# 7. OWASP ZAP (if available)
echo "[7/7] Running OWASP ZAP scan..."
if command -v zap-cli &> /dev/null; then
    zap-cli quick-scan --self-contained http://localhost:8000 \
        -o "$REPORT_DIR/zap-$TIMESTAMP.html" || true
else
    echo "  OWASP ZAP not installed, skipping..."
fi

echo "Penetration testing complete!"
echo "Reports saved to: $REPORT_DIR"
```

---

## Compliance Mapping

| Test Scenario | GDPR | SOC 2 | PCI DSS | BSA/AML |
|---------------|------|-------|---------|---------|
| Authentication & Authorization | ✓ | ✓ | ✓ | ✓ |
| Injection Attacks | ✓ | ✓ | ✓ | ✓ |
| Cryptography & SSL/TLS | ✓ | ✓ | ✓ | - |
| Secrets Management | ✓ | ✓ | ✓ | ✓ |
| Network Security | - | ✓ | ✓ | - |
| API Security | ✓ | ✓ | ✓ | ✓ |
| Container Security | - | ✓ | ✓ | - |

---

## References

- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST SP 800-115: Technical Guide to Information Security Testing](https://csrc.nist.gov/publications/detail/sp/800-115/final)
- [PTES: Penetration Testing Execution Standard](http://www.pentest-standard.org/)
- [CIS Controls](https://www.cisecurity.org/controls/)

---

**Last Updated:** 2026-02-11  
**Next Review:** 2026-05-11  
**Owner:** Security Team