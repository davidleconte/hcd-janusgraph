# Banking Use Cases: Implementation Status & Remediation Plan

**Date:** January 28, 2026
**Author:** Gemini CLI Agent
**Context:** Assessment of "Complex Banking Use Cases Solved by IBM HCD + JanusGraph + OpenSearch (JVector)" implementation.

## 1. Executive Summary

The project aims to implement four complex banking use cases leveraging a hybrid graph + vector architecture. 
**Current Status:** The infrastructure (HCD, JanusGraph, OpenSearch, Logging, Security) is well-progressed (Phase 1 Security complete, Phase 2 Infrastructure in progress). However, the **functional implementation** of the banking use cases is significantly lagging. Only the **Anti-Money Laundering (AML)** use case is partially implemented (schema and basic structuring queries), while the other three use cases are virtually non-existent in the codebase. Critical "Vector Search" and "Semantic Matching" capabilities described in the functional memorandum are currently missing from the implementation.

## 2. Implementation Status Matrix

| Use Case | Component | Status | Notes |
| :--- | :--- | :--- | :--- |
| **1. AML** | Schema | 🟡 Partial | `aml_schema.groovy` exists but vector indices are commented out. |
| | Data Gen | 🟡 Partial | `generate_structuring_data.py` exists (basic structuring only). |
| | Queries | 🟡 Partial | `structuring_detection.groovy` covers 10 basic patterns. |
| | Vector AI | 🔴 Missing | No embedding generation, no vector search integration. |
| | Notebooks | 🟡 Partial | `04_AML_Structuring_Analysis.ipynb` exists. |
| **2. Fraud Rings** | Schema | 🔴 Missing | No schema definition found. |
| | Data Gen | 🔴 Missing | No data generator. |
| | Queries | 🔴 Missing | No logic implemented. |
| | Vector AI | 🔴 Missing | |
| **3. Customer 360** | Schema | 🔴 Missing | |
| | Data Gen | 🔴 Missing | |
| | Queries | 🔴 Missing | |
| | Vector AI | 🔴 Missing | |
| **4. Trade Surv.** | Schema | 🔴 Missing | |
| | Data Gen | 🔴 Missing | |
| | Queries | 🔴 Missing | |
| | Vector AI | 🔴 Missing | |

## 3. Detailed Gap Analysis

### 3.1. Missing Functional Schemas
Use Cases 2, 3, and 4 lack any schema definitions. The existing `aml_schema.groovy` is focused solely on the "structuring" pattern and does not cover the broader entities described (e.g., "Trade", "Communication", "Device", "Login").

### 3.2. Vector Search & AI Gap (Critical)
The functional memorandum heavily emphasizes "Semantic Entity Matching", "Vector Embeddings", and "JVector".
- **Codebase:** `aml_schema.groovy` has commented out mixed index configuration (`// mgmt.buildIndex...`).
- **Dependencies:** `docker/jupyter/environment.yml` and `banking/requirements.txt` lack essential ML libraries (e.g., `sentence-transformers`, `torch`, `transformers`) required to generate embeddings for names, addresses, or communications.
- **Integration:** No code exists to generate vectors from text and insert them into the graph/OpenSearch.

### 3.3. Data Generation
Current data generation (`generate_structuring_data.py`) is narrow. It only creates `Person`, `Account`, `Transaction` for one specific AML typology. It needs to be expanded to support:
- **Fraud:** Devices, IP addresses, Login events.
- **Customer 360:** Web clicks, Support tickets, Product holdings.
- **Trade:** Orders, Executions, Emails/Chats.

## 4. Remediation & Finalization Plan

This plan runs in parallel with the ongoing Infrastructure Phase 2.

### Phase A: Foundation (AI & Vector Setup) - Week 1
1.  **Update Environment**: Add `sentence-transformers`, `scikit-learn` to `environment.yml` and `requirements.txt`.
2.  **Enable OpenSearch in Schema**: Modify `aml_schema.groovy` to correctly configure the mixed index backed by OpenSearch (JVector).
3.  **Create Vector Utility**: Develop `src/python/utils/embedding_generator.py` to generate embeddings for text (names, descriptions).

### Phase B: Complete AML Use Case - Week 1
1.  **Enhance AML Schema**: Add vector properties (e.g., `name_embedding`, `address_embedding`) to the schema.
2.  **Update Data Gen**: Modify `generate_structuring_data.py` to generate synthetic text data and their embeddings.
3.  **Implement Vector Queries**: Add a notebook demonstrating "Fuzzy Name Matching" using vector search + Gremlin traversal.

### Phase C: Implement Fraud Rings - Week 2
1.  **Design Schema**: Create `fraud_schema.groovy` (Device, IP, Login, Card).
2.  **Data Generator**: Create `generate_fraud_data.py` (Bust-out patterns, shared device rings).
3.  **Queries**: Write Gremlin traversals for "Shared Device" and "Loop Detection".
4.  **Vector Integration**: Vectorize "Behavioral Profiles" (e.g., transaction sequence embeddings) for anomaly detection.

### Phase D: Implement Customer 360 - Week 2
1.  **Design Schema**: Create `customer360_schema.groovy` (Interaction, Ticket, Product).
2.  **Data Generator**: Create `generate_customer_data.py` including unstructured text (support tickets).
3.  **Vector Integration**: Embed support ticket text for "Semantic Search" (e.g., finding similar complaints).
4.  **Queries**: Recommendation engine using "Graph + Vector" (Similar users who bought X).

### Phase E: Implement Trade Surveillance - Week 3
1.  **Design Schema**: Create `trade_schema.groovy` (Trader, Order, Instrument, Communication).
2.  **Data Generator**: Create `generate_trade_data.py` simulating insider trading scenarios (Front-running).
3.  **Vector Integration**: Embed "Communications" (Emails/Chats) to detect semantic collusion.
4.  **Queries**: Complex temporal traversals (Trade follows Communication).

### Phase F: Unified Demo & Documentation - Week 3
1.  **Master Notebook**: Create `05_Unified_Banking_Demo.ipynb` showcasing all 4 use cases.
2.  **Dashboard**: (Optional) Simple Streamlit or Dash app to visualize the graphs and alerts.
3.  **Final Documentation**: Update `banking/docs/` with details of all implemented patterns.

## 5. Immediate Action Items (Next 48 Hours)

1.  **Install ML Dependencies**: Update `requirements.txt` and rebuild/update the environment.
2.  **Fix AML Schema**: Uncomment and fix the mixed index configuration in `aml_schema.groovy`.
3.  **Prototype Embeddings**: Write a simple Python script to prove vector generation and insertion into JanusGraph.

---
**Plan Owner:** Gemini CLI Agent
**Approved By:** User
