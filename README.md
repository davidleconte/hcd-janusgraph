# HCD + JanusGraph Containerized Stack

**File**: README.md  
**Created**: 2026-01-28T10:36:00.123  
**Author**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117

---

## Overview

Production-ready containerized stack combining **HyperConverged Database (HCD) 1.2.3** with **JanusGraph** for scalable graph database operations. Fully integrated with Jupyter Lab, monitoring (Prometheus/Grafana), and visualization tools.

### Key Features

✅ **Production-Ready**: Health checks, resource limits, graceful shutdown  
✅ **Automated CI/CD**: GitHub Actions workflows for testing and deployment  
✅ **Comprehensive Monitoring**: Prometheus + Grafana + custom alerts  
✅ **Backup & Restore**: Automated backup scripts with S3 integration  
✅ **Security**: CodeQL scanning, secret detection, Trivy image scanning  
✅ **Multi-Environment**: Separate configs for dev/staging/prod  
✅ **Documentation**: Complete guides for setup, testing, and operations  

---

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/davidleconte/hcd-janusgraph.git
cd hcd-janusgraph

# 2. Copy environment template
cp .env.example .env

# 3. Deploy stack
make deploy

# 4. Verify installation
make test

# 5. Access Jupyter
open http://localhost:8888
```

📚 **See [QUICKSTART.md](QUICKSTART.md) for detailed commands and troubleshooting**

---

## Project Structure

```
hcd-tarball-janusgraph/
├── .github/              # CI/CD workflows, issue/PR templates
├── config/               # All configuration files
│   ├── compose/          # Docker compose files
│   ├── environments/     # Multi-environment configs
│   ├── janusgraph/       # JanusGraph configuration
│   └── monitoring/       # Prometheus/Grafana configs
├── docker/               # Dockerfiles for all services
├── scripts/              # Automation scripts
│   ├── deployment/       # Deploy/stop scripts
│   ├── backup/           # Backup/restore scripts
│   ├── monitoring/       # Monitoring setup
│   ├── testing/          # Test scripts
│   └── maintenance/      # Maintenance tasks
├── src/                  # Source code
│   ├── python/           # Python modules
│   └── groovy/           # Groovy scripts
├── tests/                # Test suites
│   ├── integration/      # Integration tests
│   ├── unit/             # Unit tests
│   └── fixtures/         # Test fixtures
├── docs/                 # Documentation
├── notebooks/            # Jupyter notebooks
└── data/                 # Data files
```

Total: **8 directories + 11 core files** (vs 43 files at root before restructuring!)

---

## Core Components

### Services

| Service | Description | Port |
|---------|-------------|------|
| **HCD** | Cassandra-based distributed database | 19042 |
| **JanusGraph** | Graph database | 18182 |
| **Jupyter Lab** | Interactive notebooks | 8888 |
| **Prometheus** | Metrics collection | 9090 |
| **Grafana** | Monitoring dashboards | 3001 |
| **Visualizer** | Graph visualization | 3000 |
| **Graphexp** | Graph explorer | 8080 |

### Sample Data

Pre-loaded graph includes:
- **5 people** (Alice, Bob, Carol, David, Eve)
- **3 companies** (DataStax, Acme Corp, TechStart)
- **3 products** (JanusGraph, Cloud Service Platform, Analytics Engine)
- **19 relationships** (knows, worksFor, created, uses)

---

## Documentation

| Document | Description |
|----------|-------------|
| **[QUICKSTART.md](QUICKSTART.md)** | Essential commands, URLs, troubleshooting |
| **[docs/SETUP.md](docs/SETUP.md)** | Detailed setup instructions |
| **[docs/TESTING.md](docs/TESTING.md)** | Testing guide |
| **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | System architecture |
| **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** | Deployment procedures |
| **[docs/BACKUP.md](docs/BACKUP.md)** | Backup/restore guide |
| **[docs/MONITORING.md](docs/MONITORING.md)** | Monitoring setup |
| **[docs/SECURITY.md](docs/SECURITY.md)** | Security guidelines |
| **[docs/CHANGELOG.md](docs/CHANGELOG.md)** | Version history |

---

## Requirements

- **Podman** 4.9+ (or Docker with Compose plugin)
- **Python** 3.11+
- **Git**
- **8GB+ RAM** recommended
- **20GB+ disk space**

---

## CI/CD

### GitHub Actions Workflows

- **CI** (`ci.yml`): Lint, test, build, integration tests, security scan
- **Security** (`security.yml`): CodeQL, secret scan, dependency check, image scan
- **Deploy Dev** (`deploy-dev.yml`): Auto-deploy to development
- **Deploy Prod** (`deploy-prod.yml`): Manual production deployment with approval

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

---

## Security

Report security vulnerabilities to: [david.leconte1@ibm.com](mailto:david.leconte1@ibm.com)

See [SECURITY.md](SECURITY.md) for our security policy.

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## Acknowledgments

- **HCD (HyperConverged Database)** by DataStax
- **JanusGraph** - Open-source graph database
- **Apache TinkerPop** - Graph computing framework

---

## Support

- **Issues**: [GitHub Issues](https://github.com/davidleconte/hcd-janusgraph/issues)
- **Discussions**: [GitHub Discussions](https://github.com/davidleconte/hcd-janusgraph/discussions)
- **Email**: david.leconte1@ibm.com

---

**Version**: 1.0.0  
**Status**: ✅ Production-ready  
**Last Updated**: 2026-01-28

---

**Signature**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
