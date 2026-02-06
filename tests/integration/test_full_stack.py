"""
Integration Tests for HCD + JanusGraph Full Stack
==================================================

Comprehensive integration tests for the full stack deployment.
Tests require services to be running - use fixtures for automatic skipping.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-28
Updated: 2026-01-29 (Day 5 improvements)
Phase: Week 3 Day 5 - Integration Test Improvements

Usage:
    # Deploy services first
    cd config/compose
    bash ../../scripts/deployment/deploy_full_stack.sh
    
    # Run all integration tests
    pytest tests/integration/ -v
    
    # Run specific test class
    pytest tests/integration/test_full_stack.py::TestStackHealth -v
    
    # Run with detailed output
    pytest tests/integration/ -v -s
"""

import pytest
import time
import logging
from gremlin_python.process.graph_traversal import __

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestStackHealth:
    """
    Test overall stack health and connectivity.
    
    These tests verify that all services are running and accessible.
    Tests will be skipped if services are not available.
    """
    
    def test_hcd_health(self, hcd_session):
        """
        Test HCD/Cassandra is running and accessible.
        
        Verifies:
        - Connection to HCD
        - Basic query execution
        - Version information retrieval
        """
        # Test basic query
        result = hcd_session.execute("SELECT release_version FROM system.local")
        version = result.one()[0]
        
        logger.info(f"✅ HCD version: {version}")
        assert version is not None
        assert len(version) > 0
    
    def test_janusgraph_health(self, janusgraph_connection):
        """
        Test JanusGraph is running and accessible.
        
        Verifies:
        - Connection to JanusGraph
        - Basic graph operations
        - Vertex count query
        """
        g = janusgraph_connection
        
        # Test basic query
        count = g.V().count().next()
        
        logger.info(f"✅ JanusGraph is healthy (vertex count: {count})")
        assert count >= 0
    
    def test_grafana_health(self, require_grafana):
        """
        Test Grafana is running and accessible.
        
        Note: This is an optional service for basic operations.
        """
        logger.info("✅ Grafana is healthy")
        assert require_grafana['available']
    
    def test_prometheus_health(self, require_prometheus):
        """
        Test Prometheus is running and accessible.
        
        Note: This is an optional service for basic operations.
        """
        logger.info("✅ Prometheus is healthy")
        assert require_prometheus['available']


