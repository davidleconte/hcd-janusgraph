# Audit Logging

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)  
**Contact:** +33614126117

## Overview

Comprehensive audit logging with 30+ event types for compliance.

## Event Categories

| Category | Events | Description |
|----------|--------|-------------|
| Authentication | 4 | login, logout, failed_auth, MFA |
| Authorization | 2 | access_granted, access_denied |
| Data Access | 4 | query, create, update, delete |
| GDPR | 3 | access_request, deletion_request, portability |
| AML | 2 | SAR_filing, CTR_reporting |
| Security | 2 | incident, violation |

## Usage

```python
from banking.compliance.audit_logger import get_audit_logger

audit_logger = get_audit_logger()

# Log data access
audit_logger.log_data_access(
    user="analyst@example.com",
    resource="customer:12345",
    action="query",
    result="success",
    metadata={"query": "g.V().has('customerId', '12345')"}
)
```

## Log Storage

- **Format:** JSON structured logs
- **Location:** `/var/log/audit/`
- **Retention:** 7 years (configurable)

## Compliance Reports

```python
from banking.compliance.compliance_reporter import generate_compliance_report

report = generate_compliance_report(
    report_type="gdpr",
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 1, 31)
)
```
