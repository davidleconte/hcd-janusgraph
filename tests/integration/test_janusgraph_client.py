#!/usr/bin/env python3
"""
JanusGraph Python Test Client
Demonstrates connecting to JanusGraph and running Gremlin queries
"""

from gremlin_python.driver import client, serializer
from gremlin_python.driver.protocol import GremlinServerError
import sys
import time

import pytest

@pytest.fixture(scope="module")
def jg():
    """Fixture to provide JanusGraphClient instance"""
    client = JanusGraphClient(host='localhost', port=18182)
    if not client.connect():
        pytest.skip("Could not connect to JanusGraph")
    yield client
    client.close()
class JanusGraphClient:
    """Simple client for JanusGraph using Gremlin Python driver"""
    
    def __init__(self, host='localhost', port=18182):
        """
        Initialize JanusGraph client
        
        Args:
            host: JanusGraph server hostname
            port: Gremlin WebSocket port
        """
        self.url = f'ws://{host}:{port}/gremlin'
        self.client = None
        
    def connect(self):
        """Establish connection to JanusGraph"""
        try:
            self.client = client.Client(
                self.url, 
                'g',
                message_serializer=serializer.GraphSONSerializersV3d0()
            )
            print(f"✅ Connected to JanusGraph at {self.url}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to JanusGraph: {e}")
            return False
    
    def execute(self, query):
        """
        Execute Gremlin query
        
        Args:
            query: Gremlin query string
            
        Returns:
            Query results or None on error
        """
        try:
            result = self.client.submit(query).all().result()
            return result
        except GremlinServerError as e:
            print(f"❌ Query error: {e}")
            return None
        except Exception as e:
            print(f"❌ Execution error: {e}")
            return None
    
    def close(self):
        """Close connection"""
        if self.client:
            self.client.close()
            print("🔌 Disconnected from JanusGraph")


def test_basic_queries(jg):
    """Run basic test queries"""
    print("\n" + "="*60)
    print("BASIC QUERIES")
    print("="*60)
    
    # Count vertices
    print("\n1️⃣  Count all vertices:")
    result = jg.execute("g.V().count()")
    print(f"   Total vertices: {result[0] if result else 'N/A'}")
    
    # Count edges
    print("\n2️⃣  Count all edges:")
    result = jg.execute("g.E().count()")
    print(f"   Total edges: {result[0] if result else 'N/A'}")
    
    # Count by vertex label
    print("\n3️⃣  Count vertices by label:")
    labels = ['person', 'company', 'product']
    for label in labels:
        result = jg.execute(f"g.V().hasLabel('{label}').count()")
        count = result[0] if result else 0
        print(f"   {label}: {count}")


def test_person_queries(jg):
    """Run queries for person vertices"""
    print("\n" + "="*60)
    print("PERSON QUERIES")
    print("="*60)
    
    # Get all person names
    print("\n1️⃣  All people:")
    result = jg.execute("g.V().hasLabel('person').values('name')")
    if result:
        for name in result:
            print(f"   - {name}")
    
    # Find person by name
    print("\n2️⃣  Find Alice Johnson:")
    result = jg.execute("g.V().has('person', 'name', 'Alice Johnson').valueMap()")
    if result:
        print(f"   {result[0]}")
    
    # Get people in San Francisco
    print("\n3️⃣  People in San Francisco:")
    result = jg.execute("g.V().hasLabel('person').has('location', 'San Francisco').values('name')")
    if result:
        for name in result:
            print(f"   - {name}")
    
    # People aged 25-30
    print("\n4️⃣  People aged 25-30:")
    result = jg.execute("g.V().hasLabel('person').has('age', gte(25)).has('age', lte(30)).values('name')")
    if result:
        for name in result:
            print(f"   - {name}")


def test_relationship_queries(jg):
    """Run queries exploring relationships"""
    print("\n" + "="*60)
    print("RELATIONSHIP QUERIES")
    print("="*60)
    
    # Alice's friends
    print("\n1️⃣  Who does Alice know?")
    result = jg.execute("g.V().has('person', 'name', 'Alice Johnson').out('knows').values('name')")
    if result:
        for name in result:
            print(f"   - {name}")
    
    # Who works at DataStax
    print("\n2️⃣  Who works at DataStax?")
    result = jg.execute("g.V().has('company', 'name', 'DataStax').in('worksFor').valueMap('name', 'role')")
    if result:
        for person in result:
            name = person.get('name', ['N/A'])[0]
            role = person.get('role', ['N/A'])[0]
            print(f"   - {name} ({role})")
    
    # Products created by companies
    print("\n3️⃣  Products created by each company:")
    result = jg.execute("g.V().hasLabel('company').as('company').out('created').as('product').select('company', 'product').by('name')")
    if result:
        for item in result:
            company = item.get('company', 'N/A')
            product = item.get('product', 'N/A')
            print(f"   {company} → {product}")
    
    # Who uses JanusGraph
    print("\n4️⃣  Who uses JanusGraph?")
    result = jg.execute("g.V().has('product', 'name', 'JanusGraph').in('uses').values('name')")
    if result:
        for name in result:
            print(f"   - {name}")