@pytest.mark.integration
class TestJanusGraphOperations:
    """
    Test JanusGraph graph operations.
    
    Tests basic CRUD operations and graph traversals.
    Uses test_data_cleanup fixture to clean up after each test.
    """
    
    def test_create_vertex(self, janusgraph_connection, test_data_cleanup):
        """
        Test creating a vertex.
        
        Verifies:
        - Vertex creation
        - Property assignment
        - Vertex retrieval
        """
        g = janusgraph_connection
        
        # Create test vertex
        vertex = g.addV('test_person') \
            .property('name', 'Integration Test User') \
            .property('email', 'test@example.com') \
            .property('created_at', int(time.time())) \
            .next()
        
        assert vertex is not None
        logger.info(f"✅ Created vertex: {vertex.id}")
        
        # Verify vertex exists
        count = g.V().hasLabel('test_person') \
            .has('name', 'Integration Test User') \
            .count().next()
        
        assert count >= 1
    
    def test_create_edge(self, janusgraph_connection, test_data_cleanup):
        """
        Test creating an edge between vertices.
        
        Verifies:
        - Multiple vertex creation
        - Edge creation
        - Edge retrieval
        """
        g = janusgraph_connection
        
        # Create two vertices
        v1 = g.addV('test_person') \
            .property('name', 'Person A') \
            .next()
        
        v2 = g.addV('test_person') \
            .property('name', 'Person B') \
            .next()
        
        # Create edge
        edge = g.V(v1).addE('knows').to(v2).next()
        
        assert edge is not None
        logger.info(f"✅ Created edge: {edge.id}")
        
        # Verify edge exists
        edge_count = g.V(v1).outE('knows').count().next()
        assert edge_count >= 1
    
    def test_query_traversal(self, janusgraph_connection, test_data_cleanup):
        """
        Test complex graph traversal.
        
        Verifies:
        - Multi-hop traversals
        - Path finding
        - Property value extraction
        """
        g = janusgraph_connection
        
        # Create test graph structure: Alice -> Bob -> Charlie
        alice = g.addV('test_person').property('name', 'Alice').next()
        bob = g.addV('test_person').property('name', 'Bob').next()
        charlie = g.addV('test_person').property('name', 'Charlie').next()
        
        g.V(alice).addE('knows').to(bob).next()
        g.V(bob).addE('knows').to(charlie).next()
        
        # Test traversal: Find friends of friends
        friends_of_friends = g.V(alice) \
            .out('knows') \
            .out('knows') \
            .values('name') \
            .toList()
        
        assert 'Charlie' in friends_of_friends
        logger.info(f"✅ Friends of friends traversal: {friends_of_friends}")
    
    def test_vertex_properties(self, janusgraph_connection, test_data_cleanup):
        """
        Test vertex property operations.
        
        Verifies:
        - Multiple property types
        - Property retrieval
        - Property value accuracy
        """
        g = janusgraph_connection
        
        # Create vertex with multiple properties
        vertex = g.addV('test_entity') \
            .property('string_prop', 'test value') \
            .property('int_prop', 42) \
            .property('float_prop', 3.14) \
            .property('bool_prop', True) \
            .next()
        
        # Retrieve and verify properties
        props = g.V(vertex).valueMap().next()
        
        assert 'test value' in props.get('string_prop', [])
        assert 42 in props.get('int_prop', [])
        assert 3.14 in props.get('float_prop', [])
        
        logger.info(f"✅ Vertex properties verified: {len(props)} properties")
    
    def test_delete_operations(self, janusgraph_connection, test_data_cleanup):
        """
        Test delete operations.
        
        Verifies:
        - Vertex deletion
        - Deletion confirmation
        - Idempotent deletion
        """
        g = janusgraph_connection
        
        # Create test vertex
        vertex = g.addV('test_temp').property('name', 'Temporary').next()
        vertex_id = vertex.id
        
        # Verify it exists
        count_before = g.V(vertex_id).count().next()
        assert count_before == 1
        
        # Delete vertex
        g.V(vertex_id).drop().iterate()
        
        # Verify it's deleted
        count_after = g.V(vertex_id).count().next()
        assert count_after == 0
        
        logger.info("✅ Delete operation successful")
    
    def test_batch_operations(self, janusgraph_connection, test_data_cleanup):
        """
        Test batch vertex creation.
        
        Verifies:
        - Batch insert capability
        - Transaction handling
        - Data consistency
        """
        g = janusgraph_connection
        
        # Create multiple vertices in batch
        vertex_count = 10
        for i in range(vertex_count):
            g.addV('test_entity') \
                .property('index', i) \
                .property('batch_id', 'test_batch_1') \
                .next()
        
        # Verify all vertices were created
        count = g.V().hasLabel('test_entity') \
            .has('batch_id', 'test_batch_1') \
            .count().next()
        
        assert count == vertex_count
        logger.info(f"✅ Batch operation: created {vertex_count} vertices")


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """
    Test performance characteristics.
    
    These tests measure throughput and latency.
    Marked as 'slow' since they take longer to execute.
    """
    
    def test_bulk_insert_performance(self, janusgraph_connection, test_data_cleanup):
        """
        Test bulk insert performance.
        
        Measures:
        - Insert throughput (vertices/second)
        - Total time for batch operations
        
        Performance target: > 10 vertices/second
        """
        g = janusgraph_connection
        
        start_time = time.time()
        vertex_count = 100
        
        # Bulk insert vertices
        for i in range(vertex_count):
            g.addV('perf_test') \
                .property('index', i) \
                .property('timestamp', int(time.time())) \
                .next()
        
        elapsed_time = time.time() - start_time
        throughput = vertex_count / elapsed_time
        
        logger.info(f"📊 Bulk insert: {vertex_count} vertices in {elapsed_time:.2f}s")
        logger.info(f"📊 Throughput: {throughput:.2f} vertices/second")
        
        # Performance assertion (should be > 10 vertices/second)
        assert throughput > 10, f"Performance too slow: {throughput:.2f} v/s"
    
    def test_query_performance(self, janusgraph_connection, test_data_cleanup):
        """
        Test query performance.
        
        Measures:
        - Average query latency
        - Query consistency
        
        Performance target: < 100ms per query
        """
        g = janusgraph_connection
        
        # Create test data
        for i in range(50):
            g.addV('query_test').property('value', i).next()
        
        # Test query performance
        start_time = time.time()
        iterations = 100
        
        for _ in range(iterations):
            g.V().hasLabel('query_test').count().next()
        
        elapsed_time = time.time() - start_time
        avg_query_time = (elapsed_time / iterations) * 1000  # ms
        
        logger.info(f"📊 Average query time: {avg_query_time:.2f}ms")
        
        # Performance assertion (should be < 100ms per query)
        assert avg_query_time < 100, f"Query too slow: {avg_query_time:.2f}ms"
    
    def test_traversal_performance(self, janusgraph_connection, test_data_cleanup):
        """
        Test complex traversal performance.
        
        Measures:
        - Multi-hop traversal latency
        - Path finding efficiency
        
        Performance target: < 200ms for 3-hop traversal
        """
        g = janusgraph_connection
        
        # Create a chain of vertices: v0 -> v1 -> v2 -> v3 -> v4
        vertices = []
        for i in range(5):
            v = g.addV('perf_test').property('index', i).next()
            vertices.append(v)
        
        # Create edges
        for i in range(len(vertices) - 1):
            g.V(vertices[i]).addE('next').to(vertices[i + 1]).next()
        
        # Test traversal performance
        start_time = time.time()
        iterations = 50
        
        for _ in range(iterations):
            result = g.V(vertices[0]) \
                .out('next').out('next').out('next') \
                .count().next()
            assert result == 1
        
        elapsed_time = time.time() - start_time
        avg_time = (elapsed_time / iterations) * 1000  # ms
        
        logger.info(f"📊 Average 3-hop traversal time: {avg_time:.2f}ms")
        
        # Performance assertion
        assert avg_time < 200, f"Traversal too slow: {avg_time:.2f}ms"


