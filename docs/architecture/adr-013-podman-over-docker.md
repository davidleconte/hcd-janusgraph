# ADR-013: Podman Over Docker for Container Runtime

**Status**: Accepted  
**Date**: 2026-02-19  
**Deciders**: Platform Engineering Team, Architecture Team  
**Technical Story**: Architecture documentation improvement initiative

## Context

The HCD + JanusGraph Banking Compliance Platform requires a container runtime for local development, testing, and deployment. The choice of container runtime significantly impacts security, resource management, and operational complexity.

### Problem Statement

We need to select a container runtime that provides:
- Secure container execution (rootless by default)
- Reliable orchestration for multi-container applications
- Compatibility with existing Docker tooling
- Minimal operational overhead
- Support for Kubernetes-compatible pod management

### Constraints

- Must support macOS development environments
- Must be compatible with existing Docker Compose files
- Must support rootless container execution
- Must not require daemon running as root
- Must support project isolation for multiple concurrent projects

### Assumptions

- Developers are familiar with Docker CLI
- Existing Docker Compose files can be reused
- Rootless containers provide sufficient security
- Daemonless architecture is more reliable

## Decision Drivers

- **Security**: Rootless containers reduce attack surface
- **Reliability**: Daemonless architecture eliminates single point of failure
- **Compatibility**: Docker CLI compatibility reduces learning curve
- **Isolation**: Better resource and namespace isolation
- **Future-proofing**: Kubernetes-compatible pod support

## Considered Options

### Option 1: Docker Desktop

**Pros:**
- Industry standard, widely adopted
- Excellent documentation and community support
- Native Docker Compose support
- Familiar to most developers
- Good macOS integration

**Cons:**
- Requires daemon running as root (security concern)
- Single daemon is single point of failure
- Licensing changes (Docker Desktop requires license for large organizations)
- Resource-heavy on macOS
- No native pod support

### Option 2: Podman

**Pros:**
- Rootless by default (better security)
- Daemonless architecture (no single point of failure)
- Docker CLI compatible (drop-in replacement)
- Native pod support (Kubernetes-compatible)
- Open source with no licensing concerns
- Better resource isolation
- Supports Docker Compose via podman-compose

**Cons:**
- Less mature than Docker on macOS
- Requires podman-compose for Compose file support
- Smaller community compared to Docker
- Some Docker features not yet implemented
- Requires podman machine on macOS

### Option 3: containerd + nerdctl

**Pros:**
- Lightweight, focused on container runtime
- Used by Kubernetes
- Good performance
- Open source

**Cons:**
- No native Compose support
- Less Docker-compatible
- Steeper learning curve
- Limited macOS support
- Requires additional tooling

## Decision

**We will use Podman as the container runtime for the HCD + JanusGraph Banking Compliance Platform.**

### Rationale

1. **Security First**: Rootless containers by default significantly reduce security risks. No daemon running as root means smaller attack surface.

2. **Reliability**: Daemonless architecture eliminates the single point of failure that Docker's daemon represents. Each container runs independently.

3. **Compatibility**: Podman is Docker CLI compatible, allowing us to reuse existing Docker Compose files with minimal changes via podman-compose.

4. **Future-Proofing**: Native pod support aligns with Kubernetes patterns, making future migration to Kubernetes easier.

5. **Licensing**: Open source with no licensing concerns, unlike Docker Desktop which requires licenses for large organizations.

6. **Isolation**: Better namespace and resource isolation enables multiple projects on the same machine without conflicts.

## Consequences

### Positive

- **Enhanced Security**: Rootless containers reduce attack surface and eliminate need for root daemon
- **Improved Reliability**: No single daemon means no single point of failure
- **Better Isolation**: Project-level isolation prevents conflicts between concurrent projects
- **Cost Savings**: No Docker Desktop licensing costs
- **Kubernetes Alignment**: Pod support makes Kubernetes migration easier
- **Resource Efficiency**: Better resource isolation and management

### Negative

- **Learning Curve**: Team needs to learn podman-compose and podman machine concepts
- **Tooling Maturity**: Some Docker features not yet available in Podman
- **Community Size**: Smaller community means fewer Stack Overflow answers
- **macOS Complexity**: Requires podman machine (VM) on macOS, adding abstraction layer
- **Documentation Gaps**: Less documentation compared to Docker

### Neutral

- **CLI Compatibility**: Most Docker commands work with Podman, but some differences exist
- **Compose Support**: podman-compose works but has some limitations compared to docker-compose
- **Ecosystem**: Growing ecosystem but not as mature as Docker's

## Implementation

### Required Changes

