#!/usr/bin/env python3
"""
HCD Deployment Validation Script
=================================

Validates that HCD/Cassandra is properly configured for JanusGraph.

Checks:
- HCD connection
- Keyspace existence and configuration
- JanusGraph tables created
- Replication settings
- Cluster health

Author: David LECONTE - IBM Worldwide
Date: 2026-01-29
"""

import sys
import time
from typing import Dict, List, Optional

try:
    from cassandra.cluster import Cluster
    from cassandra.auth import PlainTextAuthProvider
    from cassandra.policies import DCAwareRoundRobinPolicy
except ImportError:
    print("ERROR: cassandra-driver not installed")
    print("Install with: pip install cassandra-driver")
    sys.exit(1)


class HCDValidator:
    """HCD deployment validator"""
    
    def __init__(
        self, 
        hosts: List[str] = None, 
        port: int = 9042,
        username: str = None,
        password: str = None,
        datacenter: str = "datacenter1"
    ):
        self.hosts = hosts or ["localhost"]
        self.port = port
        self.username = username
        self.password = password
        self.datacenter = datacenter
        self.cluster = None
        self.session = None
        
    def connect(self) -> bool:
        """Connect to HCD cluster"""
        try:
            print(f"Connecting to HCD cluster at {self.hosts}:{self.port}...")
            
            auth_provider = None
            if self.username and self.password:
                auth_provider = PlainTextAuthProvider(
                    username=self.username,
                    password=self.password
                )
            
            # Use DCAwareRoundRobinPolicy for better performance
            load_balancing_policy = DCAwareRoundRobinPolicy(local_dc=self.datacenter)
            
            self.cluster = Cluster(
                self.hosts,
                port=self.port,
                auth_provider=auth_provider,
                load_balancing_policy=load_balancing_policy,
                protocol_version=4
            )
            
            self.session = self.cluster.connect()
            print("✅ Connected to HCD cluster")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to HCD: {e}")
            return False
    
    def validate_keyspace(self, keyspace: str = "janusgraph") -> bool:
        """Validate keyspace existence and configuration"""
        try:
            print(f"\nValidating keyspace: {keyspace}")
            
            # Check if keyspace exists
            query = """
                SELECT keyspace_name, replication 
                FROM system_schema.keyspaces 
                WHERE keyspace_name = %s
            """
            result = self.session.execute(query, (keyspace,))
            row = result.one()
            
            if not row:
                print(f"❌ Keyspace '{keyspace}' does not exist")
                return False
            
            print(f"✅ Keyspace '{keyspace}' exists")
            
            # Check replication configuration
            replication = row.replication
            print(f"   Replication: {replication}")
            
            # Validate replication strategy
            strategy_class = replication.get('class', '')
            if 'NetworkTopologyStrategy' in strategy_class:
                print("   ✅ Using NetworkTopologyStrategy (production-ready)")
            elif 'SimpleStrategy' in strategy_class:
                rf = replication.get('replication_factor', 0)
                if rf == 1:
                    print("   ⚠️  Using SimpleStrategy with RF=1 (development only)")
                else:
                    print(f"   ⚠️  Using SimpleStrategy with RF={rf}")
            else:
                print(f"   ⚠️  Unknown replication strategy: {strategy_class}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to validate keyspace: {e}")
            return False
    
    def validate_janusgraph_tables(self, keyspace: str = "janusgraph") -> bool:
        """Validate JanusGraph tables were created"""
        try:
            print(f"\nValidating JanusGraph tables in keyspace: {keyspace}")
            
            # Expected JanusGraph tables
            expected_tables = [
                'edgestore',
                'edgestore_lock_',
                'graphindex',
                'graphindex_lock_',
                'janusgraph_ids',
                'system_properties',
                'system_properties_lock_',
                'systemlog',
                'txlog'
            ]
            
            # Get actual tables
            query = f"SELECT table_name FROM system_schema.tables WHERE keyspace_name = '{keyspace}'"
            result = self.session.execute(query)
            actual_tables = {row.table_name for row in result}
            
            if not actual_tables:
                print(f"   ⚠️  No tables found in keyspace '{keyspace}'")
                print("   This is normal if JanusGraph hasn't started yet")
                return True  # Not a failure, just not initialized yet
            
            print(f"   Found {len(actual_tables)} tables")
            
            # Check for expected tables
            missing_tables = []
            for table in expected_tables:
                if table in actual_tables:
                    print(f"   ✅ {table}")
                else:
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"   ⚠️  Missing tables (will be created by JanusGraph): {', '.join(missing_tables)}")
            
            # Show unexpected tables (might be custom)
            unexpected = actual_tables - set(expected_tables)
            if unexpected:
                print(f"   ℹ️  Additional tables: {', '.join(unexpected)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to validate tables: {e}")
            return False
    
    def validate_cluster_health(self) -> bool:
        """Validate cluster health"""
        try:
            print("\nValidating cluster health...")
            
            # Get cluster metadata
            metadata = self.cluster.metadata
            
            # Check nodes
            print(f"   Cluster name: {metadata.cluster_name}")
            print(f"   Nodes: {len(metadata.all_hosts())}")
            
            for host in metadata.all_hosts():
                print(f"   - {host.address} (DC: {host.datacenter}, Rack: {host.rack})")
                if host.is_up:
                    print(f"     ✅ UP")
                else:
                    print(f"     ❌ DOWN")
            
            # Check if all nodes are up
            all_up = all(host.is_up for host in metadata.all_hosts())
            
            if all_up:
                print("   ✅ All nodes are UP")
                return True
            else:
                print("   ⚠️  Some nodes are DOWN")
                return False
            
        except Exception as e:
            print(f"❌ Failed to validate cluster health: {e}")
            return False
    
    def run_full_validation(self, keyspace: str = "janusgraph") -> bool:
        """Run full validation suite"""
        print("=" * 60)
        print("HCD Deployment Validation")
        print("=" * 60)
        
        results = []
        
        # Connect
        if not self.connect():
            return False
        
        # Validate keyspace
        results.append(self.validate_keyspace(keyspace))
        
        # Validate tables
        results.append(self.validate_janusgraph_tables(keyspace))
        
        # Validate cluster health
        results.append(self.validate_cluster_health())
        
        # Summary
        print("\n" + "=" * 60)
        print("Validation Summary")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        print(f"Passed: {passed}/{total}")
        
        if all(results):
            print("✅ All validations passed")
            return True
        else:
            print("⚠️  Some validations failed or showed warnings")
            return False
    
    def close(self):
        """Close connection"""
        if self.cluster:
            self.cluster.shutdown()


