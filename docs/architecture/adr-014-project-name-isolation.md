# ADR-014: Project-Name Isolation for Multi-Project Environments

**Status**: Accepted  
**Date**: 2026-02-19  
**Deciders**: Platform Engineering Team, DevOps Team  
**Technical Story**: Architecture documentation improvement initiative

## Context

When running multiple projects or multiple instances of the same project on a single Podman machine, resource conflicts can occur. Containers, networks, and volumes from different projects can interfere with each other, leading to unpredictable behavior and difficult debugging.

### Problem Statement

We need a reliable mechanism to:
- Isolate resources between different projects
- Allow multiple project instances on the same machine
- Prevent naming conflicts
- Enable clean project-specific cleanup
- Support concurrent development and testing

### Constraints

- Must work with podman-compose
- Must not require manual resource naming
- Must be enforceable in scripts and CI/CD
- Must support project-specific operations (start, stop, cleanup)
- Must be compatible with existing Docker Compose patterns

### Assumptions

- Developers may run multiple projects simultaneously
- CI/CD runners may execute multiple pipelines concurrently
- Project names are unique within an environment
- Resource prefixing is acceptable overhead

## Decision Drivers

- **Isolation**: Prevent cross-project interference
- **Clarity**: Easy to identify which resources belong to which project
- **Cleanup**: Enable complete project-specific cleanup
- **Concurrency**: Support multiple projects on same machine
- **Debugging**: Clear resource ownership for troubleshooting

## Considered Options

### Option 1: No Isolation (Default Behavior)

**Pros:**
- Simple, no configuration needed
- Works out of the box
- No naming overhead

**Cons:**
- Resource conflicts between projects
- Cannot run multiple instances
- Difficult cleanup (affects all projects)
- Unclear resource ownership
- Debugging nightmares

### Option 2: Manual Resource Naming

**Pros:**
- Full control over names
- Explicit resource identification

**Cons:**
- Error-prone (easy to forget)
- Inconsistent naming across team
- Requires changes to all compose files
- No automatic enforcement
- High maintenance burden

### Option 3: Project-Name Isolation (COMPOSE_PROJECT_NAME)

**Pros:**
- Automatic resource prefixing
- Enforced by podman-compose
- Standard Docker Compose pattern
- Easy to implement
- Clear resource ownership
- Supports concurrent projects

**Cons:**
- Requires setting environment variable
- Longer resource names
- Must be consistent across operations

## Decision

**We will use `COMPOSE_PROJECT_NAME` environment variable to enforce project-name isolation for all Podman deployments.**

### Rationale

1. **Standard Pattern**: `COMPOSE_PROJECT_NAME` is a standard Docker Compose environment variable, ensuring compatibility and familiarity.

2. **Automatic Enforcement**: podman-compose automatically prefixes all resources (containers, networks, volumes) with the project name.

3. **Clear Ownership**: Resource names clearly indicate which project they belong to:
   - `janusgraph-demo_hcd-server_1` (not just `hcd-server_1`)
   - `janusgraph-demo_hcd-janusgraph-network` (not just `hcd-janusgraph-network`)

4. **Concurrent Projects**: Multiple projects can coexist:
   - `janusgraph-demo` (main project)
   - `janusgraph-test` (test environment)
   - `janusgraph-dev` (development)

5. **Clean Cleanup**: Project-specific cleanup is straightforward:
   ```bash
   podman-compose -p janusgraph-demo down -v
   ```

6. **Scriptable**: Easy to enforce in scripts and CI/CD pipelines.

## Consequences

### Positive

- **Complete Isolation**: No resource conflicts between projects
- **Concurrent Development**: Multiple projects can run simultaneously
- **Clear Ownership**: Easy to identify which resources belong to which project
- **Clean Cleanup**: Remove all project resources with single command
- **Debugging**: Clear resource names aid troubleshooting
- **CI/CD Friendly**: Easy to enforce in automated pipelines

### Negative

- **Longer Names**: Resource names are longer (includes project prefix)
- **Environment Variable**: Must remember to set `COMPOSE_PROJECT_NAME`
- **Consistency Required**: Must use same project name across all operations
- **Documentation**: Team must understand and follow convention

### Neutral

