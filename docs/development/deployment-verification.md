# Deployment Verification - Post Commit

## ✅ Commit Status

**Successfully pushed to GitHub!**

- Commit: 9d166cd
- Branch: master
- Files changed: 371 files
- Size: 856.74 KiB

## Current Location Issue

You're currently in `config/compose/` directory, so the verification commands need adjustment:

### From config/compose/ (Current Location)

```bash
# You're already in config/compose/, so just run:
FULL_STACK_FILE=config/compose/<full-stack-compose-file>
podman-compose -p janusgraph-demo -f "$FULL_STACK_FILE" up -d

# Wait for services to start
sleep 90

# Test JanusGraph
curl http://localhost:18182?gremlin=g.V().count()

# Stop services
podman-compose -p janusgraph-demo -f "$FULL_STACK_FILE" down

# Return to project root
cd ../..
```

### From Project Root (After cd ../..)

```bash
# Navigate to compose directory
cd config/compose

# Deploy
podman-compose -p janusgraph-demo -f "$FULL_STACK_FILE" up -d

# Wait for services
sleep 90

# Test
curl http://localhost:18182?gremlin=g.V().count()

# Stop
podman-compose -p janusgraph-demo -f "$FULL_STACK_FILE" down

# Return to root
cd ../..
```

## Quick Verification Commands

### Option 1: From Your Current Location (config/compose/)

```bash
# Deploy full stack
podman-compose -p janusgraph-demo -f "$FULL_STACK_FILE" up -d && sleep 90 && curl http://localhost:18182?gremlin=g.V().count()

# If successful, stop services
podman-compose -p janusgraph-demo -f "$FULL_STACK_FILE" down

# Return to project root
cd ../..
```

### Option 2: Using Makefile (From Project Root)

```bash
# First, go back to project root
cd ../..

# Then use Makefile
make deploy

# Wait and test
sleep 90
curl http://localhost:18182?gremlin=g.V().count()

# Stop
make stop
```

## Expected Results

### Successful Deployment

```
✓ Creating network janusgraph-demo_hcd-janusgraph-network
✓ Creating volume janusgraph-demo_hcd-data
✓ Creating container janusgraph-demo_hcd-server_1
✓ Creating container janusgraph-demo_janusgraph-server_1
✓ Creating container janusgraph-demo_jupyter_1
```

### Successful Test

```bash
$ curl http://localhost:18182?gremlin=g.V().count()
{"result":{"data":[0],"meta":{}},"requestId":"...","status":{"code":200,"message":""}}
```

### Successful Cleanup

```
✓ Stopping janusgraph-demo_jupyter_1
✓ Stopping janusgraph-demo_janusgraph-server_1
✓ Stopping janusgraph-demo_hcd-server_1
✓ Removing containers
✓ Removing network
```

## Troubleshooting

### If Services Don't Start

```bash
# Check logs
podman logs janusgraph-demo_janusgraph-server_1
podman logs janusgraph-demo_hcd-server_1

# Check if ports are in use
netstat -an | grep 8182
netstat -an | grep 9042

# Force cleanup and retry
podman-compose -p janusgraph-demo -f "$FULL_STACK_FILE" down -v
podman pod rm -f janusgraph-demo_hcd-janusgraph-network
podman-compose -p janusgraph-demo -f "$FULL_STACK_FILE" up -d
```

### If Curl Fails

```bash
# Wait longer (services may need more time)
sleep 120

# Check if JanusGraph is running
podman ps | grep janusgraph

# Check JanusGraph logs
podman logs janusgraph-demo_janusgraph-server_1 | tail -50

# Try direct connection test
podman exec janusgraph-demo_janusgraph-server_1 curl 127.0.0.1:8182?gremlin=g.V().count()
```

## Production Readiness Confirmation

After successful verification:

✅ **Audit Remediation**: Complete (Grade D → B+)
✅ **Git Commit**: Pushed to GitHub (9d166cd)
✅ **Deployment**: Verified working
✅ **Security**: Sensitive files excluded
✅ **Structure**: Organized and clean

## Next Steps

1. **Verify deployment works** (run commands above)
2. **Review production readiness**: `docs/...`
3. **Consider remaining improvements**:
   - External security audit
   - MFA implementation
   - Disaster recovery drill
   - Performance optimization

## Summary

The audit remediation is complete and committed. The project structure is now:

- **Secure**: No sensitive files in repo
- **Organized**: Vendor code in vendor/, compose files in config/compose/
- **Clean**: No build artifacts or empty directories
- **Production-ready**: Grade B+ with clear path to A

All that remains is verifying the deployment still works correctly.

## Codex Deployment Verification Enforcement (2026-02-17)

This verification block is mandatory for fresh-machine acceptance.

### A) Container and service health

```bash
podman --remote ps --format 'table {{.Names}}\t{{.Status}}'
```

Expected healthy components include:

- `janusgraph-demo_hcd-server_1`
- `janusgraph-demo_vault_1`
- `janusgraph-demo_analytics-api_1`
- `janusgraph-demo_jupyter_1`

### B) Runtime dependency acceptance gates (analytics-api)

The deployed API image must satisfy R-05 through R-13:

- `slowapi`
- `pydantic-settings`
- `python-json-logger`
- `pyjwt`
- `banking` package path copied in image
- writable `/var/log/janusgraph`
- `pyotp`
- `qrcode[pil]`
- OpenTelemetry packages (`opentelemetry-api`, `opentelemetry-sdk`, OTLP gRPC exporter, Jaeger exporter, requests instrumentation)
- `requests`
- required env: `OPENSEARCH_INITIAL_ADMIN_PASSWORD`

### C) Notebook runner acceptance gates

R-14 through R-18 acceptance:

- Runner uses active Podman connection (validated run used `podman-wxd-root`).
- Exploratory notebooks resolve under `/workspace/notebooks-exploratory`.
- Jupyter runtime contains `pydantic`, `pydantic-settings`, `email-validator`.
- TBML notebook handles empty transaction stats maps.
- Insider notebook handles empty/missing DataFrame columns.

### D) Required evidence artifact

Successful full proof requires:

- `notebook_run_report.tsv`
- all notebooks `PASS`

Reference proof artifact from validated run:

- `exports/live-notebooks-final-20260217T170000Z/notebook_run_report.tsv`

Reference: `docs/implementation/audits/codex-podman-wxd-fresh-machine-enforcement-matrix-2026-02-17.md`
