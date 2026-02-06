# Quick Start Guide

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)  
**Contact:** +33614126117

## Prerequisites

- Python 3.11+
- Podman or Docker
- Conda (recommended)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/davidleconte/hcd-janusgraph.git
cd hcd-janusgraph
```

### 2. Set Up Conda Environment

```bash
conda create -n janusgraph-analysis python=3.11
conda activate janusgraph-analysis
conda env config vars set JANUSGRAPH_PORT=18182 JANUSGRAPH_USE_SSL=false
conda deactivate && conda activate janusgraph-analysis
```

### 3. Install Dependencies

```bash
uv pip install -e ".[dev,streaming]"
```

### 4. Deploy Services

```bash
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh
```

### 5. Verify Installation

```bash
# Check services
curl http://localhost:18182?gremlin=g.V().count()

# Run tests
pytest tests/unit/ -v
```

## Next Steps

- [Configuration Guide](configuration.md)
- [Architecture Overview](../architecture/overview.md)
- [Banking Platform Guide](../banking/overview.md)
