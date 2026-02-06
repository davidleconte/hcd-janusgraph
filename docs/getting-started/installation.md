# Installation Guide

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)  
**Contact:** +33614126117

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Disk | 50 GB | 100 GB |
| Python | 3.10 | 3.11 |

## Dependencies

### Core Dependencies

- `gremlinpython` < 3.8.0 (server compatibility)
- `opensearch-py`
- `cassandra-driver`
- `pydantic`

### Optional Dependencies

- `pulsar-client` (streaming)
- `prometheus-client` (monitoring)

## Installation Methods

### Method 1: pip/uv (Recommended)

```bash
# Using uv (faster)
uv pip install -e ".[dev,streaming]"

# Using pip
pip install -e ".[dev,streaming]"
```

### Method 2: From requirements

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Troubleshooting

### gremlinpython version error

If you see `.discard()` errors:
```bash
pip install "gremlinpython<3.8.0"
```

### Conda environment issues

```bash
conda deactivate
conda activate janusgraph-analysis
```
