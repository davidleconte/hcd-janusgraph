# Incident Response Runbook

**Date:** 2026-02-11  
**Version:** 1.0  
**Status:** Active  
**Review Cycle:** Quarterly

---

## Quick Reference

### Emergency Contacts

| Role | Contact | Phone | Email |
|------|---------|-------|-------|
| **On-Call Engineer** | Primary | +1-XXX-XXX-XXXX | oncall@example.com |
| **Backup On-Call** | Secondary | +1-XXX-XXX-XXXX | backup-oncall@example.com |
| **Incident Commander** | Manager | +1-XXX-XXX-XXXX | incident@example.com |
| **Security Team** | Lead | +1-XXX-XXX-XXXX | security@example.com |
| **Executive Escalation** | CTO | +1-XXX-XXX-XXXX | escalation@example.com |

### Severity Levels

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| **SEV-1** | Critical - Complete outage | 15 minutes | All services down |
| **SEV-2** | High - Major degradation | 30 minutes | JanusGraph unavailable |
| **SEV-3** | Medium - Partial impact | 2 hours | Single service degraded |
| **SEV-4** | Low - Minor issue | 24 hours | Monitoring alert |

### Common Commands

```bash
# Check service status
PODMAN_CONNECTION=podman-wxd podman --remote ps --filter "label=project=janusgraph-demo"

# View logs
PODMAN_CONNECTION=podman-wxd podman --remote logs janusgraph-server-demo_janusgraph-server_1 --tail 100

# Restart service
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo restart janusgraph-server

# Full stack restart
cd config/compose && bash ../../scripts/deployment/stop_full_stack.sh
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh

# Check metrics
curl http://localhost:9090/api/v1/query?query=up

# Backup now
./scripts/backup/backup_janusgraph.sh
```

---

## Incident Response Process

### Phase 1: Detection & Triage (0-15 minutes)

#### 1.1 Incident Detection

**Automated Detection:**
- Prometheus alerts → PagerDuty → On-call engineer
- Health check failures → Monitoring dashboard
- Error rate spikes → AlertManager
- Customer reports → Support ticket system

**Manual Detection:**
- User reports
- Monitoring dashboard review
- Log analysis
- Performance degradation

#### 1.2 Initial Assessment

**Questions to Answer:**
1. What is the impact? (users affected, services down)
2. What is the severity? (SEV-1 to SEV-4)
3. Is this a known issue? (check runbook, past incidents)
4. What changed recently? (deployments, config changes)

**Triage Checklist:**
```markdown
- [ ] Incident detected and logged
- [ ] Severity assigned
- [ ] On-call engineer notified
- [ ] Initial impact assessment complete
- [ ] Incident channel created (#incident-YYYY-MM-DD-NNN)
```

#### 1.3 Severity Assignment

**SEV-1: Critical (Page immediately)**
- All services unavailable
- Data loss occurring
- Security breach detected
- Compliance violation in progress

**SEV-2: High (Page within 30 min)**
- Core service unavailable (JanusGraph, HCD, OpenSearch)
- Significant performance degradation (>50% slower)
- Partial data loss
- Security vulnerability discovered

**SEV-3: Medium (Notify within 2h)**
- Non-critical service unavailable
- Minor performance degradation (<50% slower)
- Monitoring gaps
- Configuration issues

**SEV-4: Low (Handle during business hours)**
- Cosmetic issues
- Documentation errors
- Minor alerts
- Enhancement requests

### Phase 2: Response & Mitigation (15-60 minutes)

#### 2.1 Incident Commander Assignment

**SEV-1/SEV-2:** Incident Commander required
**SEV-3/SEV-4:** On-call engineer handles

**Incident Commander Responsibilities:**
- Coordinate response team
- Make decisions
- Communicate with stakeholders
- Declare incident resolved

#### 2.2 Communication

**Internal Communication:**
```markdown
# Incident Slack Channel Template
**Incident:** #incident-2026-02-11-001
**Severity:** SEV-2
**Status:** Investigating
**Impact:** JanusGraph unavailable, ~100 users affected
**Started:** 2026-02-11 14:30 UTC
**IC:** @john.doe
**Team:** @jane.smith @bob.jones

**Timeline:**
14:30 - Incident detected (Prometheus alert)
14:32 - On-call paged
14:35 - Investigation started
14:40 - Root cause identified (OOM)
14:45 - Mitigation in progress (restart + memory increase)
```

