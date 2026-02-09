# REST API Reference

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
**Contact:**

> **Auto-generated docs:** Run `./scripts/docs/generate_api_docs.sh` for full Python API documentation.

## Overview

FastAPI-based REST API for banking platform access.

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

### Customers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/customers` | List customers |
| GET | `/customers/{id}` | Get customer |
| POST | `/customers` | Create customer |
| PUT | `/customers/{id}` | Update customer |

### Accounts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/accounts` | List accounts |
| GET | `/accounts/{id}` | Get account |
| GET | `/accounts/{id}/transactions` | Account transactions |

### Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/transactions` | List transactions |
| POST | `/transactions` | Create transaction |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/customer360/{id}` | Customer 360 view |
| GET | `/analytics/fraud-score/{id}` | Fraud risk score |
| GET | `/analytics/aml-alerts` | AML alerts |

## Authentication

```bash
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/customers
```

## Response Format

```json
{
  "status": "success",
  "data": {...},
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```
