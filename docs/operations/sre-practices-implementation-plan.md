# SRE Practices Implementation Plan
# Priority Action 2: +0.2 Points to Excellence Score

**Date:** 2026-04-09  
**Target:** Operations Excellence 9.6 → 9.8  
**Effort:** 2-3 weeks  
**Status:** Pending

---

## Executive Summary

Implement Site Reliability Engineering (SRE) practices including Service Level Objectives (SLOs), Service Level Indicators (SLIs), error budgets, and automated runbook execution. This will improve operational maturity and reliability.

---

## Objectives

1. **Define SLOs/SLIs with error budgets** (+0.15)
   - Availability, latency, throughput SLOs
   - Error budget policy
   - Automated SLO monitoring

2. **Implement automated runbook execution** (+0.05)
   - Ansible playbooks for common operations
   - Self-healing capabilities
   - Incident response automation

---

## Phase 1: SLO/SLI Definition (Week 1)

### 1.1 Service Level Indicators (SLIs)

**Core SLIs to Track:**

```yaml
# config/sre/slis.yaml

slis:
  # Availability SLIs
  - name: api_availability
    description: "Percentage of successful API requests"
    metric: "sum(rate(http_requests_total{status!~'5..'}[5m])) / sum(rate(http_requests_total[5m]))"
    unit: "percentage"
    
  - name: janusgraph_availability
    description: "JanusGraph service uptime"
    metric: "up{job='janusgraph'}"
    unit: "boolean"
    
  - name: hcd_availability
    description: "HCD/Cassandra service uptime"
    metric: "up{job='hcd'}"
    unit: "boolean"
  
  # Latency SLIs
  - name: api_latency_p95
    description: "95th percentile API response time"
    metric: "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
    unit: "seconds"
    
  - name: query_latency_p99
    description: "99th percentile graph query latency"
    metric: "histogram_quantile(0.99, rate(janusgraph_query_duration_seconds_bucket[5m]))"
    unit: "seconds"
  
  # Throughput SLIs
  - name: api_throughput
    description: "API requests per second"
    metric: "sum(rate(http_requests_total[5m]))"
    unit: "requests/sec"
    
  - name: transaction_throughput
    description: "Transactions processed per second"
    metric: "sum(rate(transactions_processed_total[5m]))"
    unit: "transactions/sec"
  
  # Error Rate SLIs
  - name: api_error_rate
    description: "Percentage of failed API requests"
    metric: "sum(rate(http_requests_total{status=~'5..'}[5m])) / sum(rate(http_requests_total[5m]))"
    unit: "percentage"
    
  - name: query_error_rate
    description: "Percentage of failed graph queries"
    metric: "sum(rate(janusgraph_errors_total[5m])) / sum(rate(janusgraph_queries_total[5m]))"
    unit: "percentage"
```

### 1.2 Service Level Objectives (SLOs)

**SLO Definitions:**

```yaml
# config/sre/slos.yaml

slos:
  # Availability SLOs
  - name: api_availability_slo
    description: "API should be available 99.9% of the time"
    sli: api_availability
    target: 0.999
    window: 30d
    error_budget: 0.001  # 43.2 minutes/month
    
  - name: janusgraph_availability_slo
    description: "JanusGraph should be available 99.5% of the time"
    sli: janusgraph_availability
    target: 0.995
    window: 30d
    error_budget: 0.005  # 3.6 hours/month
  
  # Latency SLOs
  - name: api_latency_slo
    description: "95% of API requests should complete within 200ms"
    sli: api_latency_p95
    target: 0.200
    window: 7d
    error_budget: 0.05  # 5% can exceed 200ms
    
  - name: query_latency_slo
    description: "99% of queries should complete within 1 second"
    sli: query_latency_p99
    target: 1.0
    window: 7d
    error_budget: 0.01  # 1% can exceed 1s
  
  # Error Rate SLOs
  - name: api_error_rate_slo
    description: "API error rate should be below 0.1%"
    sli: api_error_rate
    target: 0.001
    window: 7d
    error_budget: 0.001
    
  - name: query_error_rate_slo
    description: "Query error rate should be below 0.5%"
    sli: query_error_rate
    target: 0.005
    window: 7d
    error_budget: 0.005
```

