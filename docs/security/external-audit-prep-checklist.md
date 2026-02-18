# External Security Audit Preparation Checklist

**Date:** 2026-02-12
**Version:** 2.0
**Status:** Active
**Previous Audit:** 2026-02-11 (Rating: A- 91/100)

## TL;DR

Pre-audit preparation checklist for the next external security assessment. Tracks remediation of prior findings and readiness of new features (MFA, Performance API) for audit scope.

---

## Prior Audit Findings — Remediation Status

### From External Audit Report (2026-02-11)

| # | Finding | Severity | Status | Evidence |
|---|---------|----------|--------|----------|
| 1 | MFA not implemented | MEDIUM | ✅ **RESOLVED** | `src/python/api/routers/auth.py` — TOTP enrollment, verification, lockout |
| 2 | Security headers could be strengthened | MEDIUM | ⚠️ **PENDING** | Need `SecurityHeadersMiddleware` in FastAPI |
| 3 | Dependencies with known CVEs | MEDIUM | ⚠️ **VERIFY** | Run `uv pip audit` before audit |
| 4 | OpenSearch security disabled in dev | LOW | ✅ **BY DESIGN** | Production config enables security plugin |
| 5 | Rate limiting not granular enough | LOW | ✅ **IMPROVED** | Per-endpoint limits on all new routers |
| 6 | Verbose error messages | LOW | ✅ **RESOLVED** | Generic error handler in `main.py` |
| 7 | No image vulnerability scanning in CI | LOW | ⚠️ **PENDING** | Add Trivy to CI pipeline |

### New Features Since Last Audit

| Feature | Module | Security Considerations |
|---------|--------|----------------------|
| MFA (TOTP) | `src/python/api/routers/auth.py` | Secret storage, backup codes, lockout policy |
| Performance API | `src/python/api/routers/performance.py` | Rate-limited, auth-protected, no sensitive data exposure |
| Query Profiler | `src/python/performance/query_profiler.py` | Query text logged — verify no PII in queries |
| Query Cache | `src/python/performance/query_cache.py` | Cached results could contain sensitive data — TTL enforced |
| Horizontal Scaling | `docs/architecture/horizontal-scaling-strategy.md` | Distributed rate limiting recommendation (Redis) |

---

## Pre-Audit Checklist

### 1. Code Security (1-2 days before)

```bash
# Activate environment
conda activate janusgraph-analysis

# Static analysis
uv tool run bandit -r src/ banking/ -ll -f json -o audit-prep/bandit-results.json

# Dependency audit
uv tool run pip-audit -r requirements.txt -o audit-prep/pip-audit-results.json

# Secret scanning
detect-secrets scan --all-files > audit-prep/secrets-scan.json

# Dead code analysis
uv tool run vulture src/ banking/ --min-confidence 80 > audit-prep/dead-code.txt

# Type checking
uv tool run mypy src/python banking/ --ignore-missing-imports > audit-prep/mypy-results.txt 2>&1
```

- [ ] Bandit: 0 high/critical findings
- [ ] pip-audit: 0 known vulnerabilities (or documented exceptions)
- [ ] detect-secrets: No new secrets detected
- [ ] vulture: No dead code with credentials
- [ ] mypy: No type errors in security-critical modules

### 2. Authentication & Authorization

- [ ] MFA enrollment flow tested end-to-end
- [ ] MFA lockout after failed attempts verified (default: 5 attempts, 15 min lockout)
- [ ] Backup codes generation and single-use verified
- [ ] JWT token expiration enforced
- [ ] RBAC permissions tested for all roles (admin, analyst, viewer)
- [ ] Bearer token required on all protected endpoints
- [ ] No default credentials in startup validation (`startup_validation.py`)

**Verification Commands:**
```bash
# Test MFA enrollment
curl -X POST http://localhost:8000/api/v1/auth/mfa/enroll \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-user","email":"test@example.com","method":"totp"}'

# Test rate limiting (should get 429 after threshold)
for i in $(seq 1 100); do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/auth/mfa/status/test
done | sort | uniq -c
```