- **Standard Practice**: Aligns with Docker Compose best practices
- **Explicit Configuration**: Requires explicit project name (no implicit defaults)

## Implementation

### Required Changes

1. **Environment Variable**:
   ```bash
   # Set in .env file
   COMPOSE_PROJECT_NAME=janusgraph-demo
   
   # Or export in shell
   export COMPOSE_PROJECT_NAME=janusgraph-demo
   ```

2. **Deployment Scripts**:
   ```bash
   # scripts/deployment/deploy_full_stack.sh
   : "${COMPOSE_PROJECT_NAME:=janusgraph-demo}"
   export COMPOSE_PROJECT_NAME
   
   podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d
   ```

3. **Validation Scripts**:
   ```bash
   # scripts/validation/preflight_check.sh
   if [ -z "$COMPOSE_PROJECT_NAME" ]; then
       echo "❌ COMPOSE_PROJECT_NAME not set"
       exit 1
   fi
   ```

4. **Documentation**:
   - Update README.md with project name requirement
   - Add to QUICKSTART.md
   - Document in deployment guides

5. **CI/CD Workflows**:
   ```yaml
   env:
     COMPOSE_PROJECT_NAME: janusgraph-demo
   
   steps:
     - name: Deploy
       run: |
         podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d
   ```

### Migration Path

**For Existing Deployments:**

1. **Stop Current Deployment** (if using default names):
   ```bash
   podman-compose down -v
   ```

2. **Set Project Name**:
   ```bash
   export COMPOSE_PROJECT_NAME=janusgraph-demo
   ```

3. **Redeploy with Project Name**:
   ```bash
   podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d
   ```

4. **Verify Isolation**:
   ```bash
   podman ps --filter "label=io.podman.compose.project=$COMPOSE_PROJECT_NAME"
   podman network ls --filter "label=io.podman.compose.project=$COMPOSE_PROJECT_NAME"
   podman volume ls --filter "label=io.podman.compose.project=$COMPOSE_PROJECT_NAME"
   ```

**Coexistence**: Old (non-prefixed) and new (prefixed) resources can coexist, but should be cleaned up separately.

### Rollback Strategy

If project-name isolation causes issues:

1. **Remove Project Name**:
   ```bash
   unset COMPOSE_PROJECT_NAME
   ```

2. **Deploy Without Project Name**:
   ```bash
   podman-compose -f docker-compose.full.yml up -d
   ```

3. **Update Scripts**: Remove `-p` flag from all scripts

**Rollback Trigger**: If project name causes compatibility issues with critical tooling.

## Compliance

- [x] Security review completed (isolation improves security)
- [x] Performance impact assessed (negligible)
- [x] Documentation updated (README, QUICKSTART, guides)
- [x] Team notified (training on project naming)

## References

