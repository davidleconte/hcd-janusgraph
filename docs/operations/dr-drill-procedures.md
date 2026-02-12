# Disaster Recovery Drill Procedures

**Date:** 2026-02-11  
**Version:** 1.0  
**Status:** Active  
**Platform:** HCD + JanusGraph Banking Compliance Platform

---

## Executive Summary

This document defines comprehensive Disaster Recovery (DR) drill procedures for the HCD + JanusGraph Banking Compliance Platform. These drills validate recovery capabilities, train operations teams, and ensure compliance with RTO/RPO targets.

**Drill Schedule:**
- **Monthly:** Component-level drills (2 hours)
- **Quarterly:** Full system DR drill (4 hours)
- **Annually:** Cross-region failover drill (8 hours)

**Success Criteria:**
- All services restored within RTO targets
- Data loss within RPO limits
- Complete documentation of issues
- Team proficiency demonstrated

---

## Quick Reference

### Drill Types

| Type | Frequency | Duration | Scope | Impact |
|------|-----------|----------|-------|--------|
| Component | Monthly | 2h | Single service | Low |
| System | Quarterly | 4h | Full stack | Medium |
| Failover | Annually | 8h | Cross-region | High |
| Tabletop | Quarterly | 1h | Discussion only | None |

### 5 Core Drill Scenarios

1. **Single Service Failure** - JanusGraph container crash (5 min RTO)
2. **Data Corruption** - HCD data restore from backup (30 min RTO)
3. **Complete Infrastructure Loss** - Full system rebuild (4h RTO)
4. **Network Partition** - Circuit breaker validation (30s RTO)
5. **Message Replay** - Pulsar event sourcing recovery (2h RTO)

---

## Pre-Drill Preparation

### Planning Checklist (2 weeks before)

```markdown
Infrastructure:
- [ ] Backup environment available
- [ ] Recent backups verified (< 24 hours)
- [ ] Network connectivity tested
- [ ] Access credentials validated
- [ ] Monitoring tools configured

Documentation:
- [ ] Recovery procedures reviewed
- [ ] Runbooks updated
- [ ] Contact list current
- [ ] Communication templates prepared

Team:
- [ ] All participants confirmed
- [ ] Roles assigned
- [ ] Pre-drill briefing scheduled
- [ ] Post-drill debrief scheduled

Tools:
- [ ] Communication channels tested
- [ ] Screen sharing configured
- [ ] Recording tools ready
- [ ] Documentation templates ready
```

### Pre-Drill Snapshot Script

```bash
#!/bin/bash
# pre-drill-snapshot.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAPSHOT_DIR="/backup/dr-drill-${TIMESTAMP}"
mkdir -p "$SNAPSHOT_DIR"

echo "=== Pre-Drill Snapshot ==="
echo "Timestamp: $TIMESTAMP"

# Capture service status
podman ps --all --format json > "$SNAPSHOT_DIR/services-before.json"

# Capture volumes
podman volume ls --format json > "$SNAPSHOT_DIR/volumes-before.json"

# Test database connectivity
curl -s -X POST http://localhost:18182 \
  -d '{"gremlin":"g.V().count()"}' \
  -H "Content-Type: application/json" > "$SNAPSHOT_DIR/graph-count-before.json"

echo "✓ Snapshot complete: $SNAPSHOT_DIR"
```

---

## Drill Scenario 1: Single Service Failure

**Objective:** Validate automatic recovery  
**RTO Target:** 5 minutes  
**RPO Target:** 0 (no data loss)

### Execution

```bash
#!/bin/bash
# scenario-1-service-failure.sh

echo "=== Scenario 1: Single Service Failure ==="
START_TIME=$(date +%s)

# 1. Simulate failure
podman kill janusgraph-demo_janusgraph-server_1

# 2. Monitor automatic recovery
while true; do
  STATUS=$(podman ps --filter "name=janusgraph-demo_janusgraph-server_1" --format "{{.Status}}")
  echo "Status: $STATUS"
  
  if echo "$STATUS" | grep -q "healthy"; then
    END_TIME=$(date +%s)
    RECOVERY_TIME=$((END_TIME - START_TIME))
    echo "✓ Service recovered in ${RECOVERY_TIME}s"
    break
  fi
  sleep 5
done

# 3. Verify functionality
curl -X POST http://localhost:18182 \
  -d '{"gremlin":"g.V().count()"}' \
  -H "Content-Type: application/json"

echo "Recovery time: ${RECOVERY_TIME}s (Target: < 300s)"
echo "Status: $([ $RECOVERY_TIME -lt 300 ] && echo 'PASS ✓' || echo 'FAIL ✗')"
```