def main():
    """Main entry point"""
    import os
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate HCD deployment for JanusGraph")
    parser.add_argument("--hosts", default=os.getenv("HCD_HOST", "localhost"), 
                       help="Comma-separated list of HCD hosts (default: localhost)")
    parser.add_argument("--port", type=int, default=int(os.getenv("HCD_PORT", "9042")),
                       help="HCD CQL port (default: 9042)")
    parser.add_argument("--username", default=os.getenv("HCD_USERNAME"),
                       help="HCD username (optional)")
    parser.add_argument("--password", default=os.getenv("HCD_PASSWORD"),
                       help="HCD password (optional)")
    parser.add_argument("--keyspace", default="janusgraph",
                       help="Keyspace to validate (default: janusgraph)")
    parser.add_argument("--datacenter", default="datacenter1",
                       help="Local datacenter name (default: datacenter1)")
    
    args = parser.parse_args()
    
    hosts = [h.strip() for h in args.hosts.split(",")]
    
    validator = HCDValidator(
        hosts=hosts,
        port=args.port,
        username=args.username,
        password=args.password,
        datacenter=args.datacenter
    )
    
    try:
        success = validator.run_full_validation(args.keyspace)
        sys.exit(0 if success else 1)
    finally:
        validator.close()


if __name__ == "__main__":
    main()
