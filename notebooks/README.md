# Jupyter Notebooks

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)  
**Contact:** +33614126117

## Overview

This project contains 15 Jupyter notebooks organized into two categories:

## Notebook Directories

### [Banking Notebooks](../banking/notebooks/)
11 comprehensive demos for banking use cases:

| # | Notebook | Description |
|---|----------|-------------|
| 01 | Sanctions Screening | Entity screening against sanctions lists |
| 02 | AML Structuring Detection | Structuring pattern (smurfing) detection |
| 03 | Fraud Detection | Transaction fraud analysis |
| 04 | Customer 360 View | Complete customer relationship view |
| 05 | Advanced Analytics OLAP | OLAP-style analytics on graph data |
| 06 | TBML Detection | Trade-based money laundering |
| 07 | Insider Trading Detection | Trading pattern analysis |
| 08 | UBO Discovery | Ultimate beneficial owner discovery |
| 09 | API Integration | REST API usage examples |
| 10 | Integrated Architecture | Full system demo |
| 11 | Streaming Pipeline | Pulsar streaming demo |

### [Exploratory Notebooks](../notebooks-exploratory/)
4 notebooks for learning and experimentation:

| # | Notebook | Description |
|---|----------|-------------|
| 01 | Quickstart | JanusGraph introduction |
| 02 | Complete Guide | Comprehensive JanusGraph guide |
| 03 | Advanced Queries | Advanced Gremlin patterns |
| 04 | AML Analysis | AML pattern exploration |

## Quick Start

```bash
# Activate environment
conda activate janusgraph-analysis

# Start services
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh

# Launch Jupyter
jupyter lab banking/notebooks/
```

## Requirements

- Conda environment: `janusgraph-analysis`
- Running services: JanusGraph, OpenSearch, Pulsar (via deploy_full_stack.sh)

## Recommended Order

**New Users:**
1. `notebooks-exploratory/01_quickstart.ipynb` - Learn basics
2. `banking/notebooks/01_Sanctions_Screening_Demo.ipynb` - First use case
3. Continue through banking notebooks (01-11)

**Experienced Users:**
- Jump directly to specific use case notebooks
- Use `banking/notebooks/10_Integrated_Architecture_Demo.ipynb` for full overview