### Success Criteria

- [ ] Failure detected within 30 seconds
- [ ] Container automatically restarted
- [ ] Service healthy within 2 minutes
- [ ] All queries functional
- [ ] No data loss
- [ ] Total recovery time < 5 minutes

---

## Drill Scenario 2: Data Corruption

**Objective:** Restore from backup  
**RTO Target:** 30 minutes  
**RPO Target:** 15 minutes

### Execution

```bash
#!/bin/bash
# scenario-2-data-corruption.sh

echo "=== Scenario 2: Data Corruption Recovery ==="
START_TIME=$(date +%s)

# 1. Stop services
podman stop janusgraph-demo_janusgraph-server_1
podman stop janusgraph-demo_hcd-server_1

# 2. Identify last good backup
BACKUP_FILE=$(ls -t /backup/hcd/hcd-*.tar.gz | head -1)
echo "Using backup: $BACKUP_FILE"

# 3. Restore from backup
podman volume rm janusgraph-demo_hcd-data
podman volume create janusgraph-demo_hcd-data

podman run --rm \
  -v janusgraph-demo_hcd-data:/data \
  -v /backup/hcd:/backup \
  alpine sh -c "cd /data && tar xzf $BACKUP_FILE"

# 4. Restart services
podman start janusgraph-demo_hcd-server_1

# Wait for HCD
while ! podman ps --filter "name=janusgraph-demo_hcd-server_1" --filter "health=healthy" | grep -q healthy; do
  echo "Waiting for HCD..."
  sleep 10
done

podman start janusgraph-demo_janusgraph-server_1

# Wait for JanusGraph
while ! podman ps --filter "name=janusgraph-demo_janusgraph-server_1" --filter "health=healthy" | grep -q healthy; do
  echo "Waiting for JanusGraph..."
  sleep 10
done

# 5. Verify data integrity
VERTEX_COUNT=$(curl -s -X POST http://localhost:18182 \
  -d '{"gremlin":"g.V().count()"}' \
  -H "Content-Type: application/json" | jq -r '.result.data[0]')

END_TIME=$(date +%s)
RECOVERY_TIME=$((END_TIME - START_TIME))

echo "Vertex count: $VERTEX_COUNT"
echo "Recovery time: ${RECOVERY_TIME}s (Target: < 1800s)"
echo "Status: $([ $RECOVERY_TIME -lt 1800 ] && echo 'PASS ✓' || echo 'FAIL ✗')"
```

### Success Criteria

- [ ] Services stopped cleanly
- [ ] Correct backup identified
- [ ] Restore completed successfully
- [ ] Services restarted and healthy
- [ ] Data integrity verified
- [ ] Total recovery time < 30 minutes

---

## Drill Scenario 3: Complete Infrastructure Loss

**Objective:** Full system recovery  
**RTO Target:** 4 hours  
**RPO Target:** 15 minutes

### Execution Phases

**Phase 1: Infrastructure (30 min)**
```bash
# Verify Podman machine
podman machine list
podman machine start

# Verify backups
ls -lh /backup/hcd/hcd-latest.tar.gz
ls -lh /backup/janusgraph/janusgraph-latest.tar.gz
```

**Phase 2: Volume Restoration (60 min)**
```bash
# Create and restore volumes
for volume in hcd-data janusgraph-db opensearch-data; do
  podman volume create janusgraph-demo_${volume}
  podman run --rm \
    -v janusgraph-demo_${volume}:/data \
    -v /backup/${volume%-*}:/backup \
    alpine sh -c "cd /data && tar xzf /backup/${volume%-*}-latest.tar.gz"
done
```

**Phase 3: Service Deployment (90 min)**
```bash
# Deploy full stack
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d

# Wait for services
sleep 90
```

**Phase 4: Validation (30 min)**
```bash
# Run preflight checks
./scripts/validation/preflight_check.sh

# Verify data
curl -X POST http://localhost:18182 \
  -d '{"gremlin":"g.V().count()"}' \
  -H "Content-Type: application/json"
```

### Success Criteria

- [ ] All volumes restored
- [ ] All services healthy
- [ ] Data integrity verified
- [ ] Monitoring operational
- [ ] Total recovery time < 4 hours

---

## Validation & Testing

### Data Integrity Validation