### 3. Input Validation & Injection Prevention

- [ ] Query sanitizer blocks Gremlin injection patterns
- [ ] Pydantic models validate all API inputs
- [ ] No string concatenation in Gremlin queries (use parameterized)
- [ ] Log sanitizer masks PII (credit cards, SSN, emails)
- [ ] Path traversal protection in file operations

**Verification:**
```bash
# Test Gremlin injection (should be rejected)
curl -X GET "http://localhost:8000/api/v1/persons/search?name=test');g.V().drop()" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Data Protection

- [ ] SSL/TLS certificates valid and not expiring within 30 days
- [ ] Encryption at rest configured for HCD/Cassandra
- [ ] OpenSearch encryption configured
- [ ] Vault initialized and unsealed
- [ ] All secrets stored in Vault (not environment variables in production)
- [ ] Log sanitizer active in production logging config

**Verification:**
```bash
# Check certificate expiry
./scripts/security/generate_certificates.sh --check-only

# Verify Vault status
podman exec janusgraph-demo_vault-server_1 vault status
```

### 5. API Security

- [ ] Rate limiting active on all endpoints (verify with load test)
- [ ] CORS configured with specific origins (not `*` in production)
- [ ] Security headers present:
  - [ ] `X-Content-Type-Options: nosniff`
  - [ ] `X-Frame-Options: DENY`
  - [ ] `Strict-Transport-Security` (if HTTPS)
  - [ ] `Content-Security-Policy`
  - [ ] `Referrer-Policy`
- [ ] Error responses don't leak stack traces in production
- [ ] Performance endpoints don't expose sensitive query data

**Verification:**
```bash
# Check response headers
curl -I http://localhost:8000/healthz

# Verify error handling (should be generic)
curl http://localhost:8000/nonexistent-endpoint
```

### 6. Container & Infrastructure Security

- [ ] All container images pinned to specific versions (no `:latest`)
- [ ] No privileged containers
- [ ] Resource limits set on all containers
- [ ] Network isolation verified (custom bridge network)
- [ ] JMX port not exposed externally
- [ ] Podman rootless mode active

**Verification:**
```bash
# Check for latest tags
podman images --format "{{.Repository}}:{{.Tag}}" | grep latest

# Check privileged status
podman inspect --format '{{.HostConfig.Privileged}}' $(podman ps -q)

# Verify network isolation
podman network ls | grep janusgraph-demo
```

### 7. Monitoring & Audit Logging

- [ ] Audit logger active with 30+ event types
- [ ] Failed authentication attempts logged
- [ ] Data access logged
- [ ] GDPR-relevant events captured
- [ ] Prometheus metrics collecting
- [ ] Alert rules active (31+ rules)
- [ ] Log rotation configured

**Verification:**
```bash
# Verify audit logger
python -c "from banking.compliance.audit_logger import get_audit_logger; print('OK')"

# Check Prometheus
curl -s http://localhost:9090/-/healthy

