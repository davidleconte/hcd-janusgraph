# AML Implementation - Phase 1: Infrastructure Setup

**Date**: 2026-01-28
**Author**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
**Contact**: david.leconte1@ibm.com | +33614126117

## Overview

Phase 1 focuses on setting up OpenSearch 3.4+ with JVector plugin and preparing the infrastructure for AML use case.

## Components

### 1. OpenSearch 3.4+
- Latest stable release
- Single-node setup for development
- Security disabled for easier testing
- Exposed on port 9200

### 2. JVector Plugin
- Installed from Maven Central
- High-dimensional vector search capability
- Supports DiskANN algorithm
- Billion-scale vector indexing

### 3. Banking Schema Extension
- New vertex labels for banking entities
- New edge labels for relationships
- Properties for AML-specific attributes
- Indices for fast traversals

## Implementation Steps

1. Add OpenSearch to docker-compose.full.yml
2. Create initialization script for JVector plugin
3. Define banking schema in Groovy
4. Create Python utilities for vector operations
5. Test OpenSearch + JVector integration

## Next Phase

Phase 2: Structuring/Smurfing Detection
- Synthetic data generator
- Detection queries
- Analysis notebook

---

**Status**: Documentation complete, starting implementation