```bash
#!/bin/bash
# validate-data-integrity.sh

echo "=== Data Integrity Validation ==="

# 1. Verify vertex counts
CURRENT=$(curl -s -X POST http://localhost:18182 \
  -d '{"gremlin":"g.V().count()"}' \
  -H "Content-Type: application/json" | jq -r '.result.data[0]')

EXPECTED=$(jq -r '.result.data[0]' $SNAPSHOT_DIR/graph-count-before.json)

if [ "$CURRENT" -eq "$EXPECTED" ]; then
  echo "✓ Vertex count matches: $CURRENT"
else
  echo "✗ Vertex count mismatch: $CURRENT (expected $EXPECTED)"
fi

# 2. Verify graph connectivity
CONNECTED=$(curl -s -X POST http://localhost:18182 \
  -d '{"gremlin":"g.V().hasLabel(\"Person\").limit(100).out().count()"}' \
  -H "Content-Type: application/json" | jq -r '.result.data[0]')
echo "Connected vertices: $CONNECTED"

# 3. Verify recent data (RPO check)
RPO_MS=$((15 * 60 * 1000))
RECENT=$(curl -s -X POST http://localhost:18182 \
  -d "{\"gremlin\":\"g.V().has('timestamp', gt(now() - $RPO_MS)).count()\"}" \
  -H "Content-Type: application/json" | jq -r '.result.data[0]')
echo "Recent vertices (last 15min): $RECENT"
```

### Functional Testing

```bash
#!/bin/bash
# functional-tests.sh

echo "=== Functional Testing ==="

# Test graph queries
test_query() {
  local query=$1
  local description=$2
  
  echo "Testing: $description"
  RESULT=$(curl -s -X POST http://localhost:18182 \
    -d "{\"gremlin\":\"$query\"}" \
    -H "Content-Type: application/json")
  
  if echo "$RESULT" | jq -e '.result.data' > /dev/null 2>&1; then
    echo "  ✓ PASS"
  else
    echo "  ✗ FAIL"
  fi
}

test_query "g.V().count()" "Vertex count"
test_query "g.E().count()" "Edge count"
test_query "g.V().hasLabel('Person').limit(10).values('name')" "Person names"

# Test API endpoints
curl -s http://localhost:8001/health | jq .
curl -s http://localhost:9090/-/healthy
curl -s http://localhost:3001/api/health
```

---

## Post-Drill Activities

### Immediate Debrief Template

```markdown
# DR Drill Debrief - [Date]

## Drill Information
- **Date:** [YYYY-MM-DD]
- **Type:** [Component/System/Failover]
- **Duration:** [Actual] vs [Expected]

## Objectives
- [ ] Objective 1: [Met/Not Met]
- [ ] Objective 2: [Met/Not Met]

## What Went Well
1. [Success 1]
2. [Success 2]

## What Went Wrong
1. [Issue 1] - Impact: [High/Medium/Low]
2. [Issue 2] - Impact: [High/Medium/Low]

## Metrics
- **RTO Target:** [X hours]
- **RTO Actual:** [Y hours]
- **RPO Target:** [X minutes]
- **RPO Actual:** [Y minutes]

## Action Items
| # | Action | Owner | Due Date | Priority |
|---|--------|-------|----------|----------|
| 1 | [Action] | [Name] | [Date] | [H/M/L] |

## Next Drill
- **Date:** [YYYY-MM-DD]
- **Focus:** [What to improve]
```

### Action Item Tracking

```markdown
# Action Item: [Title]

**ID:** AI-[YYYY-MM-DD]-[Number]  
**Owner:** [Name]  
**Priority:** [High/Medium/Low]  
**Due Date:** [Date]

## Description
[What needs to be done]

## Root Cause
[Why this action is needed]

## Implementation Plan
1. [Step 1]
2. [Step 2]

## Verification
[How to verify completion]
```

---

## Annual Drill Calendar

```
Month      Week  Drill Type           Duration
──────────────────────────────────────────────
January    2     Component            2h
February   1     Component            2h
March      3     System (Quarterly)   4h
April      2     Component            2h
May        1     Component            2h
June       4     System (Quarterly)   4h
July       2     Component            2h
August     1     Component            2h
September  3     System (Quarterly)   4h
October    2     Failover (Annual)    8h
November   1     Component            2h
December   4     System (Quarterly)   4h
──────────────────────────────────────────────
Total: 16 drills, 48 hours annually
```

---

## Related Documentation

- **HA/DR Architecture:** [`docs/architecture/ha-dr-resilient-architecture.md`](../architecture/ha-dr-resilient-architecture.md)
- **RTO/RPO Targets:** [`docs/operations/rto-rpo-targets.md`](rto-rpo-targets.md)
- **Incident Response:** [`docs/operations/incident-response-runbook.md`](incident-response-runbook.md)

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-11  
**Next Review:** 2026-05-11 (Quarterly)  
**Owner:** Platform Engineering Team