- [Docker Compose Project Name](https://docs.docker.com/compose/environment-variables/envvars/#compose_project_name)
- [Podman Compose Documentation](https://github.com/containers/podman-compose)
- [Podman Isolation Architecture](podman-isolation-architecture.md)
- [Deployment Architecture](deployment-architecture.md)

## Notes

### Project Naming Convention

**Format**: `<product>-<environment>`

**Examples**:
- `janusgraph-demo` - Demo/development environment
- `janusgraph-test` - Test environment
- `janusgraph-staging` - Staging environment
- `janusgraph-prod` - Production environment

**Rules**:
- Use lowercase
- Use hyphens (not underscores)
- Keep it short but descriptive
- Be consistent across team

### Resource Naming Pattern

With `COMPOSE_PROJECT_NAME=janusgraph-demo`:

| Resource Type | Pattern | Example |
|---------------|---------|---------|
| **Container** | `{project}_{service}_{replica}` | `janusgraph-demo_hcd-server_1` |
| **Network** | `{project}_{network}` | `janusgraph-demo_hcd-janusgraph-network` |
| **Volume** | `{project}_{volume}` | `janusgraph-demo_hcd-data` |

### Verification Commands

**Check Project Resources**:
```bash
# List all containers for project
podman ps --filter "label=io.podman.compose.project=janusgraph-demo"

# List all networks for project
podman network ls --filter "label=io.podman.compose.project=janusgraph-demo"

# List all volumes for project
podman volume ls --filter "label=io.podman.compose.project=janusgraph-demo"
```

**Cleanup Project Resources**:
```bash
# Stop and remove all project resources
podman-compose -p janusgraph-demo -f docker-compose.full.yml down -v

# Or manually
podman ps -a --filter "label=io.podman.compose.project=janusgraph-demo" --format "{{.Names}}" | xargs podman rm -f
podman volume ls --filter "label=io.podman.compose.project=janusgraph-demo" --format "{{.Name}}" | xargs podman volume rm -f
podman network ls --filter "label=io.podman.compose.project=janusgraph-demo" --format "{{.Name}}" | xargs podman network rm -f
```

### Multi-Project Scenarios

**Scenario 1: Development + Testing**
```bash
# Terminal 1: Development
export COMPOSE_PROJECT_NAME=janusgraph-dev
podman-compose -p $COMPOSE_PROJECT_NAME up -d

# Terminal 2: Testing
export COMPOSE_PROJECT_NAME=janusgraph-test
podman-compose -p $COMPOSE_PROJECT_NAME up -d

# Both run independently, no conflicts
```

**Scenario 2: Feature Branch Testing**
```bash
# Main branch
export COMPOSE_PROJECT_NAME=janusgraph-main
podman-compose -p $COMPOSE_PROJECT_NAME up -d

# Feature branch
export COMPOSE_PROJECT_NAME=janusgraph-feature-123
podman-compose -p $COMPOSE_PROJECT_NAME up -d

# Test both simultaneously
```

**Scenario 3: CI/CD Concurrent Builds**
```yaml
# GitHub Actions
jobs:
  test-pr-123:
    env:
      COMPOSE_PROJECT_NAME: janusgraph-pr-123
  
  test-pr-456:
    env:
      COMPOSE_PROJECT_NAME: janusgraph-pr-456

# Both can run on same runner without conflicts
```

### Troubleshooting

**Issue**: Resources not prefixed with project name

**Solution**: Ensure `-p` flag is used:
```bash
# ❌ WRONG
podman-compose up -d

# ✅ CORRECT
podman-compose -p janusgraph-demo up -d
```

**Issue**: Cannot find project resources

**Solution**: Check project name matches:
```bash
# List all projects
podman ps -a --format "{{.Labels}}" | grep "io.podman.compose.project" | sort -u

# Use correct project name
export COMPOSE_PROJECT_NAME=<actual-project-name>
```

**Issue**: Old resources interfering

**Solution**: Clean up old resources:
```bash
# List all resources (no project filter)
podman ps -a
podman network ls
podman volume ls

# Remove old resources manually
podman rm <container>
podman network rm <network>
podman volume rm <volume>
```

### Best Practices

1. **Always Set Project Name**:
   ```bash
   # In .env file
   COMPOSE_PROJECT_NAME=janusgraph-demo
   
   # Or in scripts
   : "${COMPOSE_PROJECT_NAME:=janusgraph-demo}"
   export COMPOSE_PROJECT_NAME
   ```

2. **Use Consistent Names**:
   ```bash
   # Same project name for all operations
   podman-compose -p janusgraph-demo up -d
   podman-compose -p janusgraph-demo down
   podman-compose -p janusgraph-demo logs
   ```

3. **Validate Before Operations**:
   ```bash
   if [ -z "$COMPOSE_PROJECT_NAME" ]; then
       echo "❌ COMPOSE_PROJECT_NAME not set"
       exit 1
   fi
   ```

4. **Document Project Names**:
   ```bash
   # In README.md
   ## Project Names
   - `janusgraph-demo`: Main demo environment
   - `janusgraph-test`: Test environment
   - `janusgraph-dev`: Development environment
   ```

5. **Clean Up After Testing**:
   ```bash
   # Always clean up test projects
   podman-compose -p janusgraph-test down -v
   ```

### Future Considerations

- **Namespace Isolation**: Consider Kubernetes namespaces for production
- **Resource Quotas**: Implement per-project resource limits
- **Monitoring**: Add project-level monitoring and alerting
- **Automation**: Auto-generate project names for CI/CD

---

**Last Updated**: 2026-02-19  
**Next Review**: 2026-05-19 (3 months)  
**Owner**: Platform Engineering Team