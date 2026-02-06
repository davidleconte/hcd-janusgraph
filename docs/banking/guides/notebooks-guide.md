# Banking Notebooks Guide

**Date:** 2026-02-04  
**Version:** 2.0  
**Status:** Active

---

## Overview

This guide covers the 10 Jupyter notebooks in `banking/notebooks/` that demonstrate the banking compliance platform's capabilities. Several notebooks now feature **cross-service integration**, demonstrating how JanusGraph, OpenSearch, and HCD work together for comprehensive compliance workflows.

## Prerequisites

### 1. Conda Environment

All notebooks require the `janusgraph-analysis` conda environment:

```bash
conda activate janusgraph-analysis
```

### 2. Jupyter Kernel

The ipykernel is registered with the correct environment:

```bash
# Already done - kernel registered as "JanusGraph Analysis (Python 3.11)"
# To re-register if needed:
python -m ipykernel install --user --name janusgraph-analysis --display-name "JanusGraph Analysis (Python 3.11)"
```

### 3. Services Running

Most notebooks require JanusGraph (port 18182) and some require OpenSearch (port 9200):

```bash
# Deploy services
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
```

### 4. Environment Variables (Pre-configured in Conda)

The `janusgraph-analysis` conda environment has these variables pre-configured:

| Variable | Value | Purpose |
|----------|-------|---------|
| `JANUSGRAPH_PORT` | `18182` | Gremlin server port (podman mapped) |
| `JANUSGRAPH_USE_SSL` | `false` | Disable SSL for local development |

Verify after activation:
```bash
conda activate janusgraph-analysis
echo $JANUSGRAPH_PORT      # 18182
echo $JANUSGRAPH_USE_SSL   # false
```

---

## Notebook Configuration

All notebooks use the centralized `notebook_config.py` module for:

- **Path management**: Automatic project root detection
- **Service configuration**: JanusGraph, OpenSearch, HCD connection settings
- **Environment verification**: Conda env check
- **Client creation**: `get_gremlin_client()`, `get_opensearch_client()`

### Standard Initialization

```python
from notebook_config import (
    init_notebook,
    JANUSGRAPH_CONFIG,
    OPENSEARCH_CONFIG,
    get_gremlin_client,
    get_data_path
)

config = init_notebook(check_env=True, check_services=True)
PROJECT_ROOT = config['project_root']
```

---

## Notebooks

| # | Notebook | Use Case | Services Required | Cross-Service Integration |
|---|----------|----------|-------------------|---------------------------|
| 01 | Sanctions_Screening_Demo | Fuzzy name matching with vector embeddings | OpenSearch | ✅ JanusGraph network tracing |
| 02 | AML_Structuring_Detection_Demo | Detect transaction structuring patterns | JanusGraph | - |
| 03 | Fraud_Detection_Demo | Identify fraudulent transaction patterns | JanusGraph | - |
| 04 | Customer_360_View_Demo | Unified customer profile view | JanusGraph | ✅ HCD audit logging |
| 05 | Advanced_Analytics_OLAP | OLAP-style analytics on graph data | JanusGraph | - |
| 06 | TBML_Detection_Demo | Trade-based money laundering detection | JanusGraph | - |
| 07 | Insider_Trading_Detection_Demo | Coordinated trading pattern detection | JanusGraph | ✅ OpenSearch MNPI search |
| 08 | UBO_Discovery_Demo | Ultimate beneficial owner identification | JanusGraph | ✅ OpenSearch fuzzy matching |
| 09 | API_Integration_Demo | FastAPI analytics service integration | FastAPI | - |
| 10 | Integrated_Architecture_Demo | Multi-service architecture demonstration | All Services | ✅ Full integration demo |

### Detailed Descriptions

#### 01: Sanctions Screening Demo
- **Objective**: Real-time sanctions screening with fuzzy name matching
- **Techniques**: Vector embeddings, k-NN similarity search
- **Business Value**: OFAC, EU, UN sanctions compliance
- **Cross-Service**: JanusGraph network tracing for flagged entities (trace 2-hop relationships)

