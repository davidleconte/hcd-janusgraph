# Disaster Recovery Testing Log

**Date:** 2026-02-12
**Version:** 1.0
**Status:** Active
**Owner:** Platform Engineering Team

## TL;DR

This document tracks all DR drill executions, records results against RTO/RPO targets, and captures lessons learned. Use this as the living record for compliance evidence and continuous improvement.

---

## Drill Execution Register

### Format

Each drill entry follows this structure:

| Field | Description |
|-------|-------------|
| **Drill ID** | DR-YYYY-MM-NNN |
| **Date** | Execution date |
| **Type** | Component / System / Failover / Tabletop |
| **Scenario** | Which scenario from [dr-drill-procedures.md](dr-drill-procedures.md) |
| **Participants** | Team members involved |
| **RTO Target** | From [rto-rpo-targets.md](rto-rpo-targets.md) |
| **RTO Actual** | Measured recovery time |
| **RPO Target** | Expected data loss window |
| **RPO Actual** | Measured data loss |
| **Result** | PASS / FAIL / PARTIAL |
| **Issues** | Problems encountered |
| **Action Items** | Follow-up tasks |

---

## 2026 Drill Log

### DR-2026-02-001: Component Drill — Single Service Failure

| Field | Value |
|-------|-------|
| **Date** | 2026-02-XX (Scheduled) |
| **Type** | Component |
| **Scenario** | Scenario 1: Single Service Failure (JanusGraph crash) |
| **Participants** | TBD |
| **RTO Target** | 5 minutes |
| **RTO Actual** | — |
| **RPO Target** | 0 (no data loss) |
| **RPO Actual** | — |
| **Result** | — |

**Pre-Drill Checklist:**
- [ ] Backup environment verified
- [ ] Monitoring dashboards open
- [ ] Pre-drill snapshot taken (`pre-drill-snapshot.sh`)
- [ ] All participants confirmed
- [ ] Communication channel ready

**Execution Steps:**
```bash
# 1. Take pre-drill snapshot
./scripts/testing/pre-drill-snapshot.sh

# 2. Simulate JanusGraph failure
podman kill janusgraph-demo_janusgraph-server_1

# 3. Record start time
START_TIME=$(date +%s)

# 4. Monitor recovery (auto-restart or manual)
watch -n 5 'podman ps --filter "name=janusgraph" --format "{{.Names}} {{.Status}}"'

# 5. When healthy, record end time
END_TIME=$(date +%s)
echo "Recovery time: $((END_TIME - START_TIME))s"

# 6. Validate data integrity
curl -s -X POST http://localhost:18182 \
  -d '{"gremlin":"g.V().count()"}' \
  -H "Content-Type: application/json"

# 7. Compare with pre-drill snapshot
```

**Results:**
```
RTO Actual:    ___s (Target: < 300s) — PASS / FAIL
RPO Actual:    ___  (Target: 0)      — PASS / FAIL
Data Integrity: ___  vertices (Expected: ___)
Overall:       PASS / FAIL
```

**Issues Encountered:**
1. (None / Describe)

**Action Items:**
| # | Action | Owner | Due | Status |
|---|--------|-------|-----|--------|
| 1 | — | — | — | — |

---

### DR-2026-03-001: System Drill — Data Corruption Recovery

| Field | Value |
|-------|-------|
| **Date** | 2026-03-XX (Scheduled — Q1 Quarterly) |
| **Type** | System |
| **Scenario** | Scenario 2: Data Corruption |
| **RTO Target** | 30 minutes |
| **RPO Target** | 15 minutes |

**Pre-Drill Checklist:**
- [ ] Fresh HCD backup available (< 1 hour old)
- [ ] Backup restore scripts tested
- [ ] Secondary environment ready (if applicable)
- [ ] All participants briefed

**Execution Steps:**
```bash
# See: docs/operations/dr-drill-procedures.md — Scenario 2
./scripts/testing/scenario-2-data-corruption.sh
```

**Results:** (Fill after execution)

---

### DR-2026-06-001: System Drill — Complete Infrastructure Loss

