# ADR-002: HCD as Storage Backend

**Status:** Accepted
**Date:** 2025-01-15

## Context

JanusGraph requires a storage backend for persistence.

## Decision

Use IBM HCD (Hyper-Converged Database) as the storage backend.

## Consequences

- Enterprise-grade storage with IBM support
- Cassandra-compatible API
- Built-in replication and fault tolerance
