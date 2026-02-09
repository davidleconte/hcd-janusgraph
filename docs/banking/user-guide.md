# Banking Platform User Guide

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
**Contact:**

## Getting Started

### Prerequisites

```bash
conda activate janusgraph-analysis
```

### Generate Test Data

```python
from banking.data_generators.orchestration import MasterOrchestrator, GenerationConfig

config = GenerationConfig(
    seed=42,
    person_count=100,
    company_count=50,
    account_count=200
)

orchestrator = MasterOrchestrator(config)
data = orchestrator.generate_all()
```

### Run Notebooks

1. Start services: `cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh`
2. Open Jupyter: `jupyter notebook banking/notebooks/`
3. Run notebooks in order (01-11)

## Demos Available

| Notebook | Purpose |
|----------|---------|
| 01_Sanctions_Screening | Entity screening against sanctions lists |
| 02_AML_Structuring | Structuring pattern detection |
| 03_Fraud_Detection | Transaction fraud analysis |
| 04_Customer_360 | Complete customer view |
| 05_Advanced_Analytics | OLAP-style analytics |
| 06_TBML_Detection | Trade-based money laundering |
| 07_Insider_Trading | Trading pattern analysis |
| 08_UBO_Discovery | Beneficial owner discovery |
| 09_API_Integration | REST API usage |
| 10_Integrated_Architecture | Full system demo |
| 11_Streaming_Pipeline | Pulsar streaming demo |

## API Usage

```python
import requests

# Query customer
response = requests.get("http://localhost:8000/api/v1/customers/12345")
customer = response.json()
```
