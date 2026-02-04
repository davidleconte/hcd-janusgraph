-- HCD/Cassandra Keyspace Initialization for JanusGraph
-- File: init_production_keyspace.cql
-- Purpose: Create JanusGraph keyspace with production-ready settings
-- Author: David LECONTE - IBM Worldwide
-- Date: 2026-01-29

-- Drop existing keyspace if it exists (CAREFUL: This deletes all data!)
-- Uncomment only if you want to start fresh
-- DROP KEYSPACE IF EXISTS janusgraph;

-- Create keyspace with production settings
-- NOTE: Adjust replication settings based on your cluster topology
CREATE KEYSPACE IF NOT EXISTS janusgraph
WITH replication = {
    'class': 'NetworkTopologyStrategy',
    'datacenter1': 3  -- 3 replicas in datacenter1 (adjust based on your setup)
}
AND durable_writes = true;

-- For single-node development/testing, use SimpleStrategy instead:
-- CREATE KEYSPACE IF NOT EXISTS janusgraph
-- WITH replication = {
--     'class': 'SimpleStrategy',
--     'replication_factor': 1
-- }
-- AND durable_writes = true;

-- Verify keyspace creation
DESCRIBE KEYSPACE janusgraph;

-- Show all keyspaces
DESCRIBE KEYSPACES;

/*
PRODUCTION NOTES:
=================

1. Replication Strategy:
   - NetworkTopologyStrategy: Use for production multi-datacenter deployments
   - SimpleStrategy: Use ONLY for single-node development

2. Replication Factor:
   - Development: 1 replica
   - Staging: 2 replicas
   - Production: 3+ replicas (depending on cluster size)
   - Formula: RF should be <= number of nodes in datacenter

3. Durable Writes:
   - true: Ensures data is written to commit log (REQUIRED for production)
   - false: Skip commit log writes (ONLY for testing, data loss risk)

4. After Keyspace Creation:
   - JanusGraph will automatically create required tables:
     * edgestore
     * edgestore_lock_
     * graphindex
     * graphindex_lock_
     * janusgraph_ids
     * system_properties
     * system_properties_lock_
     * systemlog
     * txlog

5. Verification:
   Run: DESCRIBE TABLES;
   Should show ~8-10 system tables after JanusGraph first start

6. Monitoring:
   - Check replication status: nodetool status
   - Check keyspace info: nodetool describecluster
   - Check disk usage: nodetool tablestats janusgraph

USAGE:
======

Development (single-node):
  cqlsh -f scripts/hcd/init_production_keyspace.cql

Production (with authentication):
  cqlsh -u cassandra -p password -f scripts/hcd/init_production_keyspace.cql

Container:
  podman exec -it janusgraph-demo_hcd-server_1 cqlsh -f /path/to/init_production_keyspace.cql
*/
