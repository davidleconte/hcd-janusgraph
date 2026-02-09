# GDPR Compliance

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)  
**Contact:** 

## Overview

Full GDPR compliance with data subject rights support.

## Supported Rights

| Right | Article | Implementation |
|-------|---------|----------------|
| Access | Art. 15 | Data export API |
| Rectification | Art. 16 | Update endpoints |
| Erasure | Art. 17 | Deletion workflows |
| Portability | Art. 20 | JSON/CSV export |
| Objection | Art. 21 | Processing flags |

## Data Subject Requests

```python
from banking.compliance import GDPRHandler

handler = GDPRHandler()

# Access request
data = handler.process_access_request(subject_id="12345")

# Deletion request
result = handler.process_deletion_request(subject_id="12345")
```

## Records of Processing

Article 30 compliant processing records maintained automatically.

## Data Retention

| Data Type | Retention | Legal Basis |
|-----------|-----------|-------------|
| Transaction | 7 years | Legal requirement |
| Customer PII | Contract duration + 3 years | Contract |
| Audit Logs | 7 years | Legal requirement |