**External Communication (if needed):**
```markdown
# Status Page Update Template
**Title:** Service Degradation - Graph Database
**Status:** Investigating
**Impact:** Some users may experience delays in fraud detection queries
**Started:** 2026-02-11 14:30 UTC
**Updates:** We are investigating an issue with our graph database service.
```

#### 2.3 Investigation

**Standard Investigation Steps:**

1. **Check Service Status**
```bash
# All services
PODMAN_CONNECTION=podman-wxd podman --remote ps --filter "label=project=janusgraph-demo"

# Specific service
PODMAN_CONNECTION=podman-wxd podman --remote inspect janusgraph-demo_janusgraph-server_1
```

2. **Review Logs**
```bash
# Recent logs
PODMAN_CONNECTION=podman-wxd podman --remote logs janusgraph-server-demo_janusgraph-server_1 --tail 500

# Follow logs
PODMAN_CONNECTION=podman-wxd podman --remote logs janusgraph-server-demo_janusgraph-server_1 --follow

# Search for errors
PODMAN_CONNECTION=podman-wxd podman --remote logs janusgraph-server-demo_janusgraph-server_1 | grep -i error
```

3. **Check Metrics**
```bash
# Prometheus queries
curl 'http://localhost:9090/api/v1/query?query=up'
curl 'http://localhost:9090/api/v1/query?query=janusgraph_query_duration_seconds'
curl 'http://localhost:9090/api/v1/query?query=container_memory_usage_bytes'
```

4. **Check Recent Changes**
```bash
# Git history
git log --since="2 hours ago" --oneline

# Deployment history
PODMAN_CONNECTION=podman-wxd podman --remote ps --format "{{.CreatedAt}}\t{{.Names}}\t{{.Status}}"
```

5. **Check Resource Usage**
```bash
# Container resources
PODMAN_CONNECTION=podman-wxd podman --remote stats --no-stream

# Host resources
top
df -h
free -h
```

#### 2.4 Mitigation Strategies

**Quick Fixes (Try First):**

1. **Service Restart**
```bash
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo restart <service-name>
```

2. **Clear Cache**
```bash
# JanusGraph cache
PODMAN_CONNECTION=podman-wxd podman --remote exec janusgraph-server-demo_janusgraph-server_1 \
  bin/gremlin.sh -e "graph.tx().rollback(); graph.close()"
```

3. **Scale Resources**
```bash
# Increase memory limit
PODMAN_CONNECTION=podman-wxd podman --remote update --memory 8G janusgraph-demo_janusgraph-server_1
```

4. **Rollback Deployment**
```bash
git revert HEAD
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
```

**Advanced Fixes:**

1. **Restore from Backup**
```bash
./scripts/restore/restore_janusgraph.sh --backup-id latest
```

2. **Failover to DR Site**
```bash
./scripts/dr/failover_to_dr.sh
```

3. **Data Repair**
```bash
# HCD repair
PODMAN_CONNECTION=podman-wxd podman --remote exec janusgraph-server-demo_hcd-server_1 nodetool repair janusgraph
```

### Phase 3: Recovery & Validation (60-120 minutes)

#### 3.1 Service Recovery

**Recovery Checklist:**
```markdown
- [ ] Service restarted/restored
- [ ] Health checks passing
- [ ] Metrics returning to normal
- [ ] No error logs
- [ ] Functionality validated
```

**Validation Commands:**
```bash
# Health checks
curl http://localhost:18182/healthz
curl http://localhost:9200/_cluster/health
curl http://localhost:8001/health

# Functional tests
./scripts/validation/test_janusgraph_queries.sh
./scripts/validation/test_opensearch_queries.sh
./scripts/validation/preflight_check.sh
```

#### 3.2 Impact Assessment

**Questions to Answer:**
1. How many users were affected?
2. How long was the outage?
3. Was any data lost?
4. Were SLAs breached?
5. What was the business impact?

**Metrics to Collect:**
- Downtime duration
- Users affected
- Transactions lost
- Revenue impact
- SLA compliance

#### 3.3 Communication Updates