def test_path_queries(jg):
    """Run path traversal queries"""
    print("\n" + "="*60)
    print("PATH TRAVERSAL QUERIES")
    print("="*60)
    
    # Path from Alice to products through company
    print("\n1️⃣  Alice's path to products (person → company → product):")
    result = jg.execute("""
        g.V().has('person', 'name', 'Alice Johnson')
         .out('worksFor')
         .out('created')
         .path()
         .by('name')
    """)
    if result:
        for path in result:
            print(f"   {' → '.join(path)}")
    
    # Friends of friends
    print("\n2️⃣  Alice's friends of friends (2-hop):")
    result = jg.execute("""
        g.V().has('person', 'name', 'Alice Johnson')
         .out('knows').out('knows')
         .dedup()
         .values('name')
    """)
    if result:
        for name in result:
            print(f"   - {name}")


def test_aggregation_queries(jg):
    """Run aggregation queries"""
    print("\n" + "="*60)
    print("AGGREGATION QUERIES")
    print("="*60)
    
    # Average age
    print("\n1️⃣  Average age of people:")
    result = jg.execute("g.V().hasLabel('person').values('age').mean()")
    if result:
        print(f"   {result[0]:.1f} years")
    
    # Count edges by label
    print("\n2️⃣  Edge counts by type:")
    result = jg.execute("g.E().groupCount().by(label)")
    if result:
        for label, count in result[0].items():
            print(f"   {label}: {count}")
    
    # People grouped by location
    print("\n3️⃣  People by location:")
    result = jg.execute("g.V().hasLabel('person').groupCount().by('location')")
    if result:
        for location, count in result[0].items():
            print(f"   {location}: {count}")


def run_initialization_check(jg):
    """Check if schema and data are initialized"""
    print("\n" + "="*60)
    print("INITIALIZATION CHECK")
    print("="*60)
    
    vertex_count = jg.execute("g.V().count()")
    edge_count = jg.execute("g.E().count()")
    
    v_count = vertex_count[0] if vertex_count else 0
    e_count = edge_count[0] if edge_count else 0
    
    if v_count == 0:
        print("\n⚠️  Graph is empty!")
        print("\nTo initialize schema and load data:")
        print("  1. Copy scripts to container:")
        print("     podman --remote --connection podman-wxd cp init_sample_schema.groovy janusgraph-server:/tmp/")
        print("     podman --remote --connection podman-wxd cp load_sample_data.groovy janusgraph-server:/tmp/")
        print("\n  2. Run schema initialization:")
        print("     podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh -e /tmp/init_sample_schema.groovy")
        print("\n  3. Load sample data:")
        print("     podman --remote --connection podman-wxd exec janusgraph-server ./bin/gremlin.sh -e /tmp/load_sample_data.groovy")
        return False
    else:
        print(f"\n✅ Graph initialized: {v_count} vertices, {e_count} edges")
        return True


def main():
    """Main test function"""
    print("JanusGraph Python Test Client")
    print("="*60)
    
    # Create client
    jg = JanusGraphClient(host='localhost', port=18182)
    
    # Connect
    if not jg.connect():
        print("\n❌ Cannot connect to JanusGraph. Make sure:")
        print("   1. JanusGraph container is running")
        print("   2. Port 18182 is accessible")
        print("   3. Run: podman --remote --connection podman-wxd ps | grep janusgraph")
        sys.exit(1)
    
    # Small delay to ensure connection is stable
    time.sleep(1)
    
    # Check initialization
    initialized = run_initialization_check(jg)
    
    if not initialized:
        jg.close()
        sys.exit(1)
    
    # Run test queries
    try:
        test_basic_queries(jg)
        test_person_queries(jg)
        test_relationship_queries(jg)
        test_path_queries(jg)
        test_aggregation_queries(jg)
        
        print("\n" + "="*60)
        print("✅ All tests completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
    finally:
        jg.close()


if __name__ == "__main__":
    main()