#### 02: AML Structuring Detection Demo  
- **Objective**: Detect structuring (smurfing) patterns
- **Techniques**: Temporal pattern analysis, amount clustering
- **Business Value**: BSA compliance, CTR avoidance detection

#### 03: Fraud Detection Demo
- **Objective**: Identify fraudulent transaction patterns
- **Techniques**: Graph traversal, anomaly detection
- **Business Value**: Reduce fraud losses

#### 04: Customer 360 View Demo
- **Objective**: Unified view of customer relationships
- **Techniques**: Multi-hop graph traversal
- **Business Value**: KYC enhancement, relationship intelligence
- **Cross-Service**: HCD compliance audit logging for profile access (GDPR)

#### 05: Advanced Analytics OLAP Demo
- **Objective**: OLAP-style analytics on graph data
- **Techniques**: Aggregations, grouping, statistical analysis
- **Business Value**: Business intelligence, reporting

#### 06: TBML Detection Demo
- **Objective**: Trade-based money laundering detection
- **Techniques**: Circular trading loops, price deviation analysis
- **Business Value**: Carousel fraud detection, shell company identification

#### 07: Insider Trading Detection Demo
- **Objective**: Detect coordinated trading patterns
- **Techniques**: Timing correlation, communication network analysis
- **Business Value**: SEC compliance, market manipulation detection
- **Cross-Service**: OpenSearch MNPI keyword search in communications

#### 08: UBO Discovery Demo
- **Objective**: Ultimate beneficial owner identification
- **Techniques**: Ownership chain traversal, effective ownership calculation
- **Business Value**: EU 5AMLD compliance, FATF recommendations
- **Cross-Service**: OpenSearch fuzzy company name matching for entity resolution
- **⚠️ Note**: Requires manual execution or longer timeout (>300s) for automated testing due to complex graph traversals. Run interactively for best experience.

#### 09: API Integration Demo
- **Objective**: Demonstrate FastAPI analytics service integration
- **Techniques**: REST API calls, batch processing
- **Business Value**: Production-ready API integration patterns

#### 10: Integrated Architecture Demo
- **Objective**: Demonstrate multi-service architecture synergies
- **Techniques**: Service latency benchmarking, cross-service AML investigation workflow
- **Business Value**: End-to-end compliance workflow demonstration
- **Cross-Service**: Full integration of JanusGraph + OpenSearch + HCD with architecture diagrams

---

## Running Notebooks

### Option 1: Jupyter Notebook

```bash
conda activate janusgraph-analysis
jupyter notebook banking/notebooks/
```

### Option 2: JupyterLab

```bash
conda activate janusgraph-analysis
jupyter lab banking/notebooks/
```

### Option 3: VS Code

1. Open the notebook in VS Code
2. Select kernel: "JanusGraph Analysis (Python 3.11)"
3. Run cells

---

## Testing

### Validation Tests

44 automated tests validate notebook structure and configuration:

```bash
pytest tests/test_notebooks.py -v
```

Tests verify:
- ✅ Valid JSON structure
- ✅ Correct kernel specification
- ✅ notebook_config usage
- ✅ Markdown headers present

### Syntax Validation

All notebooks have been validated for Python syntax errors.

---

## Troubleshooting

### "Module not found" Error

Ensure conda environment is activated:
```bash
conda activate janusgraph-analysis
```

### JanusGraph Connection Failed

1. Check services are running: `podman ps`
2. Verify port mapping: `curl http://localhost:18182`
3. Check `JANUSGRAPH_CONFIG` in notebook_config.py

### Wrong Kernel

Select "JanusGraph Analysis (Python 3.11)" from kernel dropdown.

---

## Related Documentation

- [Banking User Guide](user-guide.md)
- [API Documentation](../../api/README.md)
- [Deployment Guide](../../operations/operations-runbook.md)

---

*Last Updated: 2026-02-04* (Added NB10, cross-service integration documentation)