### 1.3 Error Budget Policy

**Error Budget Policy Document:**

```markdown
# Error Budget Policy

## Overview

Error budgets define how much unreliability is acceptable for each service. When error budget is exhausted, feature development stops and focus shifts to reliability.

## Error Budget Calculation

```
Error Budget = (1 - SLO) × Time Window
```

Example: 99.9% availability SLO over 30 days
- Error Budget = (1 - 0.999) × 30 days = 0.001 × 30 days = 43.2 minutes/month

## Policy Rules

### Green Zone (>50% error budget remaining)
- ✅ Normal feature development
- ✅ Scheduled maintenance allowed
- ✅ Experimental features permitted

### Yellow Zone (25-50% error budget remaining)
- ⚠️ Increased monitoring
- ⚠️ Defer non-critical changes
- ⚠️ Review recent changes for reliability impact

### Red Zone (<25% error budget remaining)
- 🚨 **STOP** all feature development
- 🚨 Focus on reliability improvements
- 🚨 Root cause analysis required
- 🚨 No scheduled maintenance
- 🚨 Incident response only

### Exhausted (0% error budget)
- 🔴 **FREEZE** all changes except critical fixes
- 🔴 Executive escalation
- 🔴 Post-mortem required
- 🔴 Reliability improvement plan mandatory

## Responsibilities

| Role | Responsibility |
|------|----------------|
| SRE Team | Monitor error budgets, enforce policy |
| Development Team | Respect error budget constraints |
| Product Team | Prioritize reliability when budget low |
| Management | Support policy enforcement |

## Exceptions

Exceptions require VP Engineering approval and must include:
- Business justification
- Risk assessment
- Rollback plan
- Monitoring plan
```

**Estimated Effort:** 3-4 days

---

## Phase 2: SLO Monitoring & Alerting (Week 1-2)

### 2.1 Prometheus Recording Rules

**Create recording rules for SLIs:**

```yaml
# config/prometheus/slo_rules.yaml

groups:
  - name: sli_recording_rules
    interval: 30s
    rules:
      # API Availability
      - record: sli:api_availability:ratio_rate5m
        expr: |
          sum(rate(http_requests_total{status!~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m]))
      
      # API Latency P95
      - record: sli:api_latency:p95
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket[5m])
          )
      
      # Query Error Rate
      - record: sli:query_error_rate:ratio_rate5m
        expr: |
          sum(rate(janusgraph_errors_total[5m]))
          /
          sum(rate(janusgraph_queries_total[5m]))
```

### 2.2 SLO Alerting Rules

**Create alerts for SLO violations:**

```yaml
# config/prometheus/slo_alerts.yaml

groups:
  - name: slo_alerts
    rules:
      # API Availability SLO
      - alert: APIAvailabilitySLOViolation
        expr: |
          (
            1 - sli:api_availability:ratio_rate5m
          ) > 0.001
        for: 5m
        labels:
          severity: critical
          slo: api_availability
        annotations:
          summary: "API availability SLO violated"
          description: "API availability is {{ $value | humanizePercentage }}, below 99.9% SLO"
      
      # API Latency SLO
      - alert: APILatencySLOViolation
        expr: sli:api_latency:p95 > 0.200
        for: 5m
        labels:
          severity: warning
          slo: api_latency
        annotations:
          summary: "API latency SLO violated"
          description: "API P95 latency is {{ $value }}s, above 200ms SLO"
      
      # Error Budget Exhaustion
      - alert: ErrorBudgetExhausted
        expr: |
          (
            1 - (
              sum(rate(http_requests_total{status!~"5.."}[30d]))
              /
              sum(rate(http_requests_total[30d]))
            )
          ) > 0.001
        for: 1h
        labels:
          severity: critical
          slo: error_budget
        annotations:
          summary: "Error budget exhausted"
          description: "30-day error budget exhausted, freeze all changes"
```

### 2.3 Grafana SLO Dashboard

**Create SLO dashboard:**