1. **Installation**:
   ```bash
   # macOS
   brew install podman podman-compose
   
   # Initialize podman machine
   podman machine init --cpus 4 --memory 8192 --disk-size 50
   podman machine start
   ```

2. **Compose Files**: Update compose files to use podman-compose compatible syntax
   - No changes needed for most features
   - Ensure project name is always specified: `-p janusgraph-demo`

3. **Scripts**: Update all deployment scripts to use `podman` and `podman-compose`
   ```bash
   # Replace
   docker ps
   docker-compose up -d
   
   # With
   podman ps
   podman-compose -p janusgraph-demo up -d
   ```

4. **Documentation**: Update all documentation to reference Podman
   - README.md
   - QUICKSTART.md
   - Deployment guides
   - Troubleshooting guides

5. **CI/CD**: Update GitHub Actions workflows to use Podman
   ```yaml
   - name: Install Podman
     run: |
       sudo apt-get update
       sudo apt-get install -y podman
   ```

### Migration Path

**For Existing Docker Users:**

1. **Install Podman**:
   ```bash
   brew install podman podman-compose
   podman machine init --cpus 4 --memory 8192
   podman machine start
   ```

2. **Stop Docker Services**:
   ```bash
   docker-compose down
   ```

3. **Deploy with Podman**:
   ```bash
   cd config/compose
   podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d
   ```

4. **Verify**:
   ```bash
   podman ps --filter "label=project=janusgraph-demo"
   ```

**Coexistence Period:**
- Docker and Podman can coexist on the same machine
- Use aliases to prevent accidental Docker usage:
  ```bash
  alias docker='echo "Use podman instead" && false'
  alias docker-compose='echo "Use podman-compose instead" && false'
  ```

### Rollback Strategy

If Podman proves problematic:

1. **Stop Podman Services**:
   ```bash
   podman-compose -p janusgraph-demo down
   ```

2. **Reinstall Docker Desktop**:
   ```bash
   brew install --cask docker
   ```

3. **Revert Scripts**: Change `podman` back to `docker` in scripts

4. **Deploy with Docker**:
   ```bash
   docker-compose -f docker-compose.full.yml up -d
   ```

**Rollback Trigger**: If critical features are unavailable or stability issues persist after 2 weeks.

## Compliance

- [x] Security review completed (rootless containers approved)
- [x] Performance impact assessed (comparable to Docker)
- [x] Documentation updated (README, QUICKSTART, guides)
- [x] Team notified (training sessions scheduled)

## References

- [Podman Documentation](https://docs.podman.io/)
- [Podman vs Docker](https://docs.podman.io/en/latest/Introduction.html)
- [podman-compose Documentation](https://github.com/containers/podman-compose)
- [Rootless Containers](https://rootlesscontaine.rs/)
- [Deployment Architecture](deployment-architecture.md)
- [Podman Isolation Architecture](podman-isolation-architecture.md)

## Notes

### Key Differences from Docker

1. **No Daemon**: Podman doesn't use a daemon, each container is a child process
2. **Rootless**: Containers run as regular user by default
3. **Pods**: Native support for Kubernetes-style pods
4. **Project Isolation**: Better isolation via project names and labels

### Podman Machine (macOS)

On macOS, Podman runs containers in a lightweight VM (podman machine):
- Configured with: 4 CPUs, 8GB RAM, 50GB disk
- Managed via: `podman machine start/stop/restart`
- Connection: Automatic via `PODMAN_CONNECTION` environment variable

### Project Isolation

**Critical**: Always use project name for isolation:
```bash
export COMPOSE_PROJECT_NAME="janusgraph-demo"
podman-compose -p $COMPOSE_PROJECT_NAME -f docker-compose.full.yml up -d
```

This ensures:
- Containers: `janusgraph-demo_<service>_1`
- Networks: `janusgraph-demo_<network>`
- Volumes: `janusgraph-demo_<volume>`

### Troubleshooting

**Common Issues:**

1. **Podman machine not running**:
   ```bash
   podman machine start
   ```

2. **Connection errors**:
   ```bash
   podman machine list
   podman system connection list
   ```

3. **Port conflicts**:
   ```bash
   podman ps -a
   lsof -i :<port>
   ```

### Future Considerations

- **Kubernetes Migration**: Pod support makes K8s migration easier
- **Multi-Architecture**: Better support for ARM/x86 cross-platform builds
- **Security Hardening**: Explore SELinux/AppArmor integration
- **Performance Tuning**: Optimize podman machine resources

---

**Last Updated**: 2026-02-19  
**Next Review**: 2026-05-19 (3 months)  
**Owner**: Platform Engineering Team