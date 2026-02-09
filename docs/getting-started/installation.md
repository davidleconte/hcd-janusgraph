# Installation Guide

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)  
**Contact:** 

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

### Method 1: Conda (Recommended)

```bash
# Create environment from file
conda env create -f environment.yml

# Activate
conda activate janusgraph-analysis
```

### Method 2: pip/uv

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Using uv (faster)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt

# For development (includes testing tools)
pip install -e ".[dev]"
```

### Method 3: From pyproject.toml (all extras)

```bash
pip install -e ".[dev,streaming,security,ml]"
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