```json
{
  "dashboard": {
    "title": "SLO Dashboard",
    "panels": [
      {
        "title": "API Availability SLO",
        "targets": [
          {
            "expr": "sli:api_availability:ratio_rate5m",
            "legendFormat": "Current"
          },
          {
            "expr": "0.999",
            "legendFormat": "SLO Target (99.9%)"
          }
        ]
      },
      {
        "title": "Error Budget Remaining",
        "targets": [
          {
            "expr": "1 - ((1 - sli:api_availability:ratio_rate5m) / 0.001)",
            "legendFormat": "Budget %"
          }
        ]
      },
      {
        "title": "API Latency P95 vs SLO",
        "targets": [
          {
            "expr": "sli:api_latency:p95",
            "legendFormat": "Current P95"
          },
          {
            "expr": "0.200",
            "legendFormat": "SLO Target (200ms)"
          }
        ]
      }
    ]
  }
}
```

**Estimated Effort:** 3-4 days

---

## Phase 3: Automated Runbook Execution (Week 2-3)

### 3.1 Ansible Playbooks

**Common Operations Playbooks:**

```yaml
# operations/playbooks/restart_janusgraph.yml

---
- name: Restart JanusGraph Service
  hosts: janusgraph
  become: yes
  tasks:
    - name: Check JanusGraph health
      uri:
        url: "http://localhost:8182/health"
        status_code: 200
      register: health_check
      ignore_errors: yes
    
    - name: Stop JanusGraph if unhealthy
      systemd:
        name: janusgraph
        state: stopped
      when: health_check.failed
    
    - name: Wait for graceful shutdown
      wait_for:
        port: 8182
        state: stopped
        timeout: 60
    
    - name: Start JanusGraph
      systemd:
        name: janusgraph
        state: started
    
    - name: Wait for service to be ready
      uri:
        url: "http://localhost:8182/health"
        status_code: 200
      register: result
      until: result.status == 200
      retries: 10
      delay: 5
    
    - name: Verify vertex count
      uri:
        url: "http://localhost:8182?gremlin=g.V().count()"
        method: GET
      register: vertex_count
    
    - name: Send notification
      slack:
        token: "{{ slack_token }}"
        msg: "JanusGraph restarted successfully. Vertex count: {{ vertex_count.json.result.data }}"
```

**Additional Playbooks:**

```yaml
# operations/playbooks/scale_hcd.yml
# operations/playbooks/backup_graph.yml
# operations/playbooks/restore_graph.yml
# operations/playbooks/clear_cache.yml
# operations/playbooks/rotate_logs.yml
```

### 3.2 Self-Healing Automation

**Automated remediation for common issues:**

```yaml
# operations/playbooks/self_healing.yml

---
- name: Self-Healing Automation
  hosts: all
  tasks:
    # High memory usage
    - name: Restart service if memory > 90%
      block:
        - name: Check memory usage
          shell: free | grep Mem | awk '{print ($3/$2) * 100.0}'
          register: memory_usage
        
        - name: Restart if high memory
          systemd:
            name: "{{ service_name }}"
            state: restarted
          when: memory_usage.stdout | float > 90.0
    
    # Disk space low
    - name: Clean old logs if disk > 85%
      block:
        - name: Check disk usage
          shell: df -h / | tail -1 | awk '{print $5}' | sed 's/%//'
          register: disk_usage
        
        - name: Clean logs if disk full
          shell: find /var/log -name "*.log" -mtime +7 -delete
          when: disk_usage.stdout | int > 85
    
    # Service down
    - name: Restart service if down
      block:
        - name: Check service status
          systemd:
            name: "{{ service_name }}"
          register: service_status
        
        - name: Restart if stopped
          systemd:
            name: "{{ service_name }}"
            state: restarted
          when: service_status.status.ActiveState != "active"
```

### 3.3 Incident Response Automation

**Automated incident response:**

