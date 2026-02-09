# Comprehensive Project Audit & Remediation Plan: HCD + JanusGraph + OpenSearch

**Date:** January 28, 2026
**Auditor:** Gemini CLI Agent
**Scope:** Full Project Analysis (Architecture, Code, Functional, Security)

---

## 1. Executive Summary

The `hcd-tarball-janusgraph` project is a sophisticated hybrid data platform designed to solve complex banking problems using Graph (JanusGraph), NoSQL (HCD/Cassandra), and Vector Search (OpenSearch).

**Current State Assessment:**

- **Infrastructure:** 🟡 **Partially Ready**. Core containers work, and Phase 1 security (Secrets/Auth) is complete. However, a **critical configuration mismatch** prevents the "Vector Search" capabilities from working.
- **Functional Implementation:** 🔴 **Critical Gaps**. Only 1 of 4 banking use cases (AML) is partially implemented. The advanced AI/Vector features described in the functional memorandum are **non-existent** in the code.
- **Code Quality:** 🟢 **Good**. Existing Python and Shell scripts are well-written, robust, and follow best practices. Unit tests for the client are excellent.
- **Deployment:** 🟡 **Brittle**. The deployment relies on a shell script (`deploy_full_stack.sh`) that manually runs containers, bypassing the source-of-truth `docker-compose.yml` files and hardcoding incorrect configurations.

**Top Priority:** Fix the JanusGraph<->OpenSearch wiring to enable vector search, then systematically implement the missing banking use cases.

---

## 2. Detailed Audit Findings

### 2.1. Architecture & Configuration (Critical)

| Finding | Severity | Description |
| :--- | :--- | :--- |
| **Index Backend Mismatch** | 🔴 **P0** | `deploy_full_stack.sh` explicitly sets `-e index.search.backend=lucene`. This forces JanusGraph to use a local, limited text index instead of the deployed OpenSearch cluster. **Vector search is impossible in this state.** |
| **Orchestration Drift** | 🟠 **P1** | The project contains rich `docker-compose.yml` files in `config/compose/`, but the primary deployment script (`scripts/deployment/deploy_full_stack.sh`) ignores them and runs `podman run` commands manually. This leads to configuration drift (e.g., the compose file has OpenSearch, but the script might misconfigure it). |
| **TLS/SSL Incomplete** | 🟠 **P1** | While certificate generation scripts exist (Phase 2, Week 2), `docker-compose.banking.yml` still has `TODO: Configure TLS/SSL` comments. |

### 2.2. Functional Use Cases (Banking)

| Use Case | Status | Gap Analysis |
| :--- | :--- | :--- |
| **1. AML** | 🟡 Partial | Schema exists for basic entities. **Missing:** Vector embeddings for "Fuzzy Name Matching" and "Entity Resolution". Mixed indices are commented out in `aml_schema.groovy`. |
| **2. Fraud Rings** | 🔴 Missing | No schema, data generator, or queries found. |
| **3. Customer 360** | 🔴 Missing | No schema, data generator, or queries found. |
| **4. Trade Surveillance** | 🔴 Missing | No schema, data generator, or queries found. |

### 2.3. Code Quality & Testing

| Area | Rating | Notes |
| :--- | :--- | :--- |
| **Python Client** | 🟢 Excellent | `test_janusgraph_client_enhanced.py` provides high-quality coverage with mocking. |
| **Scripts** | 🟢 Good | `deploy_full_stack.sh` includes robust health checks and error handling, though the *approach* (manual `podman run`) is debatable. |
| **Groovy** | 🟡 Fair | `aml_schema.groovy` is clean but incomplete. Lacks error handling if schema creation fails halfway. |
| **Integration Tests** | 🔴 Missing | No end-to-end tests exist to verify that data flows from HCD -> JanusGraph -> OpenSearch -> Query. |

---

## 3. Comprehensive Remediation Plan

This plan integrates Infrastructure fixes (Phase 2) with Functional implementation (Banking Use Cases).

### Phase 1: Core Infrastructure Repair (Week 1)

**Goal:** Enable Vector Search and unify deployment.

1. **Fix Deployment Script:** Refactor `deploy_full_stack.sh` to use `podman-compose` (or `docker-compose`) consuming the files in `config/compose/`. Stop manual `podman run` commands to ensure the Compose file is the single source of truth.
2. **Configure OpenSearch Backend:**
    - Update `config/janusgraph/janusgraph-hcd.properties` (or the compose environment override) to set:

        ```properties
        index.search.backend=elasticsearch
        index.search.hostname=opensearch
        index.search.elasticsearch.interface=REST_CLIENT
        ```

    - Ensure the `opensearch` container is actually reachable by `janusgraph-server` (shared network).
3. **Verify Vector Capability:** Create a "Smoke Test" script (`tests/integration/test_vector_search.py`) that:
    - Creates a schema with a vector property.
    - Inserts a node with a vector.
    - Performs a k-NN search via Gremlin.

### Phase 2: Functional Implementation - Wave 1 (Week 2)

**Goal:** Complete AML and Fraud Use Cases.

1. **AML Upgrade:**
    - Update `aml_schema.groovy`: Uncomment mixed index, add `vector` property for `person_name_embedding`.
    - Update `generate_structuring_data.py`: Use `sentence-transformers` to generate embeddings for names.
2. **Fraud Implementation:**
    - Create `banking/schema/graph/fraud_schema.groovy`: Entities: `Device`, `IP`, `Login`, `Card`.
    - Create `banking/data/fraud/generate_fraud_rings.py`: Generate "bust-out" patterns.
    - Create `banking/queries/fraud_detection.groovy`: Queries for shared device rings.

### Phase 3: Functional Implementation - Wave 2 (Week 3)

**Goal:** Customer 360 and Trade Surveillance.

1. **Customer 360:**
    - Schema: `Interaction` nodes with text content.
    - Vector: Embed support ticket text for semantic search.
2. **Trade Surveillance:**
    - Schema: `Trader`, `Communication`, `Trade`.
    - Vector: Embed "dummy emails" to detect "insider trading" language.

### Phase 4: Final Polish & Documentation (Week 4)

1. **Unified Demo:** Create a master Jupyter Notebook (`05_Unified_Banking_Demo.ipynb`) that walks through all 4 use cases live.
2. **Documentation:** Update `README.md` and `docs/` to reflect the functional capabilities.
3. **Final Security Sweep:** Complete the TLS/SSL configuration (P1-001) for the now-working OpenSearch and JanusGraph endpoints.

---

## 4. Immediate Next Steps

1. **Approve Plan:** Confirm this roadmap.
2. **Execute Phase 1:** I will start by refactoring the deployment to fix the OpenSearch configuration mismatch.

---
**Report Generated By:** Gemini CLI Agent