**Resolution Announcement:**
```markdown
# Slack Update
**Incident:** #incident-2026-02-11-001
**Status:** RESOLVED ✅
**Duration:** 45 minutes
**Root Cause:** JanusGraph OOM due to large query
**Resolution:** Service restarted with increased memory
**Impact:** ~100 users experienced delays
**Follow-up:** Post-mortem scheduled for 2026-02-12 10:00 UTC
```

**Status Page Update:**
```markdown
**Title:** Service Degradation - Graph Database [RESOLVED]
**Status:** Resolved
**Resolution:** The issue has been resolved. All services are operating normally.
**Duration:** 45 minutes (14:30 - 15:15 UTC)
**Root Cause:** Memory exhaustion due to large query
```

### Phase 4: Post-Incident Review (24-48 hours)

#### 4.1 Post-Mortem Meeting

**Attendees:**
- Incident Commander
- On-call engineer(s)
- Service owners
- Management (for SEV-1/SEV-2)

**Agenda:**
1. Timeline review
2. Root cause analysis
3. What went well
4. What could be improved
5. Action items

#### 4.2 Post-Mortem Document

**Template:**
```markdown
# Post-Mortem: [Incident Title]

**Date:** 2026-02-11
**Incident ID:** #incident-2026-02-11-001
**Severity:** SEV-2
**Duration:** 45 minutes
**Impact:** ~100 users affected

## Summary
Brief description of what happened.

## Timeline
| Time | Event |
|------|-------|
| 14:30 | Incident detected |
| 14:32 | On-call paged |
| 14:35 | Investigation started |
| 14:40 | Root cause identified |
| 14:45 | Mitigation started |
| 15:15 | Service restored |

## Root Cause
Detailed explanation of what caused the incident.

## Impact
- Users affected: ~100
- Duration: 45 minutes
- Data loss: None
- Revenue impact: $X,XXX

## What Went Well
- Quick detection (2 minutes)
- Clear communication
- Effective mitigation

## What Could Be Improved
- Better query validation
- Proactive memory monitoring
- Faster rollback process

## Action Items
- [ ] Implement query size limits (@engineer, 2026-02-15)
- [ ] Add memory alerts (@engineer, 2026-02-13)
- [ ] Document rollback procedure (@engineer, 2026-02-14)
- [ ] Update runbook (@engineer, 2026-02-12)

## Lessons Learned
Key takeaways for future incidents.
```

---

## Common Incident Scenarios

### Scenario 1: JanusGraph Unavailable

**Symptoms:**
- Prometheus alert: `JanusGraphDown`
- API returns 503 errors
- Gremlin queries timeout

**Investigation:**
```bash
# Check service status
PODMAN_CONNECTION=podman-wxd podman --remote ps | grep janusgraph

# Check logs
PODMAN_CONNECTION=podman-wxd podman --remote logs janusgraph-server-demo_janusgraph-server_1 --tail 100

# Check HCD connectivity
PODMAN_CONNECTION=podman-wxd podman --remote exec janusgraph-server-demo_janusgraph-server_1 \
  cqlsh hcd-server -e "DESCRIBE KEYSPACES"
```

**Common Causes:**
1. HCD unavailable
2. Out of memory
3. Configuration error
4. Network issues

**Resolution:**
```bash
# Quick fix: Restart
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo restart janusgraph-server

# If restart fails: Restore from backup
./scripts/restore/restore_janusgraph.sh --backup-id latest

# Validate
curl http://localhost:18182/healthz
```

### Scenario 2: High Query Latency

**Symptoms:**
- Prometheus alert: `HighQueryLatency`
- Slow API responses
- User complaints

**Investigation:**
```bash
# Check query metrics
curl 'http://localhost:9090/api/v1/query?query=janusgraph_query_duration_seconds'

# Check active queries
PODMAN_CONNECTION=podman-wxd podman --remote exec janusgraph-server-demo_janusgraph-server_1 \
  bin/gremlin.sh -e "graph.tx().getOpenTransactions()"

# Check resource usage
PODMAN_CONNECTION=podman-wxd podman --remote stats janusgraph-demo_janusgraph-server_1
```

**Common Causes:**
1. Large/complex queries
2. Missing indices
3. Resource contention
4. Data growth