```python
# src/python/sre/incident_response.py

from typing import Dict, List
import subprocess
import logging

class IncidentResponder:
    """Automated incident response system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.playbooks = {
            "high_latency": "operations/playbooks/clear_cache.yml",
            "service_down": "operations/playbooks/restart_service.yml",
            "disk_full": "operations/playbooks/clean_logs.yml",
            "memory_leak": "operations/playbooks/restart_service.yml",
        }
    
    def respond(self, incident_type: str, context: Dict) -> bool:
        """Execute automated response for incident."""
        playbook = self.playbooks.get(incident_type)
        
        if not playbook:
            self.logger.warning(f"No playbook for incident: {incident_type}")
            return False
        
        try:
            # Execute Ansible playbook
            result = subprocess.run(
                ["ansible-playbook", playbook, "-e", f"context={context}"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully resolved {incident_type}")
                return True
            else:
                self.logger.error(f"Failed to resolve {incident_type}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing playbook: {e}")
            return False
```

**Estimated Effort:** 5-7 days

---

## Phase 4: Documentation & Training (Week 3)

### 4.1 SRE Documentation

**Create comprehensive SRE docs:**

- `docs/operations/sre-overview.md` - SRE principles and practices
- `docs/operations/slo-sli-guide.md` - SLO/SLI definitions and monitoring
- `docs/operations/error-budget-policy.md` - Error budget policy and enforcement
- `docs/operations/runbook-automation-guide.md` - Automated runbook execution
- `docs/operations/incident-response-guide.md` - Incident response procedures

### 4.2 Runbook Documentation

**Document all automated runbooks:**

```markdown
# Runbook: Restart JanusGraph Service

## When to Use
- JanusGraph health check failing
- High query latency (>5s P99)
- Memory usage >90%

## Automated Execution
```bash
ansible-playbook operations/playbooks/restart_janusgraph.yml
```

## Manual Steps (if automation fails)
1. SSH to JanusGraph server
2. Check logs: `journalctl -u janusgraph -n 100`
3. Stop service: `systemctl stop janusgraph`
4. Verify stopped: `systemctl status janusgraph`
5. Start service: `systemctl start janusgraph`
6. Verify health: `curl http://localhost:8182/health`

## Rollback
If restart fails, restore from backup:
```bash
ansible-playbook operations/playbooks/restore_graph.yml
```

## Post-Incident
- Review logs for root cause
- Update runbook if needed
- File incident report
```

### 4.3 Training Materials

**Create training materials:**

- SRE principles presentation
- SLO/SLI workshop
- Error budget policy training
- Runbook automation demo
- Incident response drill

**Estimated Effort:** 2-3 days

---

## Success Criteria

### SLO/SLI Implementation
- ✅ 10+ SLIs defined and monitored
- ✅ 6+ SLOs with error budgets
- ✅ Error budget policy documented
- ✅ Prometheus recording rules configured
- ✅ Grafana SLO dashboard created
- ✅ SLO alerts configured

### Automated Runbooks
- ✅ 5+ Ansible playbooks created
- ✅ Self-healing automation implemented
- ✅ Incident response automation
- ✅ All runbooks documented
- ✅ Training materials complete

### Impact
- **Operations Score:** 9.6 → 9.8 (+0.2)
- **Overall Score:** 9.9 → 10.0 (+0.1) (with other actions)

---

## Timeline

| Week | Tasks | Deliverables |
|------|-------|--------------|
| Week 1 | SLO/SLI definition, error budget policy | SLO configs, policy doc |
| Week 2 | Monitoring setup, playbook development | Dashboards, 5+ playbooks |
| Week 3 | Self-healing, incident response, docs | Automation, training |

**Total Effort:** 2-3 weeks  
**Resources:** 1 SRE + 1 developer  
**Dependencies:** Prometheus, Grafana, Ansible

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| SLOs too strict | High | Start conservative, adjust based on data |
| Automation failures | Medium | Manual fallback procedures documented |
| False positive alerts | Low | Tune alert thresholds, add context |

---

## Next Steps

1. ⏳ Review and approve SLO/SLI definitions
2. ⏳ Configure Prometheus recording rules
3. ⏳ Create Grafana SLO dashboard
4. ⏳ Develop Ansible playbooks
5. ⏳ Implement self-healing automation
6. ⏳ Document runbooks
7. ⏳ Conduct training
8. ⏳ Deploy to production

---

**Status:** Ready to start  
**Owner:** SRE Team  
**Reviewer:** Engineering Manager  
**Next Review:** 2026-04-16 (Week 1 checkpoint)