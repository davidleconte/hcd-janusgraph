# Exploratory Notebooks

General-purpose Jupyter notebooks for JanusGraph exploration and experimentation.

## Contents

| Notebook | Description |
|----------|-------------|
| `01_quickstart.ipynb` | Quick start guide for JanusGraph |
| `02_janusgraph_complete_guide.ipynb` | Comprehensive JanusGraph guide |
| `03_advanced_queries.ipynb` | Advanced Gremlin query examples |
| `04_AML_Structuring_Analysis.ipynb` | AML pattern analysis |

## Purpose

These notebooks are for:

- Learning JanusGraph basics
- Prototyping queries
- Data exploration
- General experimentation

For banking-specific use cases, see `banking/notebooks/`.

## Usage

```bash
# Activate conda environment first
conda activate janusgraph-analysis

# Start Jupyter Lab
cd config/compose
podman-compose -p janusgraph-demo up jupyter

# Access at http://localhost:8888
```

## Requirements

- Conda environment: `janusgraph-analysis` with Python 3.11
- Running JanusGraph service (via podman-compose)

---

**Co-Authored-By:** David Leconte <team@example.com>