# Check alert rules
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups | length'
```

### 8. Test Coverage & Quality

- [ ] Test suite passes: `pytest --tb=short --no-cov -q`
- [ ] Coverage report generated: `pytest --cov=src --cov=banking --cov-report=html`
- [ ] No skipped security-critical tests
- [ ] Performance module tests passing (65+ tests)

**Current Coverage Snapshot:**
```
Module                     Coverage
───────────────────────────────────
performance/query_profiler   97%
performance/query_cache      94%
performance/benchmark        95%
security/mfa                 (verify)
security/rbac                (verify)
security/query_sanitizer     (verify)
```

### 9. Documentation Readiness

- [ ] Security architecture documented
- [ ] DR plan current: [`disaster-recovery-plan.md`](../operations/disaster-recovery-plan.md)
- [ ] DR drill log maintained: [`dr-testing-log.md`](../operations/dr-testing-log.md)
- [ ] Penetration testing procedures: [`penetration-testing-procedures.md`](penetration-testing-procedures.md)
- [ ] Compliance docs (GDPR, SOC 2, PCI DSS, BSA/AML) current
- [ ] AGENTS.md updated with security practices
- [ ] Horizontal scaling strategy documented

### 10. Compliance Readiness

| Regulation | Status | Key Evidence |
|-----------|--------|--------------|
| **GDPR** | ✅ Compliant | Audit logger, deletion support, portability |
| **PCI DSS** | ✅ Compliant | MFA implemented, encryption, audit logging |
| **SOC 2** | ✅ Compliant | Access controls, monitoring, incident response |
| **BSA/AML** | ✅ Compliant | Transaction monitoring, SAR reporting |

---

## Audit Day Preparation

### Environment Setup (Morning of Audit)

```bash
# 1. Ensure all services running
cd config/compose
podman-compose -p janusgraph-demo -f <full-stack-compose-file> ps

# 2. Verify health
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz

# 3. Verify monitoring
curl http://localhost:9090/-/healthy
curl http://localhost:3001/api/health

# 4. Run preflight validation
./scripts/validation/preflight_check.sh

# 5. Generate fresh test coverage report
conda activate janusgraph-analysis
pytest --cov=src --cov=banking --cov-report=html -q
```

### Documents to Have Ready

1. Previous audit report: [`external-security-audit-report-2026-02-11.md`](external-security-audit-report-2026-02-11.md)
2. Remediation evidence (this checklist)
3. Architecture diagrams: [`docs/architecture/`](../architecture/)
4. DR test results: [`dr-testing-log.md`](../operations/dr-testing-log.md)
5. Compliance reports: [`docs/compliance/`](../compliance/)
6. Test coverage HTML report: `htmlcov/index.html`

### Key Contacts

| Role | Name | Availability |
|------|------|-------------|
| Technical Lead | TBD | On-site |
| Security Lead | TBD | On-site |
| Infrastructure | TBD | On-call |
| Compliance | TBD | On-call |

---

## Expected Audit Score Improvement

| Category | Previous (2026-02-11) | Expected (Next) | Change |
|----------|----------------------|-----------------|--------|
| Authentication & Authorization | 95 | 98 | +3 (MFA complete) |
| Input Validation | 98 | 98 | — |
| Data Protection | 94 | 95 | +1 |
| Secrets Management | 95 | 95 | — |
| API Security | 90 | 94 | +4 (headers, perf API) |
| Container Security | 94 | 95 | +1 (image scanning) |
| Monitoring & Logging | 98 | 98 | — |
| Compliance | 96 | 98 | +2 (MFA for PCI DSS) |
| Penetration Testing | 93 | 95 | +2 |
| Dependency Security | 90 | 93 | +3 (updates) |
| **Overall** | **A- (91)** | **A (96)** | **+5** |

---

## Pending Items Before Next Audit

| # | Item | Priority | Effort | Owner | Status |
|---|------|----------|--------|-------|--------|
| 1 | Add SecurityHeadersMiddleware | P1 | 2 hours | — | TODO |
| 2 | Run `uv pip audit` and fix CVEs | P1 | 1 hour | — | TODO |
| 3 | Add Trivy image scanning to CI | P2 | 4 hours | — | TODO |
| 4 | Execute first DR drill and record results | P1 | 2 hours | — | TODO |
| 5 | Verify MFA with real authenticator app | P1 | 30 min | — | TODO |

---

## Related Documentation

- [External Audit Report (2026-02-11)](external-security-audit-report-2026-02-11.md)
- [Penetration Testing Procedures](penetration-testing-procedures.md)
- [Vault Security Review](vault-security-review-checklist.md)
- [Authentication Guide](authentication-guide.md)
- [DR Testing Log](../operations/dr-testing-log.md)