| Field | Value |
|-------|-------|
| **Date** | 2026-06-XX (Scheduled — Q2 Quarterly) |
| **Type** | System |
| **Scenario** | Scenario 3: Complete Infrastructure Loss |
| **RTO Target** | 4 hours |
| **RPO Target** | 15 minutes |

---

### DR-2026-10-001: Annual Failover Drill

| Field | Value |
|-------|-------|
| **Date** | 2026-10-XX (Scheduled — Annual) |
| **Type** | Failover |
| **Scenario** | Cross-region failover |
| **RTO Target** | 4 hours |
| **RPO Target** | 15 minutes |

---

## Metrics Dashboard

### RTO/RPO Trend Tracking

| Drill ID | Date | Scenario | RTO Target | RTO Actual | RPO Target | RPO Actual | Status |
|-----------|------|----------|------------|------------|------------|------------|--------|
| DR-2026-02-001 | TBD | Service Failure | 5 min | — | 0 | — | Scheduled |
| DR-2026-03-001 | TBD | Data Corruption | 30 min | — | 15 min | — | Scheduled |
| DR-2026-06-001 | TBD | Infra Loss | 4 hr | — | 15 min | — | Scheduled |
| DR-2026-10-001 | TBD | Failover | 4 hr | — | 15 min | — | Scheduled |

### Annual Summary (2026)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Drills completed | 16 | 0 | In Progress |
| PASS rate | 100% | — | — |
| Average RTO adherence | < 100% of target | — | — |
| Average RPO adherence | < 100% of target | — | — |
| Action items closed | 100% | — | — |

---

## Automated Drill Validation Script

```bash
#!/bin/bash
# validate-drill-results.sh
# Run after each drill to auto-capture metrics

DRILL_ID=$1
SNAPSHOT_DIR=$2
START_TIME=$3
END_TIME=$4

echo "=== DR Drill Validation: $DRILL_ID ==="

# Calculate RTO
RTO_SECONDS=$((END_TIME - START_TIME))
echo "RTO: ${RTO_SECONDS}s"

# Verify all services healthy
echo "Service Health:"
for svc in hcd-server janusgraph-server opensearch pulsar; do
  STATUS=$(podman ps --filter "name=janusgraph-demo_${svc}" --format "{{.Status}}" 2>/dev/null)
  echo "  $svc: $STATUS"
done

# Verify data integrity
CURRENT_VERTICES=$(curl -s -X POST http://localhost:18182 \
  -d '{"gremlin":"g.V().count()"}' \
  -H "Content-Type: application/json" | jq -r '.result.data[0]' 2>/dev/null)

if [ -f "$SNAPSHOT_DIR/graph-count-before.json" ]; then
  EXPECTED_VERTICES=$(jq -r '.result.data[0]' "$SNAPSHOT_DIR/graph-count-before.json")
  if [ "$CURRENT_VERTICES" == "$EXPECTED_VERTICES" ]; then
    echo "Data Integrity: PASS ($CURRENT_VERTICES vertices)"
  else
    echo "Data Integrity: FAIL ($CURRENT_VERTICES vs expected $EXPECTED_VERTICES)"
  fi
fi

# API health check
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/healthz 2>/dev/null)
echo "API Health: HTTP $API_STATUS"

echo "=== Validation Complete ==="
```

---

## Compliance Evidence

This log serves as evidence for:

| Regulation | Requirement | How This Satisfies |
|------------|-------------|-------------------|
| **SOC 2** | CC7.5 - Recovery testing | Documented drill results with metrics |
| **PCI DSS** | Req 12.10.2 - Test incident response | Regular drill execution and validation |
| **GDPR** | Art 32(1)(c) - Restore availability | Proven recovery capabilities |
| **BSA/AML** | Business continuity | Demonstrated system resilience |

---

## Related Documentation

- [DR Plan](disaster-recovery-plan.md)
- [DR Drill Procedures](dr-drill-procedures.md)
- [RTO/RPO Targets](rto-rpo-targets.md)
- [Backup Procedures](backup-procedures.md)
- [HA/DR Architecture](../architecture/ha-dr-resilient-architecture.md)
- [Operations Runbook](operations-runbook.md)

---

**Next Scheduled Drill:** 2026-02-XX (Component — Service Failure)
**Document Review:** Quarterly (after each system drill)