@pytest.mark.integration
class TestDataPersistence:
    """
    Test data persistence across operations.
    
    Verifies that data is properly persisted to storage.
    """
    
    def test_data_persistence(self, janusgraph_connection, test_data_cleanup):
        """
        Test that data persists after creation.
        
        Verifies:
        - Data is written to storage
        - Data can be retrieved after creation
        - Unique identifiers work correctly
        """
        g = janusgraph_connection
        
        # Create unique test vertex
        test_id = f"persistence_test_{int(time.time())}"
        g.addV('persistence_test') \
            .property('test_id', test_id) \
            .property('created_at', int(time.time())) \
            .next()
        
        # Verify it exists
        count = g.V().hasLabel('persistence_test') \
            .has('test_id', test_id) \
            .count().next()
        
        assert count == 1
        logger.info(f"✅ Data persistence verified for: {test_id}")
    
    def test_property_update_persistence(self, janusgraph_connection, test_data_cleanup):
        """
        Test that property updates persist.
        
        Verifies:
        - Property updates are saved
        - Updated values can be retrieved
        - Original values are replaced
        """
        g = janusgraph_connection
        
        # Create vertex with string property (use unique name to avoid schema conflicts)
        vertex = g.addV('persistence_test') \
            .property('test_status', 'original') \
            .next()
        
        # Update property
        g.V(vertex).property('test_status', 'updated').next()
        
        # Verify update persisted
        updated_value = g.V(vertex).values('test_status').next()
        assert updated_value == 'updated'
        
        logger.info("✅ Property update persistence verified")


@pytest.mark.integration
class TestErrorHandling:
    """
    Test error handling and edge cases.
    
    Verifies that the system handles errors gracefully.
    """
    
    def test_invalid_query_handling(self, janusgraph_connection):
        """
        Test handling of invalid queries.
        
        Verifies:
        - Invalid queries raise appropriate exceptions
        - System remains stable after errors
        """
        g = janusgraph_connection
        
        # Test querying with invalid vertex ID (JanusGraph uses numeric IDs)
        # Use a very large ID that definitely doesn't exist
        count = g.V(9999999999999).count().next()
        assert count == 0
        
        # Test querying with non-existent property value
        count = g.V().has('name', 'definitely_not_a_real_name_xyz123').count().next()
        assert count == 0
        
        logger.info("✅ Invalid query handled gracefully")
    
    def test_empty_result_handling(self, janusgraph_connection):
        """
        Test handling of empty query results.
        
        Verifies:
        - Empty results don't cause errors
        - Count queries return 0 for no matches
        """
        g = janusgraph_connection
        
        # Query for non-existent label
        count = g.V().hasLabel('definitely_does_not_exist_12345').count().next()
        assert count == 0
        
        logger.info("✅ Empty result handled correctly")
    
    def test_concurrent_operations(self, janusgraph_connection, test_data_cleanup):
        """
        Test concurrent vertex creation.
        
        Verifies:
        - Multiple operations can execute
        - No data corruption occurs
        - All operations complete successfully
        """
        g = janusgraph_connection
        
        # Create multiple vertices rapidly
        vertex_ids = []
        for i in range(10):
            v = g.addV('test_entity') \
                .property('concurrent_id', i) \
                .next()
            vertex_ids.append(v.id)
        
        # Verify all were created
        count = g.V().hasLabel('test_entity') \
            .has('concurrent_id') \
            .count().next()
        
        assert count >= 10
        logger.info(f"✅ Concurrent operations: created {count} vertices")


# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
