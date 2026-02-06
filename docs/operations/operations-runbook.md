# Operations Runbook

## Document Information

- **Document Version:** 1.0.0
- **Last Updated:** 2026-01-28
- **Owner:** Operations Team
- **Review Cycle:** Quarterly
- **On-Call Contact:** ops-oncall@example.com

---

## Executive Summary

This runbook provides comprehensive operational procedures for the HCD JanusGraph system, including day-to-day operations, troubleshooting, maintenance, and escalation procedures.

### Quick Reference

| Emergency | Contact | Response Time |
|-----------|---------|---------------|
| P0 - System Down | ops-oncall@example.com | 15 minutes |
| P1 - Critical Issue | ops-team@example.com | 1 hour |
| P2 - Major Issue | ops-team@example.com | 4 hours |
| P3 - Minor Issue | ops-team@example.com | 1 business day |

---

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Health Checks](#health-checks)
3. [Monitoring and Alerting](#monitoring-and-alerting)
4. [Troubleshooting Playbooks](#troubleshooting-playbooks)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Backup and Recovery](#backup-and-recovery)
7. [Scaling Operations](#scaling-operations)
8. [Security Operations](#security-operations)
9. [Incident Response](#incident-response)
10. [Escalation Procedures](#escalation-procedures)

---

## 1. Daily Operations

### 1.1 Morning Checklist

**Time:** 9:00 AM daily

```bash
#!/bin/bash
# scripts/operations/morning_checklist.sh

echo "=== Morning Health Check ==="
echo "Date: $(date)"

# 1. Check system status
echo "\n1. System Status:"
docker-compose ps

# 2. Check disk space
echo "\n2. Disk Space:"
df -h | grep -E '(Filesystem|janusgraph|cassandra)'

# 3. Check memory usage
echo "\n3. Memory Usage:"
free -h

# 4. Check recent errors
echo "\n4. Recent Errors (last hour):"
docker-compose logs --since 1h | grep -i error | tail -20

# 5. Check backup status
echo "\n5. Last Backup:"
ls -lh /backups/ | tail -5

# 6. Check certificate expiry
echo "\n6. Certificate Status:"
openssl x509 -in /etc/ssl/certs/janusgraph.crt -noout -enddate

# 7. Query performance
echo "\n7. Query Performance:"
curl -s http://localhost:8182/health | jq '.metrics.avg_query_time_ms'

echo "\n=== Health Check Complete ==="
```

### 1.2 Log Review

**Daily log review procedure:**

```bash
# Check for errors in last 24 hours
docker-compose logs --since 24h janusgraph | grep -i "error\|exception\|fatal"

# Check slow queries
docker-compose logs --since 24h janusgraph | grep "slow query" | wc -l

# Check authentication failures
docker-compose logs --since 24h janusgraph | grep "auth.*fail" | wc -l

# Generate daily report
python scripts/operations/generate_daily_report.py
```

### 1.3 Metrics Review

**Key metrics to review daily:**

```promql
# Query latency P95
histogram_quantile(0.95, rate(query_duration_seconds_bucket[24h]))

# Error rate
rate(query_errors_total[24h]) / rate(query_total[24h]) * 100

# Throughput
rate(query_total[24h])

# Resource utilization
avg_over_time(cpu_usage_percent[24h])
avg_over_time(memory_usage_percent[24h])
```

---

## 2. Health Checks

### 2.1 System Health Check

**Automated health check script:**

```python
#!/usr/bin/env python3
# scripts/operations/health_check.py

import requests
import sys
from datetime import datetime

def check_health():
    """Comprehensive health check."""
    checks = {
        'janusgraph': check_janusgraph(),
        'cassandra': check_cassandra(),
        'prometheus': check_prometheus(),
        'grafana': check_grafana()
    }
    
    all_healthy = all(checks.values())
    
    print(f"Health Check Report - {datetime.now()}")
    print("=" * 50)
    for service, healthy in checks.items():
        status = "✓ HEALTHY" if healthy else "✗ UNHEALTHY"
        print(f"{service:20s}: {status}")
    print("=" * 50)
    
    return 0 if all_healthy else 1

def check_janusgraph():
    """Check JanusGraph health."""
    try:
        response = requests.get('http://localhost:8182/health', timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"JanusGraph check failed: {e}")
        return False

def check_cassandra():
    """Check Cassandra health."""
    import subprocess
    try:
        result = subprocess.run(
            ['docker-compose', 'exec', '-T', 'hcd', 'nodetool', 'status'],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Cassandra check failed: {e}")
        return False

def check_prometheus():
    """Check Prometheus health."""
    try:
        response = requests.get('http://localhost:9090/-/healthy', timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Prometheus check failed: {e}")
        return False

def check_grafana():
    """Check Grafana health."""
    try:
        response = requests.get('http://localhost:3000/api/health', timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Grafana check failed: {e}")
        return False

if __name__ == '__main__':
    sys.exit(check_health())
```

### 2.2 Component Health Checks

**JanusGraph:**
```bash
# Check if JanusGraph is responding
curl -f http://localhost:8182/health || echo "JanusGraph unhealthy"

# Check Gremlin server
curl -X POST http://localhost:8182 \
  -H "Content-Type: application/json" \
  -d '{"gremlin":"g.V().count()"}' || echo "Gremlin server unhealthy"
```

**Cassandra/HCD:**
```bash
# Check node status
docker-compose exec hcd nodetool status

# Check if accepting connections
docker-compose exec hcd cqlsh -e "SELECT now() FROM system.local;"
```

**Monitoring Stack:**
```bash
# Prometheus
curl -f http://localhost:9090/-/healthy

# Grafana
curl -f http://localhost:3000/api/health

# Loki
curl -f http://localhost:3100/ready
```

---

## 3. Monitoring and Alerting

### 3.1 Alert Response Procedures

**Critical Alerts (P0):**

1. **System Down**
   - Acknowledge alert immediately
   - Check system status: `docker-compose ps`
   - Review recent logs: `docker-compose logs --tail=100`
   - Attempt restart if safe
   - Escalate if not resolved in 15 minutes

2. **Data Loss Risk**
   - Stop all writes immediately
   - Assess backup status
   - Contact database team
   - Do not attempt recovery without approval

3. **Security Breach**
   - Isolate affected systems
   - Preserve evidence
   - Contact security team immediately
   - Follow incident response plan

**High Priority Alerts (P1):**

1. **High Error Rate**
   - Check error logs
   - Identify error patterns
   - Review recent deployments
   - Rollback if necessary

2. **Performance Degradation**
   - Check resource utilization
   - Review slow query log
   - Check for long-running queries
   - Consider scaling if needed

### 3.2 Alert Acknowledgment

```bash
# Acknowledge alert in Prometheus Alertmanager
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "labels": {"alertname": "HighQueryLatency"},
    "annotations": {"summary": "Acknowledged by ops team"}
  }'
```

---

## 4. Troubleshooting Playbooks

### 4.1 High CPU Usage

**Symptoms:**
- CPU utilization > 80%
- Slow query response times
- System unresponsive

**Diagnosis:**
```bash
# Check CPU usage by container
docker stats --no-stream

# Check Java threads
docker-compose exec janusgraph jstack 1 | grep -A 5 "runnable"

# Check for CPU-intensive queries
docker-compose logs janusgraph | grep "execution time" | sort -k5 -n | tail -20
```

**Resolution:**
1. Identify CPU-intensive queries
2. Kill long-running queries if necessary
3. Optimize or cache problematic queries
4. Scale horizontally if sustained high load
5. Review and optimize indexes

### 4.2 High Memory Usage

**Symptoms:**
- Memory utilization > 90%
- OutOfMemoryError in logs
- Frequent GC pauses

**Diagnosis:**
```bash
# Check memory usage
docker stats --no-stream

# Check JVM heap usage
docker-compose exec janusgraph jstat -gc 1 1000 5

# Generate heap dump
docker-compose exec janusgraph jmap -dump:live,format=b,file=/tmp/heap.hprof 1
```

**Resolution:**
1. Review heap dump for memory leaks
2. Check for large transactions
3. Review cache sizes
4. Increase heap size if appropriate
5. Restart service if memory leak confirmed

### 4.3 Slow Queries

**Symptoms:**
- Query latency P95 > 1000ms
- Timeout errors
- User complaints

**Diagnosis:**
```bash
# Enable query profiling
docker-compose exec janusgraph \
  gremlin-console.sh -e "g.V().profile()"

# Check slow query log
docker-compose logs janusgraph | grep "slow query"

# Check for missing indexes
docker-compose exec janusgraph \
  cqlsh -e "SELECT * FROM system_schema.indexes;"
```

**Resolution:**
1. Identify slow query patterns
2. Add appropriate indexes
3. Optimize query structure
4. Implement caching
5. Consider query result pagination

### 4.4 Connection Pool Exhaustion

**Symptoms:**
- "No available connections" errors
- Connection timeout errors
- Increasing connection wait times

**Diagnosis:**
```bash
# Check active connections
docker-compose exec janusgraph netstat -an | grep :8182 | wc -l

# Check connection pool metrics
curl http://localhost:8182/metrics | grep connection_pool
```

**Resolution:**
1. Increase connection pool size
2. Check for connection leaks
3. Implement connection timeout
4. Review application connection handling
5. Scale if sustained high connection count

### 4.5 Disk Space Issues

**Symptoms:**
- Disk usage > 85%
- Write failures
- "No space left on device" errors

**Diagnosis:**
```bash
# Check disk usage
df -h

# Find large files
du -sh /var/lib/docker/volumes/* | sort -h | tail -20

# Check log sizes
du -sh /var/log/* | sort -h | tail -10
```

**Resolution:**
1. Clean up old logs: `find /var/log -name "*.log" -mtime +30 -delete`
2. Remove old backups: `find /backups -mtime +90 -delete`
3. Compact Cassandra: `nodetool compact`
4. Increase disk space if needed
5. Implement log rotation

---

## 5. Maintenance Procedures

### 5.1 Routine Maintenance Schedule

| Task | Frequency | Day/Time | Duration |
|------|-----------|----------|----------|
| Log rotation | Daily | 2:00 AM | 10 min |
| Backup verification | Daily | 3:00 AM | 30 min |
| Security updates | Weekly | Sunday 2:00 AM | 2 hours |
| Performance review | Weekly | Monday 10:00 AM | 1 hour |
| Capacity planning | Monthly | 1st Monday | 2 hours |
| DR test | Quarterly | TBD | 4 hours |

### 5.2 Planned Maintenance Procedure

**Pre-Maintenance:**
1. Schedule maintenance window (off-peak hours)
2. Notify stakeholders 48 hours in advance
3. Create backup before maintenance
4. Prepare rollback plan
5. Review maintenance steps

**During Maintenance:**
```bash
# 1. Enable maintenance mode
curl -X POST http://localhost:8182/admin/maintenance/enable

# 2. Drain connections
docker-compose exec janusgraph nodetool drain

# 3. Perform maintenance tasks
# (updates, configuration changes, etc.)

# 4. Restart services
docker-compose restart

# 5. Verify health
./scripts/operations/health_check.py

# 6. Disable maintenance mode
curl -X POST http://localhost:8182/admin/maintenance/disable
```

**Post-Maintenance:**
1. Verify all services healthy
2. Run smoke tests
3. Monitor for issues (1 hour)
4. Update maintenance log
5. Notify stakeholders of completion

### 5.3 Certificate Renewal

**Procedure:**
```bash
# Check certificate expiry
openssl x509 -in /etc/ssl/certs/janusgraph.crt -noout -enddate

# Renew certificate (Let's Encrypt example)
certbot renew --dry-run
certbot renew

# Update certificate in containers
docker-compose restart nginx janusgraph

# Verify new certificate
openssl s_client -connect localhost:8182 -showcerts
```

---

## 6. Backup and Recovery

### 6.1 Backup Procedures

**Daily Backup:**
```bash
#!/bin/bash
# scripts/backup/daily_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/daily"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup JanusGraph data
docker-compose exec janusgraph nodetool snapshot

# Backup Cassandra
docker-compose exec hcd nodetool snapshot

# Copy snapshots
docker cp janusgraph:/var/lib/janusgraph/snapshots $BACKUP_DIR/janusgraph_$DATE
docker cp hcd:/var/lib/cassandra/snapshots $BACKUP_DIR/cassandra_$DATE

# Compress backups
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/*_$DATE

# Encrypt backup
gpg --encrypt --recipient ops@example.com $BACKUP_DIR/backup_$DATE.tar.gz

# Upload to cloud storage
aws s3 cp $BACKUP_DIR/backup_$DATE.tar.gz.gpg s3://backups/janusgraph/

# Clean up local files older than 7 days
find $BACKUP_DIR -name "*.tar.gz*" -mtime +7 -delete

echo "Backup completed: backup_$DATE.tar.gz.gpg"
```

### 6.2 Recovery Procedures

**Full System Recovery:**
```bash
#!/bin/bash
# scripts/backup/restore.sh

BACKUP_FILE=$1

# Stop services
docker-compose down

# Restore from backup
gpg --decrypt $BACKUP_FILE | tar -xzf - -C /

# Start services
docker-compose up -d

# Verify recovery
./scripts/operations/health_check.py
```

**Point-in-Time Recovery:**
See [Disaster Recovery](disaster-recovery-plan.md) for detailed procedures.

---

## 7. Scaling Operations

### 7.1 Horizontal Scaling

**Add JanusGraph Node:**
```bash
# Update docker-compose.yml
docker-compose up -d --scale janusgraph=3

# Verify new nodes
docker-compose ps janusgraph
```

**Add Cassandra Node:**
```bash
# Add node to cluster
docker-compose up -d --scale hcd=3

# Check cluster status
docker-compose exec hcd nodetool status
```

### 7.2 Vertical Scaling

**Increase Resources:**
```yaml
# docker-compose.yml
services:
  janusgraph:
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
```

```bash
# Apply changes
docker-compose up -d
```

---

## 8. Security Operations

### 8.1 Security Monitoring

**Daily Security Checks:**
```bash
# Check for failed authentication attempts
docker-compose logs | grep "authentication failed" | wc -l

# Check for suspicious activity
docker-compose logs | grep -E "DROP|DELETE|TRUNCATE" | tail -20

# Review access logs
tail -100 /var/log/janusgraph/access.log
```

### 8.2 Security Incident Response

See [Incident Response](../operations/disaster-recovery-plan.md) for detailed procedures.

---

## 9. Incident Response

### 9.1 Incident Classification

| Priority | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| P0 | System down, data loss | 15 minutes | Complete outage, data corruption |
| P1 | Critical functionality impaired | 1 hour | High error rate, security breach |
| P2 | Major functionality degraded | 4 hours | Performance issues, partial outage |
| P3 | Minor issues | 1 business day | UI bugs, minor errors |

### 9.2 Incident Response Steps

1. **Detect and Alert**
   - Automated monitoring alerts
   - User reports
   - Health check failures

2. **Assess and Classify**
   - Determine severity
   - Identify affected systems
   - Estimate impact

3. **Respond and Mitigate**
   - Follow appropriate playbook
   - Implement workarounds
   - Communicate status

4. **Resolve and Recover**
   - Fix root cause
   - Verify resolution
   - Monitor for recurrence

5. **Document and Learn**
   - Write incident report
   - Conduct post-mortem
   - Update runbooks

---

## 10. Escalation Procedures

### 10.1 Escalation Matrix

| Level | Role | Contact | When to Escalate |
|-------|------|---------|------------------|
| L1 | On-Call Engineer | ops-oncall@example.com | Initial response |
| L2 | Senior Engineer | ops-senior@example.com | Not resolved in 30 min |
| L3 | Team Lead | ops-lead@example.com | Not resolved in 2 hours |
| L4 | Engineering Manager | eng-manager@example.com | Critical impact > 4 hours |
| L5 | CTO | cto@example.com | Business-critical outage |

### 10.2 Escalation Procedure

```bash
# Send escalation notification
./scripts/operations/escalate.sh \
  --level L2 \
  --incident INC-12345 \
  --summary "High CPU usage not resolved"
```

---

## Appendices

### Appendix A: Command Reference

**Quick Commands:**
```bash
# Restart all services
docker-compose restart

# View logs
docker-compose logs -f janusgraph

# Check status
docker-compose ps

# Execute command in container
docker-compose exec janusgraph bash

# Scale service
docker-compose up -d --scale janusgraph=3
```

### Appendix B: Contact Information

- **Operations Team:** ops-team@example.com
- **On-Call:** ops-oncall@example.com (24/7)
- **Security Team:** security@example.com
- **Database Team:** dba@example.com

### Appendix C: Related Documentation

- [Architecture Documentation](../architecture/README.md)
- [Disaster Recovery Plan](disaster-recovery-plan.md)
- Incident Response (see Disaster Recovery Plan)
- Monitoring Guide (see this runbook)
- `SECURITY.md` (root) - Security guidelines

---

**Document Classification:** Internal - Operational  
**Next Review Date:** 2026-04-28  
**Document Owner:** Operations Team