**Resolution:**
```bash
# Kill long-running queries
PODMAN_CONNECTION=podman-wxd podman --remote exec janusgraph-server-demo_janusgraph-server_1 \
  bin/gremlin.sh -e "graph.tx().rollback()"

# Add indices if needed
PODMAN_CONNECTION=podman-wxd podman --remote exec janusgraph-server-demo_janusgraph-server_1 \
  bin/gremlin.sh -e "mgmt = graph.openManagement(); ..."

# Scale resources
PODMAN_CONNECTION=podman-wxd podman --remote update --cpus 4 --memory 8G janusgraph-demo_janusgraph-server_1
```

### Scenario 3: Data Corruption

**Symptoms:**
- Data validation alerts
- Inconsistent query results
- Schema errors

**Investigation:**
```bash
# Check data integrity
./scripts/validation/verify_janusgraph_data.sh

# Check HCD consistency
PODMAN_CONNECTION=podman-wxd podman --remote exec janusgraph-server-demo_hcd-server_1 nodetool status

# Check for split-brain
PODMAN_CONNECTION=podman-wxd podman --remote exec janusgraph-server-demo_hcd-server_1 nodetool describecluster
```

**Common Causes:**
1. Failed writes
2. Network partition
3. Concurrent modifications
4. Bug in application code

**Resolution:**
```bash
# Stop writes
# (disable API or set read-only mode)

# Restore from backup
./scripts/restore/restore_janusgraph.sh --backup-id <last-good-backup>

# Replay transactions from Pulsar
./scripts/pulsar/replay_events.sh --from <timestamp>

# Validate
./scripts/validation/verify_janusgraph_data.sh
```

### Scenario 4: Security Breach

**Symptoms:**
- Security alerts
- Unauthorized access logs
- Suspicious queries
- Data exfiltration detected

**Investigation:**
```bash
# Check audit logs
grep "SECURITY" /var/log/audit.log

# Check failed auth attempts
grep "failed_auth" /var/log/janusgraph/audit.log

# Check suspicious queries
grep "SUSPICIOUS" /var/log/janusgraph/query.log

# Check network connections
netstat -an | grep ESTABLISHED
```

**Immediate Actions:**
1. **Isolate affected systems**
```bash
# Block external access
iptables -A INPUT -s 0.0.0.0/0 -j DROP

# Stop affected services
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo stop
```

2. **Preserve evidence**
```bash
# Snapshot logs
tar -czf incident-logs-$(date +%Y%m%d-%H%M%S).tar.gz /var/log/

# Snapshot containers
PODMAN_CONNECTION=podman-wxd podman --remote commit janusgraph-demo_janusgraph-server_1 evidence-janusgraph
```

3. **Notify security team**
```bash
# Send alert
./scripts/security/send_security_alert.sh \
  --severity critical \
  --type breach \
  --description "Unauthorized access detected"
```

4. **Change all credentials**
```bash
# Rotate all passwords
./scripts/security/rotate_all_credentials.sh

# Revoke all tokens
./scripts/security/revoke_all_tokens.sh
```

### Scenario 5: Disk Space Full

**Symptoms:**
- Prometheus alert: `DiskSpaceLow`
- Write failures
- Service crashes

**Investigation:**
```bash
# Check disk usage
df -h

# Find large files
du -sh /* | sort -h

# Check container volumes
PODMAN_CONNECTION=podman-wxd podman --remote volume ls
PODMAN_CONNECTION=podman-wxd podman --remote system df
```

**Resolution:**
```bash
# Clean old logs
find /var/log -name "*.log" -mtime +7 -delete

# Clean old backups
find /backups -name "*.tar.gz" -mtime +30 -delete

# Prune unused containers/images
PODMAN_CONNECTION=podman-wxd podman --remote system prune -a --volumes

# Expand disk if needed
# (cloud provider specific)
```

---

## Escalation Procedures

### When to Escalate

**Escalate to Incident Commander:**
- SEV-1 or SEV-2 incident
- Incident duration > 1 hour
- Multiple services affected
- Unclear root cause

**Escalate to Security Team:**
- Security breach suspected
- Unauthorized access detected
- Data exfiltration suspected
- Compliance violation

**Escalate to Executive:**
- SEV-1 incident > 2 hours
- Major data loss
- Regulatory reporting required
- Media attention

### Escalation Contacts

```markdown
Level 1: On-Call Engineer
  ↓ (if unresolved in 30 min)
Level 2: Incident Commander
  ↓ (if SEV-1 or >1 hour)
Level 3: Engineering Manager
  ↓ (if >2 hours or major impact)
Level 4: CTO/Executive Team
```

---

## Tools & Resources

### Monitoring Dashboards

- **Grafana:** http://localhost:3001
- **Prometheus:** http://localhost:9090
- **AlertManager:** http://localhost:9093
- **OpenSearch Dashboards:** http://localhost:5601

### Log Locations

- **JanusGraph:** `PODMAN_CONNECTION=podman-wxd podman --remote logs janusgraph-server-demo_janusgraph-server_1`
- **HCD:** `PODMAN_CONNECTION=podman-wxd podman --remote logs janusgraph-server-demo_hcd-server_1`
- **OpenSearch:** `PODMAN_CONNECTION=podman-wxd podman --remote logs janusgraph-server-demo_opensearch_1`
- **API:** `PODMAN_CONNECTION=podman-wxd podman --remote logs janusgraph-server-demo_analytics-api_1`
- **Audit:** `/var/log/janusgraph/audit.log`

### Documentation

- **Runbooks:** `docs/operations/`
- **Architecture:** `docs/architecture/`
- **API Docs:** `docs/api/`
- **RTO/RPO:** `docs/operations/rto-rpo-targets.md`

### Scripts

- **Backup:** `scripts/backup/`
- **Restore:** `scripts/restore/`
- **Validation:** `scripts/validation/`
- **Deployment:** `scripts/deployment/`

---

## Training & Drills

### Monthly Incident Response Drill

**Objectives:**
- Practice incident response procedures
- Test communication channels
- Validate runbook accuracy
- Train new team members

**Scenarios:**
1. Service outage simulation
2. Data corruption scenario
3. Security breach drill
4. DR failover test

**Success Criteria:**
- Incident detected within 5 minutes
- Response initiated within 15 minutes
- Communication clear and timely
- Resolution within RTO targets

### Quarterly Runbook Review

**Review Items:**
- Update contact information
- Validate procedures
- Add new scenarios
- Remove outdated information
- Incorporate lessons learned

---

## Appendix

### A. Incident Severity Matrix

| Impact | Urgency | Severity |
|--------|---------|----------|
| Critical | High | SEV-1 |
| High | High | SEV-2 |
| Medium | High | SEV-2 |
| Critical | Medium | SEV-2 |
| High | Medium | SEV-3 |
| Medium | Medium | SEV-3 |
| Low | Any | SEV-4 |

### B. Communication Templates

**Initial Notification:**
```
INCIDENT ALERT - SEV-[X]
Service: [Service Name]
Impact: [Brief description]
Started: [Timestamp]
Status: Investigating
IC: [Name]
Channel: #incident-[ID]
```

**Status Update:**
```
INCIDENT UPDATE - #incident-[ID]
Status: [Investigating/Mitigating/Resolved]
Progress: [What's been done]
Next Steps: [What's next]
ETA: [Estimated resolution time]
```

**Resolution:**
```
INCIDENT RESOLVED - #incident-[ID]
Duration: [X minutes/hours]
Root Cause: [Brief explanation]
Impact: [Users/services affected]
Follow-up: [Post-mortem scheduled]
```

### C. Useful Commands Cheat Sheet

```bash
# Service Management
PODMAN_CONNECTION=podman-wxd podman --remote ps                                    # List running containers
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo restart   # Restart all services
PODMAN_CONNECTION=podman-wxd podman --remote logs <container> --tail 100          # View recent logs
PODMAN_CONNECTION=podman-wxd podman --remote stats                                # Resource usage

# Health Checks
curl http://localhost:18182/healthz          # JanusGraph health
curl http://localhost:9200/_cluster/health  # OpenSearch health
curl http://localhost:8001/health           # API health

# Metrics
curl http://localhost:9090/api/v1/query?query=up  # Service status
curl http://localhost:8000/metrics                # JanusGraph metrics

# Backup/Restore
./scripts/backup/backup_janusgraph.sh             # Backup now
./scripts/restore/restore_janusgraph.sh --backup-id latest  # Restore

# Validation
./scripts/validation/preflight_check.sh           # Full validation
./scripts/validation/verify_janusgraph_data.sh    # Data integrity
```

---

**Document Owner:** Operations Team  
**Last Updated:** 2026-02-11  
**Next Review:** 2026-05-11 (Quarterly)  
**Version:** 1.0